# Local-CROS

I built Local-CROS after getting tired of trusting the first plausible answer from a single local model. The tool is simple on purpose: ask several models the same question, force them to look at each other, and keep the record on disk so I can inspect where the final synthesis came from.

## What it actually does

- runs the same prompt against 2 to 4 GGUF models,
- stores every raw answer,
- lets the models cross-evaluate each other,
- writes a combined final response.

I stopped at 4 models because beyond that the run time grew faster than the insight.

## Why it writes files for everything

I wanted traceability more than elegance. If the final synthesis is wrong, I need to see which model polluted it and which one had the useful fragment. A single pretty terminal output is not enough for that.

## Requirements

- `llama.cpp`
- 2-4 GGUF models
- Bash
- basic shell tools

## Honest limitations

- the synthesis step is heuristic, not ground truth,
- slower models make the whole round feel heavy very quickly,
- if two weak models agree, the consensus can still be bad.

## Use

```bash
./local-cros.sh "Explain the trade-off between recall and precision"
```

If you are evaluating only one model, this repo is the wrong tool. Its whole point is friction between answers.
