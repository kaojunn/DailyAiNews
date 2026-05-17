---
name: github-hot
description: GitHub 热门仓库查询与中文简报 Skill。用于回答“今天 GitHub 有什么值得看”“最近 24 小时涨星最快”“看 AI 相关热门仓库”“看总 star 排行榜”“搜一下某个主题/关键词相关仓库”等请求。默认优先返回可读的中文摘要，并在需要时调用内置脚本获取 GitHub Trending、AI 主题仓库、24 小时涨星榜、总 star 榜和指定主题检索结果。
---

# GitHub Hot Skill

用这个 Skill 查询 GitHub 热门仓库，并把结果整理成中文简报。优先调用 `scripts/github_hot.py`，不要凭记忆回答当前榜单。

## 任务路由

| 用户在问 | 执行 |
|---|---|
| “今天 GitHub 有什么值得看” / “今天 GitHub 热门” | `python scripts/github_hot.py today --limit 10` |
| “看 AI 相关热门仓库” / “AI 热门项目” | `python scripts/github_hot.py ai --limit 10` |
| “最近 24 小时涨星最快” | `python scripts/github_hot.py growth24h --limit 10` |
| “看总 star 排行榜” | `python scripts/github_hot.py leaderboard --limit 20` |
| “搜一下 agent / rust / llm / xxx 主题” | `python scripts/github_hot.py search "<query>" --limit 10` |

## 数据源选择

- `today` 与 `growth24h`：读取 GitHub Trending daily 页面。
- `leaderboard`：读取 GitHub 官方仓库搜索接口，按总 stars 降序。
- `search`：读取 GitHub 官方仓库搜索接口，按总 stars 降序。
- `ai`：组合多个 AI 主题检索结果，去重后按 stars 排序。

## 输出要求

- 默认用中文。
- 先给 3-5 条“最值得看”的摘要，再给完整列表。
- 每条至少保留：仓库名、star 数、24 小时涨星数（如有）、一句话说明、链接。
- “今天值得看”优先解释为什么值得看，不要只报数字。
- “最近 24 小时涨星最快”按 24 小时新增 stars 排序。
- “总 star 排行榜”明确这是总榜，不要把它说成今日热度。
- “主题检索”把用户原词回显为人话标题，例如“Rust 相关高星仓库”。

## 使用细节

- 在 Windows 环境优先使用工作区自带 Python：
  `C:\Users\86364\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- 如果需要 GitHub token，可通过 `GITHUB_TOKEN` 环境变量提供；没有 token 也能使用，但官方搜索接口会更容易触发速率限制。
- 当 GitHub Trending 页面结构变化导致 `today` 或 `growth24h` 失败时，明确说明是抓取失败，不要伪造结果。
- 当用户问的是“最近/今天”的动态信息时，必须重新获取数据。

## 示例

```powershell
& 'C:\Users\86364\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'C:\aiNEWS\skills\github-hot\scripts\github_hot.py' today --limit 10

& 'C:\Users\86364\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'C:\aiNEWS\skills\github-hot\scripts\github_hot.py' search 'llm agent' --limit 10
```
