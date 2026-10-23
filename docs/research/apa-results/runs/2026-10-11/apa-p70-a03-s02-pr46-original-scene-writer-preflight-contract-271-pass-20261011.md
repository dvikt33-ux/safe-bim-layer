# APA-P70.A03.S02 — PR #46: authored scene → original SceneWriter read-only preflight contract

**Task:** `APA-P70.A03.S02` · **Classification:** SOURCE_VERIFIED + OFFLINE_PASS, **PARTIAL overall** · **Date:** 2026-10-11.  
**Code:** [draft PR #46](https://github.com/dvikt33-ux/safe-bim-layer/pull/46) based on [PR #45](https://github.com/dvikt33-ux/safe-bim-layer/pull/45), no merges to main.  
**Proof:** [GitHub CI #38161552863](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38161552863) **SUCCESS: 271 tests, OK**, commit `1a37e5d84bc87d18359db73cd2594d89981a81d0`. **No Archicad native calls** in this run; CI uses mocks.

## Concrete contract defect fixed

`scripts/archicad_authored_native_plan.py::as_existing_scene_writer_preview` previously returned `metrics` without **`dimensionsMeters`**, a required field consumed in the already-existing `archicad_scene_run.SceneWriter._execute_verified_plan` before journaling. Any attempted use of the new authored preview with the native writer could have failed at the entry boundary, regardless of a valid BIM DAG. Source was inspected before modification; **do not confuse valid graph compilation with writer integration readiness**.

PR #46 fills `metrics.dimensionsMeters` as width (authored `xMax-xMin`), depth (`yMax-yMin`) and height (last selected storey level + authored height - first level), checks finite positive dimensions and adds `make_read_only_scene_writer_preview_factory(candidate)`.

The factory:
- Calls the **same** existing authored preview and existing `archicad_bim_graph.compile_graph`, preserving exact source plan hash, pinned Tapir schema, command order, material name and GUID, story ID/name/level pins.
- Requires `x/y` anchors to match the source outline minima, avoiding silent relocation while passing different CLI coordinates; requires the same pinned schema path.
- Freezes the input candidate and returns deep copies so mutations by later consumers cannot corrupt the source proof.
- Retains a strict original path guard: ONLY `C:\\LocalAI\\APA_Test_House_01.pln` can form this preview; the saved evidence copy `C:\\институт проект\\Улучшенная копия APA_Test_House_01.pln` is **not** approved, and **even the old scratch PLN is not authorized for a new mutation by this test**.
- **Does not** call native Create/Modify, create SQLite journals, open a PLN, approve an execution token, grant permissions, or change `SceneWriter`.

The independent synthetic `SceneWriter.preflight` test injects a mock exact scratch project identity, custom `GetStories` mapping, Tapir 1.5.10 version, precisely one BuildingMaterial and empty `GetAllElements`. It checks the original executor's read-only binding, required dimensions, unique native material GUID, no spatial collisions and `liveWriteAuthorized=false`, plus wrong active story and author-anchor/schema mismatches. The output **READY_FOR_EXPLICIT_TEST_RUN** under mock is not evidence that any user PLN is currently clear or authorized.

## Tested and unverified

| Slice | Result | Basis |
|---|---|---|
| `as_existing_scene_writer_preview` returns a complete source contract | OFFLINE_PASS | PR #46 diff, original SceneWriter source, CI 271 |
| `SceneWriter.preflight` receives preview and only native GET methods in synthetic fixture | OFFLINE_PASS | new tests in PR #46 |
| Wrong active story, wrong anchor, changed schema, protected evidence path | OFFLINE_BLOCK/PASS negatives | CI 271 |
| GetStories actual saved copy | USER_SUPPLIED_LIVE_READ_ONLY_PASS | [Prior owner evidence](apa-p70-a03-s02-owner-live-story-material-preflight-and-unnamed-story-native-pins-20261011.md), native 0/1/2 and one material GUID |
| New target PLN completely empty and approved for writes | NOT_VERIFIED | No new isolated user-specified disposable PLN |
| Native CreateSlabs→ModifySlabs→typed readback on new authored plan | NOT_VERIFIED | Existing writer has protected staged modify in its code, but no new authored-plan execution |
| Structural engineering suitability and compliance | NOT_VERIFIED | Authored line/load-path semantic constraints are not calculations |

**Safety conclusion:** Do not execute on the owner's 45-GUID saved copy; do not blindly execute on the earlier `C:\\LocalAI\\APA_Test_House_01.pln` just because an old SceneWriter guard allows that path. The previously used 25-element scene and historical journals cannot be replayed. For a future native test, obtain an **explicit newly created disposable empty saved PLN path**, confirm the expected operations and native story/attribute inventory, and implement an exact target-binding/approval protocol without opening a generic writable path. Only then perform a single controlled native run with durable step state and typed readback. Nothing in this milestone licenses that run.

**Controller outcome:** attach this source/offline report as an additional S02 evidence artifact; retain `PARTIAL` and `requires_approval=true`. Do not advance `P70.A03.S03` solely due to CI success. Next high-value step is a safe dedicated disposable-target request and live preflight (READ ONLY) once the owner authorizes the target; continue offline guards and provenance in parallel.
