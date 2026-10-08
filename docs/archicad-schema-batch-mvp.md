# Schema-driven batch planning for Archicad 29

Status: **offline contract compiler**, NOT a live Archicad writer.

The existing GPT -> GitHub Mailbox -> local Archicad -> GitHub roundtrip and
`create_wall_v1` live PASS remain the source of truth for actual writes.
This tool does not replace or interfere with that working channel.

## Why this exists

Do not manually test hundreds of API functions one by one. Use the published
command schemas to validate many JSON request shapes in one batch, then do
small representative live scenario tests per family of architectural tasks.

The pinned `tapir-1.5.8.json` snapshot currently documents **236 Tapir
commands** across 20 categories. The user's live Tapir version was **1.5.10**.
These two facts must not be conflated: offline contract validity against 1.5.8
does not establish 1.5.10 live command availability or semantic correctness.

## Commands

Install the off-the-shelf MIT-licensed `jsonschema` validator rather than
building an incomplete custom JSON Schema implementation:

```powershell
python -m pip install "jsonschema>=4,<5"
python scripts/archicad_batch_contracts.py --runtime-version 1.5.10
python -m unittest discover -s tests -p test_archicad_batch_contracts.py -v
```

A report on the snapshot's command count and reference resolution is emitted.
With `--runtime-version 1.5.10`, a 1.5.8 command batch gets
`REQUIRES_UPDATED_SCHEMA`; it is **not** represented as live-ready.

Example `batch.json` (offline validation **only**):

```json
{
  "requests": [
    {
      "id": "floor-table",
      "command": "GetStories",
      "params": {}
    },
    {
      "id": "example-wall",
      "command": "CreateWalls",
      "params": {
        "wallsData": [{
          "begCoordinate": {"x": 23, "y": 20},
          "endCoordinate": {"x": 24, "y": 20},
          "floorIndex": 0,
          "zCoordinate": 0,
          "height": 3,
          "thickness": 0.2,
          "referenceLineLocation": "Center",
          "structureType": "Basic"
        }]
      }
    }
  ]
}
```

```powershell
python scripts/archicad_batch_contracts.py --batch batch.json --runtime-version 1.5.10
```

The sample resembles a **previously executed** wall. It must NOT be
resubmitted to the real project: doing so would create a duplicate. The
planner does not send either example command anywhere.

## Contract boundaries

- Handles 1..100 commands in one offline planning pass.
- Validates JSON field structure, required properties, numeric bounds, enums,
  references, and nested types against the vendor's schema using
  `jsonschema`. Reports each request separately.
- Rejects unknown command names and duplicate request IDs.
- Labels operations as `READ_CANDIDATE`, `TYPED_RECIPE_REQUIRED`,
  `SPECIAL_REVIEW`, or `UNREVIEWED_COMMAND`. These are **informational**
  labels and never execution permissions.
- No network, no Archicad access, no `CreateWalls` call, no PLN writes.
- Static API schemas **cannot** validate collisions, material availability,
  hosting relations, project identity, license-dependent behavior, geometry,
  downstream effects, or outcome after a process crash.

## Integration path (not yet implemented)

1. Capture a source-pinned **Tapir 1.5.10** schema and built-in Graphisoft
   JSON API schemas; diff their command IDs with 1.5.8.
2. Reuse the **existing successful Mailbox write executor**. Call the offline
   contract compiler before queuing; **do not open arbitrary Tapir writes**
   just because they pass schema validation.
3. Map each high-level architectural intent to a small, explicit, reviewed,
   typed recipe. Resolve story identity from live `GetStories`, not from a
   hard-coded architectural '0 floor'.
4. Enforce local project fingerprint, operation ID/replay protection, source
   stale-state checks, single-writer serialization, pre-write audit trail,
   read-back and `UNKNOWN_OUTCOME` without automatic retry.
5. Run **representative** end-to-end tests for walls, slabs, host/opening,
   structure, attributes, MEP and documentation; use broad offline generated
   contract tests for the entire command catalog. Do not equate family-pass
   with untested command-pass.

This planning layer is intentionally separate from execution. The current
successfully tested write path stays unchanged until a guarded adapter is
ready and verified.


## Dependent architectural fragments (offline)

`scripts/archicad_bim_graph.py` adds dependency ordering and typed references
to created BIM elements. This is intentionally **not a Mailbox executor**.

The included example is synthetic and MUST NOT be published as a live job:

```powershell
python scripts/archicad_bim_graph.py examples/archicad_bim_graph.offline.sample.json --runtime-version 1.5.8
```

Its three operations are deliberately not ordered by creation sequence:
`window-alpha` depends on `wall-alpha` by its
`{"$createdGuid":"wall-alpha"}` reference in `ownerWallId.guid`, and on
`slab-alpha` via `after`. The compiler orders the prerequisites first and
validates those parameters against the pinned catalog. It does not resolve
an actual GUID: placeholders are represented by a sentinel **inside schema
validation only**, and are never emitted as executable parameters.

A GUID reference may point only to a supported `Create*` operation with
**exactly one element** in its create-data array. Wrong host kind, unknown
dependencies, dependency loops, and using a generated GUID outside a `.guid`
field are blocked. Arbitrary commands validated against a schema are NOT
authorized for execution. The plan checksum is a reproducibility aid, not
a replay-protection key or a user authorization.

Both the sample's coordinates and native `floorIndex` are synthetic. Resolve
a real architectural `1 этаж` from `GetStories`, never from the sample.
The current local writer understands its own verified `create_wall_v1` JOB
protocol; it does **not** consume this graph file. A reviewed translation
layer and a runtime safety gate must be completed before any live use.
