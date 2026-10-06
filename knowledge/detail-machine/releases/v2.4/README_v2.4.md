# Archicad Detail Machine DB v2.4

Release focus: **BRAAS — Узлы скатных крыш**. The complete 55-page detail album was visually re-read and rebuilt as source-bound Archicad semantics.

## What changed
- Rebuilt all 55 physical detail sheets into 11 routing families: eaves, ridges, hips, valleys, gables, wall abutments, chimney abutments, fire wall, roof break, snow retention and roof safety.
- Replaced 5 sparse legacy BRAAS facts with 22 page-specific printed/source-bound facts.
- Replaced 55 generic BRAAS IR records with 55 fail-closed v2.4 operation graphs.
- Corrected visually verified titles where the legacy normalization had added or substituted unsupported wording.
- Added 13 named BRAAS material/product variants without inventing product geometry.
- Added explicit cross-detail dependencies for the local detail sheets referenced by the album (1, 12, 24, 29/32 and 42).

## Safety invariants
- No construction dimension is derived from raster pixel scale.
- Printed dimensions without unambiguous endpoints stay unresolved rather than becoming executable offsets.
- Roof pitch/classification, structural sizes, fastener adequacy and snow/safety capacities remain project/calculation inputs.
- Manufacturer technical solutions are not promoted to verified normative requirements.
- All BRAAS v2.4 IR records remain `commit_allowed=false`.

## Checks
- detail units total: 1211
- parameter facts total: 1226
- active Archicad IR: 1211
- component variants total: 559
- BRAAS detail sheets: 55
- BRAAS active facts: 22
- SQLite integrity: `ok`
- missing active detail -> IR refs: 0
- source files SHA-256 matched: 40/40