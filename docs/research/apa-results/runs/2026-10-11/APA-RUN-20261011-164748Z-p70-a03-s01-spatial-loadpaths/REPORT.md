# APA-P70.A03.S01 — authored rooms, structural axes and aligned load-path candidates

**Scope:** Source/offline delivery on [draft PR #43](https://github.com/dvikt33-ux/safe-bim-layer/pull/43). No PLN/APX/main modifications, no live Archicad calls. [GitHub CI #38156894138](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38156894138) **247/247 PASS** (231 inherited + 16 authored-spatial tests). Controller claim was created before implementation at revision 65.

## Implemented on the existing critical path

- Existing Project Accelerator has one new entrypoint `compile_project_spatial_plan(brief, project_pack, authored_layout)`, invoking `archicad_semantic_spatial.compile_spatial`; consumes the typed semantic brief **PR #40** and source-linked project CSE candidate **PR #41**. The next native graph remains the **existing** `archicad_bim_graph.compile_graph`; no second BIM DAG/SceneWriter.
- The new source-only layout **requires authored** (not inferred) rooms with rectangular coordinates and named storeys, reference axes X/Y, continuous bearing-wall candidate lines on an axis and authored room boundary, and explicit upper→lower line load-path references. Validates room min area, footprint containment, per-storey overlap, unique IDs/axes, line thickness/length, collinear wall overlap, adjacent-floor support geometry and duplicate load links.
- Links cross-storey supports **only geometrically**; `forceTransferProved=false`, `engineeringApproved=false`, `normativeApproved=false`, `bimEmissionAuthorized=false`. Unapproved Wall CSE candidates, missing upper-storey load supports and unresolved slab-interface/detail conditions are returned, not silently replaced with generic dimensions.
- Pack and brief must have identical project identity/mode/exact PLN target. One provisional Basic slab CSE from S03 is attached per declared story. No unapproved construction system or manufacturer library is imported; `nativeWriteCalls=0`.

## Tested / known boundaries

[CI 247 PASS](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38156894138) includes 16 new synthetic tests: two storeys, 2 authored rooms and two continuous support lines with candidate alignment; no "0 этаж"; wrong project pack; missing/moved/overlapping rooms; invented axes/unsupported load paths; no wall CSE impersonating slab CSE; duplicate collinear walls; false structural approval; unsupported native graph emission. First CI uncovered a Python syntax typo, corrected on the PR branch; latest PASS is required evidence, not the failed prior run.

**Acceptance level for S01:** semantic geometry and structural *candidates* are offline-validated. This does not establish building code compliance, verified force paths, constructible wall joints, a completed building model, or native CreateElements. An authored 2-wall example is a test of semantics; we did not claim an entire floor plan design or fabricate additional walls.

## Next critical-path substep

**APA-P70.A03.S02** depends on this S01 and requires approval. Work may continue **offline**: map these *authored* continuous wall lines and explicit slab footprints to the **existing** BIM DAG via existing `archicad_building_shell.wall`/ `archicad_bim_graph.compile_graph`; preflight must resolve real project story indices, exact materials and explicit structural/detail blockers. Native Create/Modify on the user's PLN is **not** authorized by this report and must be separately approved for a disposable test copy. Do not replay PR #35 25-step scene; its verified successful readback remains archived.

**No unnecessary user tests requested here.** Next optional user-only test should be a short strictly read-only material/story binding preflight when offline S02 needs real attributes; it cannot block parallel offline development.
