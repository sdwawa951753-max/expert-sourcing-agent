"""Discovery stage.

Finds candidate experts in a field using OpenAlex (free, open, no API key) and
can pull / cross-reference Nobel laureates via the official Nobel Prize API.

OpenAlex docs:  https://docs.openalex.org
Nobel API:      https://api.nobelprize.org/2.1/laureates
"""
from __future__ import annotations

import os
from typing import Optional

from .models import Expert

OPENALEX = "https://api.openalex.org"
NOBEL = "https://api.nobelprize.org/2.1/laureates"

NOBEL_CATEGORIES = {
    "physics": "phy", "chemistry": "che", "medicine": "med",
    "economics": "eco", "literature": "lit", "peace": "pea",
}


def _get(url: str, params: dict) -> dict:
    import requests
    mailto = os.getenv("OPENALEX_MAILTO")
    if mailto and "openalex.org" in url:
        params = {**params, "mailto": mailto}   # OpenAlex "polite pool"
    r = requests.get(url, params=params, timeout=25)
    r.raise_for_status()
    return r.json()


def resolve_concept(field: str) -> tuple[Optional[str], Optional[str]]:
    """Map a free-text field to an OpenAlex concept id + canonical name."""
    data = _get(f"{OPENALEX}/concepts", {"search": field, "per-page": 1})
    results = data.get("results", [])
    if not results:
        return None, None
    return results[0]["id"], results[0]["display_name"]


def _author_to_expert(a: dict) -> Expert:
    stats = a.get("summary_stats", {}) or {}
    # institution: newer OpenAlex uses last_known_institutions (list)
    inst = None
    country = None
    insts = a.get("last_known_institutions") or []
    if insts:
        inst = insts[0].get("display_name")
        country = insts[0].get("country_code")
    elif a.get("last_known_institution"):
        inst = a["last_known_institution"].get("display_name")
        country = a["last_known_institution"].get("country_code")
    return Expert(
        name=a.get("display_name", "Unknown"),
        source="openalex",
        openalex_id=a.get("id"),
        orcid=a.get("orcid"),
        institution=inst,
        country=country,
        works_count=a.get("works_count", 0),
        cited_by_count=a.get("cited_by_count", 0),
        h_index=stats.get("h_index"),
        top_concepts=[c["display_name"] for c in (a.get("x_concepts") or [])[:6]],
    )


def find_experts(field: str, limit: int = 10, nobel_category: Optional[str] = None) -> list[Expert]:
    """Top-cited living-scholarship candidates in `field`, ranked by citations."""
    cid, cname = resolve_concept(field)
    if not cid:
        return []
    data = _get(
        f"{OPENALEX}/authors",
        {"filter": f"x_concepts.id:{cid}", "sort": "cited_by_count:desc", "per-page": limit},
    )
    experts = [_author_to_expert(a) for a in data.get("results", [])]

    # Optionally flag which of them are Nobel laureates in a given category.
    if nobel_category:
        laureate_names = {n.lower() for n in laureate_names_for(nobel_category)}
        for e in experts:
            if e.name.lower() in laureate_names:
                e.is_nobel_laureate = True
                e.nobel_detail = f"Nobel Prize ({nobel_category.title()})"
    return experts


def laureate_names_for(category: str, limit: int = 400) -> list[str]:
    code = NOBEL_CATEGORIES.get(category.lower(), category)
    try:
        data = _get(NOBEL, {"nobelPrizeCategory": code, "limit": limit})
    except Exception:
        return []
    names = []
    for lau in data.get("laureates", []):
        known = lau.get("knownName") or lau.get("fullName") or {}
        name = known.get("en") if isinstance(known, dict) else None
        if name:
            names.append(name)
    return names


def find_laureates(category: str, limit: int = 25) -> list[Expert]:
    """Pull Nobel laureates directly (e.g. to seed a shortlist of the very top)."""
    code = NOBEL_CATEGORIES.get(category.lower(), category)
    data = _get(NOBEL, {"nobelPrizeCategory": code, "limit": limit, "sort": "desc"})
    out: list[Expert] = []
    for lau in data.get("laureates", []):
        known = lau.get("knownName") or lau.get("fullName") or {}
        name = known.get("en") if isinstance(known, dict) else None
        if not name:
            continue
        prizes = lau.get("nobelPrizes", [])
        detail = None
        if prizes:
            yr = prizes[0].get("awardYear")
            detail = f"Nobel Prize in {category.title()}, {yr}"
        out.append(Expert(name=name, source="nobel", is_nobel_laureate=True, nobel_detail=detail))
    return out
