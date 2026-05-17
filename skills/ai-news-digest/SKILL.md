---
name: ai-news-digest
description: AI + GitHub 双源日报聚合 Skill。用于回答“今天有什么值得看”“给我一份 AI 日报”“整理今天 AI 和 GitHub 热点”“做一份双源日报”“今天 AI 圈和开源圈有什么新东西”等请求。默认同时汇总最近 24 小时 AI HOT 精选与 GitHub 热门仓库，生成中文 markdown 日报；也可按日期生成日报文件。
---

# AI News Digest

用这个 Skill 把 AI HOT 与 GitHub 热榜合成一份中文日报。优先调用 `scripts/daily_digest.py`，不要手工拼两边结果。

## 默认工作流

| 用户在问 | 执行 |
|---|---|
| “今天有什么值得看” / “今天 AI 圈和 GitHub 有啥” | `python scripts/daily_digest.py` |
| “给我一份 AI 日报” / “生成今日日报” | `python scripts/daily_digest.py --write` |
| “只看精简版” | `python scripts/daily_digest.py --ai-limit 5 --github-limit 5 --growth-limit 5` |
| “只看 AI” | `python scripts/daily_digest.py --sections ai` |
| “只看 GitHub” | `python scripts/daily_digest.py --sections github` |
| “加上 agent / llm 主题” | `python scripts/daily_digest.py --topic agent --topic llm --sections ai,github,topics` |

## 组成

- AI 资讯：最近 24 小时 AI HOT 精选。
- GitHub 今日值得看：GitHub Trending daily。
- GitHub 24 小时涨星最快：GitHub Trending daily 中按 `stars today` 排序。

## 输出结构

1. 标题、日期和收录数
2. 今日提要
3. AI 圈重点
4. GitHub 今日值得看
5. GitHub 24 小时涨星最快
6. 观察

## 输出要求

- 默认中文。
- 优先提炼 3-5 条真正值得看的内容，不要把榜单原样倾倒给用户。
- AI 与 GitHub 两部分都要保留原始链接。
- 对 GitHub 仓库，保留仓库名、总 stars、24 小时涨星数和一句说明。
- 对 AI 条目，保留标题、来源、发布时间和一句摘要。
- 如果 AI HOT 或 GitHub 任一来源失败，照常生成另一半，并在日报中明确标注缺失来源。
- `--write` 时同时更新 `reports/README.md` 历史索引页。

## 依赖

- `~/.codex/skills/aihot`
- `C:\aiNEWS\skills\github-hot\scripts\github_hot.py`

## 示例

```powershell
& 'C:\Users\86364\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'C:\aiNEWS\skills\ai-news-digest\scripts\daily_digest.py'

& 'C:\Users\86364\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'C:\aiNEWS\skills\ai-news-digest\scripts\daily_digest.py' --write
```
