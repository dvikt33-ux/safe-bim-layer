# APA — 640 new native-domain regressions; 1922/1922 Windows offline PASS

**Status:** OFFLINE_PASS / JUNIT_VERIFIED / DRAFT_PUBLISHED / PENDING_INDEPENDENT_AUDIT.
**Research date:** 2026-10-15.
**Execution evidence:** [GitHub Actions #38728924457](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38728924457), attempt #1, final status `completed/success`.
**Exact tested code:** `84c40745693aea3a2a2467eadda3e148e755c897` in [draft PR #102](https://github.com/dvikt33-ux/safe-bim-layer/pull/102); based on PR #100 / PR #97.
**Verifier:** `APA_OFFLINE_MATRIX_RESULT_V1`; 12/12 independent shard JUnit XML + per-shard manifests; status PASS; no missing shard.

## Independent JUnit readback

| Windows shard | Executed tests | Failure | Error | Skipped | Exit |
|---:|---:|---:|---:|---:|---:|
| 0 | 161 | 0 | 0 | 0 | 0 |
| 1 | 157 | 0 | 0 | 0 | 0 |
| 2 | 160 | 0 | 0 | 0 | 0 |
| 3 | 165 | 0 | 0 | 0 | 0 |
| 4 | 165 | 0 | 0 | 0 | 0 |
| 5 | 164 | 0 | 0 | 0 | 0 |
| 6 | 157 | 0 | 0 | 0 | 0 |
| 7 | 160 | 0 | 0 | 0 | 0 |
| 8 | 160 | 0 | 0 | 0 | 0 |
| 9 | 156 | 0 | 0 | 0 | 0 |
| 10 | 159 | 0 | 0 | 0 | 0 |
| 11 | 158 | 0 | 0 | 0 | 0 |
| **TOTAL** | **1922** | **0** | **0** | **0** | **12 PASS** |

The CI aggregator reported `time=166.424` seconds, **the sum of JUnit test elapsed times across sharded jobs**, not wall-clock duration. Windows Python 3.11, 12 independently scheduled jobs and 2 pytest-xdist workers in each job (24 configured workers; do not infer sustained real-time concurrency).

The full matrix comprises **1282 pre-existing** tests (including the earlier 512 topology scenarios), plus **640 new** parametrized cases: native assembly component membership and root/parent relations (128), Generic Opening host/cut/reverse links (128), Navigator/Drawing exact identity and ambiguity (128), Slab/Roof parameter contours and invalid records (128), dynamic command ticket/scope tamper and permission controls (128). The runner's AST-based sharding weight was extended to recognize constant-range `pytest.mark.parametrize`, so these cases are balanced across CI jobs.

## Important failed attempt retained, not concealed

Initial [GitHub Actions #38728539689](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38728539689), exact test commit `5ccc9ae1cd5c11b80b1431e47cb447cc08d07378`: 1922 collected, **12 failed, 1910 passed**, 0 errors, 0 skips, 11/12 shard PASS. All 12 failures were in the **new test oracle**, which omitted the case where a single verified navigator source on `OtherViewMap` legitimately resolves a drawing reference. No product code changed. Corrected test oracle in commit `84c4074`; new full-matrix run passed. The failure remains an immutable audit artifact.

## Scope and evidence boundaries

- All new cases invoke production **offline adapters** using controlled synthetic native-shaped data; no Archicad application, SDK binary, PLN, native assembly writes, source model, or SQLite model journal was executed or changed.
- These results do **not** establish native runtime behavior for CurtainWall/Railing/Shell, physical 3D contact, a Generic Opening void BREP, navigator map freshness, or secure runtime registration. They do not upgrade LIVE_VERIFIED statuses.
- `control/PROJECT_PLAN.json`, `main`, the canonical research branch and all existing PR branches remain unchanged.
- New audit tasks are proposed in [APA-CAND-20261015-native-matrix-followups.md](../../control/proposals/APA-CAND-20261015-native-matrix-followups.md), **PENDING_AUDIT**, not admitted S-IDs.

## Task execution record (non-authoritative draft)

- STARTED: authoring a new set of 640 offline domain regressions on an isolated branch.
- CHECKED: first CI run found 12 false failures in a test oracle; triage against current implementation.
- CORRECTED: changed the test expectation; production implementation unchanged.
- VERIFIED: follow-up CI run checked all 12 JUnit groups, 1922/1922, no failures/errors/skips.
- PUBLISHED_DRAFT: this evidence receipt and corresponding registry entry in a separate draft PR.
- NEXT: independent audit before any canonical task-state or plan mutation.
