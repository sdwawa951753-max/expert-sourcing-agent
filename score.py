"""Scoring stage — a transparent, tunable ranking.

These are HEURISTICS, not predictions. They encode reasonable priors for expert
sourcing; every weight is visible and adjustable. `responsiveness` in particular
is an honest guess based on how public-facing a person appears, not a promise.
"""
from __future__ import annotations

import math

from .models import Candidate

WEIGHTS = {
    "relevance": 0.35,       # how well they match the target field
    "seniority": 0.25,       # citation impact + laureate status
    "responsiveness": 0.20,  # heuristic likelihood of a reply
    "reachability": 0.20,    # do we have a public channel to reach them
}


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def score(c: Candidate, field_terms: list[str]) -> dict:
    e, ev = c.expert, c.evidence

    terms = {t.lower() for t in field_terms}
    concept_hit = sum(1 for cpt in e.top_concepts if any(t in cpt.lower() for t in terms))
    relevance = _clamp(0.45 + 0.15 * concept_hit + 0.05 * len(ev.notable_works))

    # citations are heavy-tailed; log-scale. ~1M cites -> ~1.0
    seniority = _clamp(math.log10(e.cited_by_count + 1) / 6.0)
    if e.is_nobel_laureate:
        seniority = _clamp(seniority + 0.15)

    # public-facing people tend to be more reachable/receptive; the very most
    # famous are often harder to reach, so we damp at the extreme top.
    responsiveness = 0.30 + 0.10 * len(ev.talks) + 0.05 * len(ev.news)
    if e.cited_by_count > 250_000:
        responsiveness -= 0.15
    responsiveness = _clamp(responsiveness)

    reachability = _clamp(
        (0.6 if c.contact.email else 0.0)
        + (0.4 if (c.contact.links or c.expert.orcid) else 0.0)
    )

    parts = {
        "relevance": round(relevance, 3),
        "seniority": round(seniority, 3),
        "responsiveness": round(responsiveness, 3),
        "reachability": round(reachability, 3),
    }
    parts["fit_total"] = round(sum(WEIGHTS[k] * parts[k] for k in WEIGHTS), 3)
    return parts
