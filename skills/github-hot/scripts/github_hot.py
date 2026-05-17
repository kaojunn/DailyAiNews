#!/usr/bin/env python3
"""Fetch GitHub hot repositories for Agent-friendly summaries."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from html import unescape


UA = "Mozilla/5.0 github-hot-skill/0.1"
GITHUB_API = "https://api.github.com/search/repositories"
TRENDING_URL = "https://github.com/trending?since=daily"


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_json(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def compact(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def clean_description(text: str) -> str:
    text = compact(text)
    text = re.sub(r"^Sponsor\s+Star\s+\S+\s*/\s*\S+\s+", "", text)
    return re.sub(r"^Star\s+\S+\s*/\s*\S+\s+", "", text)


def parse_trending(limit: int) -> list[dict]:
    html = fetch_text(TRENDING_URL)
    articles = re.findall(r"<article[^>]*Box-row[^>]*>(.*?)</article>", html, flags=re.S)
    results = []
    for article in articles:
        repo_match = re.search(r"<h2[^>]*>.*?href=\"/([^\"/]+/[^\"/]+)\"", article, flags=re.S)
        if not repo_match:
            continue
        full_name = repo_match.group(1)
        description_match = re.search(r"<p[^>]*>(.*?)</p>", article, flags=re.S)
        language_match = re.search(r'itemprop="programmingLanguage">([^<]+)</span>', article)
        stars_match = re.search(r'href="/[^"]+/stargazers"[^>]*>.*?([0-9][0-9,]*)\s*</a>', article, flags=re.S)
        today_match = re.search(r"([0-9][0-9,]*)\s+stars today", compact(article))
        results.append(
            {
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": clean_description(description_match.group(1)) if description_match else "",
                "language": compact(language_match.group(1)) if language_match else None,
                "stars": int(stars_match.group(1).replace(",", "")) if stars_match else None,
                "stars_today": int(today_match.group(1).replace(",", "")) if today_match else None,
            }
        )
    return results[:limit]


def search_repositories(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100),
        }
    )
    payload = fetch_json(f"{GITHUB_API}?{params}")
    return [
        {
            "full_name": item["full_name"],
            "url": item["html_url"],
            "description": item.get("description") or "",
            "language": item.get("language"),
            "stars": item["stargazers_count"],
            "forks": item["forks_count"],
            "updated_at": item["updated_at"],
        }
        for item in payload.get("items", [])
    ]


def ai_repositories(limit: int) -> list[dict]:
    queries = [
        "topic:artificial-intelligence",
        "topic:machine-learning",
        "topic:llm",
        "topic:ai-agent",
    ]
    merged: dict[str, dict] = {}
    for query in queries:
        for repo in search_repositories(query, limit):
            merged.setdefault(repo["full_name"], repo)
    return sorted(merged.values(), key=lambda item: item["stars"], reverse=True)[:limit]


def emit(command: str, items: list[dict]) -> None:
    print(json.dumps({"command": command, "count": len(items), "items": items}, ensure_ascii=False, indent=2))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Fetch GitHub hot repositories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("today", "growth24h", "ai", "leaderboard"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--limit", type=int, default=10)

    search = subparsers.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    try:
        if args.command == "today":
            emit("today", parse_trending(args.limit))
        elif args.command == "growth24h":
            items = sorted(
                [item for item in parse_trending(100) if item["stars_today"] is not None],
                key=lambda item: item["stars_today"],
                reverse=True,
            )[: args.limit]
            emit("growth24h", items)
        elif args.command == "ai":
            emit("ai", ai_repositories(args.limit))
        elif args.command == "leaderboard":
            emit("leaderboard", search_repositories("stars:>1", args.limit))
        elif args.command == "search":
            emit("search", search_repositories(args.query, args.limit))
        return 0
    except Exception as exc:
        print(json.dumps({"command": args.command, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
