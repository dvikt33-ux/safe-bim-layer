# Final audit addendum — native single-element Gable Roof

This addendum supersedes the earlier research recommendation that the final deterministic gable should be represented as two independent Single-plane Roof elements.

## Corrected conclusion

A simple gable should target **one native Archicad Multi-plane Roof (`API_PolyRoofID`)**.

Archicad's C++ API explicitly supports per-pivot-edge segment types via `API_PivotPolyEdgeData -> API_RoofSegmentData -> API_PolyRoofSegmentAngleTypeID`, including `Sloped` and `Gable`.

The reason the earlier research fell back to two Single-plane roofs is narrower: **stock Tapir 1.5.9 does not expose the pivot-edge segment type through `CreateRoofs` or current RoofDetails readback.**

Therefore:

- Archicad capability: YES;
- stock Tapir 1.5.9 capability: insufficient;
- recommended solution: narrow Tapir extension/fork with typed pivot-edge input + readback;
- final Safe BIM representation: one Roof GUID;
- two Single-plane roofs: fallback/probe only;
- production enablement: still NO until offline implementation, independent audit and controlled AC29 live certification.

See:

- `../03_archicad_api_contracts/SINGLE_ELEMENT_GABLE_ROOF_RESEARCH_PASSES_01_20.md`
- `../06_integration_audits/SINGLE_ELEMENT_GABLE_ROOF_INTEGRATION_AUDIT.md`

## Required next implementation block

`Tapir 1.5.9 — Native PolyRoof Gable Extension`

DONE means:

1. custom capability identity distinct from stock Tapir 1.5.9;
2. `CreateRoofs` accepts validated per-pivot-edge `Sloped/Gable` segment data;
3. native memo allocation follows documented polygon edge indexing;
4. RoofDetails returns authoritative per-edge segment data;
5. offline malformed-input/memory/error-path tests pass;
6. Safe BIM remains production-disabled;
7. independent source/code audit passes;
8. only then one controlled single-GUID gable probe is eligible for approval.
