"""Ephemeral agent representation.

An ``AgentSpecification`` is the assembled, ordered set of capabilities plus the
transitions and system framing. An ``EphemeralAgent`` wraps it with the
capabilities actually used and execution metadata. Agents exist only for the
duration of a task; capabilities persist.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from mosaic.schema import Capability


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token); avoids a tokenizer dependency."""
    return max(1, len(text) // 4)


@dataclass
class AgentSpecification:
    capabilities: list[Capability]
    transitions: dict[str, str]
    user_query: str
    system_prompt: str
    base_tokens: int = 200

    @property
    def total_tokens(self) -> int:
        body = sum(estimate_tokens(c.behavioral_pattern) for c in self.capabilities)
        trans = sum(estimate_tokens(t) for t in self.transitions.values())
        return self.base_tokens + body + trans

    def render(self) -> str:
        parts: list[str] = [self.system_prompt, ""]
        for i, cap in enumerate(self.capabilities):
            parts.append(cap.behavioral_pattern.strip())
            transition = self.transitions.get(cap.id)
            if transition and i < len(self.capabilities) - 1:
                parts.append(transition.strip())
        parts += ["", f"User request: {self.user_query}"]
        return "\n\n".join(p for p in parts if p)


@dataclass
class EphemeralAgent:
    specification: AgentSpecification
    capabilities_used: list[Capability]
    metadata: dict = field(default_factory=dict)

    @property
    def prompt(self) -> str:
        return self.specification.render()
