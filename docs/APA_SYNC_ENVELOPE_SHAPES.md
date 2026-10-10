# APA Sync — raw Slack envelope shape analysis (privacy-safe)

## Objective

The owner ran a full Slack Socket Mode round trip and a restart test successfully. However the existing strict parser rejected 23 of 28 historical messages with `Expected APA_EVENT_V1 and one JSON code fence`. As a safety matter, the earlier diagnostics **did not log raw message content**, so it is not proven whether Slack has removed code fences, altered delimiters, changed the opening/closing wrapper, or added suffixes.

This second diagnostics layer adds only a **finite structural signature** for messages rejected with that exact reason:

- `fences`: none / one / two / many (number of literal triple-backtick markers).
- `begins`: fence / object / header / other (starting pattern after the strict prefix).
- `ends`: fence / object / other.
- `object`: yes / no (both curly braces appear in the tail).

No message bodies, JSON keys/values, Slack message timestamps, tokens, user names, or arbitrary substrings enter the result. It is suitable for console aggregation. Existing validation, SQLite schema, event ingestion and security gates are unchanged.

### Operator

Stop the older running coordinator cleanly with Ctrl+C, then start this branch in a **new isolated checkout** from the owner machine. It uses the same previously installed venv and same existing SQLite database. Record only the `APA Slack bootstrap` line. The new key `rejection_shapes` will show fixed-category counts for the 23 rejected messages.

Do not send tokens or full Slack payloads to ChatGPT. Keep existing records intact. Never change `main`, installed APX or PLN.

### Follow-up decision

Only after seeing the real `rejection_shapes` counts, implement narrowly scoped, explicitly tested Slack envelope compatibility if needed. A fallback must remain fail-closed: validate full JSON object, unique event ID, whitelist fields, evidence, phase/status; never accept arbitrary natural language as a task status. Maintain separate provenance for historical messages and do not overwrite the existing canonical GitHub research evidence.

**Evidence:** Owner-supplied local diagnostics 2026-10-11: `scanned=28, accepted=0, conflicts=0, duplicates=1, not_apa_events=2, ignored_subtype=2, rejected={"Expected APA_EVENT_V1 and one JSON code fence":23}`. Associated canonical report: [2026-10-11 live diagnostic](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-sync-live-bootstrap-diagnostic-20261011.md).

**Status:** source changes and offline CI to be verified; live shape results NOT_VERIFIED until the owner executes this new build.
