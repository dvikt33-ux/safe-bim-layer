# Closed Loop v1 — Strict Implementation Stages

Status: mandatory execution order for `chatgpt/closed-loop-orchestrator-v1`.

## Core development rule

One stage = one finished capability.

Do not expand the command surface, add unrelated BIM element types, add normative logic, add UI work, or perform broad refactors while the current stage is not formally PASS.

Ideas discovered during a stage go to backlog only. They are not implemented until the current stage is closed.

A stage may advance only when:

- its explicit acceptance criteria are complete;
- all required checks are `PASS`;
- required `NOT_VERIFIED = 0`;
- blockers and unresolved ambiguity are zero;
- evidence is complete and current;
- regression for already-frozen capabilities still passes.

Anything else is not stage completion.

## Stage 1 — Freeze and prove v0 baseline

Scope: regression only. No orchestrator features.

Goal: prove that the existing working Archicad v0 remains intact.

Required proof:

1. Fresh model dump.
2. Continue the unique current end Wall by `1.0 m`.
3. Physical Archicad mutation succeeds.
4. Read-back identifies the created Wall GUID.
5. `jointDistance == 0` within tolerance.
6. Obtain a new fresh model dump.
7. Select the Wall created in step 3 as the source for the next continuation.
8. Continue it by `0.5 m`.
9. Read back the second created Wall GUID.
10. `jointDistance == 0` within tolerance.

PASS gate:

- both physical mutations executed;
- both read-backs present;
- iteration 2 uses the actual GUID/result of iteration 1;
- no required field is `NOT_VERIFIED`;
- complete evidence retained.

If Stage 1 fails, stop. Restore baseline before any higher-layer work.

## Stage 2 — Orchestrator skeleton only

Scope: orchestration state and evidence model only.

Do not add new Archicad element types or commands.

Implement:

- one `goal_id`;
- one machine-readable acceptance contract;
- state machine;
- iteration counter;
- storage of observation, planned action, executor result, read-back and audit verdict;
- terminal states:
  - `VERIFIED`
  - `WAITING_FOR_DATA`
  - `BLOCKED`
  - `UNKNOWN_OUTCOME`;
- explicit iteration limit;
- evidence trail.

PASS gate:

- deterministic offline/unit test of the state machine;
- required transitions tested;
- illegal transitions rejected;
- `UNKNOWN_OUTCOME` cannot auto-retry;
- no physical model expansion beyond the proven v0 command surface.

## Stage 3 — First autonomous closed loop

Scope: one single user goal and one already-proven Wall continuation capability.

No windows, doors, slabs, materials, normative rules, UI, or general planner expansion.

Goal:

`ONE USER GOAL -> OBSERVE -> PLAN -> EXECUTE -> READ_BACK -> AUDIT -> REPLAN -> EXECUTE -> READ_BACK -> VERIFIED`

The user supplies one request only.

Required live behavior:

1. Read fresh Archicad state.
2. Determine the source Wall from current geometry.
3. Execute continuation by `1.0 m`.
4. Read back the factual result.
5. Audit the first mutation.
6. Re-observe/replan from the changed model.
7. Use the first mutation's actual created result as the source for continuation by `0.5 m`.
8. Execute the second mutation.
9. Read back the factual result.
10. Audit all acceptance criteria.
11. Return `VERIFIED` only when every required criterion is `PASS`.

Critical adaptive proof:

`iteration_2.sourceGuid == iteration_1.readback.createdGuid`

or an equivalent evidence-backed identity check.

The second operation must not rely on a predicted/precomputed GUID.

PASS gate:

- one initial user goal;
- at least two dependent physical mutations;
- read-back after each mutation;
- second action based on first read-back;
- all required criteria `PASS`;
- no required `NOT_VERIFIED`;
- complete GUID/evidence chain;
- Stage 1 regression still PASS.

Until Stage 3 is PASS, do not broaden BIM functionality.

## Stage 4 — Hardening the same closed-loop scenario

Scope: reliability only. Keep the same Wall scenario.

Implement and prove one item at a time:

1. maximum iteration limit;
2. no-progress detection;
3. stale-model detection;
4. model-state/hash invalidation;
5. reconciliation after ambiguous execution;
6. fail-closed transport/evidence handling.

Do not add another BIM element type during this stage.

PASS gate:

- every hardening behavior has a reproducible test;
- failures terminate in the correct fail-closed state;
- no blind retry after `UNKNOWN_OUTCOME`;
- Stage 1 and Stage 3 regression remain PASS.

## Stage 5 — Add exactly one next BIM capability

Only after Stage 4 PASS.

Choose exactly one next capability from the already proven/appropriate command set.

Examples may include one of:

- Slab creation;
- Wall modification;
- another proven deterministic primitive.

Do not add several element types in the same stage.

For the selected capability:

1. define its typed request contract;
2. define read-back evidence;
3. define acceptance criteria;
4. prove single execution;
5. prove closed-loop correction where applicable;
6. preserve every prior regression.

PASS gate:

- selected capability has formal live PASS;
- closed-loop evidence is complete;
- all previously frozen stages remain PASS.

## Later stages

Continue by the same rule:

- one capability or one reliability property per stage;
- formal criteria before implementation;
- PASS before progression;
- all new ideas go to backlog until the current stage closes.

Suggested later sequence:

1. remaining BIM primitives, one by one;
2. materials/attributes;
3. undo/transactions/recovery;
4. security hardening;
5. Stage 0 integration;
6. normative Auditor integration;
7. higher project Stage Orchestrator;
8. performance optimization.

This order is guidance, not permission to skip gates.

## Explicit anti-sprawl rule

During any active stage, the following are prohibited unless they are necessary to make that stage PASS:

- adding unrelated element types;
- redesigning the whole executor;
- building UI/palette features;
- adding broad normative databases;
- performance tuning unrelated to the blocker;
- refactoring working code for style alone;
- implementing backlog ideas discovered during debugging.

Document such ideas in backlog and continue the current stage.

## Completion reporting

Every stage completion report must state:

- stage number and exact goal;
- branch and commit SHA;
- live-tested vs offline-tested items;
- acceptance criteria and verdict for each;
- model/project identity used for live test;
- GUID/evidence chain where applicable;
- regressions rerun;
- unresolved blockers;
- explicit statement whether the stage is `PASS` or `NOT PASS`.

No stage is allowed to be described as "basically done" or "almost complete" when any required gate is not PASS.
