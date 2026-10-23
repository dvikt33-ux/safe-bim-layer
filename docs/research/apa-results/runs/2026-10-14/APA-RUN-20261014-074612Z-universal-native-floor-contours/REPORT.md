# Editable native floor contours and runtime stability checkpoint

[Draft PR80](https://github.com/dvikt33-ux/safe-bim-layer/pull/80), head `cb73cd578c7cd7577f80397920d9e81b8d09c6e1`, exact starting head PR79 `60a78e0cd55fc4951c1de3c8d060adf4f9538134`; stacked ancestry preserved. Immediate parent `e375a34f68fc7f31a8f77aef0542e5ede54d5132`.

## Implemented and live result

The existing orchestrator/BIM Graph/SceneWriter now consumes explicit per-story nonrectangular contours and true holes. The authored route shares the same geometry validation; walls/rooms over voids are rejected. Parameter deltas change only affected slabs, resend native polygonOutline and all holes, and preserve GUIDs. No second generator, renderer, controller or executor was created.

In the existing explicitly authorized test PLN, one true native Slab was created with an L-shaped10x8m outer envelope,2x2m opening and0.2m thickness. Its contour then expanded to11x8m and its opening to3x2m with the same GUID. Actual native memo and closed BREP top-face contours prove net areas60→62m² and the void; bounding boxes were not substituted. Current accepted Slab material identity was reused exactly.3model writes occurred:1CreateSlabs,1Basic-material/thickness repair and1contour/holeModifySlabs. The delta issued0Creates. Native collision query found no new collisions. These are test parameters, not engineered design dimensions.

SceneWriter Save/Open and a separate final readback prove145GUID, all144previous GUID/geometry/material/story signatures unchanged, including original143. The separate168-GUID project and TRC were not modified/read. Saved-file SHA changed from `831dada412da9cb905566eb09db99b2bcb81976fbd8d7f852f78dc8b431fa91d` to `bfbae730dc65a8cd68dad707685406649f6a3e5ea79f4d63140241043b02f689` through the authorized Save. The existing journal is PASS63/UNKNOWN4; historical unknowns are retained and no ambiguous write was retried. **ARCHICAD_LIVE_PASS** applies to this source Slab create/edit/persistence cycle, not the whole MVP or every floor geometry family.

## Runtime and Stair

Supplemental post-restoration readback resolved the prior pending144 check. Actual original installed module path/SHA, Tapir1.5.10,263fresh commands and Archicad29build5101 were verified. Original APX remains `dc99af071d3dbcff9626653ccc37001613cb3fa4a8eff50c6000c1cc70e8d7c7`.

The new SDK overlay exposes exact source/resource build identity, source revision/MDID and actual local/world Stair baseline frame. Python pins the fresh identity and refuses mismatched SDK dispatch. A stale incremental binary was detected by its embedded old revision; it was rejected, cleanly rebuilt, and the builder now verifies actual APX identity/revision before issuing a receipt. **BUILD_PASS** binary `f6f0861ffb76aced7de89922bdfa5f271d9aa371795c3849cbfe6e585003187f`, source/build identity `0b929f11a7e892b5cab062a9a6dc7bdc77363cec3a59109245f95e18de770eef`, code `cb73cd578c7cd7577f80397920d9e81b8d09c6e1`. Candidate is not installed; runtime identity LIVE remains NOT_VERIFIED.

The old setter discards baseline edge/vertex buffers and retains the old walking-line memo before SolveStair. This is a concrete unqualified preparation path, not a proved faulting instruction. The detached diagnostic candidate reads source/frame/buffer information without calling the setter or solver. Exact create/edit checks complete buffers and remains default-denied without a qualified detached PASS. The original terminating request was not repeated. Stair exact dimensions and engineering suitability remain NOT_VERIFIED. A different APX needs separate deployment authorization.

The live preflight also exposed empty sentinel bounding boxes for hidden Tread/Riser children. Slot-complete native geometry, real Stair ownership and specialized membership now qualify bodyless children without hiding actual parent collisions or relabeling them as2D. Unknown ownership still blocks.

## Measured and published

Actual native operation times, including their readback: create1.002s, edit1.446s, Save3.251s, Open11.458s. Source compilation0.489s is a separate local Python measurement. These are one-component timings, not a large-model benchmark or optimization claim.

**718/718Windows APA tests PASS**,11new regressions,102upstream graph tests and main-core/MCP integration. [CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38527855349). Main orchestrator used unchanged read-only Knowledge Graph at fresh canonical revision148. Raw dumps, full private paths, realGUIDs, source PLN and APX binaries remain local. Artifact-only publisher safety flags do not conceal the earlier expressly authorized native Slab/Save/Open changes reported above.

A11.S03 remains PARTIAL; historical tasks, A07dependencies and S10blocker remain intact. Next: separately authorize/qualify the new runtime identity and safe read-only Stair diagnostic; SinglePlane Roof contour/slope is the next independent native edit contract. Existing test-file native operations are authorized, but APX replacement is a separate permission boundary. Normative/search/documentation implementations are preserved.
