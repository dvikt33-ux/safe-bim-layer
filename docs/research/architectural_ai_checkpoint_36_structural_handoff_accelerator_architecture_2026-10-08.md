# Checkpoint 36 — Structural-handoff-first redesign of the Archicad 29 accelerator

Date: 2026-10-08
Scope: architecture + reuse research, not implementation; one existing open AC29 PLN is authoritative; no live Archicad interaction or PLN modification.
Project: dvikt33-ux/safe-bim-layer, feature/working-archicad-mvp

## 0. Objective and product boundary

**Business KPI:** median human elapsed minutes from sufficiently structured architectural brief to **architecturally coherent, verified-as-far-as-model-represented, structurally reviewable AC29 package** submitted to a structural engineer. A structural-engineer-ready design is NOT a structurally designed/certified building.

DO NOT optimize surrogate metrics such as number of tools, AI agents, tokens, 3D polygons, raw wall writes or total number of documentation pages.

Stop at the *minimum sufficient deliverable for structural intake* before doing detailed production drawings or extensive specialist computations unrelated to the immediate handoff.

Relevant prior studies: checkpoints 20–35, especially 22 incremental compiler, 24 CSE, 26 view/section planner, 27 native structural quality/SAF, 28 core grammar, 31 requirements graph, 32 activity/equipment envelopes, 33 semantic event invalidation, 34 crossrepresentation release witness, 35 native quantities; parallel "details" releases and native plugins.

## 1. Real implementation state vs research backlog (repo audit)

Inspected tracked code, not merely research descriptions.

### Implemented/visible:
- `archicad-addon/Sources/ModelDumpCommands.cpp`: native evaluated 3D geometry+materials full dump; prior live evidence ~5,296 elements, 9,261 bodies, ~105 MB and 12.85 s.
- `scripts/archicad_executor.py`: ~373 lines, seven action types, fresh whole-model dump before *each* command and fresh dump after create/delete/change, so normal editing pays full export/serialization/parse twice; live tested limited create/readback cycles, not production-level modeling.
- `scripts/archicad_chat_executor.py`: narrow Russian-to-action parser, source inference and ambiguity stops.
- `scripts/archicad_change_watch.py`: read-only polling snapshots via Tapir GetDetails/Get3DBoundingBoxes, not real native event observer.
- `safe_bim_layer.py`: separate thin Tapir validation/writer path; create_room creates wall loop, slab, door, windows sequentially but NO atomic transaction/whole-operation rollback; hardcodes `floor_index=0` and first wall as opening host. Its schema validator also needs a dedicated regression suite.
- `scripts/archicad_template_builder.py`: ~4,256-line template orchestration; verify its apply-phase preconditions on separate snapshot.
- `details/ACTIVE_RELEASE`: v2.12 machine-readable catalog; 1,215 detail units, 1,835 parameter facts, 601 component variants, 532 outstanding binding tasks, five unresolved KAIMAN/KERAKAM cross-sheet contradictions. Active IR **is not approved for construction**. Relevant: `details/releases/v2.12/audit.json`.
- No test modules under tracked `tests/` in this branch tree; CI workflows mostly template and detail library. Existence of earlier live ad hoc cycles and packaged details does not equal an automated regression gate for semantic command execution.

### Serious outcome

This is a project with a small working low-level BIM actuator and an extensive, largely *research-stage* architecture. We should not create yet another parallel executor; we should connect proven paths and promote features one capability at a time.

## 2. Reuse discoveries targeted at structural handoff

### 2.1 Archicad 29 Structural Analytical Model (SAM): native first

Graphisoft AC29 only admits load-bearing eligible Column, Beam, Wall, Slab and Single-Plane Roof physical elements into the generated SAM. Composite/profile must contain Core; member enabled; structural function load-bearing. SAM has 1D/2D members, links, supports, loads and releases. Physical Model Quality checks catch missing Core connections, near misses and disproportionate cores; Structural Analytical Model Quality checks connectivity/overlaps. Generation Adjustment Rules stretch/cutback/offset/snap ANALYTICAL geometry without modifying physical element geometry.

Official:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/090_StructuralAnalyticalModelTools/090_StructuralAnalyticalModelTools-3.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/090_StructuralAnalyticalModelTools/090_StructuralAnalyticalModelTools-30.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-3.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-1.htm

AC29 C++ API offers `ACAPI_Analytical_GetAnalyticalModel`, `GetCurveElements/GetCurveMember`, `GetSurfaceElements/GetSurfaceMember`, connection and support/loads queries, `UpdateAnalyticalModel`. **SAM is view-/variation-dependent** (renovation and layer connection class can change it). Native analytical members are *derived*, not freely authored via API.
https://graphisoft.github.io/archicad-api-devkit/group___analytical.html

**Adopt** tiny read-only "Structural Intake Probe" exposing existing SAM counts, member GUIDs, core status, continuity, analytical variation+rules identity, unmapped/nonmembers and change dependencies. NO new native FEM mesher/structural solver.

### 2.2 Archicad SAF (Structural Analysis Format) is existing transport

SAF export via File > Save As or Publisher, full/visible/selected, import via Model Compare; XML-exportable SAF translators; release/loads/profile/material. Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/091_StructuralAnalysisFormat/091_StructuralAnalysisFormat-2.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/091_StructuralAnalysisFormat/091_StructuralAnalysisFormat-29.htm

**Danger:** Material Mapping Export silently applies "Other Building Materials" to an unmapped physical material. For handoff, enforce `mapping_coverage=100%` on actual load-bearing materials (or explicit engineer-approved exception) rather than accept fallback silently.
https://help.graphisoft.com/AC/29/INT/_AC29_Help/091_StructuralAnalysisFormat/091_StructuralAnalysisFormat-12.htm

SAF version target must match actual receiver. For initial test, SAF 2.2.0 sample data exists:
https://www.saf.guide/en/stable/index.html
https://examples.saf.guide/

### 2.3 Russia-relevant engineer receivers

**LIRA-FEM/LIRA-SAPR 2026 R1** public release notes: staged IFC import, *update selected IFC elements without full re-import*, retained IFC GUID and ID on export, extended SAF cross-section support; vendor explains Archicad/SAF/IFC exchange.
https://www.liraland.com/lira/release-notes/2026/components-of-bim-technology
https://lira.land/lira/systems/bim.php
Decision: P0 engineer receiver candidate, verify exact product/version/licence and roundtrip.

**SCAD Office** documentation permits direct IFC/DXF and historic specialized Archicad .r2s translator; version availability for AC29 UNKNOWN. https://scadsoft.com/help/SCAD/ru/SCAD1049/import_loading_diagram.htm

**SCIA AutoConverter** can derive linked analysis model from IFC physical structural model then pass SAF to SCIA Engineer; structural analysis interoperability/reference, commercial dependency.
https://www.scia.net/en/support/faq/scia-autoconverter/general/workflow-scia-autoconverter-scia-engineer
SCIA Open API + ADM are documented for programmatic projects/models/calculations:
https://help.scia.net/api/25.0.5008/docs/key-concepts.html

**Dlubal RFEM6** NEW official Python gRPC `dlubal.api`, version 2.15.3 (July 2026), is the preferred new integration. Older `RFEM_Python_Client` SOAP/Webservices under maintenance since May 2025. Require licensed RFEM host/API service; not default dependency.
https://apidocs.dlubal.com/quick_start.html
https://apidocs.dlubal.com/examples.html
https://github.com/dlubal-software/RFEM_Python_Client

**Ifc2CA/Code_Aster** available in IfcOpenShell ecosystem as open alternative for structural research/reference. NOT a production structural sign-off, requires analysis discipline and valid loading/supports.
https://github.com/Jesusbill/ifc2ca

**CYPE Open BIM Analytical Model** is an important FALSE FRIEND: its analytical model is explicitly for **thermal and acoustic** modelling (spaces/surfaces/junctions), not directly the FEM structural SAM. It cannot replace SAF structural exchange.
https://info.cype.com/en/software/open-bim-analytical-model/

### 2.4 Reuse local existing specialized methods

- Source code in our branch already researches native Graphisoft quantity APIs, SEO dependency graph, Difference Generator, global semantic observer events, zone boundaries, MEP physical systems, special Navigator view projection, schema/decision IR, Design Options, Favorites, IFC export hooks, Revision Manager, Publisher.
- `details/` machine library v2.12 is the first reuse source for CSE details, but unresolved conflicts and all release gates require explicit qualified appraisal.
- Existing validated local geometry writer cycles remain low-level actuators; do not throw them out.
- Native zones can map classification → live load category; AC29 Create/Update Live Loads (never assign loads without approved code/load schedule). https://help.graphisoft.com/AC/29/INT/_AC29_Help/090_StructuralAnalyticalModelTools/090_StructuralAnalyticalModelTools-23.htm

## 3. New architecture: minimum usable end-to-end *vertical slice*

```
Architectural Brief + constraints
          |
Program and Room Requirements  [small schema now; dRofus if licensed]
          |
Design Kernel [invariant grid/levels/core/shafts/structural envelope + room-fit]
  - layout/topology OR-Tools/Shapely + donor/room kits
  - CSE verified candidate families + design intent/decision record
          |
ONE Semantic Action Dispatcher [existing Safe BIM Layer + executor consolidation]
  - planning → preview → batched native write → scoped read-back
  - provider selection: native AC29/Husky/Tapir based on measured capability
  - script worker cannot silently switch project; plan has exact identity
          |
ONE Live Project Fact Cache
  - native GUID, semantic facets, native relationships, relevant quantities
  - native observer HOT; polling + Difference Generator recovery
  - on-demand mesh, cold full snapshot only at milestones
          |
Structural Intake Gate [NEW SHARED GOAL]
  - native physical model check
  - native SAM build/quality/continuity
  - material/profile SAF map and load category gate
  - receiver version/units/origin/storeys/GUID consistency
  - PRELIMINARY unknowns and questions identified
          |
Structural Intake Bundle
  - PLN reference (local/current), IFC coordination snapshot
  - SAF analytical snapshot if relevant
  - plan/axis/core/level/section documentation derived from SAME BIM
  - decision/assumption/problem log + provenance, BCF to engineer
          |
Structural Engineer analyses & returns changes
          |
Native Model Compare/Issue Manager/BCF + selective merge
          |
Then full AR/KR/detail/document compiler for agreed version
```

## 4. Hard separation of outputs by design phase

**H0 Conceptual structural feasibility intake**
- loadbearing vs partition preliminary intent;
- grid, spans, vertical core, floors, major structural openings, material family candidates;
- explicit constraints, assumptions and unanswered engineering questions;
- no invented cross-section adequacy or confirmed reinforcement.

**H1 Calculation-ready exchange**
- engineer-agreed target program/version+units/coord system;
- stable native and IFC GUID map;
- complete physical-to-analytical coverage of intended load-bearing elements;
- no accidental core disconnections, missing members, unsupported roof geometry;
- source and settings of generation rules, mapped materials/profiles, valid loads only if approved;
- SAF + IFC + accepted scope / unresolved items.

**H2 Engineer feedback cycle**
- returned sizes/positions/supports and calculated model assumptions;
- delta/influence on stairs, rooms, façade, sections, quantities, MEP, local CSE details;
- human approval when changing structural scheme.

**H3 Documentation release**
- full regulatory/document coverage and cross-representation gate, after structural acceptance.

Do NOT make H0 wait for H3. Scope should be set by engineer's agreed EIR/LOIN, not assumed maximal detail.
ISO 7817-1:2024 https://www.iso.org/standard/82914.html
buildingSMART IDS final 1.0, information ONLY (not arbitrary geometry):
https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/

## 5. Structural intake data contract (minimal illustrative)

```yaml
handoff_id: ""
state: H0_PRELIMINARY
archicad:
  project_identity: ""
  source_revision: ""
  story_table_digest: ""
  model_view_variation_digest: ""
  layer_connection_policy_digest: ""
structural_schema:
  grid_axes: []
  levels_and_heights: []
  candidates:
    walls: []
    columns: []
    beams: []
    slabs: []
    roof: []
    lateral_core: []
  opening_impact_on_load_path: []
  loads:
    categories: []
    values_status: NEEDS_ENGINEER_CONFIRMATION
  structural_constraints:
    - service_shafts
    - spans_and_clearances
    - deformation_joints
  material_and_profile_map:
    receiver: null
    unrecognized_count: null
    SAF_translator_digest: null
deliverables:
  ifc_digest: null
  saf_digest: null
  coordination_views: []
  issues: []
  structural_questions: []
  outstanding_hard_information: []
  coverage_signature: ""
verdict: NOT_VERIFIED
```

If H1 unavailable, H0 handoff is still useful and should not be described as a ready-to-calculate SAF model.

## 6. Integration anti-corruption rules

- Never use IFC Guid as native Archicad API GUID; maintain explicit mapping verified by export.
- SAF Member IDs must remain stable or be mapped through model compare; identity contract includes receiver/version/material/profile mapping and analytical variation.
- Modifying an architectural Wall should dirty relevant Core relationship / StructuralMember / SAM node / loads / SAF/IFC / structural handoff witness; changing wall paint must NOT trigger full FEM validation.
- Changing one column or storey can alter many spans/core relationships/loads — reverse dependency impact cone, not merely changed object.
- If room use changes, zone classification and approved load category may change; `Update Zones` required before area-based loads/metrics.
- 2D/detail library cannot silently certify loadbearing parts.
- Every provider chosen using Capability Contract: actual AC29 read/write, undo, partial failure, readback, version, latency, host permission, license and data ownership.
- Do not proliferate agent personas. One Architect Orchestrator + optional domain reviewers; calculations by deterministic engines.

## 7. Prioritized implementation plan — by ability to reduce elapsed time

P0. **Handoff fixture first, not general research infra.** Choose a single real test copy with two+ storeys, columns/walls, slab, stair/core, openings, structural grid. Record manual baseline from brief to engineer intake and necessary questions.

P1. **Structural Handoff Snapshot, read-only prototype:** native physical-loadbearing counts, storeys, grid, cores, part participation, documented member count, model variation, quality warnings, material/profile mapping and missing evidence; independent of full 100MB dump.

P2. **Safe unified action dispatch:** consolidate `safe_bim_layer.py` + `archicad_executor.py` behind single semantic command schema and measured provider choice, strict project guard, explicit plan/dry-run, compound undo/readback/diff; retain cycles as library and regression tests. Fix create_room hardcoded story/first-wall host, enforce rollback/recovery.

P3. **Cheap model facts before mesh:** Native GUID/property/relation/zone/quantity queries first; per-GUID 3D detail only if asked. Native Observer eventually primary, polling recovery. Batch write+read.

P4. **Structural topology early:** structural grid, loadbearing wall/column alignment, core overlap, support/beam candidate, stair, services/wet risers; detect missing load paths, native Physical/SAM model quality, don't guess section strength.

P5. **Two receiver pilots:** LIRA/SAPFIR from IFC + SAF on exact installed version, plus second receiver SCAD/SCIA depending engineer available tool. Verify material mapping, axis/levels/units, openings, ID stability, changed-object propagation and return feedback.

P6. **Room+load ready:** zones/FRG/AEE, classifications; live loads only if engineer-approved category tables; no false normative approvals.

P7. **Detail reuse from v2.12 and native Publisher:** detailed AR documentation only where critical to H1 or after structural feedback; zero unapproved auto-insertion from catalog.

P8. **After proven handoff:** incremental persistent graph/action cache, skill context router, full QA, normative depth, aesthetics, add-ons as proven gaps.

Do NOT chase opening/roof material bugs or universal generic Verifier engine ahead of H0 milestone unless they block H0.

## 8. Latency principles with verified baseline / no invented targets

Observed old full Model Dump (separate live test, before this audit) ~105 MB and 12.85s for 5,296 elements. Current `scripts/archicad_executor.py` triggers `dump('before')` then `dump('after-*')` on writes. That's two full native dumps and JSON handling in the script path; **do not multiply 12.85 by 2 as a measured end-to-end time**, since conditions/overhead vary.

Measure:
- `T_first_H0`: elapsed brief to accepted conceptual structural handoff;
- `T_first_H1`: elapsed to accepted calculation-ready package;
- `T_edit`: preview → write → readback accepted;
- `T_delta`: change → affected obligations revalidated;
- `T_struct_iteration`: structural feedback → accepted architectural change;
- `full_dump_count_per_edit`, `unnecessary_checker_calls`, `auto_commit_failure_rate`, `structural_return_count`.

Compare baseline vs new behavior on same frozen model and tasks. No performance percentages without tests.

## 9. Integration readiness matrix

| Provider | Use | Decision | Boundary |
|---|---|---|---|
| AC29 native SAM, Model Check, SAF | structural handoff | REUSE, P0 | AC29 live readback later |
| LIRA-FEM 2026 / SAPFIR | primary Russian engineer receiver | PILOT, P0 | actual license/version |
| SCIA AutoConverter | IFC→FEA/SAF alternative | OPTIONAL, P1 | commercial |
| SCAD Office | Russia engineer alternative | CHECK VERSION, P1 | AC29 plugin compatibility unknown |
| RFEM6 `dlubal.api` gRPC | external structural specialist automation | OPTIONAL, P1 | API key, host, licence |
| older RFEM SOAP client | legacy only | DO NOT BUILD ON | maintenance since 2025 |
| Ifc2CA/Code_Aster | OSS analysis research | REFERENCE, P2 | not signed-off structural calculations |
| CYPE Open BIM Analytical Model | thermal/acoustic model | SPECIALIST LATER | NOT structural SAM |
| Graphisoft room live-load mapping | approved load categories | REUSE, P1 | engineer validates values |
| buildingSMART IDS+IfcTester | handoff property completeness | REUSE, P0 | not geometry or structural strength |
| Graphisoft/BCF Issues | feedback to architect | REUSE, P0 | active version/issue mapping |
| dRofus / PRE / RRE | program source if licensed | REUSE_OR_MINI_SCHEMA | do not force subscription |
| Our details v2.12 | indexed supplier detail candidates | REUSE_WITH_GATE | source conflicts, not approved |
| Husky/Tapir/open MIT connector | authoring/capabilities | BENCHMARK_PER_ACTION | exact AC29+undo tests |
| HarnessBIM | checker contract and tests | HARVEST_SELECTIVELY | early version; no live AC29 proof |
| Solibri Connection | optional incremental independent QA | OPTIONAL | licence required |

## 10. No-code architecture audit assertions

- Current library has *many* documents and experimental scripts; runtime's general architectural planner + structural handoff compiler is **NOT IMPLEMENTED**.
- No claim that current commands can generate a normative, structurally ready multi-storey building.
- Native SAM, SAF, model checks and live-load classification are published feature capabilities, not user-project verified.
- LIRA 2026 and Dlubal gRPC are documented receivers, not installed or proven usable here.
- All live structural and model tests remain BLOCKED until explicit approval to use the working test project.

## 11. First experiment queue

- `STRUCT_HANDOFF_BASELINE_01`: manual baseline, requested engineer format and acceptance questions.
- `AC29_SAM_READ_01`: count/filter/IDs of physical and analytical members; variation; load cases; continuity; nonmembers.
- `SAF_MAP_01`: material/profile translator coverage, catchall fallback veto, units/storeys/coordinate origin.
- `SAF_RECEIVER_LIRA_01`: controlled IFC+SAF export and compare receiver import, changed ID, objects, storeys, material map.
- `STRUCT_CORE_ADJUST_01`: native core physical quality vs SAM adjustment rules and no physical geometry mutation.
- `LOADS_ZONE_01`: verified occupancy category→loads from Zones, change invalidation after Update Zones.
- `DISPATCH_HOT_01`: compare single full-dump per write vs per-GUID scoped read, determine actual latency and correctness.
- `ROOM_ATOMICITY_01`: injected failure after walls/slab, no unreconciled partial model; host and story explicit.
- `DETAIL_INDEX_MATCH_01`: query v2.12 catalog by assembly signature without approving unresolved elements.
- `ENGINEER_FEEDBACK_01`: returned dimensions/locations through Model Compare/BCF, impact on architecture and H1 snapshot.

## Sources

Graphisoft official AC29 help and C++ API URLs as above; LIRA 2026 release notes; SCAD help; SCIA API; Dlubal API gRPC docs; ISO 7817-1:2024; buildingSMART IDS1.0, SAF guide examples; GitHub tracked code and details/v2.12 audit.

**Final decision:** REFRAME SYSTEM AS "BRIEF → VALIDATED ARCHITECTURE → STRUCTURAL HANDOFF → ENGINEER FEEDBACK". H0 first, H1 next, complete documentation only after early feasibility. Incremental checked facts and a single safe command spine are the accelerators, not more LLM agents or full-model dumps.
