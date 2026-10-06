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
| `docs/STAGE4_LIVE_HARDENING.md` | Verified Stage 4 procedure and semantics | Frozen milestone reference |

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
| `safe_bim_layer.py` | Baseline-pinned legacy; Stage-2 verifier checks this exact path remains unchanged |
| `qwen_safe_bim_integration.py` | Baseline-pinned legacy; Stage-2 verifier checks this exact path remains unchanged |
| `tapir-1.5.8.json` | Legacy schema snapshot still referenced by the pinned Qwen v0.1 script |
| `archive/legacy-v0.1/` | Historical v0.1 report/schema proof moved out of the active root |
| `archive/coordination/` | Historical review/coordination material moved out of the active root |

The remaining root-level legacy runtime files are intentionally not moved yet because the
Stage-2 regression contract pins their paths. See `REFERENCE_AUDIT_2026-10-06.md`.

## REVIEW / MIGRATION — do not classify as dead yet

| Path | Reason |
| --- | --- |
| `archive/coordination/bimexec/` | Archived coordination and handoff documentation from the earlier BIMEXEC/T0 architecture |
| `examples/` | May contain useful small reproducible samples |
| root-level reports not referenced by the active closed loop | Need reference audit before archival |

A file moves from REVIEW to LEGACY only after confirming that active code/tests/docs do not
depend on it. The BIMEXEC coordination-only directory passed this check and has been archived.

## Cleanup order

1. Preserve the now-VERIFIED Stage 4 source/evidence as a milestone baseline.
2. Run the performance/evidence-I/O cleanup without weakening Stage 4 semantics.
3. Make README, this map and CURRENT_STATUS the canonical navigation layer.
4. Audit references from current source/tests/docs into LEGACY/REVIEW files.
5. Move truly historical files into an archive namespace in one dedicated commit.
6. Run all offline regressions after structural cleanup.
7. Only then consider deletion of redundant copies or obsolete generated artifacts.

## Non-goals of cleanup

Cleanup must not:

- add a new BIM capability;
- rewrite the stable v0 executor for style;
- weaken Stage 4 gates;
- rewrite historical PASS evidence;
- merge normative logic into the mutation executor;
- turn research prototypes into production merely by relocating them.
