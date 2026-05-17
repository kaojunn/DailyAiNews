#!/usr/bin/env python3
"""Render a newspaper-style poster image from a daily Markdown report."""

from __future__ import annotations

import re
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
POSTERS_DIR = ROOT / "posters"
HERO_PATH = ROOT / "site" / "assets" / "hero-editorial.webp"
SERIF = r"C:\Windows\Fonts\simsun.ttc"
BOLD = r"C:\Windows\Fonts\simhei.ttf"
KAI = r"C:\Windows\Fonts\simkai.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def extract_sections(markdown: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
        elif re.match(r"^\d+\.\s+", line) and current:
            text = re.sub(r"^\d+\.\s+", "", line)
            text = text.replace("**", "")
            sections[current].append(text)
    return sections


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, width: int, fill=20, spacing=8) -> int:
    x, y = xy
    chars = max(8, width // max(1, int(fnt.size * 0.95)))
    lines = []
    for para in text.split("\n"):
        lines.extend(textwrap.wrap(para, width=chars) or [""])
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + spacing
    return y


def make_texture(size: tuple[int, int]) -> Image.Image:
    base = Image.new("L", size, 242)
    noise = Image.effect_noise(size, 10).filter(ImageFilter.GaussianBlur(0.4))
    return Image.blend(base, noise, 0.08)


def build(report_path: Path) -> Path:
    markdown = report_path.read_text(encoding="utf-8")
    sections = extract_sections(markdown)
    date_text = report_path.stem
    issue = datetime.strptime(date_text, "%Y-%m-%d").strftime("%Y年%m月%d日")

    width, height = 1800, 2550
    paper = make_texture((width, height)).convert("RGB")
    draw = ImageDraw.Draw(paper)

    title_font = font(KAI, 104)
    mast_font = font(BOLD, 42)
    headline_font = font(BOLD, 54)
    sub_font = font(SERIF, 28)
    body_font = font(SERIF, 28)
    small_font = font(SERIF, 24)

    margin = 48
    draw.rectangle((margin, margin, width - margin, height - margin), outline=25, width=3)
    draw.rectangle((margin + 10, margin + 10, width - margin - 10, 175), outline=25, width=2)

    draw.text((80, 82), issue, font=small_font, fill=20)
    draw.text((80, 118), "今日版", font=small_font, fill=20)
    draw.text((width // 2 - 250, 64), "代码日报", font=title_font, fill=10)
    draw.text((width // 2 - 170, 170), "GitHub 与 AI 每日消息", font=mast_font, fill=20)

    y = 245
    draw.line((margin, y, width - margin, y), fill=20, width=3)
    headline = "AI 与开源生态继续加速融合"
    draw.text((margin + 10, y + 22), headline, font=headline_font, fill=10)
    draw.text((margin + 14, y + 92), "每日精选、仓库热度与开发者趋势速览", font=sub_font, fill=25)

    col_gap = 24
    left_w = 470
    image_x = margin + left_w + col_gap
    image_w = 760
    right_x = image_x + image_w + col_gap
    right_w = width - margin - right_x
    body_y = y + 145

    ai_items = sections.get("AI 圈重点", [])[:4]
    gh_items = sections.get("GitHub 今日值得看", [])[:4]
    hot_items = sections.get("GitHub 24 小时涨星最快", [])[:3]
    llm_items = sections.get("指定主题", [])[:4]

    draw.text((margin + 10, body_y), "AI 圈重点", font=mast_font, fill=10)
    yy = body_y + 52
    for item in ai_items:
        yy = draw_wrapped(draw, (margin + 10, yy), "• " + item, small_font, left_w - 30)
        yy += 8

    hero = Image.open(HERO_PATH).convert("L").resize((image_w, 390))
    paper.paste(hero.convert("RGB"), (image_x, body_y - 8))
    draw.rectangle((image_x, body_y - 8, image_x + image_w, body_y + 382), outline=20, width=2)
    draw.text((image_x + 12, body_y + 394), "开发者与 AI 工具链继续靠拢。", font=small_font, fill=20)

    draw.rectangle((right_x, body_y - 8, width - margin - 10, body_y + 382), outline=20, width=2)
    draw.text((right_x + 16, body_y + 8), "要闻速递", font=mast_font, fill=10)
    yy2 = body_y + 62
    for item in gh_items:
        yy2 = draw_wrapped(draw, (right_x + 16, yy2), "• " + item, small_font, right_w - 30)
        yy2 += 8

    mid_y = max(yy, body_y + 450) + 18
    draw.line((margin, mid_y, width - margin, mid_y), fill=20, width=2)
    box_w = (width - margin * 2 - col_gap * 3) // 4
    boxes = [
        ("涨星最快", hot_items),
        ("主题观察", llm_items),
        ("今日注脚", ["真正值得长期跟踪的项目，要同时看热度、更新频率和真实采用。"]),
        ("关键词", ["Agent", "LLM", "开源", "自动化"]),
    ]
    for idx, (label, items) in enumerate(boxes):
        x = margin + idx * (box_w + col_gap)
        draw.rectangle((x, mid_y + 18, x + box_w, mid_y + 370), outline=20, width=2)
        draw.text((x + 14, mid_y + 34), label, font=mast_font, fill=10)
        yy3 = mid_y + 92
        for item in items[:4]:
            yy3 = draw_wrapped(draw, (x + 14, yy3), "• " + item, small_font, box_w - 28)
            yy3 += 8

    lower_y = mid_y + 410
    draw.line((margin, lower_y, width - margin, lower_y), fill=20, width=2)
    draw.text((margin + 10, lower_y + 18), "深度观察", font=mast_font, fill=10)
    observation = (
        "Agent 工具链正在从“能回答”走向“能完成工作”。"
        "今天的新闻里，产品更新、智能体框架与开源生态同步升温，"
        "说明开发者工作流正在成为 AI 竞争的核心战场。"
    )
    draw_wrapped(draw, (margin + 10, lower_y + 70), observation, body_font, width - margin * 2 - 20)

    lower_box_y = lower_y + 210
    lower_box_w = (width - margin * 2 - col_gap * 2) // 3
    lower_boxes = [
        ("AI 进展", ai_items[:3]),
        ("GitHub 热门", gh_items[:3]),
        ("开发者提示", ["日报适合发现新信号，历史索引适合回看趋势。"]),
    ]
    for idx, (label, items) in enumerate(lower_boxes):
        x = margin + idx * (lower_box_w + col_gap)
        draw.rectangle((x, lower_box_y, x + lower_box_w, lower_box_y + 430), outline=20, width=2)
        draw.text((x + 14, lower_box_y + 18), label, font=mast_font, fill=10)
        yy4 = lower_box_y + 76
        for item in items:
            yy4 = draw_wrapped(draw, (x + 14, yy4), "• " + item, small_font, lower_box_w - 28)
            yy4 += 8

    footer_y = height - 110
    draw.line((margin, footer_y, width - margin, footer_y), fill=20, width=2)
    draw.text((margin + 10, footer_y + 20), "技术改变世界，协作成就未来。", font=mast_font, fill=15)
    draw.text((width - 410, footer_y + 28), "aiNEWS · 本地自动生成", font=small_font, fill=25)

    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    out = POSTERS_DIR / f"{report_path.stem}.png"
    paper.save(out)
    return out


def main() -> None:
    latest = sorted(REPORTS_DIR.glob("20??-??-??.md"))[-1]
    print(build(latest))


if __name__ == "__main__":
    main()
