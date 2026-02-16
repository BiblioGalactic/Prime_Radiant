# 🦞🔬 OpenClaw Deep Dive — From Installation to System Prompt Surgery

> **What happens when you stop trusting the magic and start reading the source code.**

A practical, honest guide to installing OpenClaw with local models, understanding its internal architecture, and learning what to keep, what to cut, and what to build yourself.

---

## 📋 Table of Contents

1. [What Is OpenClaw, Really?](#what-is-openclaw-really)
2. [Security Assessment](#security-assessment)
3. [Installation with Local Models](#installation-with-local-models)
4. [The System Prompt — Anatomy of a Monster](#the-system-prompt--anatomy-of-a-monster)
5. [Model Compatibility Matrix](#model-compatibility-matrix)
6. [What Works, What Doesn't, What's Overkill](#what-works-what-doesnt-whats-overkill)
7. [Ideas Worth Stealing](#ideas-worth-stealing)
8. [Ideas Worth Ignoring](#ideas-worth-ignoring)
9. [Building Your Own Lightweight Alternative](#building-your-own-lightweight-alternative)
10. [Conclusion](#conclusion)

---

## What Is OpenClaw, Really?

OpenClaw (formerly Clawdbot/Moltbot) is an open-source self-hosted AI assistant that sits between LLMs and your messaging channels (WhatsApp, Telegram, Discord, Signal, iMessage). Created by Peter Steinberger (PSPDFKit founder) in November 2025.

**What it actually does:** receives messages → injects a massive system prompt → sends everything to an LLM → executes tool calls from the response → routes the reply back to your channel.

**What it is NOT:** magic. The "agentic" capabilities depend entirely on the model's ability to handle function calling. With Claude Opus (200k context, native tool use), it works beautifully. With a local 7-8B model, it struggles.

**Repository:** `github.com/openclaw/openclaw` (~191k stars, TypeScript/Node.js)

---

## Security Assessment

### Known Vulnerabilities

- **CVE-2026-25253 (CVSS 8.8):** Remote code execution via single-click attack. Visiting a malicious webpage could steal your auth token, connect to your instance, disable the sandbox, and execute arbitrary commands. Patched in v2026.1.29.
- **42,665+ exposed instances** found with weak or no authentication, leaked API keys, and backdoor exploits.

### Architectural Concern

The security defenses (sandbox, command approvals) are managed via the same API that controls the agent. An attacker doesn't need to trick the LLM — they can simply use the API to disable safety features directly. This is a **design flaw**, not just a bug.

### Recommendation

Wait for the project to mature. For now, **clone and read the code** — don't give it shell access or connect it to personal messaging channels.

---

## Installation with Local Models

### Prerequisites

- Node.js ≥ 22
- llama.cpp compiled (with `llama-server`)
- A GGUF model file (we recommend Qwen3-8B for OpenClaw)

### Step 1: Install OpenClaw

```bash
npm install -g openclaw
openclaw onboard
```

During onboard:
- **Mode:** QuickStart
- **Provider:** Anthropic (or Skip — we'll configure local later)
- **Channel:** Telegram (safest for testing) or Skip
- **Skills:** `summarize`, `model-usage`, `github` (minimal set)
- **Hooks:** `session-memory` only
- **Hatch:** TUI (terminal interface)

### Step 2: Start Your Local Model Server

**Critical: Use Qwen3-8B, not Mistral 7B v0.1**

Mistral 7B v0.1 fails because:
- Only 8k real context (OpenClaw needs 16k minimum)
- No native function calling support
- Jinja template errors with tool calls

```bash
# ✅ This works
$HOME/modelo/llama.cpp/build/bin/llama-server \
  -m /path/to/Qwen3-8B-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --jinja \
  --reasoning-format none \
  -c 16384

# ❌ This does NOT work well with OpenClaw
$HOME/modelo/llama.cpp/build/bin/llama-server \
  -m /path/to/mistral-7b-instruct-v0.1.Q6_K.gguf \
  --host 127.0.0.1 \
  --port 8080
```

**Why `--reasoning-format none`?** Qwen3's Jinja template has a bug where it calls `.lstrip()` on a null `reasoning_content` field when OpenClaw sends tool calls. Disabling reasoning mode prevents this.

### Step 3: Configure OpenClaw for Local Model

Edit `~/.openclaw/openclaw.json` — replace the entire file:

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "llamacpp": {
        "baseUrl": "http://127.0.0.1:8080/v1",
        "apiKey": "not-needed",
        "api": "openai-completions",
        "models": [
          {
            "id": "llamacpp/qwen3-8b",
            "name": "qwen3-8b",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0, "output": 0,
              "cacheRead": 0, "cacheWrite": 0
            },
            "contextWindow": 32768,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "llamacpp/qwen3-8b"
      },
      "workspace": "~/.openclaw/workspace"
    }
  }
}
```

> **Note:** Include your full config (gateway, channels, hooks, etc.) alongside this. The key additions are `models.providers.llamacpp` and `agents.defaults.model.primary`.

### Step 4: Restart and Test

```bash
# Terminal 1: Gateway
openclaw gateway --force
# Look for: [gateway] agent model: llamacpp/qwen3-8b

# Terminal 2: Chat
openclaw tui
```

### Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `credit balance too low` | Still using Anthropic as default | Set `agents.defaults.model.primary` |
| `tools param requires --jinja` | llama-server missing flag | Add `--jinja` to server command |
| `context window too small (8192)` | Model ctx < 16k minimum | Set `contextWindow: 32768` in config |
| `.lstrip() on null` | Qwen3 reasoning template bug | Add `--reasoning-format none` |
| `config set` errors | OpenClaw needs full object, not incremental | Edit JSON directly with TextEdit |
| `openclaw doctor --fix` overwrites config | Doctor resets changes | Don't run doctor after manual edits |

---

## The System Prompt — Anatomy of a Monster

### Where It Lives

```
src/agents/system-prompt.ts    # 651 lines of TypeScript
```

### What It Builds (in order)

The function `buildAgentSystemPrompt()` at line 164 assembles these sections:

```
 1. Identity          → "You are a personal assistant running inside OpenClaw"
 2. Tooling           → Full list of 20+ available tools with descriptions
 3. Tool Call Style   → When to narrate vs. execute silently
 4. Safety            → No self-replication, no power-seeking, pause on conflicts
 5. CLI Reference     → OpenClaw subcommands the agent can use
 6. Self-Update       → How to update itself (only on user request)
 7. Skills            → XML-structured plugin list with descriptions + file paths
 8. Memory Recall     → How to search and cite from memory files
 9. Model Aliases     → Alternative model names
10. Workspace         → Working directory path
11. Sandbox           → Sandbox configuration (if enabled)
12. Workspace Files   → "These files are injected below in Project Context"
13. Project Context   → SOUL.md + AGENTS.md + USER.md + TOOLS.md + IDENTITY.md
                        + HEARTBEAT.md + BOOTSTRAP.md (ALL injected verbatim)
14. Reply Tags        → [[reply_to_current]] syntax
15. Messaging         → Channel routing rules
16. Voice (TTS)       → Text-to-speech configuration
17. Documentation     → Where to find docs
18. Date & Time       → Current timezone
19. Group Chat        → Context for group conversations
20. Reactions         → Emoji reaction guidelines
21. Reasoning Format  → Thinking mode configuration
22. Silent Replies    → NO_REPLY token rules
23. Heartbeats        → HEARTBEAT_OK protocol
24. Runtime           → OS, model, host, shell, channel info
```

### The Cost

With all workspace files injected, the system prompt consumes **6,000–8,000+ tokens** before the user says a single word.

| Model | Context Window | System Prompt % | Remaining for Conversation |
|-------|---------------|-----------------|---------------------------|
| Claude Opus | 200,000 | ~4% | ~192,000 tokens |
| Qwen3-8B | 32,768 | ~25% | ~24,000 tokens |
| Mistral 7B v0.1 | 8,192 | ~80% | ~1,500 tokens ❌ |

### Three Prompt Modes

Line 10-12 reveals OpenClaw has built-in modes:

```typescript
// "full": All sections (default, for main agent)
// "minimal": Reduced sections (Tooling, Workspace, Runtime) — for subagents
// "none": Just basic identity line, no sections
```

They already know it's too much. The `"minimal"` mode exists for subagents that don't need 24 sections of instructions.

### The Personality Injection

```typescript
// Line 564-565
"If SOUL.md is present, embody its persona and tone."
"Avoid stiff, generic replies; follow its guidance unless higher-priority instructions override it."
```

This is how OpenClaw overwrites model identity. The model doesn't know it's "OpenClaw" — the system prompt tells it to be OpenClaw. Any model will comply. With small models, this identity is fragile and can break after a few turns.

---

## Model Compatibility Matrix

Tested during this deep dive:

| Model | Size | Tool Calling | Context | OpenClaw Compatible | Notes |
|-------|------|-------------|---------|-------------------|-------|
| Qwen3-8B Q4 | 4.7GB | ✅ Native | 32k | ✅ Works | Best option for local |
| Ministral-8B Q8 | 8.0GB | ✅ Native | 32k | ✅ Should work | Heavier, similar quality |
| Mistral 7B v0.1 Q6 | 5.6GB | ❌ None | 8k | ❌ Fails | Context too small, no tools |
| Hermes-2-Pro Q5 | 7.1GB | ⚠️ Partial | 4k | ⚠️ Untested | Old format, may not match |
| Llama 3.1 70B Q4 | 40GB | ✅ Native | 128k | ✅ Overkill | Too slow for interactive use |
| DeepSeek Coder 6.7B | 6.7GB | ❌ None | 4k | ❌ Fails | Code-only, no tool support |

**Minimum requirements for OpenClaw:** 16k+ context, native function calling support, Jinja template compatibility.

---

## What Works, What Doesn't, What's Overkill

### ✅ Works Well
- Basic chat via TUI with local models (Qwen3-8B)
- Personality injection via SOUL.md
- Session memory hook (saves context between sessions)
- Gateway hot-reload on config changes
- Telegram bot integration (pairing system)

### ⚠️ Works Partially
- Tool calling with 8B models (model often describes tools instead of calling them)
- Weather skill (model confused web_search with weather tool)
- Skills system (lazy loading works, but model selection is unreliable)

### ❌ Doesn't Work Well with Local Models
- Complex agentic workflows (multi-step tool chains)
- Reliable function calling (8B models lack the precision)
- Full system prompt (too large for <32k context models)

### 🔴 Overkill for Local
- 24-section system prompt (6000+ tokens wasted)
- CLI Reference section (the model doesn't need to know OpenClaw commands)
- Self-Update section (unnecessary for local inference)
- Reaction guidelines (emoji usage rules burn tokens)
- Full AGENTS.md injection (800+ lines of workspace instructions)

---

## Ideas Worth Stealing

### 1. SOUL / AGENTS / USER / TOOLS Separation

Instead of one monolithic system prompt, split personality into modular files:

| File | Purpose | When to Load |
|------|---------|-------------|
| `SOUL.md` | Who you are (personality, tone) | Always |
| `AGENTS.md` | How you operate (rules, procedures) | Always |
| `USER.md` | About the human (personal context) | Private sessions only |
| `TOOLS.md` | Environment notes (paths, preferences) | When using tools |

**Security win:** Never load USER.md in group chats. Free privacy without code changes.

### 2. Two-Level Memory

```
memory/YYYY-MM-DD.md  →  Daily logs (raw, everything)
MEMORY.md             →  Curated long-term memory (distilled insights)
```

The agent searches daily logs via RAG, but the executive summary lives in MEMORY.md. Periodically, the agent reviews daily logs and updates MEMORY.md with what's worth keeping.

### 3. Lazy-Loaded Skills

```xml
<available_skills>
  <skill>
    <name>weather</name>
    <description>Get weather forecasts (no API key required)</description>
    <location>/path/to/SKILL.md</location>
  </skill>
</available_skills>
```

The agent only sees short descriptions. It reads the full SKILL.md only when the task matches. This saves thousands of tokens compared to loading all skill instructions upfront.

### 4. Heartbeat System

Every 30 minutes, the agent receives a ping:
- Nothing to do? → Reply `HEARTBEAT_OK` (minimal token cost)
- Something pending? → Take action

State tracked in JSON:
```json
{"lastChecks": {"email": 1703275200, "calendar": 1703260800}}
```

**For local models:** A cron job that runs `llama-cli` with HEARTBEAT.md as prompt. ~100 tokens per check.

### 5. Trusted vs. Untrusted Metadata

OpenClaw explicitly marks what comes from the system (trusted) vs. what comes from the user (untrusted). This prevents prompt injection where user text mimics system metadata.

---

## Ideas Worth Ignoring

### 1. The Mega System Prompt

6000+ tokens of instructions on every single call is designed for cloud models with unlimited context. For local models with 8-32k context, this is wasteful. Build a 500-token prompt that covers identity + current task only.

### 2. Depending on the Model for Tool Selection

OpenClaw sends a list of 20+ tools and hopes the model picks the right one. With 8B models, this fails regularly. Better approach: **your code decides which tool to use** (like a bash router), and the model only generates the content.

### 3. Gateway Architecture for Single-User

The WebSocket gateway, auth tokens, pairing codes — all designed for multi-device, multi-channel scenarios. If you're one person on one machine, a simple `llama-cli` call from a bash script is faster, simpler, and more reliable.

### 4. Full Workspace Injection

Injecting AGENTS.md (800+ lines of instructions about heartbeats, reactions, group chat etiquette, memory maintenance) into every prompt is insane for local models. Extract the 10 lines that matter and discard the rest.

---

## Building Your Own Lightweight Alternative

Based on everything learned from this deep dive, here's what a local-first alternative looks like:

### Architecture

```
User Query
    ↓
[Bash Router] → Classifies task type + selects model
    ↓
[Prompt Builder] → Loads SOUL.md (200 tokens) + task context
    ↓
[llama-cli] → Local inference, no server needed
    ↓
[Evaluator] → Second model validates response quality
    ↓
[Memory] → Saves to daily log + updates curated memory
    ↓
Response
```

### Key Differences from OpenClaw

| Aspect | OpenClaw | Local Alternative |
|--------|----------|-------------------|
| Orchestration | Model decides everything | Code decides, model generates |
| System prompt | 6000+ tokens | 500 tokens max |
| Tools | Model calls tools via function calling | Bash scripts execute tools directly |
| Model count | 1 cloud model does everything | Multiple local models, each specialized |
| Memory | Semantic search (needs embeddings API) | File-based with grep/RAG |
| Cost | $0.01-0.10 per interaction | $0.00 (local inference) |
| Context usage | 25-80% wasted on system prompt | 5-10% for identity + task |

### Sample Lightweight SOUL.md (for local models)

```markdown
# DANEEL — R. Daneel Olivaw

You are Daneel, a strategic AI assistant. You speak Spanish by default.

## Core traits
- Analytical, direct, no filler words
- Reference Asimov's Laws when relevant to decisions
- Admit uncertainty openly

## Rules
- Never execute destructive commands without confirmation
- Keep responses under 500 words unless asked for more
- If you don't know, say so

## Context
- Human: Gustavo (developer, Barcelona)
- Environment: macOS, bash, local AI models
- Projects: BiblioGalactic ecosystem
```

~150 tokens. Compare to OpenClaw's 6000+.

---

## Conclusion

OpenClaw is an impressive orchestration framework **designed for cloud models with unlimited context and native tool support**. When paired with Claude Opus or GPT-4, it delivers genuine agentic capabilities.

For local models, however, the architecture fights against you: the system prompt is too large, the tool calling is unreliable, and the gateway adds complexity without proportional benefit.

**The real value of exploring OpenClaw isn't using it — it's understanding how it works** so you can cherry-pick the best ideas (modular personality files, two-level memory, lazy-loaded skills, heartbeat system) and implement them in a lightweight, local-first architecture where your code handles the orchestration and your models handle what they're good at: generating text.

Don't let the framework think for your models. Let your code think, and let your models write.

---

## References

- **OpenClaw Repository:** [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)
- **CVE-2026-25253:** Remote code execution vulnerability (CVSS 8.8)
- **System Prompt Source:** `src/agents/system-prompt.ts` (651 lines)
- **OpenClaw Docs:** [docs.openclaw.ai](https://docs.openclaw.ai)

---

## About This Guide

This document was created during a live hacking session: installing OpenClaw from scratch, hitting every error, reading the source code, and reverse-engineering the system prompt — all in one night.

**Author:** Gustavo Silva da Costa ([@BiblioGalactic](https://github.com/BiblioGalactic))
*Automating complex ideas with local AI, from Bash, for humans.*

**AI Collaboration:** Claude Opus 4.6 (Anthropic) — research, analysis, architecture review, and documentation.

**Project:** [OpenClaw Local Model Modifier](https://github.com/BiblioGalactic/openclaw-modifier)
**Brand:** EtoDemerzel — Prompt Engineering & AI Automation

**Date:** February 16, 2026
**License:** MIT

---

> *"The real magic isn't in the framework — it's in understanding what the framework does, so you can do it better yourself."*

[⬆️ Back to top](#-openclaw-deep-dive--from-installation-to-system-prompt-surgery)
