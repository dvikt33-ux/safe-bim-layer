# Safe BIM Layer — Archicad Closed Loop

Safe BIM Layer is an evidence-first control layer for Archicad 29 over the Tapir JSON API.
The active development path is no longer the original "working MVP" alone: the current
system wraps the proven v0 executor in a closed loop that observes the live model, plans
one typed mutation, executes it, reads the result back, audits the evidence, and only
returns `VERIFIED` when every required criterion passes.

## Current architecture

```text
USER GOAL
   |
   v
PROJECT / CLOSED-LOOP ORCHESTRATOR
   |
   +--> OBSERVE ---- fresh factual Model Dump v1
   |
   +--> PLAN ------- typed, model-bound action
   |
   +--> EXECUTE ---- guarded Tapir mutation
   |
   +--> READ_BACK -- fresh factual model state
   |
   +--> AUDIT ------ acceptance criteria + evidence
   |
   +--> REPLAN / BLOCK / UNKNOWN_OUTCOME / VERIFIED
```

The normative/audit layer is intentionally separate from physical BIM mutation. The
executor does not get to declare success by itself; factual read-back is mandatory.

## Development rule

One stage must be formally complete before the next capability is added.

- Stage 1 — frozen v0 Wall regression: **PASS**
- Stage 2 — closed-loop orchestrator skeleton: **PASS**
- Stage 3 — first live two-step Wall loop: **PASS**
- Stage 4 — reliability hardening of that same Wall loop: **NOT YET VERIFIED**
- Stage 5 — prohibited until Stage 4 passes

See [docs/CLOSED_LOOP_IMPLEMENTATION_STAGES.md](docs/CLOSED_LOOP_IMPLEMENTATION_STAGES.md)
for the full gate policy.

## Active Stage 4

Stage 4 keeps the exact same Wall capability and hardens it against stale plans,
transport ambiguity, crashes, duplicate mutation, missing read-back, no-progress and
iteration-limit failures.

The active implementation is under:

- `closed_loop/orchestrator.py`
- `closed_loop/wall_attempts.py`
- `closed_loop/live_wall.py`
- `closed_loop/live_wall_hardening.py`
- `closed_loop/stage4_preflight.py`
- `closed_loop/stage4_fixture.py`
- `closed_loop/stage4_live_scenario.py`

The rebound test-project flow uses an explicitly pinned disposable PLN plus an isolated
synthetic Wall fixture. It must never fall back to arbitrary building Walls.

Detailed procedure: [docs/STAGE4_LIVE_HARDENING.md](docs/STAGE4_LIVE_HARDENING.md).

## Proven lower-level BIM capabilities

The older executor/recipe layer remains useful and is being migrated upward rather than
rewritten. It contains proven or partially proven recipes for Wall, Window, Door, Slab,
Roof, Morph and related read-back operations. These capabilities are **not automatically
closed-loop VERIFIED** merely because their lower-level recipes work.

Main entry points:

- `archicad-addon/Examples/model_dump_v1.py` — factual Model Dump v1
- `scripts/archicad_executor.py` — typed request executor
- `scripts/archicad_chat_executor.py` — narrow Russian-language adapter
- `scripts/archicad_write_cycles/` — geometry-derived native write/read-back recipes

## Evidence and fail-closed rules

The project treats the following as hard invariants:

1. A write is never considered complete without factual read-back.
2. `UNKNOWN_OUTCOME` never causes a blind retry.
3. A stale model invalidates the planned action before physical execution.
4. Project identity is pinned before writes.
5. Mutation attempt identity is durable before dispatch.
6. Historical evidence is not rewritten to make a newer run pass.
7. Offline fixtures are never promoted to live proof.
8. Stage status is `PASS` only when every required criterion is `PASS`.

## Repository map

The repository contains several generations of the project. Do not assume every root
file is part of the current runtime.

- **Current closed-loop core:** `closed_loop/`, `tests_stage2/`,
  `tests_stage3/`, `tests_stage4_live/`, `tests_audit_pack/`
- **Current Archicad bridge/executor:** `archicad-addon/`, `scripts/`
- **Evidence:** `outputs/closed-loop-stage1/`, `outputs/closed-loop-stage3/`,
  `outputs/closed-loop-stage4/`
- **Legacy/research generation:** old v0.1 Safe BIM/Qwen/Tapir-1.5.8 files in the
  repository root
- **Coordination/history:** `bimexec/`, Arena/Work handoff documents

The canonical classification and cleanup policy is in
[docs/PROJECT_MAP.md](docs/PROJECT_MAP.md).

## Current status

For the latest verified vs unverified boundary, use
[docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md). That file is the canonical human-readable
status page; historical reports remain immutable evidence, not the current project summary.

## Safety note

The live tools operate on the Archicad instance listening on `127.0.0.1:19723`.
Use only a disposable/test PLN for fault-injection runs. The code intentionally does not
silently switch projects, reinterpret a mismatched project as equivalent, or weaken a
failed acceptance gate.
