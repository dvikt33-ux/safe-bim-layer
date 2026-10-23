# APA №2 — BUILD-01, 2026-10-23 06Z | Engineering integration report

## Concrete contribution to BUILD-01 G2/G3

**A-01: Compound slab mutation is journaled but lacks an independently evidenced MODIFY approval.** The existing SceneWriter (PR162, blob `484c600a205192d5737e124f8d47c8583e07a9f3`) records the `CreateSlabs` operation, reads its GUID, writes `BASIC_MODIFY_ATTEMPTED` to SQLite and invokes `ModifySlabs`. In the inspected path, the second mutation does not undergo the same separate `permission == command` check as the original CREATE. This is a policy-scope gap, NOT proof of a runtime exploit. **No second writer required.** Owner: BUILD-01 executor. Gate G2 cannot be accepted until exact two-operation permission and independent readback are qualified.

**A-02: Authored additional `CreateBeams`/`CreateSlabs` have a weaker pre-graph spatial check.** `compile_authored_intent` (blob `439f6d26ce097cdfdfc33a2b5a245352073151f2`) explicitly checks story/envelope for added Walls/Roofs/Columns, but not those two additional kinds. The Tapir schema allows omitted `floorIndex` for both. Existing BIM Graph validates JSON schema and dependencies, not the full authored floor envelope. Minimum adapter: add fail-closed story index/absolute level/envelope qualification in the *existing* compiler preflight; do not create a new router.

**A-03: An offline authored run is not currently an available public `run_project` mode.** `schemaVersion=apa-authored-project/1` requires `mode in {"preflight","execute"}` and a callable transport. `compile_candidate(...,read_api=...)` provides a source-only injectable read interface; this is not a completed OFFLINE BUILD-01 test. Safe next path: exact local runtime read-only preflight after G0, or a minimal immutable source fixture passed to existing compilation functions, without writing PLN.

## G0–G5 gate status and reproducible integration path

| Gate | Current status | Reuse and exact blocking evidence | Definition of READY |
|---|---|---|---|
| G0 | BLOCKED | Windows loaded-module path+SHA256; `GetAddOnVersion`; `DynamicCommands.probe_runtime` → `API.IsAddOnCommandAvailable`; pinned 262-command Tapir 1.5.10 snapshot is historical PLN port 19723, NOT installed proof. `GetAPARuntimeInfoV1` and `GetModelDumpV1` absent in snapshot. | Exact Archicad 29 build5101 PID/port/PLN, APX SHA, registered command inventory and schemas, immutable code commit |
| G1 | SOURCE_ONLY | PR74/162 `compile_authored_intent`, `BRIEF.resolve_stories`, BIM Graph, typed host refs. Added Beams/Slabs require explicit story and envelope checks. | Actual OFFLINE/READ-ONLY preflight with two native story bindings, topological DAG, plan hash, no write |
| G2 | SOURCE_ONLY | Tapir `CreateSlabs` v1.0.3 has no `structureType/buildingMaterialId`; `ModifySlabs` v1.4.0 supports them. PR149 verifier Basic pre-existing story0 material-only, NOT the PR74 compound flow. | Exact installed schema, authorized CREATE+MODIFY, GUID/host/material/geometry readback for all 7 types |
| G3 | NOT_AUTHORIZED | Existing SceneWriter SQLite intent-before-write; PR126 `execute_batch` 1–200, PR162 group-first Column/Beam conditional. No second writer. | Separate owner approval of new scratch PLN/port/plan hash; one run, stop on UNKNOWN, no retry |
| G4 | NOT_RUN | `GetAllElements(databases)` must inspect per-database `executionResultForDatabases`; `Get3DBoundingBoxes` is not BREP; `GetModelDumpV1` runtime unproven. | Real guarded Save, GUI close, no-open proof, reopen and independent GUID/BREP/material/host checks |
| G5 | NOT_RUN | Existing authored compiler, new separate scratch and changed input brief. | Different contours/heights/openings verified in second independent native model |

## Provenance and licensing

- Source pinned: PR162 head `f7c37b84b76c040c417ccd58a5543326e50f673a`; PR74 head `5a3a9201a715a5528c93bed4a5318e2acb32eea7`; PR149 head `4c119428e9b1c24bd00774c91a6f33cbf26f0369`; PR126 head `f12aeba017ecd34a13989998f0b7700f6a0107d2`. These are **source refs**, not installed commits.
- Upstream Tapir is MIT: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE . Upstream tag 1.5.9 resolves; tag 1.5.10 returned NOT_FOUND, which does not disprove local customized 1.5.10 binary. Graphisoft Archicad/SDK proprietary; repository code license not confirmed (root LICENSE 404).
- Read historical `PROJECT_PLAN.json` rev182 at commit `049576378c961c5d7a9a62611f4091e3da70d309`, blob `c2ab2f9d606db1412c4031076103c267fc463f83`; not edited. Read matrix 61 candidates and latest available reports #1/#3.
- IFC/DXF/Hotlink/MEP/SAF/Publisher remain separate research lanes, not G0–G5 blockers.

## Evidence and counteraudits

30 selected real SOURCE reads in checks-A (issue + 14 PRs) and checks-B (15 pinned files), plus additional source checks. Nine integration routes in matrix. Counteraudit A tests mutation authority; B tests runtime/geometry completeness. Both are static and do not constitute an independent BUILD-01 model acceptance.

**Actual new tests in this cycle:** SOURCE 30 selected; OFFLINE 0; BUILD 0; INSTALLED 0; LIVE 0; ACCEPTED 0. No Windows PC access or model writes. No code/PLN/APX/main/NEXT modifications, no PR merge, no installation, no paid APIs.

## Archive 06Z

Original `research-2-integration-2026-10-22T06Z.md` not found in research-branch commit history; existing attachments and recovery index remain available. Do not fabricate original content. `PARTIAL_NOT_ACCEPTED`.

## Immediate next action

**99/100 (expert priority, NOT benchmark):** G0 read-only identify actual loaded APX SHA and runtime command registration. **98/100:** qualify the exact compound slab CREATE+MODIFY scope and added Beam/Slab story bounds in the existing compiler. Only after that may the BUILD-01 owner authorize G3 on a new scratch PLN.

MODEL_MODE_NOT_VERIFIABLE.
