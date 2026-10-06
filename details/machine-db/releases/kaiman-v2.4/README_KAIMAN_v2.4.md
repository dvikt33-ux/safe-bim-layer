# KAIMAN / KERAKAM exact-dimension layer v2.4

Scope: **WT1.2 sheets 22–39 (physical PDF pages 62–79)**. This continues the WT1.1 exact-binding work already stored in Git commit `3cbfc4e379b54d4249badd508fb64c21886ac186`.

## Result
- Added **201 exact printed dimension bindings** for 18 WT1.2 sheets.
- Combined KAIMAN exact-binding coverage is now **39/227 sheets**.
- Remaining sheets: **188**.
- No dimension was derived from raster scale.
- All detail generation stays `commit_allowed=false`.

## Major geometry now machine-readable
- Standard WT1.2 plastered wall: `20 + 380 + 15 = 415 mm`.
- Prefab slab edge: `120 + 100 + 160 = 380 mm`, slab `220 mm`.
- Window examples: storey `3000`, sill `920`, clear opening `1680 mm`.
- External/internal wall intersection: external `415`, internal `15 + 250 + 15 = 280 mm`.
- Horizontal window coursing: normal block length `250–260 mm`, closure unit `129 mm`.
- Mauerlat source example: anchor `M12`, `L=225 mm`, recommended embedment `80 mm` (source claim, not a verified current-code requirement).
- Monolithic floor edge: `160 mm` main slab + `60 mm` downstand.
- Plinth sheet 33 is preserved as a local exception with upper wall `15 + 380 + 15 = 410 mm`.
- Wood-beam pocket: beam depth `200`, bearing `250`, vertical clearances `20 mm`.

The machine must still resolve project loads, exact structural design and any secondary source callouts before writing an exact Archicad detail.