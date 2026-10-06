# Stage 4 live hardening regression contract — 2026-10-06

Status: **READY_FOR_LOCAL_LIVE_RUN — IMPLEMENTATION NOT PUBLISHED**

Purpose: finish the current Closed Loop Stage 4 without re-inventing runtime safety that was already proven by BIMEXEC T4/T5/T6/T8/T9.

The current Stage 4 implementation was reported locally as branch `work/stage4-live-hardening`, commit `f297572`, with 128/128 offline tests and seven offline Audit Packs. At revision time that branch/commit is **not published in GitHub**, so this contract does not claim that implementation was inspected here.

The correct live project preflight has already been reported PASS for:
- Archicad endpoint: `127.0.0.1:19723`
- project: `NativeGeometry_Full_Test_20261004.pln`

No Stage 5 work is allowed until this contract is satisfied.

## Evidence boundary

A Stage 4 scenario may be marked PASS only from current-run evidence. Old BIMEXEC evidence is a **regression oracle**, not a substitute for the new run.

For every write-capable scenario record:
- exact project identity;
- model/generation fingerprint before observation;
- mutationAttemptId / attemptId;
- durable pre-write checkpoint;
- whether physical dispatch started;
- dispatch count;
- created/affected GUIDs when known;
- factual post-action read-back or explicit read-back failure;
- reconciliation classification when applicable;
- automaticRetry flag;
- final orchestrator state;
- before/after model element count and relevant geometry;
- Audit Pack path/manifest for the scenario.

Global invariant:
**no scenario may issue a second physical mutation merely because the first outcome is unknown.**

## Scenario matrix

### S4-01 — happy-path wall regression

Goal:
Prove Stage 4 did not break the already VERIFIED Stage 3 create/read-back/audit path.

Required behavior:
1. Observe current model.
2. Plan exactly one safe Wall mutation using the existing supported create_wall path.
3. Immediate pre-write state check is CURRENT.
4. Persist checkpoint and mutationAttemptId before dispatch.
5. Dispatch exactly once.
6. Read back exact created GUID and source Wall.
7. Geometry/length/joint/story invariants PASS.
8. Final result VERIFIED/PASS.

Acceptance:
- physical dispatch count = 1;
- created GUID is absent before and present after;
- factual read-back exists;
- no manual model correction;
- no stale fingerprint accepted.

Regression references:
- Stage 1 `27fc1026...`
- Stage 3 `2674e1eb...`

### S4-02 — stale before execution

Goal:
A plan made from stale state must never mutate Archicad.

Required behavior:
1. Observe and plan.
2. Change the model/fingerprint before the write fence.
3. Immediate pre-write check detects stale state.
4. Old plan is invalidated.
5. Executor/mutation gateway is not called.
6. Re-observation/replanning is required.

Acceptance:
- mutationAttempt may exist only as planning metadata; **physical dispatch count = 0**;
- final result is stale/reobserve/replan, never VERIFIED;
- no automatic mutation from the stale decision.

Regression reference:
- Stage 2 stale-replan fixture.
- BIMEXEC T6 principle: external drift cannot be ignored.

### S4-03 — UNKNOWN_OUTCOME, mutation actually applied

Goal:
A lost response after physical mutation must be reconciled without duplicate creation.

Fault injection:
Physical create reaches Archicad; response/result is lost or timeout is injected after dispatch.

Required behavior:
1. Durable pre-write checkpoint exists.
2. dispatchStarted=true and dispatchCount=1 are durable.
3. Orchestrator enters UNKNOWN_OUTCOME, not FAILED-with-retry.
4. Automatic retry is false.
5. Fresh read-only reconciliation locates exactly one matching applied result.
6. Classification = APPLIED.
7. Factual read-back proves the applied geometry.
8. Original mutation is adopted as the result.
9. No second create occurs.

Acceptance:
- total physical create dispatches = 1;
- one and only one matching created element;
- reconciliation = APPLIED;
- final progression may continue only after read-back.

Regression oracle:
BIMEXEC T4 live: `APPLIED_ADOPTABLE_BY_ANCHOR`, automatic retry false.

### S4-04 — UNKNOWN_OUTCOME, mutation not applied

Goal:
Retry is allowed only after absence is actually proven and a fresh plan is made.

Fault injection:
Transport outcome is unknown, but the physical mutation did not reach/apply to Archicad.

Required behavior:
1. UNKNOWN_OUTCOME recorded.
2. No immediate retry.
3. Read-only reconciliation proves `NOT_APPLIED` and `absenceProven=true`.
4. Original decision is invalidated.
5. Fresh observation is taken.
6. Planner runs again against current model.
7. Only then may a new mutationAttemptId be created and dispatched.

Acceptance:
- no same-attempt blind replay;
- second physical dispatch, if any, belongs to a new attempt after fresh observation/replan;
- evidence clearly distinguishes attempt IDs.

Regression oracle:
Old `safe_bim_runtime.py`: retry path is admitted only for `NOT_APPLIED + absenceProven=true`.

### S4-05 — ambiguous reconciliation

Goal:
If reconciliation cannot distinguish applied vs not applied, stop.

Required behavior:
- reconciliation classification is neither confidently APPLIED nor proven NOT_APPLIED;
- state becomes BLOCKED / WAITING_USER / equivalent fail-closed state;
- `retryAllowed=false`;
- no physical write after ambiguous reconciliation.

Acceptance:
- physical dispatch count remains the original count;
- final status is not VERIFIED;
- exact ambiguity evidence retained.

Regression oracle:
Old runtime: ambiguous outcome -> `_wait(... "ambiguous outcome; no retry")`.

### S4-06 — process crash after mutation dispatch

Goal:
Restart must reconcile the in-flight mutation without duplicate write.

Fault injection:
Kill process after physical dispatch and before successful verification/DONE checkpoint.

Required behavior:
1. BEFORE_WRITE checkpoint and dispatch admission are durable before kill.
2. Restart discovers RUNNING/UNKNOWN in-flight step.
3. No automatic replay occurs on startup.
4. Read-only reconciliation runs.
5. If applied, adopt exact existing result after factual read-back.
6. If not applied, follow S4-04.
7. If ambiguous, follow S4-05.

Acceptance for the applied variant:
- total physical create dispatches across pre-crash + post-restart processes = 1;
- original candidate is adopted;
- no duplicate GUID is created.

Regression oracle:
BIMEXEC T5 live: process kill after dispatch, human/reconcile evidence, automatic retry false.

### S4-07 — no-progress protection

Goal:
Repeated equivalent model + unresolved audit + equivalent planned action must terminate before endless mutations.

Required behavior:
- progress signature/fingerprint is durable per iteration;
- equivalent repeated state increments noProgressCount;
- threshold produces `BLOCKED_NO_PROGRESS` (or exact Stage 4 equivalent);
- no extra mutation after the blocking threshold.

Acceptance:
- termination occurs at configured threshold;
- no-progress blocker occurs before a larger max-iterations limit when both would apply.

Regression reference:
Stage 2 completion `d6ed3b07...`: no-progress blocks at iteration 2 with maxIterations 5.

### S4-08 — iteration limit

Goal:
A changing-but-never-accepted loop cannot run forever.

Required behavior:
- iterations remain distinguishable, so no-progress does not trigger incorrectly;
- once configured maximum is reached, final status is iteration-limit BLOCKED;
- no `VERIFIED` without all required acceptance criteria.

Acceptance:
- number of iterations/mutation attempts does not exceed configured maximum;
- final evidence records unresolved criteria.

### S4-09 — transport failure before physical attempt

Goal:
A pre-dispatch transport failure must not be mislabeled UNKNOWN_OUTCOME.

Fault injection:
Fail before mutation dispatch admission / before the command is physically sent.

Required behavior:
- dispatchStarted=false;
- dispatchCount=0;
- status is transport/block/failure-before-attempt, not APPLIED and not a mutation-unknown state;
- no reconciliation searches for an element that could not have been written;
- recovery requires fresh current-state validation before future execution.

Acceptance:
- physical mutation count = 0;
- no created GUID;
- never VERIFIED.

### S4-10 — read-back unavailable after mutation

Goal:
Command success is insufficient for VERIFIED.

Fault injection:
Mutation returns a GUID/success, but required factual read-back is unavailable or fails.

Required behavior:
- retain mutation receipt/GUID;
- state is NOT_VERIFIED / BLOCKED_BY_TRANSPORT / UNKNOWN_OUTCOME as appropriate to the exact evidence;
- never report VERIFIED from the command response alone;
- do not blindly retry the mutation;
- later read-only reconciliation/read-back may resolve the state.

Acceptance:
- final current-run state != VERIFIED while required read-back is unavailable;
- physical dispatch count = 1;
- no duplicate retry.

Regression references:
- BIMEXEC T7/T9 negative verification principles.
- old runtime: DONE requires `_has_readback`.

## Cross-scenario invariants

Stage 4 fails if any of the following occurs:

1. Any UNKNOWN_OUTCOME is automatically replayed.
2. A restart re-dispatches a RUNNING write before reconciliation.
3. An APPLIED reconciliation creates a second element.
4. A NOT_APPLIED retry reuses stale planning state without re-observation/replanning.
5. Ambiguous reconciliation permits a write.
6. Stale-before-write reaches the executor.
7. Failed/missing read-back is promoted to VERIFIED.
8. no-progress or iteration-limit states are bypassed.
9. Audit evidence cannot distinguish planning attempts from physical dispatches.
10. Current project identity differs from the preflight target.

## Minimal run policy

Because local Work/Codex quota is constrained:
- do **not** rerun broad research;
- do **not** rebuild existing Window/Door/Slab/Roof capabilities;
- do **not** rerun unrelated 128-test suites unless code changes make it necessary;
- run only the mandatory Stage 4 scenarios needed to produce current live evidence;
- reuse the existing implementation at local `f297572` if its tree is intact;
- publish implementation + evidence only after the run is complete enough to audit.

## Stage 4 completion gate

`STAGE4_VERIFIED = true` only when:
- S4-01 through S4-10 have current evidence;
- all required scenario verdicts PASS;
- every write attempt has durable attempt identity and dispatch evidence;
- zero blind retries occurred;
- all VERIFIED outcomes have factual read-back;
- Audit Packs verify;
- implementation and acceptance report are published to GitHub;
- independent review can reproduce the verdict from published non-LFS audit evidence.

Anything less remains `STAGE4_NOT_VERIFIED`.
