# APA AC29: one-call multi-prototype copy — Column / Beam / Object

## Goal
Extend the existing installed APA receiver, **not** write a special script for each BDD element. Preserve original `DynamicCommands.plan_reuse_existing`, `copy_multiple_prototypes`, `SceneWriter`, `EvidenceAPI`, native Tapir transport, SQLite journal, and the AC29-only stable core.

## Implemented in PR #143

`scripts/apa_ac29_multi_prototype_native_copy.py` implements an explicit typed job `apa-ac29-multi-native-copy/1`. A source task contains a pinned source document, exact approved working PLN path and SHA, **full live GUID-set hash and BREP signature hash**, 1–200 total targets, approved source prototype GUIDs, element families, source anchors, targets and independent CREATE/SAVE scene IDs.

**Supported copy-first families:** `Column` with one owned `ColumnSegment`, `Beam` with one owned `BeamSegment`, and standalone native `Object` with zero owned subelements. A complex beam with multiple segments, hosted object, or Object without verifiable typed origin fails closed. Source and copied native elements must have identical source-relative BREP solids, contour/face topology, materials, home story, lineage and native typed details (apart from explicit horizontal translation). Vertical offsets are not assumed safe. Intersections against existing and other new native bodies are rejected; unsupported roof/host junctions require a separate verified existing semantic adapter.

- The existing `plan_reuse_existing` selects family-matching source prototypes. The chosen copy groups must exactly match user-approved source-to-target assignments. This is not a new selector.
- The existing `copy_multiple_prototypes` sends exactly **one** `MoveElements(copy=true)` call for all groups; root + actual segment GUID deltas are independently checked.
- The existing SceneWriter durable SQLite record, entire-model BREP scope and exact source project identity remain mandatory. No retry, no guessed `CreateColumns` fallback or unsanctioned source mutation.
- After a verified model readback the original dynamic `SaveProject` operation is the only authorized save; independent saved file digest changes and original protected PLN remains unchanged. A partial/unknown native result blocks saving.
- A prior `UNKNOWN_OUTCOME` can be accepted only by the reusable read-only prewrite BREP/GUID reconciliation; no earlier state is overwritten or replayed.

`scripts/apa_ac29_autonomous_job_bridge.py` routes the new `APPROVED_MULTI_PROTOTYPE_COPY` action through the same current local receiver, sharing the existing column job execution path. It requires a **separate local grant** under `controllers/controller-grants/<job-id>.json`, matching exact GitHub job and typed source task blob IDs and user authorization reference. **No such grant is installed by this PR.** GitHub text alone cannot grant model writes. Source task must be pinned by commit+SHA; hardcoded source element coordinates remain absent from shared executor code.

`scripts/upgrade_apa_ac29_multi_native_worker.py` is a one-time pinned in-place release updater for the **existing** Windows receiver, not a second background process. It checks exact known source versions, reuses the existing startup entry and journal, stages 3 changed files, backs up the existing receiver and single-Column helper, stops only the verified APA receiver process, then starts one updated process. It does not enqueue new jobs or write to the PLN. Deployment is **NOT VERIFIED** until an installation receipt appears from the user's Windows environment.

## Actual acceptance level

- Repo implementation + focused CI: **PASS only after current workflow completes**.
- Single native batch for multiple prototypes: **NOT LIVE TESTED in Archicad 29**.
- Beam/Object native typed detail compatibility and body topology on this installed version: **UNVERIFIED**. All such runtime uncertainties fail closed; no success is inferred from CI.
- No writes to user's BDD or source PLN; `main` unchanged. No AC30 development.
- Follow-on native `Create*` and `Modify*` can share `DynamicCommands.run_workflow` once source-qualified individual effects and readback callbacks are available; do not promote unsupported commands merely because a schema exists.
