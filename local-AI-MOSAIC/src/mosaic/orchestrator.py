"""Agent orchestrator (§3.2): compose an ephemeral agent from capabilities.

Pipeline: enforce per-role budgets -> validate compatibility (resolving
conflicts when possible) -> order by role -> generate transitions -> assemble
specification -> compress to the context budget.
"""
from __future__ import annotations

from typing import Optional

from mosaic.agent import AgentSpecification, EphemeralAgent, estimate_tokens
from mosaic.graph import CompatibilityGraph
from mosaic.intent import Intent
from mosaic.library import CapabilityLibrary
from mosaic.llm import LLMClient
from mosaic.schema import Capability, Role

# Natural reading order of roles within a composed prompt.
ROLE_ORDER = [
    Role.SYSTEM_INSTRUCTION, Role.DOMAIN_KNOWLEDGE, Role.REASONING_STRATEGY,
    Role.METHODOLOGY, Role.EXAMPLE, Role.CONSTRAINT, Role.ERROR_HANDLING,
    Role.OUTPUT_SPECIFICATION,
]

# Priority kept when compressing to the context budget (lower = more important).
COMPRESS_PRIORITY = {
    Role.SYSTEM_INSTRUCTION: 1, Role.OUTPUT_SPECIFICATION: 1,
    Role.METHODOLOGY: 2, Role.DOMAIN_KNOWLEDGE: 2, Role.REASONING_STRATEGY: 2,
    Role.CONSTRAINT: 3, Role.ERROR_HANDLING: 3, Role.EXAMPLE: 4,
}


class CompositionError(Exception):
    pass


class AgentOrchestrator:
    def __init__(self, graph: CompatibilityGraph, library: CapabilityLibrary,
                 llm: Optional[LLMClient] = None, max_context_tokens: int = 8000):
        self.graph = graph
        self.library = library
        self.llm = llm
        self.max_context = max_context_tokens
        self.transition_cache: dict[str, str] = {}
        # (min, max) instances allowed per role in a single agent.
        self.role_requirements: dict[Role, tuple[int, int]] = {
            Role.SYSTEM_INSTRUCTION: (0, 1),
            Role.METHODOLOGY: (0, 3),
            Role.EXAMPLE: (0, 3),
            Role.CONSTRAINT: (0, 2),
            Role.OUTPUT_SPECIFICATION: (0, 1),
        }

    def compose_agent(self, intent: Intent, retrieved: list[Capability],
                      user_query: str) -> EphemeralAgent:
        caps = self._expand_required(retrieved)
        caps = self._enforce_role_caps(caps)

        ok, msg = self.graph.validate_composition(caps)
        if not ok:
            caps = self._resolve_conflicts(caps)
            ok, msg = self.graph.validate_composition(caps)
            if not ok:
                raise CompositionError(f"Cannot resolve conflicts: {msg}")

        ordered = self._optimize_ordering(caps)
        transitions = self._generate_transitions(ordered)
        spec = self._assemble(ordered, transitions, user_query, intent)
        if spec.total_tokens > self.max_context:
            spec = self._compress(spec)

        return EphemeralAgent(
            specification=spec,
            capabilities_used=spec.capabilities,
            metadata={
                "capability_count": len(spec.capabilities),
                "total_tokens": spec.total_tokens,
            },
        )

    # --- pipeline steps ---
    def _expand_required(self, caps: list[Capability]) -> list[Capability]:
        """Pull in declared ``required_capabilities`` (schema dependencies)."""
        result = list(caps)
        present = {c.id for c in result}
        queue = list(caps)
        while queue:
            cap = queue.pop()
            for req_id in cap.required_capabilities:
                if req_id in present:
                    continue
                dep = self.library.get(req_id)
                if dep is not None:
                    result.append(dep)
                    present.add(req_id)
                    queue.append(dep)
        return result

    def _enforce_role_caps(self, caps: list[Capability]) -> list[Capability]:
        counts: dict[Role, int] = {}
        kept: list[Capability] = []
        for cap in sorted(caps, key=lambda c: c.performance_score, reverse=True):
            mx = self.role_requirements.get(cap.role, (0, 99))[1]
            if counts.get(cap.role, 0) < mx:
                kept.append(cap)
                counts[cap.role] = counts.get(cap.role, 0) + 1
        return kept

    def _resolve_conflicts(self, caps: list[Capability]) -> list[Capability]:
        result = list(caps)
        changed = True
        while changed:
            changed = False
            for i in range(len(result)):
                for j in range(i + 1, len(result)):
                    if self.graph.conflict_reason(result[i].id, result[j].id):
                        worse = i if result[i].performance_score <= result[j].performance_score else j
                        victim = result[worse]
                        replacement = self._find_replacement(result, victim)
                        if replacement is not None:
                            result[worse] = replacement
                        else:
                            result.pop(worse)
                        changed = True
                        break
                if changed:
                    break
        return result

    def _find_replacement(self, current: list[Capability], victim: Capability) -> Optional[Capability]:
        current_ids = {c.id for c in current}
        for cand in self.library.find_similar(victim, by_domain=True, by_role=True):
            if cand.id in current_ids:
                continue
            trial = [c for c in current if c.id != victim.id] + [cand]
            ok, _ = self.graph.validate_composition(trial)
            if ok:
                return cand
        return None

    def _optimize_ordering(self, caps: list[Capability]) -> list[Capability]:
        rank = {r: i for i, r in enumerate(ROLE_ORDER)}
        return sorted(caps, key=lambda c: rank.get(c.role, len(ROLE_ORDER)))

    def _generate_transitions(self, caps: list[Capability]) -> dict[str, str]:
        transitions: dict[str, str] = {}
        for i in range(len(caps) - 1):
            a, b = caps[i], caps[i + 1]
            key = f"{a.id}->{b.id}"
            if key in self.transition_cache:
                transitions[a.id] = self.transition_cache[key]
                continue
            text = self._default_transition(a, b)
            if self.llm is not None:
                try:
                    out = self.llm.generate(
                        "Generate a 1-2 sentence transition connecting two agent "
                        f"capabilities.\nFROM: {a.behavioral_pattern[-200:]}\n"
                        f"TO: {b.behavioral_pattern[:200]}\nTransition:",
                        max_tokens=60, temperature=0.3,
                    ).strip()
                    text = out or text
                except Exception:
                    pass
            transitions[a.id] = text
            self.transition_cache[key] = text
        return transitions

    @staticmethod
    def _default_transition(a: Capability, b: Capability) -> str:
        return (f"With the {a.role.value.replace('_', ' ')} in place, "
                f"apply the following {b.role.value.replace('_', ' ')}.")

    def _assemble(self, caps: list[Capability], transitions: dict[str, str],
                  user_query: str, intent: Intent) -> AgentSpecification:
        goal = getattr(intent, "goal", str(intent))
        system = (f"You are an ephemeral agent composed for this objective: {goal}. "
                  f"Apply the following capabilities in order, maintaining coherence.")
        return AgentSpecification(capabilities=caps, transitions=transitions,
                                  user_query=user_query, system_prompt=system)

    def _compress(self, spec: AgentSpecification) -> AgentSpecification:
        ordered = sorted(
            spec.capabilities,
            key=lambda c: (COMPRESS_PRIORITY.get(c.role, 9), -c.performance_score),
        )
        selected: list[Capability] = []
        tokens = spec.base_tokens
        for cap in ordered:
            t = estimate_tokens(cap.behavioral_pattern)
            if tokens + t <= self.max_context:
                selected.append(cap)
                tokens += t
        selected = self._optimize_ordering(selected)
        kept_ids = {c.id for c in selected}
        transitions = {k: v for k, v in spec.transitions.items() if k in kept_ids}
        return AgentSpecification(capabilities=selected, transitions=transitions,
                                  user_query=spec.user_query,
                                  system_prompt=spec.system_prompt,
                                  base_tokens=spec.base_tokens)
