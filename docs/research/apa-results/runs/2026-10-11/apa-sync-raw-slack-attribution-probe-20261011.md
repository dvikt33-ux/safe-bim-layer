# APA Sync — raw Slack Web API attribution shape confirmed (2026-10-11)

**Evidence provenance:** USER-SUPPLIED_LOCAL_READ_ONLY_JSON; independent technical attribution is a hypothesis until probed with exact safe variant. This is a local read-only Slack SDK run, not a chat-connector rendering.

## Read-only CLI result

The user ran `python -m scripts.apa_sync.inspect_raw_envelopes` from the isolated `feature/apa-sync-api-error-codes-20261011` checkout against the Slack channel `#apa-research` via the bot token, entered locally with hidden input. The program completed successfully and emitted only safe categories; no Slack API error:

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
    "fences=two;tail=other_attribution;tail_len=1-64;cr=no;invisible=no": 20
  }
}
```

## Analysis

- Exactly 20 of the rejected historical messages have **both** triple-backtick fence markers. Their postfix is short (1–64 characters), includes the static token `Sent using` and does **not** include the literal `ChatGPT` according to the probe classifier. No carriage return or common zero-width-format character was detected in that trailing region.
- This is direct evidence against the older code's requirement that `|ChatGPT` appear in the suffix. The connected ChatGPT Slack connector displayed those events with `*Sent using* <@U0C90JE4WAC|ChatGPT>`, but the separate raw Slack API appears to use a different mention display. A plausible exact native variant is `*Sent using* <@U0C90JE4WAC>`. **The probe has not yet discriminated this variant from other short attributions, so exact raw suffix remains NOT_VERIFIED.**
- There are 2 rejected unfenced messages and 1 incomplete fence message. These should remain blocked for automatic history restoration.
- Existing Slack Socket Mode→SQLite event acceptance for one manually entered event and its restart persistence are independently recorded in earlier canonical reports. History restoration remains **BLOCKED**.

## Engineering continuation

[Draft PR #30](https://github.com/dvikt33-ux/safe-bim-layer/pull/30) is a narrowly constrained parser compatibility candidate plus offline synthetic tests, and a stand-alone **read-only hypothesis check**: the updated privacy-safe probe distinguishes exact unlabelled mention from other attributions. This read-only check should be run on the owner's Windows machine **before restarting the coordinator**, so a wrong hypothesis does not force another ineffective SQLite backfill cycle.

If raw probe reports `tail=exact_known_bare_mention_footer` and `parse_valid` rises, continue to controlled import; otherwise STOP and investigate. Do not accept arbitrary trailing text, missing fences, malformed JSON, invalid phases or PASS lacking evidence.

## Evidence/provenance boundaries

No credentials, raw Slack messages, author IDs or private paths are saved here. No Archicad, PLN, APX, main or canonical task-controller status changes. A source test is not a live data import PASS.
