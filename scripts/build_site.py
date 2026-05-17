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
            out.append(f"<li>{inline(item)}</li>")
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


def page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="./assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./index.html">AI News</a>
  </header>
  <main class="page">
    {body}
  </main>
</body>
</html>
"""


def report_shell(title: str, body: str) -> str:
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
  </main>
</body>
</html>
"""


def build_reports() -> list[Path]:
    html_reports: list[Path] = []
    target_dir = SITE_DIR / "reports"
    target_dir.mkdir(parents=True, exist_ok=True)
    for report in sorted(REPORTS_DIR.glob("20??-??-??.md")):
        body = markdown_to_html(report.read_text(encoding="utf-8"))
        target = target_dir / f"{report.stem}.html"
        target.write_text(report_shell(f"AI + GitHub 双源日报 · {report.stem}", body), encoding="utf-8")
        html_reports.append(target)
    return html_reports


def build_index(reports: list[Path]) -> None:
    latest = reports[-1] if reports else None
    latest_link = f"./reports/{latest.name}" if latest else "#"
    cards = []
    for report in reversed(reports[-7:]):
        cards.append(
            f'<a class="report-card" href="./reports/{report.name}">'
            f"<span>{report.stem}</span><strong>查看日报</strong></a>"
        )
    body = f"""
<section class="hero">
  <p class="eyebrow">AI + GitHub 双源日报</p>
  <h1>每天看清 AI 圈与开源圈的真正动向</h1>
  <p class="lede">聚合 AI HOT 精选、GitHub 今日热榜和涨星最快项目，适合在手机上快速扫一遍。</p>
  <a class="primary" href="{latest_link}">查看最新日报</a>
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
    <span>AI</span>
    <span>GitHub</span>
    <span>LLM</span>
    <span>Agent</span>
  </div>
</section>
"""
    (SITE_DIR / "index.html").write_text(page_shell("AI News", body), encoding="utf-8")


def write_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "styles.css").write_text(
        """
:root {
  color-scheme: light;
  --bg: #f7f7f4;
  --paper: #ffffff;
  --ink: #171717;
  --muted: #66655f;
  --line: #dfddd7;
  --accent: #14532d;
  --accent-soft: #dcefe1;
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
.hero { padding: 18px 0 28px; }
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
.chips span {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 14px;
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


if __name__ == "__main__":
    main()
