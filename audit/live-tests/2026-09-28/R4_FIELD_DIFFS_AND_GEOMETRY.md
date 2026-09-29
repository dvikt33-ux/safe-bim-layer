# R4 field diffs and geometry readback — 2026-09-28

Source: live R4 readback audit in Archicad 29 + Tapir 1.5.9 against `Test_House_WriteSandbox.pln`.

## Beam — only R4 field differences

Element:
- label: `Балка`
- type: `Beam`
- GUID: `76BE5E50-167A-4F08-9A2E-CD621346A032`
- Archicad element ID: `БЛК - 018`

Requested in W1:
- start: `(218.0, 200.0)`
- end: `(224.0, 200.0)`
- zCoordinate: `3.0`
- height: `0.30`
- width: `0.20`

Live readback:
- start: `(218, 200)` — PASS
- end: `(224, 200)` — PASS
- zCoordinate: `3` — PASS
- height: `0.1` — DIFF
- width: `0.1` — DIFF

Additional live Beam readback fields:
- `level`: 3
- `offset`: 0
- `slantAngle`: 0
- `arcAngle`: 0
- `verticalCurveHeight`: 0
- `beamShape`: `Straight`
- `isSlanted`: false
- `isFlipped`: false
- `profileAngle`: 0
- `anchorPoint`: `Center`
- `isWidthAndHeightLinked`: false
- `profileId`: `89AF8797-218A-49CC-AFD3-30DB1CF75C03`

Interpretation limited to evidence:
- Beam placement and Z survived write/readback exactly.
- The requested 0.30 × 0.20 section did **not** read back as 0.30 × 0.20; it read back as 0.10 × 0.10.
- Because the live Beam reports a non-null `profileId`, Safe BIM must not assume that plain `width` / `height` input always controls the actual section dimensions when the active/default Beam is profile-based.
- A focused follow-up is required before treating Beam width/height as reliable across profile/default states.

## Morph specimen

GUID: `B23F010E-037C-4DE8-9C13-CB23B0032F00`

Important live readback:
- origin: `(270, 200, 0)`
- x/y/z axes: identity axes
- level: 0
- body present
- vertices show extents 0..2 on x/y/z, consistent with the requested 2 × 2 × 2 construction envelope
- bodyType read back as `Surface`
- `isClosed`: false

This confirms that a Morph body is readable, but the tested CreateMorphs box did not read back as a closed solid body according to these fields. Do not silently classify it as a closed solid.

## PolyLine specimen

GUID: `B655B27B-8651-4FDF-B9A0-A69AE6B4733B`

Live readback coordinates:
- `(210, 215)`
- `(213, 218)`
- `(216, 215)`

These exactly match the requested PolyLine coordinates.

Other readback:
- `roomSeparator`: false
- `zCoordinate`: 0

Important naming detail:
- exact Tapir element type spelling is `PolyLine`, not `Polyline`.

## Spline specimen

GUID: `1E06605B-A17A-4D4B-B269-F6A1FED5B38B`

Live readback coordinates:
- `(240, 215)`
- `(242, 218)`
- `(244, 215)`

These exactly match the requested Spline control coordinates.

Other readback:
- `closed`: false
- `roomSeparator`: false
- `zCoordinate`: 0

## Hatch specimen

GUID: `9CE18694-615E-43A1-9462-7B254BE4C8CB`

Requested polygon:
- `(250, 215)`
- `(254, 215)`
- `(254, 219)`
- `(250, 219)`

Live readback polygon:
- `(250, 215)`
- `(254, 215)`
- `(254, 219)`
- `(250, 219)`
- closing duplicate `(250, 215)`

Therefore the polygon geometry matches the requested quadrilateral, with Archicad returning the conventional closing duplicate point.

Other readback:
- `holes`: []
- `contourPenIndex`: 2
- `fillPenIndex`: 26
- `fillBackgroundPenIndex`: -1
- `showArea`: true
- `zCoordinate`: 0

## R4 totals

- expected elements: 21
- found by exact type: 21
- detailed readback supported: 19
- detailed readback unsupported: 2
- parameter checks PASS: 40
- parameter checks DIFF: 2
- verdict: `PASS_PRESENCE_WITH_FIELD_DIFFS`

Unsupported detailed readback in this set:
- Opening
- Stair

No BIM write occurred during R4.
