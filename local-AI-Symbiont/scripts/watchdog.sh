#!/usr/bin/env bash
# Symbiont — self-regulation (homeostasis): watch the working machine's load and,
# when it stays saturated too long, raise a pause flag the loop obeys. See §3.5.
# Run it alongside loop.sh (locally, or on the 2nd machine over SSH).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$HERE/config.sh" 2>/dev/null || source "$HERE/config.example.sh"

FLAG="$SYMBIONT_HOME/data/pause.flag"
INTERVAL="${WATCH_INTERVAL:-15}"   # seconds between readings
COOLDOWN="${WATCH_COOLDOWN:-30}"   # seconds below limit before clearing the pause
log() { printf '[%s] [watchdog] %s\n' "$(date '+%H:%M:%S')" "$*"; }
mkdir -p "$(dirname "$FLAG")"

# Portable load% = 1-min load average / CPU count * 100  (macOS or Linux).
load_pct() {
    local l1 n
    if [ -r /proc/loadavg ]; then
        l1="$(cut -d' ' -f1 /proc/loadavg)"; n="$(nproc 2>/dev/null || echo 1)"
    else
        l1="$(sysctl -n vm.loadavg 2>/dev/null | awk '{print $2}')"
        n="$(sysctl -n hw.ncpu 2>/dev/null || echo 1)"
    fi
    [ -n "${l1:-}" ] && [ -n "${n:-}" ] && awk -v a="$l1" -v b="$n" 'BEGIN{if(b>0)printf "%d",(a/b)*100}'
}

trap 'echo; log "stopped."; exit 0' INT TERM
log "watching: limit=${LOAD_LIMIT}% sustained ${LOAD_HOLD}s"
hot=0; cool=0
while true; do
    pct="$(load_pct || echo "")"
    if [ -n "$pct" ] && [ "$pct" -ge "$LOAD_LIMIT" ]; then
        hot=$((hot + INTERVAL)); cool=0
        if [ "$hot" -ge "$LOAD_HOLD" ] && [ ! -f "$FLAG" ]; then
            echo "load ${pct}% for ${hot}s" > "$FLAG"; log "PAUSE raised (${pct}%)"
        fi
    else
        cool=$((cool + INTERVAL)); hot=0
        if [ -f "$FLAG" ] && [ "$cool" -ge "$COOLDOWN" ]; then
            rm -f "$FLAG"; log "load normal (${pct:-?}%); pause cleared"
        fi
    fi
    sleep "$INTERVAL"
done
