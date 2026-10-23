# APA №2 BUILD-01 | 2026-10-23 07Z | Engineering integration report

## Concrete new contribution to G2

**A-07Z-01 (99/100): Schema-valid hosted opening may fail AFTER native CREATE.** Pinned Tapir CreateDoors/CreateWindows schema only requires ownerWallId and centerOffset. SceneWriter readback unconditionally requires width, height, sillHeight, centerOffset. Additional authored nativeComponents are schema-checked but lack a separate mandatory writer-field check. A missing dimension can yield KeyError after CREATE. This is a static conditional failure path, not a reproduced native event. Fix: fail-closed exact field check in existing compiler; no second writer.

**A-07Z-02 (98/100): Added Slab/Column defaults are unsafe for writer readback.** Provider schema permits omitted Slab floorIndex/thickness and Column height/width/depth. SceneWriter requires them after CREATE; added Slabs/Beams lack full story/envelope qualification. Base generated slabs do set these fields. Fix: preflight require explicit fields/story/XYZ on nativeComponents.

**B-07Z-01 (97/100): Existing Beam adapter is not connected in authored run_project.** NativeAdapter('CreateBeams') already exists in archicad_connected_components; SceneWriter requires opt-in adapter for Beams, but run_project selects only roof. Graph/preflight may look ready while Beam dispatch is refused before CREATE. Fix: conditionally register existing beam adapter and validate dispatchability in preflight; Beam optional for minimum issue #192 model.

## G0–G5 and evidence

G0 BLOCKED: actual loaded APX SHA, PID/port/PLN, runtime inventory/schema not confirmed. Historical Tapir 1.5.10 provider catalog 262 commands != installed contract. Read-only Get-Process -Module / Get-FileHash + DynamicCommands.probe_runtime recommended; do not WRITE to inspect schema.

G1 SOURCE_ONLY: PR74/162 authored compiler and BIM Graph; two native story bindings, topological DAG and plan hash require actual OFFLINE or read-only preflight. run_project authored mode offline is rejected. Additional Beam/Slab floorIndex/envelope checks required.

G2 SOURCE_ONLY: Walls/Slabs/Beams/Columns/Roof/Doors/Windows exact installed contracts pending. CreateSlabs has no direct structureType/buildingMaterialId. Existing SceneWriter CreateSlabs→ModifySlabs requires separate authorization of both mutations and independent material readback. PR149 story-0 Basic existing verifier not equivalent.

G3 NOT_AUTHORIZED: new scratch PLN exact path/SHA/port/plan hash and owner permission. Existing SQLite intent-before-write; no retry on UNKNOWN. PR126 packed and PR162 group-first deferred, no Clone duplication.

G4 NOT_RUN: actual guarded Save, GUI Close/Open, independent all-database GUID/host/material/BREP; GetModelDumpV1 absent in pinned snapshot, installed registration unknown. Get3DBoundingBoxes is not BREP.

G5 NOT_RUN: new second brief on separate scratch, not historical fixture replay.

30 distinct successful SOURCE checks: 1 issue, 14 PR metadata, 15 fetched files; see checks-A/B. Two independent static counteraudits: schema/writer and dispatcher/runtime/persistence. 9 integration routes in matrix. Upstream Tapir MIT; Graphisoft proprietary; safe-bim-layer license NOT_CONFIRMED. PR162 HEAD f7c37b84b76c040c417ccd58a5543326e50f673a is source, not installed proof. Historical PROJECT_PLAN rev182 read only, NEXT and 61-candidate matrix read only.

SOURCE=30; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. No Windows access, code/APX/PLN/main/NEXT edits, installs, PR merge or paid API. No benchmark or 100x claim. MODEL_MODE_NOT_VERIFIABLE.
