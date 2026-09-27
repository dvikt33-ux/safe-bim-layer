# FINAL ASSEMBLY AUDIT — Safe BIM UX / Sandbox / History / QA after pass 130

Date: 2026-09-27
Scope: final synthesis of UI, protection, history, sandbox, QA, selection, voice, BIBIM/AI compatibility and contextual recipe assistance.
Research branch only. No product code changes. No Live BIM writes.

---

# 1. Final objective

Safe BIM should make Archicad projects faster by:

- eliminating repetitive clicks and manual parameter edits;
- converting repeated work into deterministic recipes;
- minimizing failures through readback, QA and protected execution;
- keeping AI optional/on-demand rather than always resident;
- showing model problems immediately instead of discovering them late;
- making complex automation usable from one compact Russian palette.

The system is **not** designed as “LLM directly controls Archicad”.

Final architecture principle:

> AI proposes typed intent/recipes. Deterministic Safe BIM validates, executes, verifies, journals and audits.

---

# 2. Final palette UX

## Default compact state

One Russian Safe BIM palette, narrow and collapsed.

```text
┌────────────────────────────────┐
│ SAFE BIM                 ● SAFE│
├────────────────────────────────┤
│ Выбрано: 6 стен    Этаж: 1     │
│ [Команда / ИИ]                 │
│ [Вставить код]                 │
│ [Выбрать похожие]              │
│ [История] [Проверка]           │
├────────────────────────────────┤
│ Режим: ЗАЩИЩЁННЫЙ              │
│ ☑ checkpoint  ☑ подсветка      │
│ Последний этап: ✓              │
│ [Откатить этап]                │
└────────────────────────────────┘
```

One central expandable slot is reused by Code / AI / Similar / History / QA.

## Code behavior

- open by click;
- validate → preview → execute;
- may auto-collapse after successful completion;
- remains open on errors / WAITING_USER / UNKNOWN_OUTCOME.

## AI behavior

- open by click;
- close only by another user click;
- never auto-close after answer;
- AI produces a plan/recipe proposal, never direct write.

## Diagnostics

Tapir/backend version is hidden in normal healthy state. Show only if incompatible/unhealthy or on diagnostics page.

**Verdict: READY FOR UI PROTOTYPE.**

---

# 3. Protection model

Final protection stack:

```text
Preflight
   ↓
Checkpoint / Save
   ↓
Optional Sandbox
   ↓
One native Undo stage when supported
   ↓
Exact receipt + readback
   ↓
Incremental QA
   ↓
History record
```

## Normal mode
- standard verified Safe BIM runtime;
- readback/receipts;
- QA.

## Protected mode — recommended default for large stages
- mandatory checkpoint policy;
- one-stage native Undo when Safe BIM owns a C++ command scope;
- history entry;
- post-stage QA gate.

## Sandbox mode
- duplicate proposal in Design Option for supported types;
- Mark-Up original↔proposal mapping;
- visual distinction;
- Accept compiles/replays verified delta against originals;
- Reject removes proposal only.

**Critical safety rule:** unsupported sandbox dependency must STOP; never silently edit originals instead.

---

# 4. Undo and history

## Native Undo

Graphisoft supports grouping many modifications into one `ACAPI_CallUndoableCommand` scope.

Best long-term implementation: small native Safe BIM executor/add-on owns the entire stage command. Independent external Tapir JSON calls must not be represented to the user as one native Undo stage unless proven.

## Photoshop-like history

A useful Photoshop-like experience is feasible for **Safe BIM stages**.

Safe BIM History should show:

- stage name/time;
- checkpoint;
- affected GUID counts;
- recipe;
- QA result;
- sandbox state;
- native Undo availability;
- rollback actions actually supported.

Do not claim random-access restoration of every arbitrary native Archicad manual action; no complete public Undo-stack enumeration/restoration API has been established.

**Verdict:** own Safe BIM stage history is READY FOR IMPLEMENTATION DESIGN; full Archicad history replacement is NOT SUPPORTED.

---

# 5. Sandbox final verdict

## Best native sandbox architecture

**Design Options + Mark-Up + visual staging.**

- Design Options: geometry isolation.
- Mark-Up: original↔proposal GUID pairs and explicit change set.
- Renovation/highlight: immediate visible difference.
- checkpoint: catastrophic fallback.

## V1 sandbox capability

Enable only explicitly certified Tier-A element classes.

Start with candidates:
- simple standalone Morph;
- simple Wall without hosted openings;
- Slab;
- Mesh;
- single-plane Roof.

Later:
- wall + opening host trees;
- additional host/dependency types.

Do not initially support arbitrary associative dimensions, labels, MEP graphs, stairs/railings/curtain walls, SEO relation networks or hotlink-owned content.

## Accept semantics

Do NOT blindly move sandbox duplicates to main.

Preferred:
1. verify proposal;
2. compute typed delta;
3. verify original baseline is still unchanged;
4. replay delta on original GUIDs through normal protected Safe BIM transaction;
5. verify production result;
6. clean proposal.

**Verdict: SANDBOX V1 ARCHITECTURE READY; LIVE CERTIFICATION NEEDED PER ELEMENT CLASS.**

---

# 6. Renovation final verdict

Renovation status/filter is useful as a visual staging layer because proposal/new elements can be visually obvious.

It is not true isolation: modifying an original and changing its renovation status does not restore the previous geometry.

Use it as:
- proposal visualization;
- changed/new status cue;
- review aid.

Never use it as sole rollback/sandbox mechanism.

**Verdict: READY AS OPTIONAL VISUAL LAYER.**

---

# 7. Continuous QA final verdict

Continuous QA should run permanently but cheaply.

Architecture:

```text
Edit notification
→ dirty GUID queue
→ debounce/coalesce
→ local neighborhood
→ cheap deterministic checks
→ highlight + palette count
→ heavier checks only idle/manual
```

No AI in automatic QA.

## Priority QA v1

1. wall junction topology;
2. reference-line near misses / microgaps;
3. Building Material connection priority;
4. equal-priority 3+ wall junction order/sequence;
5. Layer Intersection Group mismatch;
6. host/opening consistency;
7. Safe BIM receipt/readback state;
8. obvious local overlaps/duplicates;
9. type-specific contour closure where deterministic.

## WallJunctionQA

Inputs are sufficiently documented for implementation:
- wall relation graph;
- reference lines/endpoints;
- `sequence` / junction order;
- Building Material `connPriority`;
- layer `conClassId`;
- collisions/relations as supporting evidence.

Tolerances still require Test_House calibration.

**Verdict: READY FOR READ-ONLY QA IMPLEMENTATION + HIGHLIGHT, AUTO-FIX LATER.**

---

# 8. Similar Selection Engine

Implement deterministic checkbox criteria, not free-form AI matching.

Wall examples:
- type;
- thickness;
- structure;
- height;
- material/composite/profile;
- layer;
- story;
- renovation status.

Fill/Hatch examples:
- fill attribute;
- foreground/background pen;
- foreground/background RGB when applicable;
- hatch subtype/category;
- orientation if requested.

Voice/AI changes checkboxes; deterministic engine selects elements.

**Verdict: LOW-RISK, HIGH-PAYOFF — IMPLEMENT EARLY.**

---

# 9. Voice final verdict

Do NOT load a general LLM for commands like:

> “выбери стены по толщине, конструкции и высоте”

Architecture:

```text
Push-to-talk
→ tiny CPU ASR
→ deterministic Russian intent/slot parser
→ visible checkbox/command state
→ user confirm if ambiguous
```

Candidates for benchmark:
- whisper.cpp tiny/base;
- sherpa-onnx small Zipformer RU.

Selection requires real benchmark on target Legion. Target properties:
- CPU-only;
- near-zero GPU VRAM;
- low RAM;
- fast cold start;
- short idle TTL/process exit.

**Verdict: READY FOR BENCHMARK HARNESS, NOT YET ENGINE SELECTION.**

---

# 10. AI/BIBIM final verdict

BIBIM confirms a useful provider compatibility model:
- Anthropic;
- OpenAI;
- Google;
- local OpenAI-compatible Ollama / LM Studio / vLLM.

Safe BIM should own its AI Broker.

## Recommended reuse

- same local OpenAI-compatible endpoint can be used by BIBIM and Safe BIM;
- Safe BIM may later explicitly import proven non-secret provider/model/base-url settings;
- cloud credentials remain explicit Safe BIM user configuration/protected credential storage;
- do not silently decrypt BIBIM DPAPI secrets;
- do not depend on BIBIM's undocumented per-launch localhost bridge API.

## Resource policy

- deterministic recipe match → AI remains unloaded;
- voice selector → ASR only;
- novel task → load/contact AI;
- produce typed recipe;
- freeze plan;
- unload after idle TTL;
- no GPU-resident model required during normal deterministic execution.

**Verdict: AI BROKER ARCHITECTURE READY; BIBIM BRIDGE DEPENDENCY REJECTED FOR V1.**

---

# 11. Learn without ML / remembered workflows

Store successful work as versioned deterministic recipes.

A recipe contains:
- context fingerprint;
- hard preconditions;
- plan DAG;
- verifier;
- capability requirements;
- safety class;
- evidence/version.

UI suggestion example:

```text
Знакомый случай
junction_v7 — пересечь стены
Совпало: узел 3 стен, структура, слой
[Проверить] [Применить]
```

Do not expose opaque fake similarity percentages unless a defined metric exists.

Known recipes should execute faster than AI because no model loading/planning is needed.

**Verdict: CORE LONG-TERM PRODUCTIVITY FEATURE.**

---

# 12. In-model contextual helpers

Two supported modes:

## Post-edit
Archicad 29 `EditNotificationInterface` → analyze context → palette/notification suggestion → click known recipe.

## Active Safe BIM helper input
Safe BIM owns input → rubber feedback line + custom Pet Palette → one-click geometry operation.

Example:

```text
wall endpoint ───────────── target wall
              довести до стены
              junction_v7
```

Passive native-tool hover interception is not required for v1 and remains unproven.

**Verdict: START WITH POST-EDIT SUGGESTIONS; ACTIVE HELPER MODE SECOND.**

---

# 13. Project-checkpoint caveat

Solo PLN and Teamwork require separate recovery mechanisms.

## Solo
- Save current project is supported.
- exact backup-copy mechanism without unwanted active-document switching requires a controlled implementation/live probe.

## Teamwork
- reservation, ownership, online status, Send/Receive Changes are supported;
- local file copy is not an equivalent rollback model for BIMcloud.

**Verdict: DO NOT SHIP A SINGLE GENERIC “RESTORE PROJECT” BUTTON UNTIL EACH MODE IS CERTIFIED.**

---

# 14. Implementation order — final recommendation

Highest value / lowest risk first:

### Wave 1 — Palette productivity foundation
1. compact Russian palette shell and state machine;
2. context summary (selection/story/project/protection mode);
3. Similar Selection Engine;
4. History UI/data model skeleton;
5. QA issue list + temporary highlight.

### Wave 2 — deterministic QA
6. change notification dirty queue/debounce;
7. WallJunctionQA read-only;
8. microgap detection/calibration;
9. contextual known-recipe suggestion UI.

### Wave 3 — protected execution
10. checkpoint abstraction (solo first);
11. Safe BIM stage history receipts;
12. native C++ grouped-executor prototype for one Undo stage;
13. integrate current safe runtime with native executor contract.

### Wave 4 — sandbox
14. Design Option + Mark-Up prototype;
15. Tier-A element clone/verify;
16. Accept via deterministic replay;
17. Reject/cleanup;
18. optional Renovation/graphic staging.

### Wave 5 — fast human input
19. voice benchmark harness;
20. CPU ASR integration;
21. deterministic Russian intent/slot parser;
22. voice → visible checkbox/command state.

### Wave 6 — AI and experience memory
23. AI Broker with on-demand provider lifecycle;
24. local OpenAI-compatible endpoint support;
25. recipe memory/catalog;
26. familiar-case matcher;
27. AI only for novel/ambiguous tasks.

---

# 15. What should NOT be built yet

- full arbitrary Archicad history replacement;
- silent checkpoint restore for Teamwork;
- universal sandbox for every element type;
- passive interception of every native tool mouse interaction;
- direct BIBIM bridge dependency;
- voice-triggered destructive writes without visible confirmation;
- AI-driven continuous QA;
- one-click auto-fix for wall junctions before the read-only QA corpus is calibrated.

---

# 16. Required controlled probes / measurements

Before relevant features leave experimental state:

1. solo PLN checkpoint-copy behavior on Windows;
2. native grouped Undo prototype with durable Safe BIM ledger ordering;
3. Design Option clone/relink for simple wall/slab/morph;
4. wall + opening host-tree sandbox clone;
5. Mark-Up modification-pair visual behavior;
6. Renovation + Design Option combined review visibility;
7. wall QA tolerance corpus;
8. temporary highlight UX in plan and 3D;
9. whisper.cpp vs sherpa-onnx benchmark on target Legion;
10. AI broker local model unload/TTL benchmark.

Each probe must have one explicit question, evidence capture and fail-closed result.

---

# FINAL ASSEMBLY VERDICT

The feature set is technically coherent and the broad research phase is now saturated.

**READY TO IMPLEMENT NOW:**
- compact Russian Palette prototype;
- Similar Selection Engine;
- Safe BIM History schema/UI skeleton;
- notification-driven incremental QA infrastructure;
- read-only WallJunctionQA + highlight;
- deterministic recipe catalog/suggestion data model;
- voice benchmark harness.

**READY FOR LIMITED PROTOTYPE, REQUIRES LIVE CERTIFICATION:**
- Design Option sandbox;
- Mark-Up review mapping;
- solo checkpoint copy;
- native one-stage Undo executor;
- interactive rubber-line/Pet-Palette helper.

**DEFER / BLOCK:**
- universal sandbox;
- complete native Archicad arbitrary-action rollback history;
- Teamwork whole-project restore;
- BIBIM internal bridge dependency.

The recommended product direction is therefore:

> **Safe BIM becomes a compact Archicad-native productivity and safety layer: deterministic first, AI on demand, recipes learned from verified work, continuous local QA, optional isolated proposals, and explicit history/rollback evidence.**

This directly optimizes the main target: faster project production with less routine and fewer silent modeling defects.