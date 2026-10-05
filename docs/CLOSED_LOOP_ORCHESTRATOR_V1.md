# Closed Loop Orchestrator v1

Status: architecture contract / next implementation layer

Baseline execution substrate: `feature/working-archicad-mvp` at commit `565ea2e0414a14bedbca09999690d7b97f877fa3`.

## Non-negotiable rule

The proven Archicad v0 execution path is a stable substrate. Planner, Auditor and Orchestrator are layered above it. Do not rewrite or broaden the proven v0 path merely to implement orchestration. Any change below the orchestrator must preserve the v0 regression tests before it can become a new baseline.

## Goal

One user request must be able to drive multiple model iterations without requiring the user to issue the next micro-command:

`GOAL -> OBSERVE -> PLAN -> EXECUTE -> READ_BACK -> AUDIT -> REPLAN -> ... -> VERIFIED`

The loop stops only when the explicit acceptance contract is satisfied or a fail-closed terminal state is reached.

## Separation of responsibility

### Executor

The Executor performs only typed BIM operations. It must not decide architectural intent or declare the project compliant. It must return factual execution/read-back evidence.

### Auditor

The Auditor never mutates the model. It compares read-back evidence against explicit acceptance criteria and returns per-criterion verdicts.

Allowed verdicts:

- `PASS`
- `FAIL`
- `NOT_VERIFIED`
- `DATA_MISSING`
- `CONFLICT`
- `BLOCKED_BY_TRANSPORT`

Only `PASS` satisfies a required criterion.

### Orchestrator

The Orchestrator owns the goal, acceptance contract, iteration state and replanning decision. It may request another typed operation only from current observed evidence. It must not assume that a requested operation succeeded.

## State machine

`RECEIVED -> OBSERVING -> PLANNING -> EXECUTING -> READING_BACK -> AUDITING`

From `AUDITING`:

- all required criteria `PASS` -> `VERIFIED`
- actionable `FAIL` -> `REPLANNING` -> `EXECUTING`
- missing user/project data -> `WAITING_FOR_DATA`
- transport/evidence insufficiency -> `BLOCKED`
- unresolved ambiguity after execution -> `UNKNOWN_OUTCOME`

`UNKNOWN_OUTCOME` must never be converted into an automatic retry without reconciliation.

## Acceptance contract

Every closed-loop job must have machine-readable acceptance criteria before mutation begins. Criteria must be objective enough to evaluate from project data, model read-back, normative evidence, or explicitly approved user input.

Example:

```json
{
  "goalId": "room-6x4-v1",
  "criteria": [
    {"id":"C01","required":true,"check":"room_internal_dimensions","expected":{"x":6.0,"y":4.0,"unit":"m"}},
    {"id":"C02","required":true,"check":"wall_thickness","expected":{"value":0.30,"unit":"m"}},
    {"id":"C03","required":true,"check":"wall_chain_closed","expected":true},
    {"id":"C04","required":true,"check":"door_width","expected":{"value":0.90,"unit":"m"}},
    {"id":"C05","required":true,"check":"window_width","expected":{"value":1.50,"unit":"m"}},
    {"id":"C06","required":true,"check":"host_relationships_valid","expected":true}
  ]
}
```

## Evidence rules

1. A planner prediction is not evidence of model state.
2. Executor success without read-back is not `PASS`.
3. Read-back must refer to the model state after the attempted mutation.
4. GUIDs of created/modified elements must be retained when available.
5. Each audit result must identify the evidence used.
6. If the model changed outside the active job, stale assumptions must be invalidated and affected geometry re-read before replanning.
7. `NOT_VERIFIED` is never silently promoted to `PASS`.

## Minimal v1 loop

The first implementation should intentionally remain narrow. It should prove orchestration rather than maximize the Archicad command surface.

1. Receive one goal and its acceptance contract.
2. Read a fresh model state.
3. Produce one typed action or action batch supported by the proven executor.
4. Execute through the existing v0 adapter/executor.
5. Read the resulting model state.
6. Audit all currently evaluable criteria.
7. If required criteria fail and a correction is possible, generate the next action from the new state.
8. Repeat with an explicit iteration limit and no-progress detection.
9. Finish only as `VERIFIED`, `WAITING_FOR_DATA`, `BLOCKED`, or `UNKNOWN_OUTCOME`.

## Safety and termination

The orchestrator must enforce:

- maximum iterations per job;
- no-progress detection using model/read-back hashes or equivalent evidence;
- stale-model detection;
- typed operation allowlist;
- no arbitrary shell/Python supplied by a remote job;
- reconciliation before retry after ambiguous execution;
- retained audit trail of requested action, executor result, read-back and verdicts.

Iteration exhaustion is `BLOCKED`, not success.

## Regression rule for v0

The current v0 proof remains mandatory:

1. Continue the selected/latest unambiguous wall by 1.0 m.
2. Read back the created wall and verify a zero-distance joint within tolerance.
3. On a fresh dump, continue the newly created wall by 0.5 m.
4. Verify that the second planning decision uses the first created wall as its source and again produces a zero-distance joint.

Any lower-layer change that breaks this proof cannot be promoted.

## First closed-loop acceptance test

After the orchestrator skeleton exists, run a single-request test on a disposable/test PLN using only operations already proven live. The test must require at least two dependent iterations where iteration 2 is chosen from the read-back of iteration 1. The user must not provide a second micro-command.

PASS requires:

- one initial user goal;
- fresh pre-action observation;
- at least two executed dependent model mutations;
- read-back after each mutation;
- second action derived from the changed model, not precomputed blindly;
- per-criterion audit evidence;
- final required criteria all `PASS`;
- no unverified required criterion;
- retained GUID/evidence chain.

Only after this test passes should the command surface be broadened systematically to additional materials/elements, transactions/undo, normative gates and performance optimization.

## Relationship to project stages

This loop is the execution primitive for the higher project workflow. It does not replace Stage 0 or normative/design stages.

Future project orchestration uses the same primitive inside each stage:

`Stage input -> work -> evidence -> audit -> correction loop -> 100% required PASS -> freeze -> next stage`.

Stage 0 remains the intake/data-gap gate. Later stages may not progress on required `FAIL`, `NOT_VERIFIED`, `DATA_MISSING`, `CONFLICT` or `BLOCKED_BY_TRANSPORT` results.
