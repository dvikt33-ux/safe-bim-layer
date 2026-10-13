# Native model-first creation and parameter edit package

The existing APA authored generator now creates a connected21-element two-story native test building from one structured intent:10Walls,2Slabs,6Windows,2Doors and1SinglePlaneRoof. Actual project stories0/3m, explicit native material, hosted openings and source-defined bearing/nonbearing roles use the existing BIMGraph/CSE/material pack and SceneWriter. No Morph, new generator or second executor. Documentation expansion was cancelled; accepted PR73 results remain intact.

## Working model and edit cycle

Opt-in outer-wall-face Slab footprints and lowerWall2.8m under0.2m intermediateSlab eliminate the former volumetric overlap. Actual native Roof lower face supplies a measured memo/body offset correction, followed by five native SubtractionUpwards links to upper Walls. Resultant native face/contact areas prove all five sloped underside contacts. Eight exterior Walls read native load-bearing roles and two partitions nonbearing; these are explicit test assignments without engineering capacity acceptance.

Roof level6.0→6.2m preserves itsGUID and raises five dependent resultant Wall caps by0.2m through native SEO. Window width1.2→1.4m preserves itsGUID/host and changes hostWall BREP. Existing model snapshot delta records6then2changed native facts and no added/removedGUIDs. Test parameters are not inferred design dimensions. Drawing rebuild was intentionally excluded from this model-first package.

Two separate clear-zone21-element scenarios were used: creation/edit prototype, then public orchestrator creation/completion. The latter created all21elements, but its following read stage initially rejected GetSolidElementLinks. The route was fixed and known created GUIDs independently reconciled; no Create was repeated. The public completion method can resume a complete verified creation set, but partial or unexpected native relation sets still require manual reconciliation.

Final Save/Open and independent native readback preserve original126accepted signatures (including prior121/109) and edited prototype147. Current168mainGUIDs persist. The completed second building has one connected component of21, native BREP shared faces/host edges and no internal or new-to-retained native volume collisions. Re-evaluating complete junctions and properties makes zero Creates, zeroSEO and zeroproperty writes. Geometry scope remains available regenerated native bodies under existing view filters; bodyless External semantics remain NOT_VERIFIED. No visibleUI inspection is claimed.

## Exact remaining boundaries

True native Grid axes remain blocked: installed CreateObjects has no GridElement tool variation contract. Loaded generic Structural Grid Object is not a nativeGridtool acceptance. Global story edits require a separately authorized project that does not contain accepted geometry. SinglePlane Roof contour/slope editing is not proved by PolyRoof ModifyRoofs. Hosted Door/Window voids work; no new GenericOpening or Stair was created, and the source staircase requirement remains unverified. Requested SEO skipPolygonHoles=true readsfalse: NOT_VERIFIED; the tested Roof is hole-free and hole-bearing scenarios are rejected. Structural/normative acceptance remains NOT_VERIFIED.

A11.S03 stays PARTIAL, A07 dependencies and S10BLOCKED retained. Normative/search/KG implementation, existing documentation and installedAPX/main/master are unchanged. Main orchestrator actually used the existing read-only KnowledgeGraph with GitHub-current plan133. No new roadmap/controller/indexer.

## Published verification

[draft PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74), head`5a3a9201a715a5528c93bed4a5318e2acb32eea7`, exact parentPR73`93557ed0cd59c471b0f903a03708ed88c8feb31b`. Ten code blobs independently match GitHub;15newtests,638/638Windows host and [Windows/Linux CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38394734173)PASS;102upstream tests and actual core/MCP smoke in each environment. Processed [evidence](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261013-121018Z-model-first-building) excludes private paths, PLN and complete technical dumps. Publisher safety flags describe only publication; the approved live isolated test was changed and saved earlier.

Next: supported true native axes contract, separately authorized story-isolated create/edit scenario, then broader qualified host/Roof edits and source staircase. Preserve current168 and never replay accepted creation.
