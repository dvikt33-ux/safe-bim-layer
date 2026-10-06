# KAIMAN / KERAKAM exact-dimension layer v2.5

Scope: **WT1.3 sheets 40–47 (physical PDF pages 80–87)**. This continues v2.4 from Git commit `a5eb3eee68817925ecfebb0fb22ab6b8fbe59f03`.

## Result
- Added **139 exact printed dimension bindings** for 8 WT1.3 sheets.
- Combined KAIMAN exact-binding coverage: **47/227 sheets**.
- Remaining: **180 sheets**.
- Cumulative exact bindings: **536**.
- No dimensions were derived from raster scale.
- All generation remains `commit_allowed=false`.

## Major geometry now machine-readable
- WT1.3 brick-faced wall stack: `120 + 10 + 380 + 15 = 525 mm`.
- Window examples: storey `3000`, sill `940`, clear opening `1630 mm`.
- Balcony branch: slab depth `160`, wall-side slab/support depth `250`, lower foam `30 mm`.
- Flat-slab branch: main slab depth `180`, lower layer `30 mm`.
- Flat-slab window-head chain: `120 + 10 + 120 + 140 + 120 + 15 mm`; KERAKAM x2 height `138`, interlayer `10`, PKB lintel height `65 mm`.

## Important source mismatch
The overall-section sheets 40/42/44/46 print **80 mm** for the upper insulation segment, while their paired enlarged nodes 41/43/45/47 print **150 mm**. The machine keeps both sheet-local values and blocks automatic aliasing. Node 1 also uses a printed `230 mm` inner structural zone whereas node 3 uses `290 mm`.

These are manufacturer technical-album values, not independently verified current-code requirements.