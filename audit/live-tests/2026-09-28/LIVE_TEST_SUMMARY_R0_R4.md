# Live Archicad / Tapir verification summary — 2026-09-28

Environment:
- Archicad 29
- Tapir Archicad Automation 1.5.9
- Read specimen: `C:\Users\Admin\Downloads\Test_House.pln`
- Write sandbox: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`

This file records only results observed in live runs. It does not infer unsupported write semantics from readback.

## R0 — identity gate

Result: PASS.

Confirmed live:
- Tapir version exactly `1.5.9`.
- Project path exactly `C:\Users\Admin\Downloads\Test_House.pln`.
- `GetStories` succeeded.
- No BIM write command was included in the probe allowlist.

Observed stories:
- index 0: level 0.0, height 4.5, name `Первый Этаж`
- index 1: level 4.5, height 3.7
- index 2: level 8.2, height 3.0
- index 3: level 11.2, name `Story 3`
- active story: 1

## R1 — geometry inventory

Result: PASS, read-only.

Confirmed live in the current database at the time of the run:
- Roof: 0
- Wall: 10
- `GetDetailsOfElements` succeeded for walls.

Important limitation: Roof count 0 meant only that no Roof was present in the current database at that moment; it did not test Roof readback capability.

## R1.1 — wall detail extraction

Confirmed live:
- Basic walls used the same Building Material GUID with different wall thicknesses (0.25 m and 0.30 m).
- Composite walls using Composite GUID `35A9ED6F-2F29-4400-B7DE-9C0DEA93A499` all read back as 0.287 m.
- Basic and Composite wall details expose `begThickness` / `endThickness` rather than a single `thickness` field.

This proves readback state only. It does not by itself prove how `CreateWalls` handles Composite thickness input.

## R2 — exact composite readback

Result: PASS, read-only.

Exact Composite GUID:
`35A9ED6F-2F29-4400-B7DE-9C0DEA93A499`

Observed skin thicknesses:
- 0.100 m
- 0.050 m
- 0.025 m
- 0.100 m
- 0.012 m

Computed sum: 0.287 m.

That exactly matched the 0.287 m readback thickness of the four walls using this Composite.

`GetComposites` did not return a `totalThickness` field in this live run; total thickness was computed from the skins.

## R3 — manually created golden specimens

Result: PASS, read-only.

Observed top-level elements:
- Walls: 16
- Roofs: 4
- Curtain Walls: 3
- Shells: 2
- Railings: 1
- Skylights: 5

All four observed roofs were `MultiPlane`, Composite, 0.3 m thick. Their readback exposed fields such as:
- `roofClass`
- `structureType`
- `thickness`
- `level`
- `levels`
- `pivotPolygonOutline`
- `polygonOutline`
- `eavesOverhang`

The live roof readback did **not** contain:
- `pivotPolyEdges`
- `angleType`
- `Gable` / `gable`

Therefore Tapir 1.5.9 can identify and read MultiPlane roofs, but `GetDetailsOfElements` does not expose per-edge gable/sloped edge classification in this live AC29 test.

Other R3 findings:
- Polygonal walls were identified as `Polygonal`; their `begThickness` / `endThickness` read back as 0, so those fields must not be treated as generic polygonal-wall thickness.
- A slanted wall returned non-vertical slant angles.
- Curtain Wall parent details were partially supported (`height`, `angle`, `flipped`).
- Shell parent details returned `Not yet supported element type`.
- Railing parent details returned `Not yet supported element type`.
- Skylight details returned `Not yet supported element type`.

Hierarchical subelement inventory:
- Curtain Walls: 553 child GUIDs total
  - 387 frames
  - 162 panels
  - 4 segments
- Railing: 1173 child GUIDs total, including balusters, baluster sets, posts, inner posts, nodes, rails, handrails, toprails, segments and connection/end elements.

## W1 / W1B — controlled write sandbox

Target project:
`C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`

W1 created elements sequentially with immediate GUID verification. The run stopped after the PolyLine step because the verifier used the wrong type spelling (`Polyline` instead of Tapir's exact `PolyLine`). The PolyLine itself was created successfully.

W1B corrected the type name and verified the existing PolyLine, then continued.

Final combined result: 21 created specimens, each present by exact type.

Created specimen set:
1. Wall
2. Window
3. Door
4. Opening
5. Column
6. Beam
7. Slab with one hole
8. Single-plane Roof at 20°
9. Mesh
10. Stair
11. Morph box
12. Zone
13. Line
14. PolyLine
15. Arc
16. Circle
17. Spline
18. Hatch
19. Hotspot
20. Text
21. Label

No `SaveProject`, `OpenProject`, `Modify*`, or `Delete*` command was used in W1B.

## R4 — readback audit of 21 written specimens

Result: `PASS_PRESENCE_WITH_FIELD_DIFFS`.

Confirmed live:
- Expected specimens: 21
- Found by exact type: 21 / 21
- Detailed readback supported: 19
- Detailed readback unsupported: 2
- Parameter comparisons PASS: 40
- Parameter comparisons DIFF: 2

Detailed readback unsupported for:
- Opening — `Not yet supported element type`
- Stair — `Not yet supported element type`

The only two field differences were on the Beam:
- requested height 0.30 m, read back 0.10 m
- requested width 0.20 m, read back 0.10 m

The W2 focused test below resolved the cause.

For Morph, PolyLine, Spline and Hatch, creation + presence + detailed readback were confirmed, but the generic R4 comparator did not have automatically comparable request/readback fields. Their live readback data is recorded in the companion report.

## W2 — Beam structure/size semantics

Result: `PASS_BASIC_BEAM_EXPLICIT_MATERIAL`.

Three isolated `CreateBeams` variants were created and immediately read back:

### A — width/height only
- requested width 0.20 m, height 0.30 m
- observed structure: PROFILE
- observed profile GUID: `89AF8797-218A-49CC-AFD3-30DB1CF75C03`
- observed width 0.10 m, height 0.10 m
- result: requested dimensions did not take effect as intended

### B — width/height + `isWidthAndHeightLinked=false`
- requested width 0.20 m, height 0.30 m
- observed structure: PROFILE
- observed profile GUID: `89AF8797-218A-49CC-AFD3-30DB1CF75C03`
- observed width 0.10 m, height 0.10 m
- result: unlinking dimensions alone did not solve the problem

### C — width/height + `isWidthAndHeightLinked=false` + explicit Building Material
- Building Material GUID: `922C639B-9875-48DF-A3FC-E0A8AC5F2839`
- observed structure: BASIC
- observed width 0.20 m
- observed height 0.30 m
- no profileId in readback
- result: exact requested rectangular dimensions were preserved

Evidence-backed Safe BIM rule:

> When Safe BIM intends to create a rectangular Basic Beam, it must explicitly provide a trusted `buildingMaterialId` (and should set `isWidthAndHeightLinked=false` when width and height differ). Passing only `width` / `height` is not deterministic because `CreateBeams` inherits the current Archicad Beam tool defaults; a Profile default can remain Profile and ignore the intended rectangular dimensions.

W2 did not call `Modify*`, `Delete*`, or `SaveProject`.

## Current evidence-backed capability map

| Element / capability | Create | Exact-type presence | Detailed readback | Notes |
|---|---:|---:|---:|---|
| Wall | yes | yes | yes | Basic/Composite/polygonal/slanted specimens observed |
| Window | yes | yes | yes | W1/R4 passed |
| Door | yes | yes | yes | W1/R4 passed |
| Opening | yes | yes | no | `GetDetailsOfElements`: not yet supported |
| Column | yes | yes | yes | W1/R4 passed |
| Beam | yes | yes | yes | Basic rectangular dimensions are deterministic when explicit trusted `buildingMaterialId` is supplied; width/height alone can inherit Profile defaults |
| Slab | yes | yes | yes | hole count and polygon readback passed |
| Single-plane Roof | yes | yes | yes | 20° specimen passed |
| Multi-plane Roof | not proven by W1 | yes | yes | manual specimens read successfully; no per-edge Gable classification exposed |
| Mesh | yes | yes | yes | basic specimen passed |
| Stair | yes | yes | no | `GetDetailsOfElements`: not yet supported |
| Morph | yes | yes | yes | detailed body readback available |
| Zone | yes | yes | yes | W1/R4 passed |
| Line | yes | yes | yes | W1/R4 passed |
| PolyLine | yes | yes | yes | exact type spelling is `PolyLine` |
| Arc | yes | yes | yes | W1/R4 passed |
| Circle | yes | yes | yes | W1/R4 passed |
| Spline | yes | yes | yes | detailed coordinate readback available |
| Hatch | yes | yes | yes | detailed polygon/fill readback available |
| Hotspot | yes | yes | yes | W1/R4 passed |
| Text | yes | yes | yes | W1/R4 passed |
| Label | yes | yes | yes | W1/R4 passed |
| Curtain Wall | not tested for create | yes | partial | parent basics + hierarchy supported |
| Shell | not tested for create | yes | no | details unsupported |
| Railing | not tested for create | yes | no (parent) | hierarchy supported |
| Skylight | not tested for create | yes | no | details unsupported |

## Safety conclusions from live work

- Exact version and exact project-path gates are practical and worked in live AC29.
- Sequential one-element writes with immediate GUID verification provide much stronger evidence than bulk creation.
- A returned GUID alone is not sufficient; exact-type presence and readback should be checked when supported.
- Unsupported detail types must be treated explicitly as unsupported rather than silently accepted.
- MultiPlane roof readback is insufficient for reconstructing per-edge gable semantics in stock Tapir 1.5.9.
- For a rectangular Basic Beam, Safe BIM must not rely on `width` / `height` alone. It must explicitly select a trusted Building Material to force Basic structure, and should explicitly unlink width/height when asymmetric dimensions are required.
