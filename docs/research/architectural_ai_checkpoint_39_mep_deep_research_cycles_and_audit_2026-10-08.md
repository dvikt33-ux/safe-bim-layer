# Checkpoint 39 — MEP engineering systems research, cross-engine integration and independent audit

Date: 2026-10-08
Target: Archicad 29, full-cycle architectural design accelerator
Scope: research-only; NO local project or Archicad PLN edits.
Research objective: minimize total elapsed time from brief to fully coordinated architecture, structure, MEP and issued project, by doing deep cold prebuild research and reusing existing engines before custom implementation.

## Pass 1 — Graphisoft AC29 built-in MEP features

Primary AC29 documentation:
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-1.htm — MEP Designer duct, pipe, cable carrier routes, available with Archicad Collaborate.
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-34.htm — System Browser volume flow and velocity.
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-39.htm — Duct Size Optimizer.
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-40.htm — Hydronics Optimizer, diameter/velocity constraints.
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-41.htm — MEP Model Quality Check: zone required supply/exhaust vs terminals flow.
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-15.htm — open port visualization/Issue Manager.
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-43.htm — associative labels/dimensions/schedules.
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-26.htm — Route Specifications reference DN/size table.
**License boundary**: built-in calculation features explicitly cloud license only; MEP Designer generally requires Archicad Collaborate or separate MEP Designer. DO NOT ASSUME user's current entitlement.

Native C++ API:
- https://graphisoft.github.io/archicad-api-devkit/group___m_e_p.html — routing, physical system graph, equipment, ports, callback.
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_routing_element_default.html — Place(polyline, segment cross-sections, optional GUID); recommends grouping placements in Undoable Command Scope.
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_routing_element.html — native route segments, nodes, polyline, MEP system, story offset.
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_system_browser_calculation_callback_interface.html — NEW AC29 SystemBrowserCalculationCallbackInterface with CalculationsRequested(root, DistributionSystemsGraph) and SubmitCalculations; replaces AC28 GraphCalculationInterface. Can integrate external/local calculated columns, not proof of a complete built-in design solver.
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_routing_element_1_1_modifier.html — ConnectLogically, same domain/system and geometry constraints.

**Critical new architectural insight:** Native AC29 can host our custom calculation results and incremental system graph notifications, with native route creation. Avoid own geometry/port fitting engine for basic routes.

## Pass 2 — Existing discipline design tools, not invented

- CYPEPLUMBING (water, sanitary, solar thermal) https://info.cype.com/en/software/cypeplumbing/ . 2025.a combined older Water/Sanitary programs; do not build integrations against deprecated names. Water/Sanitary exchange consumption/discharge between tabs. Can import IFC geometry via BIMserver.center; outputs IFC/glTF and reports. Native direct Archicad API NOT established.
- **New major discovery:** CYPEPLUMBING 2026.a automatically generates water-supply pipe layout for selected portions: https://info.cype.com/en/new-feature/automatic-layout-of-the-water-supply-system-in-cypeplumbing/ . Audit capability and return IFC before developing our own 3D water router.
- CYPEHVAC https://info.cype.com/en/software/cypehvac/ : heating/ventilation/cooling equipment, network design, IFC/glTF and reports, imports IFC building geometry, thermal loads.
- CYPELEC Distribution https://info.cype.com/en/software/cypelec-distribution/ : electric circuits and loads, grounding/lightning.
- CYPEFIRE Hydraulic Systems https://info.cype.com/en/software/cypefire-hydraulic-systems/ : sprinkler/fire hose/wet riser design, built on EPANET2, checks and model clashes; https://info.cype.com/en/new-feature/automatic-sizing/ automatic sizing iterates diameter and hydraulic check.
- CYPEFIRE https://info.cype.com/en/software/cypefire/ : compartmentation, evacuation and fire devices; feeds hydraulic systems.
- CYPELUX https://info.cype.com/en/software/cypelux/ : normal/emergency lighting, Radiance daylight, automatic zone luminaire layout https://info.cype.com/en/subject/cypelux-automatic-layout/ . **Explicit exception** automatic emergency layout is open-area/anti-panic, NOT exit/escape route placement.
- These programs are not proven to have unattended programmatic calculation/run APIs; IFC and UI support ≠ API automation.
- MagiCAD official support matrix https://www.magicad.com/mep-design/resources/standards-and-localisation/ shows MagiCAD for Revit and for AutoCAD/BricsCAD, not a proven native Archicad29 product. Do not assume direct Archicad plugin.

## Pass 3 — CALHYDRA Connection is already an official bidirectional hydraulic adapter

https://help.graphisoft.com/AC/29/RUS/_AC29_Help/086_CALHYDRA_Connection/086_CALHYDRA_Connection-1.htm
https://help.graphisoft.com/MEP/29/INT/_MEP_Designer_Help/086_CALHYDRA_Connection/086_CALHYDRA_Connection-1.htm

Graphisoft AC29/MEP Designer + CALHYDRA:
1. classify native pipe/fitting/equipment with **exactly named** CALHYDRA Classification System;
2. load manufacturer Route Specifications, matching both tools;
3. choose a SINGLE discipline/medium per export;
4. export `.chp`;
5. calculate in CALHYDRA;
6. export `.calhydraResult`;
7. import into AC29, update matching nominal pipe diameters;
8. Model Compare source/revision to verify actual modifications.

**Hard blockers:**
- license Archicad Collaborate/MEP Designer AND CALHYDRA;
- German/European calculation norms, not automatic current Russian SP compliance;
- mixed discipline export not supported; complex heating/cooling hydraulic networks, cold-water circulation and flow splitters explicitly unsupported;
- diameter not in AC29 Route Specifications -> route may remain unchanged with no error feedback;
- Teamwork requires reservation;
- UI-based manual process documented; fully unattended API not verified.

Decision: optional proven UI/file-based interoperability reference and candidate adapter. Read-back/diff compulsory. No paid dependency for core MVP.

## Pass 4 — Open calculation engines and data graphs

- EPA EPANET 2.2 MIT https://www.epa.gov/water-research/epanet , https://github.com/USEPA/EPANET2.2 . Pressurized water network pumps/valves/flows/pressure and toolkit, not a full internal gravity sewer or national-code verifier.
- EPA SWMM 5.2 public-domain https://github.com/USEPA/Stormwater-Management-Model . Runoff/stormwater/wastewater/combined sewer hydraulic dynamic model; not automatically the correct building internal sanitary pipe sizing method.
- LBNL Modelica Buildings BSD-3-Clause https://github.com/lbl-srg/modelica-buildings , https://simulationresearch.lbl.gov/modelica/ . HVAC/hydronic/dynamic energy/control simulation; not a trivial standards-checking tool. Version 13.0.0 released May 2026 (avoid citing 14 release posted Oct12 2026, future relative to current date Oct8).
- Honeybee Radiance https://www.ladybug.tools/honeybee-radiance/docs/ for daylight, and Ladybug/Honeybee for EnergyPlus/OpenStudio. Beware older legacy `ladybug-tools/honeybee` repo with outdated compatibility and `honeybee-radiance` AGPL-3.0 licensing.
- NetworkX https://networkx.org/documentation/stable/ algorithms for topological routes; no geometric code compliance or pressure/velocity.
- IfcOpenShell `ifcopenshell.api.system` + `ifcopenshell.util.system`:
  https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/system/index.html
  https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/system/index.html
  Creates IFC systems/ports/connected distribution elements, reads connected_to/from, element systems; distinguishes implicit equipment connections (early concept) vs explicit full segments/fittings (detailed engineering).
- Graphisoft IFC MEP import "MEP elements, otherwise Objects" may generate parametric routes IF sufficient data, or nonparametric equipment/Objects when missing information. Never treat imported object as equivalent to native route.
  https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-49.htm

## Pass 5 — Russian code edition audit (official Rosstandart)

- SP 60.13330.2020 HVAC + Amendment 6 effective 2026-07-07:
https://protect.gost.ru/sp/details/b00f766e-b861-4cc7-a448-c65906490262
https://protect.gost.ru/sp/changesdetails/25d65837-dfb6-408b-948f-e7f254851ded
- SP 30.13330.2020 indoor water/sewer + amendments 0–5 shown in Rosstandart:
https://protect.gost.ru/sp/details/8cd57a35-8503-4bb8-802a-324b64f3e0e7
- SP 256.1325800.2016 electrical + Amendment 9 effective 2026-01-26:
https://protect.gost.ru/sp/changesdetails/d438f64b-92ac-4527-8548-9b68adacfc66
- SP 10.13130.2020 internal fire water + Amendment 1 effective 2026-09-01:
https://protect.gost.ru/sp/changesdetails/2a55b7f6-0322-4573-9aa0-6a2979e7a130
https://39.mchs.gov.ru/deyatelnost/press-centr/novosti/5814864
IMPORTANT: Some aggregator snippets still say "not effective" despite current Oct 2026 date; use official effective dates. Code **applicability, obligatory vs voluntary status, current amendment, building type, height, region, intended use** must be proven per rule. Do not invent min pipe slope, room airflow, duct sizes, fire rating or service room size.

## Pass 6 — Cross-engine architecture: reserve systems before room details

Architectural Program + climate/site/codes
  -> Space/Zones, equipment demand, estimated utility/MEP load envelopes
  -> **Service Reservation Model** (shaft stack, riser positions, plant room volume, ceiling plenums, sanitary wet stack, roof plant load/clearance, access, fire separations, vertical/horizontal routing corridors)
  -> Architectural/structural concept constraints (grid, cores, stairs, walls, slab openings)
  -> IFC implicit MEP connectivity (endpoints/required services, source and destination)
  -> Domain design engines (native AC29, CYPE optional, EPANET for pressurized, SWMM for appropriate drainage, Modelica for energy)
  -> MEP routing solver (3D topology + cross-sectional envelopes, slope and hydraulic losses, structural obstacles, no-fire-compartment violation, maintenance clearances)
  -> AC29 native MEP RoutingElementDefault::Place batched, read-back and GUID mapping
  -> native SystemBrowserCalculationCallbackInterface or IFC/BCF results
  -> discipline-specific specialist validation and model update
  -> native documentation/schedules and final issue

Crucial: route clearance **envelopes** include insulation, installation access, future maintenance and fireproof penetration details, not just pipe centerline.
Plan vertical risers and roof drain/shafts before freezing floor plans; wet rooms on stacked service risers; do not require identical wall positions unless structural/MEP constraints demand it.

## Audit 1 — Why "fully automatic MEP" cannot be declared ready

| Category | Vendor feature documented | Headless API verified | User local test |
| --- | --- | --- | --- |
| AC29 native MEP route Place | YES | C++ native documented | NO |
| AC29 MEP calculation callbacks | YES | C++ callback documented | NO |
| AC29 MEP optimizer/cloud license | YES | UI only | NO |
| CALHYDRA bidirectional pipe diameters | YES | file/UI; headless UNKNOWN | NO |
| CYPEPLUMBING 2026.a auto water routing | YES | external automation UNKNOWN | NO |
| CYPEHVAC design/calculation | YES | external automation UNKNOWN | NO |
| CYPELEC | YES | external automation UNKNOWN | NO |
| CYPEFIRE Hydraulic auto sizing | YES | external automation UNKNOWN | NO |
| CYPELUX auto lighting layout | YES | external automation UNKNOWN | NO |
| EPANET toolkit | YES | YES local toolkit | NO |
| SWMM solver library | YES | YES C library | NO |
| Modelica Buildings | YES | local simulation with supported runtime | NO |
| IFC system graph (IfcOpenShell) | YES | YES Python | NO |
| Russian full-code-compliant automation | NO | NO | NO |

## Audit 2 — Hard failures to prevent

1. Mixing IFC/AC29/native MEP IDs or losing element/port identities on reimport.
2. Treating geometry touching as a logically connected MEP port; require connectivity graph.
3. Claiming pressure network EPANET models all gravity internal drainage.
4. Assigning HVAC flow values before room type/occupancy/edition validation.
5. Treating foreign vendor code compliance as Russian SP approval.
6. Exporting mixed disciplines into CALHYDRA.
7. Silent unchanged diameter after CALHYDRA import (unsupported DN).
8. Licensing dependency blocks whole project.
9. Calling every architectural change a full MEP reanalysis; only affected subgraphs.
10. Treating 2D pipe line or imported generic Object as full parametric native MEP.
11. Using IFC model whose zone/storey/export scope stale or mis-mapped.
12. Overloading HOT phase with detailed FEM/CFD/Modelica simulation instead of early spatial reservations.
13. Treating documentation of UI function as documented public automation API.
14. Confusing MEP Designer licensed capability with older built-in MEP Modeler editions.
15. No validation of national code change effective dates.

## Audit 3 — Coverage and stop criterion

Covered (vendor docs): native Archicad MEP read/write graph and optimizer; water/sanitary/HVAC/electrical/fire/lighting products; free pressurized/stormwater/energy engines; IFC port graph; CALHYDRA native return; current core Russian SP editions.
Not closed: Russian-specific hydraulic/electrical/HVAC solver availability and automation, full external headless APIs, all architectural space reservations and clearances with cited clause numbers, complete service discipline requirements, exact installed license, data round-trip.
Therefore **research phase not exhaustively complete**. Do not claim nothing more exists. Next focused research should prioritize Russia-native engineering calculation engines/API and source-backed *service-reservation taxonomy* before implementing.

## Decision / Reuse matrix

REUSE NOW IN RESEARCH:
- Native AC29 MEP API, ZoneBoundaryQuery, DistributionSystemsGraph, SystemBrowserCalculationCallbackInterface, route Place, native checks, native Issue Manager.
- IfcOpenShell system graph + NetworkX, COLD IFC QA.
- Existing project-specific library pack + Russian code pack.
PILOT OPTIONAL:
- CALHYDRA, CYPEPLUMBING/HVAC/FIRE/LEC/LUX (only licensed and workflow verified).
- EPANET/SWMM/Modelica when matching exact physics.
DO NOT BUILD:
- own general native MEP geometry kernel;
- own full hydraulic/fire/HVAC solver from scratch;
- universal converter from foreign compliance to Russian PASS.
BUILD CUSTOM ONLY:
- Service Reservation Model and multi-discipline spatial interface constraints;
- local first-party MEP graph-to-solver and result mapping;
- unit/edition/evidence/identity normalization;
- safe routing and rollback, audit and incremental dependency graph.

## Experiment queue
- MEP_LICENSE_01: actual AC29 MEP/Cloud/Collaborate capabilities without writes.
- MEP_NATIVE_ROUTE_01: native C++ Place and logical port connect in scratch PLN; check GUID/stories/undo.
- MEP_SYSTEM_CALLBACK_01: register columns, modify one route and verify affected subgraph only.
- MEP_ZONE_AIR_01: zone required supply/exhaust and terminal checks; license and zone update.
- MEP_IFC_PORTS_01: AC29->IFC->IfcOpenShell port graph->AC29 with native vs object type checks.
- MEP_CYPE_AUTO_WATER_01: 2026.a water auto layout, IFC return, native semantics, Russian SP gap.
- MEP_CALHYDRA_01: .chp -> calculation -> .calhydraResult, compare actual diameters; unsupported DN detection.
- MEP_EPANET_01: pressure water sample, compare published reference result and units.
- MEP_SWMM_01: drainage sample only if correct system type.
- MEP_ROUTING_01: 2 storeys, 1 wet stack, HVAC, structural obstacles, one gravity slope, 2 candidate routes, no fake clearances.
- MEP_RU_NORMS_01: exact clause and amendments, prove validity in building type.
- MEP_CHANGE_01: move toilet/zone/wall; invalidate only dependent plumbing/HVAC/structural interface and drawings.
- MEP_FINAL_01: full-cycle one small project with architecture+MEP+structural and documentation accepted by specialists.

## KPIs
T_first_complete_MEP_concept, T_first_calculated_system, T_relayout_after_room_change, number_of_unresolved_shaft_collisions, manual_engineer_minutes, IFC_ports_preserved_ratio, silent_diameter_update_failure_count, false_compliance_PASS_count (target zero), license-independent core coverage.

## Research conclusion
**Architectural space reservations and service topology BEFORE detailed floorplan freeze** is the highest-value integration. Reuse AC29 native MEP authoring, its calculation callbacks and zone ventilation checks; CALHYDRA is an existing bidirectional hydraulic reference; CYPEPLUMBING already auto-routes some water systems; IfcOpenShell supports implicit-to-explicit connectivity. Complete Russian code compliance and unattended integration are NOT proven. Continue focused research before declaring global discovery complete.
