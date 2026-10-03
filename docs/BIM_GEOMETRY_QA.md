# Roof / wall-top / rafter geometry QA contract

Status: **offline checker implemented; live collector not yet verified**  
Module: `bim_geometry_qa.py`  
Rules: BIM-QA-004, 005, 006, 007.

## Why this package is separate

The pinned Tapir 1.5.8 schema exposes `BeamDetails` through `GetDetailsOfElements`
(including beam plan endpoints, z/level, slant angle, shape and arc data) and exposes
`Get3DBoundingBoxes`. It does **not** expose Roof type-specific details in the
`TypeSpecificDetails` union. Therefore an axis-aligned roof bounding box is not
sufficient evidence to claim that valleys, ridges, gaps or roof-solid intersections
are correct.

Safe BIM must not convert this transport limitation into a false PASS. The geometry
rules therefore require complete evidence from a trusted geometry collector or a
validated reference-model capture. Until such a collector is connected to a live
Archicad copy, live validation remains `NOT_VERIFIED`.

## Evidence contract

All geometry evidence is bound to `projectId`, `snapshotId` and `auditScope` and
requires a complete scoped native element inventory.

### BIM-QA-004 / 005: roof topology

Required fields:

- `roofTopologyComplete: true`
- `roofGuids`: the complete scoped Roof GUID list
- `roofPairEvidenceComplete: true`
- `roofPairEvidence`: exactly one unordered record for every pair of scoped roofs

Each pair record contains:

```json
{
  "a": "roof-left",
  "b": "roof-right",
  "expectedRelation": "RIDGE",
  "actualRelation": "EDGE",
  "gapDistance": 0.0002,
  "gapTolerance": 0.001,
  "probeComplete": true
}
```

`expectedRelation` is one of `DISJOINT`, `POINT_TOUCH`, `RIDGE`, `VALLEY`, `HIP`,
`SEAM`. `actualRelation` is one of `DISJOINT`, `POINT`, `EDGE`, `AREA_OVERLAP`,
`VOLUME_OVERLAP`, `CROSSING`.

The checker fails unresolved area/volume/crossing collisions. Expected ridge,
valley, hip and seam pairs must have edge contact and close within a bounded gap
tolerance. Caller-supplied tolerances are capped; they cannot be enlarged enough
to hide bad geometry.

### BIM-QA-006: wall tops

Required fields:

- `wallRoofRelationsComplete: true`
- `roofAdjacentWallGuids`: complete scoped wall list
- `wallRoofRelations`: one record per roof-adjacent wall

A valid relation identifies the controlling Roof GUIDs and proves a native
relationship such as `TRIM_TO_ROOF_SHELL`, `SEO` or another reviewed native roof
relationship. It must also prove:

- operation applied;
- no stepped-wall reconstruction;
- no protrusion beyond the accepted roof envelope over bounded tolerance;
- geometry verification completed.

A manually stacked gable cannot pass this rule even if its visible silhouette is
close to the roof.

### BIM-QA-007: rafters

Required fields:

- `rafterEvidenceComplete: true`
- `rafterGuids`: complete scoped Beam rafter list
- `rafterEvidence`: one record per rafter

Each record binds a native Beam to one accepted Roof plane and contains actual or
reconstructed 3D beam-axis endpoints, bearing point, upper ridge/valley/hip target,
roof-plane point/normal and provenance for both axis and roof-plane geometry.

The checker verifies:

- element type is Beam;
- referenced roof element type is Roof;
- straight/non-curved rafter where Beam read-back exposes shape data;
- both axis endpoints lie on the intended roof plane within bounded tolerance;
- one axis endpoint reaches the intended bearing point;
- the other reaches the intended upper target.

## Fail-closed behavior

Missing completeness, malformed geometry, missing provenance, incomplete pair
coverage or excessive tolerance is `NOT_VERIFIED`. An explicit geometry collector
or transport failure is `BLOCKED_BY_TRANSPORT`. Neither permits progression.

The current main `bim_qa.py` progression auditor has not yet promoted rules 004-007
to implemented status. `bim_geometry_qa.py` is the tested geometry-evidence checker
that will be wired into progression only after a trusted live collector can produce
this contract without planner self-attestation.
