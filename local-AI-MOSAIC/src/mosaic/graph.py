"""Compatibility graph (§2.4).

Directed graph encoding synergy / conflict between capabilities. Dependency-free
(dict of edges) but exposes the same surface the whitepaper sketches with
``networkx`` (add_compatibility / add_incompatibility / validate_composition /
get_edge_weight / update_edge), so a networkx backend can replace it later
without touching callers.

Edge weights live in [-1, 1]. An explicit ``conflict`` edge, or any weight
<= -0.5, is treated as a hard conflict during validation.
"""
from __future__ import annotations

from typing import Iterable, Optional

CONFLICT_THRESHOLD = -0.5


class CompatibilityGraph:
    def __init__(self) -> None:
        self._edges: dict[tuple[str, str], dict] = {}

    # --- construction ---
    def add_compatibility(self, a: str, b: str, strength: float = 0.5) -> None:
        self._merge(a, b, weight=abs(strength), type="synergy")

    def add_incompatibility(self, a: str, b: str, reason: str = "conflicting approaches") -> None:
        self._merge(a, b, weight=-1.0, type="conflict", reason=reason)

    def update_edge(self, a: str, b: str, weight: float) -> None:
        weight = max(-1.0, min(1.0, weight))
        e = self._edges.setdefault((a, b), {})
        e["weight"] = weight
        e["type"] = "conflict" if weight <= CONFLICT_THRESHOLD else "synergy"

    def _merge(self, a: str, b: str, **attrs) -> None:
        self._edges.setdefault((a, b), {}).update(attrs)

    # --- queries ---
    def get_edge_weight(self, a: str, b: str) -> float:
        e = self._edges.get((a, b)) or self._edges.get((b, a))
        return float(e["weight"]) if e and "weight" in e else 0.0

    def conflict_reason(self, a: str, b: str) -> Optional[str]:
        """Return a reason string if a and b conflict (either direction), else None."""
        for x, y in ((a, b), (b, a)):
            e = self._edges.get((x, y))
            if e and (e.get("type") == "conflict" or e.get("weight", 0.0) <= CONFLICT_THRESHOLD):
                return e.get("reason", "conflicting approaches")
        return None

    def validate_composition(self, capabilities: Iterable) -> tuple[bool, str]:
        ids = [c.id for c in capabilities]
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                reason = self.conflict_reason(a, b)
                if reason:
                    return False, f"Conflict: {a} <-> {b} ({reason})"
        return True, "Composition valid"
