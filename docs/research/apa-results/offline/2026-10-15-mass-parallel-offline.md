# APA mass offline validation — 2026-10-15

Status: **OFFLINE_PASS; JUNIT_VERIFIED**.

Run: https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38726439729
Head: `4f3b6e43c7c748f9617d6a38da9be7bd988f4660`
Result: **1282/1282 PASS; 0 failures, 0 errors, 0 skipped; 12/12 shard PASS**, exactly **512 new** matrix cases plus **770 existing** offline cases. Evidence: GitHub Actions run #38726439729, `verify` job JUnit aggregation + `apa-offline-mass-summary` artifact.

CI bootstrap notes: runs #1 and #2 failed before test collection because `actions/setup-python` could not locate root `requirements.txt` for pip cache. Corrected `cache-dependency-path` in workflow; run #3 **PASS**. No live Archicad assertions.

Execution head: PR #97 source snapshot `8f134001ca0e3250eda587db61ac01dbd6357326`.
Test mode: isolated GitHub Actions Windows Python 3.11, 12 independent shards, 2 pytest-xdist workers per shard, complete `tests/test_*.py` plus `scripts/test_*.py`. Actual concurrency depends on GitHub runners, not the matrix size.

New tests: 256 distinct deterministic DAGs of five nodes and 256 forced-cycle variants; each case checks production `archicad_bim_graph._topo`, dependency order/purity/determinism and cycle rejection. These source-level checks are **not** live geometry tests. Additional existing integration and schema contract cases are sharded by AST test count, with an explicit weight for parametric topology tests.

Evidence standard: `junit.xml` plus `manifest.json` per shard, aggregate `apa-offline-summary.json`; count only reported executed cases. One missing job or any failed case makes the aggregate **FAIL_OR_INCOMPLETE**. No model, PLN, add-on or Archicad process is modified.

Task register additions (proposed pending audit):
- APA-OFFLINE-251015-01: compare synthetic producer/consumer references against live SDK identity shapes without using write APIs.
- APA-OFFLINE-251015-02: add native assembly source contract mutation checks (CW, Railing, Shell) with SDK Windows build artifact evidence, keeping native runtime validation separate.
- APA-OFFLINE-251015-03: isolate slow/flaky tests by named fixture and JUnit history, without suppressing failures.
- APA-OFFLINE-251015-04: add positive Generic Opening/CurtainWall/Railing/Shell dependent graph snapshots into regression fixtures.

Executed proof: the verifier parsed 12 JUnit XML reports and all 12 per-shard manifests, rejected missing shards by construction, and produced aggregate `PASS`. This is only offline validation; native SDK create functions still require separate runtime evaluation.
