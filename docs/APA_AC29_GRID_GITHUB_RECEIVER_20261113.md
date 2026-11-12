# APA AC29 — GitHub receiver for reviewed 8×4 native grid

Status: **SOURCE IMPLEMENTED / CI AND WINDOWS INSTALLATION PENDING**. This branch extends the historical PR #139 receiver; it has **not** been installed on the user's laptop.

## Scope

The existing GitHub inbox `safe-bim-bridge/main/safe-bim-mailbox/apa-ac29/jobs` accepts two *additional* tightly scoped actions in a distinct envelope `APA_AC29_GROUP_GRID_JOB_V1`:

- `GRID_8X4_CHECK`: run exactly the pre-reviewed `apa_ac29_group_grid_live_8x4.py --check`, with no native model writes.
- `GRID_8X4_EXECUTE`: run exactly the same script with `--execute`, **one time only** and only if a successful `--check` receipt has been pinned by SHA-256 in the submitted GitHub job.

No arbitrary code, command, model path, destination, or shell parameter may come from GitHub. Fixed target is `C:\LocalAI\APA_Group_Acceptance\group-ac29-grid-8x4-20261018-01.pln`. The script source is pinned to PR #174 commit `4ef970a1cef798aafbece4649af926b9f8f4e57a` and Git blob `40e85e37232e3d6149f82178785c06d2910cc6d1`. The original 44-GUID PLN is **never** an execution target.

Before any invocation the receiver verifies the review script's Git blob, exact local Git HEAD, immutable stage receipt, source/scratch file hashes, source group, absence of previous attempts, and — for execution — exact preflight SHA-256 and expected 44→172 GUID plan. Every job is locally marked attempted before command execution; network or process failure cannot replay an uncertain native operation. Results go to the pre-existing `apa-ac29/results` directory.

## Grid envelope

```json
{
  "schema": "APA_AC29_GROUP_GRID_JOB_V1",
  "jobId": "grid-8x4-check-20261113",
  "action": "GRID_8X4_CHECK",
  "createdAt": "2026-11-13T00:00:00Z",
  "expiresAt": "2026-11-14T00:00:00Z",
  "target": "group-ac29-grid-8x4-20261018-01.pln",
  "sourceCommit": "4ef970a1cef798aafbece4649af926b9f8f4e57a",
  "preflightSha256": null,
  "authorizationRef": "USER_APPROVED_AC29_GROUP_GRID_8X4_TEST_20261113"
}
```

This is an **example**, not a queued job; expiration timestamps must be current when published. For the execution job, use a **different jobId**, action `GRID_8X4_EXECUTE`, and the **actual SHA-256** returned by the completed read-only check. No execution job should be queued in advance.

## Explicit limitations

1. Adding code to GitHub does **not** upgrade the already installed Windows receiver. It must be updated through a separately verified local deployment (including controller lock, backup, installation verification, restart, and readback), **not** by placing an arbitrary command into the old inbox.
2. The reviewed PR #174 one-shot runner deliberately does not call `SaveProject`. A successful native execution **does not** prove save/close/reopen persistence. This remains a separate acceptance criterion.
3. This draft adds no automatic retry, changes no existing PLN and does not change `safe-bim-layer/main` or the original stable receiver.
4. A GitHub Actions pass verifies source/tests; only a real Archicad 29 readback can establish LIVE acceptance.

Acceptance gate: isolated test copy, preflight PASS, pinned execute receipt, exactly one CloneNativeGroupV1, 32 groups and 128 newly created element/segment GUIDs, original 44 GUIDs preserved, real save-close-reopen verification if required for production claims.
