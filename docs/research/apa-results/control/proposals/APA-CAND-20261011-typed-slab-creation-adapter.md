---
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-20261011-typed-slab-creation-adapter
origin: technical
proposer_run_id: APA-RUN-20261011-apa-attributes-native-tapir-01
source_substep_id: APA-P10.A01.S02
proposed_parent_plan: APA-P30
proposed_action: APA-P30.A02
suggested_substep_id: APA-P30.A02.S03
work_key: capability-negotiated-typed-slab-create-reconcile
title: "Typed Basic/Composite slab intent, creation and no-replay recovery adapter"
kind: BUILD
priority: 1
depends_on:
  - APA-P10.A01.S02
  - APA-P10.A02.S01
  - APA-P30.A02.S01
related:
  - APA-P30.A02.S01
  - APA-P30.A02.S02
  - APA-P20.A02.S03
inputs:
  - ART-APA-PAVILION-SAVED-READBACK-20261011
outputs:
  - "Source-controlled typed slab intent/capability adapter"
  - "Offline 1.5.10/CreateSlabs-PR785 compatibility tests"
  - "Guided single-element live test with readback and durable journal"
acceptance: "Basic/Composite thickness and material semantics enforced per active PLN; no untyped CreateSlabs write; valid material GUID and story; typed post-create readback incl bbox, polygon and structure; exact one-off reconciliation with owner approval; idempotent journal; negative tests for unknown project, wrong GUID/attribute, ambiguous write, failed readback, Composite thickness mismatch, and mixed structure IDs; test proof published in GitHub with CI/readback"
requires_approval: true
expected_mvp_benefit: "Eliminates the observed 0.2m request → 0.3m Composite default error for general plans without mandatory unreviewed APX replacement, enabling repeatable floors/material intent."
evidence_urls:
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-p20-a02-s03-saved-pln-live-readback-20261010-222136.md
  - https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785
  - https://help.graphisoft.com/AC/29/INT/_AC29_Help/150_UserInterfaceToolSettings/150_UserInterfaceToolSettings-6.htm
risks: "This is a candidate only; upstream PR785 is OPEN and not part of proven installed 1.5.10. Owner-authorized live writes only in expendable PLN; no replay, no implicit material default; controller must audit overlap and DAG/dependencies before registering."
---

## Scope vs existing tasks

`APA-P30.A02.S01` establishes the overall *sequence* of MVP milestones; it does not provide typed Basic/Composite creation or safe recovery code. `APA-P30.A02.S02` defines **acceptance gates and rollback by phase**, while this candidate is a concrete bounded **single-element implementation**. These related tasks should be used as design inputs; the independent auditor may mark **DUPLICATE** if a newer artifact already implements this exact functionality.

## Proposed stages

1. Read-only per-PLN typed attribute resolution: BuildingMaterial GUID / Composite GUID, `useWith`, skin sum, reference plane and story index; abort on ambiguity.
2. Version/capability branching: existing 1.5.10 has no `structureType` in `CreateSlabs`; new upstream PR #785 adds it but is **not merged**. Prefer direct typed Create only for verified supporting schema/installed runtime; otherwise use validated favorites or controlled Create→readback→separate Modify workflow.
3. Durable single-element operation journal; record intended identity and `ATTEMPTED` *before* native calls, store native GUID and readback; never repeat an uncertain mutation.
4. Reproducible negative/positive offline tests, then **separate** owner-authorized one-off live on expendable copy. Confirm Basic 0.2m and Composite skin-derived thickness as separate scenarios.
5. Store commit+readback and structured evidence; no PR merge or main/master/APX change without approval.

## Independent audit required

Before accepting, read current `PROJECT_PLAN.json`, check `work_key` uniqueness, genuine dependency completion, existing implementation in PR #16/#20/#21 and test lineage. Confirm separate approval for modifying any test PLN. Then write `TASK_REVIEW_V1` with the registration commit and actual readback; do not claim acceptance based solely on this proposal.


## IMPORTANT 2026-10-11 anti-duplication evidence — do not admit the original scope

**This proposal is under preliminary scope challenge, NOT approved/registered.** Subsequent [APA-P50.A02.S01 anti-dup audit](../../runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md) found a **pre-existing working-code path** in `scripts/archicad_executor.py` (older `feature/working-archicad-mvp` branch, `plan_action(create_slab)` and `run` lines 230–247) performing **CreateSlabs → ModifySlabs(structureType=Basic, buildingMaterialId)**. It also found `archicad_template_builder.py:material_dependency_plan` already resolving local Building Material/Surface/Fill attributes; PR #16 already has project intent, BIM dependency graph, SceneWriter, exact project guard and SQLite journal.

**Therefore:** it is **not warranted to create a new stand-alone typed slab adapter, material resolver, BIM DAG or orchestration service** under this candidate. Independent auditor should **DEFER / REQUIRE RESCOPE** and compare existing P30.A02.S01/S02 acceptance first; if a distinct task remains, make it **integration of existing source modules plus missing strict geometry/attribute verification and durable no-replay gates**. Do not mark DUPLICATE or APPROVED as an audit decision without a separate auditor review and validated project-plan status change. No changes to user PLN/APX/main/master are implied.

**Potential minimal missing delta:** dynamic multi-component intent translation (PR16 still restricts to 1 fixed pavilion), proven per-project selected Basic/Composite IDs and skin-derived thickness, source parity, non-atomic Create→Modify crash handling, and per-element readback accepting only exact type/geometry/story/host/material. No independent general multi-floor live PASS exists yet.
