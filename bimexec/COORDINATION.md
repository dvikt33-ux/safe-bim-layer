# BIMEXEC coordination

This file is the shared handoff point between ChatGPT/Work and Arena for BIMEXEC/T0 work.

## Rules
- Repository: `dvikt33-ux/safe-bim-layer`
- Do not use `arena-archicad-project` for BIMEXEC.
- GitHub is the source of truth for portable specs, probes, tests, and certification outputs.
- Arena local path `/home/user/bimexec/` is a test/spec environment only; final portable results must land here.
- Windows production Router remains separate until T0A/T0B certification is complete.
- No write to Archicad before explicit T0B approval.
- Arena works in an `arena/<topic>` branch and never writes directly to `main`
  (see `docs/OPERATING_MODEL.md`).

## Current state

| Item | Location | State |
|---|---|---|
| T0 probe kit (standalone) | `bimexec/probes/` | committed, branch `arena/t0-probes` (base `main` @ `72e9be1`) |
| P0 hardening specification | `bimexec/specs/BIMEXEC_P0.md` | committed |
| T0A output contract | `bimexec/specs/capability_matrix.schema.json` | committed |
| Offline tests | `bimexec/tests/` | committed, 45 + 42 checks green |
| Architecture audit | `bimexec/docs/audits/BIMEXEC_audit_v1.md` | committed |
| Live capability matrix | `bimexec/results/` | **PENDING — Windows T0A not run** |
| T0B authorisation | `bimexec/docs/T0_RESULTS.md` §3 | **NOT GRANTED** |
| docs vs results | `docs/` = contract, `results/` = live artefacts | in force |

## Request to ChatGPT/Work

1. Take the probe kit from `bimexec/probes/` (branch `arena/t0-probes`).
2. Run **T0A only**. It is read-only; it cannot damage a project.
3. Commit (or paste back) `capability_matrix.json`, the full console output, and
   the exit code; fill in the live run record in `bimexec/docs/T0_RESULTS.md`.
4. Do **not** run T0B until the go/no-go criteria in
   `bimexec/docs/T0_RESULTS.md` §3 are all satisfied **and** the decision is
   recorded there.

## Guarantees the committed kit provides

1. Python 3.10+
2. stdlib only
3. no imports from the Arena local environment
4. no Linux absolute paths in the probe kit
5. T0A strictly read-only
6. T0B requires both `--allow-write` and `--i-understand-this-writes-to-archicad`
7. T0B requires `--guid` and `--expect-project`
8. no geometry creation in T0B
9. corrected MCP Streamable HTTP client: initialize, `Mcp-Session-Id`,
   `notifications/initialized`, JSON/SSE parsing, protocol-version fallback,
   response body echoed in diagnostics on HTTP errors
10. `create_wall.production_safe = false` until live geometry certification
11. raw `GetDetailsOfElements` sample preserved in T0A output
12. backend attribution on every capability
13. client-side exact/prefix property scan recorded as `SCAN_PREFIX`
14. no production dependency on selection state

## What Arena must post back here

- commit SHA (see `HANDOFF_ARENA.md`)
- exact changed file list
- exact Windows command for T0A
- expected outputs
- go/no-go criteria for T0B
- everything that remains `UNKNOWN`

All of the above is recorded in `docs/T0_RESULTS.md` and `HANDOFF_ARENA.md`.
