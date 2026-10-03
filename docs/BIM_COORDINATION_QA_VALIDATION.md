# Offline coordination QA validation

Date: 2026-10-03. Branch: `chatgpt/archicad-modeling-standard-v1`, PR #5.

This validation covers the offline checker for:

- BIM-QA-012 ROOF_TO_WALL_COVERAGE;
- BIM-QA-013 WALL_CONNECTIVITY;
- BIM-QA-014 VERTICAL_LOADBEARING_CONTINUITY;
- BIM-QA-015 WALL_OPENING_CONFLICT;
- BIM-QA-016 OPENING_EDGE_CLEARANCE;
- BIM-QA-017 MASONRY_MODULE_FIT.

## Result

| Verification | Result |
| --- | --- |
| New coordination QA unit tests | **PASS: 21 tests, 0 failures, 0 errors** |
| Roof ending short of required wall/overhang | **PASS: rejected** |
| Internal/exterior wall gap | **PASS: rejected** |
| Upper load-bearing wall without adequate support | **PASS: rejected** |
| Wall entering Window zone | **PASS: rejected** |
| Window corner / Door wall / pier clearance violations | **PASS: rejected** |
| Masonry module mismatch | **PASS: rejected** |
| Explicit alternate module residue | **PASS: accepted when rule permits it** |
| Missing Rule Registry entry | **PASS: NOT_VERIFIED / DATA_MISSING** |
| Unverified/incomplete normative provenance | **PASS: NOT_VERIFIED / DATA_MISSING** |
| Collector failure | **PASS: BLOCKED_BY_TRANSPORT** |
| Live Archicad / production PLN validation | **NOT_VERIFIED** |

The tests also demonstrate that changing a verified Rule Registry parameter
changes the result; the checker does not contain a hidden default minimum
window/corner, door/wall, pier, roof-overhang, support or masonry dimension.

## Important boundary

The numeric values in synthetic tests are fixtures only. They are **not**
claimed to be applicable regulations or project requirements.

Production values must come from the project's verified Rule Registry with
traceable normative document/edition/clause or approved project/reference basis.

The checker is not yet wired into live Archicad collection or the runtime
progression gate. Machine-rule entries therefore remain progression-unverified
until that wiring and live capture are completed.
