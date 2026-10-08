# Current installed Archicad runtime

**Effective date:** 2026-10-09
**Evidence:** user-provided screenshot from Archicad's *Product Information* panel.

| Field | Current value |
| --- | --- |
| Application | Graphisoft Archicad |
| Major version / project compatibility track | 29 |
| Installed application version | **29.2.1** |
| Application build | **5101** |
| Distribution label from UI | **RUS FULL** |
| Architecture | **x86-64** |
| Displayed product string | **Archicad 29.2.1 (5101) RUS FULL (x86-64)** |
| Project development target | **Archicad 29.2.1 (5101)** |
| Planned later migration | Archicad 30, only after the Archicad 29 MVP is operational |

## Evidence and migration safeguards

- This supersedes earlier generic descriptions of the **currently installed application** as only `Archicad 29` or as an earlier 29.x update. The original historical evidence and timestamps remain intact.
- Keep compatibility identifiers such as `Archicad 29 DevKit`, `AC29`, `ARCHICAD_29`, installed API paths, and major version `29` when they denote the API generation rather than an installed patch-level version.
- **Tapir 1.5.8/1.5.10 is an independent add-on/API version**, not the application build. Do not replace those numbers with `29.2.1`. Verify the *currently loaded* add-on version after the update before widening execution.
- The user interface reports that the Archicad application is updated. It separately reports a library update as available; library update completion is **not** confirmed.
- The screenshot alone does not verify Python connection bindings, loaded add-ons, MEP availability after this particular update, source code compatibility, or entitlement/activation. Treat those as separate runtime checks.
- The previous guarded Mailbox dry-run against `Тест MER ` confirmed project identity and remote RESULT. It predates this runtime-version record; a post-update `GetProductInfo` + `GetAddOnVersion` check is still recommended.
- For all writes, keep the exact test PLN allowlist, GUID readback, journal and single-writer protections. The supplied project name contains a trailing space.
- Do not modify earlier experiment output, historical Git commits, old research snapshots, retained PLN, or source-checkpoint evidence to make them falsely appear to have run on build 5101.

**Canonical current-version label:** `Archicad 29.2.1 (5101) RUS FULL (x86-64)`.
