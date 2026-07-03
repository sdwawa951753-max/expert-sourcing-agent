"""Enrichment stage — gather open-web signal about an expert.

Looks for public talks (conference/keynote/YouTube), news mentions, and pulls
their most-cited works from OpenAlex. All best-effort: if search isn't
configured, we still attach whatever OpenAlex gives us.
"""
from __future__ import annotations

import os

from . import search as web
from .models import Evidence, Expert

OPENALEX = "https://api.openalex.org"


def _top_works(openalex_id: str, k: int = 4) -> list[dict]:
    import requests
    aid = openalex_id.rsplit("/", 1)[-1]
    params = {"filter": f"author.id:{aid}", "sort": "cited_by_count:desc", "per-page": k}
    mailto = os.getenv("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto
    r = requests.get(f"{OPENALEX}/works", params=params, timeout=25)
    r.raise_for_status()
    out = []
    for w in r.json().get("results", []):
        out.append({
            "title": w.get("title", ""),
            "year": w.get("publication_year"),
            "cited_by": w.get("cited_by_count", 0),
        })
    return out


def enrich(expert: Expert, provider: str | None = None) -> Evidence:
    ev = Evidence()

    if expert.openalex_id:
        try:
            ev.notable_works = _top_works(expert.openalex_id)
        except Exception:
            pass

    name = expert.name
    inst = expert.institution or ""
    talks = web.search(f'{name} {inst} keynote OR talk OR lecture', k=4, provider=provider)
    ev.talks = [t for t in talks if any(
        kw in (t["title"] + t.get("snippet", "")).lower()
        for kw in ("talk", "keynote", "lecture", "interview", "panel", "podcast", "youtube")
    )][:4]

    news = web.search(f'{name} {inst} research', k=4, provider=provider)
    ev.news = news[:3]
    return ev
