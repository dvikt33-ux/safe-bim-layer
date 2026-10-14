# APA Roof / Composite — focused integration gap review (2026-10-11)

**Status:** SOURCE_REVIEW_PARTIAL; no Archicad live/build claims. **Mode:** independent proposal for controller audit; NOT an assigned execution task, NOT DONE_PUBLISHED.

## Evidence pinned
- Archived 71 source files, original Git blobs: [archive commit 477ba54a](https://github.com/dvikt33-ux/safe-bim-layer/commit/477ba54a0620ce7c0efc1b835f1d0ad2f1a03ba5); source contents are historical Tapir 1.5.9-era proposals.
- [Previous source audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-092155Z-source71-byte-archive/REPORT.md): 13/71 content-reviewed; reports historical PolyRoof, Composite Attributes and GDL candidates, not current live compatibility.
- [Existing building-shell compiler](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-highlevel-whole-model-20261011/scripts/archicad_building_shell.py): explicitly WRITES = CreateWalls/CreateSlabs/CreateDoors/CreateWindows. `prepare()` calls existing `archicad_bim_graph.compile_graph` against `schemas/tapir-live-1.5.10/tapir-scene-live.json`, then returns SCENE_PREVIEW_OFFLINE with liveWriteAuthorized=False.
- [Pinned schema](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-highlevel-whole-model-20261011/schemas/tapir-live-1.5.10/tapir-scene-live.json) exists. This pass has NOT exhaustively parsed its roof/composite command contracts.
- [Controller revision 48](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json) defines sole task dispatch and mandatory claim/readback before task work; existing S-IDs should be reused.

## Concrete compatibility gap
1. The building compiler has a strict `validate_spec()` key set and `WRITES` allowlist. Roof or composite cannot be appended merely as new data: require explicit contract extension, operation validation, and deterministic dependency ordering.
2. `wall()` hardcodes `structureType=Basic`; floor slab similarly has no composite binding. Native composite attribute identity/availability in the *open project* must be verified before mutations.
3. A single native `API_PolyRoofID` is an SDK concept from archived research, **not evidence that Tapir 1.5.10 exposes `CreatePolyRoof`**. Prefer current supported command if verified; otherwise the existing native add-on adapter is an optional implementation under the SAME scene execution path.
4. Building-shell preview validates schema offline only. It does not authorize PLN writes, structural or normative certification, or live success.

## Minimal implementation decision gates
**Gate R0 (SOURCE):** enumerate exact roof-related commands and typed fields in pinned Tapir schema; inspect current SceneWriter dispatch, GDL/add-on source and archived PolyRoof evidence. Deliver a verified command matrix with source SHA and unsupported items explicitly flagged.

**Gate R1 (OFFLINE):** introduce optional roof recipe in building-shell input and graph compiler using verified command(s); one predictable gable/roof plane geometry, explicit floor and height relation; keep the current SceneWriter as sole executor. Schema validation, golden JSON, negative cases, graph dependency and deterministic hash tests.

**Gate C0 (SOURCE):** enumerate available Composite Attributes and exact create/modify arguments in current schema / native SDK; distinguish attribute lookup, Basic→Composite transformation, and face material overrides. Require existing attributes and explicit project-context stamp; never guess GUID/index.

**Gate C1 (OFFLINE):** add composite reference bindings to walls/slabs with backward-compatible Basic default; verify attribute prereqs, serialized payload, dependency order and failure behavior. If current write bridge lacks support, mark BLOCKED and implement narrowly in existing native writer, NOT a second orchestration layer.

**Gate L0 (LIVE, separate permission):** on a guarded disposable project only, create a small roof+composite example; read back type, element GUIDs, materials/surfaces, story/elevation and geometry. Record before/after, reversible cleanup and stop if mismatch. No uncontrolled write to production PLN.

## Candidate controller mapping for independent audit
- Existing `APA-P00.A02.S03`: semantic archive mapping / superseded_by remains PARTIAL.
- Existing `APA-P10.A01.S03`, `APA-P10.A02.S01`: roof geometry/API and current Tapir contract audit, subject to controller dependency and claim checks.
- Existing `APA-P70.A03` scope: building compiler product integration only after evidence gates.
**No new S-ID proposed here** until controller task review confirms a nonduplicate work_key.

## Acceptance for this proposal
Report published and read back on this review branch; technical findings only SOURCE_REVIEW_PARTIAL. No controller status mutation, no publisher receipt claim, no current Archicad BUILD/LIVE assertion, no change to main/PLN/APX.
