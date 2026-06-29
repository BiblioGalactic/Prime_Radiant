# Symbiont: A Self-Cultivating Local-AI Organism via Capability Composition, Corrective Retrieval, and Cross-Machine Symbiosis

**A Technical Whitepaper**

**Author:** Gustavo Silva Da Costa (Eto Demerzel)
**Date:** June 29, 2026
**Version:** 1.0
**Classification:** Emergent Agent Architecture

---

## Abstract

This paper describes **Symbiont**, a local-AI system that does not merely *run* — it **cultivates itself**. Symbiont is not a new algorithm bolted onto old ones; it is the point at which several previously independent lines of work converge and, in converging, exhibit properties that none of them had in isolation.

The constituent parts are already documented elsewhere in this repository: **MOSAIC** (composition of ephemeral agents from a library of reusable capabilities), **CRAG/TADPA** (contextual retrieval applied to instructions rather than knowledge), a **local cluster** (load distribution across machines), **cross-model evaluation and synthesis** (judging answers with other models), and **memory pre-loading**. Symbiont wires these into a single closed loop and adds the one ingredient each lacked alone: **a reason to keep going without a human in the loop, and a way to know when to stop.**

The result is an organism-like system with six self-referential properties — it **feeds itself**, **extends itself**, **judges itself**, **distributes itself**, **regulates itself**, and **knows when it has had enough**. We argue, with explicit honesty about the limits, that this is **emergence, not fusion**: the whole answers a question none of the parts could.

---

## 1. The difference between a fusion and an organism

It is easy to take five working systems, call them from one script, and announce a "platform." That is a *fusion*: a bag of parts sharing a directory. It is also easy to take one system and run it in a `while true` loop and announce "autonomy." That is a *loop*: motion without direction.

Symbiont is neither, and the distinction is the entire point of this document.

A fusion has no new behaviour — remove the wrapper and each part behaves exactly as before. A loop has new motion but no new behaviour — it repeats. **An organism has behaviour that exists only at the level of the whole.** A single neuron does not think; a single capability does not learn; a single model does not know whether it is improving. Symbiont does all three, and it does them because the parts are wired into a circuit where each one's output is another one's food.

The test we hold ourselves to: *if you can describe a property of Symbiont without mentioning at least two of its parts interacting, that property is not emergent and does not belong in this paper.* Everything below passes that test.

---

## 2. The closed loop

The canonical agentic system is open-ended: a human asks, the system answers, the system waits. Symbiont closes the loop by making the system responsible for its own inputs, its own evaluation, and its own growth.

```
        ┌─────────────────────────────────────────────────────────┐
        │                                                         │
        ▼                                                         │
  ┌───────────┐   question   ┌───────────┐   composed   ┌───────────┐
  │ GENERATORS │ ───────────▶ │  COMPOSE  │ ───────────▶ │  EXECUTE  │
  │ (N models) │              │ (MOSAIC)  │   agent      │  (strong) │
  └───────────┘              └───────────┘              └─────┬─────┘
        ▲                          │                          │ answer
        │                     gap? │ (CRAG gate)              ▼
        │                          ▼                    ┌───────────┐
        │                    ┌───────────┐    score     │   JUDGE   │
        │                    │  EXTEND   │ ◀─────────────│ (2nd model│
        │                    │ (new cap) │               │  machine) │
        │                    └─────┬─────┘               └─────┬─────┘
        │                          │ reward / prune            │ verdict
        │                          ▼                           │
        │                    ┌───────────┐                     │
        └────────────────────│  CULTIVATE │◀────────────────────┘
          keep feeding until │ (consolidate, score, mature?)
          mature             └───────────┘
```

Read it as a metabolism. **Generators** synthesise novel inputs (the system's food). **Compose** retrieves and assembles a specialised ephemeral agent from the capability library. A **corrective gate** asks whether the retrieved capabilities actually fit; if nothing fits, that absence is recorded as a *gap*. **Execute** runs the composed agent on the strong model. A **judge** — deliberately a *different* model, on a *different* machine — scores the answer. The score becomes **reward**: good capabilities rise, weak ones are pruned. Gaps become **new capabilities**, written by the system itself and curated before they are admitted. And a **cultivation** stage decides, from the trend of its own scores, whether to keep eating or to declare itself done.

No step in that paragraph is new. The circuit they form is.

---

## 3. The six self-referential properties

### 3.1 It feeds itself
A pool of *different* models generates the questions. Diversity is the point: a single model would generate a narrow, self-similar diet and the system would converge prematurely on its own blind spots. Heterogeneous generators widen the input space before the system narrows it. Each input is tagged with its origin, so evaluation can later ask *which kind of question from which model exposed which weakness.*

### 3.2 It extends itself
When the corrective gate finds that no existing capability fits an input, the gap is not an error — it is a specification. The strong model writes a **new, general capability** to cover that class of input. This is the line MOSAIC drew (capabilities as retrievable instructions) closed into a circle: the library that composes the answers also *grows* the answers it can compose.

### 3.3 It judges itself
Evaluation is done by a **second model on a second machine**, never the one that produced the answer. This is not a detail of deployment; it is what makes the reward signal trustworthy. A system that grades its own homework drifts. By physically separating executor and judge, the score that drives all learning comes from an independent observer.

### 3.4 It distributes itself
Two machines in **symbiosis** (hence the name). The strong machine executes; the lighter machine orchestrates, judges, and watches. Neither is "the server" — each does what its silicon is best at, and the system as a whole survives the saturation of either. This is the cluster line, repurposed from "spread load" to "divide cognitive labour."

### 3.5 It regulates itself
An independent **watchdog** monitors the health of the working machine. When it has been saturated too long, it raises a flag; the ingestion loop sees the flag and *pauses between units of work*, resuming only when the machine cools. The system protects its own substrate — the closest thing a script has to homeostasis.

### 3.6 It knows when it has had enough
The hardest property, and the one that separates cultivation from compulsion. Symbiont tracks the trend of its own evaluation scores and the rate at which it still discovers gaps. When the score reaches a high plateau and gaps stop appearing, it reports **maturity**: more data would cost energy and return nothing. A loop never stops. An organism reaches adulthood.

---

## 4. Maturity: an objective function with a stop condition

Most "self-improving" systems lack the second half of that phrase: a definition of *improved enough*. Symbiont's objective is explicit and bounded:

> Maximise the independent judge's score across a diverse input stream, while driving the gap-discovery rate toward zero — and **stop** when both flatten.

Three convergent signals, none requiring sophisticated statistics, only trends across many cycles:

1. **Score plateau** — the judge's average stops rising over a window of cycles.
2. **Gap exhaustion** — new inputs rarely produce gaps; the capability space is covered.
3. **Compositional advantage stable** — composed agents reliably beat the raw model, and the margin stops growing.

When the three hold together, the system is *mature*. The amount of data required is therefore **not a fixed number** — it is however much it takes for novelty to stop arriving, which depends on the diversity of the generators, not on raw volume. This is why heterogeneous self-feeding (§3.1) matters: it determines both how far the system can grow and when it will know it has finished.

---

## 5. Provenance: what converged, and what it became

| Branch (this repository) | What it contributed | What it became inside Symbiont |
|---|---|---|
| **MOSAIC** | Ephemeral agents composed from retrievable capabilities | The body: how every answer is assembled |
| **CRAG / TADPA** | Contextual retrieval of instructions; the corrective gate | The reflex: knowing when it *doesn't* know, and recording the gap |
| **local-AI-cluster** | Load distribution across local machines | The two-bodied symbiosis: executor vs. judge/orchestrator |
| **cross-eval-synth** | Comparing and judging across models | The conscience: an independent grader that the learning can trust |
| **MMAP-memory** | Pre-loaded, demand-paged memory | The metabolism's efficiency: warm capability/context state |
| **adaptive-rag daemon** | Long-running, self-adjusting retrieval | The pulse: a loop that adjusts itself instead of merely repeating |

None of these branches, alone, can feed itself, grade itself on another machine, write its own missing skills, protect its own hardware, and declare itself finished. Symbiont can, because the branches are wired so that each one's weakness is covered by another one's strength. That coverage — not the code — is the contribution.

---

## 6. The value: cultivate a mask, then lend it

The durable artifact Symbiont produces is **not a model** — it is the **capability library**. Think of it as a *mask of competence*: model-agnostic, retrievable instructions that, worn by a model at composition time, lift its answers.

This is distillation, but in an unusual place. Conventional distillation compresses a strong model's behaviour into another model's **weights** — expensive, and bolted to one model. Symbiont distills competence into **prompts** — into the library. Because the knowledge lives in instructions rather than weights, it is **portable across models without retraining**.

The workflow this enables is two-phase and economical:

1. **Cultivate** the mask once, using strong models and an independent judge (an expensive but one-time cost — the loop of §2).
2. **Wear** the mask cheaply: a smaller, weaker model, fed the composed prompt, performs well above its naive baseline — *within the domains the library covers*.

**The honest ceiling.** A mask raises the *floor* and the *consistency* of a weaker model; it narrows the gap. It does **not** erase the model's capacity — a great prompt will not make a tiny model reason like a large one. What the mask buys is that the model reliably *reaches its own ceiling* (good format, methodology applied, fewer mistakes) instead of hitting it only by luck. "A weak model stops being weak" is too strong; "a weak model stops wasting its capacity" is right.

**And it is measurable.** Run the same weak model twice — once with the composed mask, once raw — and have the judge score both. The difference *is* the value the mask adds, as a number. (Symbiont already contains this A/B comparison; it is the experiment that turns the claim into evidence.)

---

## 7. Honest limitations

In the spirit of the rest of this repository, the scars stay visible:

- **Compute-bound, not idea-bound.** Every cycle is real inference on local models. The system is patient by design, not fast. Distribution helps; it does not make it free.
- **The judge is a model.** An independent grader is more trustworthy than self-grading, but it is still a language model with its own biases. Maturity is measured against that judge, not against ground truth.
- **Self-written capabilities need curation.** A system that writes its own instructions will, left unchecked, also write mediocre ones. Symbiont curates new capabilities before admitting them and prunes redundancy — but curation is itself a model judgement, not a proof.
- **Maturity is a heuristic, not a theorem.** "The curves flattened" is a practical stop signal, not a convergence guarantee. It tells you when more of *the same* data stops helping; it cannot tell you about data you never generated.
- **Emergence is a claim, not a magic word.** We have tried to earn it (§1's test). A reader is entitled to disagree and call any individual property mundane. The argument rests on the *circuit*, not on any single node.

---

## 8. Conclusion

Symbiont is what happened when a collection of honest, separately-built local-AI tools were wired into a loop that takes responsibility for its own continuation. It generates its own questions, composes specialised agents to answer them, has those answers graded by an independent model on a second machine, writes the skills it discovers it lacks, protects the hardware it runs on, and — the part that makes it an organism rather than a loop — **knows when to stop.**

It is local. It is transparent. It is bounded. And it is, in the precise sense argued here, **more than the sum of the branches that became it.**

---

*"A loop repeats until you kill it. An organism grows until it is enough."*
— Eto Demerzel, Symbiont

---

**Author:** Gustavo Silva Da Costa (Eto Demerzel) · [BiblioGalactic](https://github.com/BiblioGalactic)
**License:** MIT (code) · CC BY 4.0 (this document)
**Status:** Working system; this paper describes a running convergence, not a proposal.
