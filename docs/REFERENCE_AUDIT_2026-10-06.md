# Reference Audit — 2026-10-06

Scope: determine which old root-level files can be moved out of the active project surface
without changing current runtime behavior or invalidating existing regression contracts.

## Active source/test scan

Scanned current closed-loop modules, Archicad executor/write-cycle scripts, Stage 2/3/4
tests and Audit Pack tests for references to the legacy root files.

### Safe to archive now

The following files had no active source/test dependency and were moved:

- `SAFE_BIM_V01_REPORT.md` -> `archive/legacy-v0.1/SAFE_BIM_V01_REPORT.md`
- `safe-bim-v01-schema-test.json` ->
  `archive/legacy-v0.1/safe-bim-v01-schema-test.json`
- `ARENA_TASK_ARCHITECTURE_AUDIT.md` ->
  `archive/coordination/ARENA_TASK_ARCHITECTURE_AUDIT.md`

These are documentation/evidence artifacts only; no active import or runtime path depends
on their original root location.

### Baseline-pinned legacy — do not move yet

- `safe_bim_layer.py`
- `qwen_safe_bim_integration.py`

They are not used by the current closed-loop runtime, but
`tests_stage2/verify.py` explicitly includes both paths in the Stage-2
`V0 runtime path unchanged` git-diff criterion against the frozen Stage-1 commit.
Relocating them would currently make that regression contract fail.

- `tapir-1.5.8.json`

This is still referenced by the historical Qwen integration script above, so it should
stay with the baseline-pinned v0.1 generation until that generation is archived as one
controlled migration.

### Historical coordination — retain, do not treat as current runtime

- `bimexec/`

Its files describe an older T0/Arena/Work coordination architecture. They are now clearly
marked historical/review. They should be migrated only after deciding whether any T0 probe
capabilities still deserve promotion into the current closed-loop architecture.

## Important distinction

"Not imported by current runtime" is not enough to permit a move. A file can also be pinned
by a regression verifier, evidence manifest, documented path contract or external workflow.
The current audit found exactly that pattern for the old v0.1 Python files.

## Next cleanup pass

1. Decide whether Stage-2's frozen-path criterion should remain path-based forever or be
   replaced by a content/hash manifest that permits archival without losing provenance.
2. If that contract is deliberately migrated, move the v0.1 Python/schema set together.
3. Audit `bimexec/` for unique capabilities vs duplicated historical coordination.
4. Keep Stage 4 implementation untouched until its mandatory live gate is complete.
