# Archicad 29 Template — preflight launcher status gate correction

Date: 2026-10-26
Target: Archicad 29.2.1 build 5101, RU/SBIM candidate template
Branch: `feature/working-archicad-mvp`

## Confirmed blocker in the previous script

`scripts/run_archicad_template_live.ps1` accepts a step only when the JSON result
has `status == "PASS"`. Previously both:

- `inspect` -> `live_inventory`
- `plan` -> `plan_summary`

returned informative JSON but did not set `status`. Therefore a passing read-only
preflight could still fail in the PowerShell runner.

A second issue: some explicit `BLOCKED_*` results in direct Python CLI execution
did not produce a nonzero exit code.

## Corrections

1. `live_inventory` now returns `status = PASS` only after required inventory
   calls return without recorded exceptions; any attribute/unit/geolocation/story
   read exception returns `BLOCKED_INVENTORY`, accompanied by `readErrors`.
2. `plan_summary` returns `PASS` when both the spec validation and supplied
   live inventory passed; it propagates the non-PASS inventory status otherwise.
3. The CLI now exits with code 2 for any result status other than `PASS`.
4. `tests/test_archicad_template_status.py` provides eight isolated regressions
   using an offline FakeTapir (no live model mutations).
5. The template CI workflow now runs this test suite.

## Verification

- GitHub Actions run: [40351563256](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/40351563256)
- Result: SUCCESS
- Tested head: `da5fe609f56ef93e1b51964d8aa9d4c877dfeed9`
- Scope: Python compile, YAML registry parse, offline validation, offline status regression tests
- Status: `PASS_OFFLINE`

## Honest remaining gates

- No result in this checkpoint proves that Windows Archicad 29.2.1 build 5101
  has executed `scripts/run_archicad_template_live.ps1 -Stage preflight` after this fix.
- No live template write, Form 3 drawing, dynamic AutoText placement,
  or final `.tpl` generation is claimed.
- The final candidate still needs clean-project read-only preflight,
  supervised write stages, and visual/PDF/DWG/IFC regression before release.

## Next test on the user's Windows workstation

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage preflight
```

Only after `preflight` returns PASS with archived evidence may the existing
write stages be considered. Do not bypass `confirm-project`, do not use
`--allow-nonempty` for template initialization, and do not touch existing
production projects.
