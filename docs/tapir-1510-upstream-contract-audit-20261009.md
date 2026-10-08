# Tapir 1.5.10 — upstream source audit and safe BIM geometry preflight

**Date:** 2026-10-09. **Scope:** Archicad 29.2.1 (5101) RUS;
local Tapir `GetAddOnVersion` reports `1.5.10`.
This is **not** an assertion that the checked-in 1.5.8 snapshot is the
runtime's exact native contract.

## Version provenance

Source: official public ENZYME-APD Tapir GitHub repository,
`docs/archicad-addon/command_definitions.js` at immutable tags:

- [1.5.8](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.8/docs/archicad-addon/command_definitions.js), Git SHA `ce033d6bdcc90b538b3c5f7ab62f676099b96823` — 236 commands.
- [1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/docs/archicad-addon/command_definitions.js), Git SHA `d0dbb11b13942e014661e1402b07958b70cd9dba` — 250 commands.
- [1.6.0](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.6.0/docs/archicad-addon/command_definitions.js), Git SHA `e0d4cca231f15c99da0b91cb2e591ab3758ae97a` — 258 commands.

**No official public tag or release for 1.5.10 was located in the checked
release/tag endpoints**. The local installed plugin's version is nevertheless
confirmed by the user's read-only `GetAddOnVersion` response, not guessed.
Do not relabel the 1.5.9/1.6.0 source as proven local 1.5.10.

## Exact input/output shape comparison

| Tapir command | 1.5.8 → 1.5.9 input | 1.5.9 → 1.6.0 input | Output between all three |
| --- | --- | --- | --- |
| CreateWalls | unchanged | unchanged | unchanged |
| CreateWindows | unchanged | unchanged | unchanged |
| CreateDoors | unchanged | unchanged | unchanged |
| CreateSlabs | unchanged | unchanged | unchanged |
| CreateColumns | unchanged | unchanged | unchanged |
| GetDetailsOfElements | **changed** | unchanged | **changed** in 1.5.9 |

**Documented 1.5.9 addition:** `GetDetailsOfElements` accepts an optional
`fields` array (min length 1), drawing values from
`ElementDetailsField` `["type","id","floorIndex","layerIndex",
"drawIndex","details","floorPlanPolygons","hotlinkId"]`.
The published upstream docs state that excluding `floorPlanPolygons`
avoids the expensive extraction of floor-plan drawing primitives, which
is a future readback performance opportunity. The 1.5.9 output schema
also introduces `hotlinkId` and permits filtered responses lacking
normally required fields.

**Current decision:** keep live writer read calls unchanged; test field-filter
compatibility on the installed 1.5.10 with a **read-only** request before using
it in a guarded writer. Absence of the 1.5.10 source forbids asserting exact
equivalence even where adjacent public releases match.

## Added offline plan geometry checks

For an explicitly defined **new, single, straight host Wall**:
- Window/Door opening center and explicit width must fit along wall length.
- When both `sillHeight` and `height` are explicit, the opening must fit
  between the wall's base and top; missing Favorite defaults are never guessed.
- Multiple explicit opening intervals on the same planned Wall cannot overlap.
  This includes windows against doors across different graph steps.
- Opening interval checks are **strict geometry-only**, with zero intentional
  clearance margin and no assertions about opening contours/casings.

These checks do NOT verify nested model booleans, joins, materials, measured
opening holes, clearance standards, real library-part sizes or structural
load paths. Existing walls/curved hosts and implicit Favorite dimensions
require native readback. All Windows/Doors/Slabs/Columns **remain disabled for
live execute** in this branch. A valid graph is a candidate only.

The current safe write allowlist remains the original single `CreateWalls`
host. The running Mailbox watcher is dry-run only and the existing test PLN
and model journals were not touched.

## Next gate before live hosted-opening recipes

1. Read-only test of `GetDetailsOfElements(fields)` and host Wall/Window/Door
   availability directly in Archicad 29.2.1, Tapir reported 1.5.10.
2. Pin a reproducible schema/source for the actual locally loaded plugin
   (or record verifiable uncertainty and validate each typed command boundary).
3. Develop host GUID binding with fresh parent geometry, existing opening
   inventory, Favorite resolution, edge clearance, deterministic operation
   identity, SQLite intent-before-write and singleton created GUID verification.
4. Run one bounded explicit test on the exact `Тест MER ` PLN before any
   automated dependent windows or doors. Never broaden the allowlist based on
   offline JSON Schema alone.
