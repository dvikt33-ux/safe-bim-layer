# Four actual Wall–Roof junctions: native assessment and guarded application

The four original walls have flat caps at absolute Z=6 m. The actual roof underside slopes above them and covers only part of each cap. The working PR63 interior specimen therefore cannot be applied directly as a complete repair of these four boundary walls. Raising a whole wall and cutting only the covered strip would leave an untrimmed strip outside the roof operator.

The new batch adapter runs on current Native Model Dump faces, typed native details, SEO relations and existing Details/CSE context. It measures the real lower-face overlap with holes retained, produces four source-bound plans, and refuses automatic execution for all four current targets. No existing element was created, modified, saved or reopened in this cycle.

| Actual wall | Gap over actual lower-face overlap, mm | Cap covered by lower roof face | Uncovered cap, m² | Direct complete-cap recipe |
|---|---:|---:|---:|---|
| East | 4.516900–1213.598644 | 48.192771% | 1.290000 | NOT_APPLICABLE |
| North | 1186.411288–1213.598644 | 59.063104% | 1.228107 | NOT_APPLICABLE |
| South | 4.516900–22.670110 | 39.436896% | 1.816893 | NOT_APPLICABLE |
| West | 22.670110–1186.411288 | 50.000000% | 1.155000 | NOT_APPLICABLE |

Measurement status is **VERIFIED** for each row. Repair status is **NOT_APPLICABLE** to the unchanged complete-cap Wall-height + Roof SEO recipe. These statuses do not mean that native repair is impossible or that the geometry has been repaired. A selected partial strip could have contact, but that would not resolve the uncovered part of the same junction.

## Four concrete correction plans

Each machine plan binds the exact wall/roof identities, actual BREP hashes, material assignments, home story, native details and current SEO state. Public evidence uses stable identity hashes; exact local GUID payloads are retained for a later explicitly approved copy.

1. **East:** qualify native lower-roof coverage of the measured 1.29 m² outside strip and the cap ends. Retain actual wall thickness/placement. The roof and wall reference lines coincide at the roof boundary; the actual 0.3 m thick wall straddles it. The rising roof also leaves a 4.5169–1213.5986 mm vertical gap over the covered strip. After an approved roof contour solution, remeasure complete cap coverage before preparing Wall height + SEO.
2. **North:** qualify lower-roof coverage of 1.228106884 m² near the high roof edge and cap end. The flat cap is below the high side of the pitched lower face by 1186.4113–1213.5986 mm. Native wall height alone does not resolve the uncovered cap. After an approved native roof-edge solution, remeasure the resulting lower contour and wall joins before SEO.
3. **South:** qualify lower-roof coverage of 1.816893116 m² at the low edge/end. The lower-face contour differs from the nominal roof outline because the actual roof has pitch, thickness and edge geometry. Even the small 4.5169–22.6701 mm vertical gap is not a complete repair while 60.5631% of the cap remains uncovered. Preserve the actual lower-face plane; lowering the whole roof would invalidate the other junctions.
4. **West:** qualify coverage of the measured 1.155 m² outside half of the 2.31 m² cap. The source cap spans 7.7 m after native wall joins and is centered on the roof's west edge. Retain these actual resultant dimensions. The 22.6701–1186.4113 mm gap varies along the roof pitch. A benchmark placed at the roof center does not qualify this boundary case.

For every plan the suitable first alternative is **native SinglePlane Roof contour/edge editing**, retaining roof pitch, thickness, material and story, then the native Wall + SEO operation. The extracted uncovered-cap polygons specify the exact measured coverage requirement; they are not an approved roof overhang design. No extra eaves, fastener, bearing length or load value is invented.

The inspected `ModifyRoofs` source has a runtime guard that rejects all roofs except `API_PolyRoofID`. The actual shared roof is `SinglePlane`. Its schema's `polygonOutline` field alone is therefore insufficient evidence of a supported edit. A native UI or SDK single-plane polygon memo operation is the appropriate next contract to qualify. Converting the roof class or recreating the accepted roof would alter the accepted model and requires a separate target-bound plan and copy authorization. Installed APX is unchanged; exact source/binary correspondence remains NOT_VERIFIED.

The unexecuted Wall candidate uses temporary height **4.411353033 m**, derived only from actual roof highest vertex Z=7.411353033 m and actual wall base Z=3 m. This is an intermediate cutting envelope, not a final wall design height. Roof coverage must be independently qualified first; the blocked candidates cannot be compiled into an executable repair plan.

## Working code path and limits

`archicad_wall_roof_assessment.py` supplies a read-only CLI over captured native data. It reuses `wall_roof_face_overlap`, the existing planar BREP reader, Shapely, Details/CSE source candidates and NetworkX's shared roof dependency graph. Four current plans share one roof dependency. All 73 Details records retain source/assembly blockers; native structural concrete does not imply a manufacturer's product match.

For a qualified, completely covered, straight Basic Wall and Basic single-plane Roof with no holes or existing SEO dependencies, `prepare_wall_roof_repair` compiles the two existing native operations with the existing BIM Graph. `execute_wall_roof_repair` uses the same SceneWriter and SQLite ledger: one exact `ModifyWalls` height edit, then one `CreateSolidElementLinks` upward subtraction. It requires explicit operation/plan/hash authorization in a separately approved saved copy, preserving the source PLN.

Fresh copy identity, saved-file hash, complete native inventory, all protected native signatures, roof BREP/material/story and target typed details are checked. Height readback must preserve the actual cap footprint. Final readback must prove complete real lower-face area, target vertices below the pinned plane, unchanged materials/story/placement, preserved GUIDs and unchanged collision results. Failure or unknown outcome stops the sequence without replay. Save/Open remains a subsequent independent persistence gate.

This application path has **OFFLINE_PASS** with real callback/SQLite tests on synthetic native responses. It has **no new LIVE write qualification** for the four current boundary walls. The earlier PR63 native specimen is historical LIVE_PASS and was not repeated.

## Targeted SEO metadata check

Read-only queries of the retained PR63 specimen from the Wall target and Roof operator sides agree: `skipPolygonHoles=false`, while the recorded request is true. Keep **NOT_VERIFIED_REQUEST_READBACK_DIFFERENCE**.

The inspected serializer maps the boolean to SDK bit `0x00000004`, and the reverse serializer reads the same bit. Both getter branches initialize flags to zero and ignore the SDK `GetFlags` error result. SDK documentation allows database/ownership/argument/link errors. Consequently false does not prove either a successful flags query or the applied operation setting. The existing specimen has no roof holes, so its successful geometry cannot identify the flag's application. Cause and exact installed source/binary correspondence remain NOT_VERIFIED. No APX modification, flag rewrite or ambiguous native retry occurred.

## Acceptance

- Current read-only native baseline: **109 GUID**, all accepted BREP, material and story signatures unchanged; saved PLN hash unchanged.
- Existing Ø200 terminal connection and MEP network unchanged. S10 remains BLOCKED; no repeated transition research or network mutation.
- Four actual geometric measurements and four machine plans completed. No source junction repair executed.
- **26 new tests**, covering cap coverage, holes, unsupported native geometry, typed source constraints, exact approval/plan binding, protected-source rejection, ordered graph, same-writer callbacks and stopping after an unknown outcome.
- Full Windows host suite: **495/495 PASS**. Windows/Linux CI and exact GitHub publication readback are recorded with the published package.
- No new native writes: Save/Open and IFC export are not repeated. The last accepted PR63 persistence/IFC result remains historical evidence, not a new acceptance.
- A11.S03 remains PARTIAL. A04.S01–S03 remain DONE_PUBLISHED. Engineering/load-transfer/manufacturer-family acceptance remains ENGINEERING_NOT_VERIFIED.

Next native step: qualify the single-plane roof contour operation and an approved contour design in a separate saved copy, then rerun the same four-target assessment. Only resulting APPLICABLE_NOT_EXECUTED plans may enter the existing writer after exact copy/operation authorization.

Published code: [draft PR64](https://github.com/dvikt33-ux/safe-bim-layer/pull/64), exact head b056cb76929a62047c82fd66961b72eb4d9078a8 on PR63 head7966db58ca8830b43938a03cc064bcc3e952a21e. All6 committed GitHub blobs match exactly. Windows host495/495PASS; Windows/Linux CI proof attached. Native109 and existing journal/saved-file hash unchanged.


Evidence: [APA-RUN-20261012-185427Z-four-real-wall-roof-native109](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-185427Z-four-real-wall-roof-native109). Draft PR64, head b056cb76929a62047c82fd66961b72eb4d9078a8. Stable SHA tokens replace private native identities; raw payloads stay local. Publication makes zero native calls.
