# APA Publisher — all-three-stage safe Git CAS recovery (PR #39)

**Date:** 2026-10-11. **Existing task:** `APA-P00.A03.S03` (publisher-and-recovery; PARTIAL). **Scope:** GitHub publication recovery for report/index, receipt, and Controller generated-view stages. **Classification:** SOURCE_READBACK + OFFLINE_GIT_CI_PASS; **NOT DEPLOYED / NO CANONICAL LIVE PROOF**. No synthetic test is a real external concurrent canonical-branch deployment test.

## Root cause and repaired design

Canonical Actions concurrency serializes only its own workflow runs. Other GitHub writers can change `research/apa-verified-results-hub-20261010` while the Publisher is preparing outputs, causing a non-fast-forward rejection. The original Publisher sent separate direct pushes for immutable report+index, receipt, and generated Controller board, which could fail halfway through the run.

[Draft PR #39](https://github.com/dvikt33-ux/safe-bim-layer/pull/39) integrates safe recovery for **all three stages**, including the previously separately reviewed Controller helper from [draft PR #38](https://github.com/dvikt33-ux/safe-bim-layer/pull/38).

1. **Report + index (`publish_stage_retry.sh reports`):** validate current plan and inbox, rebuild report/index + pending expected hashes, attempt ordinary fast-forward push. If the remote advanced, confirm old commit is an ancestor, reject changes to executable code or edits/deletions to existing immutable reports and receipts, reset only an unpushed stage commit in ephemeral Actions, rebuild on latest canonical files and try again.
2. **Receipts (`publish_stage_retry.sh receipts REPORT_SHA`):** only after the existing GitHub REST proof of report bytes pinned at `REPORT_SHA`. Keep that exact report SHA across retries. Preserve existing matching receipt bytes/idempotency, reject conflicting receipt/provenance, fail closed when immutable report or receipt was modified, and retry only on genuine GitHub CAS advance.
3. **Controller projections (`publish_generated_retry.sh`):** revalidate latest `PROJECT_PLAN`/inbox and regenerate views; preserve remote commits, reject unverified code changes and permission denials. Uses the separately audited source and tests from PR #38.

All stage recovery is limited to **four normal fast-forward attempts**; no `--force`, main/master mutation, direct PLN/APX access, task status promotion, or second Controller. Existing independent GitHub REST verification of published report/index, receipt and Controller bytes is preserved at each original workflow boundary. Authentication/permission failures without remote advance are never treated as CAS races.

## Actual tests and independent evidence

- [GitHub Actions #38154416416](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38154416416): **SUCCESS attempt 1**, with direct job-log readback: **9/9** synthetic two-clone Git stage tests, **6/6** existing Publisher tests, **24/24** Controller tests (including prior five CAS/security regressions), **39/39** total. Bash syntax PASS; canonical Controller plan/inbox read-only validation PASS.
- Two-clone local bare-Git cases: report publish with no conflict; remote plan CAS advance then report/index rebuild; receipt CAS advance retaining verified report SHA; remote modified immutable report blocked; concurrent Publisher code mutation blocked; push denied by server hook and no remote advancement blocked; wrong branch blocked; another worker's **identical receipt preserved**; conflicting receipt hash **rejected**.
- Existing GitHub REST report/receipt validation tests run in Publisher unit suite. **No** actual real-user branch Actions execution of PR #39, merge or LIVE e2e is claimed.
- Source branch: `feature/apa-publisher-report-receipt-safe-retry-20261011`; integrated workflow code SHA [08f492d](https://github.com/dvikt33-ux/safe-bim-layer/commit/08f492d1ff816e6a1996fbb02a1e63f861bb4311); branch-based CI readback verified.

## Known limits and acceptance

- Code remains in **Draft PR #39**, not the active canonical Publisher. PR #38 has overlapping Controller-stage changes, so **PR #39 is the intended integrated candidate; do not merge both independently** without reconciling file diffs.
- Simulated Git race tests are strong offline evidence, **not proof against GitHub API policy, branch rules, or live multi-writer traffic after deployment**. The number of retries is bounded and may legitimately exhaust under sustained activity.
- Still-needed acceptance: independent source and permissions review, authorized merge into the research branch, live GitHub concurrent-run audit confirming the published receipts link to the immutable report commits, and separate monitoring/recovery heartbeat gates. The existing `APA-P00.A03.S03` stays `PARTIAL`, no new S-ID is admitted.
- Active Slack receiver, model bridge, Archicad PLN, installed APX and `main/master` unchanged.

**Next measurable milestone:** one canonical full-chain Actions run *after approved integration* with report/index → GitHub readback → receipt → GitHub readback → Controller board → GitHub readback, plus an intentional concurrent plan revision test. Until then claim OFFLINE_CI_PASS only.

## Post-merge canonical deployment verification — 2026-10-11

**This post-merge evidence supersedes the pre-merge NOT_DEPLOYED statements above.** Draft [PR #39](https://github.com/dvikt33-ux/safe-bim-layer/pull/39) was merged into **only** `research/apa-verified-results-hub-20261010`, GitHub merge SHA [26e708c43849944017f18d44e54536c2277902e8](https://github.com/dvikt33-ux/safe-bim-layer/commit/26e708c43849944017f18d44e54536c2277902e8). The merged workflow GitHub contents readback contains all three bounded publish commands.

**Real GitHub Actions post-merge [run #38155818514](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38155818514): SUCCESS, attempt 1.** Verified executed jobs, not just a CI badge:

- `Commit immutable reports with bounded retry` — SUCCESS.
- `Verify remote GitHub report and index bytes` — SUCCESS.
- `Commit verified receipts with bounded retry` — SUCCESS.
- `Verify remote GitHub receipts` — SUCCESS.
- `Commit latest controller projections with bounded retry` — SUCCESS.
- `Verify controller projections via GitHub REST` — SUCCESS.

Additionally [run #38155821730](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38155821730) — SUCCESS for merged offline regression workflow. Last pre-merge hardened metadata CI [#38155742294](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38155742294) — SUCCESS; existing receipt verification now rejects forged/incomplete `schema`, `run_id`, `report_path`, `status`, `indexed`, `index_mode`, `report_commit_sha`, `index_commit_sha`, and `readback_verified` even when SHA256 and idempotency key happen to match. Existing valid published receipts remain idempotently preserved on later branch heads.

**Verified level:** `CANONICAL_DEPLOYED_AND_THREE_STAGE_GITHUB_REST_READBACK_PASS`. A **real concurrent remote advance during this specific post-merge run was not observed**; actual live CAS conflict recovery remains `NOT_VERIFIED`, whereas two-clone offline real-Git races were verified in CI. The task `APA-P00.A03.S03` remains `PARTIAL` because continuous recovery/heartbeat/error-monitoring acceptance is broader than this implementation. Main/master, working PLN, APX, and Socket Mode service were not modified.
