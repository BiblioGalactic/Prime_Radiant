"""Optional rerankers for the final retrieval stage (§2.3, step 4).

The whitepaper reranks fused candidates with a cross-encoder. We expose that as
a pluggable hook so the core stays dependency-free:

* ``LexicalReranker``   - zero-dep query-overlap reranker (stand-in).
* ``FlashRankReranker`` - real cross-encoder via FlashRank (optional dep).
"""
from __future__ import annotations

from mosaic.retrieval import tokenize
from mosaic.schema import Capability


class LexicalReranker:
    """Re-sort candidates by Jaccard overlap with the query terms."""

    def __call__(self, query: str, caps: list[Capability]) -> list[Capability]:
        q = set(tokenize(query))

        def score(c: Capability) -> float:
            doc = set(tokenize(c.behavioral_pattern + " " + " ".join(c.domain_expertise)))
            union = len(q | doc)
            return (len(q & doc) / union) if union else 0.0

        return sorted(caps, key=score, reverse=True)


class FlashRankReranker:
    """Cross-encoder reranker via FlashRank (install the 'retrieval' extra)."""

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        from flashrank import Ranker, RerankRequest
        self._ranker = Ranker(model_name=model_name)
        self._request = RerankRequest

    def __call__(self, query: str, caps: list[Capability]) -> list[Capability]:
        passages = [{"id": i, "text": c.behavioral_pattern} for i, c in enumerate(caps)]
        ranked = self._ranker.rerank(self._request(query=query, passages=passages))
        return [caps[r["id"]] for r in ranked]


def build_reranker(config):
    kind = getattr(config, "reranker", "none")
    if kind == "lexical":
        return LexicalReranker()
    if kind == "flashrank":
        return FlashRankReranker()
    return None
