# APA Sync — Safe Slack API error code diagnostics

## Incident

The owner's one-shot read-only Slack Web API envelope probe [PR #28](https://github.com/dvikt33-ux/safe-bim-layer/pull/28) launched successfully in Windows checkout `APA-Sync-RawProbe` using the existing isolated Python interpreter, but exited with:

```text
Enter SLACK_BOT_TOKEN (xoxb-, hidden; not saved):
Slack API request failed (details withheld)
```

The failure occurred in the Slack Web API request; no SQLite, Archicad/PLN/APX, installed add-on, task controller or Slack channel write was performed by the probe. The original error code was intentionally hidden, which prevented distinguishing bot credential, missing scope/channel membership, and Slack rate-limit errors. **Root cause NOT_VERIFIED.**

## Narrow patch

The probe remains strictly read-only and performs the same bounded Slack conversations.history operation. Only the error handling changes:

- `safe_slack_error_summary(response)` maps Slack `response.get("error")` to a finite allowlist of static status codes, such as `invalid_auth`, `missing_scope`, `not_in_channel`, `channel_not_found`, `ratelimited`.
- Numeric HTTP status 100–599 is returned if present.
- Integer `Retry-After` values in the range 1–3600 seconds are returned if present.
- Unknown or attacker-controlled API error strings, JSON objects, user messages, raw HTTP content, token bytes, URLs and headers other than safe numeric retry metadata are **not printed**.
- No changes to the coordinator, running Socket Mode process, SQLite ledger, parser, publisher or repository main.

## Test

Unit tests check allowlisted error codes, safe retry details, and the redaction of unknown untrusted strings and invalid headers. GitHub CI must pass before owner runs this version locally.

## Windows operator

The existing read-only probe checkout at `%USERPROFILE%\APA-Sync-RawProbe` is dedicated to this tool, so it is safe to switch its branch without changing any existing APA coding branches or current coordinator directory.

In the **second** PowerShell:

```powershell
Set-Location "$env:USERPROFILE\APA-Sync-RawProbe"
git fetch --depth 1 origin feature/apa-sync-api-error-codes-20261011
if ($LASTEXITCODE -ne 0) { throw "Git fetch failed" }
git switch -c feature/apa-sync-api-error-codes-20261011 FETCH_HEAD
if ($LASTEXITCODE -ne 0) { throw "Git switch failed" }
& "$env:LOCALAPPDATA\SafeBIM\APA-Sync\venv\Scripts\python.exe" -m scripts.apa_sync.inspect_raw_envelopes
```

Enter the **same local bot token `xoxb-`**, not the Socket Mode app token `xapp-`. No token should ever be pasted into ChatGPT, Slack or GitHub. The probe does not stop or replace the first PowerShell coordinator.

If `ratelimited` or HTTP 429, obey the numeric `retry_after_seconds` before rerunning; if `invalid_auth`, confirm the token was copied from OAuth & Permissions; if `missing_scope` or `not_in_channel`, inspect the Slack app installation and channel membership rather than creating or changing any application credentials blindly.

Only share the allowlisted error JSON or, if successful, the structural aggregate. Do not send full exception traces or tokens.

## Project status

Original Slack→SQLite one-message LIVE PASS and restart durability are retained. The 23 older research messages are still **not imported**, and historical reconciliation remains BLOCKED pending an actual raw Slack API envelope inspection. Prior OFFLINE PASS tests do not elevate this to LIVE PASS.
