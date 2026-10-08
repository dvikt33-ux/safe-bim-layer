# Architectural AI checkpoint 29 — how to actually teach the system: FLOORA, expert alignment, RLVR and architecture-specific evaluation

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Executive conclusion

This is one of the most important findings of the entire research cycle.

A current open Autodesk Research project, **FLOORA**, demonstrates almost exactly the training recipe we need for the parts of architecture that genuinely benefit from a learned model:

```
compact architecture DSL
        ↓
large synthetic curriculum
        ↓
domain pre-training
        ↓
architect edits
        ↓
supervised fine-tuning
        ↓
architect pairwise preferences
        ↓
reward model
        ↓
RL with:
  learned architect preference
  +
  deterministic/verifiable rewards
```

FLOORA is:
- open source;
- Apache-2.0;
- model weights released;
- dataset released;
- inference code released;
- based on very small Qwen3 backbones (0.6B / 1.7B);
- specifically designed for architectural layout generation.

This changes the answer to the old question:
"Do we need a large local 30B/150B model to learn architecture?"

For structured architectural subproblems, **probably not**.

A small specialized model can be more useful than a giant general-purpose model when:
- the representation is compact;
- the task is narrow;
- rewards are verifiable;
- architect preference data are available;
- a powerful general model remains available as orchestrator/researcher.

This strongly supports a hybrid:
`large cloud reasoning model + small local architecture specialist models + deterministic solvers`.

---

# 1. FLOORA is not another vague floor-plan paper — code, data and models are public

Repository:
`AutodeskAILab/floora`

Observed:
- Apache-2.0 code;
- FLOORA-0.6B;
- FLOORA-1.7B;
- Hugging Face dataset;
- DSL tokenizer;
- parser/visualizer;
- inference pipeline;
- tests.

Base models:
- Qwen3-0.6B;
- Qwen3-1.7B.

The model card reports that vocabulary resizing makes the nominal 0.6B model approximately **440M effective parameters**.

This is orders of magnitude smaller than the large local models we had been discussing.

---

# 2. FLOORA's task is narrow — this is a strength, not a replacement for the whole architect

Current direct scope:

Input:
- building metadata;
- structural material;
- massing polygon;
- optionally partial space layouts.

Output:
- labeled polygons for:
  - cores;
  - corridors;
  - living units.

Target domain:
- conceptual multifamily residential floor-plan generation.

Explicit out-of-scope:
- general architectural assistant;
- construction documentation;
- code compliance;
- structural engineering;
- MEP;
- fire/life safety;
- arbitrary building typologies.

Real-world evaluation data are mainly multifamily footprints from North American cities.

Therefore:

**FLOORA must not become the architectural authority for Russian projects.**

It is:
- a candidate generator;
- an open training recipe;
- a demonstration that small domain models work;
- a starting point for future specialization.

---

# 3. The representation lesson may be more important than the model itself

FLOORA does not train directly on verbose IFC.

It defines a compact architectural DSL that is:
- deterministic;
- parseable;
- normalizable;
- geometry-convertible;
- human readable.

The paper reports that the example DSL can be roughly 15x more compact than equivalent IFC for its conceptual-layout information.

This is directly relevant to our Fast Project Compiler.

## Revised model interface

Do not feed a local model:
- a 100 MB Model Dump;
- full IFC STEP;
- every property;
- every face.

Compile a task-specific DSL/view.

Example:

```
<context>
SITE...
PROGRAM...
STRUCTURE_ENVELOPE...
VCE...
MASSING...
ADG...
HARD_CONSTRAINTS...
</context>

<generate>
LAYOUT
</generate>
```

The model returns:
- a small candidate representation.

Then deterministic code converts/validates it.

### Decision

Introduce the concept:
**Task DSL / Compact Architectural IR**

Do not create one giant universal neural-network token format.

Different learned specialists may have different compact views:
- floor layout;
- façade grammar;
- detail selection;
- repair action.

---

# 4. FLOORA's data recipe is directly reusable

The paper/model card reports:

## Synthetic pre-training

Approximately:
- 4.1M synthetic samples before rotation augmentation;
- ~82M after augmentation.

Synthetic generation is not trusted blindly.

Near-miss model outputs are:
- repaired;
- filtered through correctness verifiers;
- only valid samples retained.

## Real/out-of-distribution evaluation

Real multifamily massings from OpenStreetMap are kept for out-of-distribution testing rather than simply mixed into synthetic training.

## Canonicalization

Layouts are normalized/canonicalized so the same design does not appear as many token sequences because of:
- polygon start vertex;
- ordering;
- translation;
- rotation-related representation variation.

This is extremely important for our future training set.

### Decision

If we train a Russian/domain specialist:
- generate synthetic examples from our deterministic engine;
- validate every synthetic target;
- canonicalize;
- deduplicate before split;
- hold real projects out for OOD testing.

Do not indiscriminately fine-tune on every old project file.

---

# 5. The architect feedback loop is almost exactly what we need

FLOORA's post-training workflow uses practicing architects.

For each massing:
- model generates multiple candidates;
- architect rates candidates;
- architect ranks them;
- architect edits the best candidate.

This produces three different signals:

## Edited best plan
-> Supervised Fine-Tuning target.

## Pairwise ranking
-> Reward-model preference data.

## Rating
-> filters/noise control and quality signal.

The paper reports:
- ~10k architect-edited SFT samples;
- ~90k pairwise preference examples.

This is the right pattern for our future project.

### Our version

Every time the user works with SBIM:

```
AI proposes candidates A/B/C
        ↓
architect chooses B
        ↓
architect edits B -> B'
        ↓
system records:
  B > A
  B > C
  B' > B
  exact edits
  reason/DDR
  hard-rule state
  project context
```

This becomes valuable learning data.

The chat transcript itself is **not** the training truth.

The structured accepted/rejected design trajectory is.

---

# 6. Hard correctness and architectural taste must use different reward channels

This is perhaps the most important training principle.

## Verifiable reward

Machine-computable:
- no room overlap;
- inside boundary;
- required area;
- adjacency;
- corridor width;
- door clearance;
- module;
- structural span envelope;
- travel distance;
- CSE compatibility;
- normative checks;
- equipment fit.

These can be rewarded deterministically.

## Architect preference reward

Not reducible to one regulation:
- plan feels coherent;
- good hierarchy;
- façade composition;
- entrance emphasis;
- proportion;
- spatial sequence;
- avoiding awkward corners;
- preserving project concept;
- choosing a better compromise.

These need:
- architect pairwise preferences;
- edits;
- ADG/Design Intent;
- possibly learned reward models.

## Critical rule

A learned preference reward may never overrule a HARD legal/safety/geometry gate.

Pipeline:

```
candidate
   ↓
HARD VERIFIERS
   ↓ PASS only
architectural preference score
   ↓
rank
```

Not a weighted sum where "beautiful" can compensate for a fire-safety failure.

---

# 7. FLOORA proves that mixed learned + verifiable RL is viable

FLOORA combines:
- a learned reward model trained from architect preferences;
- bounded verifiable rewards;
- reinforcement learning using GRPO.

The paper explicitly normalizes learned reward so it cannot numerically overwhelm the verifiable terms merely because of scale.

For us, the policy should be even stricter:

## Tier 0
hard invalid -> candidate rejected before preference ranking.

## Tier 1
validity margin / robustness.

## Tier 2
architectural preference.

## Tier 3
cost/carbon/time/maintainability tradeoffs.

This preserves a lexicographic hierarchy instead of allowing unsafe reward tradeoffs.

---

# 8. FLOORA's reported result is a major argument for small local specialist models

The current paper reports that its 0.6B model:
- outperforms substantially larger frontier models on the target task;
- reaches up to 92% VLM-judge wins on OOD real-world buildings;
- 96% on synthetic evaluation;
- is selected as best in 89.3% of reported human evaluations.

These results are **within FLOORA's narrow benchmark**, not proof that it is a better architect overall.

But the architectural lesson is powerful:

**domain representation + domain data + expert alignment can substitute for raw parameter scale for a structured subtask.**

### Consequence

The local-model strategy should change.

Do NOT begin by installing/training a giant general-purpose local model to "be the architect".

Preferred hierarchy:

```
Cloud GPT
  global reasoning / research / orchestration
        ↓
small local specialists
  repetitive structured candidate generation
        ↓
deterministic tools
  geometry / code / engineering / optimization
```

FLOORA becomes the first serious local specialist candidate.

---

# 9. Immediate FLOORA role in SBIM

## Short term — no training

Run released FLOORA model as-is.

Use it only for:
- multifamily massing -> core/corridor/unit candidate generation;
- benchmark against Finch/FloorPlan6/our solver.

Then:
- map DSL polygons into our semantic plan representation;
- run Russian hard checks;
- reject bad candidates;
- translate accepted candidate into AC29.

## Medium term — adapter

Extend context outside model if possible:
- structural envelope;
- VCE;
- selected project metrics.

Do not modify weights until baseline is measured.

## Long term — Russian/office specialization

Only after collecting structured project feedback:
- SFT from architect corrections;
- preference model from pairwise selections;
- RL/RLVR from our deterministic verification stack.

This is much more defensible than speculative fine-tuning today.

---

# 10. Existing RLVR floor-plan work independently confirms the training pattern

A 2026 Findings of ACL paper, **Generative Floor Plan Design with LLMs via Reinforcement Learning with Verifiable Rewards**, shows a text-based LLM floor-plan generator improved with RLVR.

The reward checks:
- connectivity;
- numerical constraints;
- invalid/overlapping outputs.

The published results report at least a 94% relative reduction in the paper's compatibility-error metric versus prior methods across tasks.

A second 2026 line of work uses:
- topology generation;
- Double DQN;
- multi-objective rewards;
- hierarchical curriculum;
- geometric layout generation.

### Decision

If we ever train a learned planner:
**curriculum + verifiable rewards is known practice.**

Do not invent a new RL formulation unless existing recipes fail.

---

# 11. Current commercial AI plan quality shows why evaluator-first matters

A June 2026 study compared PlanFinder-generated residential layouts with completed human-designed Polish apartments.

The generated layouts satisfied only about:
- 55.56% to 74.07% of the study's binary criteria depending on apartment type.

The study reports serious problems including:
- regulatory failures;
- too-small/awkward rooms;
- weak handling of internal structural walls;
- ergonomic deficiencies such as kitchen work-triangle reasoning.

The authors conclude AI generation is very fast but requires expert correction before professional use.

This is directly consistent with the user's observed failures.

### Consequence

Never accept:
`BIM-ready`
as equivalent to:
`architect-ready`.

Every generator enters through our benchmark/verification harness.

---

# 12. We now have several public benchmarks instead of inventing every evaluation

## FloorplanQA — ICML 2026

Tests structured spatial reasoning:
- distance;
- visibility;
- pathfinding;
- object placement.

Current frontier models show inconsistent physical/spatial reasoning.

Use to benchmark the reasoning model / tool-usage baseline.

## AEC-Bench — Nomic, Apache-2.0

Current public benchmark:
- 196 tasks;
- 9 task families;
- real drawings/specifications/submittals;
- intra-sheet;
- cross-sheet;
- project-level reasoning;
- automatic verification;
- supports agent harnesses including Codex/Claude.

Tasks include:
- technical detail review;
- detail-title accuracy;
- callout accuracy;
- cross-reference resolution/tracing;
- sheet-index consistency;
- drawing navigation;
- spec-drawing sync;
- submittal review.

This should be incorporated into our agent-evaluation baseline.

## ARCH-B — September 2026

Tests cross-representation understanding across:
- photos;
- floor plans;
- elevations;
- sections;
- renderings.

354 multiple-choice questions / 11 archetypes in current paper.

Useful for measuring whether the vision model understands that different representations describe the same building.

## Future project-specific benchmark

None of these measures:
"Can the agent safely modify our Archicad project like an architect?"

We need a local benchmark for that.

---

# 13. Proposed Architect Competence Benchmark (ACB)

Do not train until we can measure.

Create benchmark families:

## A. Spatial reasoning
Borrow:
- FloorplanQA;
- Topologic tests.

Examples:
- can furniture fit?
- can door open?
- shortest accessible route?
- visibility?
- adjacency?

## B. BIM semantics
- element/host/story/material;
- GUID identity;
- source vs derived object;
- composite/profile semantics.

## C. Architecture hard constraints
- area;
- adjacency;
- daylight;
- openings;
- module;
- CSE;
- VCE;
- structure.

## D. Change propagation
Given one edit:
- list invalidated elements;
- required checks;
- affected documentation;
- whether edit is permitted.

## E. Architectural preference
Pairwise:
- choose better plan;
- choose better façade;
- choose lower-disruption repair.

Use architect gold labels.

## F. Documentation
Use:
- AEC-Bench;
- our SPDS document obligations;
- cross-reference/detail completeness.

## G. Cross-representation
Use:
- ARCH-B-like tasks;
- our BIM ↔ plan ↔ section ↔ façade regression.

## H. Live Archicad execution
- perform semantic action;
- readback;
- no unintended edits;
- undo/rollback;
- exact geometry/property state.

Primary final KPI:
**human minutes to accepted, verified AC29 outcome.**

---

# 14. A local learning record should be explicit and immutable

Proposed record:

```yaml
learning_event_id:
project_revision:
task_context:
candidate_ids:
hard_verifier_results:
adg_scores:
cse_vce_context:
selected_candidate:
rejected_candidates:
architect_edits:
architect_rating:
pairwise_preferences:
decision_record_id:
reason_codes:
final_verified_revision:
provider:
model_version:
timestamp:
```

These records can later produce:
- SFT data;
- pairwise preference data;
- reward-model data;
- regression tests.

This is far more useful than raw chat logs.

---

# 15. Architecture feedback taxonomy must be predefined

Do not ask the architect to write essays after every correction.

One-click reason codes can capture useful labels:

- wrong adjacency;
- bad circulation;
- poor proportion;
- awkward residual space;
- wrong privacy hierarchy;
- façade rhythm broken;
- weak entrance;
- structural conflict;
- MEP conflict;
- construction/module conflict;
- equipment does not fit;
- code violation;
- overdesigned;
- too fragmented;
- too expensive/disruptive;
- lost design intent;
- document incomplete.

Optional free explanation remains available.

This minimizes annotation burden while producing trainable data.

---

# 16. Training order should be conservative

## Phase 0 — no training
Use released models and deterministic engines.

## Phase 1 — collect data
Record accepted/rejected candidates and edits.

## Phase 2 — retrieval/prompt/grammar improvement
Fix system behavior without weight updates where possible.

## Phase 3 — small SFT
Only if repeated error classes remain.

## Phase 4 — preference model
Only after enough reliable pairwise architect data.

## Phase 5 — RL/RLVR
Only after:
- rewards are stable;
- evaluation is held out;
- reward hacking tests exist.

Large general-model fine-tuning is not the first step.

---

# 17. Prevent reward hacking

Architecture has many metrics that can be "won" incorrectly.

Examples:
- maximize daylight -> giant glazing ruins façade/energy;
- minimize circulation -> insufficient spatial quality;
- maximize rentable area -> undersized support spaces;
- minimize wall moves -> preserve a bad existing state;
- maximize code margin -> inefficient building.

Safeguards:

1. HARD gates are not scalar rewards.
2. Separate objective families.
3. Track Pareto tradeoffs.
4. Preserve ADG invariants.
5. Use held-out expert evaluation.
6. Include adversarial/regression cases.
7. Log why a reward changed.
8. Never let model-generated self-score be the only judge.

---

# 18. Small local models should become skill specialists, not a second general brain

Potential future specialists:

- `LayoutStudent` — FLOORA-like floor candidates;
- `RepairStudent` — choose low-disruption repair class;
- `DetailRetriever` — retrieve candidate detail family;
- `FacadeGrammarStudent` — propose grammar-compatible opening variation;
- `DocumentStudent` — classify Information Obligations / view candidates.

Each must emit a compact structured output.

Cloud GPT remains:
- orchestrator;
- novel-problem solver;
- rule/context interpreter;
- explanation layer;
- tool/router supervisor.

This avoids duplicating a giant cloud model locally.

---

# 19. Practical experiment FLOORA-01

No fine-tuning.

1. Run `ADSKAILab/floora-0.6b`.
2. Feed 20 massing inputs relevant to our likely work.
3. Parse generated DSL.
4. Convert to our semantic floor geometry.
5. Run:
   - polygon validity;
   - overlap;
   - area;
   - corridor/core;
   - Russian program constraints where applicable;
   - Topologic spatial metrics.
6. Compare against:
   - FloorPlan6;
   - Finch if trial available;
   - architect baseline.
7. Record:
   - generation time;
   - valid pass@1/pass@5;
   - human correction minutes.

### Critical criterion

Do not judge it by the paper's North-American multifamily benchmark.

Judge it on **our acceptance benchmark**.

---

# 20. Practical experiment FEEDBACK-01

Use a single real planning problem.

Generate 4 candidates.

User:
- ranks 1–4;
- chooses best;
- corrects it.

System stores:
- pairwise preferences;
- actual edits;
- reason codes;
- final verified result.

Repeat on 10–20 design tasks.

Goal:
measure whether structured feedback collection is low-friction enough to become normal workflow.

No model training required yet.

---

# 21. Practical experiment ACB-BASELINE-01

Run current cloud agent through:

- a subset of FloorplanQA;
- AEC-Bench representative tasks;
- 20 local architectural change cases;
- AC29 write/readback tasks.

Save exact model/tool versions.

This becomes baseline `ACB-2026-10`.

Every future:
- plugin;
- model;
- local specialist;
- prompt architecture;

must beat baseline on:
- correctness;
- latency;
- human correction time.

---

# 22. New roadmap removals

Custom development is blocked pending evidence for:

- large local general "architect LLM";
- new floor-plan model architecture;
- new architectural RL algorithm;
- new general preference-training framework;
- benchmark framework from scratch;
- raw IFC language-model representation.

Reuse:
- FLOORA models/DSL/code;
- RLVR recipe;
- AEC-Bench;
- FloorplanQA;
- existing evaluation methods.

Custom justified:
- task DSL adapters;
- Russian/project-specific verifiable rewards;
- architect feedback records;
- ADG preference labels;
- ACB local benchmark;
- eventual small specialist fine-tunes if baseline evidence justifies them.

---

# Strategic conclusion

The most important change is conceptual:

**We should not try to train one AI to become an architect.**

We should build a system in which:
- deterministic tools enforce truth;
- small domain models learn narrow architectural skills;
- architect feedback teaches preferences;
- project history provides precedents;
- a strong general model orchestrates the process.

FLOORA is concrete evidence that this decomposition is not only plausible: in a narrow architectural task, it already works with a model hundreds of times smaller than the giant local models we initially considered.
