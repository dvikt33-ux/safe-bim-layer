# Examples

Reference outputs, so the shape of a result is known **before** the live run.

| File | What it is |
|---|---|
| `capability_matrix.example.json` | A real `probe_t0a.py` output, validated against `specs/capability_matrix.schema.json`. Produced **against the in-memory fake** `tests/fakes/fake_tapir_shape.py`, not against Archicad. It shows the structure and the field names; it is **not evidence about your Archicad build**. |
| `caps.example.json` | Sample certified capability report of the reference implementation (`reference/tools/run_probe.py --raw fake --allow-write`), i.e. what the executor consumes as `CapabilityMatrix`. |

## How to read `capability_matrix.example.json`

- `capabilities.<name>.supported` is tri-state: `true` certified by a real call,
  `false` proven unavailable, `null` unknown. `null` must fail closed — it is
  never "OK".
- `capabilities.<name>.backend` is the attribution: which backend actually
  answered (`tapir`, `mcp`, or `null`). A capability without attribution is
  invalid, and the schema rejects it.
- `duplicate_detection: SCAN_PREFIX` means there is no server-side prefix search
  in this stack; duplicate detection is a client-side scan of property values
  plus a prefix match.
- `raw_dumps.GetDetailsOfElements_sample` is the untouched response kept as
  evidence for wall endpoint geometry (`begCoordinate` / `endCoordinate`).
- `operations.create_wall.production_safe` is `false` here and in every run
  until live geometry certification is complete.
- `verdicts.executed: true` only means the probe ran. The decision is
  `verdicts.t0a_go`.

## Validate a fresh live output against the schema

```bash
python - <<'PY'
import json, jsonschema
schema = json.load(open("bimexec/specs/capability_matrix.schema.json"))
inst = json.load(open("capability_matrix.json"))
jsonschema.Draft202012Validator(schema).validate(inst)
print("conforms")
PY
```

`jsonschema` is a review-time convenience only; nothing in `probes/` depends on
it (stdlib only, by design).
