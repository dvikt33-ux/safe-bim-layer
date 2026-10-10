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
