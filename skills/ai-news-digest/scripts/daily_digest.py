#!/usr/bin/env python3
"""Build a Chinese daily digest from AI HOT and GitHub sources."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


AIHOT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
    "aihot-skill/0.2.0"
)
BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BASE_DIR.parent
GITHUB_HOT = BASE_DIR / "github-hot" / "scripts" / "github_hot.py"
REPORTS_DIR = PROJECT_DIR / "reports"
INDEX_PATH = REPORTS_DIR / "README.md"
SITE_BUILDER = PROJECT_DIR / "scripts" / "build_site.py"
CST = timezone(timedelta(hours=8))
CATEGORY_LABELS = {
    "ai-models": "模型发布/更新",
    "ai-products": "产品发布/更新",
    "industry": "行业动态",
    "paper": "论文研究",
    "tip": "技巧与观点",
}
SECTION_CHOICES = {"ai", "github", "topics"}


def fetch_aihot(limit: int) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = (
        "https://aihot.virxact.com/api/public/items?"
        + urllib.parse.urlencode({"mode": "selected", "since": since, "take": limit})
    )
    req = urllib.request.Request(url, headers={"User-Agent": AIHOT_UA})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("items", [])


def run_github_hot(command: str, limit: int, query: str | None = None) -> list[dict]:
    args = [sys.executable, str(GITHUB_HOT), command]
    if query:
        args.append(query)
    args.extend(["--limit", str(limit)])
    proc = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(proc.stdout)["items"]


def fmt_time(value: str | None) -> str:
    if not value:
        return "时间未知"
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(CST)
    now = datetime.now(CST)
    if dt.date() == now.date():
        return f"今天 {dt:%H:%M}"
    if dt.date() == (now.date() - timedelta(days=1)):
        return f"昨天 {dt:%H:%M}"
    return f"{dt:%m/%d %H:%M}"


def trim(text: str | None, limit: int = 88) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def github_summary(item: dict) -> str:
    return trim(item.get("summary_zh") or item.get("description"), 72)


def group_ai(items: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        groups[CATEGORY_LABELS.get(item.get("category"), "其他")].append(item)
    return groups


def editorial_line(ai_items: list[dict], today_items: list[dict], topics: dict[str, list[dict]]) -> str:
    if ai_items and today_items:
        return "Agent 正在同时推进两条线：一边更深入日常工作流，一边继续把开源工具链推向更高的完成度。"
    if ai_items:
        return "今天的主角在 AI 圈，产品更新和产业落地都比概念讨论更靠前。"
    if today_items or topics:
        return "今天更像是开源雷达日，GitHub 上的新工具和新框架格外活跃。"
    return "今天只拿到有限数据，先保留已确认的信号。"


def build_markdown(
    ai_items: list[dict],
    today_items: list[dict],
    growth_items: list[dict],
    topic_items: dict[str, list[dict]],
    date_text: str,
    sections: set[str],
) -> str:
    total_items = len(ai_items) + len(today_items) + sum(len(items) for items in topic_items.values())
    lines = [
        f"# AI + GitHub 双源日报",
        "",
        f"> 日期：{date_text}  |  时区：Asia/Shanghai  |  收录：{total_items} 条",
        "",
        "## 今日提要",
        "",
        editorial_line(ai_items, today_items, topic_items),
        "",
    ]

    if "ai" in sections:
        lines.extend(["## AI 圈重点", ""])
        if ai_items:
            shown = 0
            for label, items in group_ai(ai_items).items():
                lines.append(f"### {label}")
                for item in items:
                    shown += 1
                    lines.append(
                        f"{shown}. **{item['title']}** — {item['source']}（{fmt_time(item.get('publishedAt'))}）"
                    )
                    lines.append(f"   {trim(item.get('summary'))}")
                    lines.append(f"   {item['url']}")
                lines.append("")
        else:
            lines.extend(["AI HOT 数据获取失败。", ""])

    if "github" in sections:
        lines.extend(["## GitHub 今日值得看", ""])
        if today_items:
            for idx, item in enumerate(today_items, 1):
                stars = f"{item['stars']:,}" if item.get("stars") is not None else "未知"
                today = f" +{item['stars_today']:,}/24h" if item.get("stars_today") is not None else ""
                lines.append(f"{idx}. **{item['full_name']}** — ⭐ {stars}{today}")
                lines.append(f"   {github_summary(item)}")
                lines.append(f"   {item['url']}")
            lines.append("")
        else:
            lines.extend(["GitHub 今日热榜获取失败。", ""])

        lines.extend(["## GitHub 24 小时涨星最快", ""])
        if growth_items:
            for idx, item in enumerate(growth_items, 1):
                stars = f"{item['stars']:,}" if item.get("stars") is not None else "未知"
                today = f"+{item['stars_today']:,}" if item.get("stars_today") is not None else "未知"
                lines.append(f"{idx}. **{item['full_name']}** — 24h {today}，总星 {stars}")
            lines.append("")
        else:
            lines.extend(["GitHub 涨星榜获取失败。", ""])

    if "topics" in sections and topic_items:
        lines.extend(["## 指定主题", ""])
        for topic, items in topic_items.items():
            lines.append(f"### {topic}")
            if not items:
                lines.append("未检索到结果。")
                lines.append("")
                continue
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. **{item['full_name']}** — ⭐ {item['stars']:,}")
                lines.append(f"   {github_summary(item)}")
                lines.append(f"   {item['url']}")
            lines.append("")

    lines.extend(
        [
            "## 观察",
            "",
            "- 真正值得长期跟踪的项目，最好同时看热度、更新频率和是否进入真实工作流。",
            "- 每日榜单适合发现新信号，历史索引更适合回看趋势。",
            "",
        ]
    )
    return "\n".join(lines)


def write_index() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = sorted(
        [path for path in REPORTS_DIR.glob("20??-??-??.md") if path.name != INDEX_PATH.name],
        reverse=True,
    )
    lines = [
        "# AI + GitHub 双源日报索引",
        "",
        f"> 共 {len(reports)} 期日报",
        "",
        "| 日期 | 链接 |",
        "|---|---|",
    ]
    for path in reports:
        lines.append(f"| {path.stem} | [{path.name}](./{path.name}) |")
    lines.append("")
    INDEX_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_sections(raw: str) -> set[str]:
    sections = {part.strip().lower() for part in raw.split(",") if part.strip()}
    invalid = sections - SECTION_CHOICES
    if invalid:
        raise ValueError(f"unsupported sections: {', '.join(sorted(invalid))}")
    return sections or {"ai", "github"}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Build AI + GitHub daily digest.")
    parser.add_argument("--ai-limit", type=int, default=8)
    parser.add_argument("--github-limit", type=int, default=8)
    parser.add_argument("--growth-limit", type=int, default=5)
    parser.add_argument("--topic-limit", type=int, default=5)
    parser.add_argument("--sections", default="ai,github", help="comma-separated: ai,github,topics")
    parser.add_argument("--topic", action="append", default=[], help="repeatable GitHub topic/search query")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    sections = parse_sections(args.sections)
    if args.topic:
        sections.add("topics")

    ai_items: list[dict] = []
    today_items: list[dict] = []
    growth_items: list[dict] = []
    topic_items: dict[str, list[dict]] = {}

    if "ai" in sections:
        try:
            ai_items = fetch_aihot(args.ai_limit)
        except Exception:
            ai_items = []

    if "github" in sections:
        try:
            today_items = run_github_hot("today", args.github_limit)
        except Exception:
            today_items = []
        try:
            growth_items = run_github_hot("growth24h", args.growth_limit)
        except Exception:
            growth_items = []

    if "topics" in sections:
        for topic in args.topic:
            try:
                topic_items[topic] = run_github_hot("search", args.topic_limit, topic)
            except Exception:
                topic_items[topic] = []

    today = datetime.now(CST).strftime("%Y-%m-%d")
    markdown = build_markdown(ai_items, today_items, growth_items, topic_items, today, sections)
    print(markdown)

    if args.write:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / f"{today}.md"
        path.write_text(markdown, encoding="utf-8")
        write_index()
        subprocess.run([sys.executable, str(SITE_BUILDER)], check=True)
        print(f"\n[written] {path}", file=sys.stderr)
        print(f"[index] {INDEX_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
