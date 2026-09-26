# BIMEXEC

Portable BIMEXEC specifications, capability probes, tests, and certification outputs live here.

Shared coordination instructions: see `COORDINATION.md`.

Production Windows Router code is intentionally kept separate until T0A/T0B certification is complete.

## Status

| Stage | State |
|---|---|
| P0 hardening specification | committed (`specs/BIMEXEC_P0.md`) |
| Independent architecture audit | committed (`docs/audits/BIMEXEC_audit_v1.md`) |
| Reference implementation of the invariants | committed (`reference/`, 45 offline tests) |
| T0A probe (read-only) | committed (`probes/probe_t0a.py`) — **not yet run on a real Archicad** |
| T0B probe (first write) | committed (`probes/probe_t0b.py`) — **not authorised, not run** |
| Live capability matrix | pending, see `docs/T0_RESULTS.md` |
| `create_wall` certification | blocked; `production_safe = false` and hard-blocked in code |

Nothing in this repository has touched a real Archicad instance.

## Layout

```
bimexec/
  README.md                      this file
  COORDINATION.md                shared handoff between ChatGPT/Work and Arena
  HANDOFF_ARENA.md               status of the current Arena task
  specs/
    BIMEXEC_P0.md                P0 hardening decisions the code must honour
    capability_matrix.schema.json output contract of T0A
  probes/
    probe_t0a.py                 read-only capability probe (Windows)
    probe_t0b.py                 controlled marker round-trip, first write (Windows)
    backends.py                  backend contract: Tapir (official JSON) + MCP
    T0_PLAN.md                   plan, per-capability table, go/no-go criteria
    README_RUN_WINDOWS.txt       exact Windows commands
    SHA256SUMS.txt               integrity sums of the probe kit
  tests/
    test_p0.py  test_probe.py  test_all.py    reference-implementation tests (45)
    selftest_probes.py                        offline self-test of the probes (42 checks)
    fakes/                                    in-memory doubles, no Archicad needed
  docs/
    audits/BIMEXEC_audit_v1.md   independent architecture audit
    T0_RESULTS.md                results contract + go/no-go (no live data)
  results/
    README.md                    what belongs here and the commit rules
    TEMPLATE_T0A_RUN.md          live run record template
    (live artefacts from Work/Codex are committed here)
  examples/
    capability_matrix.example.json  sample T0A output (from a fake, structure only)
    caps.example.json               sample certified capability report
  reference/
    bimexec/*.py                 executable specification of the invariants (stdlib)
    tools/run_probe.py           CLI for the in-skeleton probe
    README.md                    invariant → test coverage map
```

## Ground rules encoded in this repository

1. **Measured, not documented.** A capability exists only when a probe records
   `supported = true`. `null` means UNKNOWN and fails closed.
2. **Backend attribution.** Every capability records which backend answered.
3. **T0A is read-only.** It makes no mutating call, ever.
4. **T0B writes only with two keys** (`--allow-write` **and**
   `--i-understand-this-writes-to-archicad`), only on a disposable project,
   only on one element, and it must prove restoration of the original value.
5. **No geometry creation.** `create_wall` / `CreateWalls` and other mutating
   commands are hard-blocked in `probes/backends.py` until live certification.
6. **No production dependency on selection state.** Elements are addressed by
   GUID only.
7. **No retries.** Any timeout, ambiguity, or "write succeeded but read-back
   disagrees" is UNKNOWN and stops the run.
8. **Router code stays out** of this repository until T0A/T0B certification is
   complete.

## Running the offline checks

```
python bimexec/tests/selftest_probes.py   # 42 checks on the shipped probes
python bimexec/tests/test_all.py          # 45 tests on the invariants
```

Python 3.10+, standard library only, no Archicad, no network.
