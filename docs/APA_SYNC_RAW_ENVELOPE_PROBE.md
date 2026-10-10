# APA Sync — read-only raw Slack envelope inspection

## Why this diagnostic exists

The owner installed the strict ChatGPT trailer compatibility build from [draft PR #27](https://github.com/dvikt33-ux/safe-bim-layer/pull/27), but actual startup bootstrap still reported **28 scanned, 0 newly accepted, 1 duplicate and 23 fenced-envelope rejects**. The earlier structural histogram showed that 20 of those 23 messages have two triple-backtick fences and **something after the last fence**. An independent ChatGPT Slack connector represents many of them with a known `*Sent using* <@U0C90JE4WAC|ChatGPT>` footer, but that rendered representation may differ from the raw Slack Web API `conversations.history` text seen by the separately installed APA Coordinator.

The cause is NOT_VERIFIED. Do not broaden the parser or claim that 20 historical messages were recovered until the actual wire-format difference is established.

## What the probe does

`scripts/apa_sync/inspect_raw_envelopes.py` is an **independent one-shot, read-only CLI**. It makes a bounded `conversations.history` request using the local `xoxb-` bot token and the existing `slack_sdk` dependency. It does not use `xapp-`, does not connect a second Socket Mode session, does not access or modify SQLite, and leaves the running coordinator untouched.

The CLI prompts for the bot token through `getpass`, holds it only in the running Python process, does not store the token or raw message text, and emits only a JSON aggregation of static structural categories:

- `scanned`, `apa_prefix`, `parse_valid`, `fence_envelope_rejected`, `non_event`, `ignored_subtype`, other fixed validation reasons;
- fence count buckets, suffix categories (`exact_known_footer`, `contains_known_footer_plus_other`, `other_chatgpt_attribution`, `other_suffix`, etc.), suffix length buckets, and CR/invisible-character presence;
- no event IDs, Slack timestamps, JSON data, authors, file paths, URLs or arbitrary substrings.

It cannot promote any historical research status or mark tasks DONE.

## Windows usage (without restarting the live coordinator)

In a **second** PowerShell window, with the live coordinator still running in the first:

```powershell
$folder = Join-Path $env:USERPROFILE 'APA-Sync-RawProbe'
if (!(Test-Path $folder)) {
    git clone --depth 1 --single-branch --branch feature/apa-sync-raw-envelope-probe-20261011 https://github.com/dvikt33-ux/safe-bim-layer.git $folder
    if ($LASTEXITCODE -ne 0) { throw "Clone failed" }
}
Set-Location $folder
& (Join-Path $env:LOCALAPPDATA 'SafeBIM\APA-Sync\venv\Scripts\python.exe') -m scripts.apa_sync.inspect_raw_envelopes
```

Enter **only the `xoxb-` bot token** locally at the hidden prompt. This should read the recent 28 messages (up to 100) without affecting the existing listener.

Share **only the printed JSON counts and structural categories**, not the token, raw message bodies or saved local files.

## Next decision

Classify exactly why PR #27 failed to match historical entries despite the known rendered footer. Implement a *narrow, evidence-driven* parser adjustment with negative-case tests, independent GitHub Actions CI and a fresh isolated checkout for live backfill. Never accept free-form trailing text, malformed/incomplete JSON, or PASS without evidence.

### Acceptance

- Offline unit tests pass, code and docs read back from GitHub.
- Owner runs the local read-only probe; results contain no message text or tokens and distinguish the envelope trailing characteristics.
- Existing Socket Mode process and SQLite sequence remain intact.
- Actual historical backfill remains NOT_VERIFIED until independently tested after a separate parser fix.

**No changes** to main, existing branches, PLN, APX or installed Archicad.
