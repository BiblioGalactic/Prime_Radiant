"""Intent analysis (§3.1).

Turns a raw user request into a structured ``Intent`` (goal, inferred domains,
complexity). Works fully offline via heuristics; if an LLM is provided it is
used to refine the result, but failures fall back to the heuristic output.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from mosaic.llm import LLMClient

KNOWN_DOMAINS = [
    "python", "javascript", "async", "error_handling", "data_analysis",
    "pandas", "testing", "type_safety", "writing", "reasoning", "sql", "api",
]


@dataclass
class Intent:
    raw: str
    goal: str
    domains: list[str] = field(default_factory=list)
    complexity: str = "intermediate"


class IntentAnalyzer:
    def __init__(self, llm: Optional[LLMClient] = None, known_domains: Optional[list[str]] = None):
        self.llm = llm
        self.known = [d.lower() for d in (known_domains or KNOWN_DOMAINS)]

    def _heuristic_domains(self, text: str) -> list[str]:
        low = text.lower()
        return [d for d in self.known if d in low or d.replace("_", " ") in low]

    def analyze(self, text: str) -> Intent:
        domains = self._heuristic_domains(text)
        complexity = ("advanced" if len(text) > 200
                      else "basic" if len(text) < 60 else "intermediate")
        goal = text.strip()

        if self.llm is not None:
            try:
                resp = self.llm.generate(
                    'Extract a JSON object with keys "goal" (string), "domains" '
                    '(list of short tags) and "complexity" (basic|intermediate|advanced) '
                    f"for this request:\n{text}\nRespond with JSON only.",
                    max_tokens=150, temperature=0.0,
                )
                blob = resp[resp.find("{"): resp.rfind("}") + 1]
                data = json.loads(blob)
                goal = (data.get("goal") or goal).strip()
                extra = [d.lower() for d in data.get("domains", []) if isinstance(d, str)]
                domains = list(dict.fromkeys(domains + extra))
                complexity = data.get("complexity") or complexity
            except Exception:
                pass

        if not domains:
            domains = ["general"]
        return Intent(raw=text, goal=goal, domains=domains, complexity=complexity)
