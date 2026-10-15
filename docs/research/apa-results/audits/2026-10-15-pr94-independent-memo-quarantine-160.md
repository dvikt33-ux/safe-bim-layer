# APA independent QA after PR #94 — unique memo / crash firewall / provider alias review

**Date:** 2026-10-15. **Branch:** `audit/apa-pr94-memo-quarantine-qa-20261015`.
**Baseline:** exact PR #94 implementation SHA `d758957f97cf1e347262da6f7e7b325ae6609ea4`.
**Audit strategy:** uniquely identify and exercise new PR94 behavior, not rerun the prior 1434 offline cases.

## New independent matrix (160 unique deterministic tests)

| Domain | Cases | Independent oracle |
| --- | ---: | --- |
| Native Roof/Slab parameter memos, including two disjoint holes and arbitrary winding/story | 40 | Analytic 2D polygon area & perimeter, source immutability, GUID/story/type retention |
| Malformed memo partial-batch isolation | 32 | Sixteen distinct failure classes, with a healthy second item retained |
| Cross-story 2D intersections & affine transformations | 32 | Independent overlap area and squared/linear scaling; assert 2D-only, NOT_VERIFIED for 3D |
| Provider alias collision + atomicity | 24 | Two namespace/schema alias paths, contract-hash stability and failed-batch rollback |
| Native quantity crash quarantine | 24 | Source-added and stock-name variants; no access to malicious transport; prepared tickets remain non-writing |
| C++/Drawing structural safety gates | 8 | Quantity refusal avoids engine calls; Drawing status/content-box error fields present and guarded |
| **Total** | **160** | Real imported APA functions and source declarations; no fake LIVE acceptance |

## Execution environment

- Test source `tests/test_apa_pr94_memo_quarantine_independent.py`
- Sharder `scripts/apa_pr94_memo_safety_shard.py`
- Aggregator `scripts/apa_pr94_memo_aggregate.py`
- 10 Windows shards + strict accounting in `.github/workflows/apa-pr94-memo-quarantine-160.yml`
- No duplicate IDs, skip, XFAIL or count-only PASS accepted by the workflow.
- No original Archicad process, PLN, unsafe quantity SDK invocation, installer, native model writes, or network access by tests.
- The product's runtime quantity crash and Drawing auxiliary query failures remain **UNRESOLVED**; no source-only / mocked / offline read is promoted to native verification.
- Source manifests and captured reports in PR #94 are prior Work evidence; this suite does not independently re-execute any current Archicad native command.

## Current status

**FINAL RESULT — 160/160 PASS (verified)**.

- Tested suite and workflow commit: `adc5f83acdeb6213c32b48369bbac897d370a395`.
- Final Windows Actions run: https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38666288641
- 10/10 Windows shards plus aggregate = **11/11 SUCCESS**.
- Deterministic SHA256 over all discovered test IDs: `ca88d354a313f212de27eef48f331fd70e551ea3c480ac2105ca5b9d184d8242`.
- 160 unique tests discovered and executed, **0 failures, 0 errors, 0 skips, 0 expected failures, 0 unexpected successes, 0 missing or duplicate IDs**.
- Per-shard test counts: 18 + 16 + 16 + 20 + 15 + 17 + 18 + 16 + 13 + 11 = 160.
- Aggregator logged `APA_PR94_MEMO_EXACT_160 True` and `APA_PR94_MEMO_SHARDS success`.

**Audit trail of initial run:** GitHub Actions run `38666158037` initially failed because QA asserted the quarantine marker contained the literal word `CRASH`, whereas the actual marker is `AC29_QUANTITY_ENGINE_ACCESS_VIOLATION_ROOT_CAUSE_NOT_VERIFIED_NO_REPLAY`. The independent *test oracle* was corrected to require `ACCESS_VIOLATION`; APA product code was **not** modified. The initial failed run has not been hidden or called a product defect. Only the subsequent full rerun at the tested commit earns PASS.

The eight historical router defects require individual re-verification against PR #94, which specifically repairs two registration defects. Those previously repaired issues should not automatically remain classified open on the newer branch. The six remaining historical cases were not retested in this suite.

**Limits:** no Archicad LIVE, no debugger isolation of native quantity access violation, no Drawing status/content-box native success, no resultant BREP readback. Documentation-only amendments after the tested commit do not alter test code.
