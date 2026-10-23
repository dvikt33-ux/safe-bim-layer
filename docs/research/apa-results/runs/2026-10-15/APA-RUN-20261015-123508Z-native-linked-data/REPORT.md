# Native component, material and IFC continuation after PR97

The existing dynamic router now feeds the existing BIM Graph dependency analysis
with typed native attribute dependencies and IFC identity references. No second
executor, graph database, IFC engine or journal was introduced. Existing Tapir
IFC commands are reused rather than implemented again in C++.

`scripts/apa_native_dependency_flow.py` exposes `capture_ifc_facts(api, router,
element_ids)` for 1–32 explicit elements. The caller supplies the established
EvidenceAPI and dynamic router with source-reviewed READ_ONLY policies. Each
call retains the router's fresh project identity, runtime registration and
input/output schema gates. The returned bundle includes provider replies and a
content hash. IFC properties remain the provider's string representation;
neither empty property lists nor IFC classification prove export compatibility.

`dependency_inputs` accepts existing component replies plus `attributes` keyed
by BuildingMaterial/Surface/Composite, optional envelope replies and `ifc_ids`.
Native attribute index and kind must resolve to one captured attribute GUID.
Names are never used as identity. Disabled overrides and inapplicable structure
material fields do not become dependencies. Material → element and native
element → IFC identity are distinct from parent/root membership, physical
contact and engineering validity. An IFC node uses its own `IFC:` namespace;
attribute nodes use `ATTRIBUTE:<KIND>:`. Missing or ambiguous inputs stay explicit.

The existing grouped SDK readers gained additive typed output fields:

- Opening: bounded native Polygon2D contours with directed edge endpoints and
  arc angles, linked status, anchor parameters and surface override flags/indices.
  The raw SDK frame stays separate; no normalization or assumed world-coordinate
  transform is applied. There is no resultant void BREP claim.
- Shell/Roof: thickness, story-relative level, explicit structure-type material
  applicability and top/side/bottom surface override flags. Existing Shell class
  frames, body flags and memo contour data remain intact.
- CurtainWall/Railing: actual native root parameter counts, height/relative level
  where defined, and reference offsets. Child parent/root queries remain separate.

The original-runtime native run read 13 existing sample/component elements:
12 nonempty IFC IDs, 61 native IFC property rows, and types including
IfcCurtainWall, IfcRailing, IfcSlab, IfcMember and IfcPlate. One element returned
an empty IFC ID/type; it was excluded from IFC identity edges. This is native
accessor evidence, not export or engineering acceptance.

The current attribute headers contain 59 building materials, 132 surfaces and
24 composites. Combined with the pinned earlier native component capture, the
existing dependency analysis produces 196 nodes/319 edges, including 23 material,
17 frame surface and 12 IFC identity dependencies. A selected material reaches
45 dependent nodes. This mixed capture flow is explicitly not a fresh live
execution of the enhanced SDK readers. Twenty-four declared-owner/parent
differences are retained as omissions, without inventing ownership edges.

All 409 GUIDs and saved bytes stayed unchanged during current native reads.
There were no Create/Modify/Delete/Save calls, APX switches or quantity-engine
calls. The accepted three native assemblies were not recreated. Offline tests
and offline CI are intentionally not run under the user's current instruction.
Build results and deployment permission are recorded separately; BUILD_PASS
must never be presented as LIVE_PASS for the enhanced SDK contracts.

Reproduction: obtain fresh runtime schemas with the existing exporter, bind the
exact authorized project, load source-reviewed policies, call
`capture_ifc_facts`, pass native header/component/envelope replies to
`dependency_inputs`, and use the existing `run`/DependencyImpact path. Retain raw
responses privately. New binary deployment and enhanced-reader acceptance require
separate authorization for that exact APX. Shell contours/Revolved/Ruled, custom
Opening polygon positives, visible inspection and quantity-engine diagnosis
remain separate acceptance boundaries. A11.S03 remains PARTIAL.


Published [draft PR104](https://github.com/dvikt33-ux/safe-bim-layer/pull/104) at `5b8e3b873b2668a5ab257f28d77bab411c350942`, exact PR97 base `8f134001ca0e3250eda587db61ac01dbd6357326`. Enhanced SDK implementation `657d995a7163c85a17f775fd8a3fd62d23afd552` produced APX `2ed42a0d330df702524216ac6773312ff29aad8642792be35aab18427f7e91cb`. Native IFC/read-only dataflow is working; enhanced SDK fields remain BUILD_PASS, not LIVE_PASS. Offline tests and CI deliberately not run. Current Knowledge Graph snapshot173 plus own byte-verified CAS174; A11.S03 remains PARTIAL. No main, tested branch, PLN or installed APX modifications in this package.
