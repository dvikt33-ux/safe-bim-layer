# APA Sync — raw Slack probe API request rejected (2026-10-11)

**Provenance:** USER-SUPPLIED_LOCAL_CONSOLE and GitHub API readback. **Current status:** API diagnostic BLOCKED, root cause NOT_VERIFIED. Historical Slack backfill remains NOT_VERIFIED.

## Owner observation

The user successfully cloned the read-only standalone probe from `feature/apa-sync-raw-envelope-probe-20261011` into `APA-Sync-RawProbe`. Its locally isolated Python ran `python -m scripts.apa_sync.inspect_raw_envelopes`, prompted for the secret `SLACK_BOT_TOKEN` via `getpass`, then printed:

```text
Slack API request failed (details withheld)
```

No request error code, HTTP status or retry hint was visible because PR #28 intentionally suppressed the exception details. The failure is consistent with various causes (authentication, missing channel access, Slack API rate limiting), **none proven** by this output. Never ask the owner to share token bytes.

The probe only requests recent Slack channel history and does not read/write SQLite, alter the running Socket Mode process, GitHub project statuses, PLN or installed Archicad. Earlier live `Slack → coordinator → SQLite → HTTP` PASS and restart durability remain separate evidence and should not be treated as failed by this diagnostic API call.

## Remediation published

An isolated patch in [draft PR #29](https://github.com/dvikt33-ux/safe-bim-layer/pull/29) safely discloses only a finite allowlist of Slack error codes, numeric HTTP status and bounded integer `Retry-After` duration, with synthetic redaction tests. It does **not** log arbitrary error text, token values, raw Slack content, URLs or credentials.

Owner should run PR #29 in their already isolated probe checkout, **without stopping the current live coordinator or reinstalling dependencies**, and share only the sanitized error JSON or successful structural aggregate. Follow up based on the actual reported code (e.g. rate limit wait, copy correct bot OAuth token, inspect bot permissions).

**Evidence gates:** source and tests created in new feature branch and GitHub readback verified. GitHub Actions CI initially pending; mark OFFLINE_PASS only once independently checked. A successful request and historical backfill remain LIVE NOT_VERIFIED until observed on owner's machine.

**Change control:** No main, canonical control plan, original feature branches, PLN or APX changed. This report is in canonical `docs/research/apa-results/` and should be linked in continuation.

## Offline CI verification (subsequent audit)

[GitHub Actions workflow run 38088808651](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38088808651) completed **SUCCESS**. The coordinator unit-test job ran **31/31 tests PASS** (including the two new safe error-code/redaction tests); the Windows launcher static check also completed SUCCESS. The job logs were independently retrieved. Code/documentation and this canonical report were read back via GitHub API. **This is an OFFLINE_PASS only**; no claim of successful raw Slack Web API read or historical import until the owner provides the actual output.
