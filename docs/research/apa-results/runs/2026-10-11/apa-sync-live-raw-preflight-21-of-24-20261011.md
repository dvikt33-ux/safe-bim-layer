# APA Sync — LIVE read-only raw Slack preflight: 21 parse-valid events

**Date:** 2026-10-11 (owner local time, UTC+3).
**Classification:** VERIFIED — read-only Slack Web API parse preflight; NOT_VERIFIED — historical SQLite replay, conflict audit and restart deduplication.

## Owner-observed run

The owner used the isolated `APA-Sync-RawProbe` checkout on the new strict normalization branch `feature/apa-sync-slack-envelope-evidence-recovery-20261011`, running `python -m scripts.apa_sync.inspect_raw_envelopes` with the `xoxb-` token entered locally in hidden input. This fetches Slack channel history, parses locally and does NOT access SQLite, modify channel messages or restart the running Socket Mode process.

Actual user-reported console output:

```json
{
  "counts": {
    "apa_prefix": 24,
    "fence_envelope_rejected": 3,
    "ignored_subtype": 2,
    "non_event": 2,
    "parse_valid": 21,
    "scanned": 28
  },
  "read_only": true,
  "rejected_stage_shapes": {},
  "scope": "APA channel, capped at 100 recent messages",
  "structural_shapes": {
    "fences=none;tail=not_applicable;tail_len=not_applicable;cr=not_applicable;invisible=not_applicable": 2,
    "fences=one;tail=other_suffix;tail_len=over-160;cr=no;invisible=no": 1,
    "fences=two;tail=empty;tail_len=zero;cr=no;invisible=no": 1,
    "fences=two;tail=exact_known_bare_mention_footer;tail_len=1-64;cr=no;invisible=no": 20
  }
}
```

## Conclusion

**LIVE READ-ONLY PARSER COMPATIBILITY PASS**: 21 of the 24 messages carrying an `APA_EVENT_V1` prefix satisfy the strict parser with the patch. Before the fix only one message was parsed and 23 were rejected. Twenty legacy messages are now parse-valid with normalized evidence URLs and exact known Slack footer. The remaining three malformed protocol messages must not be auto-imported.

This preflight establishes syntax/schema acceptance against the actual Slack Web API but does NOT establish eventual sqlite insertion, absence of historical task conflicts, nor technical correctness of any reported research claims.

## Implementation and offline evidence

- [Draft PR #33](https://github.com/dvikt33-ux/safe-bim-layer/pull/33), branch `feature/apa-sync-slack-envelope-evidence-recovery-20261011`. Accept only exact `<https://URI>` (unlabeled) wrapped URLs in `evidence_urls`, normalizes to validated HTTPS URI; accepts only the known ChatGPT attribution after a complete fence. Existing ID/phase/status/PASS evidence checks and SQLite idempotency remain unchanged.
- [GitHub Actions run 38091580453](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38091580453) completed SUCCESS, **44/44 unit tests PASS** plus Windows launcher static PASS. Actual job logs and code readback were independently checked.
- No main, deployed Archicad, PLN, APX or canonical `PROJECT_PLAN` task-controller edits.

## Required next LIVE gate

1. Cleanly stop the single active coordinator with Ctrl+C in the **first** PowerShell; wait for prompt and process exit. No second Socket Mode daemon in parallel.
2. Take a rollback copy of `%LOCALAPPDATA%\SafeBIM\APA-Sync\events.sqlite3` **after stopping** the process (not a live unsafe file copy). Do not delete the original, the WAL, or other state. Preserve existing `seq=1` smoke receipt.
3. In a separate isolated fresh checkout of PR #33, launch the same `start_windows.ps1` with local hidden xoxb/xapp credentials; it points to the existing database and automatically replays recent Slack history.
4. Inspect `APA Slack bootstrap` counts, especially `accepted`, `duplicates`, `rejected`, `conflicts`. Expected up to 20 new accepted histories, but never claim 20 before observing local output.
5. Independently call `http://127.0.0.1:8765/v1/changes?after=0` and `/v1/state`: verify original event persists and assess conflicts and effective state by `task_id:phase`. Do not promote SOURCE/OFFLINE to BUILD/LIVE evidence.
6. A subsequent clean restart must return `accepted=0` and recognize previously ingested histories as duplicates.
7. Three incomplete/unfenced events remain blocked for manual provenance audit. Slack ledger replay is not GitHub publication and never auto-completes `PROJECT_PLAN` tasks.

**Status:** verified read-only preflight, controlled SQLite live replay PENDING.
