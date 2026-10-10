# APA Sync — root cause: Slack angle-wrapped HTTPS evidence (2026-10-11)

**Classification:** owner-confirmed **read-only LIVE diagnostic**, with explicit separation between publication/tests and SQLite import. Historical import remains **NOT_VERIFIED / BLOCKED** until a controlled local rerun.

## Source observation

The owner ran `python -m scripts.apa_sync.inspect_raw_envelopes` against the actual raw Slack Web API `conversations.history` using a locally entered private `xoxb-` bot token and an independent probe checkout; this is not a rendering from ChatGPT's Slack connector. The tool reads but does not modify Slack messages, SQLite or GitHub:

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
  "rejected_stage_shapes": {
    "has_linebreak;object_open;schema_rejected:evidence_url_not_https:slack_angle_link": 20
  },
  "scope": "APA channel, capped at 100 recent messages",
  "structural_shapes": {
    "fences=none;tail=not_applicable;tail_len=not_applicable;cr=not_applicable;invisible=not_applicable": 2,
    "fences=one;tail=other_suffix;tail_len=over-160;cr=no;invisible=no": 1,
    "fences=two;tail=empty;tail_len=zero;cr=no;invisible=no": 1,
    "fences=two;tail=exact_known_bare_mention_footer;tail_len=1-64;cr=no;invisible=no": 20
  }
}
```

## Established technical findings

1. Twenty historical events have valid **decodable JSON objects**, complete code fences and the exact unlabelled Slack attribution footer `*Sent using* <@U0C90JE4WAC>`. Those 20 fail **strict evidence URL validation**, because Slack encodes at least one `evidence_urls` value beginning `<https://` rather than a plain `https://` URL. This is proven by the privacy-safe validator-specific category, not a guess.
2. The original manually posted smoke event remains parse-valid in the live probe. Restart durability for `apa-live-smoke-20261011-002` at `seq=1` was previously verified; **no new SQLite changes** occurred from this standalone probe.
3. There are three further malformed protocol messages (two without code fences, one missing a closing fence), and four non-APA/ignored Slack messages. Those must **not** be auto-imported by broadening the parser.
4. The probe does not reveal whether *all* wrapped URLs use exactly `<https://...>` or also include label text such as `<https://...|label>`. Thus the narrow `<https://...>` normalization is a **candidate** that requires a new read-only live acceptance. It must fail closed for unknown syntaxes.

## Implementation candidate and controls

Published isolated [draft PR #33](https://github.com/dvikt33-ux/safe-bim-layer/pull/33) from `feature/apa-sync-slack-envelope-evidence-recovery-20261011` on top of PR #32:

- In `coordinator.parse_event`, normalize **only exact unlabeled angle-wrapped HTTPS URLs** in `evidence_urls` to their underlying URI before applying strict existing HTTPS/credential checks. Keep the allowlist of fields, mandatory source/summary/task/status/phase, limits, PASS URL evidence rule and conflict/deduplication logic.
- Accept the exact known Slack ChatGPT attribution directly after a completed fence or on a new line. No arbitrary trailing prose or HTML syntax accepted.
- Add negative cases for non-HTTPS, labeled, malformed, credentialed URLs, wrong sender and missing evidence; add positive parser, read-only prediction, normalized SQLite persistence and duplicate replay tests.
- No database schema migration, main/PLN/APX/installed Archicad changes, token logging, Slack mutation or automatic canonical `PROJECT_PLAN` approval.

## Next gates

1. Verify GitHub CI and code/test/doc readback for PR #33. **OFFLINE PASS only** if successful.
2. Owner reads raw Slack via the updated standalone probe in the **second PowerShell**, leaving the existing Socket Mode listener active. A successful result should show `parse_valid` increasing from 1 toward 21 and a corresponding reduction in `fence_envelope_rejected`. This is not yet claimed.
3. Only after step 2 is successful, stop old listener, start PR #33's tested code from a separate checkout using private tokens and unchanged local SQLite; capture bootstrap `accepted`, `rejected`, `duplicates`, `conflicts`.
4. Confirm original event remains at `seq=1`, audit phase-specific status conflicts, and repeat restart without duplicated rows.
5. Provenance audit of the remaining three malformed messages from original GitHub sources, not loose natural-language parsing. Transport PASS is **not** independent verification of historical technical findings.
6. Canonical governance: research artifacts require GitHub commit and readback, Slack ledger does not substitute for immutable reports nor autonomously mark `PROJECT_PLAN` tasks DONE.

**Status at writing:** root cause verified by user output, code candidate published, CI/live backfill pending evidence. The canonical report remains separate from feature PR and will be updated with actual acceptance results.
