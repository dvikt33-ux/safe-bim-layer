# APA Publisher — подтверждённая гонка Git push при параллельной публикации (2026-10-11)

**Evidence kind:** SOURCE_VERIFIED GitHub Actions job logs. **Work key:** existing `APA-P00.A03.S03` (`publisher-and-recovery`) — no duplicate task admission; task remains PARTIAL.  
**Branch:** `research/apa-verified-results-hub-20261010`. **No modifications** to publisher source, main, installed Archicad, PLN, APX or SQLite by this audit.

## Incident

[GitHub Actions run 38097725783](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38097725783) triggered on canonical research branch completed **FAILURE**. Its `publish` job reached `Commit controller projections`. Before this step, tests, `APA_DONE_PUBLISHED 7` and `APA_CONTROLLER_BUILT tasks=74 ready=16 published_v2=7 orphan=0` completed. Generated controller views were committed locally; the subsequent `git push origin HEAD:refs/heads/research/apa-verified-results-hub-20261010` failed with:

```text
! [rejected] HEAD -> research/apa-verified-results-hub-20261010 (fetch first)
error: failed to push some refs
hint: Updates were rejected because the remote contains work that you do not
hint: have locally.
```

This is a **non-fast-forward / concurrent-writer race**, not evidence that report JSON is malformed. Workflow concurrency protects competing runs in its group but **does not serialize direct GitHub file writes from ordinary ChatGPT against the workflow's checkout snapshot**.

## Recovery actually observed

The later [run 38098046479](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38098046479) and [run 38098175271](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38098175271) both completed **SUCCESS**. The latter's independently fetched job log includes:

```text
APA_DONE_PUBLISHED 8
APA_CONTROLLER_BUILT tasks=74 ready=17 published_v2=8 orphan=0
APA_CONTROLLER_READBACK_VERIFIED docs/research/apa-results/control/generated/CONTROL_BOARD.md
APA_CONTROLLER_READBACK_VERIFIED docs/research/apa-results/control/generated/HANDOFF.md
APA_CONTROLLER_READBACK_VERIFIED docs/research/apa-results/control/generated/STATE.json
```

The real current `PROJECT_PLAN.json` (revision 44) and regenerated `CONTROL_BOARD.md` were separately read back and show `APA-P00.A02.S03` PARTIAL, no active lease, and no orphan V2 manifests. **Current state recovered**, but reliability under sustained concurrent direct edits remains NOT_VERIFIED.

## Safe remediation candidate within existing task APA-P00.A03.S03

1. Treat commit/push stages as **optimistic CAS**, not an unconditional push. On non-fast-forward: fetch current canonical tip; inspect newly created content; replay only derived deterministic projection generation atop current tip; run controller validate/verify-inbox and do final readback again. Never force-push, reset away newer reports, or overwrite immutable V2 runs/receipts.
2. Keep retry bounded (e.g. maximum 2–3 attempts with backoff), detect immutable receipt/content conflicts before each attempt. Fail closed with explicit incident if not converged.
3. Test two writers in an offline synthetic repository: simultaneous direct file update + workflow projection commit; verify both results remain, no lost V2 report/index, valid `PROJECT_PLAN.json`, no duplicate receipt or orphan run, bounded terminal failure on deliberate conflicts.
4. Audit candidate implementation in a **new code branch + PR**, not direct in protected existing feature branches. Only after CI PASS and independent review consider deployment to canonical publisher workflow.

**Classification:** `LIVE_GITHUB_ACTIONS_RACE_OBSERVED`, `RECOVERY_BY_SUBSEQUENT_SUCCESSFUL_RUNS_CONFIRMED`, `CONCURRENCY_FIX_NOT_IMPLEMENTED`. This finding must not become a new duplicate S-ID: `APA-P00.A03.S03` already contains retry/recovery acceptance.
