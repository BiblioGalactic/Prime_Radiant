"""Embedding backends for contextual capability retrieval (§2.2).

Three implementations behind one ``Embedder`` protocol:

* ``HashingEmbedder``      - deterministic, dependency-free, runs offline.
* ``SentenceTransformerEmbedder`` - local neural embeddings (optional dep).
* ``LlamaServerEmbedder``  - embeddings via an OpenAI-compatible endpoint.

The hashing embedder is the default so the entire MOSAIC loop is reproducible
out of the box; swap in a neural backend for production-quality semantics.
"""
from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Embedder(Protocol):
    dim: int
    def embed(self, text: str) -> np.ndarray: ...
    def embed_batch(self, texts: list[str]) -> np.ndarray: ...


class HashingEmbedder:
    """Hashed bag-of-words+trigrams projected to a fixed-dim unit vector."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _tokens(self, text: str) -> list[str]:
        words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
        toks = list(words)
        for w in words:
            for i in range(len(w) - 2):
                toks.append(w[i:i + 3])
        return toks or ["<empty>"]

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for tok in self._tokens(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0 if (h >> 8) & 1 else -1.0
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self.embed(t) for t in texts])


class SentenceTransformerEmbedder:
    """Local neural embeddings via sentence-transformers (optional dependency)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> np.ndarray:
        return np.asarray(
            self._model.encode([text], normalize_embeddings=True)[0], dtype=np.float32
        )

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.asarray(
            self._model.encode(list(texts), normalize_embeddings=True), dtype=np.float32
        )


class LlamaServerEmbedder:
    """Embeddings via an OpenAI-compatible ``/embeddings`` endpoint.

    Pair with ``llama-server --embedding``. Endpoint/model are configurable.
    """

    def __init__(self, base_url: str, model: str = "local-embedding",
                 api_key: str = "not-needed", timeout: float = 120.0):
        import httpx
        self._httpx = httpx
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.dim = int(len(self.embed("dimension probe")))

    def embed(self, text: str) -> np.ndarray:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, getattr(self, "dim", 0)), dtype=np.float32)
        resp = self._httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": list(texts)},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        arr = np.asarray([d["embedding"] for d in resp.json()["data"]], dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms


def build_embedder(config) -> Embedder:
    """Construct the embedder named in ``config.embedder``."""
    kind = config.embedder
    if kind == "sentence-transformers":
        return SentenceTransformerEmbedder()
    if kind == "llama-server":
        base = config.llm.embedding_base_url or config.llm.base_url
        return LlamaServerEmbedder(base, config.llm.embedding_model,
                                   config.llm.api_key, config.llm.timeout)
    return HashingEmbedder(config.embedding_dim)
