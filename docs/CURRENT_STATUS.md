# Current Project Status

Status date: 2026-10-07.

This page is the canonical human-readable status. Historical reports remain evidence and
may describe an older point in the project.

## Closed-loop stages

| Stage | Status | Evidence boundary |
| --- | --- | --- |
| Stage 1 — v0 Wall regression | PASS | Live two-step Wall continuation with factual GUID/read-back chain |
| Stage 2 — orchestrator skeleton | PASS | Offline deterministic state-machine and guard tests |
| Stage 3 — first autonomous Wall loop | PASS | Live one-goal, two-dependent-mutation closed loop |
| Audit Pack | PASS | Deterministic source-pinned evidence pack and verifier |
| Stage 4 — live hardening | **PASS / VERIFIED** | All C01–C30 criteria PASS; required live/offline scenario matrix complete |
| Stage 4 performance/evidence-I/O cleanup | **PASS / VERIFIED** | Post-Stage-4 optimization only; safety semantics unchanged |
| Stage 5 | NOT STARTED | Permitted; no Stage 5 capability has been started |

## Latest Stage 4 work

Confirmed in the operator run:

- Fresh source-pinned `hardening-offline-007` completed with `Offline proof PASS`.
- Explicit project binding to `C:\Users\Admin\Downloads\дбликат.pln` passed.
- The rebound fixture setup passed with one physical `CreateWalls` dispatch.
- Factual element count changed exactly `5297 -> 5299`.
- Fixture predecessor GUID:
  `CBE5E561-B3E5-49D3-A597-8282DD69472A`.
- Fixture seed GUID:
  `CDD32EF6-18F1-4413-BBAE-E46CB9569582`.
- The fixture report proved two added Wall GUIDs and no automatic retry.

The real `S4-01` run `live-20261007-001/S4-01` completed successfully:

- scenario status: `PASS`;
- job final status: `VERIFIED`;
- physical mutation calls: `2`;
- duplicate mutation count: `0`;
- confirmed native responses: `2`;
- Audit Pack: `PASS`;
- iteration 1 created `3534BB8A-898C-4F39-B739-03F2C74DEB96` from source
  `C6A1776C-BEC4-4758-9827-D23CAFCEF7B2` at +1.0 m;
- iteration 2 used that exact created GUID as its source and created
  `BBEE36AC-5A89-4797-AFAC-F03CF75A5321` at +0.5 m;
- both joins were factual `jointDistance = 0.0`;
- protected-main runtime guard: PASS.

The real `S4-02` run also completed successfully:

- scenario status: `PASS`;
- job final status: `VERIFIED`;
- physical mutation calls: `3` (one helper + two goal segments);
- duplicate mutation count: `0`;
- confirmed native responses: `3`;
- stale decision invalidations: `1`;
- stale action executor calls: `0`;
- Audit Pack: `PASS`;
- both accepted goal-segment joins had factual `jointDistance = 0.0`.

The real `S4-03` run also completed successfully:

- scenario status: `PASS`;
- job final status: `VERIFIED`;
- physical mutation calls: `2`;
- duplicate mutation count: `0`;
- reconciliation outcome: `RECONCILED_APPLIED`;
- confirmed native responses: `2`;
- Audit Pack: `PASS`;
- the first lost-response mutation was not replayed;
- the second segment used the reconciled first segment GUID as its source;
- both factual joins had `jointDistance = 0.0`.

The real `S4-06` run completed successfully:

- scenario status: `PASS`;
- job final status: `VERIFIED`;
- crash worker exit code: `86`;
- recovered from crash: `true`;
- reconciliation outcome: `RECONCILED_APPLIED`;
- physical mutation calls: `2`;
- duplicate mutation count: `0`;
- confirmed native responses: `2`;
- Audit Pack: `PASS`;
- the crashed first mutation was not replayed;
- the second segment continued from the reconciled created GUID;
- both factual joins had `jointDistance = 0.0`.

## Stage 4 required live scenarios

| Scenario | Purpose | Current status |
| --- | --- | --- |
| S4-01 | Happy two-segment regression | **LIVE PASS / VERIFIED** |
| S4-02 | Stale plan rejected before execution, then replan | **LIVE PASS / VERIFIED** |
| S4-03 | Lost response after physical mutation; reconcile applied without duplicate | **LIVE PASS / VERIFIED** |
| S4-04 | Reconciled not-applied -> fresh observation/replan | OFFLINE PASS only |
| S4-05 | Ambiguous reconciliation -> block | OFFLINE PASS only |
| S4-06 | Crash after mutation -> restart/reconcile without duplicate | **LIVE PASS / VERIFIED** + offline PASS |
| S4-07 | No-progress guard | OFFLINE PASS |
| S4-08 | Iteration-limit guard | OFFLINE PASS |
| S4-09 | Pre-dispatch transport failure | OFFLINE PASS |
| S4-10 | Missing factual read-back never verifies | OFFLINE PASS |

## Performance pass

The post-Stage-4 performance/evidence-I/O cleanup is complete and **PASS / VERIFIED**.

Measured operator results:

- retained LIVE S4-06 Audit Pack verification: about 117.6 s historical -> 23.732 s optimized;
- 10 factual S4-06 snapshots collapse to 3 timing-normalized semantic states (5 / 3 / 2);
- fresh `hardening-offline-010`: PASS in 22.367 s;
- prior full-recompute control `hardening-offline-009`: PASS in 195.744 s;
- Stage 1 fast historical revalidation: 5.786 s;
- Stage 3 fast historical revalidation: 5.936 s;
- focused performance/Audit Pack regressions: 58/58 PASS.

The fast historical path is fail-closed: it reuses accepted semantic PASS only
when the historical verifier Git blob, accepted pack contracts/manifests and all
pinned source bytes remain unchanged. Any mismatch falls back to the full historical verifier.

Acceptance receipt:
`outputs/closed-loop-stage4/stage4-performance-acceptance.json`.


Stage 4 has no remaining acceptance blocker. Project identity binding, fixture setup, stale-plan rejection, unknown-outcome reconciliation and crash recovery all passed in their required proof modes.

A separate repository-maintenance issue was discovered on 2026-10-06: `main` legitimately
advanced from the historical merge-base `72e9be15...` to `d5695f43...` by adding only the
construction-detail machine database under `knowledge/detail-machine/`. The old Stage-4
check incorrectly required the entire `main` branch SHA to remain frozen forever.

That brittle check has now been replaced with a protected-path guard. Stage 4 permits
unrelated main changes, but fails if `main` changed protected BIM runtime/evidence paths
such as `closed_loop/`, `scripts/`, `archicad-addon/`, Stage 1-4 tests/evidence, or the
baseline-pinned v0.1 runtime files.

`hardening-offline-006` is historical for the pre-main-guard source state. The replacement source-pinned proof `hardening-offline-007` passed before the accepted live runs.

The final Stage 4 acceptance report is `VERIFIED`; C01–C30 all PASS and there is no remaining live gate.

## What is frozen

Stage 4 is closed. Preserve these as the verified baseline:

- Stage 1 historical evidence;
- Stage 3 historical evidence;
- the stable v0 physical Wall execution path;
- the no-blind-retry rule;
- mutation-attempt durability;
- project/model identity binding;
- mandatory factual read-back.

## Next after Stage 4

The planned performance/evidence-I/O cleanup is complete and VERIFIED. The next step may migrate one already-proven BIM capability at a time into the closed loop; prefer existing proven recipes over new implementations from scratch.
