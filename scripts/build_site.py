#!/usr/bin/env python3
"""Build a small static site from generated Markdown reports."""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
SITE_DIR = ROOT / "site"
ASSETS_DIR = SITE_DIR / "assets"
HERO_IMAGE = "./assets/hero-editorial.webp"
TOPIC_PAGES = {
    "ai": ("AI", "聚焦 AI 圈重点动态"),
    "github": ("GitHub", "查看今日热门开源项目"),
    "llm": ("LLM", "浏览大模型相关仓库"),
    "agent": ("Agent", "浏览智能体相关仓库"),
}


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(https?://\S+)", r'<a href="\1" target="_blank" rel="noreferrer">\1</a>', text)
    return text


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    in_list = False
    for raw in lines:
        line = raw.rstrip()
        if not line:
            if in_list:
                out.append("</ol>")
                in_list = False
            continue
        if line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ol>")
                in_list = False
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_list:
                out.append("</ol>")
                in_list = False
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("> "):
            out.append(f"<p class=\"meta\">{inline(line[2:])}</p>")
        elif re.match(r"^\d+\.\s+", line):
            if not in_list:
                out.append("<ol>")
                in_list = True
            item = re.sub(r"^\d+\.\s+", "", line)
            tag_match = re.match(r"^\[([^\]]+)\]\s+(.*)", item)
            if tag_match:
                item_html = f'<span class="tag">{html.escape(tag_match.group(1))}</span> {inline(tag_match.group(2))}'
            else:
                item_html = inline(item)
            out.append(f"<li>{item_html}</li>")
        elif line.startswith("   "):
            out.append(f"<p class=\"detail\">{inline(line.strip())}</p>")
        elif line.startswith("- "):
            if in_list:
                out.append("</ol>")
                in_list = False
            out.append(f"<p class=\"bullet\">{inline(line[2:])}</p>")
        else:
            if in_list:
                out.append("</ol>")
                in_list = False
            out.append(f"<p>{inline(line)}</p>")
    if in_list:
        out.append("</ol>")
    return "\n".join(out)


def page_shell(title: str, body: str, prefix: str = ".") -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{prefix}/assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{prefix}/index.html">AI News</a>
  </header>
  <main class="page">
    {body}
  </main>
</body>
</html>
"""


def report_shell(title: str, body: str, prev_link: str | None, next_link: str | None) -> str:
    prev_html = f'<a href="{prev_link}">上一篇</a>' if prev_link else "<span>上一篇</span>"
    next_html = f'<a href="{next_link}">下一篇</a>' if next_link else "<span>下一篇</span>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="../assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="../index.html">AI News</a>
  </header>
  <main class="page report">
    {body}
    <nav class="report-nav">
      {prev_html}
      <a href="#top">返回顶部</a>
      {next_html}
    </nav>
  </main>
</body>
</html>
"""


def build_reports() -> list[Path]:
    html_reports: list[Path] = []
    target_dir = SITE_DIR / "reports"
    target_dir.mkdir(parents=True, exist_ok=True)
    source_reports = sorted(REPORTS_DIR.glob("20??-??-??.md"))
    for idx, report in enumerate(source_reports):
        body = markdown_to_html(report.read_text(encoding="utf-8"))
        target = target_dir / f"{report.stem}.html"
        prev_link = f"./{source_reports[idx - 1].stem}.html" if idx > 0 else None
        next_link = f"./{source_reports[idx + 1].stem}.html" if idx + 1 < len(source_reports) else None
        target.write_text(
            report_shell(f"AI + GitHub 双源日报 · {report.stem}", body, prev_link, next_link),
            encoding="utf-8",
        )
        html_reports.append(target)
    return html_reports


def extract_top_items(markdown: str) -> list[tuple[str, str]]:
    ai_items: list[tuple[str, str]] = []
    github_items: list[tuple[str, str]] = []
    current_section = ""
    for line in markdown.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
        if re.match(r"^\d+\.\s+", line) and current_section in {"AI 圈重点", "GitHub 今日值得看"}:
            plain = re.sub(r"^\d+\.\s+", "", line)
            plain = re.sub(r"^\[([^\]]+)\]\s+", r"\1 · ", plain)
            plain = re.sub(r"\*\*", "", plain)
            if current_section == "AI 圈重点":
                ai_items.append((current_section, plain))
            else:
                github_items.append((current_section, plain))
    return ai_items[:2] + github_items[:1]


def build_index(reports: list[Path]) -> None:
    latest = reports[-1] if reports else None
    latest_link = f"./reports/{latest.name}" if latest else "#"
    latest_md = REPORTS_DIR / f"{latest.stem}.md" if latest else None
    top_items = extract_top_items(latest_md.read_text(encoding="utf-8")) if latest_md else []
    cards = []
    for report in reversed(reports[-7:]):
        cards.append(
            f'<a class="report-card" href="./reports/{report.name}">'
            f"<span>{report.stem}</span><strong>查看日报</strong></a>"
        )
    body = f"""
<section class="hero">
  <img class="hero-image" src="{HERO_IMAGE}" alt="">
  <div class="hero-copy">
    <p class="eyebrow">AI + GitHub 双源日报</p>
    <h1>每天看清 AI 圈与开源圈的真正动向</h1>
    <p class="lede">聚合 AI HOT 精选、GitHub 今日热榜和涨星最快项目，适合在手机上快速扫一遍。</p>
    <a class="primary" href="{latest_link}">查看最新日报</a>
  </div>
</section>

<section class="metrics">
  <div><strong>{len(reports)}</strong><span>累计日报</span></div>
  <div><strong>AI</strong><span>热点精选</span></div>
  <div><strong>GitHub</strong><span>开源雷达</span></div>
</section>

<section class="spotlight">
  <div class="section-head">
    <h2>今日最值得看</h2>
    <span>Top 3</span>
  </div>
  <div class="spotlight-grid">
    {''.join(f'<article><small>{section}</small><p>{html.escape(text)}</p></article>' for section, text in top_items)}
  </div>
</section>

<section>
  <div class="section-head">
    <h2>最近日报</h2>
    <span>{len(reports)} 期</span>
  </div>
  <div class="report-grid">
    {''.join(cards) if cards else '<p>还没有日报。</p>'}
  </div>
</section>

<section class="topics">
  <h2>快捷主题</h2>
  <div class="chips">
    {''.join(f'<a href="./topics/{slug}.html">{label}</a>' for slug, (label, _) in TOPIC_PAGES.items())}
  </div>
</section>
"""
    (SITE_DIR / "index.html").write_text(page_shell("AI News", body), encoding="utf-8")


def extract_topic_items(markdown: str, slug: str) -> list[str]:
    lines = markdown.splitlines()
    items: list[str] = []
    active_heading = ""
    active_subheading = ""
    for line in lines:
        if line.startswith("## "):
            active_heading = line[3:].strip()
            active_subheading = ""
        elif line.startswith("### "):
            active_subheading = line[4:].strip()
        elif re.match(r"^\d+\.\s+", line):
            plain = re.sub(r"^\d+\.\s+", "", line)
            if slug == "ai" and active_heading == "AI 圈重点":
                items.append(plain)
            elif slug == "github" and active_heading == "GitHub 今日值得看":
                items.append(plain)
            elif slug == "llm" and active_heading == "指定主题" and active_subheading == "llm":
                items.append(plain)
            elif slug == "agent" and active_heading == "指定主题" and active_subheading == "agent":
                items.append(plain)
    return items


def build_topics(reports: list[Path]) -> None:
    target_dir = SITE_DIR / "topics"
    target_dir.mkdir(parents=True, exist_ok=True)
    latest = reports[-1] if reports else None
    latest_md = (REPORTS_DIR / f"{latest.stem}.md").read_text(encoding="utf-8") if latest else ""
    for slug, (label, description) in TOPIC_PAGES.items():
        items = extract_topic_items(latest_md, slug)
        rendered = []
        for item in items:
            tag_match = re.match(r"^\[([^\]]+)\]\s+(.*)", item)
            if tag_match:
                rendered.append(
                    f'<li><span class="tag">{html.escape(tag_match.group(1))}</span> {inline(tag_match.group(2))}</li>'
                )
            else:
                rendered.append(f"<li>{inline(item)}</li>")
        item_html = "".join(rendered)
        body = f"""
<section class="topic-hero">
  <p class="eyebrow">主题</p>
  <h1>{label}</h1>
  <p class="lede">{description}</p>
</section>
<section>
  <div class="section-head">
    <h2>最新日报中的相关条目</h2>
    <span>{len(items)} 条</span>
  </div>
  <ol class="topic-list">{item_html}</ol>
</section>
"""
        (target_dir / f"{slug}.html").write_text(page_shell(f"{label} 主题", body, ".."), encoding="utf-8")


def write_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "styles.css").write_text(
        """
:root {
  color-scheme: light;
  --bg: #f5f3ee;
  --paper: #ffffff;
  --ink: #171717;
  --muted: #66655f;
  --line: #dfddd7;
  --accent: #14532d;
  --accent-soft: #dcefe1;
  --coral: #c96d52;
  --blue: #385f89;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.65;
}
.topbar {
  border-bottom: 1px solid var(--line);
  background: rgba(247,247,244,.92);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
}
.brand {
  display: block;
  max-width: 860px;
  margin: 0 auto;
  padding: 14px 20px;
  color: var(--ink);
  text-decoration: none;
  font-weight: 700;
}
.page {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px 20px 56px;
}
.hero {
  min-height: 360px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  margin: 8px 0 22px;
  background: #ece6db;
}
.hero-image {
  width: 100%;
  height: 100%;
  min-height: 360px;
  object-fit: cover;
  display: block;
}
.hero-copy {
  position: absolute;
  inset: 0;
  width: min(58%, 500px);
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: linear-gradient(90deg, rgba(245,243,238,.96), rgba(245,243,238,.88), rgba(245,243,238,0));
}
.eyebrow { color: var(--accent); font-weight: 700; margin: 0 0 10px; }
h1 {
  font-size: clamp(28px, 5vw, 42px);
  line-height: 1.15;
  margin: 0 0 14px;
}
.lede { max-width: 620px; color: var(--muted); margin-bottom: 20px; }
.primary {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  padding: 10px 16px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
}
.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 18px 0 28px;
}
.metrics div {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}
.metrics strong {
  display: block;
  font-size: 24px;
}
.metrics span {
  color: var(--muted);
  font-size: 14px;
}
.spotlight {
  margin: 8px 0 28px;
}
.spotlight-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.spotlight-grid article {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}
.spotlight-grid small {
  color: var(--coral);
  font-weight: 700;
}
.spotlight-grid p {
  margin-bottom: 0;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 14px;
}
.section-head h2, .topics h2 { margin: 0; }
.section-head span { color: var(--muted); }
.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}
.report-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  color: var(--ink);
  text-decoration: none;
}
.report-card strong { color: var(--accent); }
.topics { margin-top: 28px; }
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chips a {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 14px;
  text-decoration: none;
}
.report h1 { font-size: 30px; }
.report h2 {
  margin-top: 28px;
  padding-top: 10px;
  border-top: 1px solid var(--line);
  font-size: 22px;
}
.report h3 { margin-top: 18px; font-size: 18px; }
.meta { color: var(--muted); }
.report ol {
  padding-left: 22px;
}
.report {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 8px;
  margin-right: 6px;
  background: #eef1f5;
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
}
.report-nav {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 32px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}
.report-nav span {
  color: var(--muted);
}
.topic-hero {
  margin-bottom: 24px;
}
.muted {
  color: var(--muted);
}
.topic-list {
  padding-left: 22px;
}
.topic-list li {
  margin: 12px 0;
}
.report li {
  margin: 14px 0 4px;
}
.detail {
  margin: 3px 0 3px 22px;
  color: #34332f;
}
.bullet {
  margin-left: 0;
}
a {
  color: var(--accent);
  word-break: break-word;
}
@media (max-width: 640px) {
  .page { padding: 18px 16px 40px; }
  .brand { padding-inline: 16px; }
  .report h1 { font-size: 26px; }
  .detail { margin-left: 0; }
  .hero {
    min-height: 420px;
  }
  .hero-image {
    min-height: 420px;
  }
  .hero-copy {
    width: 100%;
    justify-content: flex-end;
    padding: 20px;
    background: linear-gradient(180deg, rgba(245,243,238,0), rgba(245,243,238,.78), rgba(245,243,238,.98));
  }
  .metrics {
    grid-template-columns: 1fr;
  }
  .spotlight-grid {
    grid-template-columns: 1fr;
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    write_assets()
    reports = build_reports()
    build_index(reports)
    build_topics(reports)


if __name__ == "__main__":
    main()
