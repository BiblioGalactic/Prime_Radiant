"""LLM client abstraction.

MOSAIC needs an LLM for three jobs: intent analysis, capability
contextualization, and inter-capability transitions (plus, optionally, final
task execution). All of these go through the tiny ``LLMClient`` protocol, so
the engine is agnostic to whether the model is a local llama-server, a remote
API, or a deterministic mock used in tests.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str: ...


class MockLLM:
    """Deterministic, offline client so the whole pipeline runs without a server.

    Returns small, plausible responses keyed off the prompt. Good enough to
    exercise composition end-to-end in tests and demos.
    """

    def generate(self, prompt, *, system=None, max_tokens=512, temperature=0.7):
        low = prompt.lower()
        if "transition" in low:
            return ("Having established the above, we now carry that context "
                    "forward into the next capability.")
        if "context" in low and "capabilit" in low:
            return ("Reusable capability; activates on semantically related "
                    "requests; pairs well with complementary methodologies.")
        if "json" in low or "domains" in low:
            return '{"goal": "complete the requested task", "domains": [], "complexity": "intermediate"}'
        return "OK"


class OpenAICompatibleLLM:
    """Client for any OpenAI-compatible ``/chat/completions`` endpoint.

    Works directly against a local llama.cpp ``llama-server``. The endpoint and
    model come from configuration, so no specific host or model path is baked in.
    """

    def __init__(self, base_url: str, model: str, api_key: str = "not-needed",
                 timeout: float = 120.0):
        import httpx  # imported lazily so the core has no hard dependency
        self._httpx = httpx
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def generate(self, prompt, *, system=None, max_tokens=512, temperature=0.7):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
