# Closed Loop Package Map

This document describes the **logical** package boundaries of the current
`closed_loop/` directory. It intentionally does not move Python modules while Stage 4 is
open, because several current tests and source-pinned proofs depend on their present paths.

## 1. Core contracts

### `models.py`

Owns typed serializable contracts:

- state and verdict enums;
- acceptance criteria and contracts;
- observed facts and observations;
- typed actions and planner decisions;
- execution/read-back/job records.

This is the data-contract layer. It should not acquire Archicad transport logic.

### `auditor.py`

Pure acceptance evaluator. It compares retained observed facts against an explicit
`AcceptanceContract` and produces typed audit criteria.

### `orchestrator.py`

Owns the generic state machine and transition rules:

`RECEIVED -> OBSERVING -> PLANNING -> EXECUTING -> READING_BACK -> AUDITING`

plus replan/wait/block/unknown/verified terminals.

It owns orchestration semantics, not Archicad-specific geometry.

**Logical layer:** `core/`.

## 2. Offline test support

### `mocks.py`

Deterministic fixture-only Observer/Planner/Executor/ReadBack implementations. No transport
and no model writes. It is used by Stage 2 and Stage 4 regression tests.

### `demo.py`

Small Stage-2 offline demonstration over the mocks.

**Logical layer:** `testing/`.

Do not mistake these modules for production adapters.

## 3. Live Archicad adapter

### `live_wall.py`

Binds the generic orchestrator to the proven Wall continuation capability:

- project identity checks;
- Model Dump snapshots;
- live model fingerprints;
- Wall source/fixture selection;
- live planner/model check;
- guarded execution/read-back;
- Stage-3 acceptance helpers.

This module is deliberately Wall-specific today.

**Logical layer:** `live/wall/`.

## 4. Durable mutation and recovery

### `wall_attempts.py`

Owns the durable mutation-attempt protocol:

- attempt UUID preparation;
- mutation signature;
- exclusive journal claim;
- dispatch/confirmation state;
- factual reconciliation;
- recoverable orchestrator extension.

### `live_wall_hardening.py`

Connects the durable attempt protocol to the frozen live Wall executor and implements
controlled fault boundaries/read-back/reconciliation for Stage 4.

**Logical layer:** `recovery/wall/`.

Important current coupling: `wall_attempts.py` imports Wall-specific helpers from
`live_wall.py`. That is acceptable for the active stage but should be broken only in a
post-Stage-4 refactor with a new regression proof.

## 5. Stage harnesses

### `stage3.py`

Historical-but-still-relevant Stage-3 executable harness: offline regression, v0
regression and first live one-goal loop.

### `stage4_preflight.py`

Identity/environment/source-pin gate.

### `stage4_fixture.py`

Creates/verifies the isolated synthetic Wall fixture for rebound disposable PLNs.

### `stage4_offline_evidence.py`

Builds hermetic offline proof and retained fixture evidence.

### `stage4_live_scenario.py`

Runs the mandatory Stage-4 live scenarios and builds scenario evidence/Audit Packs.

**Logical layer:** `harness/stage3` and `harness/stage4`.

Harness code should not become the permanent application API.

## Dependency direction we want

```text
models
  ^
  |
auditor
  ^
  |
orchestrator
  ^
  +-------------------+
  |                   |
testing/mocks      live/wall
                      ^
                      |
                recovery/wall
                      ^
                      |
                stage harnesses
```

The current source is close to this shape but not fully separated. The important known
exception is the Wall-specific dependency from `wall_attempts.py` back into
`live_wall.py`.

## Refactor gate

Do **not** physically move these modules while Stage 4 is NOT VERIFIED.

A package split becomes eligible only after:

1. all mandatory Stage-4 live scenarios PASS;
2. committed Stage-4 evidence is frozen;
3. a fresh source-pinned offline proof passes;
4. the refactor is a separate commit/branch with zero behavior change;
5. Stage 1, Stage 2, Stage 3, Audit Pack and Stage 4 regressions all pass afterward.

Proposed eventual layout:

```text
closed_loop/
  core/
    models.py
    auditor.py
    orchestrator.py
  testing/
    mocks.py
    demo.py
  live/
    wall.py
  recovery/
    wall_attempts.py
    wall_hardening.py
  harness/
    stage3.py
    stage4_preflight.py
    stage4_fixture.py
    stage4_offline_evidence.py
    stage4_live_scenario.py
```

This is a cleanup target, not permission to refactor before the gate.
