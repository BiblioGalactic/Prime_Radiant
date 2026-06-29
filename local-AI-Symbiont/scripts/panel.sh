#!/usr/bin/env bash
# Symbiont — observability + the stop condition. Reads the per-cycle score trend,
# pings both machines, and prints whether the system is MATURE (see §4).
# The engine/loop is expected to append "cycle,score" rows to data/progress.csv.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$HERE/config.sh" 2>/dev/null || source "$HERE/config.example.sh"

ping_srv() { curl -s -m 3 "$1/models" >/dev/null 2>&1 && echo "🟢 up" || echo "🔴 down"; }
PROG="$SYMBIONT_HOME/data/progress.csv"
META="$SYMBIONT_HOME/data/META.md"
EXE="$(ping_srv "$EXEC_URL")"; JUD="$(ping_srv "$JUDGE_URL")"
WD="normal"; [ -f "$SYMBIONT_HOME/data/pause.flag" ] && WD="⏸️ paused"

python3 - "$PROG" "$META" "$EXE" "$JUD" "$WD" "$META_SCORE" <<'PY'
import sys, time, csv, os
PROG, META, EXE, JUD, WD, target = sys.argv[1:7]
target = float(target)
rows = []
if os.path.exists(PROG):
    with open(PROG) as f:
        for r in csv.reader(f):
            if len(r) >= 2:
                try: rows.append((r[0], float(r[1])))
                except ValueError: pass   # skip header / bad lines
scores = [s for _, s in rows]
L = ["# Symbiont — META", f"_generated {time.strftime('%Y-%m-%d %H:%M:%S')}_", "",
     f"- executor ({EXE})", f"- judge ({JUD})", f"- watchdog: {WD}", ""]
if rows:
    L += ["## Score per cycle", "| cycle | score |", "|---|---|"]
    L += [f"| {c} | {s:.2f} |" for c, s in rows[-12:]]
    if len(scores) >= 2:
        d = scores[-1] - scores[0]
        arrow = "📈 rising" if d > 0.05 else ("📉 falling" if d < -0.05 else "➡️ flat")
        L.append(f"\n- trend: {scores[0]:.2f} → {scores[-1]:.2f} ({arrow}, {len(scores)} cycles)")
    L.append("\n## Mature? (stop condition)")
    if len(scores) < 5:
        L.append(f"- 🔴 too early ({len(scores)} cycles); aim for ≥10")
    else:
        rec = scores[-5:]; band = max(rec) - min(rec); rise = scores[-1] - scores[-5]
        if rise > 0.1:
            L.append(f"- 🟡 still improving (+{rise:.2f} over 5); keep feeding it")
        elif band <= 0.08 and sum(rec) / len(rec) >= target:
            L.append(f"- 🟢 MATURE: stable & high (±{band:.2f}, avg≥{target}); more data buys little")
        elif band <= 0.08:
            L.append(f"- 🟢 plateau (±{band:.2f}) but below target; improve capabilities, not data volume")
        else:
            L.append(f"- 🟡 unstable (±{band:.2f}); let it run longer")
    L.append("- 'enough' = score plateau + few new gaps + composition still beats raw.")
else:
    L.append("(no data/progress.csv yet — run ./loop.sh)")
open(META, "w").write("\n".join(L) + "\n")
print("\n".join(L))
PY
echo; echo "📄 $META"
