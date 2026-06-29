"""Offline proof-of-concept demo (no server required).

Runs the full MOSAIC loop with the deterministic MockLLM and the hashing
embedder, so it works anywhere. To run against your local cluster instead,
build the engine with an OpenAICompatibleLLM and set embedder: llama-server
in config.yaml.

    python examples/demo.py
"""
from __future__ import annotations

from pathlib import Path

from mosaic.config import MosaicConfig
from mosaic.engine import MosaicEngine
from mosaic.llm import MockLLM


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg = MosaicConfig(
        capabilities_dir=str(root / "capabilities"),
        state_path=str(root / "data" / "state.json"),
    )
    engine = MosaicEngine.from_config(cfg, llm=MockLLM())

    request = ("Write an async Python function that fetches many URLs with "
               "robust error handling, and add tests for it.")

    intent, agent = engine.compose(request)
    print("REQUEST  :", request)
    print("GOAL     :", intent.goal)
    print("DOMAINS  :", intent.domains, "| complexity:", intent.complexity)
    print("COMPOSED :", [c.id for c in agent.capabilities_used])
    print("TOKENS   :", agent.metadata["total_tokens"])
    print("-" * 64)
    print(agent.prompt)
    print("-" * 64)

    before = {c.id: round(c.performance_score, 3) for c in agent.capabilities_used}
    engine.feedback(agent, success=True, quality=0.9)
    after = {c.id: round(c.performance_score, 3) for c in agent.capabilities_used}
    print("SCORES   :", before, "->", after)


if __name__ == "__main__":
    main()
