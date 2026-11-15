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
