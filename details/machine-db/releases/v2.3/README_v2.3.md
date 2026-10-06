# Archicad Detail Machine DB v2.3

Release focus: **KAIMAN / KERAKAM wall type WT1.1, sheets 1–21 (physical PDF pages 41–61)**.

## What changed
- Added **196 source-printed dimension bindings** with semantic endpoints. No dimension was measured from raster pixels.
- Bound the repeated WT1.1 wall stack (where printed): **120 + 10 + 380 + 15 = 525 mm**.
- Bound source geometry for prefabricated slab edges, window heads/sills, external-wall corners, external/internal-wall intersection, mansard/cold-attic/combined-roof junctions, plinth, monolithic slab edges and wood-beam bearing.
- Preserved corner masonry course sequencing for sheets 6–7 and opening closure logic for sheet 8.
- Wood beam source geometry now carries the printed **120×200 mm** section, **250 mm** bearing, **40 mm** lateral clearances and **20 mm** vertical clearances.
- All 21 sheets remain fail-closed: dimension coverage is intentionally marked **key printed dimensions, nonexhaustive**. Project structural sizing, alternative-product selection and any unbound secondary dimensions still block committed generation.

## Machine behavior
The Archicad IR for sheets 1–21 now runs `BIND_SOURCE_PRINTED_DIMENSIONS` before project-specific structural resolution. Exact values are bound to semantic endpoints in the local detail frame; the machine is prohibited from scaling dimensions from the drawing image.

## Checks
- detail units: 1211
- parameter facts: 1351
- Archicad IR: 1515
- v2.3 dimension bindings: 196
- SQLite integrity: `ok`
- missing detail → IR refs: 0
- KAIMAN/KERAKAM `commit_allowed=true`: 0