# APA Sync — staged raw Slack envelope diagnostic

## Trigger / locally verified result

The owner's read-only native Slack Web API probe (2026-10-11) printed `scanned=28`, `apa_prefix=24`, `parse_valid=1`, and `fence_envelope_rejected=23`. Structural aggregation confirmed **20 historical messages** have two complete triple-backtick fence markers and the **exact** unlabelled Slack attribution `*Sent using* <@U0C90JE4WAC>`. The proposed parser patch in [PR #30](https://github.com/dvikt33-ux/safe-bim-layer/pull/30) added that form and passed 34/34 offline tests, but the owner's subsequent read-only probe still showed only **one** parse-valid event. Therefore the attribution form is proven, but **another envelope or JSON-shape mismatch remains**. Restarting the coordinator before diagnosing it is not warranted.

## This diagnostic

A new isolated `scripts.apa_sync.inspect_raw_envelopes` implementation adds `rejected_stage_shapes` to the previous read-only JSON summary. For events with exactly two fenced markers and the known, exact Slack attribution, it:

1. Classifies whether the prefix-to-opening-fence section has a linebreak, and whether the middle fence segment starts with `json`, `JSON`, a JSON object, or something else.
2. Attempts JSON decoding **only in memory** of the body between markers; classifies failure without logging parse exceptions or JSON content.
3. If decoding succeeds to a JSON object, constructs a temporary canonical fenced string and passes it through the existing strict `parse_event` validator. This diagnostic DOES NOT insert the object or modify the live parser, SQLite, GitHub controller task status, or Slack messages.
4. Emits only safe finite labels such as `has_linebreak;object_open;json_decoding_failed`, `has_linebreak;object_open;schema_rejected`, or `no_linebreak;object_open;valid_json_and_schema_envelope_mismatch`.

The original `counts` and `structural_shapes` remain available for comparison. The `rejected_stage_shapes` histogram must have no user-generated text or source substrings. Tests cover decode error, validation failure, envelope-only error and privacy of the resulting aggregate.

## Next step on owner's Windows PC

Use the existing isolated `APA-Sync-RawProbe` checkout to fetch the `feature/apa-sync-envelope-stage-probe-20261011` branch, switch to it and re-run the **one-shot, read-only** `inspect_raw_envelopes` module with local hidden `xoxb-` credentials. The current separate Socket Mode listener stays running. Share only `counts` and `rejected_stage_shapes`.

If the histogram shows `valid_json_and_schema_envelope_mismatch` on the 20 legacy messages, inspect the fixed structure of the preamble (without message bodies) and repair only the corresponding delimiter rule. If it shows `json_decoding_failed`, avoid blindly accepting data; audit actual legacy encoding in a limited, privacy-safe way. If it shows `schema_rejected`, keep the original validator and investigate supported historical schema fields; do not automatically promote PASS, treat unsupported claims as verified, or import arbitrary content.

## Controls and acceptance

- Offline CI and GitHub API readback required before owner runs.
- This step is diagnostics only; live event acceptance and SQLite historical backfill are **NOT_VERIFIED**.
- Do not change main, installed Archicad, PLN, APX, or existing branches; do not share tokens or raw Slack text.
