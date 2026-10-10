# APA Sync — restart persistence and bounded bootstrap observation (2026-10-11)

**Evidence:** owner-provided PowerShell/daemon output. **Classification:** USER-REPORTED LIVE PASS for restart persistence; historical reconciliation NOT_VERIFIED. Subsequent diagnostic code is published in [draft PR #25](https://github.com/dvikt33-ux/safe-bim-layer/pull/25).

## Previously confirmed baseline

[Live acceptance report](apa-sync-live-socket-e2e-20261011.md) records one verified Slack event `apa-live-smoke-20261011-002` (`task_id=APA-SYNC-SMOKE-01`, `LIVE/INFO`). The connected Slack reader independently confirmed this message existed in `#apa-research`; the owner independently checked the localhost API.

## Restart observation

Owner stopped the previous coordinator and relaunched `start_windows.ps1` from the isolated checkout of `feature/apa-sync-live-readiness-20261010`. The new process logged:

```text
2026-10-11 00:19:15,373 INFO apa.sync APA Slack bootstrap {'scanned': 28, 'accepted': 0, 'conflicts': 0}
2026-10-11 00:19:15,377 INFO apa.sync APA coordinator local read API at http://127.0.0.1:8765
2026-10-11 00:19:16,372 INFO slack_bolt.App A new session has been established
2026-10-11 00:19:16,372 INFO slack_bolt.App Bolt app is running!
2026-10-11 00:19:16,465 INFO slack_bolt.App Starting to receive messages from a new connection
```

Session identifiers and secret prompts deliberately omitted.

PowerShell `Invoke-RestMethod 'http://127.0.0.1:8765/v1/changes?after=0' | ConvertTo-Json -Depth 10` showed precisely one event with `event_id=apa-live-smoke-20261011-002`, original `seq=1`, `next_cursor=1`, `conflict=false`, `slack_ts=1791666696.416509`, and unchanged `ingested_at=2026-10-10T21:11:34+00:00`.

## Findings

- **PASS (user-reported live):** database persisted after restart, Slack Socket Mode reconnected, unchanged event is still accessible via read-only localhost API.
- **PASS for this smoke event:** startup replay did not add a duplicate to the ledger; `accepted=0` and `next_cursor=1`.
- **NOT_VERIFIED:** reasons why 27 other channel messages were not newly ingested. The bootstrap aggregate only reports newly accepted counts; a zero count cannot by itself distinguish duplicates, unsupported messages and parse errors.
- **NOT_VERIFIED:** comprehensive historical backfill, multiple conflicting statuses, proof of external downstream agents consuming cursor changes, automatic GitHub publication from coordinator.

## Next task

Run the non-content-logging bootstrap diagnostic counters from [draft PR #25](https://github.com/dvikt33-ux/safe-bim-layer/pull/25) after offline CI passes; collect only categorized aggregate counts. Write a narrowly scoped format compatibility patch if the observed reasons warrant one, and maintain strict provenance and event validation.

**Safety:** No main/PLN/APX changes, no secrets, no unverified technical PASS escalation.
