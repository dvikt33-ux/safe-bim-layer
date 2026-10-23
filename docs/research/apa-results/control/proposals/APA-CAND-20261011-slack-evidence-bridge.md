# Proposed APA Slack evidence-to-controller bridge — independent review required

```yaml
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-20261011-slack-evidence-bridge
origin: audit
proposer_run_id: ad-hoc-source-review-20261011-slack-bridge
source_substep_id: APA-P60.A02.S04
proposed_parent_plan: APA-P60
proposed_action: APA-P60.A02
suggested_substep_id: APA-P60.A02.S05
work_key: slack-ledger-evidence-to-github-notifications
title: Safe Slack ledger evidence reconciliation and GitHub notification bridge
kind: INTEGRATION
priority: 1
depends_on: [APA-P60.A02.S02]
related: [APA-P60.A02.S03, APA-P60.A02.S04, APA-P00.A03.S03]
inputs: [ART-CONTROLLER, ART-PUBLISHER, ART-APA-SLACK-LIVE-TRANSPORT-E2E-20261011]
outputs:
  - Validated event-to-evidence bridge, reusing existing controller
  - Idempotent GitHub receipt notification into Slack
  - Offline negative/duplicate/cursor-resume test suite
  - Independent isolated LIVE E2E verification with readback
acceptance: Verified evidence-only Slack ingestion, idempotent cursor/replay and authenticated provenance; no change of task status by raw Slack. Independently verified report/receipt -> Slack notification -> local SQLite readback; controller tasks only mutate via existing CAS claim and authorization gates.
requires_approval: true
expected_mvp_benefit: Connect existing event ledger with existing GitHub project evidence without a second dispatcher or repeated manual relaying.
evidence_urls:
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-slack-controller-github-gap-audit-20261011.md
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-sync-live-message-delivery-e2e-20261011.md
risks: No always-on runner proof; channel text is untrusted; automatic task admission/claim forbidden from raw Slack; code modifications and local live testing require approval. Do not put tokens in repo.
```

## Duplication audit (initial, not final approval)
- `APA-P60.A02.S03`: CAS concurrency and lease tests; **not** a Slack input/output bridge.
- `APA-P60.A02.S04`: proposal approval policy; bridge proposals should go through this process.
- `APA-P00.A03.S03`: GitHub research publisher/recovery; new bridge MUST reuse it, not create a replacement publisher.
- `APA-P40.A01.S01–S04`: user Scheduled Tasks / 24h execution; this proposal is **not** a research scheduler and must not change `policies.trigger`.

## Two-stage engineering slice, not a new orchestration system
1. **Offline read-only bridge:** cursor-based `/v1/changes` ingestion with allowlisted event types, source SHA and receipt validation, audit records and retries; no writes to controller task status. Outgoing notifications only after verified canonical report/receipt exist; dedup by immutable event id.
2. **Gated LIVE acceptance:** isolated Windows launcher with user approval, synthetic existing-artifact reference (not fake DONE), Slack outgoing event readback, one matching SQLite event, zero duplicates/conflicts; verify controller `PROJECT_PLAN.json` task statuses, leases and claim refs unchanged. A separate independently claimed Scheduled execution remains the ONLY permitted task-claim path.

**Disposition:** `PENDING_INDEPENDENT_AUDIT`; `APA-P60.A02.S05` is provisional, absent from executable `PROJECT_PLAN.json` until reviewed and atomically admitted. No controller task claim, source branch code mutation, or Archicad Live claim from this proposal.
