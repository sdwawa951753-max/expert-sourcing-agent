"""Expert Sourcing Agent — find, profile, and warmly reach domain experts
for AI model feedback (RLHF, evaluations, red-teaming, benchmark authoring)."""
from .models import Candidate, Contact, Evidence, Expert, OutreachDraft, Profile
from .llm import LLMClient
from .pipeline import run_candidates, run_live

__version__ = "0.1.0"
__all__ = [
    "Candidate", "Contact", "Evidence", "Expert", "OutreachDraft", "Profile",
    "LLMClient", "run_candidates", "run_live",
]
