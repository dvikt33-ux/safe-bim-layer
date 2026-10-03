# Offline geometry-QA validation

Date: 2026-10-03. Branch: `chatgpt/archicad-modeling-standard-v1`, PR #5.

This validation covers the new isolated `bim_geometry_qa.py` checker for the
geometry evidence contracts behind BIM-QA-004 ROOF_COLLISIONS, 005 ROOF_GAPS,
006 WALL_TOPS and 007 RAFTER_ALIGNMENT.

| Verification | Result |
| --- | --- |
| New geometry-QA unit tests | **PASS: 21 tests, 0 failures, 0 errors** |
| Complete synthetic gable/roof/rafter fragment | **PASS** |
| Roof area/volume collision negative cases | **PASS: checker returns FAIL** |
| Missing/duplicate roof-pair evidence | **PASS: NOT_VERIFIED** |
| Ridge gap / wrong contact topology | **PASS: checker returns FAIL** |
| Excessive caller tolerance | **PASS: NOT_VERIFIED** |
| Stepped gable / missing native trim | **PASS: checker returns FAIL** |
| Wall protrusion / incomplete geometry proof | **PASS: FAIL / NOT_VERIFIED as designed** |
| Rafter off roof plane | **PASS: checker returns FAIL** |
| Wrong rafter bearing/upper target | **PASS: checker returns FAIL** |
| Wrong rafter native type / curved Beam | **PASS: checker returns FAIL** |
| Missing rafter geometry provenance | **PASS: NOT_VERIFIED** |
| Explicit geometry-collector failure | **PASS: BLOCKED_BY_TRANSPORT** |
| Live Archicad geometry collector | **NOT_VERIFIED** |
| Production PLN validation | **NOT_VERIFIED** |
| Main `bim_qa.py` progression wiring for 004-007 | **NOT YET PROMOTED** |

## Important boundary

The new checker does not infer roof correctness from a Tapir 3D bounding box and
does not trust planner intent as actual geometry. Tapir 1.5.8 lacks Roof
 type-specific output in `GetDetailsOfElements`, so a separate trusted geometry
collector/reference capture is required before these four rules can be promoted
to live-validated blockers in the main progression auditor.

This is deliberate: a visually plausible roof with overlapping planes or a gap
must remain `NOT_VERIFIED` until actual topology evidence exists.
