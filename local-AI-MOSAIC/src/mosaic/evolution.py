"""Evolutionary optimization loop (§3.3).

After each agent execution, update the performance scores of the capabilities
used (Definition 2.3), strengthen or weaken their pairwise edges in the
compatibility graph, and periodically prune persistent under-performers that
have better alternatives.
"""
from __future__ import annotations

import time
from collections import defaultdict

from mosaic.agent import EphemeralAgent
from mosaic.graph import CompatibilityGraph
from mosaic.library import CapabilityLibrary

SYNERGY_STEP = 0.05
CONFLICT_STEP = 0.10


class CapabilityEvolutionEngine:
    def __init__(self, library: CapabilityLibrary, graph: CompatibilityGraph,
                 learning_rate: float = 0.1, prune_threshold: float = 0.3):
        self.library = library
        self.graph = graph
        self.alpha = learning_rate
        self.prune_threshold = prune_threshold
        self.performance_history: list[dict] = []

    def update_from_execution(self, agent: EphemeralAgent, task_success: bool,
                              quality_score: float = 1.0) -> None:
        caps = agent.capabilities_used
        for cap in caps:
            old = cap.performance_score
            new = cap.register_outcome(task_success, quality_score, self.alpha)
            self.performance_history.append({
                "capability_id": cap.id, "t": time.time(),
                "old": old, "new": new,
                "success": task_success, "quality": quality_score,
            })
        self._update_graph(caps, task_success)

        if self.performance_history and len(self.performance_history) % 100 == 0:
            self.prune_underperformers()

    def _update_graph(self, caps, success: bool) -> None:
        for i, a in enumerate(caps):
            for b in caps[i + 1:]:
                w = self.graph.get_edge_weight(a.id, b.id)
                if success:
                    a.record_synergy(b.id)
                    b.record_synergy(a.id)
                    self.graph.update_edge(a.id, b.id, min(1.0, w + SYNERGY_STEP))
                else:
                    nw = max(-1.0, w - CONFLICT_STEP)
                    self.graph.update_edge(a.id, b.id, nw)
                    if nw <= -0.5:
                        if b.id not in a.incompatible_capabilities:
                            a.incompatible_capabilities.append(b.id)
                        if a.id not in b.incompatible_capabilities:
                            b.incompatible_capabilities.append(a.id)

    def prune_underperformers(self, min_samples: int = 50) -> list[str]:
        recent = self.performance_history[-100:]
        scores: dict[str, list[float]] = defaultdict(list)
        for h in recent:
            scores[h["capability_id"]].append(h["new"])

        pruned: list[str] = []
        for cid, vals in scores.items():
            if len(vals) < min_samples:
                continue
            avg = sum(vals) / len(vals)
            if avg >= self.prune_threshold:
                continue
            cap = self.library.get(cid)
            if not cap:
                continue
            better = [a for a in self.library.find_similar(cap, by_domain=True, by_role=True)
                      if a.performance_score > avg + 0.1]
            if better:
                self.library.archive(cid)
                pruned.append(cid)
        return pruned
