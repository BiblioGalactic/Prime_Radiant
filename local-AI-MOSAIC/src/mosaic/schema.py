"""
MOSAIC capability schema.

Implements the capability specification from the MOSAIC whitepaper
(Appendix A) as validated Pydantic models.

A ``Capability`` is the atomic unit of MOSAIC: a reusable, context-aware
micro-agent that can be retrieved from a library and composed into an
ephemeral agent. Capabilities persist and improve; agents are transient.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, Enum):
    """Functional role a capability plays inside a composed agent."""

    SYSTEM_INSTRUCTION = "system_instruction"
    METHODOLOGY = "methodology"
    EXAMPLE = "example"
    CONSTRAINT = "constraint"
    OUTPUT_SPECIFICATION = "output_specification"
    ERROR_HANDLING = "error_handling"
    REASONING_STRATEGY = "reasoning_strategy"
    DOMAIN_KNOWLEDGE = "domain_knowledge"


class ComplexityLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Capability(BaseModel):
    """A single MOSAIC capability (micro-agent).

    Maps directly to the schema in Appendix A of the whitepaper. The
    contextual *embedding* lives in the vector index, not here; the
    optional ``contextual_text`` field lets callers carry the contextualized
    string in memory during retrieval/composition.
    """

    # --- required ---
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Role
    domain_expertise: list[str] = Field(min_length=1)
    behavioral_pattern: str = Field(min_length=1)
    performance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    version: str = "0.1.0"

    # --- composition relationships ---
    compatible_capabilities: list[str] = Field(default_factory=list)
    incompatible_capabilities: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    successful_compositions: dict[str, int] = Field(default_factory=dict)

    # --- optional metadata ---
    token_count: Optional[int] = Field(default=None, ge=0)
    language: Optional[str] = None
    framework: Optional[str] = None
    complexity_level: Optional[ComplexityLevel] = None
    last_updated: datetime = Field(default_factory=_utcnow)
    author: Optional[str] = None
    usage_count: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)

    contextual_text: Optional[str] = None

    @field_validator("domain_expertise", "tags")
    @classmethod
    def _normalize(cls, v: list[str]) -> list[str]:
        """Normalize tag-like lists to lowercase, trimmed, de-duplicated."""
        seen: dict[str, None] = {}
        for s in v:
            s = s.strip().lower()
            if s:
                seen.setdefault(s, None)
        return list(seen)

    def register_outcome(
        self,
        success: bool,
        quality: float = 1.0,
        alpha: float = 0.1,
    ) -> float:
        """Closed-loop performance update (Definition 2.3).

        ``s_{t+1} = s_t + alpha * (outcome * quality - s_t)``

        Returns the new performance score.
        """
        outcome = (1.0 if success else 0.0) * max(0.0, min(1.0, quality))
        self.performance_score += alpha * (outcome - self.performance_score)
        self.performance_score = max(0.0, min(1.0, self.performance_score))
        self.usage_count += 1
        self.last_updated = _utcnow()
        return self.performance_score

    def record_synergy(self, other_id: str) -> None:
        """Increment the co-activation counter for a successful pairing."""
        self.successful_compositions[other_id] = (
            self.successful_compositions.get(other_id, 0) + 1
        )
