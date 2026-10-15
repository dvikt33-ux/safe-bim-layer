# APA — native contract + JSON Pointer hardening, verified Windows offline 2338 / 2338

Date: **2026-10-15**. Status: **OFFLINE_PASS / JUNIT_VERIFIED / PUBLISHED_IN_DRAFT / PENDING_INDEPENDENT_AUDIT**.

- Full verified execution: [GitHub Actions #38736451749](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38736451749): **completed/success**, test code commit `0e57dfd888156b98148b7e6de6623e1e393de37c`; final verification job success.
- Source/repair in [draft PR #105](https://github.com/dvikt33-ux/safe-bim-layer/pull/105), isolated branch `ci/apa-offline-parallel-contract-security-20261015`, based on previously verified [PR #102](https://github.com/dvikt33-ux/safe-bim-layer/pull/102).
- Initial failing proof: [GitHub Actions #38736049083](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38736049083), baseline commit `2b81816ae97fbec04b9968904dcc64084130adbc`: **2322 collected, 32 failed, 2290 passed, 0 errors, 0 skipped**, 11/12 shard success, aggregate FAILURE. This defect is not silently removed from the evidence trail.

## Independently parsed JUnit result

`APA_OFFLINE_MATRIX_RESULT_V1` aggregated **12 per-shard JUnit XMLs + manifests**, no missing shard, all exit code 0, all shard statuses PASS. Full run counts: **tests=2338, failures=0, errors=0, skipped=0**; sum of JUnit `time=194.896` seconds (not CI wall time).

| Shard | JUnit tests | Failures | Errors | Skipped | Exit |
|---:|---:|---:|---:|---:|---:|
| 0 | 192 | 0 | 0 | 0 | 0 |
| 1 | 195 | 0 | 0 | 0 | 0 |
| 2 | 196 | 0 | 0 | 0 | 0 |
| 3 | 195 | 0 | 0 | 0 | 0 |
| 4 | 196 | 0 | 0 | 0 | 0 |
| 5 | 195 | 0 | 0 | 0 | 0 |
| 6 | 194 | 0 | 0 | 0 | 0 |
| 7 | 199 | 0 | 0 | 0 | 0 |
| 8 | 188 | 0 | 0 | 0 | 0 |
| 9 | 191 | 0 | 0 | 0 | 0 |
| 10 | 206 | 0 | 0 | 0 | 0 |
| 11 | 191 | 0 | 0 | 0 | 0 |
| **Total** | **2338** | **0** | **0** | **0** | **12 success** |

Windows Python 3.11, 12 independent jobs, 2 xdist workers per job (24 configured; runner capacity is not asserted as simultaneous execution). This is **416 new cases** plus **1922 previously verified** offline cases.

## New coverage, nonduplicating domains

- **192** source-pinned SDK input contract tests against 5 distinct source-declared Native commands, positive + malformed boundaries, with `nativeWritePermission=False`.
- **128** local-only typed workflow JSON Pointer cases: **64 positive escaped-token result references**, **64 malformed refs**.
- **16** direct runtime JSON Pointer lookup regressions (independent of the planning stage).
- **64** combined dependency capture tests joining Opening, hierarchical components, Navigator and Drawing, including cycle detection and namespace isolation.
- **16** checked-in native Shell C++ source-only serialization gates (Extruded/Revolved/Ruled, contour bound/edge/flags). **No SDK binary compilation or shell geometry live claim.**

## Actual code defect found and fixed

The original `DynamicCommands._schema_at` stripped slashes without requiring a leading `/`, accepted unescaped or invalid `~` sequences, and accepted noncanonical array indexes such as `00`. In concrete contract planning, 32 negative test inputs that should have failed were incorrectly accepted; this was reproducible on GitHub Actions JUnit. The **existing** `scripts/archicad_dynamic_commands.py` was patched, not replaced: common RFC 6901 token validation now rejects relative pointer strings and invalid escapes, enforces canonical array indexes at the array node, and applies the same checks in the result resolver `_result_at`. The successful full run confirms the tested cases, not universal safety of all possible inputs.

The initial failures were genuine **production-adapter contract validation deficiencies**, not merely a test-oracle mismatch. No new command executor, native geometry engine, automatic write or scheduler was introduced.

## Authorization and status boundary

The entire CI run is synthetic offline / source review. No Archicad process, Windows user PLN, APX native build, element creation or modification, save, live SDK call, or physical BREP verification. The result **does not** upgrade LIVE_PASS. No changes to main, canonical research branch, original PR #97/#100/#101/#102 or original author PLN. The authoritative `control/PROJECT_PLAN.json` was not edited. Research proposals remain **PENDING_AUDIT**.

### Run registration timeline

1. `STARTED` — isolated branch, candidate tests registered by new code commit.
2. `FAILED_IDENTIFIED` — 32 incorrect accepts in typed JSON Pointer planning, exact first CI artifact retained.
3. `FIXED` — existing adapter patched with shared validation; regression suite extended to runtime lookup.
4. `VERIFIED` — full second CI run, 2338 / 2338, JUnit and 12 manifests.
5. `DRAFT_PUBLISHED` — evidence and audit candidates are present in research branch; no controller DONE_PUBLISHED promotion without independent audit.
