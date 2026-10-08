# Checkpoint 40 — offline, license-feasible engineering stack

Date: 2026-10-08
Scope: research only, no PLN modification
Binding constraint from user: **no Graphisoft cloud license, no Graphisoft AI, no paid foreign engineering software licenses**. Existing local Archicad 29 remains the only assumed proprietary host; actual MEP authoring entitlement is unknown and must be probed, not assumed.

## Correction to checkpoint 39
- Graphisoft states MEP calculation functions are cloud-license only: https://help.graphisoft.com/AC/29/INT/_AC29_Help/005_NewFeatures/005_NewFeatures-50.htm
- Graphisoft route UI says MEP Designer available with Collaborate: https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-4.htm
- Graphisoft support also mentions service-contract license: https://support.graphisoft.com/hc/de/articles/46919068406417-MEP-Designer-in-Archicad-29-und-neuer-nicht-verf%C3%BCgbar
- AC29 C++ MEP RoutingElementDefault::Place API documented: https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_routing_element_default.html ; API presence does NOT prove the user's license permits its runtime use.
- If MEP route API is blocked, fallback is native Archicad Morph/Object/3D geometry and IFC system semantics, with honest flag NOT_NATIVE_MEP_ROUTE. Do not claim hydraulic graph is physically connected just because geometry touches.

## Strong new candidate: OpenMEP Suite
Repo: https://github.com/kakarot-oncloud/openmep-suite
Verified from GitHub connector: README and MIT LICENSE exist.
Repo claims 26 discipline calculators, Python 3.11 FastAPI on localhost:8000, modular engines, regional standards adapters, tests 167/~84% coverage. These are project claims, NOT independently run or validated.
Disciplines: cable sizing, voltage drop, demand, short-circuit, HVAC loads, ducts, ventilation, plumbing/pipe/drain/pumps, sprinkler/fire pumps, BOQ/report.
Regional rules: GCC, Europe/UK, India, Australia/NZ. **No Russian SP adapter.** Adaptation requires primary-source Russian editions, separate unit tables, known benchmark cases, peer review and engineer acceptance. Avoid claiming normative Russian compliance.
Audit source-code/test correctness and licensing of embedded normative tables; MIT source license does not grant unlimited rights to reproduce standards tables.
Initial reuse candidate: modular calculation API + pure-Python physics, not automatic compliance signoff.

## Other open source
- IfcOpenShell https://github.com/IfcOpenShell/IfcOpenShell : Python/C++ IFC, system port graph, IfcTester IDS, IfcClash, IfcDiff, BCF, ifcmcp; LGPL/GPL component-specific licenses; free local execution.
- EPANET 2.2 https://github.com/USEPA/EPANET2.2 : MIT pressurized water hydraulics, not internal gravity sewer.
- EPA SWMM https://github.com/USEPA/Stormwater-Management-Model : stormwater/drainage hydraulics, only where appropriate.
- Modelica Buildings https://github.com/lbl-srg/modelica-buildings : BSD-3-Clause dynamic energy/HVAC simulation, high-complexity optional.
- FreeCAD + IFC as independent offline fallback geometry/IFC review, not replacement for authoritative Archicad PLN.
- Newly discovered OpenAEC Foundation https://open-aec.com/en/ lists open Heatloss Studio (Dutch NEN 12831), Open Calculations Studio and Open BIM Validator Studio, Open Planner Studio; **country-specific and beta**: audit source repo, license, API and real maturity before promotion.

## Revised architecture
GPT director
  -> deep cold prebuild (Russian normative editions, project library, open engine selection)
  -> service-reservation model before room plan freeze
  -> local planning/NetworkX/OR-Tools
  -> Archicad 29 via existing native C++/Tapir writer (no cloud)
  -> optional native MEP route only after license probe; fallback physical model + IFC ports
  -> OpenMEP + EPANET + SWMM + specialized physics engines locally
  -> separate Russian rules adapter with source provenance
  -> IFC IDS/BCF and engineer review
  -> native Archicad drawings and release

## Selection rule
P0 = local + legally usable + API/CLI + exact domain physics + no cloud entitlement + source-verified.
P1 = free but code not independently audited / license unknown / foreign norm only.
REFERENCE_ONLY = paid foreign/cloud software (CYPE, CALHYDRA, SCIA, RFEM, MagiCAD), do not put on execution critical path.
LIRA-FEM local integration only if user already has legal licensed version and confirms it; otherwise reference-only.
Never bypass or emulate licensing.

## Priority research/test
1. OPENMEP_CODE_AUDIT_01: read engines, adapters, standards_data, 167 tests, compare calculation sample to independent published benchmark.
2. AC29_MEP_LICENSE_PROBE_01: read-only check native routing tools/API availability on actual installed license; do not assume native MEP.
3. RUS_SP_RULEPACK_01: create source-backed current edition test cases for water/HVAC/electrical/fire, separate physics and compliance.
4. SERVICE_RESERVE_01: shafts/plant/ceiling/roof/maintenance/firestop spatial reservation model for building type.
5. EPANET_REFERENCE_01: benchmark pressurized network.
6. IFC_PORT_ROUNDTRIP_01: exact ports/system/level/GUID mapping and non-native route fallback.
7. FULLCYCLE_FREE_01: complete one small building with architecture/MEP/structural review and documentation without cloud or paid foreign engineering dependencies.

## Audit conclusions
- Verified: vendor restrictions, existence of native C++ route API, OpenMEP README/MIT, IfcOpenShell source capabilities.
- Unverified: OpenMEP numerical correctness and legal provenance of standards tables, user MEP license, Russian SP compliance, fully automated building end-to-end.
- The free-stack direction is plausible but not yet a validated complete engineering product.
