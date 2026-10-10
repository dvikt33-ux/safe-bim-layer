# APA Sync — LIVE SQLite historical backfill completed, 20 events accepted

**Date:** 2026-10-11, 02:24:13 local Windows log (UTC+03:00).
**Evidence:** user-provided live Windows PowerShell coordinator console output.
**State:** LIVE PASS — 20 history messages accepted by the coordinator's SQLite ingestion bootstrap; conflict count zero. **Pending:** independent HTTP API state readback, individual task status/provenance review, second clean-restart idempotence and separate audit of 3 malformed Slack events.

## Preconditions confirmed in earlier owner-side runs

- The owner used an isolated checkout `feature/apa-sync-slack-envelope-evidence-recovery-20261011` and verified *read-only* raw Slack Web API parsing: **21/24 APA_EVENT_V1 messages parse_valid** out of 28 channel messages.
- The owner independently verified a SQLite rollback snapshot with `PRAGMA integrity_check` on source and snapshot, identical stored `(seq,event_id,payload)` rows: `SQLITE_BACKUP_VERIFIED`, `EVENTS: 1`, `ORIGINAL_SMOKE_PRESENT: True`. This is a pre-recovery backup; snapshot path/token are not published.
- [Draft PR #33](https://github.com/dvikt33-ux/safe-bim-layer/pull/33) passed [GitHub Actions run 38091580453](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38091580453), **44/44 offline tests PASS** and Windows launcher static PASS. It strictly normalizes `<https://...>` evidence URLs and accepts only the exact known ChatGPT footer. It does not broadly accept invalid JSON or unsupported statuses.

## Owner-observed live coordinator restart

The owner launched `scripts/apa_sync/start_windows.ps1` in fresh dedicated Windows checkout `APA-Sync-Live-Recovery`; bot/app tokens were entered with hidden prompts locally. The new live process reported at 2026-10-11 02:24:13 (user console, local time):

```text
APA Slack bootstrap {
 'scanned': 28,
 'accepted': 20,
 'conflicts': 0,
 'duplicates': 1,
 'not_apa_events': 2,
 'ignored_subtype': 2,
 'rejected': {'Expected APA_EVENT_V1 and one JSON code fence': 3},
 'rejection_shapes': {
   'fences=none;begins=header;ends=other;object=yes': 1,
   'fences=none;begins=other;ends=other;object=no': 1,
   'fences=one;begins=fence;ends=object;object=yes': 1
 }
}
APA coordinator local read API at http://127.0.0.1:8765
Listening to Slack events only in channel C0C886E1PGR
A new Socket Mode session has been established
Bolt app is running!
Starting to receive messages from a new connection
```

**Confirmed LIVE:** 20 newly accepted, 1 previously persisted duplicate, zero ingest conflicts reported by this bootstrap, 3 structurally malformed rejects, 4 non-APA/ignored messages; local read API and Socket Mode launched successfully.

**Scope note:** The reported `accepted: 20` reflects successful SQLite ingest calls in `bootstrap_channel`. This does not yet establish a separate `/v1/changes` API readback or `/v1/state` effective status for every task. The original smoke event `seq=1` was verified **before** recovery. A post-recovery API check is required to verify `seq=1` persistence, total event count (expected 21), absence of currently effective conflicts and phase/status distribution.

**Important chronological caveat:** historical records appended after an already saved live smoke event receive later monotonically increasing SQLite sequence values; `seq` is an ingestion cursor, not historical Slack-time order. Use `slack_ts` when reconstructing source chronology.

## Next gates

1. Keep the one running coordinator open. In **another** PowerShell run a read-only `Invoke-RestMethod` to `http://127.0.0.1:8765/v1/changes?after=0&limit=200` and `http://127.0.0.1:8765/v1/state`. Emit only safe counts and a small table of `seq,task_id,phase,status,conflict`, not raw `payload` and evidence URLs. Verify sequence 1 and total 21.
2. Inspect aggregate effective conflict count and phase/status distribution. `SOURCE` and `OFFLINE` records are claimed research evidence, NOT independent BUILD/LIVE PASS for Archicad.
3. Cleanly restart the same tested branch once. Expect `accepted=0`, `duplicates=21` and 3 malformed rejects, subject to no new Slack messages, then independently read back the API and record results.
4. Audit the 3 malformed messages separately against original immutable GitHub reports; do **not** loosen validation merely to inflate acceptance.
5. Reconcile the independent GitHub research registry and task controller with imported events under explicit source/provenance review. Do not auto-mark tasks DONE from Slack events alone.

## Change control

No `main`, existing development branches, Archicad 29, PLN, APX or master PROJECT_PLAN changed by this bootstrapped recovery. Canonical report stored in `docs/research/apa-results/runs/2026-10-11/`; GitHub readback must confirm publication. Transport and persistence recovery success does **not** establish autonomous ChatGPT research, auto-push from chats or a complete Archicad project interface.

## Owner-verified independent LOCAL HTTP API readback (2026-10-11)

**Gate result: LIVE HTTP API READBACK PASS.** After the successful 02:24 Socket Mode bootstrap, the owner independently ran the following read-only requests from another PowerShell while the coordinator remained running:

- `GET http://127.0.0.1:8765/v1/changes?after=0&limit=200`
- `GET http://127.0.0.1:8765/v1/state`

Only counts and a safe table of `seq, task_id, phase, status, conflict` were shared. The actual output:

```text
EVENTS_TOTAL: 21
ORIGINAL_SMOKE_PRESERVED: True
STATES_TOTAL: 16
EFFECTIVE_CONFLICTS: 0
NEXT_CURSOR: 21

LIVE, INFO        1
OFFLINE, PASS     4
SOURCE, INFO     13
OFFLINE, INFO     2
LIVE, BLOCKED     1
```

All 21 event rows were displayed; every row's `conflict=False`. The original `apa-live-smoke-20261011-002` remains at `seq=1`. The final persisted row `seq=21` is present. Among the 16 effective task/phase states, the API reports `EFFECTIVE_CONFLICTS=0`. Important: 16 is the number of distinct task/phase state keys (21 events include successive informational updates), **not** an independent count of all historical research tasks or proof of semantic deduplication. `APA-SYNC-LIVE-01:LIVE` remains **BLOCKED**; `APA-SYNC-LIVE-READINESS-01:OFFLINE` is PASS only in OFFLINE, with no promotion to Archicad BUILD/LIVE.

### State transitions and remaining gates

| Scope | Result | Evidence |
| --- | --- | --- |
| Slack Socket Mode connection | LIVE_PASS | owner-local 02:24 daemon log |
| Strict historical parser on raw Slack | LIVE_READ_ONLY_PASS | `21/24` parse valid, earlier raw probe |
| SQLite history bootstrap | LIVE_PASS | `accepted=20, duplicates=1, conflicts=0` |
| SQLite post-backfill readback | **LIVE_PASS** | `EVENTS_TOTAL=21`, cursor 21, seq1 preserved |
| Derived state query | **LIVE_PASS** | 16 task-phase state keys, zero effective conflicts |
| New history events verified after another daemon restart | **NOT_VERIFIED** | requires clean stop/restart: expected accepted=0, duplicates=21, rejected=3 if unchanged history |
| Three malformed legacy messages | **BLOCKED / pending provenance audit** | two missing fences, one incomplete closing fence |
| Automatic ChatGPT research and publication to GitHub | **NOT_VERIFIED / not delivered by Slack ledger** | no claim of autonomous chat exporter or 24/7 research agent |

**Audit linkages (existing controller S-IDs; no unauthorized dispatch):** `APA-P00.A02.S03` (legacy evidence reconciliation) covers source-linked review of remaining malformed messages; `APA-P00.A02.S04` (publication completeness) covers verifying each claim against GitHub immutable report + receipt before marking anything DONE. Controller `PROJECT_PLAN.json` revision/status/claims were NOT changed: this run did not obtain a formal controller claim and LIVE message transport is not task completion.

**Next operator action:** cleanly stop the running coordinator with Ctrl+C, restart the same tested checkout (not another daemon in parallel) and capture the fresh `APA Slack bootstrap` counts. Then re-read the local read-only API to ensure 21 rows and preserved seq1, and publish the final receipt. **No new Slack messages should be sent just to test dedupe.**

## Owner-verified second clean restart: idempotence PASS (2026-10-11 02:33 local, UTC+03:00)

**Verification provenance:** exact owner-supplied PowerShell Socket Mode logs from the second launch using the same tested `APA-Sync-Live-Recovery` checkout and existing SQLite file. The 02:33 bootstrapping was executed after the previous successful 02:24 first history import and 21-event API readback.

```text
2026-10-11 02:33:01,669 INFO apa.sync APA Slack bootstrap {
 'scanned': 28,
 'accepted': 0,
 'conflicts': 0,
 'duplicates': 21,
 'not_apa_events': 2,
 'ignored_subtype': 2,
 'rejected': {'Expected APA_EVENT_V1 and one JSON code fence': 3},
 'rejection_shapes': {
   'fences=none;begins=header;ends=other;object=yes': 1,
   'fences=none;begins=other;ends=other;object=no': 1,
   'fences=one;begins=fence;ends=object;object=yes': 1
 }
}
2026-10-11 02:33:01,672 INFO apa.sync APA coordinator local read API at http://127.0.0.1:8765
2026-10-11 02:33:01,672 INFO apa.sync Listening to Slack events only in channel C0C886E1PGR
2026-10-11 02:33:02,592 INFO slack_bolt.App A new session has been established
2026-10-11 02:33:02,592 INFO slack_bolt.App Bolt app is running!
2026-10-11 02:33:02,652 INFO slack_bolt.App Starting to receive messages from a new connection
```

### Acceptance results and precise limits

- **HISTORICAL REPLAY IDEMPOTENCE: LIVE PASS.** With unchanged 28-message Slack history, the second bootstrap recognized all 21 parse-valid messages as duplicates, accepted zero new rows and raised zero conflicts. No second copy of the historical records was created by that bootstrap.
- **STORAGE API BEFORE RESTART: LIVE PASS.** The previous separate `/v1/changes` and `/v1/state` requests had independently read 21 rows, preserved `seq=1`, cursor 21, 16 distinct task-phase keys and zero effective conflicts.
- **API AFTER SECOND RESTART: pending fresh readback.** The new daemon reports a successful API bind, but a separate `GET /v1/changes` call since the 02:33 restart has not yet been shown by the owner; do not fabricate it. An optional read-only API check will close that final post-restart data-persistence gate.
- **3 malformed APA protocol messages: source audit pending.** Exactly two lack a proper pair of fences and one has an incomplete fence. They remain intentionally rejected; do not permit unrestricted parser repair.
- **Scope of completion:** Slack history bootstrap, deduplication, persistence readback from the first restart, and Socket Mode connection have met their measured acceptance gates. This does **not** establish continuous 24/7 execution, automatic publication of normal ChatGPT research to GitHub, full evidence provenance verification, or Archicad BUILD/LIVE readiness.

### Controller mapping and next allowed work

The canonical controller at revision 35 includes existing `APA-P00.A02.S03` (`work_key=legacy-evidence-dedup`, READY) and `APA-P00.A02.S04` (`work_key=publication-completeness-audit`, PARTIAL). These already cover reconciliation of the three rejected events with immutable GitHub reports and validating source claims before admitting them to the research corpus. No duplicate S-ID, unauthorized claim, premature `DONE_PUBLISHED` or changes to controller `PROJECT_PLAN.json` were made by this documentation-only evidence update.

**Next priority:** audited, source-backed disposition for each of the three malformed messages under the existing evidence-reconciliation S-ID. A completed Slack transport test is not approval to weaken the import protocol.
