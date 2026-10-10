# APA Sync — native Slack footer confirmed; historical envelope still rejected (2026-10-11)

**Provenance:** USER-SUPPLIED_LOCAL_READ_ONLY_OUTPUT. Distinguish actual Slack read-only check from offline synthetic unit tests. **Current status:** raw Slack read PASS; historical SQLite backfill **BLOCKED / NOT_VERIFIED**.

## Verified observation

Owner ran `python -m scripts.apa_sync.inspect_raw_envelopes` in a dedicated Windows `APA-Sync-RawProbe` checkout with a privately entered xoxb bot token. The tool successfully read the raw `conversations.history` stream without touching the running Socket Mode listener or SQLite, and printed:

```json
{
  "counts": {
    "apa_prefix": 24,
    "fence_envelope_rejected": 23,
    "ignored_subtype": 2,
    "non_event": 2,
    "parse_valid": 1,
    "scanned": 28
  },
  "read_only": true,
  "scope": "APA channel, capped at 100 recent messages",
  "structural_shapes": {
    "fences=none;tail=not_applicable;tail_len=not_applicable;cr=not_applicable;invisible=not_applicable": 2,
    "fences=one;tail=other_suffix;tail_len=over-160;cr=no;invisible=no": 1,
    "fences=two;tail=empty;tail_len=zero;cr=no;invisible=no": 1,
    "fences=two;tail=exact_known_bare_mention_footer;tail_len=1-64;cr=no;invisible=no": 20
  }
}
```

**Confirmed:** the 20 legacy messages with complete fences end with the **exact raw Slack suffix** `*Sent using* <@U0C90JE4WAC>`. The footer hypothesis from [PR #30](https://github.com/dvikt33-ux/safe-bim-layer/pull/30) was correct. However, **the new parser still reports only 1 valid event**, so there must be an additional envelope/JSON formatting incompatibility. It is unsafe to restart the existing live coordinator for historical backfill until that second cause is established.

No evidence yet of dropped or modified SQLite data: earlier baseline confirmed existing smoke event `apa-live-smoke-20261011-002`, `seq=1`, dedupe after restart. Since the owner has not rerun local `/v1/changes` in this most recent turn, preserve that as earlier verified evidence, not a fresh check.

## Remediation path

[Draft PR #31](https://github.com/dvikt33-ux/safe-bim-layer/pull/31) adds a **one-shot, privacy-safe staged raw-envelope probe** and synthetic tests on a new branch (no other project branch modified). It prints counts grouped by whether the two-fence JSON candidate is decodable and validates as an `APA_EVENT_V1` object under a canonical in-memory envelope; does not log source values, message IDs, URLs, or secrets.

Next: offline CI PASS, owner runs updated read-only RawProbe in the second PowerShell, submits only `counts` and `rejected_stage_shapes`. Based on those counts, select the narrowest strict parser adjustment, verify negative tests, then controlled historical replay and dedupe. For the 2 unfenced + 1 incomplete messages, do not bypass validation; treat separately in provenance audit.

**Do not** mark PROJECT_PLAN tasks DONE from Slack claims; keep source/offline/build/live gates distinct; no main, PLN, APX or installed Archicad changes.
