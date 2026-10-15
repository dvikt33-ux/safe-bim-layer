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

GitHub source published; Windows CI **PENDING**. This document must not report a PASS until final ten-shard and full-coverage aggregate readback.
