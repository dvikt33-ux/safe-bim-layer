# Documentation Index

Use this page to navigate the project without relying on historical file names.

## Start here

1. [../README.md](../README.md) — project purpose, architecture and active runtime.
2. [CURRENT_STATUS.md](CURRENT_STATUS.md) — latest PASS / NOT VERIFIED boundary.
3. [PROJECT_MAP.md](PROJECT_MAP.md) — current vs evidence vs legacy vs review classification.
4. [CLOSED_LOOP_IMPLEMENTATION_STAGES.md](CLOSED_LOOP_IMPLEMENTATION_STAGES.md) — mandatory stage gates.

## Active closed-loop design

- [CLOSED_LOOP_ORCHESTRATOR_V1.md](CLOSED_LOOP_ORCHESTRATOR_V1.md) — orchestrator contract.
- [CLOSED_LOOP_IMPLEMENTATION_STAGES.md](CLOSED_LOOP_IMPLEMENTATION_STAGES.md) — stage order and anti-sprawl policy.
- [STAGE2_ORCHESTRATOR_SKELETON.md](STAGE2_ORCHESTRATOR_SKELETON.md) — Stage 2 design/evidence.
- [STAGE3_LIVE_WALL_CLOSED_LOOP.md](STAGE3_LIVE_WALL_CLOSED_LOOP.md) — first live adaptive loop.
- [STAGE4_LIVE_HARDENING.md](STAGE4_LIVE_HARDENING.md) — current reliability stage.

## Evidence and audit

- [AUDIT_PACK_V1.md](AUDIT_PACK_V1.md) — deterministic evidence-pack design.
- `outputs/closed-loop-stage1/` — Stage 1 frozen live evidence.
- `outputs/closed-loop-stage3/` — Stage 3 frozen live evidence.
- `outputs/closed-loop-stage4/` — Stage 4 contracts and generated evidence.

Historical evidence is not the current status page. Do not infer the present stage from
an old PASS/BLOCKED report without checking [CURRENT_STATUS.md](CURRENT_STATUS.md).

## Lower-level Archicad runtime

The active bridge/executor documentation lives primarily beside the code:

- `archicad-addon/Examples/model_dump_v1.py`
- `scripts/archicad_executor.py`
- `scripts/archicad_chat_executor.py`
- `scripts/archicad_write_cycles/`

The original root README used to describe only this layer; it is now treated as a
subsystem of the closed loop.

## Historical / migration material

See [PROJECT_MAP.md](PROJECT_MAP.md) and
[REFERENCE_AUDIT_2026-10-06.md](REFERENCE_AUDIT_2026-10-06.md) before touching root-level
v0.1, Qwen, Tapir 1.5.8, Arena, Work or archived BIMEXEC material. These files are retained for provenance until a
reference audit proves they can be moved safely.

## Package structure

- [CLOSED_LOOP_PACKAGE_MAP.md](CLOSED_LOOP_PACKAGE_MAP.md) — logical core/live/recovery/harness boundaries and the post-Stage-4 refactor gate.
- [BRANCH_INVENTORY_2026-10-06.md](BRANCH_INVENTORY_2026-10-06.md) — active, milestone, diverged and cleanup-candidate branch classification.

## Status vocabulary

- **PASS** — all required checks for that stated scope are satisfied.
- **NOT VERIFIED** — implementation/evidence is incomplete for required acceptance.
- **BLOCKED** — a gate intentionally stopped progression.
- **UNKNOWN_OUTCOME** — physical mutation may or may not have occurred; never blind retry.
- **OFFLINE PASS** — useful proof, but not a substitute for mandatory live evidence.
