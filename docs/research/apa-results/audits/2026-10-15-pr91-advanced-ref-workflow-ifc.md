# APA independent advanced QA — PR 91 (2026-10-15)

## Scope and provenance

Independent continuation of PR 90's 378-case matrix, based on head SHA
90ab6800a797bd1454756e9b2a425e43c3053ab2.
Branch: audit/apa-advanced-ref-workflow-ifc-20261015.
Draft PR: https://github.com/dvikt33-ux/safe-bim-layer/pull/91
Neither main nor older PR branches were changed.

The new test_archicad_advanced_ref_workflow_ifc_qa.py file generates
288 distinct unittest identities:

| Area | Cases | Primary code under test |
| --- | ---: | --- |
| Three-level namespaced JSON Schema refs | 64 | DynamicCommands.add_provider, prepare, validate |
| Escaped JSON Pointer and schema walk | 48 | DynamicCommands._schema_at, _result_at |
| Three-step dependent local workflows | 48 | prepare_workflow, run_workflow, BIM Graph |
| APX provider isolation | 48 | add_provider, contract_hash, prepare |
| Synthetic IFC4 structures | 48 | archicad_local_modules.ifc_select, ifc_geometry, _ifc |
| Rejected malformed source result | 32 | result schema, fail-closed chained dispatch |
| TOTAL | 288 | Actual APA imports; not separate algorithm copies |

The synthetic IFC cases construct temporary IFC4 models containing two walls
and one door, plus invalid input path checks. Missing geometric representations
are not reported as engineering or Archicad-native geometry acceptance.
There are no writes to user PLN or original IFC files.

## Parallel execution and evidence

Workflow: .github/workflows/apa-advanced-ref-workflow-ifc.yml
Runner: scripts/apa_advanced_qa_shard.py
Aggregator: scripts/apa_novel_aggregate.py (reused unchanged from PR 90)

10 Windows shards discover ONLY the 288 new tests, reject a mismatch or duplicate
test identities, and partition each test ID deterministically via SHA-256.
Each shard uploads explicit test IDs, failures, errors and tracebacks.
Aggregation independently checks no missing or overlapping tests, consistent
discovery hash, 288 executions, and zero FAIL/ERROR/SKIP/XFAIL/unexpected success.

Previous 735 and 378 test suites are not part of this new workflow.
Eight existing router defects remain open until explicitly repaired.

## SHA / initial run

Tests: f0abe510159df3dcdb07dae2ee9adce5b55d5729
Runner: c2117090c07dc33081f694efc6fd04cb30cb225c
Workflow: f87ae6f17e3b48d46707ee8d837a3f23f26caaa8
Initial Actions run: 38659200570
Status at creation: QUEUED, no PASS evidence yet.

This is OFFLINE_QA and not APX installed, native SDK registration,
Archicad LIVE_VERIFIED, or user project acceptance.
Report new failures without silently marking them expected.
Work-side functional expansion must continue independently.
