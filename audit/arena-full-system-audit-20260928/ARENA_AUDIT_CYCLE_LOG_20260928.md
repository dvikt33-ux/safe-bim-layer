# Arena audit cycle log — 2026-09-28

Method mandated by `ARENA_TASK_FULL_SYSTEM_AUDIT_20260928.md`: AUDIT → targeted passes → AUDIT → … until no static/source/design question remains → FINAL AUDIT. This log records what each cycle opened and closed. Arena had no Archicad; "closed" means closed at STATIC/INFERRED level or reduced to an executable LT experiment.

## Cycle 1 — Scope and repository archaeology

Opened: which code is actually audited; where the hardened runtime lives; whether tests/CI exist; whether live evidence is committed.
Passes: full read of the audit branch (30 files); `git ls-tree` of all 13 branches; merge-base analysis; worktrees for `arena/tapir159-compat-geometry-c6ab474` and `research/archicad29-tapir159-expansion`; ran all offline suites (108 pytest + 64 subtests; bimexec 45/62/14).
Closed: audit branch = v0.1 layer + docs, zero tests/CI; hardened runtime only on `arena/*`; research never references it; live scripts/raw JSON not committed (`.gitignore`).
New questions → Cycle 2: exact Tapir baseline; behaviour of every command the research relies on.

## Cycle 2 — Tapir source truth (tag 1.5.9 vs research baseline)

Passes: clone upstream; `git describe b1dc828` = `1.5.9-76-gb1dc828`, ADDON_VERSION 1.5.10; diff `1.5.9..b1dc828` (20 files, +1727/−357); generated 250-command inventory from `command_definitions.js` at 1.5.9 and 255 at baseline.
Closed: baseline mismatch (CONTRADICTED); five commands and several fixes absent live, incl. Slab `Get3DBoundingBoxes` crash (#686).
New questions → Cycle 3: Morph internals; SEO/opening internals; batch undo semantics.

## Cycle 3 — Morph / SEO / Opening / batch internals

Passes: read `BuildMorphBodyFromGeometry`, `AddMorphBodyFromMemo`, `CreateMorphs`/`ModifyMorphs` execute paths incl. `rotationDegreesZ` matrix code and `edgeDefault` handling; `CreateElementsCommandBase::Execute`, `ExecuteCreateWithElements`, `ExecuteModifyWithResults`; every `ACAPI_CallUndoableCommand` site; `CreateSolidElementLinks`, `TrimElements`, `RemoveElementTrims`, `GetCollisions`; `CreateOpenings` AC29 path; `GetAllProperties`; `Get3DBoundingBoxes` incl. ModelAccess body path.
Closed: `rotationDegreesZ` bug reproduced analytically (matches W7); partial-commit batches (lambda always NoError) with `TrimElements` as the atomic counter-example; `isClosed` is a status bit; `GetCollisions` exists (missed by research); Opening schema rectangular-only.
New questions → Cycle 4: are the Tapir comments about edge types and `PlacePolygonal` actually API limits? Does the API have destructive Morph booleans, per-edge roof data, shells, quantities?

## Cycle 4 — Official Archicad 29 API verification

Passes: fetched `ACAPI::Element::OpeningDefault` (Place/PlacePolygonal: "custom … use the polygon given"), `OpeningExtrusionParameters` (ShapeType Rectangular/Circular, width/height, LimitType, Constraint), element function group (`ACAPI_Element_ChangeMorphEdgeType`, `ACAPI_Element_SolidOperation_Create`, `ACAPI_Element_GetQuantities`, `ACAPI_Element_CalcBounds`, `ACAPI_Element_GetCollisions`, `ACAPI_Element_GetExtent3D`), `API_PivotPolyEdgeData`/`API_RoofSegmentData`, `API_RevolvedShellData`; community thread on morph solidity after API solid operation (unanswered; weak corroboration).
Closed: Tapir "not fixable from an add-on" (edge type) CONTRADICTED; Tapir "extents only" (PlacePolygonal) over-generalised; destructive boolean API confirmed; per-edge roof and revolved shell API confirmed; Tapir exposes none of these.
New questions → Cycle 5: database/window model and ghost GUIDs; verification rungs; fonts; library route.

## Cycle 5 — Databases, verification primitives, fonts, library

Passes: `ExecuteActionForEachDatabase`, `SwitchCurrentDatabaseToFloorPlan` (#532), `ChangeWindow` implementation (GoToView / storyIndex / databaseId), `DatabaseIdResolver` (fixed GUIDs vs `databaseUnId`), `GetSectionElements`/`GetElementsByType` `databases` parameter, `CreateAssociativeDimensionsOnSection` (no DB switch), `RebuildView`, `GetDetailsOfElements` supported-type list, `AttributeType` enum (no Font), `TextStyleSettableDetails.fontIndex`, favorites commands, `SaveAsModuleFile`/hotlink commands, `MoveElements`/`RotateElements` copy flags, `CreateProfiles`/`CreateComposites`/`CreatePenTables`/`CreateLines` schemas, `CreateStairs`, `CreateRoofs` (no per-edge).
Closed: read-side dual context is stock; write-side needs a small PR; ghost-GUID mechanism has a stock existence check; verification ladder can be stock for rungs 1–4; font-by-role via favorites; assemblies via `.mod`+hotlink.
New questions → Cycle 6: hardened runtime details relevant to A (locks, reconcile, project guard).

## Cycle 6 — Arena runtime safety review

Passes: `safe_bim_operations.py` (reconcile: contractHash, executionIdentity, no geometry→APPLIED), `safe_bim_runtime.py` (`_assert_project`), `safe_bim_lock.py`, `safe_bim_verification.py` signatures, grep for sandbox/version/allowlist (none).
Closed: strengths and gaps of the hardened runtime enumerated; P0 list finalised.

## Cycle 7 — Cross-check of research documents

Passes: `RESEARCH_MASTER_AUDIT.md` (older research pinned `d0dbb11` correctly), `WALL_COMPOSITE_THICKNESS_FAILURE_AUDIT.md` (rules consistent with schema), ledger §7–§15 (P0/P1/P2 list), task spec §B/§C/§E/§G/§J/§Tests.
Closed: contradictions register (audit §16); verdict table (audit §15) maps 1:1 to the 20 items.

## FINAL AUDIT — reopen check

Questions re-examined after drafting: (1) could `GetCollisions` be surface-only? → kept as UNRESOLVED (LT-B2/LT-C1) rather than assumed; (2) is per-write `ChangeWindow` justified by W5/W5B? → not provable from committed docs; reduced to LT-E1 instead of asserting removal; (3) does `ExecuteActionForEachDatabase` exist at 1.5.9 (not just baseline)? → verified on the 1.5.9 checkout; (4) is `CreateStairs` really in 1.5.9? → yes (inventory). No remaining static question that can be settled without Archicad; residual list in audit §17.
