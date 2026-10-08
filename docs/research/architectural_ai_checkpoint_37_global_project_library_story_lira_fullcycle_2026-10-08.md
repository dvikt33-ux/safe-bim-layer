# Checkpoint 37 — full-cycle AI architect, global-to-project library, story convention, LIRA-FEM automation

Date: 2026-10-08
Target: Archicad 29
Mode: RESEARCH / DOCS ONLY, NO LOCAL AC29 OR PLN MODIFICATION.
Supersedes the *end-goal framing* of checkpoint 36. **Structural handoff remains milestone H1, not the end of the accelerator.**

## 0. User-defined product goal

Design an entire building from brief/site constraints through architecture, preliminary and then calculated structural systems, MEP coordination, normative review, construction details, interoperable project documentation, issued complete BIM/PDF/IFC packages, engineer feedback and final accepted design.

Must support BOTH modes:
- GENERATE_FROM_ZERO: entire project synthesis;
- ADAPT_EXISTING: inspect and finish existing authoritative Archicad PLN without unwanted file switching.

Success KPI: total human elapsed time from brief to final accepted project; monitor milestone times separately. No fabricated compliance/certified engineering claims.

A deliberately LONG/DEEP research+compile stage BEFORE modeling is not overhead to eliminate if it reduces expensive design-stage interruptions and rework. Treat as offline COLD PREBUILD, then HOT execution with reused project knowledge.

## 1. Global/Project library TWO-TIER architecture

Existing `details/ACTIVE_RELEASE` = v2.12 (1,215 detail units, 1,835 parameter facts, 601 component variants, 532 unresolved binding tasks, 5 KAIMAN cross-sheet mismatches). These counts are CONTENT, NOT APPLICATION COVERAGE or construction approval.

`details/index/source_counts.json` shows severe family imbalance:
- FAVORIT composite-panel 167 + FAVORIT sheet materials 200 = 367 ventilated façade records;
- KAIMAN/KERAKAM ceramic wall 227;
- relatively few complete systems for foundations, basement waterproofing, structural connections, accessible openings, firestop penetrations, large vertical cores, movement joints, complex roof drains, thermal bridges, stairs.

**Therefore do not maximize number of detail records. Optimize complete coverage of applicable construction conditions.**

### Global Source Registry (GSR) — LARGE persistent reusable index
Not a giant PLA loaded in Archicad. Store:
- source URL, publisher, source document title, exact version/date/hash, download license, usage rights;
- jurisdiction, product availability, system family, valid structural/equipment interface;
- certified/tested performance with proof, NOT just advertised value;
- source project edition, exact page/sheet, crop and detail ID;
- formats (PLA, LCF, GSM, DWG, IFC, RVT, PDF, STEP, native object);
- AC29 binary/version compatibility, object provenance and authoring capability;
- geometric/topological junction signature;
- material, thickness, opening, host, loading, climate, exposure and fire/acoustic/thermal limits;
- transformations allowed without invalidating evidence;
- statuses UNREVIEWED, TRANSCRIBED, TECHNICAL_REFERENCE, DESIGN_CANDIDATE, VERIFIED_APPLICABILITY, ENGINEER_APPROVED, BLOCKED;
- copyright/license restriction. Metadata/linking is preferred over copying restricted manufacturer files.

Use current `details/releases/v2.12/*` release as **read-only indexed source**; avoid reformatting 1,215 cases and losing provenance.

### Project Library Pack (PLP) — SMALL/FROZEN snapshot generated after research
For each approved project variant:
- choice of structure/MEP/fire/roof/facade/window/finishes and corresponding family options;
- selected 2D nodes; reusable native AC29 Favorites/Composites/Complex Profiles/attributes; only compatible objects;
- typified room kits, equipment, engineer reference systems;
- normative edition applicability, products and source evidence;
- project-local dependencies (interface signatures, locations, link IDs);
- manifest with all exact source hashes/licenses, component versions, known unknowns, validation tests;
- immutable approved version for audit, fast update by changed dependencies.
Link to global library, do NOT import every archive into Archicad.

### Per-project research compiler
1. Brief -> requirements/functional graph, architectural type and region/authority/edition.
2. Structural + envelope/MEP conceptual variants.
3. Enumerate **interfaces required** from those variants, build a missing-condition coverage map.
4. Search own v2.12 and manufacturer systems first, then portals/industry catalogs/technical publications, then engineer-approved donor library.
5. Filter source validity, rights, jurisdiction, exact CSE configuration, project-specific climate/fire/acoustic/loading.
6. Prioritize missing *families*, not many duplicates of one supplier.
7. Extract/transcribe approved source facts and parametric templates, retain source references.
8. Validate with normative/expert sources; if specialist calculation needed mark unsolved/approval required.
9. Assemble PLP and verify AC29 import/readback compatibility (later on scratch project).
10. Freeze revision, compiled norm pack, UI capabilities and dependent project decisions.
11. Warm start generation; subsequent changes only re-run changed relevant research chunks.

**Prebuild termination criteria**: project program + geospatial constraints known; every applicable critical assembly family has at least one candidate or clearly BLOCKED status; every safety-critical unknown identified; structural/MEP conflict classes mapped; source provenance complete; no spurious false approvals. Time may be large, but avoid endless non-productive catalog crawling after sufficient coverage.

### Newly verified primary source pools
- TechnoNICOL Archicad system catalog PLA, roof/wall/foundation assemblies; 2025 update +36 systems, removal 17 obsolete: https://nav.tn.ru/bim/stroitelnye-sistemy/katalog-sistem-archicad/
- TechnoNICOL Archicad equipment PLA/LCF, 161 objects: https://nav.tn.ru/bim/komplektatsiya-stroitelnykh-sistem/katalog-komplektatsii-dlya-ploskoy-krovli-archicad/
- TechnoNICOL Archicad detail albums: https://nav.tn.ru/bim/albomy-uzlov/albomy-uzlov-archicad/
- TechnoNICOL 2D detail elements +60: https://nav.tn.ru/bim/albomy-uzlov/katalog-elementov-uzlov-archicad/
- TechnoNICOL wedge thermal insulation library object published 2026-08-13 supports AC22–28 only: AC29 not verified; do not install directly. https://nav.tn.ru/bim/plaginy/bibliotechnyy-element-klin-tekhnonikol-dlya-archicad/
- KNAUF Russian technical solutions 88 documents including work albums/CAD/BIM: https://www.knauf.ru/documents/tehnicheskie-resheniya/
- KNAUF products 1006 documents (NOT all technical nodes), supported test reports: https://www.knauf.ru/documents/all-documents/
- Knauf international Archicad BIM details and BIM WIZARD (jurisdiction and version relevance caution): https://tools.knauf.pt/herramientas-y-servicio/descargas/formulario-bim.html
- Hilti manufacturer CAD/IFC technical/test docs, firestop/equipment: https://www.hilti.group/content/hilti/CP/XX/en/services/engineering/technical-data.html
- NBS Swagger API appears to be marketplace inventory, NOT proof of generic full NBS Source catalog or details API: https://api.nbs.com/index.html

### Coverage taxonomy to research at project start
- substructure: foundation, groundwater/basement, retaining walls, settlement/movement;
- frame: slab-column, wall-slab, beam-column, steel bolt/weld, timber connections, transfer;
- envelope: façades, wall corner, parapet, roofing, window/door head/jamb/sill, balcony thermal break;
- fire/acoustics: compartment continuity, shafts, penetration sealing, floor/wall sound;
- services: MEP risers, ducts, embedded parts, equipment supports, roof drainage, maintenance access;
- circulation: stairs, railings, ramps, lifts, expansion joints;
- interior: partitions, drywalls, wet-room systems, floor build-ups, ceilings;
- site/civil: grades, paving, drains, pedestrian accessibility, entrance ramps;
- climate/locality: wind/snow/temperature/exposure/soil/groundwater.
Each category needs APPLICABILITY COVERAGE, not arbitrary record counts.

## 2. Story semantics — never treat API index as architectural name

User convention: **lowest above-ground occupied floor is «1 этаж», with its floor-level elevation at +0.000 m**. Do not create or publish a level named «0 этаж» to mean floor1.

Archicad exposes `API_StoryType.index`, `floorId`, `level`, `uName` and `API_StoryInfo.firstStory, lastStory, actStory, skipNullFloor`. `skipNullFloor` controls whether above-ground story indices begin with 1 rather than 0. This is first-party, not a guess:
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___story_info.html
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___story_type.html

Do NOT simply add 1 to every index: basements, floors skipped, story table, and project-specific naming matter.

**Canonical story resolver contract:**
```yaml
architectural_story:
  name: "1 этаж"
  ordinal_above_ground: 1
  elevation_m: 0.0
  project_zero_m: 0.0
  archicad_floor_index: from_GetStories_or_GetStorySettings
  archicad_floor_id: from_native_story
  elevation_datum: Project_Zero
  below_ground: false
  above_ground: true
  verified_exists_in_current_project: true
```

For every write:
1. Receive story ID/name/architectural ordinal from design intent.
2. Resolve against actual currently open AC29 story table, floorId/index/level.
3. Reject ambiguous / missing / mismatching elevation.
4. Put actual resolved `floorIndex` in Tapir payload.
5. Read-back verifies underlying story relation AND exact elevation; no synthetic floor creation.
6. Projects with basements need explicit `-1` etc mapping via real story table, not guessing.
7. When starting a new project, intentionally create named story «1 этаж» at +0.000, then «2 этаж» at project-specific elevation, etc, using native settings.

Known issue in `safe_bim_layer.py`: `create_room` hard-codes floorIndex 0 and attaches door to first wall; fix before considering it production. Do not replace 0 with 1 blindly.

## 3. LIRA-FEM (formerly LIRA-SAPR) automation — much stronger than assumed

Official 2025 rename: «ЛИРА-САПР» became LIRA-FEM, «САПФИР-3D» became LIRA-CAD. Ref:
https://lira.land/lira/release-notes/2025/

LIRA-FEM 2026 R1 supports COM automation in Python/C#/C++/JS:
- `LIRA-FEM API` controls model/editor (VISOR), manipulates model and input tables;
- `LIRA-FEM RES API` reads computed results; 2024–25 Python `comtypes` example with documented `LiraResAPI.dll`, `LiraResultsAccess`, `LoadCaseDisplacements`;
- 2026 user extensions loaded inside process, commands + calculations pipeline + report book CSV/screenshot sections;
- 2026 batch task calculator and LAN compute queue, server auto results return if configured;
- 2026 partial IFC updates and import enhancements plus SAF exchange;
- no need to develop own structural FEM solver.
Sources:
https://www.liraland.com/lira/release-notes/2026/api-and-input-tables
https://help.lirasapr.com/en-gb/extensions/
https://lira.land/forum/forum9/topic2666/messages/
https://lira.land/lira/release-notes/2026/calculation-and-performance
https://lira.land/lira/systems/analysis_server.php
https://lira.land/lira/release-notes/2026/components-of-bim-technology

**CRITICAL HONESTY GAPS:**
- Specific headless COM method to submit/run/check job with unattended licensing+UI not yet verified. Batch GUI + LAN queue confirmed as features, API trigger remains test requirement.
- Actual installed user version/licence/modules/API/CodeMeter required; do not state the user possesses them.
- Structural load cases, boundaries, support stiffness, combinations, FEM mesh, analysis interpretation must be engineer-verified. A successful software run is not professional structural approval.
- 2026 LIRA-FEM examples show country-specific DBN/EN/Kazakhstan/SNiP snow standards; this does not establish current Russian SP20 / SP63 compliance of user's edition. Gate by explicit country, active standard and exact code edition.
- EU/UA manufacturer/source bundles need jurisdiction and product availability filter.

### Suggested LIRA adapter / not a new FEM engine

```
AC29 physical BIM / native SAM
   -> first-party SAF + scoped IFC if needed
   -> StructuralExchangeManifest (IDs, units, axes, story-level mapping, materials, profile, supports, case assumptions)
   -> adapter to LIRA-CAD / LIRA-FEM:
      COM model/input table population or IFC/SAF import;
      optional calculation dispatch through proven batch/LAN interface;
      RES API result read;
      report/action/evidence mapping;
   -> StructuralEvidenceBundle:
      displacements, forces, utilization, checks, governing case,
      exact norm/combination/solver version, source model digest,
      result trust/specialist signoff.
   -> engineering changes as BCF/model compare / GUID impact proposals
   -> Architect accepts relevant geometry/material/section edits
   -> re-export and re-evaluate affected questions.
```

**Do not feed unqualified FEM numeric section into AC29 automatically as design approval.** Allow *proposal* with engineer review and accepted signatures.

### LIRA automation staged tests
1. `LIRA_DISCOVERY_01`: installed version, licensing/modules, API class IDs, registered COM ProgIDs, data IO, supported design standards.
2. `LIRA_RES_01`: read known solved beam from a test case through `LiraResAPI.dll`, compare with UI displacement/internal force.
3. `LIRA_MODEL_01`: read/write small test model via COM + input table, verify no undocumented resets.
4. `LIRA_CALC_01`: benchmark batch/UI job execution and discover whether equivalent API job start/status/cancel exists.
5. `LIRA_EXCHANGE_01`: AC29 sample SAF/IFC → LIRA, compare nodes, axes, levels, material/profiles/loads, member mapping.
6. `LIRA_BACKFLOW_01`: map engineered dimensions/requirements and model update to AC29 as proposed changes then explicit engineer approval.
7. `LIRA_RU_CODES_01`: engineer validates Russian active SP applicability vs actual installed LIRA standard settings; no assumption.

## 4. Full-cycle phases — conceptual structure handoff NOT final goal

- P0 Research&Compile: long COLD research, formal requirements, code versions, global-source→project library, BIM template capabilities and specialist handoff.
- P1 Concept Generate: architectural grammar/invariants, site/axes, core, rooms, concept structural grids/envelopes, topological and accessibility constraints; one BIM model.
- P2 Candidate Selection: OR-Tools/Finch/precedent/TopologicPy etc rank feasible options; project library CSE matches.
- P3 Author: existing native AC29 writer route, batched, local readback and impact-aware change tracking.
- P4 Engineer Input and Simulation: SAM/SAF/IFC, structural (LIRA if licensed), HVAC/MEP/fire/energy/acoustics as needed.
- P5 Convergence: coordinate engineer findings back into architecture, update only affected dependents, regenerate accepted scopes.
- P6 Documentation Compiler: native saved views, sections, details, schedules, layouts/publisher, Russian SPDS, demand-driven coverage.
- P7 Final Evidence&Publish: normative model and cross-representation checks, signed specialist evidence, output revisions and package.
- P8 Project Maintenance: later changes regenerate localized affected deliverables and notify required specialists.

**Research may be deep and expensive if it buys faster implementation but has objective closure tests.** No need to wait for H3 to do H1, or for engineer acceptance before running preliminary architectural checks. Active design phases have short HOT cycles.

## 5. Integration architecture / only unique custom glue

```
High-level Project Director [GPT]
          |
 PREBUILD RESEARCH COMPILER
  Global Source Registry -> Project Library Pack + compiled rulepack
          |
 PLANNING: constraints/predecessor library/OR-Tools + design intent
          |
 ONE AC29 ACTION DISPATCHER
  native tools + Tapir / Husky / validated adapters
          |
 Authoritative CURRENT OPEN PLN (model and project identity)
          |
 Incremental Fact+Dependency Graph  [native observer, room fit, CSE, quality]
          |                    \
 SAM/IFC/SAF + specialist engines    Native documentation compiler
 LIRA-FEM/MEP/fire/thermal QA           saved views/schedules/Publisher
          |                    /
        ENGINEER FEEDBACK + REPAIR
          |
        FULL-CYCLE VERIFIED RELEASE
```

New custom justified:
- global/project library applicability+provenance registry;
- gap/coverage assessment;
- exact story name/index/elevation resolver;
- LIRA adapter and source/result identity/provenance mapping;
- cross-system action routing+dependence and evidence;
- project-specific design optimization / repair priorities.
Reuse:
- existing JSONL detail corpus v2.12;
- manufacturer native AC29 BIM data;
- Archicad native Favorites, CSE, SAM, SAF, views and zones;
- program/space solver prior research; IFC IDS/BCF, validated code engines.
Stop:
- flat mega-library imported into AC29;
- static assumptions `floorIndex=0`;
- generic structural FEM solver;
- unbounded vector database without demonstrated FTS/typed metadata need;
- selecting detail based solely on visual similarity or number of pages;
- assuming all LIRA result values conform to current Russian SP;
- documentation generated separately from real BIM model.

## 6. Prioritized incremental and experimental gates

1. `STORY_NAME_INDEX_01`: read-only story table; verify first user-story at 0m with correct name and actual API index; below-ground story variants; reject fake floor zero label.
2. `LIBRARY_COVERAGE_01`: derive coverage matrix for one target project, identify missing construction families in v2.12; do NOT conclude 1,215 nodes are enough.
3. `PROJECT_LIBRARY_PACK_01`: prototype manifest with 10–30 applicable cases and immutable source links; candidate!=approved, zero unknown sources promoted.
4. `AC29_LIBRARY_IMPORT_01`: native PLA/LCF/GSM versioned import on scratch project, verify dependencies, stability and characteristics.
5. `LIRA_DISCOVERY_01` → `LIRA_BACKFLOW_01`: only after installed/licensed receiver confirmed.
6. `FULLCYCLE_01`: a small building from brief to model, H0/H1 handoff, engineered response, coordinated model, documentary release. Score total elapsed human minutes + rework and false pass rate.

## 7. Open questions / genuine residual risk

- Current Archicad project may have story index 0 that legitimately represents "1 этаж", or numbering can be affected by `skipNullFloor`; only native read reveals actual mapping.
- LIRA-FEM product availability + license + local ru-code module remain unknown.
- No measured autonomous end-to-end success on user's machine.
- Manufacturer source permissions/versions may restrict offline hoarding; link/cite metadata first.
- A large prebuild research package can become stale: record source hashes and version-based revalidation; model changes may introduce new junction families.
- Some specialist modules can produce results without official acceptance; evidence remains scoped to engineering discipline.

## Reference Source Highlights
- https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___story_info.html
- https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___story_type.html
- https://lira.land/lira/release-notes/2025/
- https://www.liraland.com/lira/release-notes/2026/api-and-input-tables
- https://lira.land/lira/release-notes/2026/loads
- https://lira.land/forum/forum9/topic2666/messages/
- https://nav.tn.ru/bim/stroitelnye-sistemy/katalog-sistem-archicad/
- https://nav.tn.ru/bim/komplektatsiya-stroitelnykh-sistem/katalog-komplektatsii-dlya-ploskoy-krovli-archicad/
- https://nav.tn.ru/bim/albomy-uzlov/albomy-uzlov-archicad/
- https://www.knauf.ru/documents/tehnicheskie-resheniya/
- https://www.knauf.ru/promo/architects/
- https://www.hilti.group/content/hilti/CP/XX/en/services/engineering/technical-data.html

Next cycle: project-specific missing-junction taxonomy and total coverage benchmark; then LIRA API class-by-class deep inspection once installed version is known.
