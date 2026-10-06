# Safe BIM Layer v0.1 report

## Architecture

Qwen is constrained to the high-level `create_room` tool. `safe_bim_layer.py` deterministically constructs Tapir payloads, validates them against the pinned Tapir 1.5.8 schema before writes, performs one write at a time, reads elements back, compares requested versus actual fields, validates opening host relationships, and stops on the first failure.

## Implemented operations

`create_wall_loop`, `create_basic_slab`, `insert_window`, `insert_door`, and `create_room` are implemented. Slabs are accepted only when read-back reports `structureType: Basic` and the requested numeric thickness. The current Tapir `CreateSlabs` schema exposes no direct `structureType` or `buildingMaterialId` field, so the layer does not invent one; a Composite/default result fails closed.

## Tests

- Offline schema preflight: PASS for `CreateWalls`, `CreateSlabs`, `CreateWindows`, and `CreateDoors`; zero writes.
- One requested Qwen integration probe against `C:\LocalAI\SafeBIM_v01_Integration.pln`: Qwen high-level `create_room` request timed out after the bounded 25-second probe. No low-level writes were issued, so the result is `FAIL/QWEN_HIGH_LEVEL_TOOL_CALL`, not a Safe BIM or Tapir geometry result.
- The integration copy remains free of walls, slab, doors, and windows after the failed probe.

## Known limitations

- `Tapir_ModifyWalls` may change `showOnHome false -> true`.
- The earlier slab `0.20 -> 0.30` mismatch was caused by a Composite slab, not proven thickness ignoring.
- Internal `floorPlanPolygons` may be multi-polygon; that alone is not a visual wall-join failure.
- v0.1 stops on mismatch but does not auto-rollback partial writes.
