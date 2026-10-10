# APA — START HERE for any new chat or agent

Authority: [PROJECT_PLAN.json](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json). Read [CONTROL_BOARD](CONTROL_BOARD.md), [TASK_CARDS](TASK_CARDS.md) and [RELATIONSHIPS](RELATIONSHIPS.md) and [THEMES](THEMES.md) before proposing work.

## Mandatory procedure

1. Select one eligible S-ID from the generated control board; inspect dependencies, related work and evidence.
2. On a scheduled ChatGPT trigger, atomically set status IN_PROGRESS, owner, lease_until and claim_ref=unique executor_run_id via GitHub blob-SHA CAS. Re-read the committed file before starting work.
3. If the CAS fails or task is already IN_PROGRESS/DONE_PUBLISHED, do not work. Select another eligible S-ID only after fresh readback.
4. Work only within task scope. Commit PUBLISH_REQUEST_V1 with matching substep_id, executor and executor_run_id; publisher rejects an unstarted or expired run.
5. Verify report, CI, receipt and acceptance. Then atomically set DONE_PUBLISHED and attach evidence; for partial results use PARTIAL, for failure BLOCKED with reason. Clear owner/lease/claim_ref.
6. Record status to GitHub and re-read it. If write/readback fails, report failure and do not claim completion.
7. Scheduler is created and managed by the user in ChatGPT Scheduled. Controller never starts research and cannot guarantee a scheduled task will run.

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
