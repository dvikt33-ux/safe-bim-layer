# APA functional module manifest consistency — follow-up offline check

- Date: 2026-10-15.
- Audited functional source SHA: `a444d5a6b481bfabd9c48f23c17df05c51ab0ea4` from [PR #88](https://github.com/dvikt33-ux/safe-bim-layer/pull/88).
- Mode: GitHub file readback + independent structural validations, **no Archicad or local PLN/APX**, no compilation and no invocation of proprietary APX commands.
- Files compared: `schemas/accelerator/functional-modules.json`, `schemas/accelerator/functional-module-coverage.json`, `schemas/accelerator/mass-capabilities/operation-effects.json`, `schemas/accelerator/mass-capabilities/providers.json`.
- **14/14 structural consistency checks PASS; 0 FAIL.** These metadata checks are not Python unittest runs or proof of runtime registration.

| # | Verified invariant | Result |
|---:|---|---|
| 1 | Nine local module command records | PASS |
| 2 | Five new TapirCommand SDK contracts + one DevKit AddOnCommandTest contract | PASS |
| 3 | 368 native/official/source + 9 local = 377 prepared | PASS |
| 4 | 368 native/source - 337 prior compatible = 31 still requiring runtime | PASS |
| 5 | Six novel analytical capabilities + three existing APA utilities = nine local | PASS |
| 6 | Every local command has a dependency mapping | PASS |
| 7 | All local dependency mappings are string arrays | PASS |
| 8 | Every local command has both input and result schema | PASS |
| 9 | Every SDK/DevKit candidate contract has both input and result schema | PASS |
| 10 | Native and local implementation digest fields have SHA-256 shape | PASS |
| 11 | Existing operation effect manifest retains 337 records | PASS |
| 12 | Provider inventory contains 33 uniquely named records | PASS |
| 13 | Coverage correctly counts five new SDK build commands and one DevKit reuse | PASS |
| 14 | No independently callable non-Tapir vendor APX commands are falsely claimed | PASS |

**Important limitations:** Digest string format is not cryptographic recomputation of current source/binary bytes. Presence of a JSON Schema object is not proof the schema is semantically complete or conformant with a real native response. All five SDK commands plus one DevKit candidate are still only BUILD_PASS until their registration and read-only invocation are verified in Archicad. The nine local entries were previously shown LOCAL_CALLABLE_VERIFIED on archived evidence; this check only covers ledger consistency.

Parallel full-repo unit/Knowledge Graph/statics on immediately preceding code (documentation-only later change) were completed in [run 38649516535](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38649516535): 735 unique unittest IDs, 727 regular PASS, 8 known XFAIL; upstream KG 102/102. This follow-up does **not** re-run those 735 tests.

No main, PR #88 feature branch, or user local files changed.
