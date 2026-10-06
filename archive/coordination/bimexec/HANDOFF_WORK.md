# Handoff to Work/Codex

STATUS: RUN READ-ONLY LIVE BASELINE NOW.

Repository source of truth: `dvikt33-ux/safe-bim-layer`, branch `main`.

Rules:
- No Archicad mutations.
- Do not call `CreateWalls`, `SetPropertyValuesOfElements`, `API.SetPropertyValuesOfElements`, `set_selection`, `clear_selection`, create/move/delete/change tools, or any other write operation.
- Do not modify production Router/BIBIM.

Tasks on the real Windows machine:
1. Discover active Archicad JSON API port among 19723/19724 via read-only calls.
2. Read current project identity/path/name.
3. Read Tapir `GetAddOnVersion`.
4. Read stories.
5. Read walls, select one existing wall, call `GetDetailsOfElements`, preserve raw JSON.
6. Correctly initialize MCP Streamable HTTP at `http://127.0.0.1:8001/mcp`, then `notifications/initialized`, then `tools/list`; record protocol/session/runtime tools and inferred mode.
7. Check whether `bimexec/probes/` exists. If it does and static audit proves T0A is read-only and checksums match, run only T0A. If it does not, finish the baseline anyway.
8. Commit results to:
   - `bimexec/results/WORK_LIVE_BASELINE_2026-09-26.md`
   - `bimexec/results/GetDetailsOfElements_wall_sample.json` when available
   - `bimexec/results/capability_matrix.json` only if T0A actually ran.

Required summary fields:
`PROBES_PRESENT`, `ACTIVE_PORT`, `PROJECT`, `TAPIR_VERSION`, `MCP_OK`, `MCP_MODE`, `WALL_SAMPLE_OK`, `MUTATIONS=0`, `BLOCKERS`.
