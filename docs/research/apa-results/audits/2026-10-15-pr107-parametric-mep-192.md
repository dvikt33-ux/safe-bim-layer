# APA PR107 independent offline QA — GDL, parametric edit preparation, MEP

Date: 2026-10-15. Code baseline: **PR107 exact head `9a3091638eaa1a9c72f9a08c17d02855d8419edc`**.
Source documents: `docs/APA_NATIVE_PARAMETRIC_EDIT.md`, `docs/evidence/APA_NATIVE_PARAMETRIC_BUILD.json`,
`scripts/apa_native_parameter_edit.py` and `scripts/apa_native_dependency_flow.py`.
Isolation branch: `audit/apa-pr107-parametric-mep-192-20261015` (draft PR).

## New source-anchored suite — 192 unique offline cases

| Group | Cases | Oracle |
|---|---:|---|
| GDL matrix roundtrips | 40 | Analytic row-major d1×d2 rectangular rank, typed scalar data, deep copy and existing setter ticket |
| GDL invalid edits | 32 | Duplicate parameter identity, edit locks, disabled parameters, wrong shape/type/rank, invalid values |
| Parametric assembly preparation | 32 | All 9 declared native kinds, exact type/stamp/target/changes, immutability and no execution permission |
| Parametric assembly negative validation | 32 | Inapplicable fields, non-numeric stamps, unsupported element kinds, GUID errors, nonfinite/out of range values, profile cardinality |
| MEP topology typed namespaces | 32 | RoutingElement / Segment / Node / RigidSegment / Transition ownership, direction, namespace, no physical claim |
| MEP reciprocal port evidence | 24 | Independent two-endpoint confirmation required before marking a captured connection physical |
| **Total** | **192** | Production functions imported, no reimplemented APA calculation or transport |

Test file: `tests/test_apa_pr107_parametric_mep_independent.py`.
SHA-partitioned sharder: `scripts/apa_pr107_parametric_qa_shard.py`.
Independent account aggregator: `scripts/apa_pr107_parametric_aggregate.py`.
Windows workflow: `.github/workflows/apa-pr107-parametric-mep-192.yml`.

Ten Windows shards must report 192 unique discovered and executed test IDs with no missing/duplicate/failed/error/skipped/XFAIL, plus successful independent aggregate. Each shard emits individual failed IDs and stack traces. No previously passing suites are reexecuted.

## Native acceptance boundary

- These tests evaluate *offline preparation* and synthetic MEP capture transformations.
- They **do not** execute `ModifyNativeAssemblyV1` or any native SDK write.
- Native source status stays **BUILD_PASS, LIVE_NOT_VERIFIED** until authorized exact APX readback and isolated-copy writes.
- New MEP topology positive live examples remain NOT_VERIFIED.
- No model writes, SceneWriter execution, GDL setter execution, original-PLN access, APX installation, quantity engine, or Save/Open.
- The pending specific PR104 binary authorization **does not authorize** a new PR107 APX.
- Original runtime, 409 GUID evidence, and archive hashes are inherited Work results rather than re-proven offline here.

## Evidence state

**FINAL VERIFIED CI: 192 / 192 PASS**.

- Exact tested QA head `f1ddaf0d5d9046d0a80a7d2ef058dcfeb6c8baeb`.
- Final Windows Actions: https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38762509508
- All **10/10 Windows shards** plus independent aggregator **SUCCESS (11/11 jobs)**.
- 192 independently discovered, 192 run, **0 FAIL, ERROR, SKIP, XFAIL, unexpected success, missing or duplicate IDs**.
- Sorted test-ID SHA256: `9964621d229e2fc2e4005e81ed4654298c8d0004223c6b79624694b74112f208`.
- Windows shard counts: `24+15+16+15+14+16+26+23+24+19=192`.
- GitHub CI log: `APA_PR107_PARAMETRIC_EXACT_192 True`, `APA_PR107_PARAMETRIC_SHARDS success`.
- All discovered and executed cases are fresh; no prior suites rerun.

**Initial CI incident (retain as evidence):** first run
https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38762164897
failed because synthetic GDL element GUID strings did not match the official
UUID-pattern schema. One MEP test also incorrectly expected two diagnostic
endpoint edges when a third uncaptured port was referenced one-sidedly.
Both fixture/oracle errors were corrected *only in QA*. No APA product source
or native code was changed. The final pass is based exclusively on the new
entire-suite execution at the exact tested QA SHA; the initial failed run
is not hidden or counted as a product failure.

Native MODIFY, MEP positive readback, model persistence and body/child-GUID
reconciliation remain **NOT_VERIFIED**. A green offline CI does not grant
an APX-install or SceneWriter-write permission.
