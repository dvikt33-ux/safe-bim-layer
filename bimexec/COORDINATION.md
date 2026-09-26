# BIMEXEC coordination

This file is the shared handoff point between ChatGPT/Work and Arena for BIMEXEC/T0 work.

## Rules
- Repository: `dvikt33-ux/safe-bim-layer`
- Do not use `arena-archicad-project` for BIMEXEC.
- GitHub is the source of truth for portable specs, probes, tests, and certification outputs.
- Arena local path `/home/user/bimexec/` is a test/spec environment only.
- Windows production Router remains separate until T0A/T0B certification is complete.
- No write to Archicad before explicit T0B approval.

## Current request to Arena
Commit the finalized Windows T0 bundle into this repository instead of returning a ZIP only.

Expected paths:
- `bimexec/probes/probe_t0a.py`
- `bimexec/probes/probe_t0b.py`
- `bimexec/probes/backends.py`
- `bimexec/probes/T0_PLAN.md`
- `bimexec/probes/README_RUN_WINDOWS.txt`
- `bimexec/probes/SHA256SUMS.txt`

If other standalone files are required, add them under `bimexec/probes/` as well.

### Required guarantees
1. Python 3.10+
2. stdlib only
3. no imports from `/home/user/bimexec`
4. no Linux absolute paths
5. T0A strictly read-only
6. T0B requires both `--allow-write` and `--i-understand-this-writes-to-archicad`
7. T0B requires `--guid` and `--expect-project`
8. no geometry creation in T0B
9. corrected MCP Streamable HTTP client: initialize, `Mcp-Session-Id`, `notifications/initialized`, JSON/SSE parsing, diagnostics body on HTTP errors
10. `create_wall.production_safe = false` until live geometry certification
11. raw `GetDetailsOfElements` sample preserved in T0A output
12. backend attribution on every capability
13. client-side exact/prefix property scan is `SCAN_PREFIX`
14. no production dependency on selection state

### What Arena should post back here
- commit SHA
- exact changed file list
- exact Windows command for T0A
- expected outputs
- go/no-go criteria for T0B
- anything that still remains `UNKNOWN`

ChatGPT/Work will then review the committed files from this repository and run only T0A on Windows first.
