"""Contact stage — find PUBLIC, PROFESSIONAL contact channels only.

This tool is built for personalized, one-to-one professional outreach (the way
a recruiter or chief of staff reaches a scholar about a real opportunity). It
deliberately does NOT:
  - guess/permute private email addresses at scale
  - scrape data behind logins or paywalls
  - collect personal (non-professional) contact details

It surfaces what a scholar has themselves made public for contact: an ORCID
record, an institutional faculty page, a personal academic site. Always honor
opt-outs and applicable law — see docs/RESPONSIBLE_USE.md.
"""
from __future__ import annotations

import re

from . import search as web
from .models import Contact, Expert

# Only accept emails that look like institutional/professional addresses shown
# on a public page. This is intentionally conservative.
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.(?:edu|ac\.[a-z]{2}|org|gov)")


def _orcid_links(orcid: str | None) -> list[str]:
    if not orcid:
        return []
    return [orcid if orcid.startswith("http") else f"https://orcid.org/{orcid}"]


def find_contact(expert: Expert, provider: str | None = None) -> Contact:
    c = Contact()
    c.links = _orcid_links(expert.orcid)

    # Look for a public faculty / lab / personal page.
    hits = web.search(f'{expert.name} {expert.institution or ""} faculty OR homepage OR lab',
                      k=5, provider=provider)
    for h in hits:
        url = h.get("url", "")
        if not url:
            continue
        if any(dom in url for dom in (".edu", ".ac.", "orcid.org")) and url not in c.links:
            c.links.append(url)
        # If a public page's snippet exposes a professional email, capture it.
        m = _EMAIL_RE.search(h.get("snippet", ""))
        if m and not c.email:
            c.email = m.group(0)
            c.email_source = url

    if c.email:
        c.best_channel = "email"
    elif expert.orcid:
        c.best_channel = "orcid"
    elif c.links:
        c.best_channel = "homepage form"
    return c
