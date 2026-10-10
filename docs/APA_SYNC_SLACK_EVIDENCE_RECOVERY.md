# APA Slack-to-SQLite historical recovery: wrapped evidence URLs

## Confirmed owner-side root cause (2026-10-11)

The owner ran the independent, privacy-preserving *raw Slack Web API* probe against channel `#apa-research` (not the Slack connector rendering). The local read-only result was:

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
  "rejected_stage_shapes": {
    "has_linebreak;object_open;schema_rejected:evidence_url_not_https:slack_angle_link": 20
  },
  "structural_shapes": {
    "fences=none;tail=not_applicable;tail_len=not_applicable;cr=not_applicable;invisible=not_applicable": 2,
    "fences=one;tail=other_suffix;tail_len=over-160;cr=no;invisible=no": 1,
    "fences=two;tail=empty;tail_len=zero;cr=no;invisible=no": 1,
    "fences=two;tail=exact_known_bare_mention_footer;tail_len=1-64;cr=no;invisible=no": 20
  }
}
```

This proves 20 historical messages carry decodable JSON and an exact known ChatGPT bare mention footer, but their strict schema validation fails for **HTTPS evidence URLs wrapped in Slack's angle-link format**, beginning with `<https://`. A previously suggested footer-only parser patch was insufficient. The **remaining question** is whether all wrapped URLs are exact unlabeled links `<https://...>` or include additional Slack display-label syntax; the privacy-preserving diagnostic did not reveal full raw URL strings. Therefore do not claim full live recovery until a read-only preflight passes.

## Minimal production patch

`scripts/apa_sync/coordinator.py` only:

- Accept the **exact** known signed attribution string after the *completed* fenced APA JSON object, with or without a newline before the footer: `*Sent using* <@U0C90JE4WAC>` (or the existing known `|ChatGPT` rendered-label form). All other trailing text remains invalid.
- When validating `evidence_urls` only, accept exactly `<https://URI>` and normalize to `https://URI` **before running the existing HTTPS host/credential checks**. Reject malformed, labeled, nested, non-HTTPS or whitespace-containing wrappers and preserve the original validator for task IDs, allowed keys, phase, status, source, length and PASS evidence requirements.
- Store the normalized link target as the canonical evidence URL; leave Slack `channel/ts` provenance, original event IDs and per-phase status unchanged. This preserves append-only SQLite deduplication, conflict logic and replays.
- Do not accept unfenced or incomplete event payloads. Do not convert source/offline evidence into LIVE or BUILD PASS.
- No database schema migration, token handling change, extra Slack permissions, GitHub plan auto-approval, Archicad connection, APX or PLN edits.

## Offline tests

Add strict positive cases (Slack-wrapped evidence, adjacent exact footer, multiline/compact JSON) and strict negative cases (alternate sender, arbitrary trailing text, labeled links, non-HTTPS, broken angle syntax, PASS without evidence, credentialed URL). Verify replay accepts one record and retries produce no duplicates, preserves original task phase and stores normalized HTTPS URLs. Add a read-only probe test predicting valid legacy acceptance without DB writes. GitHub Actions CI and code readback must pass before using this with live data.

## Owner-side acceptance: **read-only first, no restart**

In existing `%USERPROFILE%\APA-Sync-RawProbe` checkout, fetch and switch to `feature/apa-sync-slack-envelope-evidence-recovery-20261011`, then run `python -m scripts.apa_sync.inspect_raw_envelopes` with the existing local `xoxb-` bot token. **Leave the first PowerShell coordinator running.**

- Expected preflight: around `parse_valid=21` rather than `1`, and `fence_envelope_rejected` decreases from `23` toward `3`. The exact number must be observed, not assumed. Histograms remain sanitized.
- **Do not restart or write the SQLite ledger if the read-only preflight does not confirm valid parsing of most historical events.** Diagnose residual finite categories instead.
- After the preflight succeeds, cleanly stop the running listener, use an isolated checkout of the tested branch, restart with private `xoxb-`/`xapp-` tokens and preserve `%LOCALAPPDATA%\SafeBIM\APA-Sync` unchanged. Inspect bootstrap accepted/duplicate/rejected/conflicts counts and `/v1/changes?after=0` plus `/v1/state`.
- Confirm original event `apa-live-smoke-20261011-002` stays `seq=1`; historical records are new append-only sequence numbers. Review any state conflicts. A second clean restart must yield no new duplicates.
- Three known malformed messages (two unfenced and one incomplete fence) require separate source-linked/manual audit; do not auto-import.

## Critical governance

Transport/import success only certifies faithful collection of Slack event claims, **not** independent correctness of the claims. GitHub canonical `docs/research/apa-results/` remains authoritative for research artifacts and verifiable source evidence. The coordinator by itself neither uploads artifacts to GitHub nor updates the canonical `PROJECT_PLAN`.

**Status at creation:** confirmed raw-link root cause, code/test candidate published. LIVE read-only normalized preflight and SQLite historical replay **NOT_VERIFIED**.
