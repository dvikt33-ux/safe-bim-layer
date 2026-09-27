# FINAL DIRECT GITHUB EXECUTION AUDIT — AFTER PASS 180

Date: 2026-09-28
Scope: direct delivery of ChatGPT-generated Safe BIM jobs to the user's Archicad environment through GitHub, eliminating manual copy-paste while preserving local execution safety.
Status: final research synthesis for this workstream. No product code changes. No Live BIM writes.

---

# 1. Final objective

Target user experience:

```text
User in ordinary ChatGPT:
"Сделай коробку дома с крышей и перекрытиями"

ChatGPT
  -> reads current project snapshot
  -> generates typed Safe BIM job
  -> publishes job to private GitHub bridge

Safe BIM local service
  -> detects new job
  -> validates exact current project state
  -> compiles preview/sandbox/checkpoint

Palette
  -> shows ready job
  -> user presses one local Apply button

Safe Runtime
  -> performs verified writes
  -> publishes result/evidence

ChatGPT
  -> can read the result without manual log copy-paste
```

No PowerShell and no manual code transfer are required in the normal flow.

---

# 2. Final verdict

## Technically feasible
**YES.**

The system already possesses most of the architectural primitives:

- ChatGPT-side GitHub write capability;
- a proven local GitHub polling/de-duplication pattern in the existing AI dispatcher;
- Safe BIM durable SQLite jobs;
- single-flight and fail-closed execution logic;
- project identity and stale-context research;
- a planned local context cache and project-state snapshot.

The missing work is a bounded command-ingress layer, not a fundamental platform limitation.

## Safe to auto-execute arbitrary ChatGPT code
**NO.**

Raw Python/JSON command blobs must never become an unattended remote-code-execution path.

## Recommended v0.1
**Automatic delivery + automatic validation/preview + one local Apply click.**

This achieves the user's primary productivity goal—no copying or pasting—while preserving a clear physical-mutation boundary inside Archicad.

---

# 3. Chosen architecture

```text
                     PRIVATE GITHUB BRIDGE
                  ┌─────────────────────────┐
                  │ state/                  │
ARCHICAD ────────>│   current snapshot      │──────> ChatGPT
                  │                         │
                  │ jobs/                   │<────── ChatGPT
                  │   immutable job         │
                  │                         │
                  │ results/                │<────── Safe BIM
                  └────────────┬────────────┘
                               │
                      conditional polling
                               │
                               v
                   LOCAL BRIDGE QUEUE SERVICE
                   - GitHub authentication
                   - ETag/backoff
                   - once-only admission
                   - local SQLite queue
                               │
                               v
                        SAFE BIM PALETTE
                   - preview / checkpoint
                   - optional sandbox
                   - local confirmation
                               │
                               v
                        SAFE BIM RUNTIME
                   - project identity gate
                   - state-hash gate
                   - capability gate
                   - single-flight
                   - read-back/reconcile
                               │
                               v
                            ARCHICAD
```

GitHub is an asynchronous transport and audit surface, never the BIM execution authority.

---

# 4. Why GitHub polling is preferred first

GitHub webhooks require a publicly reachable HTTP receiver. A workstation behind NAT therefore needs an external relay/proxy or hosted receiver. That adds setup, security and availability dependencies.

For v0.1, poll one tiny queue-head/ref object with conditional HTTP requests and backoff.

Target behavior to benchmark:

- active Archicad session: 2–5 s polling;
- idle/no project: 15–60 s;
- failures: exponential backoff + jitter;
- immediate refresh after acknowledgement.

Do not pull/decode the full repository on every interval.

Webhook relay remains a later latency optimization, not a prerequisite.

---

# 5. Security boundary

GitHub credentials must not be embedded in:

- `.apx` binary;
- HTML/JS palette assets;
- committed config;
- recipe/job payload.

Use a localhost sidecar/bridge service and OS-protected secret storage.

Prototype authentication can use a fine-grained token restricted to one private repository and minimum required contents permissions.

Longer-term hardening can use a GitHub App with short-lived installation access tokens.

---

# 6. Job envelope

Research schema created:

`github_execution_job_v0_1.schema.json`

Mandatory concepts:

- protocol version;
- job ID;
- monotonic sequence;
- source project ID;
- source snapshot ID;
- project root hash;
- optional target GUID state hashes;
- payload class;
- execution policy;
- recipe hash;
- capability contract;
- optional mutation budget.

Payload classes:

- `SAFE_RECIPE`;
- `SAFE_SCRIPT`;
- `RAW_CODE`.

`RAW_CODE` is schema-forced to `RAW_CODE_REVIEW` and cannot be auto-executed.

---

# 7. Execution policies

## `READ_ONLY_AUTO`
Safe read/query job can run automatically.

## `PREVIEW_AUTO`
Compile and prepare preview/sandbox automatically; no BIM mutation.

## `WRITE_CONFIRM`
Default for ChatGPT-generated geometry in v0.1. Prepare everything automatically, then require one local `Применить` click.

## `WRITE_TRUSTED_RECIPE`
Future option only for certified recipe families with exact local checks and bounded mutation budget.

## `RAW_CODE_REVIEW`
Never unattended.

---

# 8. Stale-context race is solved locally

Canonical race:

```text
snapshot N -> ChatGPT job -> user edits model -> local intake
```

Required local resolution:

1. compare logical project ID;
2. compare snapshot/root hash;
3. compare exact target state hashes;
4. re-read relevant target neighborhood immediately before write.

Any mismatch:

`STALE_CONTEXT`

Physical BIM writes: **0**.

The result publisher sends enough mismatch evidence for ChatGPT to regenerate a fresh job.

---

# 9. Duplicate delivery cannot mean duplicate write

GitHub may return the same queue state indefinitely.

Local admission key:

```text
job_id
+ sequence
+ immutable received commit/hash
```

Persist admission in SQLite before execution.

The existing Safe BIM execution lock/single-flight layer remains mandatory. A repeated poll cannot re-dispatch the physical operation.

---

# 10. GitHub result publishing

Do not commit every runtime micro-state.

Local SQLite stores detailed transitions.

Publish coalesced external milestones:

- received/waiting for user if useful;
- stale/rejected status;
- terminal DONE/FAILED/CANCELLED/UNKNOWN_OUTCOME;
- optional coarse progress for long jobs.

A result contains at minimum:

- job ID;
- received Git commit/hash;
- verified local project ID;
- final status;
- physical dispatch count;
- created/modified receipt GUIDs;
- final state/evidence hash;
- failure/QA summary.

---

# 11. Offline behavior

GitHub outage must not make BIM execution unsafe.

- no connectivity -> no new remote admission;
- already-admitted local job remains governed by SQLite/runtime;
- terminal results queue locally and publish later;
- no mutation ever waits for GitHub to acknowledge it.

Wrong/opened project mismatch -> 0 writes.

Archicad closed -> remote job may be staged locally as `WAITING_PROJECT`, not executed against another project.

---

# 12. Reuse from existing Arena/GPT bridge

Concepts worth reusing:

- monotonic sequence/turn ID;
- local persisted last-seen state;
- exactly-once logical handling;
- malformed control data -> stop, never guess;
- GitHub as durable source of transport truth.

Do not reuse the same `agent-handoff/signal.json` as the BIM job queue. Agent handoff and physical BIM execution require separate schemas, permissions, retention and safety rules.

---

# 13. UI integration

Collapsed Safe BIM palette:

```text
SAFE BIM
Контекст: ✓ синхронизирован
Удалённое задание: #184
Готово к применению

[Посмотреть] [Применить] [Отклонить]
```

Arrival must not steal focus.

Expanded preview can show:

```text
Дом: коробка + перекрытия + крыша
Создать: 43
Изменить: 0
Удалить: 0
Checkpoint: ✓
Sandbox: ✓
QA: PASS

[ПРИМЕНИТЬ]
```

This preserves the compact-window requirement while eliminating manual code insertion.

---

# 14. Recommended implementation sequence

## Phase A — fake/read-only prototype

1. Create private bridge repository.
2. Implement `BridgeQueueClient`.
3. Conditional polling/ETag/backoff.
4. Parse `github_execution_job_v0_1`.
5. Persist admission in SQLite.
6. Show received jobs in Palette.
7. Publish fake/read-only result.

No BIM writes.

## Phase B — project binding

8. Connect `Project Context Bridge` identity/root hash.
9. Implement `STALE_CONTEXT` gate.
10. Validate capabilities/recipe hash/mutation budget.

Still use no-op/fake mutation.

## Phase C — Safe Runtime integration

11. Feed only validated typed recipes to existing runtime.
12. `WRITE_CONFIRM` only.
13. Checkpoint/sandbox/preview.
14. One controlled live job.
15. Independent audit.

## Phase D — trusted automation

Only after repeated certification consider `WRITE_TRUSTED_RECIPE` for narrow known recipe families.

---

# 15. Final risk register

Remaining implementation risks, not research unknowns:

1. GitHub credential provisioning/rotation on Windows.
2. Exact polling latency and API-rate behavior under real daily use.
3. Private bridge repository creation and permission design.
4. Crash window between local admission and palette/runtime handoff.
5. Synchronization of context snapshot vs command queue under rapid edits.
6. User experience for multiple pending jobs.
7. Result retention/cleanup policy.
8. Live certification that one delivered `WRITE_CONFIRM` recipe cannot bypass existing runtime safety.

These are prototype/test items, not reasons to reject the architecture.

---

# 16. Final conclusion

The requested no-copy-paste workflow should be implemented.

The correct target is not remote arbitrary code execution. It is a bidirectional Safe BIM bridge:

```text
Archicad -> project context -> ChatGPT
ChatGPT -> typed job -> Archicad
Archicad -> verified result -> ChatGPT
```

For v0.1, the best safety/productivity point is:

**automatic remote job delivery, automatic context validation and preview preparation, then one local Apply click before physical BIM writes.**

This eliminates the repetitive manual transfer step, keeps the palette compact, preserves local authority, and creates a clean path toward later fully automatic execution of only certified recipe families.
