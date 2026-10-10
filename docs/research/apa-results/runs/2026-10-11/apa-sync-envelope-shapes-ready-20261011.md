# APA Sync — raw Slack envelope diagnostics ready for local LIVE verification

**Date:** 2026-10-11. **Source evidence:** [owner-supplied local log](apa-sync-live-bootstrap-diagnostic-20261011.md). **Code:** [draft PR #26](https://github.com/dvikt33-ux/safe-bim-layer/pull/26), based on diagnostic PR #25, which builds on PR #24. Existing code branches and main remain unchanged.

## Motivating observation

The previous diagnostic recorded `scanned=28`, `duplicates=1`, `not_apa_events=2`, `ignored_subtype=2`, `rejected={Expected APA_EVENT_V1 and one JSON code fence: 23}`. The 23 messages are **not yet imported**. Exact raw Slack API envelope remains unknown. Displayed content in ChatGPT's Slack integration cannot establish the wire-format received by the separate Socket Mode bot.

## Delivered and independently verified

- Implemented fixed-category `rejection_shapes` histogram to distinguish counts of literal triple-backtick fences, starting envelope, ending envelope and presence of braces. Logs aggregate only finite labels, no message content/URLs/secrets.
- Added two synthetic tests for privacy-safe classification and counts.
- Published implementation, tests and operator documentation to dedicated feature branch and opened [draft PR #26](https://github.com/dvikt33-ux/safe-bim-layer/pull/26).
- GitHub API readback of code, tests and operator documentation: PASS.
- [GitHub Actions run 38087839977](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38087839977) **SUCCESS**. Unit job: **23/23 PASS**, new tests `test_bootstrap_reports_rejected_shape_counts` and `test_rejected_event_envelope_shape_has_fixed_safe_labels` both PASS; Windows launcher static job PASS.
- No parser acceptance relaxation, schema/database migrations, main/PLN/APX writes.

## Next required LIVE check

Ask the owner to stop current live coordinator using Ctrl+C and to clone branch `feature/apa-sync-fence-shapes-20261011` to a separate Windows folder; launch with the unchanged PowerShell script and local hidden credentials. Read **only** the `APA Slack bootstrap` aggregate dictionary containing `rejection_shapes`. Validate existing `seq=1` remains unchanged. Then implement a minimal and tested compatibility fix if the observed raw shape justifies it.

**Status:** OFFLINE 23/23 PASS, LIVE raw-shape inspection NOT_VERIFIED. Historical replay after format recovery remains BLOCKED. No inaccurate historic PASS promotion or automatic GitHub publication is claimed.
