# BIMEXEC — historical coordination layer

Status: **REVIEW / HISTORICAL COORDINATION**, not the active Safe BIM closed-loop runtime.

This directory contains portable BIMEXEC specifications, capability-probe planning and
handoff documents from an earlier T0/Arena/Work execution architecture. It remains useful
as provenance and as a source of migration ideas, but its handoff state must not be read as
the current project status.

Current project entry points:

- `../README.md` — active Safe BIM / Archicad closed-loop architecture
- `../docs/CURRENT_STATUS.md` — canonical PASS / NOT VERIFIED boundary
- `../docs/PROJECT_MAP.md` — cleanup and migration classification

## Contents

- `COORDINATION.md` — historical shared handoff rules
- `HANDOFF_ARENA.md` — historical Arena transfer instructions
- `HANDOFF_WORK.md` — historical Work/Codex read-only baseline instructions

## Cleanup rule

Do not delete or revive BIMEXEC by implication. Before any code or probe from this
directory is migrated into the active runtime, compare it against the current closed-loop
contracts and safety invariants. Any useful capability should be migrated explicitly and
tested under the current stage gate.

Production Windows Router code remains outside the current Stage 4 scope.
