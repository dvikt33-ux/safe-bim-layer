# APA Slack ↔ GitHub receipt evidence bridge — offline POC, PR #37

**Date:** 2026-10-11. **Result:** SOURCE_AND_OFFLINE_CI_PASS / LIVE_NOT_VERIFIED / DEPLOYMENT_NOT_AUTHORIZED. This is a supplemental development artifact for owner audit, not a Scheduled claim or controller task DONE.

## Published implementation
- [Draft PR #37](https://github.com/dvikt33-ux/safe-bim-layer/pull/37), head `feature/apa-sync-receipt-evidence-bridge-poc-20261011`, base `feature/apa-sync-slack-envelope-evidence-recovery-20261011`. No changes to main or existing tested branch.
- New `scripts/apa_sync/receipt_bridge.py`: pinned GitHub content reads and publisher receipt validation; task-evidence registration, readback flags and immutable report SHA256; read-only cursor-based `127.0.0.1:8765/v1/changes` scan; deterministic `INFO/SOURCE` notification; explicit `--publish` only, existing `step_sync.after_step` reuse, bounded history dedup. No controller CAS/task changes or autonomous runner.
- New `tests/test_receipt_bridge.py`: fabricated offline fixtures, negative schema/SHA/path/unknown-task/dedup checks; no Slack tokens or real project data. Source README in `scripts/apa_sync/RECEIPT_BRIDGE_POC.md`.
- Updated only the PR branch's `.github/workflows/apa-sync-offline.yml` to actually execute new tests. Final source/CI change commit [8d4cef6](https://github.com/dvikt33-ux/safe-bim-layer/commit/8d4cef67648c83aa75f177467982ec240cce4749), connector file readbacks PASS.

## Independently checked CI
[GitHub Actions run 38144639897](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38144639897) — **SUCCESS, attempt 1**:
- Pre-existing `test_apa_slack_sync.py`: **44 offline tests PASS**.
- New `test_receipt_bridge.py`: **16 offline tests PASS** (direct job log).
- Python source compile PASS.
- Windows PowerShell launcher syntax PASS (no actual Windows deployment).

## Authority/scope limits
- Current canonical controller `PROJECT_PLAN.json` revision 51 at the time of this report: no `APA-P60.A02.S05` task; the [independent review](../..//control/reviews/APA-CAND-20261011-slack-evidence-bridge.md) is `DEFERRED`. The bridge is prototype code only; registration as an artifact does **not** approve deployment or change a task status.
- Existing Socket Mode on user Windows was not restarted, installed or tested with this PR. No real outbound GitHub receipt → Slack → SQLite LIVE E2E is claimed. The earlier user-observed seq22 result verifies the older Slack ingress path only.
- Send prevention is best-effort history dedup with a bounded scan; it does not claim exactly-once execution or durable transactional outbox. No automatic receipt polling or GitHub task trigger exists.
- Potential future hardening: authenticated access, host configuration approval, persistent outbox with crash recovery, end-to-end loop prevention, explicit local consent for LIVE and reconciliation; keep `PROJECT_PLAN.json` sole authority.

## Trace
PR `#37`, branch `feature/apa-sync-receipt-evidence-bridge-poc-20261011`, code commit `8300b69889938197d8409f717a8a13d72802c411`, tests commit `733d2b0bbe1a7e88d27b71704ce25e71831674cf`, docs commit `6b54c8ac12a311745fd727c6aae5b3a9f73eb13d`, CI wiring commit `8d4cef67648c83aa75f177467982ec240cce4749`.

## Additional source-backed integration check (GitHub Actions)

New PR-head commit [a8b11de](https://github.com/dvikt33-ux/safe-bim-layer/commit/a8b11deceb163857876de2136b7555fab479b3ed) added an actual pinned, published canonical GitHub receipt readback to the test workflow: controller snapshot commit `8af838f0ad96c98bfcdafab86ad318901a23ecd1`, `APA-P70.A01.S01`, registered receipt `APA-RUN-20261011-091905Z-p70-source-integration-map.json`.

[CI run 38144870385](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38144870385) is **SUCCESS on attempt 1**, including step `Pinned real GitHub receipt readback to Slack INFO dry-run` PASS; independent job-step readback verifies it ran. The test exercised real GitHub REST pinned content, source report checksum/registration, and creation of `INFO` event without Slack send. Existing 44 + new 16 offline tests and Windows launcher parsing also PASS.

**Revised evidence level:** GITHUB_PINNED_REAL_RECEIPT_DRY_RUN_PASS, OFFLINE_CI_PASS, **WINDOWS_AND_OUTBOUND_SLACK_LIVE_NOT_VERIFIED**. No claim that the bridge is enabled or automatically runs.

## Durable SQLite outbox and safe retry layer — independent CI evidence (2026-10-11)

Additional draft PR #37 changes on `feature/apa-sync-receipt-evidence-bridge-poc-20261011` implement separate opt-in `scripts/apa_sync/notification_outbox.py` and `publish_with_outbox()`, **without modifying the running Windows Socket Mode service or its `events.sqlite3`**.

- New isolated outbox persisted in `%LOCALAPPDATA%/SafeBIM/APA-Sync/receipt-outbox.sqlite3` by default, only when `--publish` is used. SQLite `BEGIN IMMEDIATE` protects per-event reservation. Existing `SENT` event IDs are not resent.
- Uncertain delivery or process crash after `IN_FLIGHT`: on the next explicitly requested attempt, scan Slack for the exact event ID and semantic payload; if found, reconcile the Slack timestamp as `SENT`, otherwise fail closed. **No blind retry**; exactly-once delivery not claimed.
- Same event ID with changed proof/status rejected. Bounded Slack channel read protects against silent partial history dedup; no automation/daemon, GitHub write, controller lease or task mutation.
- Code commit [d9629bb](https://github.com/dvikt33-ux/safe-bim-layer/commit/d9629bb8276a1b3dc0c54da8260f48e6916680af), outbox file commit [d32cd7d](https://github.com/dvikt33-ux/safe-bim-layer/commit/d32cd7d1c9ef625578eef7dad264937fdbb37e0f), outbox test commit [e3ca02e](https://github.com/dvikt33-ux/safe-bim-layer/commit/e3ca02e46c8c54b955db2e9085c9b3a8a1a62564), source readback confirmed. Updated [PR documentation](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-sync-receipt-evidence-bridge-poc-20261011/scripts/apa_sync/RECEIPT_BRIDGE_POC.md), commit [08a5970](https://github.com/dvikt33-ux/safe-bim-layer/commit/08a597088d3758a58d7806a6a296a9abce8d3b32).

### Independent CI

[GitHub Actions 38145391099](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38145391099) **SUCCESS on attempt 1**:
- Existing Slack receiver: 44/44 offline PASS.
- Receipt contract: 16/16 offline PASS.
- Outbox/crash/restart/duplicate/concurrency: 11/11 offline PASS.
- **TOTAL 71/71 unit tests PASS**, real pinned GitHub receipt INFO dry-run PASS, Windows PowerShell launcher syntax PASS.

### Unclosed gates
The actual new bridge has **NOT** sent a Slack message from Windows with this outbox; installed receiver remains untouched. Automatic GitHub→Slack push-trigger wiring, post-restart real Slack/SQLite readback, long-running reliability, transactional exactly-once and autonomous ChatGPT execution are **NOT_VERIFIED**. Candidate `APA-P60.A02.S05` remains `DEFERRED` and absent from executable `PROJECT_PLAN.json`. No new S-ID was claimed. Keep this implementation as draft until code security review and separately authorized LIVE deployment.

## Windows-native SQLite/outbox offline verification — CI acceptance

[GitHub Actions 38146011092](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38146011092): `SUCCESS`, attempt 1, checked jobs/logs:
- Linux coordinator-unit: 44 pre-existing Slack tests + 16 receipt validation tests + 13 outbox/replay/concurrency tests = **73/73 tests PASS**; pinned **real** canonical GitHub receipt → `INFO` dry-run PASS.
- Windows `windows-latest`: actual Python 3.11 execution of 16 receipt tests + 13 SQLite outbox tests = **29/29 tests PASS**; `WINDOWS_BRIDGE_OFFLINE_PASS`, Windows PowerShell launcher parse `POWERSHELL_SYNTAX_PASS`.
- Hardened `NotificationOutbox.mark_sent`: transition to SENT only from RESERVED/IN_FLIGHT/UNCERTAIN. Reconfirming the identical Slack timestamp is idempotent; changing it is rejected and the stored timestamp remains unchanged.
- Source commits: Windows test workflow [bd53dd6](https://github.com/dvikt33-ux/safe-bim-layer/commit/bd53dd6d26f36d0d05856311af76ce073d915623), timestamp lock [563a85f](https://github.com/dvikt33-ux/safe-bim-layer/commit/563a85fba1d1c566171022281cee23dcb927bed2), regression cases [d5ead94](https://github.com/dvikt33-ux/safe-bim-layer/commit/d5ead9466d0c34584e1f0fa4d4b1857a222112a6), [draft PR #37](https://github.com/dvikt33-ux/safe-bim-layer/pull/37). New PR documentation [0ed1e89](https://github.com/dvikt33-ux/safe-bim-layer/commit/0ed1e8906f6a7538f771dddb82f591dd384d5f90).

**Scope:** SOURCE + OFFLINE_CI_LINUX_AND_WINDOWS_PASS + PINNED_GITHUB_RECEIPT_DRY_RUN_PASS; **NOT** actual Windows laptop execution, outbound Slack LIVE, unattended GitHub↔Slack reconciliation, deployment, or task DONE. `APA-P60.A02.S05` was not admitted; controller tasks/leases untouched. Do not imply operational bidirectional sync from a synthetic/mocked Windows runner.
