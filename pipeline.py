"""Orchestration — wire the stages together.

    discover -> enrich -> contact -> analyze -> outreach -> score -> rank

`run_live` does the full open-web pipeline. `run_candidates` runs the
analysis/outreach/scoring half over already-built candidates (used by --demo,
and by anyone feeding in their own shortlist).
"""
from __future__ import annotations

from . import analyze as analyze_mod
from . import contact as contact_mod
from . import discover as discover_mod
from . import enrich as enrich_mod
from . import outreach as outreach_mod
from . import score as score_mod
from .llm import LLMClient
from .models import Candidate


def run_candidates(cands: list[Candidate], llm: LLMClient, cfg: dict,
                   field_terms: list[str], log=print) -> list[Candidate]:
    for c in cands:
        log(f"  · profiling {c.expert.name}")
        c.profile = analyze_mod.analyze(c, llm)
        c.outreach = outreach_mod.draft_outreach(c, llm, cfg.get("outreach", {}))
        c.scores = score_mod.score(c, field_terms)
    cands.sort(key=lambda c: c.fit_total, reverse=True)
    return cands


def run_live(field: str, limit: int, llm: LLMClient, cfg: dict,
             nobel_category: str | None = None, log=print) -> list[Candidate]:
    log(f"Discovering top experts in “{field}” via OpenAlex…")
    experts = discover_mod.find_experts(field, limit=limit, nobel_category=nobel_category)
    if not experts:
        log("No experts found (check the field term or your connection).")
        return []
    log(f"Found {len(experts)}. Enriching + finding contact…")

    provider = cfg.get("search", {}).get("provider")
    cands: list[Candidate] = []
    for e in experts:
        c = Candidate(expert=e)
        c.evidence = enrich_mod.enrich(e, provider=provider)
        c.contact = contact_mod.find_contact(e, provider=provider)
        cands.append(c)

    return run_candidates(cands, llm, cfg, field_terms=field.split(), log=log)
