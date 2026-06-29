# Symbiont — reference scripts

Generic, machine-agnostic reference implementation of the loop described in the
[whitepaper](../README.md). No machine-specific paths, IPs or hostnames live
here — everything is configured through `config.sh`.

## The pieces

| script | role (whitepaper §) | what it does |
|---|---|---|
| `config.example.sh` | — | the single place you edit: paths, model list, endpoints, thresholds |
| `generate.sh` | self-feeding (§3.1) | each of several **different** local models invents a question |
| `loop.sh` | metabolism (§2) | alternates ingestion and cultivation; obeys the watchdog; refreshes the panel |
| `watchdog.sh` | self-regulation (§3.5) | pauses the loop when the machine stays saturated; resumes when it cools |
| `panel.sh` | maturity (§4) | score trend across machines + the **stop condition** verdict |

## Architecture, in one line

Symbiont is the **orchestration layer**. The actual composition of answers is done
by a **MOSAIC-compatible engine** (`ENGINE_CMD`): it must take a request as `$1`,
compose+execute it, and expose `--consolidate` (learn from real use) and `--extend`
(turn discovered gaps into new capabilities). The judge runs on a **second machine**
(`JUDGE_URL`) so the reward signal is independent of the executor.

## Quickstart

```bash
cp config.example.sh config.sh      # then edit: GEN_MODELS, EXEC_URL, JUDGE_URL…
./watchdog.sh &                     # homeostasis (optional, recommended)
./loop.sh                           # run until mature or Ctrl-C
./panel.sh                          # ask: is it mature yet?
```

## Requirements

- `bash`, `curl`, `python3`
- [llama.cpp](https://github.com/ggerganov/llama.cpp) (`llama-cli` for generators, `llama-server` for the endpoints)
- a MOSAIC-compatible composition engine on `ENGINE_CMD`

> Design note: never pass `--log-disable` to the generators — on recent llama.cpp
> builds it silences the generation itself, not just the telemetry. Redirect
> `stderr` instead (already done in `generate.sh`).
