# ARENA FULL SYSTEM AUDIT — Safe BIM / Archicad 29 / Tapir 1.5.9

Date: 2026-09-28  
Author: Arena (independent adversarial auditor; did **not** run Archicad)  
Audit branch: `audit/arena-full-system-audit-20260928` (created from `research/archicad-full-capability-audit-20260928` @ `4fedb7c`; `main` untouched)  
Companion artifacts (same branch):

- `ARENA_CAPABILITY_MATRIX_20260928.md` — capability × (Archicad API / Tapir 1.5.9 / Safe BIM v0.1 / Arena runtime) with evidence grades
- `ARENA_LIVE_TEST_PLAN_20260928.md` — executable live experiments (LT-xx) for every UNRESOLVED_LIVE_REQUIRED item
- `ARENA_IMPLEMENTATION_PLAN_20260928.md` — ordered implementation plan with required tests
- `audit/arena-full-system-audit-20260928/ARENA_AUDIT_CYCLE_LOG_20260928.md` — AUDIT → pass → AUDIT cycle record
- `audit/arena-full-system-audit-20260928/TAPIR_1.5.9_COMMAND_INVENTORY.md` — generated inventory of all 250 commands at tag 1.5.9

---

## 0. Evidence discipline used in this report

| Label | Meaning in this report |
|---|---|
| **LIVE_CONFIRMED** | Recorded by the user's live sessions (R0–R4, W1–W8) in committed documents. Arena did not reproduce it; Arena only checked internal consistency. |
| **STATIC_CONFIRMED** | Arena read the exact source: Tapir git tag `1.5.9` (= commit `d0dbb11b13942e014661e1402b07958b70cd9dba`, `ADDON_VERSION "1.5.9"`), official Archicad 29 API reference (graphisoft.github.io/archicad-api-devkit, fetched 2026-09-28), or the Safe BIM repositories. File:line references are to tag 1.5.9 unless stated. |
| **INFERRED** | Reasoned from static evidence; not directly proven. |
| **UNRESOLVED_LIVE_REQUIRED** | Cannot be settled without Archicad; reduced to an executable experiment `LT-nn` in the live test plan. |
| **CONTRADICTED** | A claim in the ChatGPT research docs, the Tapir source comments, or the Safe BIM code that conflicts with stronger evidence. |

Promotion rules honoured throughout: API success ≠ element exists; GUID ≠ durable element; SEO link ≠ evaluated cut; AABB overlap ≠ solid intersection; API capability ≠ Tapir capability; Tapir capability ≠ live behaviour; mock test ≠ live proof.

What Arena executed: Python/pytest test suites of the Safe BIM branches (offline/mock only), `git` archaeology of all 13 branches of `dvikt33-ux/safe-bim-layer`, a full clone of `ENZYME-APD/tapir-archicad-automation` (tag 1.5.9 and the research baseline commit `b1dc828`), and targeted fetches of the official Archicad 29 API reference. **No Archicad session, no Tapir HTTP call, no .pln file was touched.**

---

## 1. Executive summary (what changes after this audit)

1. **The research baseline is not the live build (CONTRADICTED → corrected).** The ChatGPT research documents on the audit branch cite Tapir commit `b1dc828` as "1.5.9 baseline". `b1dc828` is `1.5.9-76-gb1dc828`, `ADDON_VERSION "1.5.10"`, 76 commits and +1727/−357 source lines after the installed 1.5.9 (STATIC_CONFIRMED). Five commands and at least six behavioural fixes present in the baseline do **not** exist in the live add-on — most importantly the fix for **`Get3DBoundingBoxes` crashing Archicad (SIGSEGV) on a Slab that is not drawn in the current window (Tapir #686)**. Every AABB-based preflight, every "background section execution", and every multi-story readback that touches a Slab is a process-kill risk on the live 1.5.9 until proven otherwise (LT-F3). The earlier research branch (`research/archicad29-tapir159-expansion`) had pinned the correct commit `d0dbb11`; the newer branch regressed.

2. **Two Tapir source comments that the research treats as hard limits are contradicted by the official API (CONTRADICTED, STATIC_CONFIRMED).**
   - Morph edge type: Tapir 1.5.9 writes `element.morph.edgeType` through `ACAPI_Element_Create/Change` and its comment says the discard is "Not fixable from an add-on" (`ExtendedElementCommands.cpp:3077–3095`). The official reference documents `ACAPI_Element_ChangeMorphEdgeType(elemID, API_MorphEdgeTypeID)` — "Use this function to change all edge types of a morph element … The ACAPI_Element_Change function does not offer such functionality." Tapir never calls it (grep at 1.5.9 and at `b1dc828`: 0 hits). Edge smoothing at whole-body granularity is a ~10-line Tapir PR, not a Safe BIM limitation.
   - Destructive Morph boolean: `ACAPI_Element_SolidOperation_Create(target, operator, APISolid_Substract|Add|Intersect, &results)` exists ("target and operator elements will be deleted; result elements returned"; requires undo scope; `APIERR_NO3D` unless both are Morphs). Tapir 1.5.9 does not expose it (0 hits). ChatGPT's claim is confirmed; its wrapper spec must add the GUID-replacement lifecycle.

3. **Tapir 1.5.9 already contains most of ChatGPT's "dual-context" primitives — as internal helpers (STATIC_CONFIRMED).** `ExecuteActionForEachDatabase` (`CommandBase.cpp:1016–1051`) switches the *current database* without touching the *front window*, runs an action, and restores; it is used by `GetElementsByType`/`GetAllElements`/`GetSectionElements` (`databases` parameter) and `GetView2DTransformations`. `SwitchCurrentDatabaseToFloorPlan` (`ExtendedElementCommands.cpp:294`) exists because `ACAPI_Element_CreateExt` refuses Window/Door creation with `APIERR_BADDATABASE` when the current database is not the floor plan (issue #532). So `RunInDatabase` is not speculative — it is a generalisation of code that already ships; but the same code shows which API restrictions bite (§E).

4. **Safety architecture verdict.** The v0.1 layer on the audit branch is not a safety layer (§A). The hardened Arena runtime (`arena/tapir159-compat-geometry-c6ab474`) is materially better (checkpointed steps, contract hashes, project-path guard, per-GUID readback, no promotion of geometry-match to APPLIED) but still lacks: a command allowlist on `TapirClient.call`, a Tapir version gate (`GetAddOnVersion` is never called anywhere), a top-level `succeeded` envelope check, and a sandbox allowlist. `qwen_safe_bim_integration.cleanup_copy` on the audit branch is a P0 data-loss path (unchecked `OpenProject` → deletes every Wall in whatever project is open). No branch has CI. All 229 passing checks (108 pytest + 64 subtests + 45 + 62 + 14 bimexec) are offline/mock.

5. **Evidence integrity.** Raw live evidence (integration-result/diagnostic JSON) lived under `%TEMP%` and is excluded by `.gitignore`; only the R4 console transcript and prose summaries are committed. Live claims are therefore currently unverifiable by a third party. Fix: commit evidence under `audit/live-tests/<date>/raw/` with SHA-256 manifest (§A.8).

6. **Verification hierarchy (F).** Arena replaces ChatGPT's five-rung wrapper-first hierarchy with a stock-first ladder that needs **zero** new C++ for rungs 1–4: typed readback → analytic AABB (never `Get3DBoundingBoxes` on Slab in 1.5.9) → `GetCollisions` (stock; evaluated solid intersection with volume tolerance) → built-in quantity properties via `GetPropertyValuesOfElements` → ModelAccess-based `EvaluateElements3D` (Tapir PR that reuses the `AccumulateSolidBodyBounds` precedent already in `ElementCommands.cpp`). Whether `GetCollisions` and built-in Volume reflect SEO-evaluated bodies is the single most valuable live experiment (LT-C1/LT-C2).

7. **Batch atomicity.** All Tapir create/modify batches run in ONE `ACAPI_CallUndoableCommand` whose lambda always returns `NoError` → partial success commits and is one undo step (STATIC_CONFIRMED). `TrimElements` already uses the atomic pattern (returns the real error from the lambda → rollback). The fix is an `atomic` flag in Tapir (tiny), not a Safe BIM `BatchModelTransaction`.

8. **Shared library (J).** The four architecture claims are confirmed with one correction: the right primitive for reusable *assemblies* is not a GSM at all — Tapir 1.5.9 already has `SaveAsModuleFile` (elements → `.mod`) + `CreateHotlinkNodes`/`CreateHotlinkInstances` (stock, native BIM preserved). `SaveSelectionAsSharedLibraryObject` (GSM) should be limited to true parametric objects and deferred.

The full verdict table on the 20 ChatGPT P0/P1/P2 items is in §13.

---

## 2. Baseline facts (all STATIC_CONFIRMED unless labelled)

### 2.1 Repositories and branches

- `dvikt33-ux/safe-bim-layer` audit target branch `research/archicad-full-capability-audit-20260928` @ `4fedb7c` = `main` (`72e9be1`) + 16 documentation files. Code on it is the v0.1 layer only (`safe_bim_layer.py`, 201 lines; `qwen_safe_bim_integration.py`). **Zero tests, zero CI workflows, no dependency manifest.**
- The hardened runtime exists only on `arena/*` branches; newest `arena/tapir159-compat-geometry-c6ab474` (`c6ab474`, 125 files). Merge-base with the research branch is `main` — the research documents never reference the hardened runtime; ChatGPT's architecture was written against v0.1.
- Live-run scripts (W1–W8) and the live-run safety policy are in **no branch**. Raw JSON evidence is git-ignored (`*integration-result*.json`, `*diagnostic*.json`).
- `research/archicad29-tapir159-expansion` (older ChatGPT research) pins Tapir 1.5.9 to `d0dbb11` (correct). The newer audit-branch ledger uses `b1dc828` (1.5.10-dev) as baseline (incorrect for the live build).

### 2.2 Tapir 1.5.9 vs research baseline

| Item | Tag 1.5.9 (live) | `b1dc828` (research baseline) |
|---|---|---|
| ADDON_VERSION | 1.5.9 | 1.5.10 |
| Commands (generated docs) | 250 | 255 (+`ImportClassificationsXml`, `ImportPropertiesXml`, `UpdateClassificationItems`, `UpdateClassificationSystems`, `UpdatePropertyGroups`) |
| `Get3DBoundingBoxes` Slab | `ACAPI_Element_CalcBounds` for all types except Roof/Zone (ModelAccess body bounds) and Stair (#563 sub-element union) → SIGSEGV when the slab is not drawn in the current window (#686) | Slab routed to ModelAccess body path ("to avoid a crash, not for precision") |
| `ModifyTexts` height only | ignored | fixed |
| Drawing `isCutWithFrame` flag only | ignored (#651) | fixed |
| Beam `circleBased` | missing | present |
| Navigator `sourceNavigatorItemId` | missing | present |
| Label on Slab crash | present (INFERRED from diff comments) | fixed |

Everything in §B–§K was verified against the **1.5.9** source; where the baseline differs it is stated.

### 2.3 Live environment (LIVE_CONFIRMED per committed docs, not by Arena)

Archicad 29, Tapir 1.5.9, port 19723, sandbox `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`, trusted Building Material `922C639B-9875-48DF-A3FC-E0A8AC5F2839`, composite `35A9ED6F-2F29-4400-B7DE-9C0DEA93A499` (0.287 m), stories 0/1/2/3 at 0/4.5/8.2/11.2 m. R4: 21/21 element types present, 40 PASS / 2 DIFF (Beam height/width with non-null profileId), detailed readback unsupported for Opening and Stair.

---

## 3. Domain A — Safety architecture

### A.1 Choke points and bypasses

| Finding | Grade | Location |
|---|---|---|
| `TapirClient.call` is public, un-allowlisted, no envelope check, no version gate, in v0.1 **and** in the Arena runtime | STATIC_CONFIRMED | `safe_bim_layer.py` both branches |
| v0.1 swallows transport/command errors into `ids=[]`; positional readback matching; `_read_details([])` on empty writes | STATIC_CONFIRMED | v0.1 `safe_bim_layer.py` |
| `qwen_safe_bim_integration.cleanup_copy`: `client.call('OpenProject')` result unchecked → `GetAllElements` + `DeleteElements` of every Wall in whatever project is open | STATIC_CONFIRMED, **P0** | audit branch |
| bimexec is a separate offline planner/validator with fakes; separation is real but nothing prevents importing `TapirClient` directly | STATIC_CONFIRMED | `bimexec/` |
| No Tapir version gate anywhere (`GetAddOnVersion` never called); schema pinned to `tapir-1.5.8.json` while live is 1.5.9 | STATIC_CONFIRMED / CONTRADICTED vs "verify exact 1.5.9" | both branches |
| No sandbox allowlist; Arena runtime has a project-path equality guard (`ResumableExecutor._assert_project`) but any path is accepted as a job target | STATIC_CONFIRMED | `safe_bim_runtime.py:356` |
| Arena runtime: SQLite checkpoint per step, `attemptId`, `contractHash` (SHA-256 of prepared contract), `executionIdentity` bound to job/position/attempt/project, `preexistingGuids` foreign-identity check, readback via per-GUID `GetDetailsOfElements`, geometry MATCH never promoted to APPLIED | STATIC_CONFIRMED (good) | `safe_bim_operations.py:64–115`, `safe_bim_runtime.py` |
| Arena runtime issues `GetNavigatorItemTree` + `ChangeWindow` before **every** write (`ensure_active_story`) | STATIC_CONFIRMED (cost; necessity UNRESOLVED → LT-E1) | `safe_bim_layer.py` arena branch |

**Verdicts**

- ChatGPT: "Safe BIM fail-closed runtime remains the only intended production write authority." **MODIFY.** Intent is right, but the audited code does not enforce it. Required (all in Python, no Archicad needed to test):
  1. `TapirClient.call` becomes private (`_raw_call`) and the public path is `call(command, params, *, capability)` where `capability` is looked up in a static allowlist `{command: {"mode": read|write|dangerous, "min_tapir": "1.5.9", "schema": ...}}`. Unknown command → `CapabilityError` (fail-closed). Dangerous commands (`OpenProject`, `CloseProject`, `SaveProject`, `QuitArchicad`, `DeleteElements`, `DeleteAttributes`, `DeleteNavigatorItems`, `SetLibraries`, `SetStories`, `PublishPublisherSet`, `PrintView`, `TrimElements`, `CreateSolidElementLinks`, every `Modify*`) require an explicit `intent` token from the planner.
  2. Session handshake, mandatory before the first write: `GetAddOnVersion` must equal the pinned version (`1.5.9`); `GetProjectInfo.projectPath` must be inside the sandbox allowlist **and** the project must carry a Safe BIM sandbox marker (`GetProjectInfoFields` → field `SAFEBIM_SANDBOX_TOKEN`, written once with `SetProjectInfoField` when the sandbox is provisioned). Path equality alone is insufficient (the same path can host a production file after a copy).
  3. Envelope validation: every response must satisfy `succeeded is True` and `result` present; per-item `ElementIdOrError` arrays are split into ids/errors — an error item is a failure of the step, never `ids=[]`.
  4. `cleanup_copy`: delete the function; cleanup must be a planned job whose delete list is the exact GUID set recorded in the job's receipts, executed only after `_assert_project` passes.
- ChatGPT: "version gates". **ACCEPT**, with the concrete rule that the allowlist stores `min_tapir`/`max_tapir` per command and behavioural quirks are keyed by exact version (e.g., `Get3DBoundingBoxes` on Slab forbidden for `== 1.5.9`).

### A.2 Transactions / partial writes (P0 #4)

- STATIC_CONFIRMED: `CreateElementsCommandBase::Execute` (`ElementCreationCommands.cpp:51`), `ExecuteCreateWithElements` (`ExtendedElementCommands.cpp:937`) and `ExecuteModifyWithResults` (`:954`) wrap the whole array in one `ACAPI_CallUndoableCommand` whose lambda **always returns `NoError`**. Failed items produce per-item errors while successful items commit. One JSON call = one undo step. Tapir has no `Undo` command (inventory checked).
- STATIC_CONFIRMED counter-example: `TrimElements` returns the real error from the lambda → Archicad rolls the whole command back. The atomic pattern is already in the codebase.
- **Verdict on ChatGPT's C++ `BatchModelTransaction` / "high-level transactions": MODIFY.** Simplest correct fix is an optional `"atomic": true` request flag in the three shared executors: on the first item error, return that error from the lambda (rollback) and report `executionResults` for all items with `"rolledBack": true`. Until that PR is deployed, Safe BIM must (a) run **preflight-all-then-write** per batch and (b) size batches so that a partial commit is always reconcilable: every created GUID is written to the checkpoint before the next item, and a partial batch is classified `PARTIAL_APPLIED` with a compensating delete list — never retried blindly.
- Required tests: fake-BIM test where item 2 of 3 fails → executor state `PARTIAL_APPLIED`, compensating list = [guid1], no automatic retry; live LT-A2 (one invalid `buildingMaterialId` in a 3-wall batch; expect 2 walls present in 1.5.9, and 0 with the atomic flag).

### A.3 Project identity, sandbox, modal state

- Arena runtime: `ModalStateError` detection and `_assert_project` exist (STATIC_CONFIRMED). Add the sandbox token (§A.1) and a **pre-write `GetCurrentWindowType`** check with an explicit list of window types in which writes are allowed (FloorPlan only for element creation until LT-E2 proves otherwise).

### A.4 Undo / rollback

- Rollback is not available from Tapir. Safe BIM's compensation must be explicit deletes of receipt GUIDs. Because `DeleteElements` is itself a batch that partially commits, compensation must be verified by `GetElementsByType`/`GetDetailsOfElements` absence check, and a failed compensation is `UNKNOWN_OUTCOME` (human).

### A.5 Fail-closed dependencies (Building Material, Composite, Layer, Font)

- Composite thickness rule from `WALL_COMPOSITE_THICKNESS_FAILURE_AUDIT.md` (`thickness` must equal the verified skin sum; never pick nearest composite) — **ACCEPT**; already consistent with `CreateComposites` schema (skins with `thickness`, separators = skins+1) and `GetComposites`.
- Attribute resolution must be GUID-based with a per-session `GetAttributesByType` snapshot; attribute **index** is never durable identity (indices shift after `DeleteAttributes`). Same rule for library parts (§J).
- Fonts: **no font enumeration in Tapir 1.5.9** — `AttributeType` enum lacks `Font`; texts take only `fontIndex` (STATIC_CONFIRMED). See §H for the favorites-based alternative.

### A.6 Attribute/material resolution in live docs

- W3 composite thickness LIVE_CONFIRMED; consistent with the static rule. No contradiction found.

### A.7 Concurrency

- `safe_bim_lock.py`: process + thread exclusion on the SQLite DB path (crash-released file lock). Adequate for one Archicad instance. Not linked to the Archicad instance identity — if two Archicad instances run, the lock does not prevent talking to the wrong one; the sandbox token check closes this.

### A.8 Evidence integrity (P0 #5)

- Rule: every live run writes `audit/live-tests/<date>/raw/<run-id>/{request,response}-NNN.json` plus `MANIFEST.sha256`; summaries must cite raw file names; `.gitignore` exceptions for that path. Without this, LIVE_CONFIRMED claims are unverifiable and cannot be re-graded by Arena.

---

## 4. Domain B — Morph subsystem

### B.1 Facts (1.5.9, `ExtendedElementCommands.cpp`; unchanged at `b1dc828`)

| Fact | Grade |
|---|---|
| `BuildMorphBodyFromGeometry` (2583–2751): Solid requires ≥4 vertices / ≥4 polygons, Surface ≥2 / ≥1; uses `ACAPI_Body_Create/AddVertex/GetOrAddEdge/AddPolygon/Finish`; holes via 0-separator; `filled:false` = wire loop; per-face `surfaceId` (AC27+). **No closedness, orientation, or manifold check.** | STATIC_CONFIRMED |
| `CreateMorphs`: `size` → cuboid else `body`; `floorIndex` optional (derived from `basePoint.z`); **no `layerIndex`** (`additionalProperties:false`); `surfaceId` applied by a follow-up `ACAPI_Element_Change`. | STATIC_CONFIRMED |
| Readback (`AddMorphBodyFromMemo`, 3159–3400): `isClosed` = `Modeler::MeshBody::IsClosedBody()` status bit (not recomputed), `bodyType` = Archicad-owned `elem.morph.bodyType`, `edgeDefault` = `elem.morph.edgeType`. | STATIC_CONFIRMED |
| `ModifyMorphs(body=…)`: `ACAPI_Element_Change(&element,&mask,&bodyMemo,APIMemoMask_All,true)`. | STATIC_CONFIRMED |
| `rotationDegreesZ` (≈6456): mixes tmx rows 0 and 2 over columns 0..3 (including the translation column) — a rotation about world **Y** through the world origin; reproduces W7 `(9950,600,0)→(0,600,−9950)` exactly. | STATIC_CONFIRMED (matches LIVE W7) |
| Edge type: Tapir sets `element.morph.edgeType` in Create (4598–4605) and Change (6502–6511); comment 3077–3095: discarded by SDK, "Not fixable from an add-on"; readback of `edgeDefault` uses the same field. | STATIC_CONFIRMED |
| Official API: `ACAPI_Element_ChangeMorphEdgeType(const API_Guid&, API_MorphEdgeTypeID)` changes **all** edge types of a morph; "ACAPI_Element_Change does not offer such functionality". Tapir never calls it. | STATIC_CONFIRMED (official docs) → Tapir comment **CONTRADICTED** |
| W7D: valid solid → `ModifyMorphs(body)` → `isClosed:false`, `bodyType:"Solid"`; second identical modify NOOP. | LIVE_CONFIRMED (docs) |
| W1 morph read `Surface/isClosed:false` vs W7D `Solid/true` — W1 body likely mis-wound or open; GUID `B23F010E-…` must be re-read (LT-B4). | INFERRED |
| Independent anecdote: Graphisoft community thread 2025-02-24 "After solid operation using api, the morph is not solid" (0 replies) — corroborates that closed status can be lost after API-side operations. | INFERRED (weak) |

### B.2 Answers to the five questions

1. **Is the proposed workaround architecture correct?** Partly. Correct: never send `rotationDegreesZ`; verify `isClosed` after every body write; treat `ModifyMorphs(body)` as untrusted. Incorrect/missing: (a) the ledger treats edge smoothing as impossible — it is a one-call Tapir fix (`ACAPI_Element_ChangeMorphEdgeType`); (b) `isClosed:false` after Change is a *status* flag — the geometry may be perfectly closed; the workaround must decide based on **functional** evidence (volume/collision), not the flag alone; (c) no pre-write topology validation exists anywhere — Safe BIM must own it (B.2.3).
2. **Fix in Tapir, dedicated C++ command, or delete/recreate?** Ordered: (i) *Now*: delete + `CreateMorphs` + relink (`GetSolidElementLinks` → `RemoveSolidElementLinks` → `CreateSolidElementLinks` on the new GUID) — Create is LIVE_CONFIRMED to yield `isClosed:true`; GUID changes, so this must be a GUID-replacing operation with a mapping record (same lifecycle class as `SolidOperation_Create`). (ii) *Cheap experiment*: Tapir PR that uses `APIMemoMask_MorphBody` instead of `APIMemoMask_All` and re-reads `IsClosedBody()`; if the flag is restored, keep in-place modify (LT-B1). (iii) A dedicated C++ command is only justified if (ii) fails and in-place editing is truly required (it is not; morphs used as SEO operators are cheap to recreate).
3. **Validation around Morph body writes.** *Pre-write (Safe BIM, pure Python, unit-testable):* every polygon ≥3 distinct non-collinear vertices; vertex indices in range; for `Solid`: each undirected edge shared by exactly two polygons with opposite direction (closed, orientable 2-manifold), Euler check `V−E+F = 2(1−g)` with genus from hole loops, signed volume > 0 (outward normals) else reverse all loops, no duplicate vertices within 1e-6 m, face planarity within 1e-5 m, no self-intersection for convex-decomposable bodies (cheap AABB pair test + exact triangle test on candidates), computed volume within tolerance of the requested primitive when the body is generated from a primitive. *Post-write:* readback `body.vertices/polygons` count equality after normalisation (Tapir renumbers vertices — compare canonical form), `isClosed==true` for Solid, `bodyType==Solid`, and — for anything that will be an SEO operator — a functional check: `GetCollisions([morph],[probe])` with a probe box known to intersect (LT-B2). Fail-closed: a `Solid` that reads `isClosed:false` is `UNVERIFIED`, never PASS.
4. **Basis axes vs fixing `rotationDegreesZ`?** Both, but the durable abstraction is: Safe BIM computes a full placement `{origin, xAxis, yAxis, zAxis}` from `(pivot, yaw, pitch, roll)` and always sends all three axes (Tapir writes tmx directly). File a Tapir issue for `rotationDegreesZ` with the W7 reproduction, and until fixed put it on the **forbidden-parameter list** enforced by the allowlist. Do not use `RotateElements` for morphs as a primary path (2D rotation about Z only; copy semantics fine) — acceptable as a secondary check.
5. **Wrapper for Morph edge types.** Tapir PR: after Create/Change with `body.edgeDefault`, call `ACAPI_Element_ChangeMorphEdgeType(guid, edgeType)` inside the same undo scope; return `edgeDefault` from readback. Granularity is **all edges** (API limit); per-edge smoothing remains display-override only. Safe BIM exposes `edge_mode ∈ {HardVisible, HardHidden, SoftHidden}` per element, never per edge. Verification: readback `edgeDefault` equals request (LT-B3, requires the PR build).

### B.3 Lifecycle policy

ChatGPT policy (temporary → convert freely; final → last resort + reason + confirmation) **ACCEPT**, plus: every GUID-replacing operation (delete/recreate, `SolidOperation_Create`) must write a `guid_lineage` record `{old_guids, new_guids, operation, receipt}` so links, properties and classifications can be re-applied and audits can follow the element.

---

## 5. Domain C — SEO / Opening / booleans

### C.1 Facts

| Fact | Grade |
|---|---|
| `CreateSolidElementLinks` per link `{targetId, operatorId, operation ∈ Subtraction/SubtractionUpwards/SubtractionDownwards/Intersection/Addition, linkFlags{inheritOperatorAttributes, skipPolygonHoles}}`; per-link `executionResults`; `RemoveSolidElementLinks`, `GetSolidElementLinks`. | STATIC_CONFIRMED |
| `TrimElements` (roof/shell trim, `trimType`, atomic), `RemoveElementTrims`, `GetElementTrims`. | STATIC_CONFIRMED |
| `GetCollisions(elementsGroup1, elementsGroup2, settings{volumeTolerance=0.001, performSurfaceCheck, surfaceTolerance})` → `ACAPI_Element_GetCollisions` (official: "detect collisions between two groups"). Stock, missed by the research hierarchy. | STATIC_CONFIRMED |
| `CreateOpenings` schema: only `ownerElementId, basePoint, width, height`. AC29 path: `CreateOpeningDefault()->PlacePolygonal(parent, point, 4-corner rectangle)`. Tapir comment: PlacePolygonal "evidently normalizes the polygon and keeps only its extents". | STATIC_CONFIRMED |
| Official AC29 docs: `PlacePolygonal` — "The created opening will be **custom**, and use the polygon given as parameter even if the default was set to rectangular or circular"; `Place(parent, point)` uses the default's shape; `OpeningExtrusionParameters::GetShapeType()` ∈ Rectangular/Circular/custom, width/height, `LimitType`, `Constraint`, anchor. | STATIC_CONFIRMED (official docs) |
| Reconciliation: Tapir offset a *rectangle* and saw no change — a rectangle is fully described by its extents, so that experiment cannot distinguish "extents only" from "polygon kept, position normalised to the input point". The Tapir inference is **over-generalised**; polygonal openings are plausible. | INFERRED → LT-C4 |
| `ACAPI_Element_SolidOperation_Create` (destructive Morph boolean) exists; Tapir does not expose it. | STATIC_CONFIRMED (official docs) |
| W8: SEO Subtraction link persists; "body-replaced operator" evidence is link-level only, not evaluated geometry. | LIVE_CONFIRMED (docs) — correctly graded by the research |
| Built-in quantities: `GetAllProperties` lists StaticBuiltIn/DynamicBuiltIn definitions with GUIDs → `GetPropertyValuesOfElements` can read built-in Volume/Area; official `ACAPI_Element_GetQuantities` documents "surface, volume, perimeter, length … all construction elements". Whether these reflect SEO/trim cuts: not provable statically. | STATIC_CONFIRMED existence / UNRESOLVED_LIVE_REQUIRED semantics → LT-C2 |

### C.2 Decision tree (Arena)

```text
intent?
├─ architectural hole in a wall/slab/roof/shell/mesh (through or niche, rectangular/circular/polygon)
│    → native Opening (AC29 PlacePolygonal / Place). Tapir 1.5.9: rectangular only.
│      Circular/polygon: Tapir PR (shape enum + polygonCoordinates). Until then → SEO with a
│      temporary Morph operator (never a permanent Morph, never a destructive boolean).
│      PASS requires: Opening GUID listed by GetElementsByType(Opening) in the owner's database
│      + GetCollisions(probe-in-hole, owner) == no collision + probe-at-jamb == collision (LT-C4).
├─ element-to-element 3D cut that must stay associative (wall under roof, beam through slab,
│  column minus duct chase)
│    → TrimElements when the trimming element is Roof/Shell (native trim, atomic, cheapest)
│    → else CreateSolidElementLinks(Subtraction*/Intersection/Addition) with the operator on a
│      dedicated SEO layer; PASS requires the evaluated-geometry verifier (C.3).
├─ freeform result that is itself the deliverable (sculpted element, terrain cut)
│    → destructive Morph boolean via Tapir PR CreateMorphSolidOperations (GUID-replacing) OR
│      compute the boolean outside Archicad and write the result with CreateMorphs (Safe BIM
│      owns the kernel step; result body is validated by B.2.3 before write). Prefer the latter
│      when the operands are Safe BIM-authored: fewer GUID replacements, fully unit-testable.
└─ temporary construction / operator geometry
     → CreateMorphs on layer SAFEBIM_TEMP (layer set by SetDetailsOfElements after create, because
       CreateMorphs has no layerIndex), lifecycle=temporary, mandatory deletion step in the job.
```

**Verdict on ChatGPT hierarchy (native Opening → SEO → destructive Morph): MODIFY.** Insert `TrimElements` between Opening and SEO for roof/shell cases, and split "destructive Morph" into API-boolean vs. external-boolean-plus-Create. The hierarchy must be selected by *intent*, not tried in order.

### C.3 Minimum evaluated-geometry verifier for a boolean PASS

A boolean result is PASS only when **all** of the following hold (stock Tapir 1.5.9, no new C++):

1. **Link/trim truth**: `GetSolidElementLinks`/`GetElementTrims` lists the exact pair and operation.
2. **Evaluated intersection**: `GetCollisions([target],[operator], volumeTolerance=1e-6)`; after Subtraction the pair must report **no** collision (the operator's volume was removed from the target); after Addition/Intersection the expected relation must hold. Preflight: before linking, the same call **must** report a collision, otherwise the operation is a no-op (`REJECT_NO_OVERLAP`).
3. **Quantity delta**: built-in Volume of the target via `GetPropertyValuesOfElements` before and after; `ΔV ≈ −V(target ∩ operator)` within tolerance (analytic when both are boxes; otherwise ≥ 1% of operator volume as a sanity bound).
4. **Rebuild**: `RebuildView` (or `regenerate:true`) before 2 and 3 in the database whose 3D model is being evaluated.

Live gate (LT-C1, LT-C2): prove that `GetCollisions` and built-in Volume are computed on the SEO-evaluated bodies. If both fail to reflect the cut, the fallback is the ModelAccess `EvaluateElements3D` PR (§F); until then "SEO applied" stays `LINK_ONLY`.

---

## 6. Domain D — Native BIM semantics

| Question | Finding | Grade |
|---|---|---|
| One-GUID gable roof | `CreateRoofs` 1.5.9: multi-plane (uniform `levels[]`) or single-plane (`pivotLine`+`angle`); **no per-edge data**. Official API: `API_PivotPolyEdgeData.levelEdgeData[]` of `API_RoofSegmentData{angle, angleType (API_PolyRoofSegmentAngleTypeID), eavesOverhang, topMaterial, bottomMaterial}` per pivot edge (memo `pivotPolyEdges`). A gable is a per-edge `angleType` on the gable edges. → API capability yes, Tapir capability no. | STATIC_CONFIRMED |
| Revolved Shell vs Morph | `API_ShellType`/`API_RevolvedShellData{slantAngle, revolutionAngle, shellShape, axisBase, segmentation, begAngle…}` exists; Tapir has no `CreateShells`; W4 LIVE only covers roofs. Verdict: for domes/vaults/cones the Shell is the strongest native type (quantities, composites, trims); Morph only when the Shell cannot express it. | STATIC_CONFIRMED |
| Stairs | `CreateStairs` exists in 1.5.9 (baseline polyline, riser/tread, favorite) — the ledger omits it. | STATIC_CONFIRMED |
| Composite/basic/profile walls | Rule set in the failure audit is correct. | STATIC_CONFIRMED |

**Verdicts:** P1 #9 (`CreateShells` wrapper) **ACCEPT** (scope: Extruded + Revolved first). P1 #10 (per-edge roof) **ACCEPT** with exact spec `edgeOverrides:[{edgeIndex, angleType: Sloped|Gable, angle, eavesOverhang, topMaterialId, bottomMaterialId}]` → `memo.pivotPolyEdges`; verification = readback of the same array plus `Get3DBoundingBoxes` zMax equal to the ridge height computed analytically.

---

## 7. Domain E — Plan / Section / Elevation / 3D execution

### E.1 Facts

| Fact | Grade |
|---|---|
| `ExecuteActionForEachDatabase` (`CommandBase.cpp:1016–1051`): `ACAPI_Database_GetCurrentDatabase` → for each id `ACAPI_Window_GetDatabaseInfo` + `ACAPI_Database_ChangeCurrentDatabase` → action → restore. Restores on the normal path only; no RAII/exception guard. Used by `GetElementsByType`, `GetAllElements`, `GetSectionElements` (`databases` param) and `GetView2DTransformations`. | STATIC_CONFIRMED |
| `SwitchCurrentDatabaseToFloorPlan` (`ExtendedElementCommands.cpp:280–320`) because `ACAPI_Element_CreateExt` rejects Window/Door creation with `APIERR_BADDATABASE` unless the current database is the floor plan (#532); walls/columns/slabs/openings created from the 3D window "without complaint". | STATIC_CONFIRMED |
| `ChangeWindow` (`ApplicationCommands.cpp`): `navigatorItemId` → `ACAPI_View_GoToView` (AC27+; applies layer combo/scale/MVO/zoom); `windowType+storyIndex` → `ChangeCurrentDatabase` + `ACAPI_Window_ChangeWindow`; `windowType+databaseId` → same. There is no "change database only" command and no `GetCurrentDatabase` command; `GetCurrentWindowType` exists. | STATIC_CONFIRMED |
| `databaseId`: fixed synthetic GUIDs for FloorPlan (`d5d16dd4-093f-4674-895d-410d634d8c7e`) and 3DModel (`f6a45617-c97c-44c8-9b98-25dbf98c35f3`); all others = `API_DatabaseInfo.databaseUnId.elemSetId`. | STATIC_CONFIRMED |
| `CreateAssociativeDimensionsOnSection` creates in the **current** database; it does not switch. `GetSectionElements` is the only command returning raw section element ids (owner GUID included). | STATIC_CONFIRMED |
| `RebuildView` → `ACAPI_View_Rebuild(&regenerate)` on the current view. | STATIC_CONFIRMED |
| `SaveAsModuleFile` requires the current window to be floor plan/section/elevation/detail (schema text). | STATIC_CONFIRMED |
| `Get3DBoundingBoxes` on Slab uses `CalcBounds`, which dereferences the current window's draw environment → SIGSEGV when the slab is not drawn there (#686). | STATIC_CONFIRMED (baseline fix comment) |

### E.2 Answers to the five questions

1. **Does the dual-context model reduce expensive switching?** For reads: yes, and it is stock today — pass `databases:[…]` to `GetElementsByType`/`GetSectionElements`; no window changes. For writes into section/elevation databases (dimensions, texts, 2D): a database-only switch is what Tapir does internally, so a `RunInDatabase` PR is small (wrap the shared executors in `ExecuteActionForEachDatabase`). The largest measurable win in the *current* Safe BIM is elsewhere: the Arena runtime performs `GetNavigatorItemTree` + `ChangeWindow` before **every** write. Whether that is necessary at all is UNRESOLVED: elements carry an explicit `floorIndex`; only Window/Door creation is known to need the floor-plan *database* (#532), not a particular story. LT-E1 measures create-with-explicit-`floorIndex` while another story is displayed; if readback is correct, the per-write switch is removed (expected ≥2 round-trips and one redraw saved per write).
2. **API restrictions that can invalidate background writes** (all STATIC/official): `APIERR_BADDATABASE` for element creation outside the floor plan database (Window/Door proven; others per type unknown → LT-E2); `ACAPI_Element_SolidOperation_Create` returns `APIERR_BADDATABASE/NOTMINE` on databases it cannot operate on; `CalcBounds` depends on the current **window** draw state (crash class, not error); ModelAccess reflects the last generated 3D model (needs the 3D window/sight rebuilt — "prewarm"); `GoToView` changes layer visibility, which changes what `CalcBounds`, selection and section generation see; undo scopes are per command — a database switch inside a batch is fine, across batches not transactional.
3. **Operations that need the Front Window**: `Get3DBoundingBoxes` on Slab (1.5.9); `GetSelectedElements`/`ChangeSelectionOfElements`/`HighlightElements` (window-bound); `FitInWindow`, `Set3DCutPlanes`, `SetViewRotation`, `GetView2DTransformations` for the front view; `SaveAsModuleFile`; `PrintView`, `GetElementPreviewImage`/`GetRoomImage` (rendering); `RebuildView` (rebuilds the *current* view); `GetPointFromUser`; 3D model generation for ModelAccess. Everything else is current-database-bound.
4. **Nested context restore after exceptions**: C++ side — RAII `DatabaseScope` (save in ctor, restore in dtor, `noexcept`) replacing the manual restore in `ExecuteActionForEachDatabase`; nested scopes form a stack naturally. Python side — forbid nesting (the Arena runtime already raises on nested execution contexts); one flat `database_context(db)` per step that restores in `finally` and then *verifies* by `GetCurrentWindowType` + (new) `GetExecutionContext`; if verification fails the job goes to `PAUSED_CONTEXT_UNKNOWN` — never continue writing in an unknown context.
5. **Durable database identity**: `(project sandbox token, databaseId GUID [= databaseUnId for generated DBs], databaseType, navigator item name, marker element GUID)`; re-resolve each session via `GetNavigatorItemTree` → `GetDatabaseIdFromNavigatorItemId`; never persist navigator item *indices* or window order. Fixed synthetic GUIDs for FloorPlan/3D are Tapir constants and may be hard-coded with a version guard.

### E.3 Ghost GUIDs and section dimensions (P1 #11)

Root-cause hypothesis (INFERRED): `CreateAssociativeDimensionsOnSection` called while the current database is the floor plan creates the dimension in the floor plan (or fails silently per item) — the returned GUID is real but lives in the wrong database, so the section never shows it. The stock existence check is: `GetElementsByType(elementType=Dimension, databases=[sectionDb])` must list the GUID (STATIC_CONFIRMED that the command supports this). **ACCEPT** the "create → read in target DB → PASS" rule, with the stock command named. LT-E3 verifies both the ghost mechanism and the check.

**Verdicts:** `GetExecutionContext` **ACCEPT** (tiny Tapir PR: returns windowType, databaseId, databaseType, storyIndex, navigatorItemId; also exposes `ACAPI_Database_GetCurrentDatabase`). `RunInDatabase` **MODIFY**: implement as an optional `database` parameter on the shared create/modify executors (reusing `ExecuteActionForEachDatabase`), not a generic "run any command in DB" wrapper (which would re-open the #532 class of failures for element creation). Context scheduler / batch rebuild / prewarm **ACCEPT as planner-level grouping** (no C++), with the measurement in §G. `RebuildDatabase` **REJECT** as separate primitive — `RebuildView(regenerate)` after a `ChangeWindow(databaseId)` covers it; add only if LT-G2 shows the window switch dominates.

---

## 8. Domain F — Off-screen 3D / geometry verification

### F.1 Facts

- Tapir 1.5.9 already uses ModelAccess: `AccumulateSolidBodyBounds` (`ElementCommands.cpp` ≈4020–4050) calls `ACAPI_ModelAccess_Get3DInfo` and iterates `API_Component3D` bodies (`nPgon`, world-space `xmin..zmax`) for Roof/Zone/Stair bounds. STATIC_CONFIRMED. This is the exact precedent an `EvaluateElements3D` command would extend (vertices/polygons per body → volume by divergence theorem, closedness by edge adjacency, body count).
- `ACAPI_Element_CalcBounds` is "model extent of an element of the current database" — window/draw-state dependent; not geometric truth. STATIC_CONFIRMED.
- `GetCollisions` is stock (§C). Built-in quantity properties readable via `GetPropertyValuesOfElements` (§C). `ACAPI_Element_GetQuantities` exists (official) but is not exposed by Tapir.

### F.2 Arena hierarchy (replaces ChatGPT's list)

| Rung | Mechanism | Cost | Proves | Never proves |
|---|---|---|---|---|
| 1 | Typed readback `GetDetailsOfElements` (supported types only; Opening/Stair/Shell/Skylight/Dimension/Railing unsupported in 1.5.9) + `GetElementsByType(databases=[target])` existence | 1 call | parameters persisted, element exists in the intended DB | geometry, cuts |
| 2 | **Analytic AABB** computed by Safe BIM from readback (wall axis+thickness+height; slab polygon+level+thickness; morph vertices) — `Get3DBoundingBoxes` only for types safe in 1.5.9 (never Slab) | 0 calls | gross placement | intersection |
| 3 | `GetCollisions` with `volumeTolerance` | 1 call per pair-set | evaluated solid overlap / non-overlap (if LT-C1 passes) | which faces |
| 4 | Built-in Volume/Area via `GetPropertyValuesOfElements` (property GUIDs snapshot from `GetAllProperties`) | 1–2 calls | quantity effect of cuts (if LT-C2 passes) | topology |
| 5 | `EvaluateElements3D` (Tapir PR, ModelAccess) | 1 call | per-body closedness, volume, bounds, polygon count — evaluated | visual correctness |
| 6 | Visible 3D / `GetElementPreviewImage` | slow | human review | — |

### F.3 Proposed `EvaluateElements3D` contract (Tapir PR)

```json
// request
{"elements":[{"elementId":{"guid":"…"}}],
 "options":{"database":{"guid":"…"} /* optional; default current */,
            "rebuild3D": true,          // regenerate the 3D model for the element set before reading
            "includeBodies": false,     // return per-body polygon counts & vertex hashes
            "volume": true, "closedness": true, "bounds": true}}
// response (per element, same order)
{"results":[{"elementId":{"guid":"…"},
  "status":"Evaluated|No3DModel|NotGenerated|Error",
  "bodyCount":2, "solidBodyCount":2, "wireBodyCount":0,
  "isClosed":true,                // all solid bodies closed (edge adjacency computed, not the status bit)
  "volume":0.4532,                // sum of signed volumes of closed bodies, m³
  "surfaceArea":3.921,
  "bounds":{"xMin":..,"yMin":..,"zMin":..,"xMax":..,"yMax":..,"zMax":..},   // from body vertices, world space
  "polygonCount":12, "vertexCount":8,
  "geometryHash":"sha256-of-canonicalised-vertices-and-faces",             // stable across sessions for regression
  "error":{"code":0,"message":""}}]}
```

Implementation notes: reuse `Get3DInfo`/`GetComponent` (`API_BodyID`, `API_PgonID`, `API_PedgID`, `API_EdgeID`, `API_VertID`); ModelAccess reflects the last 3D generation — `rebuild3D` must either open/rebuild the 3D sight or return `NotGenerated` honestly; never `CalcBounds`. `geometryHash` gives a regression-test primitive that does not need images.

**Verdicts:** ChatGPT `EvaluateElements3D`/`GetElementQuantities` **ACCEPT with the contract above** and ordering: rungs 1–4 first (stock), rung 5 only after LT-C1/LT-C2 show what stock cannot prove. `GetConnectionTable` **REJECT for now** (`GetConnectedElements`/`GetRelationsOfElements` exist in 1.5.9). "Temporary Sight/session abstraction" **REJECT** (no evidence it is needed; `rebuild3D` option covers it).

---

## 9. Domain G — Performance

Benchmark methodology (applies to every item): 30 repetitions per scenario on the sandbox, warm and cold, record per-call wall time from the Python client (`time.perf_counter`), report **median and p95**, interleave A/B variants (ABAB…) to cancel drift, log Archicad window type and story per run, pin Tapir/Archicad versions in the result file, commit raw timings under `audit/perf/<date>/`. Never compare numbers across different projects or window states.

| Item | Expected benefit | Correctness risk | Complexity | Measure live | Simpler alternative |
|---|---|---|---|---|---|
| Batch/undoable scope (one call per batch) | fewer round-trips, one undo step | partial commit (§A.2) until `atomic` flag | low (Tapir already batches) | LT-G1: 1×N vs N×1 create | preflight-all + small batches |
| Preflight-all then write | avoids mid-batch failure | preflight ≠ live acceptance (races with user) | low | count of preflight rejects | already required |
| Fail-fast batch | limits blast radius | none | low (Tapir `atomic`) | LT-A2 | — |
| Minimal rebuilds | fewer redraws | stale readback if rebuild skipped before verify | medium | LT-G2 rebuild cost | rebuild only before verification rungs 3–5 |
| Context grouping | fewer window switches | wrong-DB writes if grouping is wrong | medium | LT-E1 | drop per-write `ChangeWindow` if LT-E1 passes |
| Fewer JSON round-trips (readback batching) | linear speedup on readback | per-item error attribution | low | LT-G3: per-GUID vs batched `GetDetailsOfElements` | batch readback with order check by GUID |
| Caches (story/attribute/library) | avoids re-reads | stale after user edits/attribute deletion | medium | hit-rate | snapshot per job + invalidate on any write/attribute call |
| Event-driven invalidation | freshness | Tapir notification commands (`SetElementNotificationClient`) untested | high | — | per-job snapshot (simpler) |
| Capability handshake | prevents 1.5.9/1.5.10 drift | none | low | — | §A.1 (required anyway) |

Verdict on P2 #17–#20: #17 **ACCEPT (promote to P0 — it is a safety control)**; #18 **MODIFY** (per-job snapshot, not event-driven); #19 **ACCEPT** as planner grouping; #20 **MODIFY** (Tapir `atomic` flag + batched readback; no new transaction layer).

---

## 10. Domain H — GOST/SPDS documentation engine

Arena does not invent GOST requirements. Findings on the *engine* architecture:

| Requirement class | Parameterizable? | Auto-verifiable with 1.5.9? | Notes |
|---|---|---|---|
| Text heights / fonts / pens per role | yes (`TextStyleSettableDetails`: `fontIndex`, `height` mm, `penIndex`, `widthFactor`, `fixedSize`) | height/pen/index yes; **font family no** (no font enumeration) | favorites-based creation (below) |
| Line types / weights per role | yes (`CreateLines`, `CreatePenTables`, `GetLines`, `GetPenTables`) | yes (attribute readback) | — |
| Dimension chains on plan/section | partially (`CreateAssociativeDimensions`, `…OnSection` presets: WallCompositeFaces, WallSkinBorders, SlabCompositeFaces, SlabSkinBorders, BeamOrColumnRefLineEndPoints, BeamOrColumnBoundingBoxCorners, DoorWindowWallHoleCorners, DoorWindowModelHotspots; `CreateWallThicknessDimensions`; `GetDimensionData`) | existence + `GetDimensionData` readback | placement offsets are policy, not normative |
| Scale/view-dependent rules | yes (`Get/SetViewSettings`, `GetModelViewOptions`, layouts) | yes via view settings readback | rule evaluation must take `(scale, viewType)` inputs |
| Layout/title block | `CreateLayout`, `CreateLayoutSubset`, `GetLayoutSettings`, autotext | partial | — |

**Font resolution (P1 #14): MODIFY.** Creation path today without any C++: define Safe BIM-owned Favorites in the sandbox/template (`SB_TEXT_GOST_2_5`, `SB_TEXT_GOST_3_5`, `SB_LABEL_…`) and use `favoriteName` in `CreateTexts`/`CreateLabels` — the favorite's settings are applied first and explicit fields override (schema text, STATIC_CONFIRMED). Verification: readback `fontIndex` equals the favorite's `fontIndex` snapshot. Audit path (checking arbitrary existing texts by font *name*) still needs a Tapir PR `GetFonts` (enumerate `API_FontID` attributes → `{index, name}`); keep `ResolveFontByName` as a thin client of it.

**`GostComplianceAudit` architecture: ACCEPT with structure** `RuleSet(version, scale, viewType) → Rule{id, normative_ref | policy, selector (element type/layer/role), predicate over readback, severity, auto_fixable}` → `AuditReport{rule_id, element GUID, observed, expected, grade}`; normative vs policy separation is a field on each rule; every rule must declare which readback fields it consumes so unsupported types are reported as `NOT_AUDITABLE` rather than PASS. P1 #15 remains open; no live evidence yet (LT-H1 = favorites font roundtrip).

---

## 11. Domain I — Profiles / Composites

Facts (STATIC_CONFIRMED, schema at 1.5.9): `CreateProfiles` copies geometry from `sourceAttributeId` and/or builds from `newSkins` (AC27+ caller polygons with `edgeOverrides`), `skinOverrides` by `skinId` from `GetProfiles`, `wallType/beamType/coluType/handrailType/otherGDLObjectType` flags, `overwriteExisting` by id/index/name. `CreateComposites`: `useWith`, `skins[{type Core|Finish|Other, buildingMaterialId, framePen, thickness}]`, `separators` (= skins + 1), `overwriteExisting`. R4 DIFF: beam `height/width` readback differs when `profileId` is non-null (LIVE) — profile-driven dimensions must be verified from the profile, not the element fields.

Contracts (Arena):

- `CompositeBuilder.preflight(spec)`: all BM GUIDs resolve via `GetBuildingMaterials`; `sum(skins.thickness) == requested_total ± 1e-6`; skin order/type list equals spec; name collision policy explicit (never silent overwrite of a composite used by elements → check `GetElementsByType` filter by `compositeId` first). `postconditions`: `GetComposites` returns the attribute with equal skin list; `attributeId` stored (never index).
- `ProfileBuilder.preflight(spec)`: polygons simple, non-self-intersecting, CCW outer/CW holes, min edge length ≥ 1 mm, area > 0, skins non-overlapping (pairwise polygon intersection area < 1e-9), each skin's BM resolves; when `sourceAttributeId` is used, `GetProfiles` snapshot taken first and `skinId`s validated against it. `postconditions`: `GetProfiles` readback polygon canonical form equals request; a test element (beam/column) created from the profile on `SAFEBIM_TEMP` and its `Get3DBoundingBoxes` extents equal the profile bounds (profile elements are safe for `CalcBounds`? — not proven; use analytic bounds until LT-F3 result), then deleted.
- `ElementRecipe`: `{intent, structure ∈ Basic|Composite|Profile, attribute refs by GUID, geometry, verification plan (rung list), lifecycle}`; a recipe is executable only if every attribute ref resolved in the current session snapshot (fail-closed).

Tests: pure-Python unit tests for all preflight predicates (self-intersection, thickness sum, skin overlap); fake-BIM test for attribute-in-use overwrite refusal; live LT-I1 (composite create+wall+readback) and LT-I2 (profile from `newSkins` + beam + readback).

---

## 12. Domain J — Shared library

Claims: (1) Embedded Library insufficient for cross-project reuse — **CONFIRM** (project-local by definition; `AddFilesToEmbeddedLibrary` only). (2) Linked Local Library is the correct basic mechanism — **CONFIRM** (`AddLibraries`/`SetLibraries`/`GetLibraries`/`ReloadLibraries` exist; `SetLibraries` replaces the local set — use `AddLibraries`, never `SetLibraries`, from Safe BIM). (3) Auto-attach behaviour — **CONFIRM with guard**: `GetLibraries` → attach only if the canonical path is absent → `ReloadLibraries`; duplicate-attach regression test required; note `SetLibraries` docs say set libraries *before* opening a file to avoid the missing-library dialog (modal risk for `OpenProject` flows). (4) Runtime library-part index is not durable identity — **CONFIRM**; resolve per session by `GetAvailableLibraryParts` name + subtype (+ UniID when exposed).

**Better alternative to `SaveSelectionAsSharedLibraryObject` (P1 #16): MODIFY.** Two different needs were conflated:

- Reusable **assemblies** (a standard bathroom, a stair core, a repeated unit): use stock `SaveAsModuleFile(moduleFilePath, elements)` → `.mod` in `SAFE_BIM_LIBRARY/Modules/` → `CreateHotlinkNodes` + `CreateHotlinkInstances` in other projects. Elements stay native BIM (walls remain walls; quantities, composites, openings intact), versioning = file versioning + `ChangeHotlinkInstances` update; dedupe by source path is built into `CreateHotlinkNodes` (AC26+). Constraint: `SaveAsModuleFile` requires the front window to be a plan/section/elevation/detail (front-window operation). Live LT-J1.
- Reusable **parametric objects** (furniture, fixtures): GSM. There is no stock Tapir command; a C++ command would need `ACAPI_LibraryPart_*` creation with generated GDL from element geometry (via ModelAccess) — a large, risky item; defer until a concrete object need exists. When built: write into the shared folder, subtype from `GetAvailableLibraryParts`, `ReloadLibraries`, verify by `GetAvailableLibraryParts` filter, never overwrite a GSM that `GetElementsByType(Object)` shows in use without a version bump (new file name), Teamwork/BIMcloud libraries out of scope.

---

## 13. Domain K — Arrays / revolve

- `MoveElements`/`RotateElements` have `copy:true` (STATIC_CONFIRMED schema) — planner-level arrays are feasible **but** each copy is a new GUID returned only via the command's result; verify each by readback (rung 1) and by count. `RotateElements` is 2D (begin/end/origin points) — no tilt. Progressive scale is not available (no scale command) → **REJECT** "optional progressive scale".
- Figures of revolution: Revolved Shell (native) > Morph body generated by Safe BIM (validated by B.2.3) > SEO composition. Until `CreateShells` exists, Safe BIM-generated Morph bodies are the only route (LIVE_CONFIRMED that arbitrary bodies create closed via `CreateMorphs`).

---

## 14. Tests & CI audit

State: every passing check is **unit/mock or integration-without-Archicad**; there are **no** live tests in any branch and **no CI**. Audit branch: 0 tests. Arena branch: 108 pytest + 64 subtests + bimexec 45/62/14 (run by Arena on 2026-09-28, all green; `pytest bimexec/tests` is not collectable because `test_all.py` raises `SystemExit` at import — run the three scripts directly).

Missing regression tests (all implementable offline against a fake Tapir unless marked LIVE):

| Bug | Test | Layer |
|---|---|---|
| Morph closedness after body replacement | planner refuses `ModifyMorphs(body)` for lifecycle=final; delete/recreate path emits lineage record; fake returns `isClosed:false` → step `UNVERIFIED` | unit + LIVE LT-B1 |
| `rotationDegreesZ` | allowlist rejects the parameter; axis computation unit tests (yaw 90° about pivot p maps known points) | unit |
| Edge type write | request carries `edgeDefault`; fake readback mismatch → FAIL (post-PR: LIVE LT-B3) | unit |
| Ghost GUID existence | created dimension GUID not listed by `GetElementsByType(databases=[target])` → FAIL | unit + LIVE LT-E3 |
| Composite thickness semantics | thickness ≠ skin sum → preflight reject; nearest-composite selection forbidden | unit |
| Partial-write batch | item 2 of 3 fails → `PARTIAL_APPLIED`, compensation list, no auto-retry | unit + LIVE LT-A2 |
| Invalid Building Material dependency | unresolved GUID → fail-closed before any write call recorded | unit |
| Database/context restoration | fake raises mid-step → context restored and verified; nested context refused | unit |
| Library duplicate attach | `GetLibraries` already contains path → no `AddLibraries` call | unit |
| GOST role resolution | role → favorite mapping missing → `NOT_AUDITABLE`, no default font | unit |

CI: GitHub Actions running `pytest` for the runtime + the three bimexec scripts + JSON schema validation of every request fixture against `tapir-1.5.9.json` (to be generated from the 1.5.9 `command_definitions.js`, replacing the 1.5.8 pin).

---

## 15. Verdict table — ChatGPT P0/P1/P2 items

| # | Problem | ChatGPT proposal | Arena verdict | Arena alternative / key change | Remaining live evidence |
|---|---|---|---|---|---|
| P0-1 | `ModifyMorphs(body)` closedness | workaround architecture | MODIFY | delete+create+relink now; Tapir memo-mask experiment; functional verification, not the flag | LT-B1, LT-B2 |
| P0-2 | `rotationDegreesZ` | avoid, use axes | ACCEPT + | forbidden-parameter allowlist; upstream issue with W7 repro | none (STATIC+LIVE closed) |
| P0-3 | SEO proof weaker than evaluated | quantity/ModelAccess wrappers | MODIFY | stock `GetCollisions` + built-in Volume first; `EvaluateElements3D` after | LT-C1, LT-C2 |
| P0-4 | partial batch writes | C++ transaction | MODIFY | Tapir `atomic` flag (pattern exists in `TrimElements`); `PARTIAL_APPLIED` state | LT-A2 |
| P0-5 | evidence files lagging | update docs | MODIFY | raw evidence + SHA-256 manifest committed; ungrade claims without raw files | — |
| P1-6 | edge smoothing wrapper | new API wrapper | MODIFY | `ACAPI_Element_ChangeMorphEdgeType` call in Tapir (all-edges) — comment "not fixable" CONTRADICTED | LT-B3 |
| P1-7 | polygon Opening | `shape` + polygon extension | ACCEPT + | `PlacePolygonal` documented as custom polygon; Tapir "extents only" inference over-generalised | LT-C4 |
| P1-8 | destructive Morph boolean | `CreateMorphSolidOperations` | ACCEPT (modified lifecycle) | `SolidOperation_Create` confirmed; GUID-replacing lineage; external-boolean+Create as alternative | LT-C5 (post-PR) |
| P1-9 | Shell wrapper | `CreateShells` | ACCEPT | Extruded + Revolved first | post-PR |
| P1-10 | per-edge roof | wrapper | ACCEPT | exact `pivotPolyEdges` spec | post-PR |
| P1-11 | section dimension existence | GetDetails in target DB | ACCEPT | stock `GetElementsByType(databases=[…])` named as the check | LT-E3 |
| P1-12 | background DB execution | `RunInDatabase` etc. | MODIFY | `database` param on executors + `GetExecutionContext`; RAII restore; no generic runner | LT-E1, LT-E2 |
| P1-13 | off-screen verifier | `EvaluateElements3D` | ACCEPT (contract §F.3, after stock rungs) | ModelAccess precedent in Tapir | LT-C1/C2 first |
| P1-14 | font by name | `ResolveFontByName` | MODIFY | favorites for creation now; `GetFonts` PR for audit | LT-H1 |
| P1-15 | GOST engine | new engine | ACCEPT (architecture §H) | rule schema with normative/policy split, NOT_AUDITABLE | — |
| P1-16 | shared library save | `SaveSelectionAsSharedLibraryObject` | MODIFY | `.mod` + hotlink for assemblies (stock); GSM deferred | LT-J1 |
| P2-17 | capability negotiation | handshake | ACCEPT → **P0** | version gate + allowlist | — |
| P2-18 | event-invalidated caches | events | MODIFY | per-job snapshot | — |
| P2-19 | group by database | scheduler | ACCEPT (planner) | — | LT-E1 |
| P2-20 | high-level transactions | fewer round-trips | MODIFY | `atomic` + batched readback | LT-G1/G3 |

---

## 16. Contradictions register

| # | Claim | Stronger evidence | Grade |
|---|---|---|---|
| 1 | Research baseline `b1dc828` = Tapir 1.5.9 | `git describe` = `1.5.9-76-gb1dc828`, `ADDON_VERSION 1.5.10` | CONTRADICTED |
| 2 | Tapir comment: Morph edge type "Not fixable from an add-on" | official `ACAPI_Element_ChangeMorphEdgeType` | CONTRADICTED |
| 3 | Tapir comment: `PlacePolygonal` "keeps only its extents" | official docs: custom polygon used; experiment used a rectangle | CONTRADICTED as a general claim (INFERRED) |
| 4 | Safe BIM v0.1 "verify exact 1.5.9" | schema pinned 1.5.8; no version gate | CONTRADICTED |
| 5 | "Safe BIM fail-closed runtime is the only write authority" | public unguarded `TapirClient.call`; `cleanup_copy` | CONTRADICTED (today) |
| 6 | Ledger omits `CreateStairs`, `GetCollisions`, `SaveAsModuleFile`/hotlink route | 1.5.9 inventory | corrected |
| 7 | Ledger: `MorphBody` "no fillet/chamfer API" | not contradicted (edge *type* ≠ fillet) | STATIC_CONFIRMED |

---

## 17. Residual risks and open questions (only confirmed items)

1. Live 1.5.9 `Get3DBoundingBoxes`+Slab crash class (STATIC from upstream fix; not yet reproduced live) — until LT-F3, treat as real.
2. Whether `GetCollisions` / built-in Volume operate on SEO-evaluated bodies (LT-C1/C2) — determines whether stock Tapir can ever grade a cut as PASS.
3. Whether element creation with explicit `floorIndex` is correct while another story/window is active (LT-E1/E2) — determines the per-write `ChangeWindow` cost and the background-write design.
4. `ModifyMorphs(body)` root cause (Archicad status flag vs geometry) — LT-B1/B2.
5. `PlacePolygonal` true shape (LT-C4, needs Tapir PR build or the temporary Morph probe design).
6. Evidence integrity: all LIVE_CONFIRMED items are graded on prose + one transcript; raw JSON must be committed before any of them are used as regression baselines.

Everything else in the research documents that Arena examined is either STATIC_CONFIRMED consistent, or corrected above.
