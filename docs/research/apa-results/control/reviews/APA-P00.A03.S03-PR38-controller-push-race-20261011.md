# APA — independent source review of draft PR #38 (2026-10-11)

**Associated S-ID:** `APA-P00.A03.S03` — `PARTIAL`. **Scope:** Project Controller generated-view GitHub push race. **Decision:** `SOURCE_AND_OFFLINE_ACCEPTABLE_WITH_LIMITS`; **NOT_DEPLOYMENT_APPROVED**, **NOT DONE_PUBLISHED**. Not a new task, not a task claim, not an independent Windows/Archicad LIVE proof.

## Examined evidence

- [Draft PR #38](https://github.com/dvikt33-ux/safe-bim-layer/pull/38): [retry script](https://github.com/dvikt33-ux/safe-bim-layer/blob/fix/apa-publisher-controller-race-rebuild-20261011/tools/apa_controller/publish_generated_retry.sh), [synthetic actual-git tests](https://github.com/dvikt33-ux/safe-bim-layer/blob/fix/apa-publisher-controller-race-rebuild-20261011/tools/apa_controller/tests/test_publish_generated_retry.py), [new read-only CI](https://github.com/dvikt33-ux/safe-bim-layer/blob/fix/apa-publisher-controller-race-rebuild-20261011/.github/workflows/apa-controller-push-race-offline.yml).
- [CI run #38150011113](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38150011113): 23 Controller tests (initial four Git cases included), six Publisher tests, DAG/inbox validation PASS.
- **New independent adversarial gate:** [CI #38150622305](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38150622305) **SUCCESS**, including five synthetic bare-repo Git scenarios (non-conflicting, remote CAS advance, executable-code change, wrong repository, denied push without remote head change), six Publisher tests, existing Controller tests, safety/inbox checks and `bash -n`.
- New code changes: [push rejection classifier](https://github.com/dvikt33-ux/safe-bim-layer/commit/bea4da3224da67b5abe4ad2cd56a67a2ab7dce07) and [real rejected-push test fixture](https://github.com/dvikt33-ux/safe-bim-layer/commit/1b441da37e00432ee07f1fe954b31c210093cb90).

## Review findings

1. **Root cause confirmed:** Workflow-specific GitHub Actions concurrency does not serialize direct GitHub connector CAS writes. A normal `git push` at the final projection stage gets `non-fast-forward` if remote branch moves after checkout; multiple historical workflow attempts failed despite controller validation passing.
2. **Correctness of bounded retry:** New helper retrieves `FETCH_HEAD`, proves anchor ancestry before resetting any local, unpublished projection commit, validates code has not changed, then reruns controller validation and rebuilds projections from the latest canonical `PROJECT_PLAN.json`. No force-push. Four-attempt cap and fail-closed if tests/scope/permissions fail.
3. **Additional defect identified and repaired:** Initial PR treated any failed push as race (including permission rejection). New code requires **remote advancement** after `git fetch`; otherwise it blocks immediately with `push rejected without remote advancement`, preserving the original remote state. The negative regression installs a rejecting `pre-receive` hook on an isolated bare origin and verifies **exactly one failed send**; a first draft of the test wrongly generated no new commit and was corrected. Only the final CI pass counts for this gate.
4. **Authority and safety:** Read-only/offline CI; no `main`, user PLN, installed APX, native bridge, committed task-status field or non-target repository was altered. The script is not active in canonical branch until separately authorized PR merge.
5. **Important limit:** Fix applies **only to `Commit controller projections`**, not earlier report/index and receipt pushes. End-to-end three-stage concurrency and actual canonical post-merge recovery remain `NOT_VERIFIED`. Repeatedly rerunning canonical Actions is operational mitigation, not proof of complete repair.

## Decision and next work

The scoped solution is **acceptable for continued review**, not merge/deployment sign-off. Keep PR #38 draft until code ownership/branch policy permits an explicit merge and a live concurrent-push verification. Within existing `APA-P00.A03.S03`, the next distinct work slice is to design **first/second-stage** fail-closed recovery while preserving immutable report SHAs, receipt idempotency keys, and cross-stage GitHub verification. Do NOT blindly apply the projection-stage `git reset --hard` pattern to report/receipt stages without proving immutability.

No new S-ID is admitted and `APA-P00.A03.S03` stays `PARTIAL`. Independently verified means separately examined source + CI; not a separate human sign-off.
