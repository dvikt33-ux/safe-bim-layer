# APA — START HERE for any new chat or agent

Authority: [PROJECT_PLAN.json](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json). Read [CONTROL_BOARD](CONTROL_BOARD.md), [TASK_CARDS](TASK_CARDS.md) and [RELATIONSHIPS](RELATIONSHIPS.md) and [THEMES](THEMES.md) before proposing work.

## Mandatory procedure

1. Select one eligible S-ID from the generated control board; inspect dependencies, related work and evidence.
2. Claim the task in PROJECT_PLAN.json via GitHub blob-SHA compare-and-swap: status CLAIMED, owner, lease_until, claim_ref. Never overwrite a competing claim.
3. Work only within the task scope and acceptance criteria. Check prior artifacts; do not repeat a work_key.
4. Commit PUBLISH_REQUEST_V1 inbox JSON with matching S-ID and executor. Unclaimed new runs are rejected.
5. Verify GitHub Actions success and DONE_PUBLISHED receipt; only then review acceptance, mark DONE_PUBLISHED, and clear claim.
6. If blocked, preserve findings, document blocked_reason, and return to the controller. Do not create a parallel plan.

## Parallel eligible work lanes

- CONTROL: none
- CONSOLIDATION: APA-P00.A01.S03, APA-P00.A02.S03, APA-P50.A01.S01
- RESEARCH: APA-P10.A01.S01, APA-P10.A01.S02, APA-P10.A01.S03, APA-P10.A02.S01
- BUILD: APA-P00.A03.S03
- INTEGRATION: none
- VALIDATION: APA-P00.A03.S01, APA-P00.A02.S04, APA-P60.A02.S03

## Safety

No autonomous ChatGPT research is started by this controller. 24/7 NOT_RUNNING.
No Deep Research/paid API without explicit approval. No main, PLN, APX, tested branch edits or merge.
Legacy reports are not fully mapped; see APA-P50.A01.S01.
