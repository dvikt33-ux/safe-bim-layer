# W3 — Composite Wall thickness semantics

Environment:
- Archicad 29
- Tapir Archicad Automation 1.5.9
- Write sandbox: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`

Result: `PASS_COMPOSITE_DEFINES_PHYSICAL_THICKNESS`.

Tested Composite GUID:
`35A9ED6F-2F29-4400-B7DE-9C0DEA93A499`

Known Composite skin-sum from prior R2 readback: `0.287 m`.

## Variants

### A — requested `thickness=0.287`
- created GUID: `DECD9AD4-7F2A-4F15-9C34-2EA331F3AC87`
- observed `structureType`: `Composite`
- observed `compositeId`: `35A9ED6F-2F29-4400-B7DE-9C0DEA93A499`
- observed `begThickness`: `0.287`
- observed `endThickness`: `0.287`

### B — requested `thickness=0.500`
- created GUID: `698EC614-7C53-4BAF-9D0F-33C80358D7A7`
- observed `structureType`: `Composite`
- observed `compositeId`: `35A9ED6F-2F29-4400-B7DE-9C0DEA93A499`
- observed `begThickness`: `0.287`
- observed `endThickness`: `0.287`

### C — requested `thickness=0.100`
- created GUID: `FAF2CC4C-3A97-4DE4-BBBD-FFA0C07DEA2F`
- observed `structureType`: `Composite`
- observed `compositeId`: `35A9ED6F-2F29-4400-B7DE-9C0DEA93A499`
- observed `begThickness`: `0.287`
- observed `endThickness`: `0.287`

## Conclusion

All three walls retained the exact requested Composite and all three read back at the Composite's physical thickness of `0.287 m`, regardless of the conflicting input `thickness` value.

Evidence-backed Safe BIM rule:

> For `structureType=Composite`, the exact trusted `compositeId` is the physical-thickness source of truth. A separately requested `thickness` must be treated as a validation constraint only. Safe BIM should calculate the Composite skin-sum before creation and fail closed on mismatch rather than attempting to force another thickness.

No `Modify*`, `Delete*`, or `SaveProject` command was used in W3.
