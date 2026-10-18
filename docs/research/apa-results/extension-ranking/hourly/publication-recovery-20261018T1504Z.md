# APA publication-path recovery diagnostic

Observed at 2026-10-18T15:04:27.501Z.

Repository: dvikt33-ux/safe-bim-layer
Target branch: `research/apa-extension-ranking-hub-20261018` (never main).

* Earlier verified content: `NEXT_RESEARCH_PRIORITIES.md` read successfully; `research-1-20261018T14Z.md` exists and has blob SHA `b82c8d683fe24d321fe75c1101aa4287c647872a`.
* Opera list_tabs responds and currently exposes 273 open tabs. Reading an older research source tab encountered a readiness timeout (10000 ms); this is not evidence of permanent disconnection.
* Test procedure: explicit branch, preflight absence, create_file, then fetch_file and strict content comparison.
* The file does not change production code, main, PLN or APX. This is a publication diagnostic, not a claim of AC29 LIVE verification.

If this succeeds, hourly tasks should prefer this contents-API method and fall back to Git Objects only after a confirmed write failure. Do not claim write success without readback.
