# APA №1 — full research 2026-10-18 20Z

30 real documentary source-contract checks; two independent counteraudits; six handoff cards. No actual execution, installs or native calls. ChatGPT web + connected GitHub used.

## Provenance warning

Search index labels many IfcOpenShell pages as 0.8.5 (crawled months ago), while opening same live pages now displays 0.9.0post1. Therefore source snapshot only; exact 0.8.5 wheel SHA, API signature and local installation NOT_VERIFIED. Do not use 0.9 behavior as 0.8.5 proof. IfcOpenShell LGPL upstream, Windows 0.8.5 wheels listed on PyPI. AC29 MEP licensing separate.

## 30 checks

1. **MEP gap** [A]. Question: is there a ready contract? Evidence: PR165 _ifc_ports lines 170–190 counts IfcDistributionPort/IfcRelConnectsPorts, nativeMEPConnectionVerified=false. Counteraudit: Graph traversal still missing. Next: pin installed version and independent readback; status SOURCE_DOC.
2. **MEP port list** [B]. Question: is there a ready contract? Evidence: util.system.get_ports(element,flow_direction=None) returns ports. Counteraudit: IFC export may omit native ports. Next: pin installed version and independent readback; status SOURCE_DOC.
3. **MEP edge** [B]. Question: is there a ready contract? Evidence: get_connected_port(port) returns a port or None. Counteraudit: Null does not prove native PLN defect. Next: pin installed version and independent readback; status SOURCE_DOC.
4. **MEP adjacency** [B]. Question: is there a ready contract? Evidence: get_connected_from/to(element,flow_direction) returns neighboring elements. Counteraudit: No hydraulic flow simulation. Next: pin installed version and independent readback; status SOURCE_DOC.
5. **MEP system membership** [B]. Question: is there a ready contract? Evidence: get_element_systems/get_system_elements return memberships. Counteraudit: Not geometric proximity. Next: pin installed version and independent readback; status SOURCE_DOC.
6. **IFC2X3 class gate** [C]. Question: is there a ready contract? Evidence: add_system defaults IfcDistributionSystem; IFC2X3 uses IfcSystem. Counteraudit: IFC mutation, no PLN operation. Next: pin installed version and independent readback; status SOURCE_DOC.
7. **IFC port owner** [D]. Question: is there a ready contract? Evidence: add_port(file,element) creates assigned IfcDistributionPort. Counteraudit: No native AC29 port creation. Next: pin installed version and independent readback; status SOURCE_DOC.
8. **Port cardinality** [E]. Question: is there a ready contract? Evidence: connect_port(port1,port2,direction,element) limits one peer; SOURCE/SINK. Counteraudit: No automatic physical sizing. Next: pin installed version and independent readback; status SOURCE_DOC.
9. **MEP group** [F]. Question: is there a ready contract? Evidence: assign_system(products,system) returns IfcRelAssignsToGroup or None for empty. Counteraudit: Check empty list. Next: pin installed version and independent readback; status SOURCE_DOC.
10. **AC29 import preset** [G]. Question: is there a ready contract? Evidence: IFC Geometry Conversion has MEP elements, otherwise Objects. Counteraudit: UI not JSON API. Next: pin installed version and independent readback; status SOURCE_DOC.
11. **AC29 MEP license** [H]. Question: is there a ready contract? Evidence: MEP Systems marked Available with Archicad Collaborate. Counteraudit: User entitlement unknown. Next: pin installed version and independent readback; status SOURCE_DOC.
12. **Paid hydraulic solver** [I]. Question: is there a ready contract? Evidence: CALHYDRA requires separate license plus MEP Designer/Collaborate. Counteraudit: EXCLUDE under free-only policy. Next: pin installed version and independent readback; status SOURCE_DOC.
13. **4D plan** [J]. Question: is there a ready contract? Evidence: sequence.add_work_plan(name,predefined_type,start_time) creates IfcWorkPlan. Counteraudit: IFC only, not APA scheduler. Next: pin installed version and independent readback; status SOURCE_DOC.
14. **4D baseline** [K]. Question: is there a ready contract? Evidence: add_work_schedule(...,predefined_type,work_plan) supports PLANNED/BASELINE/ACTUAL. Counteraudit: Do not invent baseline. Next: pin installed version and independent readback; status SOURCE_DOC.
15. **4D WBS** [L]. Question: is there a ready contract? Evidence: add_task(work_schedule OR parent_task,name,identification,predefined_type). Counteraudit: Parent/root mutually exclusive. Next: pin installed version and independent readback; status SOURCE_DOC.
16. **4D time** [M]. Question: is there a ready contract? Evidence: add_task_time(task,is_recurring=False) creates blank IfcTaskTime. Counteraudit: No guessed duration. Next: pin installed version and independent readback; status SOURCE_DOC.
17. **4D ISO duration** [N]. Question: is there a ready contract? Evidence: edit_task_time(task_time,attributes) uses ScheduleStart/ScheduleDuration P2D. Counteraudit: Calendar source needed. Next: pin installed version and independent readback; status SOURCE_DOC.
18. **4D calendar** [O]. Question: is there a ready contract? Evidence: add_work_calendar(name,predefined_type) models working shifts. Counteraudit: Not a Russian holiday calendar. Next: pin installed version and independent readback; status SOURCE_DOC.
19. **4D output** [P]. Question: is there a ready contract? Evidence: assign_product(relating_product,related_object) yields IfcRelAssignsToProduct. Counteraudit: Constructed product, not demolition input. Next: pin installed version and independent readback; status SOURCE_DOC.
20. **4D input** [Q]. Question: is there a ready contract? Evidence: assign_process(relating_process,related_object) yields IfcRelAssignsToProcess. Counteraudit: Do not reverse process semantics. Next: pin installed version and independent readback; status SOURCE_DOC.
21. **4D cascade** [R]. Question: is there a ready contract? Evidence: cascade_schedule(task) propagates successor dates; cycles cause recursion error. Counteraudit: Not general optimizer. Next: pin installed version and independent readback; status SOURCE_DOC.
22. **4D critical path** [S]. Question: is there a ready contract? Evidence: recalculate_schedule(work_schedule) forward/backward pass, total/free floats. Counteraudit: Cycle fixture required. Next: pin installed version and independent readback; status SOURCE_DOC.
23. **4D readback** [T]. Question: is there a ready contract? Evidence: util.sequence.get_related_products/get_work_schedule_tasks provide outputs/tasks. Counteraudit: Independent QA possible. Next: pin installed version and independent readback; status SOURCE_DOC.
24. **5D schedule** [U]. Question: is there a ready contract? Evidence: cost.add_cost_schedule(name,predefined_type) creates IfcCostSchedule. Counteraudit: Not Russian GESN compliance. Next: pin installed version and independent readback; status SOURCE_DOC.
25. **5D hierarchy** [V]. Question: is there a ready contract? Evidence: add_cost_item(cost_schedule OR cost_item) creates root/child item. Counteraudit: Rates not provided. Next: pin installed version and independent readback; status SOURCE_DOC.
26. **5D formula** [W]. Question: is there a ready contract? Evidence: edit_cost_value_formula(cost_value,formula) supports arithmetic 5000*1.19. Counteraudit: Not tax-law validation. Next: pin installed version and independent readback; status SOURCE_DOC.
27. **5D rate** [X]. Question: is there a ready contract? Evidence: assign_cost_value(cost_item,cost_rate) reuses SCHEDULEOFRATES. Counteraudit: Currency/unit provenance. Next: pin installed version and independent readback; status SOURCE_DOC.
28. **5D readback** [Y]. Question: is there a ready contract? Evidence: util.cost.get_cost_items_for_product/get_total_quantity/calculate_applied_value. Counteraudit: No accuracy claim. Next: pin installed version and independent readback; status SOURCE_DOC.
29. **PDF provenance** [Z,AA,AB]. Question: is there a ready contract? Evidence: add_information + add_reference + assign_document links IfcDocumentReference to products. Counteraudit: No PDF vector recognition; distinct from PR154. Next: pin installed version and independent readback; status SOURCE_DOC.
30. **Mapped assemblies** [AE,AF]. Question: is there a ready contract? Evidence: util.placement.get_mappeditem_transformation returns 4x4; PR170 only OBJ/GLB/bounds. Counteraudit: Needs two-instance matrix test. Next: pin installed version and independent readback; status SOURCE_DOC.

## Six cards for researcher #2 (expert score, NOT benchmark)

- **C20-01 94/100 MEP IFC connectivity**. Found: util.system get_ports/get_connected_port/get_connected_to/from/get_system_elements. Not duplicate: PR165 only relation counts. Question for #2: exact pinned 0.8.5 source, license, Win11 and data shape? DONE: 3 IFC4 fixtures with dangling, flow, membership and GUID checks.
- **C20-02 89/100 4D IFC scheduling**. Found: api.sequence IfcTask/calendar/cascade/recalculate. Not duplicate: PR165–170 no 4D route. Question for #2: exact pinned 0.8.5 source, license, Win11 and data shape? DONE: 3-task/cycle fixture; dates and floats independently checked.
- **C20-03 86/100 5D IFC cost/QTO**. Found: api.cost and util.cost, IfcCostItem/rate/quantity. Not duplicate: PR166 IDS/ODS is not 5D. Question for #2: exact pinned 0.8.5 source, license, Win11 and data shape? DONE: unit/currency/rate source/QTO reconciliation.
- **C20-04 90/100 PDF drawing→IFC provenance**. Found: api.document IfcDocumentInformation/Reference/RelAssociatesDocument. Not duplicate: PR154 parses PDF but does not link document GUID. Question for #2: exact pinned 0.8.5 source, license, Win11 and data shape? DONE: sheet ID/revision/hash to element GUID readback.
- **C20-05 77/100 External library references**. Found: api.library IfcLibraryReference/IfcRelAssociatesLibrary. Not duplicate: no norm-checking claim. Question for #2: exact pinned 0.8.5 source, license, Win11 and data shape? DONE: offline URI/license reference QA.
- **C20-06 81/100 Mapped-instance transforms**. Found: util.placement get_mappeditem_transformation. Not duplicate: PR170 world bounds != source matrix. Question for #2: exact pinned 0.8.5 source, license, Win11 and data shape? DONE: two repeated IFC instances matrix/axis/unit check.

## Independent counteraudit A — source/version/license

Read NEXT_RESEARCH_PRIORITIES.md 19Z, candidates.json 61, priority_matrix 61, canonical PROJECT_PLAN.json revision182/91 tasks read-only; latest #2 19Z and #3 19Z. PR154/159/160/162 and PR165/166/167/168/170/171 checked. Upstream API docs currently 0.9.0post1 despite indexed 0.8.5; local 0.8.5/Windows binary hash NOT_VERIFIED. AC29 MEP import translator is UI, not programmatic JSON. CALHYDRA is paid and excluded. No 1.5.10 Tapir local catalog checked.

## Independent counteraudit B — engineering value/duplication

PR165 _ifc_ports lines 170–190 counts exported port relations and explicitly sets nativeMEPConnectionVerified=false. PR170 B3 actions IFCGeometryOBJ/GLB/Bounds, not 4D/5D/IFC document associations. No second IFC parser or writer. Missing exported IFC ports do not prove a native PLN fault. IFC 4D/5D methods would mutate only an authorized IFC copy, not native Archicad; none executed. Document links cannot infer wall/window geometry or ensure SP/GOST compliance. No speed benchmark or ACCEPTED.

## Sources

[A]: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py
[B]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/system/index.html
[C]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/system/add_system/index.html
[D]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/system/add_port/index.html
[E]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/system/connect_port/index.html
[F]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/system/assign_system/index.html
[G]: https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-49.htm
[H]: https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-33.htm
[I]: https://help.graphisoft.com/AC/29/INT/_AC29_Help/086_CALHYDRA_Connection/086_CALHYDRA_Connection-1.htm
[J]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/add_work_plan/index.html
[K]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/add_work_schedule/index.html
[L]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/add_task/index.html
[M]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/add_task_time/index.html
[N]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/edit_task_time/index.html
[O]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/add_work_calendar/index.html
[P]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/assign_product/index.html
[Q]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/assign_process/index.html
[R]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/cascade_schedule/index.html
[S]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/recalculate_schedule/index.html
[T]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/sequence/index.html
[U]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/cost/add_cost_schedule/index.html
[V]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/cost/add_cost_item/index.html
[W]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/cost/edit_cost_value_formula/index.html
[X]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/cost/assign_cost_value/index.html
[Y]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/cost/index.html
[Z]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/document/add_information/index.html
[AA]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/document/add_reference/index.html
[AB]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/document/assign_document/index.html
[AC]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/library/add_reference/index.html
[AD]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/library/assign_reference/index.html
[AE]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/placement/index.html
[AF]: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-geometry-b3-20261018/scripts/apa_ifc_geometry_b3.py

Version/license: https://pypi.org/project/ifcopenshell/0.8.5/ ; https://github.com/IfcOpenShell/IfcOpenShell

## Status

SOURCE=30 documentary checks, some version PARTIAL. OFFLINE/BUILD/INSTALLED/LIVE=NOT_RUN; ACCEPTED=NO. MODEL_MODE_NOT_VERIFIABLE. No main, PLN, APX, code, NEXT_RESEARCH_PRIORITIES.md, plan182, installs, paid APIs, Work/Codex/Arena or PR merge.
