# Archicad Detail Machine DB v2.5

Release focus: **BRAAS technical manual — constructions, laying and arrangement of tile roofing** (222-page source).

## What changed
- Rebuilt all 87 pre-existing `BRAAS_ROOF_TECH` machine cards as source-bound v2.5 rules, assemblies, selection tables, product references, maintenance/safety rules or section aliases.
- Replaced 74 generic/unbound legacy facts with 93 typed active source facts, including critical values from pages that the old detail extractor had skipped.
- Replaced 87 generic IR records with 87 fail-closed v2.5 IR records.
- Corrected every active card title/routing class from the actual manual section meaning rather than text-fragment extraction.
- Reclassified section-22 heading pages (106, 136, 142, 149, 161) as reference-only and route them to the already processed `BRAAS_ROOF_DETAILS` detail families instead of pretending the heading page itself contains build geometry.
- Added 16 source product/catalog variants from the appendices: membranes, ventilation products, sealing products, vapor barriers and associated materials.
- Added explicit source anomalies for the Range-1/Range-2 wording conflict, Opal wind-clip product-code conflict and the printed descending Difodamm installation temperature range.

## Important machine rules
- Tile model + roof slope must be selected before model-specific LAF/LA/PUT/LAT rules can execute.
- Structural sizes/loads and fastener capacities stay project/calculation inputs.
- Wind and snow tables are manufacturer-source evidence and require current normative/project validation before committed use.
- No distance is measured from raster drawings.
- Manufacturer-cited SP/GOST references remain `claimed_by_source_not_independently_verified`.
- All BRAAS technical-manual v2.5 records remain `commit_allowed=false`.

## Checks
- detail units total: 1211
- parameter facts total: 1245
- active detail → IR records: 1211
- all IR rows including history: 1515
- component variants total: 575
- BRAAS technical cards: 87
- BRAAS technical active facts: 93
- SQLite integrity: `ok`
- missing active detail → IR refs: 0
- source files SHA-256 matched: 40/40