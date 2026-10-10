# APA Sync — native Slack mention variant for ChatGPT attribution (2026-10-11)

## Incident and evidence provenance

The owner's stand-alone read-only raw Slack Web API probe (branch `feature/apa-sync-api-error-codes-20261011`) **successfully** read 28 channel messages without touching Socket Mode/SQLite and emitted:

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
  "structural_shapes": {
    "fences=none;tail=not_applicable;tail_len=not_applicable;cr=not_applicable;invisible=not_applicable": 2,
    "fences=one;tail=other_suffix;tail_len=over-160;cr=no;invisible=no": 1,
    "fences=two;tail=empty;tail_len=zero;cr=no;invisible=no": 1,
    "fences=two;tail=other_attribution;tail_len=1-64;cr=no;invisible=no": 20
  }
}
```

**Finding:** All 20 candidate historical messages have two triple-backtick code-fence markers, with a short `Sent using` attribution suffix that **does not contain the literal word `ChatGPT`**. Their unlabelled raw mention is a strong **hypothesis**, not yet byte-for-byte confirmed, because the privacy-preserving probe output classifies rather than prints the suffix. The connected ChatGPT Slack connector rendered many corresponding messages as `*Sent using* <@U0C90JE4WAC|ChatGPT>`. A raw Slack Web API mention may instead have the canonical `<@U0C90JE4WAC>` form with no display label.

The previous code [PR #27](https://github.com/dvikt33-ux/safe-bim-layer/pull/27) accepted only the connector-rendered form with the literal `|ChatGPT`; its live startup therefore **still rejected 23**. This is a confirmed LIVE block, even though 27/27 synthetic tests passed. Previous evidence: [historical reject report](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-sync-footer-live-rejection-pr27-20261011.md).

## Isolated minimal fix

This new branch adds **only** the literal known unlabelled mention alternative after a complete fenced APA JSON object:

- previously supported connector-labelled form: `*Sent using* <@U0C90JE4WAC|ChatGPT>`;
- newly supported native Slack mention candidate: `*Sent using* <@U0C90JE4WAC>`.

No generic "strip trailing text" or acceptance of unknown sender IDs/labels, missing closing JSON fence, malformed JSON, PASS without valid HTTPS evidence URLs, or unknown status/phase. The identity string is **not an authority claim**; all technical statuses retain their original source provenance and validation gates.

The standalone read-only raw Slack probe now has a separate finite safe bucket `tail=exact_known_bare_mention_footer`. This enables testing the hypothesis in a read-only pass before touching the running coordinator or its SQLite ledger.

## Acceptance workflow

1. Offline GitHub CI tests and code API readback must pass.
2. **No daemon restart yet:** In the existing dedicated `APA-Sync-RawProbe` checkout, fetch and switch to this new branch, execute `python -m scripts.apa_sync.inspect_raw_envelopes` with the privately entered bot token. The `structural_shapes` should count an `exact_known_bare_mention_footer` group; `parse_valid` should increase from 1. If it remains `other_attribution`, **STOP**: the raw suffix differs; do not restart for a speculative patch.
3. Only after successful read-only preflight, stop the current coordinator with Ctrl+C, then start this tested branch using `scripts/apa_sync/start_windows.ps1`. Keep existing `%LOCALAPPDATA%\SafeBIM\APA-Sync\events.sqlite3` intact. **Previously saved `seq=1` must remain present.**
4. Evaluate `bootstrap accepted/duplicates/rejected/conflicts`, `/v1/changes` and `/v1/state`. Expect *up to* 20 new valid historical messages, not an assumed hard-coded number. An imported Slack `PASS` is still a historical claim, not independent BUILD/LIVE acceptance.
5. Restart one final time to prove idempotence, then audit remaining three malformed messages separately from their original canonical GitHub evidence.

## Tests

Positive: labelled and unlabelled exact known attribution with compact/pretty JSON; negative: wrong sender, wrong label, extra trailing text, incomplete fence, PASS without evidence; idempotent bootstrap with both historical shapes.

## Safety and scope

No mutation of `main`, existing work branches, installed Archicad, PLN, APX or canonical PROJECT_PLAN status. No raw Slack content, token values or identifiers are printed by diagnostics. This code branch is subordinate to earlier diagnostic branches, and the evidence report is saved in canonical `docs/research/apa-results/` with GitHub commit and readback.

**Status on publication:** OFFLINE CI pending independent verification, read-only raw Slack compatibility and LIVE historical backfill **NOT_VERIFIED**.
