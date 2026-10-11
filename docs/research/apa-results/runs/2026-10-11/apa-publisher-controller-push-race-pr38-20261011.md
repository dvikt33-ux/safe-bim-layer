# APA Research OS — controller projection GitHub push race repair (PR #38)

**Date:** 2026-10-11. **Track:** existing `APA-P00.A03.S03` (Publisher, recovery and retry). **Level:** SOURCE_VERIFIED + OFFLINE_GIT_RACE_CI_PASS. **Not deployed / canonical LIVE NOT_VERIFIED.** This is an ad-hoc source repair, not a claimed Scheduled execution and not a task completion.

## Verified root cause

The canonical [publisher workflow](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/.github/workflows/apa-research-publisher.yml) uses three independent `git push` calls for report, receipts, and generated controller views. Its GitHub Actions concurrency group serializes only other instances of that workflow, not GitHub connector CAS writes to the branch. New commits by external researchers advance the remote head between generation and the last push. This repeatedly produced `! [rejected] HEAD -> research/apa-verified-results-hub-20261010 (fetch first)` at **Commit controller projections** while DAG tests and plan validation had already passed.

Documented examples from actual workflow logs include [#38139685031](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38139685031), [#38141454288](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38141454288), [#38143375383](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38143375383), [#38144743676](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38144743676), and [#38149052498](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38149052498). These needed rerun attempts before CI SUCCESS. No claim the final race is already eliminated in deployed canonical branch.

## Source changes, entirely isolated in draft PR

[Draft PR #38](https://github.com/dvikt33-ux/safe-bim-layer/pull/38) on `fix/apa-publisher-controller-race-rebuild-20261011`, targeting `research/apa-verified-results-hub-20261010`:

- `tools/apa_controller/publish_generated_retry.sh`: bounded four-attempt normal fast-forward publishing. On rejection, fetch remote, verify the last published immutable report/receipt **anchor remains an ancestor**, reject concurrent modifications to executable controller/publisher/workflow sources, ensure no unexpected local commits or dirty tracked checkout, discard *only* the unpushed generated-view commit **inside ephemeral GitHub Actions**, revalidate plan and inbox, regenerate controller board from latest source, retry normal push. No force push, no merge to main, no deletion of remotely accepted data.
- `.github/workflows/apa-research-publisher.yml`: replaces only the failure-prone `Commit controller projections` stage with bounded helper. Prior report/receipt stages unchanged. Existing remote controller projection SHA/hash verification remains.
- `tools/apa_controller/tests/test_publish_generated_retry.py`: reproducible two-client bare Git origin test for uncontended fast-forward, concurrent plan update, fail-closed concurrent code change, and wrong repository context.
- `.github/workflows/apa-controller-push-race-offline.yml`: read-only PR CI for Controller + Publisher suites and synthetic local Git race. Simulates canonical `GITHUB_REF` *only* within the Python validation test processes; live Publisher authority guard is unchanged.

## Independently verified tests

- **Local synthetic Git regression:** 4/4 PASS using actual `git init --bare`, two clones and forked shell/Python subprocesses. Observed first rejected push, successful second attempt, preserved rival `PROJECT_PLAN` revision and regenerated `HANDOFF`.
- [GitHub Actions #38150011113](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38150011113): **SUCCESS**, 23 Controller unit tests and 6 Publisher unit tests, canonical plan validation and inbox verification PASS; `bash -n` source parse PASS.
- Initial PR CI attempt [#38149943265](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38149943265) failed because the existing Publisher test requires `GITHUB_REF` to equal canonical branch, whereas the PR has `refs/pull/38/merge`. Test harness corrected to set simulated canonical ref for read-only unit processes; no runtime security gate weakened.

## Scope and remaining gates

- This fixes the **controller-generated-views publication race** when the proposal is deployed; report and receipt push stages are still unchanged. Do not claim a fully transaction-serialized three-stage publisher.
- Since the draft PR is not merged, **current canonical Publisher is unchanged**, and all 24/7/autonomous capabilities remain unproven.
- This artifact must not turn `APA-P00.A03.S03` from PARTIAL to DONE. Next acceptance: independent diff review of PR #38; then explicit authorized merge; real post-deployment concurrent canonical-branch Actions run and immutable receipts/readback. Continue to prioritize functional APA MVP.
- No user Archicad, active PLN, installed APX, main/master, Slack daemon, or existing feature branch modified.

## Independent source audit: distinguish rejected push from true CAS race

[Independent source review](../../control/reviews/APA-P00.A03.S03-PR38-controller-push-race-20261011.md), [commit 7e633a3](https://github.com/dvikt33-ux/safe-bim-layer/commit/7e633a3edca0206f540c483aca15fd8d276c2b52) examined the code and regression behavior **after** initial PR #38 CI.

**Additional fixed defect:** original retry classified all `git push` failures as remote CAS conflicts, including a permission/server rejection without any remote commit advance. The helper now fetches `FETCH_HEAD`, compares to the verified anchor, and immediately blocks if the remote did not advance. The added independent bare Git test installs a rejecting `pre-receive` hook **after** committing an intentionally stale projection, so the test triggers a real rejected push. The remote SHA must remain unchanged and a second retry is forbidden.

[CI #38150622305](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38150622305) **SUCCESS**: five synthetic actual-Git cases and the rest of the Controller and Publisher offline suites PASS, plus canonical plan and inbox read-only validation. Initial adversarial test had a fixture flaw (generated bytes identical to committed baseline) and failed; it was repaired before the PASS and is not counted as prior acceptance.

**Audit decision:** SOURCE_AND_OFFLINE_ACCEPTABLE_WITH_LIMITS; **not merge/deployment approval**. Canonical live workflow remains unchanged. Report and receipt stage push races are not yet addressed, and actual post-merge concurrent publisher recovery remains NOT_VERIFIED. Associated controller task `APA-P00.A03.S03` is still PARTIAL.
