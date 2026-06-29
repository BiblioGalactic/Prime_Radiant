#!/usr/bin/env bash
# Symbiont — self-feeding: a pool of DIFFERENT local models each invent a random
# question. Diversity is the point (see whitepaper §3.1). Prints "model<TAB>question".
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$HERE/config.sh" 2>/dev/null || source "$HERE/config.example.sh"

PROMPT='### Instruction:
Invent ONE single short, original, curious question on any topic. Reply with only the question.

### Response:
'

clean() { tr -d '\r' | sed -e 's/<|[^|]*|>//g' -e 's/\[end of text\]//g' -e 's/###.*$//' \
                          | tr '\n' ' ' | sed -e 's/  */ /g' -e 's/^ *//' -e 's/ *$//'; }

for model in $GEN_MODELS; do
    [ -r "$model" ] || { echo "skip (unreadable): $model" >&2; continue; }
    tag="$(basename "$model" .gguf)"
    # NOTE: never use --log-disable here; on recent builds it also silences the
    # generation. Send stderr (telemetry) to a log and keep stdout (the text).
    q="$("$LLAMA_CLI" -m "$model" -p "$PROMPT" -n 48 -c 2048 --temp 1.0 --top-p 0.95 \
            -no-cnv --no-display-prompt 2>/dev/null | clean)"
    [ -n "${q// /}" ] && printf '%s\t%s\n' "$tag" "$q"
done
