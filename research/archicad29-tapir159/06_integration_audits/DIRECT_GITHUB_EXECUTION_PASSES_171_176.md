# DIRECT GITHUB EXECUTION — PASSES 171–176

Date: 2026-09-28

## Pass 171 — user interaction model

The desired UX can be nearly zero-touch:

1. User asks ChatGPT: “сделай коробку дома с крышей и перекрытиями”.
2. ChatGPT reads the latest project snapshot.
3. ChatGPT publishes a job.
4. Palette shows a compact notification: `Получено задание #...`.
5. Depending on policy:
   - low-risk/read-only job starts validation automatically;
   - write job opens preview or waits for one local confirmation;
   - explicitly trusted recipe may auto-enter sandbox, but not bypass safety checks.

The user should not copy code or use PowerShell.

## Pass 172 — command policy levels

Recommended per-job policy:

- `READ_ONLY_AUTO`: may run immediately.
- `PREVIEW_AUTO`: compile/validate/preview automatically, no BIM mutation.
- `WRITE_CONFIRM`: prepare checkpoint/sandbox and wait for one local click.
- `WRITE_TRUSTED_RECIPE`: future option; executes only a pre-certified recipe family with local preconditions satisfied.
- `RAW_CODE_REVIEW`: never auto-run.

Default for ChatGPT-generated geometry should be `WRITE_CONFIRM`, not fully unattended execution.

This still removes copy-paste while preserving user agency at the mutation boundary.

## Pass 173 — existing handoff reuse

The existing `arena-archicad-project` handoff protocol already has useful invariants:

- monotonic `turn_id`;
- target/source/status fields;
- locally persisted `last_turn_id`;
- de-duplication;
- durable GitHub source of truth;
- stop on malformed control data instead of guessing.

Direct Safe BIM jobs should reuse these principles, but must not reuse the same `signal.json` as a BIM execution queue. Agent coordination and BIM command execution have different threat models and retention needs.

## Pass 174 — acknowledgement/write amplification

Naively committing every transition (`RECEIVED`, `VALIDATING`, `PREVIEWING`, `RUNNING`, every step, `DONE`) would create unnecessary GitHub content.

Prefer:

- one immutable job commit from ChatGPT;
- local SQLite stores detailed runtime transitions;
- GitHub publishes only meaningful external milestones, coalesced:
  - `RECEIVED/WAITING_USER`;
  - terminal `DONE/FAILED/CANCELLED/UNKNOWN_OUTCOME/STALE_CONTEXT`;
  - optional periodic progress only for long jobs.

This reduces API writes and repository noise.

## Pass 175 — failure and offline modes

If GitHub is unavailable:

- current local Safe BIM jobs continue according to their already-admitted local state;
- no new remote job is admitted;
- physical BIM execution never depends on a later GitHub acknowledgement;
- results queue locally and publish when connectivity returns.

If Archicad is closed:

- local queue service may fetch and stage jobs;
- job remains `WAITING_PROJECT`;
- no attempt should auto-open or mutate an unrelated PLN unless the job policy explicitly supports project opening and identity is exact.

If the wrong project is open:

- `PROJECT_MISMATCH`, 0 physical writes.

## Pass 176 — race conditions

Critical race:

```text
ChatGPT reads snapshot N
 -> publishes job J
 -> user edits model to N+1
 -> local service receives J
```

Resolution is mandatory stale-context admission:

- compare logical project ID;
- compare project root hash or source snapshot generation;
- compare exact target state hashes;
- re-read target neighborhood immediately before write.

If mismatch:

`STALE_CONTEXT`, 0 writes, publish diff summary for ChatGPT to regenerate the recipe.

A job may never “best effort” apply to a changed model unless its recipe explicitly declares tolerant preconditions and the local compiler proves them.
