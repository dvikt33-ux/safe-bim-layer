# Archicad Accelerator: offline floor checkpoint — 2026-10-09

## Scope and provenance

- Work branch: `chatgpt/accelerator-floor-offline-20261009`.
- **Base branch:** `chatgpt/whole-scene-v1-20261009`, initial SHA
  `f02a167eb73cb149713cf5e613911b144fce5be2`.
- The user's **Windows-local** branch
  `feature/archicad-project-accelerator-mvp-20261009` and commit
  `308264c` were **not** available in GitHub when this checkpoint was started.
  This branch **does not claim to contain, replay, or replace** that local
  commit, local `--schema` fixes, installed Tapir binaries, or
  `outputs/accelerator/` logs.
- `main`, PLN, mailbox watcher, binary extensions, local checkouts were not
  changed by the GitHub-only changes.
- Schema pinned in this published branch: `tapir-1.5.8.json`, **not** the
  user's locally generated Tapir 1.5.10 documentation. The actual runtime
  version is a distinct gate.

## How to run offline (no Archicad needed)

On an existing clone of this **checkpoint branch**, Python 3.11 and
`jsonschema>=4,<5`:

```powershell
python -m pip install "jsonschema>=4,<5"
python -m unittest discover -s tests -p "test_archicad_*.py" -v
python scripts/archicad_accelerator_offline_benchmark.py --output outputs/accelerator/offline-metrics.json
python scripts/archicad_typical_floor_graph.py --anchor-x 200 --anchor-y 200 --output outputs/accelerator/typical-floor-preview.json
```

The benchmark is **one runnable scenario** encompassing a 12-element mocked
pavilion, partial-failure journal + duplicate prevention, and a 101-element
mocked parametric floor. It uses `FakeNative` from the existing pavilion
suite. It records mock API call counts and timings, serialized request/response
bytes, and mock readback calls. It does **not** measure real native latency.

## The parametric floor

Default footprint: **36 × 18 m**; height **3 m**; six 6 m bays,
central nominal 2.4 m corridor, single first storey
(`GetStories` native index `0`, floorId `1`; not a so-called zero floor).
One source object controls the grid, exterior walls, corridor boundaries,
partition walls, hosted room doors/windows, columns and slab.

Default graph contents:

| Element | Count |
| --- | ---: |
| Wall | 36 |
| Column | 28 |
| Window | 24 |
| Door | 12 |
| Slab | 1 |
| **Total** | **101** |

Additionally: 12 semantic room records, one corridor and three reserved
core footprints (stair, lift, MEP). These are **not** extra Archicad native
elements. Their native creation, materials, Zone assignments, physical joins,
clashes, fire escape and code compliance are explicitly **UNSUPPORTED** or
**NOT_VERIFIED**. No automatic compliance certification is provided.

The old graph parser enforced the 100-request batch cap for the whole plan.
Only **offline graph capacity** is changed to 500 nodes. The existing
`MAX_REQUESTS=100` remains for the low-level batch contract.
This change does **not** grant permission for 500 native writes or silently
enable batching.

The newly added test consumes the original graph compiler and the original
pavilion `resolve_params`, `created_guid`, `requested_details`,
`verify_readback`, and `check_previous_wall` routines on the same
`FakeNative` implementation. A 101-step fake execution is not a replacement
for collision detection, journalled floor execution, or native readback.

## The existing pavilion: read-only and potentially executable commands

The only real application entrypoint kept here is the **existing**
`scripts/archicad_scene_run.py`, not the new floor generator.

Read-only preflight on the user's Windows **test system**, using an already
existing journal directory and a user-chosen empty site:

```powershell
python .\scripts\archicad_scene_run.py --anchor-x 200 --anchor-y 200 --data-dir "<EXISTING_JOURNAL_DIR>" --summary
```

**Prepared, but prohibited to run without a separate explicit approval:**

```powershell
python .\scripts\archicad_scene_run.py --anchor-x 200 --anchor-y 200 --data-dir "<EXISTING_JOURNAL_DIR>" --execute --scene-id "<FRESH_UNIQUE_SCENE_ID>" --confirm-plan-hash "<HASH_FROM_SAME_ANCHOR_PREFLIGHT>"
```

This command must only be evaluated after checking local uncommitted changes,
the exact test project and active model, installed Tapir version, real 1.5.10
command schema, complete element scan and collision clearance. No name/path
guessing, no PLN switching or saving, no automatic retries, rollback or
deletion on unknown result. Do not run it on an actual working design.

The approved target identity is pinned in the existing program; edit nothing
to bypass project/version safety checks.

## Acceptance gates

| Gate | Status |
| --- | --- |
| Published separate GitHub branch from prior tested code | DONE |
| Restore local accelerator commit `308264c` exactly | BLOCKED — no local access |
| Restore local `outputs/accelerator/`, binary/schema changes | BLOCKED — no local access |
| Existing pavilion 12-element synthetic workflow | TESTED IN CI; FAKE NATIVE |
| Pavilion native read-only preflight on user's machine | USER-REPORTED PRIOR RESULT; NOT RERUN HERE |
| Pavilion live 12-element creation | NOT EXECUTED |
| Typical floor single-source graph and 101-step fake readback | TESTED IN CI; FAKE NATIVE |
| Floor native write and actual material verification | UNSUPPORTED / NOT EXECUTED |
| Native API latency and safe batching improvement | NOT MEASURED |

## Measured performance policy

Record `apiCallCount`, `requestBytes`, `responseBytes`,
`mockApiWallTimeMs`, `readbackApiWallTimeMs` and scene duration separately.
These are collected by the benchmark under Python+FakeNative and **must not**
be interpreted as Archicad speed measurements. The safe optimizer may later
compare serial execution, schema caching and validated batch read operations
under a genuinely identical live PLN snapshot. There is **no authorization**
to batch native writes based on mock speed alone.

Before any floor live writing, extend `SceneWriter` via guarded, reviewed
planner binding and a full project-specific spatial envelope; do not simply
substitute a larger graph into the pavilion's fixed 4×3 m collision scanner.
Verify host GUIDs and all created elements by native readback. A new floor
run must have its own durable operation journal and stricter dimension,
attribute and project identity gates.
