# Archicad Detail Machine DB v2.2

Release focus: **KAIMAN / KERAKAM ceramic-block wall technical album**. The preserved source has 267 physical PDF pages. The album contains explanatory/design material on physical pages 1–35, the node index on 36–40, and **227 indexed construction-detail sheets on physical pages 41–267**.

## What changed
- Rebuilt all 227 KAIMAN/KERAKAM detail IR records around the actual source wall taxonomy instead of one generic ceramic-wall template.
- Encoded **19 source wall-type branches**: product family + facing brick/render/external insulation + source-declared loadbearing/nonbearing class.
- Added **23 source product variants** from table 3.1: ceramic units and PKB lintels with their printed envelope dimensions/technical fields. Exact internal ceramic void geometry is deliberately not reconstructed from raster images.
- Added **24 typed source-wide technical facts**, stored once and inherited by applicable detail graphs.
- Added a **227-record sheet-specific dimension queue**. Exact printed dimensions/callout endpoint binding is now an explicit next-stage task for every detail rather than an implicit generic blocker.

## Archicad machine policy
- Default architectural representation: Archicad `Wall` with thickness from the selected source product.
- Optional detailed masonry representation: source-explicit block envelope + selected horizontal bed joint 10–15 mm + half-block running bond; internal void pattern stays blocked unless a separately dimensioned/vector component is available.
- Facing-brick, render and external-insulation branches are separate and cannot be mixed.
- Where the album offers alternatives (KAIMAN 38 vs KERAKAM 38 Thermo; KERAKAM 25 vs 25XL), the machine must request/receive project selection.
- Manufacturer technical statements and cited SP/GOST references remain `claimed_by_source`; current normative validity is a separate database concern.
- Raster geometry is topology evidence only. No pixel measurement becomes a dimension.
- `commit_allowed=false` for all KAIMAN/KERAKAM details until sheet-specific dimensions and project structural parameters are resolved.

## Checks
- detail units total: 1211
- parameter facts total: 1155
- Archicad IR total: 1515
- component variants total: 536
- KAIMAN/KERAKAM detail sheets: 227
- KAIMAN/KERAKAM global source facts: 24
- KAIMAN/KERAKAM catalog variants: 23
- SQLite integrity: `ok`
- missing active detail → IR refs: 0
- source files hash-matched: 40/40