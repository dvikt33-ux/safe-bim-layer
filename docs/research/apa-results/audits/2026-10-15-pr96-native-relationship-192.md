# PR96 — independent offline QA of captured native relationships

Date: 2026-10-15.

## Audited implementation

- Repository: `dvikt33-ux/safe-bim-layer`
- Source commit: `76ab55c1c34fa327c2c71b7615e7cde5b090f69c` (draft PR #96)
- Work package: `APA-P70.A11.S03`, canonical plan revision **169**, still **PARTIAL**.
- New QA branch: `audit/apa-pr96-native-dependency-qa-20261015`.
- Source under test: `scripts/apa_native_dependency_flow.py` and the already installed
  `archicad_project_accelerator` / `archicad_local_modules` / existing BIM Graph APIs.

This suite is intentionally independent of the Work's five focused contract tests.
No older 735, 378, 288, 384, 384, or 160 cases are reexecuted.

## 192 new deterministic, source-anchored cases

| Target | Tests | Oracle |
| --- | ---: | --- |
| Hierarchical Stair membership | 32 | Independent expected parent-child pairs, dedup, invalid GUID and native error omission |
| Parent/root component SDK result gates | 32 | Respect exact native success codes, suppress self-loops, compare declared owner without inferring edges |
| Opening connected and cut relationships | 32 | Independent expected directed edges, host resolved flag, overlapping cut-host evidence, dedup |
| Drawing ViewMap source links | 32 | Exact captured view set, deleted status flag, unknown source refusal and updateStatus=-1 not treated as freshness |
| Mixed component/opening/drawing permutation | 32 | Same sorted node/edge graph after reordered input, no inferred cross-type connection |
| Actual read-only APA BIM Graph dispatch | 32 | Run production `apa_native_dependency_flow.run` into local `DependencyImpact`, compare affected/topological results, hash, check no writes and fail-closed unknown changed IDs |
| **Total** | **192** | Does not invent native command or physical contact |

QA code: `tests/test_apa_pr96_native_relationships_independent.py`.
Sharder: `scripts/apa_pr96_dependency_qa_shard.py`.
Aggregator: `scripts/apa_pr96_dependency_aggregate.py`.
CI: `.github/workflows/apa-pr96-native-dependency-192.yml`.

Windows CI divides the exact new unittest identifiers into 10 immutable SHA256
partitions and verifies exactly 192 discoveries, 192 executions, no duplicate
IDs or missing test, no FAIL/ERROR/SKIP/XFAIL, and all shards SUCCESS. Full
JSON run artifacts preserve individual failing test IDs and traces.

## Evidence boundaries

- OFFLINE_QA only. This does not rerun PR96 native Archicad readbacks, and
  does not elevate missing Shell / Generic Opening / Railing / Curtain Wall
  positive samples to LIVE_VERIFIED.
- Host/cut and hierarchical relationships do not prove physical contact.
- Drawing `updateStatus=-1` does not prove that the drawing is current.
- `GetNativeElementQuantitiesV1` remains QUARANTINED and is never invoked.
- No installation, network call, PLN mutation, native APX state change or
  user data is involved.

## Status

### Final independently verified result: **192 / 192 PASS**

- Exact tested QA source/workflow SHA: `4facf8ce7713013bbbd1d0128e453c53fb4eda9b`.
- Original source being audited: PR96 SHA `76ab55c1c34fa327c2c71b7615e7cde5b090f69c`.
- CI run: https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38705275566
- 10/10 Windows test shards **SUCCESS**, independent reconciliation **SUCCESS**, **11/11 jobs**.
- Sorted unique test ID SHA256: `9629a8a0d8fceadc654ae00c1813804ca9fac11b03e8d903c9c867ddb761901e`.
- 192 discovered/192 run, **0 FAIL, ERROR, SKIP, XFAIL, unexpected success, duplicate or missing ID**.
- Shard counts: `20 + 14 + 21 + 25 + 18 + 13 + 23 + 22 + 22 + 14 = 192`.
- Aggregator log: `APA_PR96_DEPENDENCY_EXACT_192 True`,
  `APA_PR96_DEPENDENCY_SHARDS success`.
- The aggregate and each shard publish inspectable JSON Actions artifacts.

These facts apply strictly to the tested QA code SHA. This documentation
update is report-only and cannot be interpreted as a second runtime test.
The eight and two older router defects are not automatically reclassified;
only actual PR94 and PR96 contracts touched by these tests are in scope.
