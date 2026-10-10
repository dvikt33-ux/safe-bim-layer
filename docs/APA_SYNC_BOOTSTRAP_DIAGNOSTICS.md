# APA Sync — safe historical bootstrap diagnostics

**Scope:** Slack `#apa-research` historical event import after verified live Socket Mode delivery on 2026-10-11.
**Code base:** PR #24 (Socket Mode launcher), with no changes to Archicad, PLN, APX, `main`, the canonical research branch, or existing research artifacts.

## Verified live observations

- The owner established Slack Bolt Socket Mode and received a genuine root `APA_EVENT_V1` message.
- The owner provided read-only local API output for event `apa-live-smoke-20261011-002`: `seq=1`, `next_cursor=1`, `conflict=false`, Slack timestamp `1791666696.416509`.
- After a clean restart, the same SQLite row remained at `seq=1` and the API `next_cursor` remained 1. The startup log showed `scanned=28, accepted=0, conflicts=0`.
- Thus a restart did not duplicate this smoke event. It does **not** prove why other historical messages were not imported.

## What this change adds

The existing bounded Slack history replay now logs aggregated counters:
- `scanned` — total returned channel messages;
- `accepted` — newly committed SQLite rows;
- `duplicates` — already committed identical event records;
- `not_apa_events` — irrelevant messages that do not start with the protocol prefix;
- `ignored_subtype` — unsupported Slack message subtype;
- `rejected` — counts grouped by existing **static parser exception reason** (e.g. missing JSON fence, over 5000 characters or invalid field), with no raw text, event identifiers, URLs or token values;
- `conflicts` — number of *newly ingested* conflicting rows.

**Parser rules and database writes remain unchanged.** In particular, historical reports exceeding the existing input length or failing evidence validation are **not** silently accepted, reclassified or truncated. If history is rejected, investigate the reason before proposing any compatibility fix. This diagnostic change should not modify the SQLite ledger except for any previously valid events that the existing historical replay would accept.

## Windows operator runbook

Leave the currently running APA Coordinator alone until ready to test. The diagnostics build is in a **separate code branch** and should be checked out separately; do not switch the existing working branch in place.

1. Stop the existing coordinator with Ctrl+C and wait until its process terminates, freeing localhost port 8765.
2. Clone branch `feature/apa-sync-bootstrap-diagnostics-20261011` into a **separate** folder such as `%USERPROFILE%\APA-Sync-Diagnostics`.
3. Run the existing `scripts/apa_sync/start_windows.ps1` launcher from the new clone. Previously installed isolated Python venv will be reused, and tokens will be prompted securely and used only within the launched process.
4. The startup line now includes the safe per-reason counters. Capture **only the aggregated `APA Slack bootstrap` line**, not environment variables, tokens or message contents.
5. Query `http://127.0.0.1:8765/v1/changes?after=0` to confirm the existing sequence remains accessible. Some additional rows may legitimately be imported by the unchanged historical replay; inspect for conflicts before downstream consumers treat them as authoritative.

**Pass criteria for diagnostics:** log contains expected counter keys; prior SQLite sequence remains intact; actual invalid reasons are captured without revealing message bodies. **NOT VERIFIED** until the user runs this build locally.

## Next technical gate

Use the observed counts to create a targeted parser compatibility proposal with tests. Preserve original event IDs, Slack timestamps, order and phase-specific status; do not turn SOURCE/OFFLINE into BUILD/LIVE PASS. Separate internal GitHub report persistence (canonical `docs/research/apa-results/`) from Slack transport: the read-only coordinator by itself does not push documents or advance PROJECT_PLAN task states.

## Tests

Run `python -m unittest discover -s tests -p 'test_apa_slack_sync.py' -v` offline. A new synthetic client test checks diagnostics, safe counters and bootstrapped retry deduplication. **CI status is not claimed until the new PR run completes.**
