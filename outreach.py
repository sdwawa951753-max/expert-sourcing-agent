"""Outreach stage — draft a personalized note likely to earn a reply.

The principles encoded here (specificity over flattery, respect for the
recipient's time, a single low-friction ask, credible framing) are the same
ones in docs/OUTREACH_PLAYBOOK.md. Live mode hands them to Claude with the
expert's real talking points; offline mode fills a proven template.
"""
from __future__ import annotations

from .llm import LLMClient
from .models import Candidate, OutreachDraft

SYSTEM = (
    "You write short, sincere professional outreach that respects the reader's "
    "time. You NEVER use hype, mass-mail phrasing, or false urgency. You open "
    "with a specific, genuine reference to the person's own work, make one clear "
    "low-friction ask, and keep it under 130 words. You never fabricate mutual "
    "connections or claims."
)


def _prompt(c: Candidate, cfg: dict) -> str:
    tps = "\n".join(f"- {t}" for t in c.profile.talking_points) or "- (use their known field)"
    return f"""Draft a first-touch outreach email.

TO: {c.expert.name}, {c.expert.institution or ''}
THEIR SUMMARY: {c.profile.summary}
PERSONALIZATION HOOKS:
{tps}

SENDER: {cfg.get('sender_name','')}, {cfg.get('sender_role','')}
THE OPPORTUNITY: {cfg.get('offer','')}
THE ASK: {cfg.get('ask','a short intro call')}

Rules:
- Subject line: specific, 6 words max, no clickbait.
- Body: <=130 words. Open with a concrete reference to THEIR work (use a hook).
- Explain the opportunity in one or two plain sentences.
- One clear, low-friction ask. No pressure, no flattery filler.
- Warm, peer-to-peer tone. Sign as the sender.

Return JSON: {{"subject": "...", "body": "..."}}"""


def draft_outreach(c: Candidate, llm: LLMClient, cfg: dict) -> OutreachDraft:
    if not llm.mock:
        try:
            d = llm.complete_json(_prompt(c, cfg), system=SYSTEM, max_tokens=500)
            return OutreachDraft(subject=d.get("subject", ""), body=d.get("body", ""))
        except Exception:
            pass

    # ---- offline template (clean stand-in; live mode uses Claude) ----
    e, ev = c.expert, c.evidence
    last = e.name.split()[-1]
    area = (e.top_concepts or ["your field"])[0]
    if ev.notable_works:
        hook = f'your paper "{ev.notable_works[0]["title"]}"'
    elif ev.talks:
        hook = f'your talk "{ev.talks[0]["title"]}"'
    else:
        hook = f"your work on {area.lower()}"

    subject = f"{area}: shaping how frontier AI learns"
    body = (
        f"Dear Prof. {last},\n\n"
        f"I've been reading {hook}, and it's exactly the kind of rigor that "
        f"frontier AI models need more of right now.\n\n"
        f"I lead {cfg.get('sender_role','an AI expert network')}. We connect leading "
        f"researchers with AI labs that need expert human feedback to evaluate and "
        f"improve their models — {cfg.get('offer','paid, flexible, around your schedule')}.\n\n"
        f"Would you be open to {cfg.get('ask','a 20-minute intro call')} in the next couple of weeks?\n\n"
        f"Warm regards,\n{cfg.get('sender_name','[Your Name]')}\n{cfg.get('sender_role','')}"
    )
    return OutreachDraft(subject=subject, body=body, channel=c.contact.best_channel or "email")
