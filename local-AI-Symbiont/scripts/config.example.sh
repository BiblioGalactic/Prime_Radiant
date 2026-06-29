#!/usr/bin/env bash
# Symbiont — configuration (copy to config.sh and edit). All paths/endpoints are
# generic placeholders: there is NO machine-specific data in this repository.
#
#   cp config.example.sh config.sh   &&   $EDITOR config.sh

# --- where Symbiont keeps its data (questions, scores, history) ---------------
SYMBIONT_HOME="${SYMBIONT_HOME:-$HOME/.symbiont}"

# --- the composition engine Symbiont drives (a MOSAIC-compatible CLI) ----------
# It must accept a natural-language request as $1 and print/execute the answer.
ENGINE_CMD="${ENGINE_CMD:-python3 -m mosaic}"

# --- llama.cpp CLI for the question GENERATORS (the diverse "diet") ------------
LLAMA_CLI="${LLAMA_CLI:-llama-cli}"           # must be on PATH, or give a full path
# Space-separated list of local GGUF models used to GENERATE questions.
# Use several DIFFERENT models on purpose — diversity widens the input space.
GEN_MODELS="${GEN_MODELS:-/path/to/model-a.gguf /path/to/model-b.gguf}"

# --- cluster endpoints (OpenAI-compatible servers, e.g. llama-server) ----------
# Keep EXECUTOR and JUDGE on DIFFERENT machines/models: the judge must be
# independent from the executor for the reward signal to be trustworthy.
EXEC_URL="${EXEC_URL:-http://localhost:8080/v1}"    # strong model: executes answers
JUDGE_URL="${JUDGE_URL:-http://localhost:8081/v1}"  # 2nd machine: judges + light tasks

# --- cadence and thresholds ----------------------------------------------------
ROUNDS="${ROUNDS:-10}"           # ingestion rounds per cycle (rounds x models = inputs)
META_SCORE="${META_SCORE:-4.0}"  # maturity target: stable judge score (0-5 scale)
LOAD_LIMIT="${LOAD_LIMIT:-85}"   # watchdog: % CPU load (sustained) that triggers a pause
LOAD_HOLD="${LOAD_HOLD:-120}"    # seconds of sustained high load before pausing

export SYMBIONT_HOME ENGINE_CMD LLAMA_CLI GEN_MODELS EXEC_URL JUDGE_URL \
       ROUNDS META_SCORE LOAD_LIMIT LOAD_HOLD
mkdir -p "$SYMBIONT_HOME/data" "$SYMBIONT_HOME/queue" "$SYMBIONT_HOME/done"
