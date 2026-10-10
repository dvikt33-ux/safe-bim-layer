# APA-P10.A01.S03 — AC29 native Opening / Shell contour geometry: new SOURCE delta

- **ПЛАН:** APA-P10 — Independent technical audit AC29
- **ДЕЙСТВИЕ:** APA-P10.A01 — Native SDK and geometry
- **ТЕКУЩИЙ ПОДШАГ:** APA-P10.A01.S03 — Morph/Roof/Shell/Openings/SEO/3D dump; acceptance: coverage/side-effect matrix.
- **UTC:** 2026-10-10T14:39:40Z; **run:** APA-RUN-20261010-143940Z-opening-shell-geom; **executor_run_id:** apa-technical-20261010T1438Z-7f3b6d
- **Phase:** SOURCE; **status:** INFO / SOURCE_VERIFIED for exact docs; SYNTHETIC NOT_RUN, OFFLINE NOT_RUN, BUILD NOT_VERIFIED, LIVE NOT_VERIFIED.
- **Version:** Graphisoft `archicad-api-devkit` ref **29.3100**; no installed header/APX or PLN was accessed. This is a focused increment, not full closure of S03.

## Finding 1 — AC29 typed Opening returns geometry AND distinct parent/cut relations

**Problem.** A host GUID from `ACAPI_Element_GetConnectedElements` alone is insufficient to reconstruct a generic opening's void, shape, direction or the full set of cut elements. This limitation was previously identified; the NEW finding is the dedicated **Archicad 29** high-level API covering these properties in one typed object.

**Primary source read (actual HTML body, pinned 29.3100):**
- [Opening class](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening.html), blob `cde6560da87433b888f7552180fa4a410f3868c9`. `Opening::GetParentElement() -> Result<UniqueID>` returns a parent if present; `GetCutElements() -> std::vector<UniqueID>` returns *all cut elements, including parent*; `GetConnectedOpenings(uniqueId,token)` returns openings cutting the specified element; `GetOpeningGeometry()` and `GetExtrusionParameters()` return typed read-only views.
- [OpeningGeometry](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening_geometry.html) — `GetAnchorPoint()`, `GetVectorX()`, `GetVectorY()`, `GetExtrusionDirection()`, `GetPolygon() -> optional<Geometry::Polygon2D>`. **No custom polygon = nullopt**, not an invalid opening.
- [OpeningExtrusionParameters](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening_extrusion_parameters.html) — `GetShapeType()`, `GetLimitType()`, `GetFiniteBodyLength()`, `GetExtrusionStartOffset()`, `GetWidth()/GetHeight() -> optional<double>`, and separate overridden end/extrusion surface getters. **For Polygonal shape, width/height can be nullopt**; finite length can be absent for other limit types.

**MVP:** first read `Opening::Get()`, geometry + extrusion + parent + cut GUIDs into one semantic record. Use Native Model Dump only to verify actual 3D subtraction/holes, not to infer the cut relation from XY projection. Keep distinct `parent_guid` and `cut_element_guids`; do not assume a single host. Preserve optional fields as null rather than 0.

**Read-only test:** on an unchanged isolated PLN with rectangular, circular, polygonal openings, read shapes and all cut GUIDs; compare the parent inclusion, local basis, optional dimensions and finite/infinite limits with known UI/3D data. PASS: exact agreement and explicit unsupported/hidden errors; FAIL: missing cut element, incorrect shape/basis, false 0 for nullopt; NOT_VERIFIED: no installed 29.3100 provenance or no independent 3D check. **Current: NOT_VERIFIED LIVE.**

**Auditor:** Are the new typed Opening getters actually present in installed AC29 29.3100 headers, and can `GetCutElements` differ from a single `GetConnectedElements` host on the test model? How does renovation/filtering affect the returned set?

## Finding 2 — Shell hole geometry is not a flat XY polygon

**Problem.** Treating shell contour memo coordinates as world XY and ignoring hole depth can displace or erase voids in an APA export.

**Primary source read:**
- [API_ElementMemo, SDK 29.3100](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___element_memo.html), blob `1bf3a607327dbfb4dea1789639126b9cd0499bec`: `shellContours` includes body contour when `hasContour` is true and hole contours when `numHoles > 0`; indexing differs if no outer contour is provided. `morphBody` and `morphMaterialMapTable` are separate memo fields; `roofEdgeTypes` and `sideMaterials` are also separate.
- [API_ShellContourData, SDK 29.3100](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___shell_contour_data.html), blob `02895e8759d10419fa23d4abc7858e7c9af4d6d0`: `plane` is an `API_Tranmat`; contour coordinates are in its **2D coordinate system**; `height` is extrusion depth for a hole, always 0 for outer contour; `id` is 0 for outer contour.
- [API_BodyType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___body_type.html), blob `f5e49417bfae1ea565a1640878c94bb11188db63`: 3D body has `tranmat`, local component counts and parent element. [API_PgonType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___pgon_type.html), blob `76b7b6b23170c195169efb83aea294748841466f`: polygon `iumat` is polygon material reference; not itself a Building Material GUID.

**MVP:** reuse existing 3D dump for final world geometry, supplement with typed shell memo `plane + contour/hole IDs + depth` and morph material-map provenance; avoid reinterpreting 2D coordinates as world XY. Material provenance must distinguish face `iumat`/surface from structural Building Material and overrides. The exact transform convention and 3D parity are **not verified** by this source-only pass.

**Read-only test:** on a disposable shell with one outer contour and two holes, obtain `GetMemo` contours and `Get3DInfo`/3D bodies, compare transformed points and depth with actual cut faces, including case without outer contour. PASS: hole count, plane transformation, extrusion depth and 3D void agree; FAIL: lost/shifted hole or wrong depth; NOT_VERIFIED if geometry is hidden or native data inaccessible. **Current: NOT_VERIFIED LIVE.**

**Auditor:** What is the exact `API_Tranmat` multiplication order in SDK29 for shell contour planes, and how should an absent outer contour be represented in the exported schema?

## Architecture comparison (no invented performance)

| Axis | A: typed AC29 semantic overlay + existing Native Model Dump | B: infer openings/shell holes from raw 3D mesh alone |
|---|---|---|
| Coverage | Shape, extrusion limits, parent/cut GUIDs, shell hole planes + existing 3D | Visible 3D bodies, requires inference for semantics |
| Integration | Read-only native wrapper + external validator; reuse dump | Extensive reverse-engineering of voids/hosts |
| Build effort | Smaller **expected**, not measured; AC29 header/build gate needed | Larger **expected**, not measured |
| Main risks | API availability, optional values, 3D sight parity, local transforms | Lost parent/cut links, ambiguous voids, surface attribution |
| Runtime/performance | NOT_MEASURED | NOT_MEASURED |
| Decision | **A for MVP** with fail-closed parity checks | B only as independent geometric evidence |

## Coverage and side-effects matrix (partial S03)

| Object / operation | SOURCE read | Read-only caveat | Status |
|---|---|---|---|
| Generic Opening shape/extrusion/parent/cut | AC29 typed Opening | nullopt fields, installed SDK provenance, cut parity | SOURCE_VERIFIED; LIVE NOT_VERIFIED |
| Shell contour/hole | ElementMemo + ShellContourData | local 2D plane, optional outer contour, hole depth | SOURCE_VERIFIED; LIVE NOT_VERIFIED |
| Morph material overrides | ElementMemo fields | material map separate from body, mapping untested | SOURCE_VERIFIED; LIVE NOT_VERIFIED |
| Roof SEO/trim | Already covered in earlier `ART-SDK-SEO` | undoable native writer not run | EXISTING SOURCE; LIVE NOT_VERIFIED |
| Full 3D body/face materials | BodyType + PgonType | body transform; face surface not structural material | SOURCE_VERIFIED; LIVE NOT_VERIFIED |

**Proposal for independent audit:** [APA-CAND-20261010-opening-geometry-parity-8e41](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/proposals/APA-CAND-20261010-opening-geometry-parity-8e41.md) — a new focused validation S-ID under P20, `PENDING_AUDIT`, **not yet an executable task**. Audit must check overlap with P20.A01.S02 and S03, and accept/reject via CAS.

**Overall acceptance:** S03 is **PARTIAL** because comprehensive Morph/Roof/Shell/Openings/SEO/3D dump matrix still needs source-to-installed SDK and independent 3D checks. No SOURCE-only finding is called BUILD/LIVE PASS. No changes to main, other branches, PLN, APX, installed software or paid runtime.
