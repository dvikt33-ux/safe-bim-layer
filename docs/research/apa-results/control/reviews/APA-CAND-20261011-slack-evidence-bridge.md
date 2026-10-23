# TASK_REVIEW_V1 — APA-CAND-20261011-slack-evidence-bridge

```yaml
schema: TASK_REVIEW_V1
proposal_id: APA-CAND-20261011-slack-evidence-bridge
auditor_run_id: apa-slack-review-20261011-source-followup
source_substep_id: APA-P60.A02.S04
origin: audit
decision: DEFERRED
verified_sources:
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/3bdf572b27b27a27335f24336625777f189fec4d/scripts/apa_sync/socket_mode.py
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/3bdf572b27b27a27335f24336625777f189fec4d/scripts/apa_sync/coordinator.py
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/3bdf572b27b27a27335f24336625777f189fec4d/scripts/apa_sync/step_sync.py
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/tools/apa_controller/controller.py
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/.github/workflows/apa-research-publisher.yml
overlap_checked_against:
  - APA-P00.A03.S03
  - APA-P60.A02.S02
  - APA-P60.A02.S03
  - APA-P60.A02.S04
  - APA-P40.A01.S01
  - APA-P40.A01.S02
  - APA-P40.A01.S03
  - APA-P40.A01.S04
final_task_ids: []
plan_commit_sha: null
readback_verified: false
reason: >-
  No semantic duplicate in checked controller tasks, but the candidate requires
  approval for new executable bridge/runner, explicit deployment/auth boundaries
  and a narrowed safe evidence-notification design. Do not admit a new S-ID yet.
```

## Review finding: real gap, not a duplicate

The pinned Slack receiver `capture_event()` calls `EventStore.ingest()` and logs seq/conflict; it has no GitHub controller claim, no GitHub REST write, and no outbound acknowledgment. The local step CLI `step_sync.py` reads/post messages only upon invocation, with outgoing `--publish` explicit. The canonical GitHub publisher workflow triggers on canonical branch commits and publishes receipts/control projections; it has no Slack delivery step.

The user-measured live `seq=22`, `next_cursor=22`, `conflict=False` proves one ChatGPT→Slack→SQLite event, not an automatic status change. No 24/7 runner is established. The inspected controller revision **50** has no task with proposed `work_key=slack-ledger-evidence-to-github-notifications`; `APA-P60.A02.S05` is not registered.

## Reviewer architecture decision

**Keep one authority: `PROJECT_PLAN.json`.** Treat Slack as untrusted event/evidence transport. This candidate must NOT enable messages such as `PASS`, `INFO`, or `DONE` to change a canonical task state, create a lease, skip an audit, initiate unattended research, or publish a fabricated receipt.

Minimal acceptable implementation, if authorized:
1. **Inbound**: local read-only replay of the existing SQLite ledger using `/v1/changes?after=N`, durable cursor and strict event-ID dedup. Only emit evidence candidates after verifying a pinned *canonical GitHub* source: exact commit/blob SHA, matching report/receipt and controller artifact mapping. Raw `evidence_urls` are untrusted even when HTTPS; validating URL syntax does not authenticate provenance.
2. **Outbound**: on a genuinely verified canonical report/receipt, emit a narrow `INFO` event through the already supported Slack Bot/connector path, with proof links and immutable notification key. Use an outbox+retry or explicit at-least-once semantics, not an unprovable exactly-once claim. Suppress feedback loops by origin/direction and event-ID filtering.
3. **Policy**: retain the current trigger rule that only user-configured ChatGPT Scheduled Tasks may initiate research. The bridge is NOT a dispatcher, not a new publisher, and cannot modify task statuses. Never weaken receiver parser or create second controlling source.
4. **Runtime**: choose and explicitly authorize a host, credentials strategy and failure policy before executable code/auto-launch. Existing `socket_mode.py` process currently runs from a pinned non-canonical feature branch on Windows; codebase implementation must target its verified base and deploy only with owner approval.

## Missing preconditions for approval/admission

- **Authorization**: proposal says `requires_approval=true`; this follow-up request to continue audit is not a separately recorded approval to deploy or alter executable APA components.
- **Deployment design**: specify whether the bridge is a bounded extension to local Socket Mode worker, a post-commit publisher notification step, or an existing Scheduled Task callback; define owner of restart, reliability, and API authentication. Do NOT add another permanent research executor.
- **GitHub ↔ Slack data contract**: commit SHA/receipt pinning, Slack event schema, outbound source label, loop prevention, durable idempotency key, secrets handling, rate limits, and reconciliation after partial GitHub/Slack failure.
- **Acceptance controls**: fail-closed offline test suite for replay, invalid/non-GitHub evidence, mismatched SHA, duplicate events, conflicting states, socket disconnect, non-fast-forward GitHub race; independent LIVE isolated end-to-end with Slack send/readback and SQLite readback without task mutation.
- **Independent admission**: update the candidate with the agreed bounded host/permissions, then perform a separate authorized `TASK_REVIEW_V1` with `APPROVED` only after a real CAS commit of `PROJECT_PLAN.json` and controller CI/readback. Current review is `DEFERRED`, not approval.

## Change and evidence gates

No change to `main`, PLN, APX, working Slack receiver branch, task statuses, owners or leases. No new S-ID. Evidence in this review is source-level and prior user-observed local LIVE proof; NO new automatic GitHub↔Slack LIVE test is claimed. Future work must use the single existing controller and the established Slack ledger, with user authorization for code/deployment.
