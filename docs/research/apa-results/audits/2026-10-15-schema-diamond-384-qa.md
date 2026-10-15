# APA independent offline QA — schema limits / diamond graph / safety (2026-10-15)

## Provenance and isolation
Based on successful PR #91 head `d731d9e4a5e4a1f5d560d00f79487915343e20c2`.
Independent new branch: `audit/apa-boundaries-diamond-replies-20261015`.
No modifications to main or existing branches, no writes to Archicad PLN, APX or live model.

## Newly designed coverage — 384 cases
| Category | Unique test IDs | Production code exercised |
| --- | ---: | --- |
| Strict parameter arrays, enums, numeric bounds, regex and required keys | 80 | DynamicCommands.add_provider / prepare / validate |
| Disjoint oneOf result contracts and rejection of malformed replies | 64 | DynamicCommands.validate_result |
| Source snapshot deep-copy, hash stability and SOURCE_ONLY classification | 64 | include_source_snapshot / contract_hash / prepare |
| Four-stage diamond BIM Graph, fan-out/fan-in, checkpoints and native-write isolation | 64 | prepare_workflow / run_workflow / local handlers |
| Diamond-shaped polygons, analytic intersection and tolerance thresholds | 64 | archicad_local_modules.polygon_relations |
| Prepared workflow plan integrity under six independent mutation types | 48 | run_workflow, plan hash and permission gate |
| **TOTAL** | **384** | Imported APA modules |

Distinct scenarios from PR #90 (378) and PR #91 (288); no old tests
are run by this suite. The artificial QA handlers are passed to the
existing router and BIM Graph; no reimplementation of routing, validation,
geometry engines or execution flow is substituted.

CI workflow: `.github/workflows/apa-schema-diamond-384.yml`.
10 Windows shards use `scripts/apa_schema_diamond_qa_shard.py` for
SHA-256 partition and enforce exactly 384 distinct discovered unittest IDs.
The unchanged prior aggregator `scripts/apa_novel_aggregate.py`
verifies each shard's ID list, common discovery fingerprint, no misses
or duplicates, 384 executed and zero FAIL/ERROR/SKIP/XFAIL.

## Known limitations
This is OFFLINE_QA only; no native registration, Archicad LIVE_VERIFIED
or engineering acceptance. The eight pre-existing router defects
remain open and must not be misrepresented as fixed:
1. Empty JSON Pointer member.
2. Negative JSON Pointer list index.
3. Unauthorized GUID nested owner reference.
4. Nullable error field rejected as a failure.
5. Placeholder generation ignores schema maximum.
6. Non-atomic duplicate provider registration.
7. Ambiguous namespace/schema collision.
8. Non-absolute schema pointer accepted.

## Evidence status at publication
## Final confirmed GitHub Actions CI

- Tested commit SHA: `e9c1fec762d642f22c2d386f606fe977f6b88d09`.
- Workflow run: https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38660116941
- Final conclusion: **SUCCESS**, 11/11 jobs (10 Windows test shards + accounting).
- Discovery SHA-256: `2cd230d4a891f9ddd6653eaea828a5974477162521a6b729a30bcb8dde207000`.
- Exactly **384** discovered and executed unique tests.
- **0 failures, 0 errors, 0 skipped, 0 XFAIL, 0 unexpected successes, 0 coverage issues**.
- Individual shard counts: 37 + 43 + 31 + 39 + 31 + 43 + 44 + 33 + 41 + 42 = 384.
- Full per-test IDs, failures and aggregate JSON were uploaded as workflow artifacts; GitHub Actions accounting log independently confirmed `APA_SCHEMA_DIAMOND_EXACT_384 True`.
- Earlier 735, 378 and 288 tests are not part of this workflow.
- Updating this research report creates only a documentation commit; the stated tested SHA remains the code evidence.

Result is restricted to offline imported APA modules, not live Archicad/native SDK/APX.
