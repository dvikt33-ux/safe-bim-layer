# APA-P70.A03.S02 — 20 native template AABBs → authored XY translation / existing writer spatial scan

**Date:** 2026-10-11 · **Scope:** S02 spatial-clearance source-only milestone · **Overall task:** PARTIAL, native Create/Modify not approved.  
**Source:** [stacked draft PR #47](https://github.com/dvikt33-ux/safe-bim-layer/pull/47), `feature/apa-authored-spatial-clearance-20261011`, head `03f94e9bb67e01a0944813b25eaea50b1afa0ead` on PR #46.  
**Independent offline CI:** [run #38165025171](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38165025171) **SUCCESS, 275/275 tests** (271 inherited, 4 new).

## 1. What the owner actually measured

Read-only Tapir on PID `96948` port `19724`, exact project `C:\\LocalAI\\APA_Isolated_Writer_Test_01.pln`:
- `status=READ_ONLY_CLASSIFICATION`, `projectUnchanged=true`, `elementCount=20`.
- `GetDetailsOfElements`: **16 Object and 4 Elevation**; 20 detail rows.
- `Get3DBoundingBoxes`: 20 bounded rows, none without a native bbox. All observed `zMin=zMax=0`m.
- Four Object rows (indexes 3, 7, 11, 15) each have `bbox=(-3.862057698..0, -0.361429..+0.33, z=0)`.
- The remaining rows are mainly at `x≈-6 / +27..28` or `y≈-6 / +27..28` bounding the template. The 20 exact owner-provided native AABBs are transcribed as fixture literals in `tests/test_archicad_authored_native_plan.py`, with no synthetic replacement geometry.
- `nativeWriteCalls=0`. No native Create/Modify, no PLN save or deletion.

## 2. Evaluation of the first candidate and alternate location

The previous example authored footprint was `x=0..10`, `y=0..8`, and source story envelope `z=-0.3..6.3`. The original `archicad_scene_run.scan_for_existing_geometry` expands safety by XY `0.35`m and Z `0.1`m; the four near-origin Object AABBs intersect this envelope. **Origin (0,0) fails; do not run the native writer there.**

A source-only proposed shift `(+40m,+40m)` yields footprint `x=40..50`, `y=40..48`, Z envelope `-0.3..6.3`; safety scan limits are `x=39.65..50.35`, `y=39.65..48.35`, `z=-0.4..6.4`. All **20 current user-provided** AABBs are outside this bounding volume. This is **offline clearance against this single measured snapshot only** — live `GetAllElements` and `Get3DBoundingBoxes` at the exact target must be rerun before any future mutation.

## 3. Actual source change, no duplicate engine

Added `archicad_semantic_spatial.relocate_authored_xy(layout,dx,dy)`, an **explicit-only**, pure, deep-copy translation in existing semantic module. Moves outline/room rectangular bounds, structural axes and continuous bearing-line spans in world X/Y consistently; load-path links, storeys, CSE and IDs remain unchanged. Refuses nonfinite/out-of-range offsets, unknown axes and malformed layouts. The translated output must still pass existing `compile_spatial`, `compile_authored_native_candidate` and existing BIM graph validation. **No source or geometry is silently repositioned by SceneWriter**.

- [Source module SHA `5cfcfa1ee016703b1d2bf672a2af288901c0229d`](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-authored-spatial-clearance-20261011/scripts/archicad_semantic_spatial.py).
- [Spatial tests SHA `2cefe5f016187016ef4e8bfd434ca94ba0c26326`](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-authored-spatial-clearance-20261011/tests/test_archicad_semantic_spatial.py).
- [Native adapter/owner 20 bbox regression SHA `33ab9a53653e3bd63583dd575510bb58c2dbc40c`](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-authored-spatial-clearance-20261011/tests/test_archicad_authored_native_plan.py).

The owner-measured 20 bboxes are injected into the **original** `SceneWriter.scan_for_existing_geometry` in offline tests:
- proposed (40,40): `nativeElementsInspected=20`, `volumetricBodiesChecked=20`, zero gaps in mock returned bboxes, no `SPATIAL_COLLISION`;
- original (0,0): `SPATIAL_COLLISION` as expected;
- compile moved authored wall and slab plans via existing BIM DAG; resulting slab polygon starts `(40,40)`. Does not create a single native element.

## 4. Safety/acceptance

**OFFLINE_PASS** 275/275 + **USER_SUPPLIED_LIVE_READ_ONLY_CLASSIFICATION_PASS** 20 detailed element rows. **LIVE_SPATIAL_CLEARANCE_NOT_VERIFIED** at proposed +40,+40 position; post-snapshot changes are unknown. `APA-P70.A03.S02` stays **PARTIAL** (requires_approval=true). The original SceneWriter preview is still gated to the historic scratch path; do not bypass it by changing global constants, and do not use saved 45-GUID PLN or the unrelated SyncGuids instance at port 19723. No new test-PLN write permission exists yet.

**Next step:** one short **read-only** collision scan of `C:\\LocalAI\\APA_Isolated_Writer_Test_01.pln` at port `19724` for envelope X40..50/Y40..48/Z−0.3..6.3, under fresh `GetProjectInfo` before and after. Then prepare an exact new target writer binding and reviewed one-shot immutable source plan/approval if and only if the user authorizes that specific mutation. Continue source/CI work in parallel; no repeat of previously verified 25-/45-element legacy scene.
