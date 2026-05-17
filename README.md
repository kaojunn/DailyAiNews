# aiNEWS

一个轻量的 AI + GitHub 双源日报项目。

## 内容

- AI HOT 精选资讯
- GitHub 今日热榜
- GitHub 24 小时涨星最快
- 可选 GitHub 主题栏目
- 静态网页首页与历史日报页

## 目录

- `reports/`：Markdown 日报与索引
- `site/`：可直接发布的静态网站
- `skills/`：本项目使用的本地 skills
- `scripts/`：站点生成脚本

## 常用命令

```powershell
& 'C:\Users\86364\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  '.\skills\ai-news-digest\scripts\daily_digest.py' --write
```

```powershell
& 'C:\Users\86364\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  '.\scripts\build_site.py'
```

```powershell
.\scripts\publish_daily.ps1
```

`publish_daily.ps1` 会在日报和站点文件有变化时自动提交并推送；如果还没配置 Git 远程仓库，它只会做本地提交，不会报错中断。
