# APA-P70.A01.S01 — Source-backed full-cycle product ↔ existing implementation map

**Date:** 2026-10-11. **Phase:** SOURCE. **Result:** crosswalk and source audit, not live acceptance.
**Controller:** `PROJECT_PLAN.json` (authoritative); this report does not create a second execution plan.
**Source baseline:** PR #34 `e955ffb63d24d79e3068b27d16a89dfa9860f99f` stacked on PR #16 `bcac2e821a95f927fa6ae9f5fa5742b45d9ca2dd`; both Draft/open. The existing delivery roadmap remains **PROPOSED_FOR_INDEPENDENT_AUDIT**, not authoritative task status.

## 1. Required full product modes and source-backed coverage

The [full-cycle contract](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-highlevel-whole-model-20261011/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md) explicitly requires `GENERATE_FROM_ZERO` **and** `ADAPT_EXISTING` (sole active PLN), subsequent structural feedback and final BIM/document release. The native first above-ground floor is named "1 этаж" at ±0.000; actual native story index must be resolved by GetStories, not assumed to be architectural floor number. No automatic protected-PLN switching.

| Requirement / product boundary | Existing implementation; immutable Git blob SHA | Verified level and actual limitation | Next existing task |
|---|---|---|---|
| Full-cycle goal, two modes, floor semantics | `docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md` `8b1cb6e835c29859c7eb3fd4dc7df24a05e3f0c9` | SOURCE_READ specification; full product not implemented | P70.A01.S03 / P70.A02.S01 |
| Intent compiler, single entry | `scripts/archicad_project_accelerator.py` `2017fbc43a3bebe11d65cd1786b0ae15a94acaea` | SOURCE_READ; `compile_intent` accepts **one** component and two primitive types; `run_project` has offline/preflight/one-shot execute; does NOT implement arbitrary project adaptation | P70.A01.S03 / P70.A02.S01 |
| Restricted parametric shell | `scripts/archicad_building_shell.py` `04b08ee0cb8267f8e035158c419d99b15f13c62b` | SOURCE_READ; width/depth 6–30 m, 1–3 named stories, 2–4 parallel bays; fixed slab 0.20 m; rectangular shell, fixed room topology; sample 25 create ops. **Not** general room planning/engineering | P70.A03.S01/S02 |
| Native dependency planning | `scripts/archicad_bim_graph.py` `fc68f82b1d0cf89d5d4576ac03225572a6ffadf2` | SOURCE_READ; schema validation, topology, references, hosted openings. No proven native generic clash/structural validation | P70.A03.S01/S03 |
| Only guarded scene writer | `scripts/archicad_scene_run.py` `322f610b08c5434da0db1897f15f474665a40b8a` | SOURCE_READ; `SceneWriter` journal before mutation; `execute` creates and verifies only; source contains **no transaction-safe resume/edit-existing path**; no replay allowed on ambiguous partial write | P70.A03.S02/S03 |
| Legacy native slab adaptation | `scripts/archicad_executor.py` `efbaf139c4a6707226a2e6bbe07a7cc9f5fafa28` | SOURCE_READ; `create_slab` calls `CreateSlabs` then `ModifySlabs(structureType=Basic,buildingMaterialId=...)`. This is a **non-atomic** donor recipe, not yet integrated into `SceneWriter` recovery | P70.A03.S02 |
| Project-local attributes/templates | `scripts/archicad_template_builder.py` `eadef8875372578609985edbd30ceced5075d4e8` | SOURCE_READ; `get_fill_runtime_index`, `material_dependency_plan`, material & template methods exist. Per-object semantic material resolver for generic building is NOT proven | P70.A02.S03 / P70.A03.S02 |
| Integration/capability coverage | `scripts/archicad_accelerator_integration.py` `b4efd579d5acc723439a1553e79b4a4b1c0074cd` | SOURCE_READ; read adapter, capability gates, saved dump. Provider presence ≠ installed/live support | P50.A02.S01 / P70.A01.S03 |
| Synthetic shell integration tests | `tests/test_archicad_building_shell_integration.py` `1d3dac1d52e71b833b5b53dca459f02878fba37b`; PR #34 | SOURCE_READ and GitHub Actions SUCCESS for head SHA. Synthetic 25-element linked creation ≠ actual full building | P70.A03.S02 |
| Live scratch attempt and slab mismatch | canonical [incident record](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md) `b6e6f4e246829af04313af63b0e4487f7f043f86` | **USER_REPORTED_LIVE_PARTIAL**, read-only diagnostic cited: 4 walls PASS, slab Created-Unverified 0.30 m Composite vs 0.20 m Basic intent; after failed readback, remaining 20 ops NOT_RUN. No validated Save/Reopen or safe continuation | P70.A03.S02/S03 |
| Build/release roadmap | `docs/research/apa-results/control/APA_ACCELERATOR_DELIVERY_ROADMAP_20261011.md` `10fb9eb468cae1c9bb8200b76440824b2469607e` | SOURCE_READ; proposed, awaiting independent audit. Do not dispatch from roadmap prose | P70.A01.S03 |
| Existing integration/anti-dup governance | `docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md` `0d70526395a66b6de32d6709ec5ff6d0e9687ce0`; `apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md` `156cfb713aac1cec401d4fc1b0d0c479cda1043c` | SOURCE_READ; reuse one graph/writer; research/report is not native test evidence | P70.A01.S03 |
| Roof, foundation, structural nodes, MEP, IFC/PDF final release | PR #16/34 + delivery roadmap (above); separately recorded native and library capabilities | NOT_VERIFIED as an integrated high-level executable. UI-level MEP availability and prior native write cycles **do not** prove generic project execution | P70.A04–A08 |

Code-path references are to the **PR #34 head** unless otherwise stated. `ARCHICAD 29 / Tapir 1.5.10` target is historical provenance from source reports, **not a live session executed by this audit**. GitHub CI verifies offline checks only.

## 2. Independent audit of proposed roadmap

1. **Reuse choice ACCEPTABLE AS DESIGN:** `Project Accelerator → existing BIM Graph → single SceneWriter → Tapir / already-supported native addon → typed readback`. No second writer, no separate "house agent", no competing controller or material database.
2. **Gap found:** Product promises adaptive replanning, semantic rooms, construction systems, material binding and edits. Current code `compile_intent` supports a single component, fixed primitive, `SceneWriter.execute` creates fresh steps; no update/diff. The roadmap must retain these as future deliverables, not existing capability.
3. **Root native slab incident:** `building-shell-v1` emits `CreateSlabs(thickness=0.20)`; the installed command can inherit project Composite 0.30. `verify_readback` correctly catches mismatch; it does **not** repair it. Native helper `ModifySlabs` already exists; port a narrow stateful adapter into the same journal. Do not simply loosen thickness tolerance or retry entire scene.
4. **Dependency warning:** `P70.A03.S02` depends on `P70.A03.S01`, which depends on P70.A02 library/story tasks; do not mark A03.S02 dispatchable prematurely. The repair can be scoped to an authorized regression/incident in an existing assigned task; changing DAG priority requires controller-reviewed modification.
5. **Test evidence:** PR #34 commit `e955ffb63d24d79e3068b27d16a89dfa9860f99f` has GitHub Actions `38097687501` conclusion SUCCESS. PR description reports 108/108 offline tests, but this audit **did not reproduce them on Windows** and does not upgrade to LIVE_PASS.
6. **Working-product test:** real first MVP criterion is a previously authorized disposable PLN with complete typed story/material/geometry/host readback, zero unknown native writes, and saved-reopened reinspection. Later exact model **diff/update** with stable GUID; not a prettier fixed-format building.

## 3. Delivery order / what to hand to implementer

The delivery roadmap exists; **do not author another project schedule**. Use these existing task IDs and dependency gates:

| Order | Controller ID | Bounded executable output | Definition of DONE |
|---|---|---|---|
| D0 source & reuse | P70.A01.S01 → S03 | This crosswalk, then independent review, missing-adapter specification | all files/SHAs and actual integration boundaries accepted |
| D1 incident recovery, after relevant gates | P70.A03.S02 + S03 | exact GUID/ledger reconciliation; pre-approved `ModifySlabs` on scratch only; typed readback; no blind replay | slab 0.20m **and** Basic/material verified, no ambiguous journal steps |
| D2 semantic compiler | P70.A02.S01, S03; P70.A03.S01 | per-project actual GetStories, attribute pack, room/axis/structural intent | repeatable offline graph and inspectable material/source mapping |
| D3 complete editable BIM model | P70.A03.S02 → S03 | connect donors to same writer, create/readback then diff/update | full native readback and Save→reopen; incremental modify without duplicates |
| D4 constructive scope | P70.A04–A05 | roof/foundation/stairs/detail & structural handoff | real supported geometry, provenance and engineering gates |
| D5 MEP & release | P70.A06–A08 | engineering coordination, project views/specs, IFC/PDF | output checked against model; unresolved norm/specialist obligations visible |

**Work handoff:** give implementer one eligible S-ID + its existing PR/branch SHA, relevant donor code, acceptance, prohibited side effects and expected evidence; no broad request to "build universal APA" without task boundaries. Keep main and protected PLN untouched. **No Work runtime was used in this audit.**

## 4. Recommended next decision

**P70.A01.S03** should independently ratify/modify the existing delivery roadmap and freeze single-writer contracts. It is held until this S01 is accepted; **P70.A01.S02** additionally waits for **P50.A01.S01**. For D1 prioritize existing incident without falsely claiming that blocked DAG dependencies are complete.

No new task IDs proposed: the identified gaps are already covered by P70.A01/A02/A03 and P00.A03.S03 (publisher race). New tasks would be semantic duplicates. Reassess only after the first SOURCE audit and implementation acceptance.

## 5. Safety & proof

No PLN/APX/main/master/prior tested code branch edits; GitHub research metadata and inbox only. CI status observed through GitHub; local Archicad not accessed. `SOURCE_VERIFIED` here means source code and authored repository documents **read through GitHub by blob SHA**; it does not certify all claims inside historical reports. This report requires GitHub publisher receipt/readback before claiming DONE_PUBLISHED.
