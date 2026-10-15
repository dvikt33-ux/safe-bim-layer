# APA mass offline validation — 2026-10-15

Status: **RUN_REQUESTED; RESULTS_NOT_YET_VERIFIED**.

Execution head: PR #97 source snapshot `8f134001ca0e3250eda587db61ac01dbd6357326`.
Test mode: isolated GitHub Actions Windows Python 3.11, 12 independent shards, 2 pytest-xdist workers per shard, complete `tests/test_*.py` plus `scripts/test_*.py`. Actual concurrency depends on GitHub runners, not the matrix size.

New tests: 256 distinct deterministic DAGs of five nodes and 256 forced-cycle variants; each case checks production `archicad_bim_graph._topo`, dependency order/purity/determinism and cycle rejection. These source-level checks are **not** live geometry tests. Additional existing integration and schema contract cases are sharded by AST test count, with an explicit weight for parametric topology tests.

Evidence standard: `junit.xml` plus `manifest.json` per shard, aggregate `apa-offline-summary.json`; count only reported executed cases. One missing job or any failed case makes the aggregate **FAIL_OR_INCOMPLETE**. No model, PLN, add-on or Archicad process is modified.

Task register additions (proposed pending audit):
- APA-OFFLINE-251015-01: compare synthetic producer/consumer references against live SDK identity shapes without using write APIs.
- APA-OFFLINE-251015-02: add native assembly source contract mutation checks (CW, Railing, Shell) with SDK Windows build artifact evidence, keeping native runtime validation separate.
- APA-OFFLINE-251015-03: isolate slow/flaky tests by named fixture and JUnit history, without suppressing failures.
- APA-OFFLINE-251015-04: add positive Generic Opening/CurtainWall/Railing/Shell dependent graph snapshots into regression fixtures.

After CI, replace RUN_REQUESTED with evidence-linked run counts and outcomes; until then do not claim passing tests.
