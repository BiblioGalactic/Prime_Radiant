"""Hybrid capability retrieval (§2.3).

Semantic search (dense, on contextual embeddings) + lexical search (BM25) fused
via Reciprocal Rank Fusion, with metadata filtering (domain / performance) and
an optional reranker. The vector index is in-memory (numpy cosine) so the POC
runs with zero infrastructure; the same interface fronts a Qdrant backend later.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Callable, Optional

import numpy as np

from mosaic.embeddings import Embedder
from mosaic.library import CapabilityLibrary
from mosaic.schema import Capability

Reranker = Callable[[str, list[Capability]], list[Capability]]


def tokenize(text: str) -> list[str]:
    return "".join(c.lower() if c.isalnum() else " " for c in text).split()


def contextual_text(cap: Capability) -> str:
    base = cap.contextual_text or ""
    return f"{base} {cap.behavioral_pattern} {' '.join(cap.domain_expertise)} {' '.join(cap.tags)}".strip()


class BM25:
    """Minimal Okapi BM25 over a fixed corpus (dependency-free)."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = docs
        self.N = len(docs)
        self.avgdl = (sum(len(d) for d in docs) / self.N) if self.N else 0.0
        df: Counter = Counter()
        for d in docs:
            for term in set(d):
                df[term] += 1
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()}

    def scores(self, query: list[str]) -> np.ndarray:
        out = np.zeros(self.N, dtype=np.float32)
        avgdl = self.avgdl or 1.0
        for i, d in enumerate(self.docs):
            if not d:
                continue
            freqs = Counter(d)
            dl = len(d)
            s = 0.0
            for t in query:
                f = freqs.get(t, 0)
                if not f:
                    continue
                idf = self.idf.get(t, 0.0)
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / avgdl))
            out[i] = s
        return out


class HybridRetriever:
    def __init__(self, library: CapabilityLibrary, embedder: Embedder,
                 reranker: Optional[Reranker] = None, rrf_k: int = 60,
                 semantic_weight: float = 0.6, lexical_weight: float = 0.4):
        self.library = library
        self.embedder = embedder
        self.reranker = reranker
        self.rrf_k = rrf_k
        self.semantic_weight = semantic_weight
        self.lexical_weight = lexical_weight
        self.reindex()

    def reindex(self) -> None:
        self._caps = self.library.all()
        texts = [contextual_text(c) for c in self._caps]
        self._matrix = (self.embedder.embed_batch(texts) if self._caps
                        else np.zeros((0, self.embedder.dim), dtype=np.float32))
        self._bm25 = BM25([tokenize(t) for t in texts])

    def retrieve(self, intent: str, required_domains: Optional[list[str]] = None,
                 min_performance: float = 0.0, k_semantic: int = 20,
                 k_final: int = 5) -> list[Capability]:
        if not self._caps:
            return []

        # --- metadata filter (domain + performance) ---
        req = {d.lower() for d in (required_domains or [])}
        idxs = [
            i for i, c in enumerate(self._caps)
            if c.performance_score >= min_performance
            and (not req or (req & set(c.domain_expertise)))
        ]
        if not idxs:  # don't let an over-tight filter return nothing
            idxs = [i for i, c in enumerate(self._caps) if c.performance_score >= min_performance]
        if not idxs:
            idxs = list(range(len(self._caps)))

        # --- semantic ranking ---
        q = self.embedder.embed(intent)
        sims = self._matrix @ q
        sem_order = sorted(idxs, key=lambda i: float(sims[i]), reverse=True)[:k_semantic]

        # --- lexical ranking ---
        bm = self._bm25.scores(tokenize(intent))
        lex_order = sorted(idxs, key=lambda i: float(bm[i]), reverse=True)[:k_semantic]

        # --- reciprocal rank fusion ---
        fused: dict[int, float] = {}
        for rank, i in enumerate(sem_order, 1):
            fused[i] = fused.get(i, 0.0) + self.semantic_weight / (self.rrf_k + rank)
        for rank, i in enumerate(lex_order, 1):
            fused[i] = fused.get(i, 0.0) + self.lexical_weight / (self.rrf_k + rank)

        ordered = sorted(fused, key=lambda i: fused[i], reverse=True)[:max(k_final * 3, k_final)]
        candidates = [self._caps[i] for i in ordered]

        if self.reranker:
            candidates = self.reranker(intent, candidates)
        return candidates[:k_final]
