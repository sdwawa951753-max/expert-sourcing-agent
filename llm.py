"""Thin LLM wrapper.

Uses Anthropic's Claude when `ANTHROPIC_API_KEY` is set. If no key is present
(or `mock=True`), it flips into an offline mode so the whole pipeline still runs
end-to-end for the demo — the analysis/outreach stages detect `client.mock` and
fall back to deterministic templates. That means anyone can `--demo` this repo
with zero setup, and get real Claude-authored output the moment they add a key.
"""
from __future__ import annotations

import json
import os


class LLMClient:
    def __init__(self, model: str = "claude-sonnet-4-6", mock: bool = False):
        self.model = model
        self.mock = mock
        self._client = None
        if not self.mock:
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                # No key -> degrade gracefully instead of crashing.
                self.mock = True
            else:
                from anthropic import Anthropic  # imported lazily
                self._client = Anthropic(api_key=key)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1200) -> str:
        if self.mock:
            raise RuntimeError(
                "LLMClient is in offline/mock mode; callers should branch on "
                "`client.mock` before calling complete()."
            )
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or None,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

    def complete_json(self, prompt: str, system: str = "", max_tokens: int = 1200) -> dict:
        raw = self.complete(
            prompt + "\n\nReturn ONLY valid JSON. No markdown, no commentary.",
            system,
            max_tokens,
        ).strip()
        # tolerate ```json fences if the model adds them
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
