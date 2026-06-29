# MOSAIC — Reference Implementation (local-first)

Working code for the MOSAIC paradigm described in `README.md`: agents are
**ephemeral compositions of persistent, evolvable capabilities**. The core runs
fully offline (deterministic mock LLM + hashing embedder); point it at a local
`llama.cpp` cluster for real inference. No machine-specific paths or endpoints
are hardcoded — everything goes through config / environment variables.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .            # core: pydantic, pyyaml, numpy
# optional backends, added per need:
pip install -e ".[llm]"            # httpx — talk to llama-server
pip install -e ".[retrieval]"      # qdrant-client, bm25s, flashrank
pip install -e ".[embeddings]"     # sentence-transformers
```

## Run the offline demo

```bash
python examples/demo.py     # composes an agent end-to-end, no server needed
pytest -q                   # full test suite (offline)
```

## Use it in code

```python
from mosaic import MosaicConfig, MosaicEngine
from mosaic.llm import OpenAICompatibleLLM

cfg = MosaicConfig.load("config.yaml")          # or MosaicConfig() for defaults
llm = OpenAICompatibleLLM(cfg.llm.base_url, cfg.llm.model)   # your llama-server
engine = MosaicEngine.from_config(cfg, llm=llm)

result = engine.run("Write an async fetcher with retries and tests")
print(result["agent"].prompt)                   # the composed ephemeral agent
print(result["output"])                         # model output (if execute=True)

engine.feedback(result["agent"], success=True, quality=0.9, persist=True)
```

## Point at your local cluster

`llama.cpp`'s `llama-server` exposes an OpenAI-compatible API. Copy
`config.example.yaml` to `config.yaml` (gitignored) and set the endpoint, or use
environment variables:

```bash
export MOSAIC_LLM_BASE_URL=http://<host>:<port>/v1
export MOSAIC_LLM_MODEL=<model-name>
export MOSAIC_EMBEDDER=llama-server     # use the server for embeddings too
```

For embeddings, run a `llama-server --embedding` instance and set
`embedder: llama-server` (or `sentence-transformers` for a local neural model).

## Architecture map (code ↔ whitepaper)

| Whitepaper | Module |
|---|---|
| Capability (Appendix A, Def. 2.1/2.3) | `schema.py` |
| Contextual capability embedding (§2.2) | `contextualize.py` |
| Hybrid retrieval: semantic + BM25 + RRF (§2.3) | `retrieval.py` |
| Cross-encoder rerank (§2.3, step 4) | `rerank.py` |
| Compatibility graph (§2.4) | `graph.py` |
| Agent orchestrator (§3.2) | `orchestrator.py` |
| Evolutionary optimization (§3.3) | `evolution.py` |
| End-to-end loop (§3.1) | `engine.py` |
| Capability library + persistence | `library.py` |
| LLM / embedding backends | `llm.py`, `embeddings.py` |

## Add capabilities

Drop a YAML file in `capabilities/` (see `capabilities/python_poc.yaml`). Each
entry follows the Appendix A schema; `id`s are referenced by
`compatible_capabilities` / `incompatible_capabilities` / `required_capabilities`.
Learned state (scores, synergies) is persisted separately to `data/state.json`,
so editing a capability's text never erases its learning.

## What evolved (lessons from running it for real)

Running MOSAIC continuously surfaced refinements worth recording; they also live, as a
closed self-cultivating loop, in the sibling project [Symbiont](../local-AI-Symbiont/):

- **Off-domain fallback.** When nothing in the library fits a request, force-fitting a
  code-shaped agent onto (say) a housing question produces nonsense. The composer now
  detects "no capability fits" and falls back to a plain general assistant.
- **Corrective gate + self-extension.** Before composing, the system checks whether the
  retrieved capabilities actually fit (a CRAG-style quality gate); if they don't, it
  records a *gap* and later turns that gap into a new capability it writes itself.
- **Capability curation.** A library that writes its own capabilities will also write
  weak ones. New capabilities are scored by a judge before admission and redundant ones
  pruned; generation prompts were tightened to yield *general rules*, not request-specific recipes.
- **Robust loading.** `from_dir` now ignores non-capability YAML (e.g. a rejected-
  capabilities log) instead of crashing the whole load — a real bug fixed in this reference.
- **A stop condition.** "Self-improving" needs a definition of *improved enough*: track the
  judge's score trend and the gap-discovery rate; when both flatten, declare maturity.
```
