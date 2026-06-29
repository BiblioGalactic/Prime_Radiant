#!/usr/bin/env bash
# Symbiont — the metabolism: alternate INGESTION (feed the engine) and
# CULTIVATION (let it consolidate, score, extend), never overlapping, pausing
# whenever the watchdog says the machine is too hot. See whitepaper §2.
#   ./loop.sh [CYCLES]      (0 or empty = run until mature or Ctrl-C)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$HERE/config.sh" 2>/dev/null || source "$HERE/config.example.sh"

CYCLES="${1:-0}"
PAUSE_FLAG="$SYMBIONT_HOME/data/pause.flag"
log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }

wait_if_paused() {
    while [ -f "$PAUSE_FLAG" ]; do
        log "watchdog: machine hot ($(cat "$PAUSE_FLAG" 2>/dev/null)); waiting…"
        sleep 30
    done
}

# INGESTION: generators invent questions; the engine composes+executes each one.
# Provenance (which model asked) travels with the request for later analysis.
ingest_round() {
    "$HERE/generate.sh" | while IFS=$'\t' read -r source question; do
        [ -n "${question// /}" ] || continue
        wait_if_paused
        log "[$source] $question"
        SYMBIONT_SOURCE="$source" $ENGINE_CMD "$question" || log "engine error (continuing)"
    done
}

# CULTIVATION: the engine learns from what it just did and extends itself.
# Convention: a MOSAIC-compatible engine exposes consolidation/extension steps.
cultivate() {
    log "cultivating (consolidate + extend); judge on $JUDGE_URL"
    $ENGINE_CMD --extend     2>/dev/null || true   # turn discovered gaps into new capabilities
    $ENGINE_CMD --consolidate 2>/dev/null || true  # judge real use, reward/prune, score the cycle
}

trap 'echo; log "stopped. See ./panel.sh for the maturity verdict."; exit 0' INT TERM

i=0
while [ "$CYCLES" -eq 0 ] || [ "$i" -lt "$CYCLES" ]; do
    i=$((i + 1))
    log "════════ cycle $i ════════"
    wait_if_paused
    for _ in $(seq 1 "$ROUNDS"); do ingest_round; done
    cultivate
    "$HERE/panel.sh" >/dev/null 2>&1 || true       # refresh META.md every cycle
    log "cycle $i done — check ./panel.sh"
done
log "finished $i cycles."
