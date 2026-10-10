# APA Sync — strict schema rejects 20 otherwise decodable historical Slack events

**Date:** 2026-10-11. **Provenance:** user-provided read-only Slack Web API diagnostic; supplementary connector-rendered Slack comparison is *not* proof of raw API byte structure. **Status:** LIVE raw Slack access PASS; historical ingestion BLOCKED / NOT_VERIFIED.

## Latest locally confirmed result

The user ran `python -m scripts.apa_sync.inspect_raw_envelopes` in their isolated raw Slack diagnostic checkout and received:

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
    "has_linebreak;object_open;schema_rejected": 20
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

### Established facts

- The 20 historical messages have a complete pair of code-fence markers and the exact raw Slack ChatGPT attribution `*Sent using* <@U0C90JE4WAC>`.
- All 20 decode as **JSON objects** with the read-only stage diagnostic, but **fail the original strict APA event validator even after re-encoding to a canonical envelope**. Therefore the attribution-only parser compatibility PR #30 cannot be declared sufficient to recover historical records.
- The one manually posted `APA-SYNC-SMOKE-01` LIVE/INFO event remains parse-valid in this latest raw probe.
- Two unfenced events and one with only a single fence remain malformed and intentionally excluded from automatic acceptance.
- In a separate read of Slack connector-rendered content, the same family of legacy JSON objects appeared to satisfy known required fields; this discrepancy hints at raw Slack value transformation but does **not** prove a specific reason. Slack link rendering is one hypothesis, not a verified root cause.

### Changes published

[Draft PR #32](https://github.com/dvikt33-ux/safe-bim-layer/pull/32) adds a privacy-safe finite `schema_rejected:<category>` signature to the read-only `rejected_stage_shapes` diagnostic. Categories distinguish unknown keys, invalid required fields, invalid status/phase, and evidence URL validation; for an HTTPS validation failure, it can detect known Slack `<https://...>` wrappers **without printing any URL**.

The new diagnostic **does not alter** the production parser, run live Socket Mode, write SQLite, change PROJECT_PLAN task statuses, or modify main/PLN/APX. Tests cover category specificity and absence of raw message content in output.

**Next gate:** verify offline GitHub CI, have the owner run the updated single-shot read-only probe from a separate PowerShell, capture only the aggregate `rejected_stage_shapes`, then implement a narrowly proven compatibility patch and verify a controlled replay with explicit status/conflict audit. Do not overclaim LIVE historical acceptance.

**Publication:** canonical `docs/research/apa-results/` with independent GitHub readback. This report is separate from the feature PR and preserves the historical trace even if the PR is closed.

## PR #32 CI acceptance and test correction

The first GitHub Actions run on the new diagnostic branch [38090796152](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38090796152) **FAILED** in two newly authored synthetic tests. The tests had mistakenly supplied otherwise correctly fenced messages that were rejected directly at schema validation; their `rejected_stage_shapes` therefore remained empty, because the staged fallback intentionally runs only for the **outer envelope** error. The test fixtures were corrected to deliberately fail the outer envelope while retaining decodable JSON. No production parser or SQLite changes were needed.

The corrected commit `1d7b488e8484e3d16b7a25c5fad3a7d13ceefbd9` passed [GitHub Actions run 38090858639](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38090858639): **38/38 unit tests PASS**, including both new tests `test_stage_validation_identifies_slack_angle_evidence_urls` and `test_stage_validation_separates_unknown_fields`. Windows launcher static check PASS. Jobs and detailed log lines independently fetched via GitHub API. The initial failed run is retained in the audit trail, not concealed.

**New live outcome:** still NOT_VERIFIED. Next action is one read-only raw Slack probe with the user's local bot token to receive static `schema_rejected:<reason>` categories for the 20 messages. The tool does not write back to Slack, SQLite, GitHub or Archicad.
