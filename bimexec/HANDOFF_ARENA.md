# Handoff to Arena

STATUS: READY FOR TRANSFER — committed on branch `arena/t0-probes`, rebased on
`main` @ `72e9be1`. Not pushed: Arena has no `gh`, PAT, or SSH push path and
must not receive user secrets.

## Shared GitHub target

- repository: `dvikt33-ux/safe-bim-layer`
- branch: `arena/t0-probes` (exists on the remote, currently at `12ae4e5`; after
  the transfer it must point at the commits below)
- target paths under that branch: `bimexec/probes/`

## Transfer protocol

Do NOT ask for PAT, SSH keys, or any secret.

1. Two commits on top of `main` @ `72e9be1`; the bundle is exported from exactly
   that state.
2. Surface `arena-t0-probes.bundle` as a user-visible artifact, together with
   `arena-t0-probes.diff` and `patches/*.patch`.
3. Do not regenerate source from prose and do not squash the two commits.
4. Work/Codex imports the bundle on a machine with repository write access and
   pushes the exact commits to GitHub branch `arena/t0-probes`.
5. After the push, ChatGPT compares the remote branch against `main`, reviews the
   files, and creates/reviews a PR before any merge.

## Result of this task

| Item | Value |
|---|---|
| Repository | `dvikt33-ux/safe-bim-layer` |
| Branch | `arena/t0-probes` |
| Base | `main` @ `72e9be1` |
| Commits on top of base | 3 (2 bundle + 1 AC29 live-fix) |
| Bundle commit (the kit) | `607441aaf39998f1f0d5d1c22b8e66a796d3e8de` |
| Tip commit (records the SHA above) | see `git log -1` |
| Bundle version | 1.1 |
| Push state | committed locally, **not pushed**. The bundle is handed to the user; Work/Codex imports and pushes it. No PAT, no SSH, no secrets. |

### Required source files

```
bimexec/probes/probe_t0a.py
bimexec/probes/probe_t0b.py
bimexec/probes/backends.py
bimexec/probes/T0_PLAN.md
bimexec/probes/README_RUN_WINDOWS.txt
bimexec/probes/SHA256SUMS.txt
```

### Files added

```
bimexec/probes/probe_t0a.py
bimexec/probes/probe_t0b.py
bimexec/probes/backends.py
bimexec/probes/T0_PLAN.md
bimexec/probes/README_RUN_WINDOWS.txt
bimexec/probes/SHA256SUMS.txt
bimexec/specs/BIMEXEC_P0.md
bimexec/specs/capability_matrix.schema.json
bimexec/docs/audits/BIMEXEC_audit_v1.md
bimexec/docs/T0_RESULTS.md
bimexec/results/README.md
bimexec/results/TEMPLATE_T0A_RUN.md
bimexec/examples/README.md
bimexec/examples/caps.example.json
bimexec/examples/capability_matrix.example.json
bimexec/reference/README.md
bimexec/reference/bimexec/__init__.py
bimexec/reference/bimexec/adapters.py
bimexec/reference/bimexec/binding.py
bimexec/reference/bimexec/executor.py
bimexec/reference/bimexec/journal.py
bimexec/reference/bimexec/lock.py
bimexec/reference/bimexec/probe.py
bimexec/reference/bimexec/states.py
bimexec/reference/bimexec/tapir_raw.py
bimexec/reference/bimexec/verify.py
bimexec/reference/tools/run_probe.py
bimexec/tests/README.md
bimexec/tests/selftest_probes.py
bimexec/tests/test_all.py
bimexec/tests/test_p0.py
bimexec/tests/test_probe.py
bimexec/tests/fakes/fake_backend.py
bimexec/tests/fakes/fake_backend_leftover.py
bimexec/tests/fakes/fake_backend_silentnoop.py
bimexec/tests/fakes/fake_no_custom_prop.py
bimexec/tests/fakes/fake_tapir_shape.py
```

### Files changed

```
bimexec/README.md          structure, status, ground rules
bimexec/COORDINATION.md    status table, request to ChatGPT/Work, guarantees
bimexec/HANDOFF_ARENA.md   this file
```

### Verification performed by Arena (offline, no Archicad)

- `python bimexec/tests/test_all.py` → **45/45 PASS**
- `python bimexec/tests/selftest_probes.py` → **62/62 PASS**, covering:
  T0A read-only + fail-closed exit 2; T0B default performs no write; T0B rejects
  a single write key; T0B round-trip proves restoration of the original value;
  silent no-op write stops at `READ_BACK` with `UNKNOWN`; leftover `BX:PROBE:`
  stops at `PRECHECK`; `CreateWalls` / `DeleteElements` / `SetSelection` are
  hard-blocked; AC29 backend is available without official `GetProjectInfo`;
  `elements_by_type` with empty GUIDs is not certified; empty property values
  alone never certify `read_custom_property`.
- `bimexec/examples/capability_matrix.example.json` validates against
  `bimexec/specs/capability_matrix.schema.json` (draft 2020-12), including two
  negative cases: a capability without `backend` is rejected, and
  `create_wall.production_safe = true` is rejected.
- `bimexec/probes/SHA256SUMS.txt` recomputed and verified.

## Exact Windows command for T0A

```
python probe_t0a.py --out capability_matrix.json --ports 19723,19724 --mcp-url http://127.0.0.1:8001/mcp --expect-project "C:\PLN\MCP_TEST.pln"
```

Expected outputs, the go/no-go criteria for T0B, and the remaining UNKNOWN items
are in `bimexec/docs/T0_RESULTS.md`.

## docs/ vs results/

- `bimexec/docs/` — specification and contract only: audits, the results
  contract, go/no-go criteria. No live data.
- `bimexec/results/` — live artefacts produced by Work/Codex on Windows:
  `WORK_LIVE_BASELINE_2026-09-26.md`, `GetDetailsOfElements_wall_sample.json`,
  `capability_matrix.json`. Template: `bimexec/results/TEMPLATE_T0A_RUN.md`.

## Still UNKNOWN (must be answered by the live T0A run)

1. Live Tapir Add-On version.
2. Which Element ID address resolves on AC29.
3. Whether `GetDetailsOfElements` returns wall coordinates in `details.wall`.
4. Whether the MCP endpoint on 8001 initializes, and its reported mode.
5. Whether a hand-created user-defined property can be written through
   `API.SetPropertyValuesOfElements` — this is what T0B tests.
6. Story `index → name` completeness.

## Safety

- Do not run T0B.
- Do not perform any Archicad write.
- Do not write directly to `main`.
- No production Router integration yet.

Work/Codex separately owns live Windows read-only checks and T0A execution once
the probe source is available.
