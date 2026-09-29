# W5 / W5B — Story, wall and window semantics (Archicad 29 + Tapir 1.5.9)

Date: 2026-09-28
Target project: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`
Tapir: 1.5.9

## W5 partial run
W5 created only the first story-0 wall, GUID `2A52916E-5405-41D2-B58A-C064509733DB`, then the Python harness stopped on a local `NameError` before further writes. The stop was in the test harness (`top` was not defined), not in Tapir/Archicad.

The first wall was intentionally reused by W5B instead of creating a duplicate.

## W5B live result
Verdict: `PASS_W5B_STORY_WALL_WINDOW`
Exit code: `0`

Scenario:
- 6 walls total
- 1 wall reused from failed W5
- 5 new walls created by W5B
- 6 windows created
- all wall checks: PASS
- all window checks: PASS

## Wall story/Z behavior

### Story 1 ordinary wall
- GUID: `96E7EFE0-EE4F-4D89-B881-57F5156D46BB`
- `floorIndex = 1`
- absolute Z = `4.5`
- `bottomOffset = 0`
- height = `3.7`

### Story 2 ordinary wall
- GUID: `82E9E9F8-8F32-4241-A2F9-A5FF5014EE93`
- `floorIndex = 2`
- absolute Z = `8.2`
- `bottomOffset = 0`
- height = `3.0`

### Story 1 wall with +0.25 m bottom offset
- GUID: `8F55728F-6FD4-4E17-8B75-21DA5C30B8CB`
- `floorIndex = 1`
- absolute Z = `4.75`
- `bottomOffset = 0.25`
- height = `3.0`

This confirms the tested behavior: with an explicit `floorIndex`, the supplied vertical coordinate behaves as a bottom offset from the home story and detailed readback returns the resulting absolute Z.

### Wall created at absolute Z=4.5 with no explicit `floorIndex`
- GUID: `EE41DAA2-66B6-4BD3-8C93-BF4C5A05AC3C`
- Archicad assigned `floorIndex = 1`
- absolute Z = `4.5`
- `bottomOffset = 0`
- height = `3.0`

Important live finding: when `floorIndex` is omitted and absolute Z lands exactly on story 1, Archicad assigns story 1 as the wall's home story in this tested project.

### One wall spanning three story levels
- GUID: `DC33F082-CED1-4C3A-AA50-C04CDE935A2C`
- `floorIndex = 0`
- absolute Z = `0`
- `bottomOffset = 0`
- height = `11.2`

The tall wall remains a single Wall element with home story 0.

## Window behavior

### Windows in three separate ordinary walls
Readback `floorIndex` values:
- story-0 wall window -> `0`
- story-1 wall window -> `1`
- story-2 wall window -> `2`

Result: `[0, 1, 2]`.

### Three windows in the single 11.2 m wall
All three windows have the same owner wall GUID:
`DC33F082-CED1-4C3A-AA50-C04CDE935A2C`

But their own readback story indices follow their vertical positions:
- sillHeight `0.9` -> window `floorIndex = 0`
- sillHeight `5.4` -> window `floorIndex = 1`
- sillHeight `9.1` -> window `floorIndex = 2`

Result: `[0, 1, 2]`.

This is a critical Safe BIM finding: windows hosted by one multi-story wall are not forced to inherit the wall's home story. Archicad assigns each window to the story corresponding to its vertical location while preserving the common owner wall.

## Safe BIM conclusions
1. Explicit `floorIndex + zCoordinate` can be used deterministically for story-relative wall placement in the tested runtime.
2. Omitting `floorIndex` and supplying absolute Z can cause Archicad to infer a home story from elevation.
3. A fixed-height wall can span multiple stories as one native Wall element.
4. Windows can be placed at different vertical levels in that one wall and still retain the same owner GUID.
5. Each such window may receive its own `floorIndex` based on vertical location.
6. Safe BIM must therefore verify both `ownerElementId` and returned window `floorIndex`; owner story alone is insufficient to describe window story placement.

No `Modify*`, `Delete*`, or `SaveProject` command was used in W5B.
