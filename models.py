"""Typed data models passed between pipeline stages.

The pipeline is a straight line:

    Expert  ->  +Evidence  ->  +Contact  ->  +Profile  ->  +Outreach  ->  +scores

Each stage enriches a `Candidate`. Keeping everything in dataclasses (rather
than loose dicts) makes the flow easy to read, easy to serialize to JSON, and
easy to test.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Expert:
    """A person discovered from an open source (OpenAlex, Nobel API, manual)."""
    name: str
    source: str = "openalex"                 # openalex | nobel | manual
    openalex_id: Optional[str] = None
    orcid: Optional[str] = None
    institution: Optional[str] = None
    country: Optional[str] = None
    works_count: int = 0
    cited_by_count: int = 0
    h_index: Optional[int] = None
    top_concepts: list[str] = field(default_factory=list)
    is_nobel_laureate: bool = False
    nobel_detail: Optional[str] = None       # e.g. "Nobel Prize in Physics, 2018"
    homepage: Optional[str] = None
    scholar_url: Optional[str] = None


@dataclass
class Evidence:
    """Public, open-web signal gathered about the expert."""
    talks: list[dict] = field(default_factory=list)         # {title,url,source}
    news: list[dict] = field(default_factory=list)          # {title,url,source}
    notable_works: list[dict] = field(default_factory=list)  # {title,year,cited_by}


@dataclass
class Contact:
    """Public, professional contact info only (see docs/RESPONSIBLE_USE.md)."""
    email: Optional[str] = None
    email_source: Optional[str] = None       # URL where it was publicly listed
    links: list[str] = field(default_factory=list)
    best_channel: Optional[str] = None        # email | homepage form | orcid


@dataclass
class Profile:
    """LLM-synthesized read on the expert and their fit for AI-feedback work."""
    summary: str = ""
    expertise: list[str] = field(default_factory=list)
    fit_for_ai_feedback: str = ""            # why they'd be valuable for RLHF/evals
    talking_points: list[str] = field(default_factory=list)
    responsiveness_notes: str = ""


@dataclass
class OutreachDraft:
    subject: str = ""
    body: str = ""
    channel: str = "email"


@dataclass
class Candidate:
    expert: Expert
    evidence: Evidence = field(default_factory=Evidence)
    contact: Contact = field(default_factory=Contact)
    profile: Profile = field(default_factory=Profile)
    outreach: Optional[OutreachDraft] = None
    scores: dict = field(default_factory=dict)  # relevance/seniority/reachability/responsiveness/fit_total

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def fit_total(self) -> float:
        return float(self.scores.get("fit_total", 0.0))
