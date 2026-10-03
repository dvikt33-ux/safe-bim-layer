# Safe BIM Layer v0.1

Qwen emits only the high-level `create_room` contract. `safe_bim_layer.py` owns Tapir payload construction, pinned-schema preflight, one-write-at-a-time execution, ordered read-back, requested-vs-actual diffs, host relationship checks, and fail-closed orchestration.

High-level operations:

- `create_wall_loop(contour, floor_index, height, thickness)`
- `create_basic_slab(contour, level, floor_index, thickness)`
- `insert_window(host_wall_guid, params)`
- `insert_door(host_wall_guid, params)`
- `create_room(contour, wall_height, wall_thickness, slab, door, windows)`

`CreateSlabs` schema v1.5.8 does not expose `structureType` or `buildingMaterialId`; it exposes `favoriteName`, `level`, `thickness`, `referencePlaneLocation`, polygon, and floor. The Safe BIM Layer therefore does not invent low-level values: it creates with the supported schema and fails unless read-back reports `structureType: Basic` and the requested numeric thickness.

Known limitations recorded for v0.1:

- `Tapir_ModifyWalls` may change `showOnHome false -> true`.
- The earlier slab `0.20 -> 0.30` mismatch was caused by a Composite slab, not proven thickness ignoring.
- `floorPlanPolygons` may be multi-polygon; that alone is not a wall-join failure without geometric/visual evidence.
- A failed operation stops the room transaction; v0.1 does not auto-delete partial writes.

## BIM modeling constitution

Generated geometry is governed by [the Archicad modeling standard](docs/SAFE_BIM_ARCHICAD_MODELING_STANDARD.md). The standard forbids visual approximations that violate BIM semantics, requires staged generation with audits, and blocks `PASS` when mandatory QA is unresolved.

Reference-pattern capture is defined by [the Archicad reference-model protocol](docs/ARCHICAD_REFERENCE_MODEL_PROTOCOL.md). Machine-readable blocker rules and pass dependencies are in [`docs/archicad_modeling_qa_rules.v1.json`](docs/archicad_modeling_qa_rules.v1.json).

The offline [blocker auditor](docs/BIM_QA.md) implements rules 001, 002, 003,
008, 009, 010 and 011 using captured read-back plus explicit scoped
intent/identity evidence. Rule 011 enforces **minimum semantically correct
element count / operations before fragmentation**: e.g. one Wall + roof trim is
preferred over a stepped gable made of many Walls, and one/minimal Slab set +
native cut/SEO operations is preferred over a pile of porch fragments.

Roof/wall/rafter geometric blocker logic for 004–007 is documented in
[`docs/BIM_GEOMETRY_QA.md`](docs/BIM_GEOMETRY_QA.md) and implemented as a
separate fail-closed offline checker because Tapir 1.5.8 does not expose enough
Roof type-specific read-back to prove a live roof system by itself.

The coordination/dimensional supplement
[`docs/BIM_COORDINATION_AND_DIMENSIONAL_STANDARD.md`](docs/BIM_COORDINATION_AND_DIMENSIONAL_STANDARD.md)
adds rules 012–017 for roof-to-wall coverage, wall junction continuity,
vertical load-bearing continuity, wall/opening conflicts, opening-edge
clearances and masonry modular coordination. `bim_coordination_qa.py` contains
the offline calculation logic. It has **no hard-coded regulatory distances**:
every production threshold/module must resolve to a VERIFIED Rule Registry entry
with normative or approved project provenance. Missing rule data is
`NOT_VERIFIED / DATA_MISSING`, never an assumed PASS.

Offline validation for these coordination rules is recorded in
[`docs/BIM_COORDINATION_QA_VALIDATION.md`](docs/BIM_COORDINATION_QA_VALIDATION.md).

Run `python -m unittest discover -v`. Missing evidence blocks PASS; unimplemented
or not-yet-wired live checks remain NOT_VERIFIED. The offline auditors do not
change existing runtime operations or access a live PLN.

## Collaboration workflow

The production control path is local: Qwen emits high-level intent, Safe BIM
Layer validates and verifies each Tapir operation, and Archicad is reached only
through the local bridge. GitHub is the private review boundary. Arena is used
for scoped architecture reviews and pull requests in its own branch; it never
operates a local or real Archicad project. See
[the operating model](docs/OPERATING_MODEL.md) and the
[first Arena audit brief](ARENA_TASK_ARCHITECTURE_AUDIT.md).
