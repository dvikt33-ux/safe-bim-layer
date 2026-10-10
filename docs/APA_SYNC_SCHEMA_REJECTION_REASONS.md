# APA Slack event-history recovery — safe schema rejection reason diagnosis

## Owner's latest LIVE read-only evidence

At 2026-10-11, the locally deployed `APA-Sync-RawProbe` reported 28 history messages, 24 with `APA_EVENT_V1`, 23 strict `fence_envelope_rejected`, and 1 `parse_valid`. Importantly the further **non-mutating** diagnostic produced:

```json
{
  "rejected_stage_shapes": {
    "has_linebreak;object_open;schema_rejected": 20
  },
  "structural_shapes": {
    "fences=two;tail=exact_known_bare_mention_footer;tail_len=1-64;cr=no;invisible=no": 20
  }
}
```

For these 20 historical events, the raw Slack API has exactly two code-fence markers, an exact, known ChatGPT mention footer, and a **JSON object that successfully decodes**. But reconstructing a canonical fenced event from that JSON and calling the original `parse_event` still raises `InvalidEvent`. Thus simply relaxing Slack fence syntax would NOT recover those events correctly: the **strict schema/field validation** remains the immediate blocking gate.

The exact schema rejection cause is still unverified. Plausible categories include unsupported additional fields, required field mismatch, restricted status/phase, unsafe evidence URL format or length limits. No assumption is treated as a confirmed root cause.

## Delivered change (read-only diagnostic only)

New branch `feature/apa-sync-schema-rejection-reasons-20261011` builds on the tested existing historical probe but adds finite categorization of `InvalidEvent` reasons inside `_staged_fence_diagnosis`. Existing `rejected_stage_shapes` histogram will now include fixed suffixes, e.g.:

- `schema_rejected:unexpected_keys`
- `schema_rejected:missing_or_bad_event_id`
- `schema_rejected:evidence_url_not_https:slack_angle_link`
- `schema_rejected:pass_missing_evidence`
- `schema_rejected:other_validation_failure`

The `slack_angle_link` category is triggered **only** if a value of `evidence_urls` starts with the Slack `<https://` wrapper. It reports no URL or source text. This is important because the ChatGPT Slack connector may render URLs differently from the raw Slack API, and the failure class must be established before transforming them.

All output categories are drawn from a static allowlist; unknown error messages are reduced to `other_validation_failure`. **No event values, URLs, Slack message IDs, tokens, JSON fields or arbitrary exception messages are printed**. The real-time coordinator, production parser, SQLite, task controller, and GitHub publisher code are unmodified.

## Next gate

1. Independently verify Github CI and source readback.
2. Owner should use the existing isolated `APA-Sync-RawProbe` checkout (second PowerShell) and read the new branch, then run the one-shot module with the bot `xoxb-` token, entered privately. Keep the first Socket Mode process running; no need for a restart.
3. Share **only** `counts` and `rejected_stage_shapes` aggregate.
4. Investigate the single confirmed schema-error class. If evidence URL Slack wrapping is the cause, implement strictly validated transport-level unwrapping of known Slack URL syntax with negative tests. If unknown fields, require per-field review; never accept unknown keys blindly. If length caps, do not truncate evidence or report text.
5. Only after offline and read-only live acceptance of the proposed parser, restart once for historical replay in the existing SQLite ledger. Audit imported source vs OFFLINE vs LIVE results, conflicts and deduplication independently.

**No writes** to `main`, deployed Archicad, PLN, APX, or canonical PROJECT_PLAN task states. Research evidence is committed to canonical `docs/research/apa-results/` separately from this feature branch.
