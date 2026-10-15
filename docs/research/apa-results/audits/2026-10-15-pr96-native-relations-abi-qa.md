# APA PR96 — independent offline SDK relationship/ABI QA (2026-10-15)

## Baseline and noninterference

Exact production baseline: `76ab55c1c34fa327c2c71b7615e7cde5b090f69c` (draft PR #96).
Isolated audit branch: `audit/apa-pr96-native-relations-abi-20261015`.
Changes are restricted to NEW test source, NEW shard runner, NEW aggregate,
NEW workflow and this report. No modifications to PR96 branch or main.

Only new tests run. Prior 1594 independent offline IDs are not re-executed.
All tests import production relationship conversion and BIM Graph; the native
C++ generated schema is parsed and compared with the checked-in manifest.

## Matrix: 192 new seeded cases

| Area | Cases | Independent assertions |
| --- | ---: | --- |
| Stair component parent/root and declared owner | 32 | Native error gates, self-edge suppression, deduplicated ancestry, mismatch recorded but not invented |
| Opening host, cuts and linked openings | 32 | 8 distinct positive/negative relation patterns, direction, GUID normalization and suppression of self-edges |
| Drawing ViewMap linkage and status semantics | 32 | Only explicitly known, nondeleted source views create edges; unknown links and `-1` freshness never promoted |
| Hierarchical membership merged with new binding reader | 32 | Same parent/child de-dup, native partial errors, component evidence independent of membership failure |
| Real existing BIM Graph / DependencyImpact execution | 32 | Multi-branch change propagation, source hash, checkpoint/authority, no native writes, reject unknown changed GUID |
| Actual C++ raw JSON schema vs APA manifest | 32 | Exact parity for all 5 changed SDK groups; six types of malformed parameters and preflight non-escalation |
| **Total** | **192** | No copy of graph or validation engine |

**Files**

- `tests/test_apa_pr96_native_relations_abi_qa.py`
- `scripts/apa_pr96_native_qa_shard.py`
- `scripts/apa_pr96_native_qa_aggregate.py`
- `.github/workflows/apa-pr96-relations-abi-192.yml`

CI has ten independent Windows 3.11 shards, SHA256 partitioning by actual
`unittest` test ID, a common sorted discovery hash and strict coverage
aggregation. Any FAIL, ERROR, SKIP, XFAIL or duplicate causes failure.

## Guardrails and evidence limits

- No connection to Archicad, installed APX, original PLN or quantity engine.
- Synthetic positive Opening inputs **do not** prove LIVE Generic Opening.
- Synthetic Drawing ViewMap links **do not** establish update freshness.
- C++/manifest schema equivalence **does not** prove source compilation.
- Component membership **does not** establish physical contact or resultant BREP.
- Quantity preflight is read-only; engine remains QUARANTINED.
- Native runtime facts remain from PR #96 only; this new QA cannot relabel them.

## CI result

**PENDING** until all ten Windows shards and independent aggregate finish.
Record tested exact commit, suite SHA256, counts, failure details and GitHub
Actions run URL before converting this to PASS.
