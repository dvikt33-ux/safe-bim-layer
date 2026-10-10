# APA Sync — live Socket Mode → SQLite acceptance (2026-10-11)

**Scope:** APA Slack event coordinator for Archicad 29 project. **Evidence class:** USER-SUPPLIED_LOCAL_OUTPUT + INDEPENDENT_SLACK_READ. **Outcome:** LIVE PASS for one incoming event; other integration scenarios NOT_VERIFIED.

## Objective

Verify that a new explicit `APA_EVENT_V1` root message in the project Slack channel is received via Slack Socket Mode, persisted in the local SQLite event ledger and visible through the localhost HTTP read API.

## Environment and evidence

- Source implementation: [draft PR #24](https://github.com/dvikt33-ux/safe-bim-layer/pull/24) (`feature/apa-sync-live-readiness-20261010`). The test was run by the owner on Windows with this branch checked out.
- Slack channel: [#apa-research](https://app.slack.com/client/T0C847UM0A2/C0C886E1PGR), channel ID `C0C886E1PGR`.
- Slack evidence: [test event message `apa-live-smoke-20261011-002`](https://app.slack.com/archives/C0C886E1PGR/p1791666696416509), posted 2026-10-11 at approximately 00:11 MSK; message content independently observed using the connected Slack read API.
- The owner's local process log reported `A new session has been established`, `Bolt app is running!` and `Starting to receive messages from a new connection`.
- The owner's localhost `GET /health` returned `ok=True` and `mode=read_only_local`.
- The owner supplied the output of `Invoke-RestMethod "http://127.0.0.1:8765/v1/changes?after=0" | ConvertTo-Json -Depth 10`. The assistant cannot independently access the owner's localhost API or SQLite database.

## Observed data

Valid test event (user posted it to Slack):

```json
{"event_id":"apa-live-smoke-20261011-002","task_id":"APA-SYNC-SMOKE-01","status":"INFO","phase":"LIVE","source":"manual-test","summary":"Checking live Slack to SQLite delivery"}
```

Owner-supplied local HTTP API output included:

```json
{"changes":[{"seq":1,"event_id":"apa-live-smoke-20261011-002","task_id":"APA-SYNC-SMOKE-01","phase":"LIVE","status":"INFO","source":"manual-test","summary":"Checking live Slack to SQLite delivery","conflict":false,"slack_channel":"C0C886E1PGR","slack_ts":"1791666696.416509","ingested_at":"2026-10-10T21:11:34+00:00"}],"next_cursor":1}
```

This establishes the end-to-end receipt for **one** event at sequence 1 on the owner's machine. The earlier test message `apa-live-smoke-20261011-001` lacked the closing JSON fence and was not accepted.

The initial historical bootstrap logged `scanned=26, accepted=0, conflicts=0`. This is not a failure of live connectivity; existing channel messages may have different fence formats and/or exceed the input length bound. Historical backfill is NOT_VERIFIED.

## Acceptance matrix

| Gate | Result | Evidence boundary |
|---|---|---|
| Slack app installed and channel membership | PASS | Slack connector channel history showed bot join |
| Slack Socket Mode session establishment | REPORTED PASS | Owner's local launcher log |
| Local HTTP health | REPORTED PASS | Owner's PowerShell output |
| Valid new event present in Slack | PASS | Independently read Slack message |
| Local SQLite persistence + localhost `/v1/changes` read | USER-REPORTED LIVE PASS | Owner's API output: `seq=1`, `next_cursor=1`, `conflict=false` |
| Historical replay / recovery after restart | NOT_VERIFIED | Requires separate test |
| Duplicate delivery idempotence | NOT_VERIFIED in LIVE | Offline tests exist, not equivalent |
| Contradictory statuses and conflict recovery | NOT_VERIFIED in LIVE | Requires separate test |
| Ordinary ChatGPT threads receiving proactive mid-turn pushes | UNSUPPORTED | Threads must read Slack at next step |
| GitHub auto-publication of research results from SQLite | NOT_VERIFIED / NOT_IMPLEMENTED by this read-only API | Do not claim Slack automatically publishes to GitHub |

## Next measured objective

1. Check channel event parsing failures separately from transport, without logging sensitive Slack message contents.
2. Test restart and bounded historical bootstrap with the valid smoke event; verify idempotence (`seq` remains 1).
3. Audit and cautiously reconcile older `APA_EVENT_V1` messages; do not silently re-label historical technical statuses or evidence.
4. Confirm a second agent can read a newly committed cursor/state on its next explicit work step.

**Safety:** No tokens, private PLN contents or local path details are retained. No Archicad file changes, APX installs or main branch changes are claimed.
