# Architectural AI checkpoint 29 — code-backed audit of Pascal, ArchSight AIOS and DDC Skills

Date: 2026-10-08
Branch: feature/working-archicad-mvp
Target: Archicad 29 ONLY; Archicad 30 deferred
Status: static source audit, NOT runtime-tested on user's PLN

## Purpose and method
This checkpoint extends checkpoints 20–28 (open normative/IFC graph; CSE; documentation; section/detail selection; whole-system OS; vertical-core/design grammar; specialist models/benchmarks).
New candidates were checked against GitHub README, repository metadata, source code, test files and licences.
We distinguish:
- IMPLEMENTED_IN_SOURCE (source and test references visible);
- CLAIMED_IN_README;
- EXPLICITLY_UNSUPPORTED;
- AC29_NOT_TESTED;
- WRONG_DOMAIN.

No automatic installation and no tests on the user's Archicad session were performed.

## Finding A — Pascal Editor is more than a viewer

Source: https://github.com/pascalorg/editor
License: MIT (root repository); no native Archicad connector verified.
Repo is local-first scene graph/editor with bundled scene packages:
- packages/core: schema, scene state, geometry systems;
- packages/mcp: headless local MCP, mutation tools and SQLite scene storage;
- packages/ifc-converter: IFC import/export;
- packages/viewer/editor/nodes/cli.

### High-value code-backed mechanisms
1. `packages/mcp/src/tools/apply-patch.ts`: planned create/update/delete batch, patch guards, identity constraints, single undo step. Tool says batch atomic; full persistence crash-atomicity should not be assumed without tests.
2. `packages/mcp/README.md`: SQLite local state, versioned writes, live `scene_events` stream/SSE; version conflict yields `live_sync_version_conflict`.
3. `packages/core/src/systems/wall/wall-operations.ts`: wall rectangle reuses existing covered segments; wall division retains original wall ID and migrates referenced zone boundary-wall IDs.
4. `packages/core/src/systems/owned-floor-openings.ts`, `stair/stair-opening-sync.ts` and `elevator/elevator-opening-sync.ts`: owner-linked slab/ceiling openings are derived from stairs/lifts. Explicit provenance (`source`, `stairId`, `elevatorId`) and stable derived-ID logic are present.
5. `packages/core/src/systems/wall/wall-assembly.ts`: layered wall geometry, material thicknesses and side/justification logic; source clearly warns that presets are based on US IRC/ASTM and some thicknesses are unverified.
6. `packages/ifc-converter/README.md`: importing IFC can recover parametric walls, doors, windows, slabs, columns and room/level objects; roof semantics and many IFC classes fall back to imported meshes; reference-line cleanup and a Pascal-specific identity round trip are documented. Tests include openings, room-first load, wall extents, export round trip.
7. `packages/mcp/src/tools/check-collisions.ts`: candidate furniture plan-footprint AABB with declared dimensions/rotation and `checked|partial|insufficient_evidence`; explicitly does NOT verify vertical clearances, door swing, room containment, delivery route, exact item mesh geometry.

### Very important boundary
Pascal does NOT demonstrate:
- current Russian SP/GOST legal checking;
- Archicad native composites/GDL/layouts;
- native Archicad live connection;
- load-bearing/span/fire/MEP full engineering;
- architectural project-wide cross-storey constraint propagation.

Thus it is NOT an alternative source of truth to the user's AC29 PLN.

### Best use
REUSE_CODE/METHOD candidate for:
- patch guards and batch architecture;
- owned/reactive openings;
- IFC-to-room-aware scene import heuristics;
- rapid independent visualization/prototyping;
- honest clearance assessment and incomplete-evidence reporting.

Do NOT add Pascal as a permanent second editor in the MVP until measured benefit is shown.
Use a tiny isolated sample; do not copy US norm presets as Russian construction rules.

## Finding B — ArchSight AIOS has a real normative knowledge governance/runtime pattern

Source: https://github.com/ArchSightLabs/archsight-aios
License: Apache-2.0.
Category: agent skill/workflow governance, NOT BIM authoring.

Verified source:
- `docs/v1.5.0-knowledge-pack-runtime.md`;
- `templates/knowledge-pack/knowledge-pack.source.json`;
- `runtime/capability-registry.json`;
- `governance/arbitration-protocol.md`;
- `scripts/validate-knowledge-pack.mjs`.

Knowledge Pack source defines:
- pack ID/region/discipline/status/version;
- source register, authorization/hash/review;
- standards including sourceVersion/effectiveStatus;
- clauses with application conditions and exceptions;
- entities/relations and provenance;
- lookup rules with required context;
- evaluation questions and expected citations/abstentions;
- human review status.

Compile/lookup/eval workflow produces a local reference knowledge pack.
`knowledge.norm_lookup` result states include `found`, `not_found`, `conflict`, `inapplicable`, `error`, plus context applicability. The evidence-arbitration protocol forbids treating LLM inferences as deterministic tool results and distinguishes review from execution.

Limit explicitly stated by its authors:
- NOT a production normative corpus;
- NOT automatic code compliance;
- sample evidence is SYNTHETIC;
- source licensing must be respected;
- published knowledge means internal review, not legal/regulatory approval.

### Best use
REUSE_METHOD/OPTIONAL_CODE for:
- Russian verified clause-pack packaging;
- abstention/conflict/inapplicability tests;
- claim/evidence/decision triage;
- multi-agent tool-permission governance;
- one set of instructions shared across AI clients.

COMPARE with existing ACCORD/AEC3PO/BCRL/SHACL work. Do not create a second normative data universe: either adapt the Knowledge Pack protocol as a lightweight retrieval interface or use it solely for tests/policies. One canonical source/requirements graph must remain authoritative.

## Finding C — DDC Skills contains ready tasks, but a Skill is not automatically a tested executable

Source: https://github.com/datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction
License: MIT repository-level; linked converters/datasets may have separate restrictions.
README currently describes 238 SKILL.md packages across BIM, QTO, analytics, reports, CAD conversion, costing, automation.

Inspected examples:
- `1_DDC_Toolkit/BIM-Analysis/bim-validation-report/SKILL.md`: contains example Python validator code and a rule taxonomy; does NOT prove Archicad 29 end-to-end reliability.
- `1_DDC_Toolkit/BIM-Analysis/ifc-qto-extraction/SKILL.md`: explains extraction with DDC executables/IfcOpenShell; significant performance/ROI percentages are promotional, NOT independently benchmarked here.
- `1_DDC_Toolkit/CAD-Converters/ifc-to-excel/SKILL.md`: instructs use of `IfcExporter.exe`; another converter repository contains a proprietary EULA, so repository MIT does not authorize treating all its binary dependencies as freely reusable.

### Best use
REUSE_SKILL_TEMPLATE for narrow work such as:
- IFC extract-to-sheet/structured output;
- QTO reporting;
- model validation report formatting;
- change-order/project admin workflows.

For native BIM operations use AC29/Tapir/IfcOpenShell and existing QA; do not let broad LLM-generated scripts become an unreviewed parallel authoring backend.

## False positive screened out — "bimstack"
Repository `govtech-bb/bimstack` is for Barbados government digital-service delivery agents, not Building Information Modeling. Architecture/product patterns may be generic, but it is WRONG_DOMAIN for this search. Explicitly reject despite name.

## Updated project recommendations

### Keep
- Archicad 29 authoritative live model;
- native Model Dump/observer read path;
- benchmarked Tapir / Archicad-MCP / HuskyBIM for writes;
- IFCtoLBD for IFC semantic snapshot;
- ACCORD/AEC3PO/SHACL/IDS open compliance concepts;
- external solvers/specialist engineering;
- HOT/WARM/COLD, LIGHT/MEDIUM/HEAVY, Coverage Signatures, CSE, Information Obligations.

### New candidate utilities
- Pascal local scene/MCP: sandbox only, to evaluate reactive geometry and IFC, not second production editor.
- ArchSight Knowledge Pack: offline sandbox for 20 source-verified Russian clauses with negative/conflict/edition cases.
- DDC Skills: read/adapt validated task templates only; check every binary and data licence.

### Do NOT install three more full applications
Source-level audit is not evidence of practical AC29 interoperability. Production choice requires an instrumented run in a disposable project.

## Proposed tests (not yet executed)

### PASCAL-IFC-01
- AC29 -> controlled IFC sample;
- import into Pascal;
- compare wall, window host, rooms, stairs, floors and native IDs;
- mutate wall and measure dependent update;
- IFC re-export, verify GUIDs, composite/layer metadata and losses against AC29 Model Dump;
- detect unsupported cases explicitly; never overwrite user PLN.

### PASCAL-DEPENDENCY-01
- one staircase/shaft with openings on 2+ storeys;
- move/resize; check owned openings add/update/remove, no duplicates;
- compare against AC29 actual expected behavior;
- assess time/memory, not screenshots.

### AIOS-RU-01
- 20 verified Russian requirements (no unauthorized full texts);
- pack source/hash/version/applicability/exception and human-review state;
- 5 applicable, 5 missing-context, 5 historical/superseded, 5 conflicting/false-context tests;
- require abstention and citations on every normative claim;
- compare with ACCORD/our existing active rule packs.

### SKILL-IFC-01
- IFC extraction on real AC29 sample;
- report exact GUID/story/quantities with units;
- compare with Archicad's own measured quantities;
- audit licensing for any external executable.

## Final principle
Do not use another tool simply because its repository has many features, skills or stars.
Acceptance = less human time to a verified usable AC29 project, with reliable semantics, code applicability and reversible edits.
