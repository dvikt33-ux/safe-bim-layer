# APA Sync — LIVE import regression persists with PR #27 (2026-10-11)

**Evidence class:** USER-SUPPLIED_LOCAL_LOG, explicitly separated from code/CI readbacks. **Outcome:** legacy history import STILL BLOCKED / NOT_VERIFIED. **Published fix:** [draft PR #27](https://github.com/dvikt33-ux/safe-bim-layer/pull/27) passed offline 27/27, but failed the owner's live legacy import gate. No reinterpretation of any earlier SOURCE/OFFLINE status.

## Actual local execution

Owner cloned `feature/apa-sync-chatgpt-trailer-20261011` in a separate checkout and launched the Windows Socket Mode coordinator with privately entered bot/app tokens. The log of 2026-10-11 at 00:36 MSK reported:

```text
APA Slack bootstrap {
  'scanned': 28,
  'accepted': 0,
  'conflicts': 0,
  'duplicates': 1,
  'not_apa_events': 2,
  'ignored_subtype': 2,
  'rejected': {'Expected APA_EVENT_V1 and one JSON code fence': 23},
  'rejection_shapes': {
    'fences=two;begins=header;ends=other;object=yes': 9,
    'fences=two;begins=fence;ends=other;object=yes': 11,
    'fences=none;begins=header;ends=other;object=yes': 1,
    'fences=none;begins=other;ends=other;object=no': 1,
    'fences=one;begins=fence;ends=object;object=yes': 1
  }
}
APA coordinator local read API at http://127.0.0.1:8765
Listening to Slack events only in channel C0C886E1PGR
A new session has been established
Bolt app is running!
Starting to receive messages from a new connection
```

No secrets, user-owned file paths or session IDs are included here. The latest user log does not itself show the current `/v1/changes` state; prior `seq=1` and restart durability were proven separately in [receipt](apa-sync-restart-dedupe-20261011.md).

## Conclusions

- **LIVE PASS (transport):** Slack Socket Mode session connected; local HTTP read API started.
- **LIVE FAIL / BLOCKED (historical acceptance):** PR #27 did not recover any previously rejected historical `APA_EVENT_V1` message; `accepted=0`, `rejected=23`.
- **OFFLINE PASS:** [GitHub Actions 38088099570](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38088099570) ran 27/27 parser/ledger unit tests successfully, but these synthetic test strings did not reproduce the actual raw Slack Web API envelope.
- The previous ChatGPT Slack connector display of `*Sent using* <@U0C90JE4WAC|ChatGPT>` after complete fences should **not** be assumed to match byte-for-byte what the separate local Slack bot receives. The exact mismatch is NOT_VERIFIED; do not blindly strip arbitrary suffix content.

## New isolated diagnostic work

[Draft PR #28](https://github.com/dvikt33-ux/safe-bim-layer/pull/28) adds a one-shot **read-only raw Slack envelope probe** to an isolated branch. The proposed tool prompts for the local `xoxb-` token and summarizes bounded raw `conversations.history` content as finite structural categories, **without printing message text, URLs, authors, timestamps or secrets**, touching SQLite, stopping/restarting the running coordinator, or modifying Archicad.

Once CI passes, the owner can launch the probe in a second PowerShell window using the existing venv. Based only on the observed raw suffix categories, prepare a narrowly scoped compatibility fix and test it locally. Malformed/incomplete JSON and PASS without evidence must remain invalid.

**Safety:** No main/PLN/APX changes, no mutation of existing feature/research branches. This report is immutable and published in the canonical APA research hub. GitHub readback required before declaring publication complete.
