# Archicad Detail Machine DB v2.3

Release focus: **ROCKFACADE 2022**. The PDF, DXF and DWG representations were cross-checked and the 101 machine sheets on physical PDF pages 8-108 were rebuilt around the **actual sheet footer**, not the album TOC.

## What changed
- Exact sheet index: 101/101 physical sheets now have source page, actual sheet code and exact footer title.
- Added DXF vector evidence for every sheet: per-sheet entity counts, vector cell coordinates, handles and printed DIMENSION annotations.
- Preserved a critical scale guard: raw DXF lengths are not treated as real construction dimensions because the source contains sheet/detail scaling and manual dimension overrides.
- Replaced 90 legacy ROCKFACADE parameter facts with 144 cleaner source facts/printed annotations.
- Added 10 named ROCKFACADE material/product catalog nodes without inventing product geometry.
- Added a source-bound Archicad routing grammar for sections 1-12.

## Source inconsistency found
The printed TOC is not identical to the physical sheet set. It lists section 1 as 1.1-1.13, including three Lamella-specific sheets, but the actual sheet footers contain only 1.1-1.10. Conversely, the TOC lists section 7 only through 7.6, while physical sheets 7.7-7.9 also exist. The machine therefore treats **actual sheet footers as canonical** and never fabricates TOC-only details.

## Checks
- detail units total: 1211
- parameter facts total: 1209
- Archicad IR total: 1515
- component variants total: 546
- ROCKFACADE sheets: 101
- ROCKFACADE active facts: 144
- DXF DIMENSION entities mapped: 126
- SQLite integrity: `ok`
- missing active detail -> IR refs: 0
- ROCKFACADE source representation hashes matched: 3/3
- `commit_allowed=true` for ROCKFACADE: 0