# APA Publisher — external hourly condition watch, 2026-10-11

**Task:** `APA-P00.A03.S03` (publisher-and-recovery). **Classification:** `SCHEDULER_ENABLED; GITHUB_LIVE_READBACK_PASS; ALERT_DELIVERY_NOT_VERIFIED`.

## Confirmed operational change

A ChatGPT Scheduled Task named **«APA Publisher: контроль сбоев»** was actually created and enabled on 2026-10-11 with `timing_mode=condition_watch`, schedule `RRULE:FREQ=HOURLY`. Its condition checks **only** the latest GitHub Actions run whose `name` is `APA Research OS automatic publisher` and `head_branch` is `research/apa-verified-results-hub-20261010`, using the GitHub Actions runs API with up to 100 recent branch runs. Alerts are requested when its latest run completes with failure, timed_out, cancelled, action_required, startup_failure; an active run exceeds 45 minutes since creation; or the GitHub check fails/returns unusable data. Healthy recent running or successful cases should remain silent. The task is **read-only** and has no GitHub/Archicad/PLN/APX/Slack write actions.

**Why external monitoring?** GitHub `schedule` workflows run from the repository default branch `main`; APA forbids modifying `main`. The merged reusable `tools/apa_publisher/watchdog.py` [PR #42](https://github.com/dvikt33-ux/safe-bim-layer/pull/42) has [17 passing offline unit tests](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38156708432), but remains an on-demand module because a research-branch GitHub cron cannot activate it. An independent ChatGPT hourly condition watch now supplies the scheduler.

The task service returned `is_enabled=true` and a nonempty `last_run_time` after creation; **the exact conditions checked on that future task run were not independently verified**. The user's account task metadata currently states `notifications_enabled=false` and `email_enabled=false` for this task. **Consequently no delivered push/email notification is claimed**. User notification settings must be enabled, then a genuine or safely simulated alert must be observed before escalating this alert gate.

## GitHub readback

- [Latest reviewed canonical Publisher #38157660584](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38157660584) **SUCCESS**, completed 2026-10-11T16:58:53Z.
- Two earlier failed runs [#38157569010](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38157569010) and [#38157185067](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38157185067) failed in a Controller unit test `test_approval_required_is_not_dispatchable` (`AssertionError False is not true`). The current Controller source test isolates approval from dependencies by clearing `depends_on`, and the later Publisher run is GREEN; these older failures are preserved as historical evidence, not falsely treated as the most recent run.
- [Merged three-stage Publisher PR #39](https://github.com/dvikt33-ux/safe-bim-layer/pull/39) includes retry and immutable readback and was previously verified with a live GitHub Actions full-chain run. **No actual post-merge concurrent CAS conflict is proven by the new watch.**

## Follow-up gates

1. Enable notification delivery for the watch in ChatGPT task/notification settings; confirm `notifications_enabled=true` through task metadata.
2. Prove one genuinely delivered alert without intentionally breaking or corrupting the canonical Publisher. Do not create an artificial canonical failure just to satisfy this test.
3. Independently exercise post-merge true concurrent GitHub CAS recovery in an authorized non-production setup or with passive observation of a real race.

**Do not change** task `APA-P00.A03.S03` from PARTIAL, assert `DONE_PUBLISHED`, or claim continuous Windows/Slack heartbeat. The monitoring scheduler is installed and enabled but delivery is not accepted yet. No main/master, working PLN, installed APX, or live Slack process changed.
