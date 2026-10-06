# Archicad Detail Machine DB v2.6

Release focus: **POROTHERM / Wienerberger low-rise housing technical album**. The 105-page PDF was re-audited against its physical sheet footers and source tables.

## What changed
- Rebuilt POROTHERM source semantics for all physical technical sheets available in sections 1-12.
- Recovered **11 real source sheets** omitted by the legacy machine layer: pages 71, 72, 73, 75, 76, 77, 78, 79, 81, 101, 102.
- Active POROTHERM source now contains **73 constructible technical sheets** plus 7 retained section-header compatibility records.
- Replaced the five sparse legacy facts with **54 typed source facts**, including masonry module/bond rules, mortar/joint parameters, slab-bearing rules, parapet/plinth protection and sheet 12.1 mesh/anchor data.
- Added **23 source-traceable component variants** covering POROTHERM blocks, TERCA facing bricks, masonry mixes and sheet-12.1 meshes/anchors.
- Added source-bound compiler branches for basement foundations, foundation slabs, floor-wall junctions, external/internal wall junctions, corners, internal walls/ducts, pitched-roof junctions, flat-roof parapets, bay windows and mesh/anchor hardware.

## Source anomalies preserved
- The printed TOC lists section 1 as `1.1-1.4`, but the physical album contains sheet `1.5` on PDF page 25. The physical footer is canonical.
- Source spellings `PHOROTERM/PHOROTHERM` on some sheets and the blind-area slope literal `1:1,1` are not silently normalized into geometry.
- The album cites 2011-2016-era SP/GOST/SNiP editions; those remain `claimed_by_source`, not automatically current/verified rules.

## Machine safety
- No construction dimension is measured from raster scale.
- Product catalog geometry uses verified rectangular envelopes only; internal block void geometry is not synthesized.
- Structural sizing, reinforcement, anchors, foundation/roof capacities and exact project levels remain project-engineering inputs.
- `commit_allowed=false` for all POROTHERM v2.6 IR records.

## Current state
- detail units: 1222
- parameter facts: 1294
- Archicad IR rows: 1595
- active detail -> IR bindings: 1222
- component variants: 598
- POROTHERM active machine records: 80
- SQLite integrity: `ok`
- missing active detail -> IR refs: 0
- source representations hash-matched: 40/40