# APA Sync — historical Slack ChatGPT footer compatibility (2026-10-11)

**Project:** APA for Archicad 29. **Source provenance:** Owner-provided local Socket Mode logs + independent read from connected Slack channel + verified GitHub CI. **Outcome:** OFFLINE PASS (27/27). Historical SQLite backfill LIVE NOT_VERIFIED as of publication.

## Observed raw-format signature

On 2026-10-11 the owner ran a safe diagnostics build with a live Slack App attached to channel `C0C886E1PGR`. It returned:

```text
scanned=28
accepted=0
duplicates=1
not_apa_events=2
ignored_subtype=2
rejected={'Expected APA_EVENT_V1 and one JSON code fence': 23}
rejection_shapes={
'fences=two;begins=header;ends=other;object=yes': 9,
'fences=two;begins=fence;ends=other;object=yes': 11,
'fences=none;begins=header;ends=other;object=yes': 1,
'fences=none;begins=other;ends=other;object=no': 1,
'fences=one;begins=fence;ends=object;object=yes': 1
}
```

Twenty previously rejected events have two complete triple-backtick markers but text after the closing fence. Reading their displayed contents through the independent connected Slack API, many such messages end with precisely:

```text
*Sent using* <@U0C90JE4WAC|ChatGPT>
```

The displayed Slack connector representation is not guaranteed to be byte-identical to the owner's separate Socket Mode bot raw payload. However, the user's local finite-shape histogram independently supports a shared trailing-text problem.

A second independent connector read of all 28 messages found 24 `APA_EVENT_V1` prefixes: 21 complete messages match the **proposed** strict envelope regex when including the ChatGPT footer (20 historical plus the previously accepted new smoke event). The three remaining malformed messages comprise two without triple-backtick fences and one missing a closing fence. This is a *structural preflight*, not local SQLite acceptance. The 21 syntactically compatible messages had phases LIVE 2, SOURCE 13, OFFLINE 6, and statuses INFO 16, PASS 4, BLOCKED 1, without an observed same-task-and-phase status mismatch in connector-level content. This does not independently verify their technical claims.

## Delivered code

- [Draft PR #27](https://github.com/dvikt33-ux/safe-bim-layer/pull/27), isolated branch `feature/apa-sync-chatgpt-trailer-20261011`, based on PR #26.
- `scripts/apa_sync/coordinator.py`: parse a **single** complete fenced JSON block and accept **only** the exact trailing ChatGPT footer above. Do not strip arbitrary text. Keep strict JSON IDs, phase/status, source, summary, evidence requirements for PASS, deduplication and conflict handling. The footer does not imply any authority.
- `tests/test_apa_slack_sync.py`: test multiple valid legacy fence shapes, reject wrong or additional suffixes, reject incomplete fences, verify PASS cannot omit evidence, verify bootstrap and retry deduplication.
- `docs/APA_SYNC_CHATGPT_FOOTER_COMPAT.md`: operational gates.

## CI / GitHub publication

- [GitHub Actions 38088099570](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38088099570) **SUCCESS**.
- Unit suite: **27/27 PASS**, including the four newly added attribution and bootstrap tests.
- Windows PowerShell launcher static check: PASS.
- Dedicated branch & PR published and code/test/doc readback from GitHub API PASS.

## Next live acceptance on owner's Windows system

1. Stop the older running Python Socket Mode process cleanly (Ctrl+C); do not touch the existing SQLite database.
2. Clone `feature/apa-sync-chatgpt-trailer-20261011` into a new checkout, run the same PowerShell launcher and enter local tokens privately.
3. Capture only safe aggregate `APA Slack bootstrap` counters; verify the known original event `apa-live-smoke-20261011-002` remains `seq=1`. **Up to 20 old events may now become accepted; the exact number is unknown until LIVE.**
4. Inspect `/v1/changes` and `/v1/state`, review any `CONFLICT`; perform restart deduplication only after first acceptance.
5. Leave the three malformed events out of automatic backfill; handle separately with an audited, source-linked historical normalization process.

**Scope / controls:** No main, PLN, installed Archicad or APX changes. Existing PR branches left intact. SQLite stores source reports but does not publish research artifacts to GitHub nor change PROJECT_PLAN task states. Technical SOURCE/OFFLINE PASS claims are not elevated to BUILD/LIVE PASS by restoration.

## Related canonical reports

- [One-event live receipt and SQLite read](apa-sync-live-socket-e2e-20261011.md).
- [Restart durability](apa-sync-restart-dedupe-20261011.md).
- [First aggregate rejection counts](apa-sync-live-bootstrap-diagnostic-20261011.md).
- [Structural diagnostic CI evidence](apa-sync-envelope-shapes-ready-20261011.md).
