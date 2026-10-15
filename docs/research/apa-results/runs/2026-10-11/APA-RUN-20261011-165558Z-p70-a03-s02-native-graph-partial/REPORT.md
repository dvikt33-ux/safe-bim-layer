# APA-P70.A03.S02 — source/offline milestone: authored geometry → SAME native BIM DAG

**Partial delivery, not full S02 acceptance.** [Draft PR #44](https://github.com/dvikt33-ux/safe-bim-layer/pull/44), stacked on spatial [PR #43](https://github.com/dvikt33-ux/safe-bim-layer/pull/43). [GitHub Actions #38157380799](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38157380799): **258/258 offline tests PASS**. Project Controller claimed task S02 in source-only mode because `requires_approval=true`; **no live native Create/Modify is authorized or attempted**.

## What was built

Existing `archicad_project_accelerator.py` now exposes `compile_authored_native_candidate`, a small adapter to `archicad_authored_native_plan.compile_candidate`, which uses existing `archicad_building_shell.wall/step` helpers and the **original** `archicad_bim_graph.compile_graph`. No second graph, no SceneWriter recreation. All source is in PR #44.

From authored room boundaries/bearing lines (S01), existing project-scoped slab CSE (S03) and **explicit user-authored story heights**, the adapter:
1. Obtains **only** `GetProjectInfo`, `GetStories`, `GetAttributesByType` from caller-supplied read-only adapter; exact PLN identity before queries, unique real story indices/floor IDs and levels, pinned story-label mapping and existing `resolve_basic_slab_material` for exactly one name→GUID.
2. Rejects unknown heights or mismatched story map/material GUID since Project Pack binding. No guess `floorIndex=0`; no silent use of the active floor or a `.bpn` backup.
3. Emits one `CreateSlabs` source operation per **explicit source footprint** and one continuous `CreateWalls` operation per **authored bearing line** (NOT per arbitrary room boundary; no invented openings/partition walls), with endpoints/sizes copied from source constraints.
4. Calls the existing `GRAPH.compile_graph` on a single `{operations:[...]}` value with pinned Tapir schema. Returns native sourcePlanHash, topological order, commands and schema SHA. `liveWriteAuthorized=false`, `nativeWriteCalls=0`, `sceneReservationCreated=false`, `plnChanged=false` regardless of schema success.

**Synthetic demonstration** using two authored walls and two slabs resolves first floor with arbitrary native index **1** and second with index **3** (from injected `GetStories`), and compiles **4** native command candidates. This is not a declaration of a four-element building or a universal dwelling generator.

## Acceptance and blockers

- **Source and offline tests: PASS** [CI #38157380799](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38157380799): 258/258 full suite, including 11 new gate tests for plan geometry, real story indices, authored height 3.0m, precise single BM GUID, exact opened PLN identity, stale story/material, CSE nonapproval, no write token, no duplicate writer, no blind roomBays.
- **Live use: NOT_VERIFIED.** No Archicad localhost calls were made in this milestone, only injected test transport. No PLN/APX/main changes; existing successful 25-step scratch model remains untouched.
- **Missing wall construction-system approval:** S01 carries unbound wall CSE IDs, unverified load-path forces and real structural junction details. The existing 0.2m slab material is only a past user native test; current `CreateSlabs` schema source operation alone **does not guarantee Basic slab material is applied**, as the historical Composite-vs-Basic repair incident showed. Before any native write, S02 requires a durable Create→ModifySlabs staged plan with full typed BM/absolute Z readback, incident-safe journaling (before each call) and exact test PLN approval.
- S02 user approval applies to the **specific** scratch test file and operations only. Prior 45-GUID saved copy is not to be modified, and any old scene reservation must never be replayed.
- Engineering/calculation, roof/stairs/MEP/details/full floor layout and structural realism are still open. **Mark controller S02 PARTIAL**, not DONE. Consequently S03 must remain blocked by dependency until real S02 acceptance.

**Next highest-value work:** generalize a safe one-shot `CreateSlabs` then `ModifySlabs` exact Basic material/story sequence *inside the existing SceneWriter*, and a minimal read-only preflight for the currently open test copy. GitHub CI should run in parallel while source code continues; manual user test is optional/short and must not block offline development.
