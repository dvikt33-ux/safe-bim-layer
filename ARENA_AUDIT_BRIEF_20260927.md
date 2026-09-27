# Arena audit brief — plinth-grade runtime snapshot

## Snapshot context

- Baseline Story/Elevation Safety commit: `d0179c097a0094fdb2fa3bda7bf0d11810835435`.
- Development branch at snapshot preparation: `plinth-grade-controller-history`.
- Audit snapshot branch: `arena/plinth-grade-runtime-audit-20260927`.
- Live evidence: plinth wall GUID `FCA25CFD-A6B7-4BCF-A6B0-A521509FC170`; `floorIndex=0`; `z=-0.600`; `height=0.600`; `structureType=Basic`; bottom/top `=-0.600/0.000`.
- `create_plinth_segment` was added after the live PASS.
- Modal/busy probe used `GetProjectInfo` / `GetStories`. `Invalid program status` is expected to lead to fail-closed / `WAITING_USER`, with no blind retry.
- Scope includes the resumable runtime/controller, `StoryResolver`/`VerticalContext`, and current-job/history UX.

These are recorded evidence points, not guarantees. Arena should independently inspect and re-run relevant checks against this snapshot.

## Audit scope

Please independently audit:

- runtime state machine;
- concurrency and single-flight behavior;
- `WAITING_USER` / `UNKNOWN_OUTCOME` resume semantics;
- reconciliation and no-blind-retry guarantees;
- project identity;
- vertical BIM correctness;
- runtime integration of `create_plinth_segment`;
- controller/IPC current-job and history behavior;
- localhost/security boundaries;
- crash/restart/stale SQLite behavior;
- malformed requests;
- duplicate writes and races.

## Known suspicions for independent verification

These are audit questions, not asserted findings:

1. Does `WAITING_USER → Continue` reconcile or can it dispatch blindly?
2. Can parallel `Continue` requests pass admission and dispatch one job more than once?
3. Is `create_plinth_segment` exposed through the resumable runtime operations dispatcher with correct reconciliation?
4. Are generated artifacts excluded from the snapshot and future commits?

## Pre-snapshot local checks

Reported before this snapshot preparation:

- regression checks: `33/33 PASS`;
- BIMEXEC: `62 checks passed`;
- `compileall`: PASS;
- `py_compile`: PASS;
- `git diff --check`: PASS.

The exact commands and fresh results executed during snapshot preparation are recorded below. A successful check does not replace independent Arena review.

### Fresh commands/results

- `python -m pytest -q` — NOT RUN: `No module named pytest`.
- `python -m unittest -q test_resumable_executor test_safe_bim_layer_regressions test_story_vertical_context` — PASS; `Ran 24 tests`; `OK`.
- `python -m compileall -q . -x "palette[\\/]build-v143[\\/]"` — PASS.
- `python -m py_compile controller/app.py controller/client.py safe_bim_layer.py safe_bim_runtime.py test_resumable_executor.py test_safe_bim_layer_regressions.py test_story_vertical_context.py` — PASS.
- `git diff --check` — PASS.

## Snapshot boundary

This branch is an audit snapshot only. No functional bug fixes are included, `main` is not changed, no branch is merged, and no pull request is opened.

Excluded generated/local artifacts include `logs/`, SQLite state/database files, `__pycache__/`, temporary plans, `palette/build-v143/`, `.apx`, `.pdb`, `.obj`, `.lib`, `.exp`, CMake build output, and other generated files covered by `.gitignore`.
