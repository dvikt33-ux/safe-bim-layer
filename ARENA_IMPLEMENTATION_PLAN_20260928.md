# ARENA IMPLEMENTATION PLAN — Safe BIM hardening and capability build-out

Date: 2026-09-28. Companion to `ARENA_FULL_SYSTEM_AUDIT_20260928.md` (verdicts) and `ARENA_LIVE_TEST_PLAN_20260928.md` (LT ids). Ordering principle: safety controls that need no Archicad first; stock-Tapir verification second; Tapir upstream PRs third; new engines last. Every item lists the tests that must exist before it is called done and whether it is unit/mock, integration-without-Archicad, or live.

Base branch for code work: `arena/tapir159-compat-geometry-c6ab474` (the only branch with the hardened runtime and tests). The research/audit branches hold documents only. `main` is not modified by this plan until a reviewed merge.

---

## Phase 0 — Stop the bleeding (Python only, ≤ 1 day, no Archicad)

| # | Change | Files | Tests (all offline) |
|---|---|---|---|
| 0.1 | Delete `qwen_safe_bim_integration.cleanup_copy`; replace with a planned `cleanup_job` that deletes only receipt GUIDs after `_assert_project` and sandbox-token checks | `qwen_safe_bim_integration.py` | fake-BIM: cleanup with unknown project → refused; with receipts → exact GUID list deleted and absence verified |
| 0.2 | `TapirClient._raw_call` private; public `call(command, params, *, capability)`; static allowlist module `safe_bim_capabilities.py` `{command: {mode, min_tapir, max_tapir, forbidden_params}}`; `ModifyMorphs.rotationDegreesZ` in `forbidden_params`; unknown command → `CapabilityError` | `safe_bim_layer.py`, new `safe_bim_capabilities.py` | unit: unknown command refused; forbidden param refused; dangerous mode requires `intent` |
| 0.3 | Envelope validation: `succeeded` must be `True`; per-item `ElementIdOrError` split; any error item fails the step | `safe_bim_layer.py` | unit with recorded 1.5.9 error envelopes |
| 0.4 | Session handshake: `GetAddOnVersion == pinned`, `GetProjectInfo.projectPath ∈ sandbox allowlist`, `GetProjectInfoFields` contains `SAFEBIM_SANDBOX_TOKEN` | `safe_bim_layer.py`, `safe_bim_service.py` | unit: wrong version / path / token → no write call ever recorded |
| 0.5 | Regenerate `tapir-1.5.9.json` from `docs/archicad-addon/command_definitions.js` at tag 1.5.9; validate every outgoing payload against it (jsonschema); drop the 1.5.8 file | repo root | unit: every fixture payload validates; a payload with `rotationDegreesZ` still validates against Tapir schema but is refused by 0.2 (proves the allowlist is the control) |
| 0.6 | Evidence store: `audit/live-tests/<date>/raw/…` with SHA-256 manifest; `.gitignore` exception; runtime writes every request/response there when `SAFEBIM_EVIDENCE_DIR` is set | runtime + `.gitignore` | unit: manifest matches files |
| 0.7 | GitHub Actions: pytest (runtime + house primitives + safety), the three bimexec scripts, schema validation | `.github/workflows/ci.yml` | CI green |

## Phase 1 — Batch and context semantics (Python, uses stock Tapir)

| # | Change | Tests |
|---|---|---|
| 1.1 | Executor state `PARTIAL_APPLIED` with compensation list; never auto-retry a partially applied batch; compensation verified by absence readback | unit (fake item-2 failure) + LT-A2 |
| 1.2 | `database_context(db)` (flat, no nesting) that restores in `finally` and verifies with `GetCurrentWindowType` (+ `GetExecutionContext` when available); failure → `PAUSED_CONTEXT_UNKNOWN` | unit (fake raises mid-step) |
| 1.3 | Existence check in target DB: `GetElementsByType(type, databases=[db])` after any document-element creation (dimensions, texts on sections) | unit + LT-E3 |
| 1.4 | Remove per-write `ChangeWindow` for element types proven by LT-E1; keep for unproven types (table in capabilities module keyed by element type) | LT-E1 |
| 1.5 | Per-job attribute/story/library snapshot (`GetStories`, `GetAttributesByType` per used type, `GetLibraries`) invalidated on any write to those domains; GUID-only references | unit |

## Phase 2 — Verification ladder with stock commands

| # | Change | Tests |
|---|---|---|
| 2.1 | Analytic AABB from readback for Wall/Slab/Column/Beam/Morph; `Get3DBoundingBoxes` allowed only for types listed as safe for the pinned version (never Slab on 1.5.9) | unit (geometry), LT-F3 (optional) |
| 2.2 | `GetCollisions` preflight for every SEO link (operator ∩ target must collide) and post-condition (per operation) | unit (fake) + LT-C1 |
| 2.3 | Built-in quantity reader: discover Volume/Area property GUIDs via `GetAllProperties` once per session; `ΔV` postcondition for Subtraction/Trim | unit (fake) + LT-C2/C3 |
| 2.4 | Morph pre-write validator (manifold, orientation, Euler, planarity, signed volume, self-intersection) and post-write comparator (canonical vertex renumbering) | pure unit tests with known-good/known-bad bodies (open box, inverted cube, torus with hole loop, duplicate vertex) |
| 2.5 | Morph GUID-replacing lifecycle (delete + `CreateMorphs` + relink from `GetSolidElementLinks`) with `guid_lineage` records | unit + LT-B1 |
| 2.6 | Opening strategy: native rectangular now; probe-based evaluated proof; polygon/circular deferred to 3.4 | LT-C4 |

## Phase 3 — Tapir upstream PRs (C++; each small, each with a live test)

| # | PR | Scope | Live test |
|---|---|---|---|
| 3.1 | `atomic:true` on `CreateElementsCommandBase::Execute`, `ExecuteCreateWithElements`, `ExecuteModifyWithResults` (return first error from the undoable lambda; report `rolledBack`) | ~40 lines | LT-A2 (expect 0 walls) |
| 3.2 | `GetExecutionContext` (window type, current database id/type, story index, navigator item id) | ~60 lines | trivial |
| 3.3 | `ACAPI_Element_ChangeMorphEdgeType` after Create/Change when `edgeDefault` given | ~10 lines | LT-B3 |
| 3.4 | `CreateOpenings.shape ∈ Rectangular|Circular|Polygonal`, `polygonCoordinates`, `limitType/finiteBodyLength`, via `OpeningDefault` modifier + `Place`/`PlacePolygonal` | ~150 lines | LT-C4 polygon variant |
| 3.5 | `CreateMorphSolidOperations` (`ACAPI_Element_SolidOperation_Create`, returns result GUIDs, deleted operand GUIDs) | ~80 lines | LT-C5 |
| 3.6 | `ModifyMorphs(body)` experiment: `APIMemoMask_MorphBody` + closed-status re-read; document result upstream | ~5 lines | LT-B1 variant |
| 3.7 | `database` parameter on the shared create/modify executors (reuse `ExecuteActionForEachDatabase`; RAII `DatabaseScope`) | ~80 lines | LT-E2/E3 |
| 3.8 | `EvaluateElements3D` (ModelAccess; contract in audit §F.3) | ~300 lines | compare with LT-C1/C2 |
| 3.9 | `GetFonts` (enumerate `API_FontID`) | ~40 lines | LT-H1 follow-up |
| 3.10 | `CreateRoofs.edgeOverrides` → `memo.pivotPolyEdges` (`API_RoofSegmentData.angleType/angle/eavesOverhang/materials`) | ~120 lines | gable roof readback + ridge height |
| 3.11 | `CreateShells` (Extruded, Revolved) | ~250 lines | dome/vault creation + volume |
| 3.12 | Upstream issue reports: `rotationDegreesZ` (W7 repro), Slab `CalcBounds` crash already fixed post-1.5.9 (ask for a 1.5.10 release), `PlacePolygonal` comment correction | — | — |

Pin policy: Safe BIM's allowlist gains per-command `min_tapir` as each PR ships; behaviour keyed by exact version until then.

## Phase 4 — Builders and recipes

| # | Change | Tests |
|---|---|---|
| 4.1 | `CompositeBuilder` (preflight: BM GUIDs, thickness sum, in-use check; postcondition: `GetComposites` equality) | unit + LT-I1 |
| 4.2 | `ProfileBuilder` (polygon validity, skin overlap, `GetProfiles` canonical readback; probe element on `SAFEBIM_TEMP`) | unit + LT-I2 |
| 4.3 | `ElementRecipe` schema `{intent, structure, attribute refs (GUID), geometry, verification rungs, lifecycle}`; executable only when all refs resolve in the session snapshot | unit |
| 4.4 | Arrays at planner level (`MoveElements/RotateElements copy`), per-copy readback and count check | unit + LT-K1 |

## Phase 5 — Library and documentation engines

| # | Change | Tests |
|---|---|---|
| 5.1 | Shared library attach: `GetLibraries` → `AddLibraries` only if absent → `ReloadLibraries`; never `SetLibraries` | unit (duplicate attach) |
| 5.2 | Assembly reuse: `SaveAsModuleFile` + `CreateHotlinkNodes/Instances` wrapper with front-window guard and versioned file names | LT-J1 |
| 5.3 | GOST rule engine skeleton: `RuleSet(version, scale, viewType)`, rules with `normative_ref|policy`, `NOT_AUDITABLE` for unsupported readback; role→favorite mapping for texts | unit (rule evaluation on recorded readbacks) + LT-H1 |
| 5.4 | GSM `SaveSelectionAsSharedLibraryObject`: deferred until a concrete parametric-object need exists | — |

## Definition of done per phase

- Phase 0/1: CI green; no write path reachable without allowlist + handshake (grep test: `_raw_call` referenced only from `call`); all 10 regression tests from audit §14 present.
- Phase 2: every SEO/trim/opening step produces a receipt with rung results (1–4) and a grade; `LINK_ONLY` is never displayed as PASS.
- Phase 3: each PR merged upstream or carried as a documented fork build with its own `GetAddOnVersion` string; Safe BIM refuses PR-dependent commands on stock 1.5.9.
- Phase 4/5: recipes and rules are data files validated by schema tests; live evidence committed under `audit/live-tests/`.
