"""Analysis stage — turn raw signal into a decision-useful profile.

Live mode asks Claude to synthesize the expert's work + open-web evidence into:
  summary, expertise[], fit_for_ai_feedback, talking_points[], responsiveness_notes

Offline/demo mode produces a deterministic template from the same structured
inputs so the pipeline runs with no key. The *prompt* below is the real product
logic — it's what you'd tune to improve output quality.
"""
from __future__ import annotations

from .llm import LLMClient
from .models import Candidate, Profile

SYSTEM = (
    "You are a senior talent researcher for an AI lab's expert network. You "
    "assess whether a scholar would be valuable for high-quality human feedback "
    "work: RLHF preference rating, expert evaluations, benchmark authoring, and "
    "red-teaming of frontier models. You are precise, evidence-grounded, and "
    "never invent facts about a person."
)


def _prompt(c: Candidate) -> str:
    e, ev = c.expert, c.evidence
    works = "\n".join(f"- {w['title']} ({w.get('year','?')}, cited {w.get('cited_by',0)}x)"
                      for w in ev.notable_works) or "- (none retrieved)"
    talks = "\n".join(f"- {t['title']} ({t['url']})" for t in ev.talks) or "- (none found)"
    return f"""Assess this scholar as a potential expert contributor to AI model
feedback and evaluation work.

NAME: {e.name}
INSTITUTION: {e.institution or 'unknown'}
NOBEL LAUREATE: {'yes — ' + (e.nobel_detail or '') if e.is_nobel_laureate else 'no'}
CITATIONS: {e.cited_by_count:,}  |  H-INDEX: {e.h_index}  |  WORKS: {e.works_count}
FIELDS: {', '.join(e.top_concepts) or 'unknown'}

MOST-CITED WORKS:
{works}

PUBLIC TALKS / MEDIA:
{talks}

Return JSON with keys:
  summary            (2-3 sentences, who they are and what they're known for)
  expertise          (list of 3-6 specific sub-areas)
  fit_for_ai_feedback(2-3 sentences: concretely why their expertise helps train/
                      evaluate AI, and what kinds of tasks they'd be strong on)
  talking_points     (list of 2-4 specific, personalized hooks for outreach —
                      reference actual work/talks, not generic flattery)
  responsiveness_notes (1-2 sentences, honest read on likelihood/route to reach
                      them, based only on how public-facing they appear)"""


def analyze(c: Candidate, llm: LLMClient) -> Profile:
    if not llm.mock:
        try:
            data = llm.complete_json(_prompt(c), system=SYSTEM, max_tokens=900)
            return Profile(
                summary=data.get("summary", ""),
                expertise=data.get("expertise", []),
                fit_for_ai_feedback=data.get("fit_for_ai_feedback", ""),
                talking_points=data.get("talking_points", []),
                responsiveness_notes=data.get("responsiveness_notes", ""),
            )
        except Exception:
            pass  # fall through to template

    # ---- offline template ----
    e, ev = c.expert, c.evidence
    areas = e.top_concepts[:4] or ["their field"]
    lead_work = ev.notable_works[0]["title"] if ev.notable_works else None
    tp = []
    if lead_work:
        tp.append(f"Reference their work \"{lead_work}\" and its relevance to evaluating model reasoning.")
    if ev.talks:
        tp.append(f"Mention their public talk: \"{ev.talks[0]['title']}\".")
    tp.append(f"Connect {areas[0]} to where frontier models currently struggle.")
    return Profile(
        summary=(f"{e.name} is a highly-cited researcher"
                 + (f" at {e.institution}" if e.institution else "")
                 + (f" and a {e.nobel_detail}" if e.is_nobel_laureate else "")
                 + f", known for work in {', '.join(areas)}."),
        expertise=areas,
        fit_for_ai_feedback=(
            f"Deep, verifiable expertise in {areas[0]} makes them well-suited to "
            "author hard evaluation items and judge model outputs where correctness "
            "requires genuine domain knowledge — exactly the feedback that improves "
            "frontier models."),
        talking_points=tp,
        responsiveness_notes=(
            "Appears public-facing (gives talks / media)." if ev.talks
            else "Best reached via a specific, well-researched note through official channels."),
    )
