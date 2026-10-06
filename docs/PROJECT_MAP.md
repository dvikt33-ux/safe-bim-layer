# Project Map and Cleanup Classification

This file is the canonical map for repository cleanup. The immediate rule is
**classify first, move/delete later**. Historical proof and working recipes must not be
destroyed merely because a newer orchestration layer exists.

## CURRENT — active runtime or active verification path

| Path | Role | Cleanup rule |
| --- | --- | --- |
| `closed_loop/` | Closed-loop state machine, live adapters, recovery and Stage 4 harness | Keep active |
| `scripts/archicad_executor.py` | Typed BIM executor used by the proven v0 path | Keep active |
| `scripts/archicad_chat_executor.py` | Narrow natural-language -> typed request adapter | Keep active |
| `scripts/archicad_write_cycles/` | Proven native recipes and geometry checks | Keep; migrate capability-by-capability |
| `archicad-addon/Examples/model_dump_v1.py` | Factual model read path | Keep active |
| `tests_stage2/` | Orchestrator regression | Keep active |
| `tests_stage3/` | First live-loop regression logic | Keep active |
| `tests_stage4_live/` | Stage 4 reliability tests | Keep active |
| `tests_audit_pack/` | Evidence-pack verification | Keep active |
| `docs/CLOSED_LOOP_IMPLEMENTATION_STAGES.md` | Stage gate policy | Canonical |
| `docs/STAGE4_LIVE_HARDENING.md` | Current Stage 4 procedure and semantics | Canonical for Stage 4 |

## EVIDENCE — immutable proof, not source code

| Path | Meaning |
| --- | --- |
| `outputs/closed-loop-stage1/` | Frozen v0 live regression evidence |
| `outputs/closed-loop-stage3/` | First autonomous closed-loop live evidence |
| `outputs/closed-loop-stage4/` | Stage 4 acceptance/offline/live evidence |

Evidence may be compacted or moved only with SHA-preserving manifests and a verified
migration. Never edit historical evidence in place to reflect a newer run.

## LEGACY / HISTORICAL — useful provenance, not the current runtime

| Path | Why it is legacy |
| --- | --- |
| `safe_bim_layer.py` | Earlier Safe BIM v0.1 deterministic wrapper over Tapir 1.5.8 |
| `SAFE_BIM_V01_REPORT.md` | Historical report for the v0.1 generation |
| `qwen_safe_bim_integration.py` | Earlier local-Qwen high-level planner experiment |
| `safe-bim-v01-schema-test.json` | v0.1-era schema test artifact |
| `tapir-1.5.8.json` | Old pinned schema snapshot; active live baseline uses newer Tapir |
| `ARENA_TASK_ARCHITECTURE_AUDIT.md` | Historical review prompt, not runtime behavior |

These files should eventually move under an archive/history namespace after references are
checked. They should not be deleted in the first cleanup pass.

## REVIEW / MIGRATION — do not classify as dead yet

| Path | Reason |
| --- | --- |
| `bimexec/` | Coordination and handoff documentation from earlier execution architecture |
| `examples/` | May contain useful small reproducible samples |
| root-level reports not referenced by the active closed loop | Need reference audit before archival |

A file moves from REVIEW to LEGACY only after confirming that active code/tests/docs do not
depend on it.

## Cleanup order

1. Keep the active Stage 4 source and evidence frozen enough to finish verification.
2. Make README, this map and CURRENT_STATUS the canonical navigation layer.
3. Audit references from current source/tests/docs into LEGACY/REVIEW files.
4. Move truly historical files into an archive namespace in one dedicated commit.
5. Run all offline regressions.
6. Only then consider deletion of redundant copies or obsolete generated artifacts.

## Non-goals of cleanup

Cleanup must not:

- add a new BIM capability;
- rewrite the stable v0 executor for style;
- weaken Stage 4 gates;
- rewrite historical PASS evidence;
- merge normative logic into the mutation executor;
- turn research prototypes into production merely by relocating them.
