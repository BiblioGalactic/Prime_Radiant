# Local Agentic Assistant Setup

I wrote this installer because repeating the same local-assistant setup on every machine was wasted time. The goal here is not to prove that an assistant is "advanced". The goal is to stand up a usable local toolchain around `llama.cpp` without rebuilding the scaffolding by hand each time.

## What it sets up

- a local LLM client,
- command execution,
- file reading and writing,
- project configuration,
- a starting point for agent-style workflows.

## Why it is an installer and not a polished app

I needed reproducibility more than product gloss. If I can recreate the environment quickly on a new machine, the script has done its job.

## What to watch carefully

- if you disable safe mode, you are accepting host command risk,
- model paths and `llama-cli` paths are still explicit and local,
- the assistant is only as useful as the model you point it to.

## Honest debt

- this setup saves time, but it does not remove the need to review what the assistant executes,
- environment drift still matters: Python, shell tools and model locations can go stale,
- "agentic" does not mean autonomous enough to trust blindly.

## Install

```bash
chmod +x setup_asistente.sh
./setup_asistente.sh
```

Run this when you want a fast local bootstrap, not when you want a sealed appliance.
