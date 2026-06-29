"""Contextual capability embedding (§2.2) - the namesake step of MOSAIC.

Instead of embedding a raw prompt fragment, we embed a model-written description
of how the capability functions *within the wider library*: its purpose, when it
activates, what it pairs with, and which query patterns should retrieve it. This
compositional context is what makes retrieval aware of a capability's role in an
assembled agent rather than just its surface text.

Generated contexts are cached by ``(id, version)`` because (re)generation is the
dominant cost; the cache lives in a local JSON file.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from mosaic.llm import LLMClient
from mosaic.library import CapabilityLibrary
from mosaic.schema import Capability

CONTEXT_PROMPT = """<capability_library>
Purpose: {purpose}
Total Capabilities: {size}
Domains: {domains}
</capability_library>

<capability>
ID: {id}
Role: {role}
Domain: {domain}
Behavior: {behavior}
Compatible With: {compatible}
Performance: {score:.2f}
</capability>

Task: Provide a 50-100 token context situating this capability within the library.
Cover: (1) its primary function, (2) typical activation scenarios, (3) capabilities
it pairs well with, (4) query patterns that should retrieve it.
Respond ONLY with the context text."""


class Contextualizer:
    def __init__(self, llm: LLMClient, cache_path: Optional[str | Path] = None):
        self.llm = llm
        self.cache_path = Path(cache_path) if cache_path else None
        self._cache: dict[str, str] = {}
        if self.cache_path and self.cache_path.exists():
            try:
                self._cache = json.loads(self.cache_path.read_text())
            except Exception:
                self._cache = {}

    def _library_context(self, library: CapabilityLibrary) -> dict:
        domains = sorted({d for c in library for d in c.domain_expertise})
        return {
            "purpose": "Composable library of reusable agent capabilities",
            "size": len(library),
            "domains": ", ".join(domains),
        }

    def contextualize(self, cap: Capability, lib_ctx: dict) -> str:
        key = f"{cap.id}@{cap.version}"
        if key in self._cache:
            return self._cache[key]
        prompt = CONTEXT_PROMPT.format(
            purpose=lib_ctx["purpose"], size=lib_ctx["size"], domains=lib_ctx["domains"],
            id=cap.id, role=cap.role.value, domain=", ".join(cap.domain_expertise),
            behavior=cap.behavioral_pattern.strip()[:400],
            compatible=", ".join(cap.compatible_capabilities) or "none",
            score=cap.performance_score,
        )
        try:
            ctx = self.llm.generate(prompt, max_tokens=150, temperature=0.0).strip()
        except Exception:
            ctx = ""
        if not ctx:  # fallback keeps retrieval working even without an LLM
            ctx = f"Capability for {', '.join(cap.domain_expertise)} ({cap.role.value})."
        self._cache[key] = ctx
        return ctx

    def apply(self, library: CapabilityLibrary) -> None:
        """Populate ``contextual_text`` for every capability, then persist cache."""
        lib_ctx = self._library_context(library)
        for cap in library:
            cap.contextual_text = self.contextualize(cap, lib_ctx)
        self.save()

    def save(self) -> None:
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self._cache, indent=2))
