# Current Project Status

Status date: 2026-10-06.

This page is the canonical human-readable status. Historical reports remain evidence and
may describe an older point in the project.

## Closed-loop stages

| Stage | Status | Evidence boundary |
| --- | --- | --- |
| Stage 1 — v0 Wall regression | PASS | Live two-step Wall continuation with factual GUID/read-back chain |
| Stage 2 — orchestrator skeleton | PASS | Offline deterministic state-machine and guard tests |
| Stage 3 — first autonomous Wall loop | PASS | Live one-goal, two-dependent-mutation closed loop |
| Audit Pack | PASS | Deterministic source-pinned evidence pack and verifier |
| Stage 4 — live hardening | NOT YET VERIFIED | Mandatory live scenarios are not all complete |
| Stage 5 | NOT STARTED | Forbidden until Stage 4 PASS |

## Latest Stage 4 work

Confirmed in the operator run:

- `hardening-offline-006` completed with `Offline proof PASS`.
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

## Stage 4 required live scenarios

| Scenario | Purpose | Current status |
| --- | --- | --- |
| S4-01 | Happy two-segment regression | **LIVE PASS / VERIFIED** |
| S4-02 | Stale plan rejected before execution, then replan | NOT VERIFIED |
| S4-03 | Lost response after physical mutation; reconcile applied without duplicate | NOT VERIFIED |
| S4-04 | Reconciled not-applied -> fresh observation/replan | OFFLINE PASS only |
| S4-05 | Ambiguous reconciliation -> block | OFFLINE PASS only |
| S4-06 | Crash after mutation -> restart/reconcile without duplicate | OFFLINE PASS; LIVE NOT VERIFIED |
| S4-07 | No-progress guard | OFFLINE PASS |
| S4-08 | Iteration-limit guard | OFFLINE PASS |
| S4-09 | Pre-dispatch transport failure | OFFLINE PASS |
| S4-10 | Missing factual read-back never verifies | OFFLINE PASS |

## Current blocker

The project is **not blocked by project identity anymore** and is **not blocked by the
missing synthetic Wall fixture anymore**. Those two issues were resolved.

A separate repository-maintenance issue was discovered on 2026-10-06: `main` legitimately
advanced from the historical merge-base `72e9be15...` to `d5695f43...` by adding only the
construction-detail machine database under `knowledge/detail-machine/`. The old Stage-4
check incorrectly required the entire `main` branch SHA to remain frozen forever.

That brittle check has now been replaced with a protected-path guard. Stage 4 permits
unrelated main changes, but fails if `main` changed protected BIM runtime/evidence paths
such as `closed_loop/`, `scripts/`, `archicad-addon/`, Stage 1-4 tests/evidence, or the
baseline-pinned v0.1 runtime files.

Because `closed_loop/live_wall.py` changed to implement this correction, the previously
observed `hardening-offline-006` proof is now historical for the prior source state. A new
source-pinned offline proof is required before the next accepted live S4 run.

The remaining live gate is now: S4-02 -> S4-03 -> S4-06, with all required criteria and Audit Packs passing.

## What is frozen

Do not casually rewrite these while Stage 4 is open:

- Stage 1 historical evidence;
- Stage 3 historical evidence;
- the stable v0 physical Wall execution path;
- the no-blind-retry rule;
- mutation-attempt durability;
- project/model identity binding;
- mandatory factual read-back.

## Next after Stage 4

Only after Stage 4 PASS, migrate one already-proven BIM capability at a time into the
closed loop. The preferred migration pool is existing proven recipes rather than new
implementations from scratch.
