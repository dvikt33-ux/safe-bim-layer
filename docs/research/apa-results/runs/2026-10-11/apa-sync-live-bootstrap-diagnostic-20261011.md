# APA Sync — live historical Slack bootstrap diagnostic (2026-10-11)

**Provenance:** USER-SUPPLIED_LOCAL_LOG; other GitHub/Slack artifacts independently read in companion reports. **Classification:** LIVE diagnostic observed; historical import remains BLOCKED/NOT_VERIFIED.

## Context
Following [one-event acceptance](apa-sync-live-socket-e2e-20261011.md) and [successful restart persistence](apa-sync-restart-dedupe-20261011.md), the owner executed the isolated, safe-counter diagnostic build from [draft PR #25](https://github.com/dvikt33-ux/safe-bim-layer/pull/25). GitHub Actions run [38087418984](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38087418984) finished SUCCESS: **21/21 unit tests** and Windows launcher static check PASS. These are offline tests, not live history recovery.

## Live boot log submitted by owner

```text
2026-10-11 00:25:22 INFO apa.sync APA Slack bootstrap {
  'scanned': 28,
  'accepted': 0,
  'conflicts': 0,
  'duplicates': 1,
  'not_apa_events': 2,
  'ignored_subtype': 2,
  'rejected': {'Expected APA_EVENT_V1 and one JSON code fence': 23}
}
2026-10-11 00:25:22 INFO apa.sync APA coordinator local read API at http://127.0.0.1:8765
2026-10-11 00:25:23 INFO slack_bolt.App A new session has been established
2026-10-11 00:25:23 INFO slack_bolt.App Bolt app is running!
2026-10-11 00:25:23 INFO slack_bolt.App Starting to receive messages from a new connection
```

The aggregate counts sum to 28. The existing event was recognized as a duplicate. **23 Slack messages were not admitted to SQLite because the strict fenced-JSON parser did not match the raw message text.** The diagnostic intentionally did not record raw Slack text, URLs or credentials, so the exact discrepancy is **not established** by the current counters. Displayed Slack connector messages often render fences, which may not represent raw Events API text identically.

## Verified and unverified

- PASS — live Socket Mode connection and start of event listening observed from local log.
- PASS — diagnostic build deployed and correct accounting seen for 28 items.
- PASS — existing event `apa-live-smoke-20261011-002` classified as duplicate on replay, not reinserted.
- BLOCKED — legacy event import: 23 strict format failures; original data not overwritten or reclassified.
- NOT_VERIFIED — precise raw Slack text shape (fence missing, altered, trailing suffix, rich-text conversion, etc.).
- NOT_VERIFIED — restoration of all historical events; event-level validity beyond parse shape; conflict outcomes.

## Next gate

Create a new, minimal diagnostic that counts **only safe structural features** of parser-rejected messages (e.g. presence of opening/closing backtick fences, event prefix, brace/object shape, trailing extra content), without storing or printing message bodies, IDs or URLs. Obtain on-device counts and add exact synthetic unit tests for proven raw shape. Only then permit a strict parser compatibility patch. Preserve Slack timestamps, event IDs, evidence and independent phase statuses; no broad acceptance of arbitrary text.

**Canonical publication:** committed/read back in the research hub. No main, installed Archicad, PLN or APX changes.
