# Safe BIM synthesis passes 121–130

Date: 2026-09-27
Purpose: convert prefinal research into implementation contracts.
Research branch only; no product changes and no Live BIM writes.

---

## Pass 121 — protection-mode state machine

Safe BIM should expose three user-facing modes, not dozens of technical toggles.

### NORMAL

- validate;
- optional preview/highlight;
- standard Safe BIM runtime;
- exact receipts/readback;
- incremental QA.

### PROTECTED

Everything in NORMAL plus:

- mandatory pre-stage Save/checkpoint policy;
- one native Undo stage when the active executor can guarantee it;
- explicit history entry;
- stronger post-stage QA gate.

### SANDBOX

Everything in PROTECTED plus:

- Design Option proposal copy/isolation when supported for the target element class;
- Mark-Up stage/mapping;
- proposal visualization;
- explicit Accept/Reject.

**Fail-closed rule:** if requested SANDBOX operation includes an unsupported dependency class, do not silently fall back to editing originals. Ask user to downgrade mode explicitly or reduce scope.

UI can still expose individual expert checkboxes, but the default mental model is three protection modes.

---

## Pass 122 — stage history and rollback precedence

Each Safe BIM stage should record a `StageRecord` roughly containing:

```yaml
stage_id: SB-184
project_fingerprint: ...
started_at: ...
completed_at: ...
mode: PROTECTED
summary_ru: Изменить стены секции А
recipe:
  id: wall_fix_v3
  version: 3
checkpoint:
  kind: solo_pln_copy
  location: ...
  checksum: ...
native_undo:
  label: Safe BIM — стены секции А
  available_at_completion: true
sandbox:
  option_id: null
  markup_id: null
elements:
  originals: [...]
  created: [...]
  modified: [...]
receipts: [...]
qa_before: ...
qa_after: ...
result: DONE
```

Rollback UI precedence:

1. **Reject Sandbox** if unaccepted isolated proposal exists.
2. **Native Undo Stage** if Archicad still exposes the stage as undoable and identity matches.
3. **Restore Checkpoint** only through an explicitly certified restore procedure.
4. Otherwise show **Manual recovery required**, never simulate success.

Do not auto-chain repeated Archicad Undo calls by a guessed count.

---

## Pass 123 — sandbox v1 support matrix

Initial support should be deliberately small.

### Tier A — enable first

Candidate simple/standalone element types after live clone certification:
- Morph;
- simple Wall without hosted openings;
- Slab;
- Mesh;
- single-plane Roof.

### Tier B — second wave

- Wall + Door/Window host tree;
- simple Object/Column/Beam with known references;
- simple Zone where isolation semantics are verified.

### Tier C — explicit refusal in sandbox v1

Until specifically implemented:
- dimensions/associative labels;
- SEO/trim relation graphs;
- stairs/railings/curtain walls;
- MEP routed topologies;
- hotlink-owned or externally constrained content;
- arbitrary grouped hierarchies.

Rule: sandbox coverage is a capability manifest per element class, not a generic boolean.

---

## Pass 124 — sandbox acceptance compiler

Accepting a sandbox stage must NOT mean “move all sandbox GUIDs into main”.

Preferred algorithm:

1. sandbox recipe has already produced proposal geometry;
2. readback verifies proposal exact GUIDs;
3. compute typed delta between original fingerprint and proposal fingerprint;
4. compile a production plan against original GUIDs;
5. validate project identity and current originals are unchanged from sandbox baseline;
6. execute production plan in standard Safe BIM protected transaction;
7. readback production originals/new elements;
8. only after PASS remove/reject proposal artifacts.

If an original changed after sandbox creation, Accept returns `STALE_BASELINE` and does zero production writes.

This preserves identity and prevents overwriting parallel manual work.

---

## Pass 125 — continuous QA scheduler that must not slow Archicad

QA should be event-driven and budgeted.

Proposed scheduler:

```text
Edit/element notification
→ append GUIDs to dirty set
→ debounce 150–500 ms (configurable)
→ coalesce duplicate GUIDs
→ compute affected local neighborhood
→ execute Tier-0 cheap checks
→ update UI/highlight
→ schedule heavier checks only when idle or explicitly requested
```

### Tier-0 checks (<small local budget>)
- receipt state consistency;
- endpoint near-miss for changed walls;
- wall relation existence;
- obvious invalid host links.

### Tier-1 checks
- detailed priority/junction analysis;
- local collisions;
- contour closure;
- duplicate geometry within neighborhood.

### Tier-2 checks
- whole-floor/full-project audit;
- user-triggered or idle-time only.

Safety/performance rules:

- never run AI in automatic QA;
- never scan all project elements after each edit;
- cancel stale queued QA when newer edits supersede it;
- UI remains non-blocking;
- expose `Проверка: 3 проблемы` rather than intrusive dialogs.

---

## Pass 126 — WallJunctionQA algorithm contract

For each changed Wall `W`:

1. Read wall geometry/reference line and story/layer/structure.
2. Query actual wall relations.
3. Build nearby candidate set within a small endpoint/intersection envelope.
4. For each candidate:
   - determine whether reference lines should intersect;
   - compare layer intersection group (`conClassId`);
   - determine relevant Building Material/component priority where accessible;
   - compare junction order/sequence for equal-priority multi-wall nodes.
5. Classify endpoint/node:
   - `CONNECTED_EXPECTED`;
   - `NOT_CONNECTED_EXPECTED` (e.g. differing layer groups);
   - `MICROGAP`;
   - `MISSING_RELATION`;
   - `AMBIGUOUS_EQUAL_PRIORITY_ORDER`;
   - `UNSUPPORTED_COMPLEX_STRUCTURE`.
6. Highlight only actionable anomalies.
7. Offer certified known fix only when preconditions match exactly.

Tolerance must not be hard-coded from intuition. Calibrate using a Test_House corpus with known 0, sub-mm, mm and cm gaps, plus different scales/units.

No automatic junction repair in continuous QA v1.

---

## Pass 127 — compact Russian palette state machine

Collapsed state target: narrow persistent palette.

Primary buttons:

```text
[Команда / ИИ]
[Вставить код]
[Выбрать похожие]
[История]
[Проверка]
```

### Code state

- click `Вставить код` → open central slot;
- editor supports Safe Recipe first; raw JSON/Python only in expert mode;
- buttons: `Проверить`, `Предпросмотр`, `Выполнить`;
- after successful execution, optional user setting `Сворачивать код после запуска` defaults ON;
- on failure/WAITING_USER/UNKNOWN_OUTCOME remain open.

### AI state

- click `Команда / ИИ` → open AI slot;
- second click closes;
- NEVER auto-close after AI answer;
- context chips: selected count/types, active story, protection mode;
- `Создать план`, not direct “write now”.

### Similar state

Checkbox criteria; voice button changes boxes, user sees result before selection.

### History / QA

Open in same central slot; no simultaneous three-column IDE layout by default.

Backend health appears as a small status dot; Tapir version string only on diagnostics/error page.

---

## Pass 128 — voice benchmark and runtime contract

Voice v1 is a separate tiny service/process, NOT the main LLM.

Benchmark protocol on target Legion:

- 40 fixed Russian architectural phrases;
- 10 noisy/fast variants;
- models:
  - whisper.cpp tiny quantized/non-quantized candidate;
  - whisper.cpp base candidate;
  - sherpa-onnx small Zipformer RU int8 candidate if available;
- CPU-only first;
- thread counts: 1, 2, 4;
- metrics:
  - process cold start;
  - model load time;
  - utterance latency;
  - peak RAM;
  - GPU VRAM (expected ~0 CPU path);
  - word/slot correctness;
  - command intent correctness.

Runtime policy:

- push-to-talk;
- VAD optional;
- short warm TTL (for example 30–120 s, final value benchmark-driven);
- unload/exit after TTL;
- if ASR/parser confidence is low, only fill text box and ask user to confirm.

No voice action directly performs model writes.

---

## Pass 129 — AI Broker and BIBIM compatibility contract

Safe BIM AI Broker should expose a common provider interface:

```text
provider: local_openai | openai | anthropic | google
model: ...
base_url: ...
credential_ref: ...
load_policy: on_demand
idle_unload: ...
```

### Local compatibility

If BIBIM is configured for Ollama/LM Studio/vLLM, Safe BIM can reuse the same OpenAI-compatible URL/model when the user imports or selects it. This avoids multiple model runtimes.

### Cloud compatibility

Safe BIM stores its own credential reference. Optional import from BIBIM must be explicit and must not silently extract DPAPI-protected keys.

### Broker resource policy

- deterministic recipe match → AI not started;
- simple voice selector → ASR only, main LLM not started;
- novel planning → start/provider request;
- freeze typed recipe;
- unload local model after configurable idle window;
- before GPU-heavy Twinmotion workflow, offer/perform AI unload according to user setting.

BIBIM bridge itself is not a stable dependency for v1.

---

## Pass 130 — known-recipe/contextual suggestion scoring

Recipe suggestions must be conservative and explainable.

Proposed context match layers:

1. **Hard preconditions** — element types/count/topology/support class; mismatch means recipe not eligible.
2. **Semantic equality** — relevant structure/material/story/host relation.
3. **Geometric tolerance** — only fields recipe declares tolerant.
4. **Safety capability** — all operations certified in current backend/version.
5. **Freshness** — recipe version compatible with current Safe BIM/Tapir/Archicad contract.

UI should avoid an opaque “96% AI similarity” unless the number has a meaningful defined metric. Prefer:

```text
Знакомый случай
junction_v7 — пересечь стены
Совпало: типы, узел 3 стен, слой, структура
Не совпало: высота стены C (не влияет)
[Проверить] [Применить]
```

A known recipe is still compiled/validated against the current project before execution.

---

# Synthesis after pass 130

The architecture is sufficiently specified for a final assembly audit.

No additional broad research is required before starting implementation prototypes for:

1. compact Palette shell/state machine;
2. Similar Selection Engine;
3. incremental WallJunctionQA read-only/highlight mode;
4. Safe BIM History data model;
5. voice benchmark harness;
6. Design Option sandbox prototype limited to Tier-A elements;
7. future native Safe BIM executor for grouped Undo.

Items that remain live-probe/implementation dependent are explicitly bounded rather than undocumented.