"""End-to-end and unit tests for the MOSAIC reference implementation.

Run: pytest -q   (everything is offline; no server needed)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mosaic.agent import AgentSpecification, estimate_tokens
from mosaic.config import MosaicConfig
from mosaic.embeddings import HashingEmbedder
from mosaic.engine import MosaicEngine
from mosaic.evolution import CapabilityEvolutionEngine
from mosaic.graph import CompatibilityGraph
from mosaic.intent import IntentAnalyzer
from mosaic.library import CapabilityLibrary
from mosaic.llm import MockLLM
from mosaic.orchestrator import AgentOrchestrator, CompositionError
from mosaic.retrieval import HybridRetriever
from mosaic.schema import Capability, ComplexityLevel, Role

CAPS_DIR = Path(__file__).resolve().parents[1] / "capabilities"


def cap(cid, role, domains, behavior="do the thing", score=0.8, **kw):
    return Capability(id=cid, role=role, domain_expertise=domains,
                      behavioral_pattern=behavior, performance_score=score, **kw)


# --- schema ---
def test_capability_normalizes_and_evolves():
    c = cap("c1", Role.METHODOLOGY, ["Python", "  Async ", "python"])
    assert c.domain_expertise == ["python", "async"]          # lowercased + deduped
    s0 = c.performance_score
    s1 = c.register_outcome(True, 1.0)
    assert s1 > s0 and c.usage_count == 1
    for _ in range(50):
        c.register_outcome(False, 1.0)
    assert 0.0 <= c.performance_score <= 1.0                   # stays bounded


def test_capability_requires_domain():
    with pytest.raises(Exception):
        Capability(role=Role.EXAMPLE, domain_expertise=[], behavioral_pattern="x")


# --- graph ---
def test_graph_detects_conflict():
    g = CompatibilityGraph()
    g.add_incompatibility("a", "b", "async vs sync")
    a, b, c = cap("a", Role.METHODOLOGY, ["x"]), cap("b", Role.METHODOLOGY, ["x"]), cap("c", Role.EXAMPLE, ["x"])
    ok, _ = g.validate_composition([a, b])
    assert not ok
    ok, _ = g.validate_composition([a, c])
    assert ok


def test_graph_edge_weight_updates():
    g = CompatibilityGraph()
    g.update_edge("a", "b", 0.6)
    assert g.get_edge_weight("a", "b") == pytest.approx(0.6)
    assert g.get_edge_weight("b", "a") == pytest.approx(0.6)   # symmetric lookup


# --- retrieval ---
def test_retrieval_prefers_relevant_capability():
    lib = CapabilityLibrary([
        cap("async", Role.METHODOLOGY, ["async", "python"], "handle async errors with gather"),
        cap("write", Role.METHODOLOGY, ["writing"], "write a clear essay"),
    ])
    r = HybridRetriever(lib, HashingEmbedder(256))
    got = r.retrieve("python asyncio error handling", k_final=1)
    assert got and got[0].id == "async"


def test_retrieval_metadata_filter():
    lib = CapabilityLibrary([
        cap("hi", Role.METHODOLOGY, ["python"], score=0.9),
        cap("lo", Role.METHODOLOGY, ["python"], score=0.2),
    ])
    r = HybridRetriever(lib, HashingEmbedder(256))
    got = r.retrieve("python", min_performance=0.5, k_final=5)
    assert {c.id for c in got} == {"hi"}


# --- orchestrator ---
def test_orchestrator_resolves_conflict_and_orders():
    a = cap("a", Role.METHODOLOGY, ["x"], score=0.9)
    b = cap("b", Role.METHODOLOGY, ["x"], score=0.4)       # weaker -> dropped on conflict
    sysc = cap("s", Role.SYSTEM_INSTRUCTION, ["x"], score=0.9)
    lib = CapabilityLibrary([a, b, sysc])
    g = CompatibilityGraph()
    g.add_incompatibility("a", "b")
    orch = AgentOrchestrator(g, lib, llm=MockLLM())
    intent = IntentAnalyzer().analyze("x task")
    agent = orch.compose_agent(intent, [sysc, a, b], "do x")
    ids = [c.id for c in agent.capabilities_used]
    assert "b" not in ids and "a" in ids
    assert ids[0] == "s"                                   # system instruction first


def test_orchestrator_enforces_role_budget():
    sys1 = cap("s1", Role.SYSTEM_INSTRUCTION, ["x"], score=0.9)
    sys2 = cap("s2", Role.SYSTEM_INSTRUCTION, ["x"], score=0.5)
    lib = CapabilityLibrary([sys1, sys2])
    orch = AgentOrchestrator(CompatibilityGraph(), lib, llm=MockLLM())
    intent = IntentAnalyzer().analyze("x")
    agent = orch.compose_agent(intent, [sys1, sys2], "x")
    roles = [c.role for c in agent.capabilities_used]
    assert roles.count(Role.SYSTEM_INSTRUCTION) == 1       # at most one system instruction


def test_compress_to_budget():
    caps = [cap(f"c{i}", Role.METHODOLOGY, ["x"], "word " * 200) for i in range(5)]
    spec = AgentSpecification(caps, {}, "q", "sys", base_tokens=10)
    orch = AgentOrchestrator(CompatibilityGraph(), CapabilityLibrary(caps), max_context_tokens=120)
    smaller = orch._compress(spec)
    assert smaller.total_tokens <= 120 and len(smaller.capabilities) < 5


# --- evolution ---
def test_evolution_updates_scores_and_graph():
    a = cap("a", Role.METHODOLOGY, ["x"], score=0.5)
    b = cap("b", Role.EXAMPLE, ["x"], score=0.5)
    lib = CapabilityLibrary([a, b])
    g = CompatibilityGraph()
    ev = CapabilityEvolutionEngine(lib, g)
    from mosaic.agent import EphemeralAgent
    agent = EphemeralAgent(AgentSpecification([a, b], {}, "q", "s"), [a, b])
    ev.update_from_execution(agent, task_success=True, quality_score=1.0)
    assert a.performance_score > 0.5
    assert g.get_edge_weight("a", "b") > 0                 # synergy strengthened
    assert a.successful_compositions.get("b") == 1


# --- end to end ---
def test_engine_end_to_end_offline():
    cfg = MosaicConfig(capabilities_dir=str(CAPS_DIR), state_path="/tmp/mosaic_state.json")
    engine = MosaicEngine.from_config(cfg, llm=MockLLM())
    result = engine.run("write an async python function with error handling and tests",
                        execute=True)
    agent = result["agent"]
    assert agent.capabilities_used                          # something was composed
    assert result["output"]                                 # mock produced output
    # no conflicting pair survived composition
    ids = [c.id for c in agent.capabilities_used]
    assert not ("meth-async-errors" in ids and "meth-sync-simple" in ids)
    # feedback raises scores and keeps the index consistent
    engine.feedback(agent, success=True, quality=0.9)
    assert all(0.0 <= c.performance_score <= 1.0 for c in engine.library)


def test_estimate_tokens_monotonic():
    assert estimate_tokens("a" * 4) <= estimate_tokens("a" * 40)


# --- contextualization (§2.2) ---
def test_contextualizer_populates_and_caches(tmp_path):
    from mosaic.contextualize import Contextualizer
    lib = CapabilityLibrary([
        cap("a", Role.METHODOLOGY, ["python"]),
        cap("b", Role.EXAMPLE, ["async"]),
    ])
    cache = tmp_path / "ctx.json"
    ctx = Contextualizer(MockLLM(), cache_path=str(cache))
    ctx.apply(lib)
    assert all(c.contextual_text for c in lib)   # every capability got context
    assert cache.exists()                         # cache persisted
    # second run loads from cache without error
    Contextualizer(MockLLM(), cache_path=str(cache)).apply(lib)


# --- required-capability expansion ---
def test_orchestrator_expands_required_dependencies():
    main = cap("main", Role.METHODOLOGY, ["x"], required_capabilities=["dep"])
    dep = cap("dep", Role.EXAMPLE, ["x"])
    lib = CapabilityLibrary([main, dep])
    orch = AgentOrchestrator(CompatibilityGraph(), lib, llm=MockLLM())
    intent = IntentAnalyzer().analyze("x")
    agent = orch.compose_agent(intent, [main], "x")     # only 'main' retrieved
    assert "dep" in [c.id for c in agent.capabilities_used]


# --- reranker ---
def test_lexical_reranker_orders_by_overlap():
    from mosaic.rerank import LexicalReranker
    a = cap("a", Role.METHODOLOGY, ["python"], "async error handling with gather")
    b = cap("b", Role.METHODOLOGY, ["writing"], "compose a persuasive essay")
    ranked = LexicalReranker()("async error handling", [b, a])
    assert ranked[0].id == "a"


# --- real OpenAI-compatible client (parsing, no network) ---
def test_openai_compatible_client_parses_response():
    from mosaic.llm import OpenAICompatibleLLM

    class FakeResp:
        def raise_for_status(self):
            return None
        def json(self):
            return {"choices": [{"message": {"content": "  hello world  "}}]}

    class FakeHttpx:
        def post(self, *a, **k):
            return FakeResp()

    client = OpenAICompatibleLLM.__new__(OpenAICompatibleLLM)
    client._httpx = FakeHttpx()
    client.base_url, client.model, client.api_key, client.timeout = "http://x/v1", "m", "k", 1.0
    assert client.generate("hi") == "hello world"
