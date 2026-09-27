# Safe BIM UI / Sandbox / History / QA — research passes 91–110

Date: 2026-09-27
Scope: Archicad 29, Safe BIM research branch only. No product-code changes. No Live BIM writes.

## Research objective

Design a compact Russian Safe BIM palette that minimizes occupied Archicad workspace while adding:

- code insertion/execution without PowerShell;
- manually toggled AI panel;
- deterministic similar-element selection;
- staged/visible proposed changes;
- checkpoint + rollback protection;
- continuous geometry QA;
- history/timeline;
- contextual known-recipe suggestions;
- lightweight voice command mapping;
- optional reuse of BIBIM-compatible AI providers.

Evidence grades used below:

- **CONFIRMED** — exact Graphisoft/BIBIM/API documentation or source supports the statement.
- **DESIGN** — architecture proposal derived from confirmed primitives.
- **LIVE_PROBE_REQUIRED** — public API exists but behavior for our workflow still needs one controlled test.
- **UNSUPPORTED/UNKNOWN** — not proven by public API.

---

## Pass 91 — compact one-palette UI

**Finding: CONFIRMED + DESIGN.**

Graphisoft supports an Archicad modeless/dockable `DG::Palette` and browser control / JavaScript connection. A browser control can be used purely as the renderer of one Safe BIM palette; it does not need to appear to the user as a separate “web app”.

Target interaction:

- Russian UI by default.
- Small collapsed palette.
- One expandable content slot.
- `Код`: click opens; after successful execution it MAY auto-collapse.
- `ИИ`: click opens; second click closes; it MUST NOT auto-collapse after an answer.
- Backend/Tapir version is hidden unless compatibility check fails.

Proposed collapsed surface:

```text
SAFE BIM                      ● SAFE
Выбрано: 6 стен   Этаж: 1
[Команда/ИИ] [Код] [Похожие]
[История] [Проверка]
Защита: ☑ checkpoint ☑ подсветка ☐ sandbox
Последний этап: ✓
[Откатить этап]
```

Primary source:
- Graphisoft: Browser control in Archicad and JavaScript connection.

---

## Pass 92 — one Safe BIM action = one native Undo entry

**Finding: CONFIRMED, with backend limitation.**

`ACAPI_CallUndoableCommand` / `ACAPI::CallUndoableCommand` can group a series of Archicad database modifications inside one undoable command. Graphisoft explicitly recommends grouping a user action so the user does not need multiple Undo presses.

Constraints:

- undoable command runs on the main thread;
- nested/conflicting add-on command scopes can return `APIERR_NOTMINE` / refusal;
- complete operations such as project Save cannot run inside an undoable scope.

**Architecture consequence:** a future thin native `SafeBIMExecutor.apx` is the cleanest way to make “one Safe BIM stage = one native Undo item”. Current external Tapir JSON requests must NOT be assumed to combine into one native Undo transaction.

Source:
- Graphisoft Archicad 29 C++ API, Command Scopes: `ACAPI_CallUndoableCommand`.

---

## Pass 93 — pre-stage project checkpoint

**Finding: CONFIRMED API primitive; checkpoint-copy semantics still need validation.**

`ACAPI_ProjectOperation_Save()` exists and is a complete operation. It cannot be called inside undoable/non-undoable command scopes.

Recommended ordering:

1. compile/validate plan;
2. save current project;
3. create checkpoint artifact/copy using a separately verified mechanism;
4. execute model mutation stage;
5. readback + QA.

Open question: exact “save a backup copy without changing the active document path/state” behavior for solo PLN must be proved before implementing automatic checkpoint copies. Teamwork needs a different strategy.

Source:
- Graphisoft Archicad 29 C++ API, Project Operations / `ACAPI_ProjectOperation_Save`.

---

## Pass 94 — Photoshop-like history: what can and cannot be promised

**Finding: partial.**

No public API has been found that exposes Archicad’s entire native Undo stack as a random-access list of historic model states.

However, Safe BIM can build its own reliable stage history because it controls:

- job/step IDs;
- exact receipt GUIDs;
- before/after fingerprints;
- checkpoint identifiers;
- QA result;
- native Undo label when available.

Archicad notifications expose element create/change/delete and Undo/Redo element events, so Safe BIM can also log manual model events while loaded.

**UI rule:** call it **Safe BIM History**, not “full Archicad history”, unless a future API proves full stack access.

Suggested timeline entry:

```text
#184  23:41  Safe BIM: стены секции А
Checkpoint: CP-184
Created: 37  Modified: 12
QA: PASS
Native Undo: available
[Restore checkpoint] [Inspect] [Undo stage]
```

Source:
- Graphisoft Notification Manager.

---

## Pass 95 — Renovation as visual staging

**Finding: CONFIRMED but NOT a sandbox.**

Elements expose renovation status and views use Renovation Filters to show/hide/override Existing/New/Demolished elements.

Useful Safe BIM mode:

- new/proposal elements receive an agreed staging renovation status when appropriate;
- special view/filter makes them visually obvious;
- after every stage the user sees what changed without manually comparing views.

Limitation: changing an existing original element and setting its renovation status does NOT preserve the original geometry. Therefore Renovation is visualization/staging, not rollback/isolation.

Use Renovation as one layer of visibility, never as the sole safety mechanism.

---

## Pass 96 — Design Options as the strongest native sandbox candidate

**Finding: CONFIRMED API surface; dependency cloning requires live certification.**

Archicad 29 `ACAPI::DesignOptions::DesignOptionManager` supports at least:

- `CreateDesignOptionSet`;
- `CreateDesignOption`;
- `CreateDesignOptionCombination`;
- activate/deactivate option in a combination;
- `CanBeMovedToOtherDesignOption(elemGuid)`;
- `RelinkElementToDesignOption(elemGuid, option)`;
- `SetDesignOptionAsDefault`.

This makes a native isolated proposal workflow plausible:

1. create `SAFE BIM SANDBOX` option;
2. duplicate affected originals;
3. move/relink duplicates to sandbox option;
4. mutate only duplicate GUIDs;
5. show main + proposal combination;
6. accept/reject explicitly.

**Critical blocker:** hosted/dependent elements (doors/windows, associative annotations, derived relations) require dependency-closure cloning and must be tested type by type. Do not claim universal sandbox yet.

Source:
- Graphisoft Archicad 29 DevKit `DesignOptionManager` member list.

---

## Pass 97 — Mark-Up / Issue layer for reviewable change sets

**Finding: CONFIRMED and highly relevant.**

`ACAPI_Markup_AttachElements` supports component types and an optional original→modified GUID map for `APIMarkUpComponent_Modification`.

This maps well to Safe BIM proposal review:

- one Mark-Up Issue per Safe BIM stage;
- original GUID ↔ proposed duplicate GUID pairs;
- new/deleted/highlighted elements attached with matching component type;
- native issue/change-review semantics instead of inventing all visualization ourselves.

Mark-Up attachment requires an undoable scope.

**Proposed sandbox stack:**

- Design Option = isolation;
- Mark-Up = explicit original/proposal mapping and review set;
- Renovation / highlight = strong visual contrast;
- checkpoint = catastrophic fallback.

Source:
- Graphisoft `ACAPI_Markup_AttachElements`, `modificationElemTable`.

---

## Pass 98 — temporary highlighting and visible QA

**Finding: CONFIRMED.**

`ACAPI_UserInput_SetElementHighlight` / `ACAPI_UserInput_ClearElementHighlight` allow temporary 2D/3D model highlighting; redraw is required after changing highlight state.

This supports:

- red highlight for broken junctions;
- amber for suspicious microgaps;
- cyan for proposed targets;
- selected Safe BIM history-stage elements;
- “show next error”.

Exact color/style control for every case still needs API/source confirmation; basic temporary element highlighting is confirmed.

Source:
- Graphisoft Archicad 29 C++ API, View Handling.

---

## Pass 99 — wall-junction QA: deterministic, not AI

**Finding: CONFIRMED inputs.**

Important Archicad junction behavior is governed by more than endpoints:

- wall reference lines must geometrically connect;
- Building Material connection priority matters;
- equal-priority 3+ wall junctions use junction order/sequence;
- Layer Intersection Groups can prevent physical intersection even when geometry overlaps.

Relevant API data includes:

- `API_BuildingMaterialType.connPriority`;
- layer `conClassId`;
- wall `sequence`;
- wall reference-line/end coordinates;
- wall structure/material/composite/profile data;
- `ACAPI_Element_GetRelations` / wall connection relations;
- collision APIs for broader checks.

**Deterministic QA proposal:** changed wall → gather local relation graph → compute expected connectivity → detect missing/ambiguous relation → highlight GUIDs.

This directly addresses the user case where three walls meet and one fails to cleanly connect.

---

## Pass 100 — continuous incremental QA

**Finding: CONFIRMED API primitives.**

Archicad supports element observer/notification APIs and Archicad 29 adds `ACAPI::EditNotificationInterface`, which runs after element editing.

Safe pattern:

- callback records changed GUIDs only;
- heavy QA NEVER runs inside the notification callback;
- queue + debounce changes;
- after edit completes, run only local checks affected by those GUIDs;
- update temporary model highlights and palette issue count.

Candidate continuous checks:

- wall junction relation mismatch;
- endpoint near-miss/microgap;
- open/unclosed polygon/contour where applicable;
- invalid/unsupported stage state;
- duplicate or overlapping elements;
- host/opening consistency;
- receipt/readback inconsistencies for Safe BIM-created elements.

Source:
- Graphisoft Notification Manager; Archicad 29 new `EditNotificationInterface`.

---

## Pass 101 — contextual “one-click known fix” suggestions

**Finding: CONFIRMED UI primitives + DESIGN.**

Graphisoft API supports custom Pet Palettes and custom user-input rubber feedback lines.

Therefore a Safe BIM helper input mode can show:

```text
──────────── suggested extension
junction_v7 — пересечь стены
```

A click can execute a previously verified deterministic recipe.

Important scope distinction:

- feasible when Safe BIM owns the current input/helper interaction;
- passive interception of every native Archicad tool edit is not yet proven;
- Archicad 29 edit notifications improve post-edit suggestions but are after-edit, not necessarily native-tool hover interception.

Sources:
- `API_PetPaletteType` / `ACAPI_Dialog_PetPalette`;
- `API_RubberLineType` / user-input API.

---

## Pass 102 — Similar Selection Engine

**Finding: CONFIRMED selection API, deterministic design.**

Archicad supports get/select/deselect selection and selection-change notification. Safe BIM can implement a checkbox selector with type-specific criteria.

Example wall criteria:

- ☑ type;
- ☑ thickness;
- ☑ structure type;
- ☑ height;
- ☐ layer;
- ☐ story;
- ☐ material/composite/profile;
- ☐ renovation status.

Fill/hatch criteria can expose fill type and relevant pen/appearance properties instead of relying on vague “same-looking” AI comparison.

AI/voice may populate checkboxes, but actual comparison and selection remains deterministic.

---

## Pass 103 — Safe BIM metadata inside PLN

**Finding: CONFIRMED.**

Archicad supports Add-On-specific User Data on elements and Element Sets that hold GUID collections plus custom user data.

Potential uses:

- Safe BIM stage ID;
- recipe ID/version;
- job ownership metadata;
- element-set representing one stage/proposal;
- link between project-local model and external SQLite receipt ledger.

Do not make embedded data the sole canonical receipt store; external durable ledger is still valuable for crash recovery.

Sources:
- Graphisoft Custom User Data;
- Graphisoft Element Set Manager.

---

## Pass 104 — project experience memory (“learn without ML”)

**Finding: DESIGN supported by deterministic project primitives.**

A remembered solution should be stored as a versioned **Recipe**, not model weights.

Suggested record:

```yaml
id: junction_v7
human_name: Пересечь стены
context_fingerprint:
  element_types: [Wall, Wall, Wall]
  topology: three_way_junction
preconditions: ...
plan_dag: ...
verifier: ...
safety_class: certified
success_evidence: ...
```

Workflow:

- Safe BIM recognizes a matching context fingerprint;
- palette shows “Знакомый случай: junction_v7 — пересечь стены”;
- one click validates against current model and executes only if preconditions still match;
- AI is not loaded.

AI is fallback for novel/ambiguous cases, not the normal executor.

---

## Pass 105 — voice should NOT use a chat LLM for simple commands

**Finding: CONFIRMED feasible alternatives.**

For commands such as:

> “выдели стены по толщине, конструкции и высоте”

recommended pipeline:

```text
push-to-talk
→ local ASR
→ deterministic Russian intent/slot parser
→ checkbox state
→ visible confirmation
→ deterministic select
```

No general-purpose LLM is necessary.

`whisper.cpp` supports Windows/CPU and small models. Documented approximate memory:

- tiny: ~273 MB;
- base: ~388 MB;
- small: ~852 MB.

`sherpa-onnx` also supports Windows and a dedicated Russian small Zipformer model with `num_threads=1`, plus VAD workflows. This is an attractive candidate for a fast CPU-only voice layer.

Sources:
- ggml-org/whisper.cpp README;
- sherpa-onnx Russian Zipformer documentation and C/C++ API.

---

## Pass 106 — voice resource policy

**Finding: DESIGN.**

For this workstation, voice should avoid competing with Archicad/Twinmotion GPU resources.

Preferred behavior:

- push-to-talk only;
- CPU inference by default;
- process/model starts on first voice use and may remain warm only for a short configurable TTL;
- unload/exit after idle;
- 1 inference thread initially, benchmark 1/2/4 threads later;
- VAD prevents unnecessary decode time;
- grammar/synonym parser handles command mapping.

Benchmark before choosing between `whisper.cpp tiny/base` and `sherpa-onnx small Zipformer RU`; decision should use measured latency and recognition accuracy on the user’s architectural vocabulary.

---

## Pass 107 — BIBIM provider reuse: what is proven

**Finding: CONFIRMED from BIBIM README.**

BIBIM supports:

- Anthropic;
- OpenAI;
- Google;
- local OpenAI-compatible Ollama / LM Studio / vLLM.

On Windows its config is documented at `%APPDATA%\BIBIM\rag_config.json`; cloud keys are protected with DPAPI. BIBIM uses a localhost HTTP bridge between its Archicad add-on and desktop UI, authenticated by a per-launch token from `bridge.json`.

BIBIM is Apache-2.0 open source.

Source:
- `SquareZero-Inc/bibim-archicad/README.md`.

---

## Pass 108 — BIBIM provider reuse: safe integration decision

**Finding: DESIGN / partial.**

Safe BIM should NOT silently decrypt or scrape BIBIM’s private API keys.

Recommended provider architecture:

```text
Safe BIM AI Broker
├─ OpenAI-compatible local endpoint
├─ OpenAI
├─ Anthropic
├─ Google
└─ Optional: Import BIBIM non-secret settings
```

Best compatibility path for local AI:

- BIBIM and Safe BIM both point to the same Ollama/LM Studio/vLLM endpoint;
- no duplicated local model runtime is required;
- Safe BIM has its own load/unload policy.

Cloud key reuse should require explicit user action and Safe BIM’s own protected credential store.

Direct dependency on BIBIM’s localhost bridge is NOT yet recommended: the public README documents the bridge architecture, but not a stable external API contract for third-party callers.

---

## Pass 109 — unified palette AI behavior

**Finding: DESIGN consistent with resource research.**

User-visible design:

- one Safe BIM palette only;
- no PowerShell;
- no separate AI app;
- AI area opens manually and stays open until user closes it;
- closing/collapsing the AI area does not necessarily kill the provider immediately; the broker may use a short TTL;
- model runtime should unload before heavy Archicad/Twinmotion work when idle.

AI output is never sent directly to Archicad. Flow:

```text
Voice/text → AI/intent layer → typed Recipe proposal → Validate → Preview → Safe Runtime
```

Known deterministic recipe match bypasses AI entirely.

---

## Pass 110 — composite protection model

**Intermediate architecture after 20 passes:**

```text
                   SAFE BIM STAGE
                         │
           ┌─────────────┴─────────────┐
           │                           │
       Checkpoint                 Native Undo
      pre-stage save          one command when
       / backup                  executor supports
           │                           │
           └─────────────┬─────────────┘
                         │
                  Sandbox (optional)
       Design Option proposal duplicates
                         │
             Mark-Up original↔proposal
                         │
              Renovation/highlight UI
                         │
                  Continuous QA
                         │
                 Accept / Reject
```

Safety levels should be explicit in UI:

- **Normal** — existing verified production path;
- **Protected** — checkpoint + grouped undo where supported + QA;
- **Sandbox** — duplicate proposal in Design Option + review mapping + QA; originals untouched until Accept.

The current evidence is strong enough to continue designing the sandbox prototype, but NOT enough to claim all Archicad element classes can be cloned with dependencies safely.

---

## Source index

Primary sources used in passes 91–110:

1. Graphisoft Archicad 29 C++ API — Command Scopes (`ACAPI_CallUndoableCommand`).
2. Graphisoft Archicad 29 C++ API — Project Operations (`ACAPI_ProjectOperation_Save`).
3. Graphisoft Archicad 29 C++ API — Notifications Manager / `EditNotificationInterface`.
4. Graphisoft Archicad 29 C++ API — View Handling / temporary element highlight.
5. Graphisoft Archicad 29 DevKit — `DesignOptionManager` member list.
6. Graphisoft Archicad 29 C++ API — Issue management / `ACAPI_Markup_AttachElements`.
7. Graphisoft Archicad 29 C++ API — Pet Palette / User Input / Rubber Line.
8. Graphisoft Archicad 29 C++ API — Custom User Data / Element Set.
9. Graphisoft Archicad 29 C++ API — Wall / Layer / Building Material / Relation structures.
10. Graphisoft Archicad Help 29 — wall intersection priority / junction order / layer intersection groups.
11. `SquareZero-Inc/bibim-archicad` README (Apache-2.0; providers; localhost bridge; config/DPAPI).
12. ggml-org `whisper.cpp` README.
13. k2-fsa `sherpa-onnx` Windows/Russian model documentation.

No live Archicad writes were performed by this research pass.