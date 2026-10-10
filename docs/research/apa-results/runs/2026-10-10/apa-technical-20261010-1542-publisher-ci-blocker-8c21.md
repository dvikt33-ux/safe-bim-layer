# APA-P10.A01.S02 — publication CI blocker / controller lease schema

**UTC:** 2026-10-10T15:42Z. **Phase:** OFFLINE source/log inspection. **Status:** BLOCKED for V2 receipt, source report GitHub READBACK PASS.

- [Full source report](apa-technical-20261010-153928-profile-fields-edge-material-8c21.md) — commit `9c9d72b8b18679089379bcaa8b61d30d9b0a41e6`, exact GitHub readback PASS.
- [PUBLISH_REQUEST_V1 inbox](../../inbox/APA-RUN-20261010-153928Z-profile-attribute-readback.json) — commit `69e77e13d0ea75c3c849a8b5bc98348b74dd9571`, readback PASS.
- [GitHub Actions publisher run 38064652309](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38064652309) — **FAIL** in `Project Controller DAG, claim and dispatch tests`. All 15 controller tests failed at plan validation with `controller.ControllerError: Bad lease APA-P60.A02.S04`.
- [Controller source L122–126](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/tools/apa_controller/controller.py#L122-L126): active `lease_until` must match exact `YYYY-MM-DDTHH:MM:SSZ` (no fractional seconds). Current *other executor's* S04 lease was `2026-10-10T16:25:55.686Z`, valid ISO timestamp but rejected by controller's stricter regex.
- **No edits to S04 ownership, lease or claim** were made by technical executor. The audit owner should normalize its own lease to whole seconds (without shortening actual lease), or finish/release S04, then rerun controller CI. This is a **plan schema conflict**, not a failed technical profile finding.
- V2 immutable report/receipt **NOT_CREATED**; direct Markdown report and proposal remain saved. Technical S02 is `PARTIAL`, not DONE. This failure must not be mistaken for missing GitHub write permission.
- No main/master/PLN/APX modifications.
