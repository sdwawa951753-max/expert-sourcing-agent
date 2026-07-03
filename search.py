"""Pluggable web search.

Supports Tavily or Serper via env keys. If neither is configured, `search()`
returns an empty list so the pipeline still runs (it just won't have open-web
evidence). This keeps the dependency surface small and lets users bring whatever
search provider they already pay for.
"""
from __future__ import annotations

import os
from typing import Optional


def _tavily(query: str, k: int) -> list[dict]:
    import requests
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    r = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": key, "query": query, "max_results": k},
        timeout=20,
    )
    r.raise_for_status()
    return [
        {"title": x.get("title", ""), "url": x.get("url", ""), "snippet": x.get("content", "")}
        for x in r.json().get("results", [])
    ]


def _serper(query: str, k: int) -> list[dict]:
    import requests
    key = os.getenv("SERPER_API_KEY")
    if not key:
        return []
    r = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        json={"q": query, "num": k},
        timeout=20,
    )
    r.raise_for_status()
    return [
        {"title": x.get("title", ""), "url": x.get("link", ""), "snippet": x.get("snippet", "")}
        for x in r.json().get("organic", [])
    ]


def search(query: str, k: int = 5, provider: Optional[str] = None) -> list[dict]:
    provider = (provider or os.getenv("SEARCH_PROVIDER") or "tavily").lower()
    try:
        if provider == "tavily":
            return _tavily(query, k)
        if provider == "serper":
            return _serper(query, k)
    except Exception:
        # Search is best-effort enrichment; never let it break the run.
        return []
    return []
