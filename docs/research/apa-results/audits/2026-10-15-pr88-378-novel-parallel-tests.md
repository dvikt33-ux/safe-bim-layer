# APA: 378 new independent offline tests on PR #88

**Date:** 2026-10-15. **Auditor:** GPT-6 independent QA. **Evidence status:** WINDOWS_CI_PASS. **Domain:** offline, no native Archicad runtime.

## Exact provenance

- **Source code baseline**: [PR #88](https://github.com/dvikt33-ux/safe-bim-layer/pull/88), verified source SHA `a444d5a6b481bfabd9c48f23c17df05c51ab0ea4`. The implementation files under test are unchanged from earlier implementation SHA `07e73f9c3f634ed93ea06be79bdf603bf0124abf`.
- **QA feature branch and PR:** `audit/apa-novel-property-matrix-20261015`, [draft PR #90](https://github.com/dvikt33-ux/safe-bim-layer/pull/90). It adds only new QA scripts, tests, workflow and this documentation. Work's PR #88 branch, main/master, user PLN and installed APX were not modified.
- **Final successful run:** [GitHub Actions #38651886778](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38651886778), `APA 378 novel property QA parallel`, Windows-hosted, Python 3.11.
- **Tested QA commit SHA:** `4b6a301dfcaa072904dbad9883b8637b58baaf3b`.
- **Suite fingerprint:** `0cbc8e24e598da64dafe06da673c5d886c46b138f942d2deed410728f9fd79d1`.
- **Result:** `discoveredTests=378; testsRun=378; failures=0; errors=0; skipped=0; expectedFailures=0; unexpectedSuccesses=0; issues=[]`. All ten shards and aggregate completed successfully.

## Novel test matrix (378 independent fixture IDs)

| Group | Cases | Independent oracle or invariant |
| --- | ---: | --- |
| Dependency-impact DAG variants | 80 | Independently computed graph reachability, coverage of affected nodes, edge precedence of topological order |
| Cyclic dependency variants | 32 | Found cycle witness edges must be present in synthetic source graph; execution remains blocked |
| Rectangle polygon relations | 60 | Analytic rectangle area/perimeter, axis-aligned overlap formula, boundary-touch classification |
| Polygon hole cases | 24 | Exact area `W² − hole²`, combined inner/outer perimeter, disjoint polygon fully inside hole |
| CP-SAT feasible integer assignments | 48 | Enumeration of all permissible slot assignments for 3–4 tasks; exact global minimum/capacity agreement |
| CP-SAT infeasible constraints | 24 | 3–5 tasks with combined capacity 2 must report infeasibility, no fake assignment/objective |
| Local JSON Schema adversarial inputs | 54 | Nine distinct local entry contracts × six malformed parameter constructions; provider validates before invocation |
| Valid local data-domain calls prepared | 9 | Nine entry contracts prepared without granting native writes or pretending local computation is Archicad |
| Prepared ticket tampering probes | 27 | Nine local entries × three modifications: permission, payload and catalog hash — reject drift |
| Newly added SDK source-only statuses | 20 | Five SDK group contracts × four distinct source/runtime identity checks; no false LIVE or CALLABLE promotion |
| **TOTAL** | **378** | Deterministic, independently audited before use |

The CI exercises the **actual imported** modules `archicad_local_modules.py`, `archicad_dynamic_commands.py` and the APA orchestrator's functional-module catalog. The 48 CP-SAT cases compare returned optima to independently computed brute-force minima; do not count solver-internal validation as an independent oracle. The 60 rectangles and 24 hole cases compare Shapely results with analytical formulas.

All source fixtures are new; **the previous 735 individual test IDs are not invoked by this workflow**. The dedicated shard loader selects only `tests/test_archicad_novel_combinatorial_qa.py`.

## Parallel execution and exact coverage

Ten Windows GitHub-hosted runners execute nonoverlapping SHA-256 partitions:

`0:33, 1:45, 2:41, 3:48, 4:32, 5:37, 6:44, 7:23, 8:36, 9:39`.

The final aggregator collected **10/10 reports**, verified a single shared discovery hash, 378 distinct IDs with no duplicates, all ID assignments represented, and zero failures. It required all runners successful before declaring the workflow successful. Real output:

```text
APA_PARALLEL_AGGREGATE:
  shardsExpected=10; shardsFound=10; discoveredTests=378; testsRun=378
  failures=0; errors=0; skipped=0; expectedFailures=0
  unexpectedSuccesses=0; issues=[]
NOVEL_QA_SHARDS success
```

No native Archicad API was invoked and no user's installed APX/PLN/Windows development files were accessed. Dependencies were installed on isolated GitHub Windows runners.

## Diagnostic notes from exploratory runs

Earlier runs [#38651671819](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38651671819) and [#38651793664](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38651793664) exposed **test-harness expectation mismatches**, not validated module implementation failures:

1. A ticket-mutability test originally expected only `ValueError`/`KeyError` when a JSON Schema failure correctly raised `jsonschema.ValidationError`. The assertion was corrected to accept the correct validation exception class.
2. The SDK group manifest carries `BUILD_CANDIDATE_NOT_RUNTIME_REGISTERED`, but `DynamicCommands.add_provider` returns `SOURCE_CONTRACT_NOT_RUNTIME_PROBED` in the runtime catalog row. The test now checks the **observed registry value**, which accurately does not imply runtime registration. This distinction is a metadata traceability observation, **not** LIVE pass or a confirmed functional SDK defect.

These two causes were corrected **in new QA test code only** before final successful run. No Work production code was changed. Earlier failed runs are not treated as PASS.

## Boundaries and follow-up

- **Verified offline:** randomized deterministic DAG/cycle invariants, axis-aligned polygon geometry/holes, synthetic integer assignment optima and impossibility, invalid JSON Schema inputs, local module privilege separation, source-only SDK catalog status.
- **Not verified:** native Archicad/PLN write operations; SDK APX runtime registration or actual SDK call return; raw C++ DevKit build reproducibility on GitHub, third-party vendor APX private ABI; engineering/normative fitness; arbitrary polygon/3D topology; full-repository regression beyond the dedicated novel suite.
- **Still open (not exercised as resolved):** the eight XFAIL findings from [PR #87](https://github.com/dvikt33-ux/safe-bim-layer/pull/87) and provider namespace/atomicity concerns. This newly successful suite does **not** transform those existing defects into PASS.
- **Recommended next separate test groups:** property generators for complex $ref / recursive schema and result-binding DAG, IFC schema-level synthetic files, provider manifest permutations and collisions, integer solver overflow/timeout handling. Keep each focused and source-grounded; do not relabel catalog counts as LIVE.

## Reproduce

Run only the new suite on Windows with project offline dependencies:

```powershell
python -m unittest discover -s tests -p test_archicad_novel_combinatorial_qa.py -v
```

For the exact parallel method use `.github/workflows/apa-novel-combinatorial-parallel.yml` in PR #90: ten shards invoke `scripts/apa_novel_unittest_shard.py`; `scripts/apa_novel_aggregate.py` validates coverage. These scripts import no Archicad runtime processes and leave Work's existing development context untouched.

**Publication requirement:** full source, workflow, SHA and CI are GitHub-visible. Canonical plan changes are not made by the independent QA branch: accepted task changes require the established control-plane CAS/lease.
