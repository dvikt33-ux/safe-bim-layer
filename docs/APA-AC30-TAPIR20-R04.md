# APA R04 / Archicad 30 / Tapir 2.0: isolated source integration

Baseline commit: `4a0a79d3e921104fbac2830c681caf7877e03334`.
Working branch: `integration/ac30-tapir20-20261115`.
This is **source-only**, not an installed Windows release, approved model writer, or an MCP deployment.
The legacy Archicad 29 modules, original R03 worktree, installed MCP release, active PLN, and GitHub branches are not changed.

## New APA command routes

- `apa.py ac30-native-read --profile PROFILE --elements ELEMENTS --output NEW_RECEIPT`:
  strict exact project, baseline backup, APX SHA256, AC30/Tapir version, port, and homogeneous-by-type quantification. Each batch is checked against the per-element independent request. A failed batch falls back only to verified independent quantities; parity drift is blocked. No mutation API is reachable.
- `apa.py ac30-wall-preflight --profile PROFILE --wall GUID --group GUID --expected-height 3.2 --new-height 3.6 --output NEW_RECEIPT`:
  read-only preflight. Detects grouping, exact baseline wall height and whether Suspend Groups is required. It does NOT call ModifyWalls or change group mode; no write authorization.
- `apa.py ac30-normalize-changes --diff CHANGE_RECEIPT --readback CREATED_READBACK --final FINAL --intent CREATE_INTENT --create-response CREATE_RESPONSE --output NEW_RECEIPT`:
  offline root-vs-change-event classification. Requires corroborating source and resulting GUID. No inferred extra roots.

## Actual checks performed 2026-11-15

Evidence root:
`D:\AI\APA-AC30\evidence\ac30-r04-source-integration-20261115`.

- Live through updated R04 `apa.py`: `AC30_TAPIR20_R04_SOURCE_READ_PASS` on `APA_Change_Watch_Test.pln`, port 19725. 8 Wall, 2 Slab, 2 Roof; homogeneous batches matched independent results exactly. `ac30-native-read-receipt.json`.
- Live through updated R04 `apa.py`: `AC30_GROUPED_WALL_PREFLIGHT_PASS` for wall `C8EBF5F0-BE73-4D3B-908C-14CD75132CB6` and group `D609571F-E769-439F-B92B-8AECD1E2AC7F`; current Suspend Groups false and must be enabled for any future authorized modification. `ac30-grouped-wall-preflight.json`.
- Source-only replay of historical create watcher: 214 new GUID events, exactly 1 proven `Railing` root, 213 UNRESOLVED. **Actual historical command** `CreateNativeAssemblyV1` with `args.kind = Railing`; the independent create response reported `nativeModelWrites = 1` and matched GUID. `ac30-change-normalization-v2.json`.
- Early source-only report `ac30-change-normalization.json` is superseded; it incorrectly labelled historical command `CreateRailings` without checking source intent/response. Keep for audit, do not cite it as authoritative.
- New source tests `tests/test_apa_ac30_*.py`: 23/23 PASS, exitCode 0.
- The grouped-wall **actual write/restore** was separately tested earlier with `fix_grouped_modifywalls.py` on the test copy. This source integration adds only its validated read-only preflight; it does not expose a write path.

## Controls and remaining acceptance

- All new `apa.py` routes are isolated from the existing `mcp-control` routes, which are still bound to R03 and port 19723. The tested live AC30 project is on port 19725.
- The installed MCP release is still `27bb539e8fdcfdd207d23b50e8bb59f1ee27c774` and target `test-house` has `writeEnabled:false` at verification.
- No installed APA/Archicad Add-On binary was replaced. No model save was executed by the new read-only routes.
- Do not deploy, push, merge, or install until release manifest integration, full regression test suite, code review, independent acceptance, and exact AC30 MCP profile are prepared.
- 213 GUIDs are NOT proven subelements and remain unresolved, pending classification against a live source with independently verified ownership.

## 2026-11-15: R05 forward-port and dedicated read-only AC30 MCP

- Fresh upstream Work PR #213 pinned and inspected: `2423ad561f1c4a59ca61292e25474060914c9186`. This introduces the R05 1NF ceramic partition design, wall coordination and a detail review route. The source integration was cleanly rebased from `ff21a40f36246085b1884a4c6b2d93826b0648d5` onto this revision. No established AC29 code or installed MCP profile was changed.
- Added `apa.py ac30-mcp --profile PINNED_PROFILE --elements PINNED_INVENTORY` by isolating a new `scripts/apa_ac30_mcp.py` transport from the legacy `mcp-control`. By default the server runs over stdio. It exposes one read-only tool `apa_ac30_read` with only `status` and `quantities` modes, no create/modify/delete/save tools. The process pins operator profile and GUID inventory SHA256 at startup and rechecks inputs and exact PLN/backup/add-on hashes, versions, and project identity for each call. Maximum 64 elements for a single MCP inventory; all quantities are homogeneous by type and checked against independent results.
- Genuine MCP Python SDK client test using the installed isolated Python 3.11.9 environment passed, status `AC30_MCP_REAL_STDIO_PASS`. 12 elements (8 Wall, 2 Slab, 2 Roof), all typed batch results exactly match independent output; baseline saved PLN, backup and installed APX SHA256 unchanged after the test. Evidence: `D:\AI\APA-AC30\evidence\ac30-r04-source-integration-20261115\live-mcp-acceptance-20261115.json`.
- New AC30 unit regressions: `31/31 PASS`. Source Work R05 native-plan tests: `21/21 PASS`; R05 project design: `20/20 PASS`. Legacy MCP transport tests: `2/2 PASS`. A real offline `apa.py plan` on R05's `r05-1nf-partition-design.json` created one `variant-a` with 9 BIM Graph operations, `DESIGN_VARIANTS_REVIEWED`, `DESIGN_CHECKS_REVIEWABLE` and `executionPermission=false`.
- This does **not** imply a full release acceptance. No long-running AC30 MCP deployment or remote connector was installed; the temporary stdio MCP process terminated after the client test. The optional loopback HTTP mode passed a disposable one-shot test but has not been production-qualified. Existing stable MCP stays on release `27bb539e8fdcfdd207d23b50e8bb59f1ee27c774`, with only read-disabled-for-write test target as last checked.
- A one-shot genuine MCP SDK client also passed the separate localhost streamable-HTTP transport on `127.0.0.1:18888`, status `AC30_MCP_REAL_LOOPBACK_HTTP_PASS`. It used only the `apa_ac30_read` tool, checked 12 elements with independent quantity parity and verified the PLN/backup/APX hashes. The temporary process exited and TCP port 18888 was checked CLOSED. Receipt: `D:\AI\APA-AC30\evidence\ac30-r04-source-integration-20261115\live-mcp-http-acceptance-20261115.json`.
- Offline unified APA entrypoint regression also passed `12/12`; targeted total is `31 + 21 + 20 + 2 + 12 = 86/86 PASS` (five individually executed suites). No full-repository regression/CI claim. `apa.py plan` R05 smoke result is in `r05-plan-smoke-20261115.json` in the evidence directory.
- Remaining: run full R05 CI, review release manifest/packaging, define a protected independent persistent AC30 deployment with credentials/access control and verified restart/reconnect, and explicitly approve any external connector or BIM write pathway. Neither transport's one-shot pass grants production authorization.
