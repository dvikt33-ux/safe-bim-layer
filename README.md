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
