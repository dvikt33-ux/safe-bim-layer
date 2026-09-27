# Tests

Everything here runs offline: no Archicad, no network, no write to any project.

| Command | What it proves |
|---|---|
| `python bimexec/tests/selftest_probes.py` | The **shipped probe files** behave as claimed: T0A read-only and fail-closed, T0B default = no write, two-key rule, round-trip with proven restore, silent-noop detection, leftover-marker detection, `create_wall` hard-blocked, AC29 backend without official `GetProjectInfo`, empty-GUID rejection, empty-property-values rejection. 62 checks. |
| `python bimexec/tests/test_all.py` | The **reference implementation** of the BIMEXEC invariants (WAL/state machines/marker binding/verify gating/executor). 45 tests. |
| `python bimexec/tests/test_p0.py` | P0 subset only: mutation outcomes, mapping states, marker round-trip, verify statuses, recovery. |
| `python bimexec/tests/test_probe.py` | Capability certification: `UNKNOWN` never becomes `OK`, uncertified capability blocks dispatch, empty-scope fallback. |

Python 3.10+, standard library only. Exit code 0 = all green.

## Layout

```
tests/
  test_all.py            runner over both test modules (reference implementation)
  test_p0.py             P0 invariants
  test_probe.py          capability certification
  selftest_probes.py     offline self-test of probes/probe_t0a.py and probes/probe_t0b.py
  fakes/                 in-memory doubles, loaded by the probes via --backend-module
    fake_tapir_shape.py       response shape of the real Tapir add-on (type/id/floorIndex/layerIndex + details.wall)
    fake_no_custom_prop.py    same, but BIMEXEC/BIMEXEC_MARKER does not exist yet
    fake_backend.py           minimal in-memory model
    fake_backend_silentnoop.py  set_property_value returns success but writes nothing (defect class E3)
    fake_backend_leftover.py    project already contains a BX:PROBE: marker
    fake_backend_bad_guid.py     GetElementsByType answers with empty GUIDs
    fake_no_custom_prop_silent.py property missing, but the call returns empty values instead of failing
```

The fakes are **not** needed on Windows: they exist so that probe logic can be
verified without an Archicad instance. Use them like this:

```
python bimexec/probes/probe_t0a.py --out cm.json --backend-module bimexec/tests/fakes/fake_tapir_shape.py
```

## What these tests deliberately do not do

- They never reach a real Archicad instance.
- They never assert that Archicad behaves in any particular way — that is what
  the live T0A run is for.
- They do not cover the production Router, which is out of this repository
  until T0A/T0B certification is complete.

## H1 — AC29/Tapir adapter parity (offline only)

`test_h1_contract.py`: 24 contract regressions, socket creation blocked. Golden
payload is fixed from the c55f404 T1/T2 recipe; the command-spy backend never
connects to Archicad. This suite is also registered by `test_all.py`: 93 existing
+ 24 H1 = 117 tests. No production capability is promoted.

```bash
python3 bimexec/tests/test_all.py
python3 bimexec/tests/test_h1_contract.py
python3 bimexec/tests/test_probe_v13.py
```

See [H1 scope and deferred B2–B7](../docs/H1_ADAPTER_PARITY.md). Historical
`results/` evidence is not rewritten by these regressions.

H1 offline execution logs and exact Python-source hashes: `h1_evidence/`.
They are new H1 artifacts, not replacements for T0–T9 live evidence.
