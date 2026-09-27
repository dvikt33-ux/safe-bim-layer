# W2 — Beam semantics live test

Date: 2026-09-28

Environment:
- Archicad 29
- Tapir Archicad Automation 1.5.9
- Project: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`

Purpose: resolve the R4 Beam mismatch where `CreateBeams` requested width 0.20 m / height 0.30 m but readback returned 0.10 m / 0.10 m.

Building Material used for the explicit Basic variant:
`922C639B-9875-48DF-A3FC-E0A8AC5F2839`

## Variant A — width/height only

Request:
- width: 0.20 m
- height: 0.30 m

Live readback:
- GUID: `2A8BC3E9-8320-450D-8C99-9CC6003B6DDC`
- observed structure: PROFILE
- profileId: `89AF8797-218A-49CC-AFD3-30DB1CF75C03`
- buildingMaterialId: none
- width: 0.10 m
- height: 0.10 m
- `isWidthAndHeightLinked`: false

Result: requested rectangular dimensions were not preserved.

## Variant B — width/height + dimensions unlinked

Request:
- width: 0.20 m
- height: 0.30 m
- `isWidthAndHeightLinked=false`

Live readback:
- GUID: `5BB0E0C3-58B2-4135-A693-9B76102911A8`
- observed structure: PROFILE
- profileId: `89AF8797-218A-49CC-AFD3-30DB1CF75C03`
- buildingMaterialId: none
- width: 0.10 m
- height: 0.10 m
- `isWidthAndHeightLinked`: false

Result: unlinking dimensions alone did not switch the beam away from the inherited Profile structure and did not make width/height deterministic.

## Variant C — explicit Basic material + dimensions unlinked

Request:
- width: 0.20 m
- height: 0.30 m
- `isWidthAndHeightLinked=false`
- `buildingMaterialId=922C639B-9875-48DF-A3FC-E0A8AC5F2839`

Live readback:
- GUID: `D105DF1E-5768-4464-B6BF-124F1FFC7A72`
- observed structure: BASIC
- profileId: none
- buildingMaterialId: `922C639B-9875-48DF-A3FC-E0A8AC5F2839`
- width: 0.20 m
- height: 0.30 m
- `isWidthAndHeightLinked`: false

Result: exact requested rectangular dimensions were preserved.

## Verdict

`PASS_BASIC_BEAM_EXPLICIT_MATERIAL`

## Safe BIM rule derived from live evidence

For a rectangular Basic Beam, Safe BIM must explicitly provide a trusted `buildingMaterialId`. Passing only `width` / `height` is not deterministic because Tapir `CreateBeams` starts from the active Archicad Beam tool defaults; if those defaults are Profile-based, the result can remain Profile and the intended rectangular dimensions can be lost.

When width and height differ, Safe BIM should also explicitly set `isWidthAndHeightLinked=false`.

This test did not call `Modify*`, `Delete*`, or `SaveProject`.
