# APA Slack historical events — ChatGPT attribution compatibility

## Evidence-driven issue

Owner's local Socket Mode log on 2026-10-11 from [draft PR #26](https://github.com/dvikt33-ux/safe-bim-layer/pull/26):

```text
scanned=28 accepted=0 duplicates=1 not_apa_events=2 ignored_subtype=2
rejected={"Expected APA_EVENT_V1 and one JSON code fence":23}
rejection_shapes={
  "fences=two;begins=header;ends=other;object=yes":9,
  "fences=two;begins=fence;ends=other;object=yes":11,
  "fences=none;begins=header;ends=other;object=yes":1,
  "fences=none;begins=other;ends=other;object=no":1,
  "fences=one;begins=fence;ends=object;object=yes":1
}
```

For 20 of 23 parser rejections, the expected two JSON fences exist but something follows the closing fence. Independently reading several of the corresponding messages through the connected Slack connector shows a known footer placed after the otherwise completed JSON code block:

```text
*Sent using* <@U0C90JE4WAC|ChatGPT>
```

This is evidence of the footer shape **in Slack connector representations**, not proof of the exact raw event bytes on the owner's machine. The owner should still verify live bootstrap after this patch.

## Narrow compatibility fix

In `scripts/apa_sync/coordinator.py`, allow **only** the exact ChatGPT Slack attribution line following a completed, valid JSON fence. Preserve the mandatory `APA_EVENT_V1` prefix, exactly one fenced JSON object, existing strict field allowlist, required IDs, phase, status, source, summary, HTTPS evidence requirements for PASS, idempotence and conflict logic.

No generic text stripping, arbitrary footer regex, no accepting unfenced or incomplete JSON, no skipping existing evidence or status checks. The ChatGPT footer provides **no additional authority** and is not evidence of technical PASS.

Tests include a header + compact code-fence variant, both footer and no-footer cases, wrong footer and appended arbitrary prose rejection, incomplete fence rejection, PASS without evidence rejection and duplicate replay idempotence.

## Local acceptance criteria

After GitHub CI passes:

1. Stop the running coordinator cleanly with Ctrl+C. Clone the new feature branch in an isolated folder; leave earlier checkouts and their working branches untouched.
2. Launch `start_windows.ps1` with local, hidden `xoxb-` and `xapp-` tokens. The existing local SQLite database under LOCALAPPDATA is reused; never delete or replace it.
3. Inspect the `APA Slack bootstrap` counters, particularly accepted, duplicates, rejected, and conflicts. Expected: many of the 20 messages may now be accepted, **but 20 accepted is not asserted** until confirmed by local output.
4. Independently query localhost `/v1/changes?after=0` and `/v1/state`; confirm the original live smoke event still exists, and separately review any `CONFLICT` statuses.
5. Verify one more restart does not create duplicate rows. Do not automatically change canonical PROJECT_PLAN task states based solely on historical Slack INFO/PASS messages.

Any remaining malformed events (e.g. 2 without backtick fences and 1 with a missing closing marker) stay **blocked for automatic import**; review and normalize from original GitHub artifacts only through a dedicated, cited audit.

## Separation of concerns

The Socket Mode coordinator is an event transport/ledger, **not** an autonomous research engine, a GitHub publisher, nor a means to push into already-running ChatGPT text turns. Research results remain valid only after explicit GitHub commit, readback and linking in canonical `docs/research/apa-results/`. No main, PLN, APX or installed Archicad changes.

## Source and status

- [Live diagnostic report](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-sync-live-bootstrap-diagnostic-20261011.md).
- [Original one-event LIVE acceptance](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-sync-live-socket-e2e-20261011.md).
- **Status:** source patch staged. Offline CI and LIVE historical backfill status must be verified separately.
