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

Source and workflow published to GitHub. CI pending; no PASS claim until 10/10 shards and final aggregate readback.
