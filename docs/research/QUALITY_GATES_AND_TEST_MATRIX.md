# Safe BIM Quality Gates and Test Matrix

This document defines concrete checks that generated Archicad models should pass before the runtime declares them ready.

The goal is to replace subjective “looks okay” validation with layered geometric, semantic, connection and architectural checks.

---

# 1. Severity model

```text
BLOCKER  Model cannot continue safely.
ERROR    Model can exist but cannot be declared MODEL_READY.
WARNING  Model is usable but contains a quality concern.
INFO     Diagnostic only.
```

A pass may continue after WARNING/INFO. BLOCKER stops before further dependent writes. ERROR normally stops finalization but may allow diagnostics/refinement.

---

# 2. Gate sequence

```text
G0  Input/spec validation
G1  Canonical topology
G2  Pre-write geometry
G3  Post-write read-back
G4  Connection/interface validation
G5  Collision scan
G6  Gap/continuity scan
G7  Freeform topology
G8  Architectural alignment
G9  Model reliability / finalization
```

---

# 3. G0 — Input/spec validation

| Check | Severity | Rule |
| --- | --- | --- |
| Project identity | BLOCKER | runtime must target explicitly selected project copy |
| Tapir/schema compatibility | BLOCKER | installed provider must match pinned/accepted schema policy |
| Story resolution | BLOCKER | every story reference resolves to factual elevation |
| Project datum | BLOCKER for survey/site | sea-level/project-zero conversion must be explicit |
| Missing required design parameter | BLOCKER | never guess a required dimension marked authoritative |
| StyleKit favorite missing | ERROR/WARNING by profile | fallbacks must be explicit and logged |
| Invalid unit | BLOCKER | all internal geometry normalized to project SI convention |

---

# 4. G1 — Canonical topology gate

## Vertices

- unique IDs;
- finite coordinates;
- snap to canonical shared identity only when declared equivalent;
- no two canonical vertices closer than duplicate tolerance unless intentionally distinct.

## Edges

- start != end;
- finite length;
- no duplicate edge with same semantics;
- no opposite duplicate edge representing the same wall boundary;
- valid owning loop(s).

## Loops

- at least three non-collinear vertices;
- closed by topology, not merely by approximate coordinate;
- no self-intersection;
- no duplicate consecutive vertex;
- normalized winding;
- finite non-zero area.

## Space adjacency

For internal shared boundaries:

```text
space A says adjacent to B
=> space B must say adjacent to A
=> both reference the same canonical edge
```

Failure is BLOCKER.

---

# 5. G2 — Pre-write element checks

## Wall

Mandatory:

- canonical edge valid;
- height > 0;
- thickness > 0;
- story exists;
- reference-line convention resolved;
- start/end connection intent defined;
- no exact duplicate WallPlan fingerprint.

Additional:

- if wall is exterior, orientation/inside-outside direction should be deterministic;
- if wall ends at another declared wall, reference-line nodes must coincide;
- if host openings exist, usable host length must contain all opening intervals.

## Slab

Mandatory:

- polygon simple;
- area > epsilon;
- thickness > 0;
- reference plane valid;
- no coplanar duplicate owned by the run.

Flag ERROR if two slab polygons on the same story substantially overlap without declared assembly intent because slab-slab collision does not automatically clean up in Archicad.

## Roof

Mandatory:

- all face polygons simple;
- slope > 0 when sloped roof intended;
- each internal ridge/valley edge has two owners;
- elevation from both adjacent faces agrees at shared edge within tolerance;
- no face self-intersection;
- no duplicate coplanar face;
- support/trim wall set identified before final connection pass.

## Column

Mandatory:

- position derives from declared grid/local support;
- dimensions > 0;
- height > 0;
- no duplicate at same support location/story unless assembly explicitly permits.

## Door/Window

Mandatory:

- host GUID/type known;
- local center/interval inside wall span;
- width/height > 0;
- vertical interval fits intended host envelope;
- no overlap with another opening on same host unless intentional.

## Mesh

Mandatory:

- one continuous boundary per intended terrain element;
- valid XYZ;
- no self-intersecting boundary;
- contour/breakline data do not contradict declared datum;
- no duplicate surface created by the same source dataset.

## Morph

Mandatory pre-write solid checks:

- all face indices valid;
- no polygon has <3 unique vertices;
- no zero-length edges;
- no duplicate faces;
- no isolated vertices for solid body;
- every undirected edge incidence = 2 for closed solid;
- consistent orientation;
- non-zero finite volume estimate;
- no self-intersection if exact/triangle test available.

---

# 6. G3 — Post-write read-back gate

Every mutation produces a receipt.

Required receipt fields:

```json
{
  "run_id": "...",
  "step_id": "...",
  "operation": "...",
  "input_hash": "...",
  "guid": "...",
  "semantic_type": "Wall",
  "normalized_expected": {},
  "normalized_actual": {},
  "geometry_fingerprint": "...",
  "status": "VERIFIED_PASS"
}
```

## Read-back normalization rules

### Points

Coordinate differences within configured tolerance are equal.

### Polygon equivalence

Accept:

- cyclic vertex shift;
- reversed winding if semantically irrelevant;
- explicit closing point vs implicit closure;
- coordinate noise within tolerance.

Reject:

- missing corner;
- changed topology;
- different hole set;
- substantial area/bounds mismatch.

### Element identity

A successful create must return a new owned GUID or be reconciled to exactly one new fingerprint after an uncertain response.

Never silently adopt a pre-existing foreign element merely because geometry matches.

---

# 7. G4 — Connection/interface gate

Connections must be modeled as first-class data.

## Wall-wall

Check:

- canonical node shared;
- Archicad reference lines intersect;
- junction classification expected;
- material priorities/junction order compatible with desired cleanup.

## Wall-roof

Preferred:

- verified `TrimElements` relationship where appropriate.

Check:

- wall does not end materially below intended roof underside;
- wall does not visibly penetrate roof beyond intended trim;
- trim relation references correct roof and wall GUIDs.

## Solid Element Operation

For each expected boolean relation:

```text
target
operator
operation
flags
```

must be stored and verified through `GetSolidElementLinks` when possible.

## Wall-opening

Host relation is mandatory, not inferred from proximity.

## Terrain/building

Require explicit interface classification:

- `ABOVE_GRADE`
- `CUT_INTO_TERRAIN`
- `RETAINED_EDGE`
- `FOUNDATION_INTERFACE`
- `ROAD_ON_GRADE`

Unknown site intersection is ERROR.

---

# 8. G5 — Collision matrix

The collision engine must not treat all intersections equally.

## Matrix categories

```text
ALLOW_TOUCH
ALLOW_DECLARED_OVERLAP
REQUIRE_CONNECTION
REQUIRE_BOOLEAN
FORBID_OVERLAP
PROJECT_RULE
```

Example default matrix:

| A | B | Default |
| --- | --- | --- |
| Wall | Wall | REQUIRE_CONNECTION |
| Wall | Slab | PROJECT_RULE |
| Wall | Roof | REQUIRE_CONNECTION |
| Wall | Door/Window | ALLOW_DECLARED_OVERLAP |
| Slab | Slab | FORBID_OVERLAP unless assembly declared |
| Column | Slab | ALLOW_DECLARED_OVERLAP |
| Column | Wall | PROJECT_RULE |
| Roof | Roof | REQUIRE_CONNECTION if adjacent; otherwise FORBID_OVERLAP |
| Morph | Morph | FORBID_OVERLAP unless assembly/boolean declared |
| Mesh | Wall/Slab | PROJECT_RULE / terrain interface |

## Broad phase

Use AABB spatial index.

Per element store:

```text
xmin xmax
ymin ymax
zmin zmax
```

Query only spatial neighbors.

## Narrow phase

Type-specific tests:

- line/reference-line intersection;
- polygon intersection/containment;
- vertical interval overlap;
- plane-vs-volume intersection;
- triangle intersection for Morph validation.

## Duplicate geometry

Duplicates are a special collision class with much stronger evidence:

- same semantic type;
- same story;
- normalized geometry fingerprint equal;
- materially same parameters.

Run-owned duplicate = ERROR.

---

# 9. G6 — Gap and continuity gate

## Room enclosure

A room expected to be enclosed must have a closed boundary graph.

Checks:

- every boundary node has expected degree;
- no dangling edge;
- no missing edge between adjacent boundary vertices;
- boundary loop area consistent with intended room polygon.

## External envelope

Check each story/envelope band for:

- perimeter continuity;
- corners connected;
- roof enclosure continuity;
- openings intentionally bounded by hosts.

## Roof

For every internal roof edge:

- exactly two adjacent faces unless edge declared opening/eave;
- shared world-space edge coordinates match;
- shared elevation matches;
- ridge/valley semantic classification consistent.

## Morph

For solid Morph every edge must be incident to exactly two faces. This mirrors Graphisoft’s own solidity definition.

---

# 10. G7 — Freeform topology and geometry gate

Inspired by Graphisoft Morph solidity requirements and polygon-mesh repair practice.

## Topological checks

- edge incidence;
- connected components;
- consistent orientation;
- closed shell for Solid;
- no dangling faces/edges.

## Geometric checks

- no zero-area triangle after triangulation;
- no nearly collinear pathological face below threshold;
- no self-intersection;
- no overlapping duplicate face;
- no inverted local normal relative to component orientation;
- valid finite volume.

## Repair policy

Safe automatic repairs:

- remove duplicate closing vertex;
- normalize orientation;
- merge truly duplicate vertices inside snap tolerance if topology says they are identical;
- triangulate non-planar validation representation.

Unsafe automatic repairs:

- fill large missing surfaces without source design intent;
- merge nearby but semantically distinct components;
- arbitrarily move vertices to eliminate self-intersection.

---

# 11. G8 — Architectural alignment and visual quality gate

This gate makes the difference between technically valid geometry and a convincing architectural model.

## Façade alignment

For each alignment group:

- sill levels align within tolerance;
- head levels align within tolerance;
- vertical bay axes align;
- family widths/heights obey allowed variants;
- exceptions must be explicitly tagged.

## Structural rhythm

- columns align with structural grid;
- walls intended to align with grid do so;
- repeated bay widths follow pattern;
- no unexplained 20–50 mm drift accumulated by repeated arithmetic.

## Corners

- openings do not collide with corner cleanup zones;
- façade modules terminate intentionally;
- cladding/detail system has an explicit corner rule.

## Roof composition

- roof slopes belong to allowed style family;
- ridge hierarchy corresponds to mass hierarchy;
- secondary roofs do not accidentally penetrate primary roof;
- eaves/overhangs use consistent rules.

## Material coherence

- each semantic family resolves to intended Favorite/material/composite/profile;
- random tool defaults are not accepted as final architectural styling.

---

# 12. G9 — Reliability / LOD-like readiness gate

Suggested internal target tags:

```text
CONCEPT_GEOMETRY
DESIGN_GEOMETRY
COORDINATION_GEOMETRY
FABRICATION_DETAIL_UNSUPPORTED
```

`DESIGN_GEOMETRY` should roughly correspond to LOD 300-like reliability for owned elements:

- specific measurable size;
- shape;
- location;
- orientation.

`COORDINATION_GEOMETRY` should additionally require important interfaces, similar in spirit to LOD 350.

Safe BIM must not mark an element at a reliability level higher than the data and checks actually support.

---

# 13. Unit test matrix

## Polygon normalization

1. Same polygon, different start index -> PASS equal.
2. Same polygon, reversed winding -> PASS equal when orientation not significant.
3. Same polygon with repeated closing point -> PASS equal.
4. One corner moved above tolerance -> FAIL.
5. Bow-tie polygon -> pre-write BLOCKER.
6. Polygon with duplicate consecutive vertex -> normalized or BLOCKER according to profile.

## Wall topology

1. L-junction shared canonical node -> PASS.
2. Visible wall bodies touch but reference-line endpoints differ -> FAIL connection.
3. Two identical walls same edge/story -> duplicate ERROR.
4. T-junction with declared third wall -> PASS after reference-line validation.

## Openings

1. Window inside host interval -> PASS.
2. Window crosses wall endpoint -> ERROR.
3. Two windows overlap -> ERROR unless declared grouped system.
4. Host GUID points to non-Wall -> BLOCKER.

## Roof

1. Two roof faces share exact ridge -> PASS.
2. Same XY ridge but different computed ridge height -> ERROR.
3. Wall reaches roof and verified trim exists -> PASS.
4. Wall penetrates roof with no declared trim -> ERROR.

## Morph

1. Closed cube -> PASS.
2. One face missing -> non-manifold ERROR.
3. One face reversed -> orientation ERROR/repairable.
4. Duplicate coplanar face -> ERROR.
5. Self-intersecting solid -> ERROR.

## Terrain

1. Single Mesh with coherent XYZ sublines -> PASS.
2. Two run-owned identical terrain Meshes -> duplicate ERROR.
3. Survey point datum inconsistent with configured datum -> BLOCKER.
4. Unknown region extrapolated beyond source-data policy -> ERROR/WARNING depending profile.

## Resume/reconciliation

1. verified receipt + rerun -> skip element.
2. response lost but exactly one new fingerprint found -> reconcile and verify.
3. response lost and two candidate new elements exist -> RECONCILIATION_REQUIRED.
4. pre-existing coincident foreign element -> never auto-adopt.

---

# 14. Integration test scenes

Maintain a small deterministic suite of Archicad test scenes/specs.

## Scene A — Clean room box

Tests:

- four-wall loop;
- slab;
- door;
- windows;
- polygon normalization;
- wall corner cleanup.

## Scene B — Multi-room apartment

Tests:

- shared interior walls;
- room adjacency;
- multiple hosted openings;
- duplicate prevention.

## Scene C — Gable building

Tests:

- two roof planes;
- ridge agreement;
- roof-wall trims;
- gable/end walls;
- openings near roof condition.

## Scene D — L-shaped building

Tests:

- concave footprint;
- roof valley;
- slab polygon;
- junction topology.

## Scene E — Terrain + road + retaining wall

Tests:

- one Mesh;
- road slab;
- explicit grade relationship;
- site/building collision classification.

## Scene F — Freeform Morph pavilion

Tests:

- Morph manifold checks;
- self-intersection rejection;
- orientation correction.

## Scene G — Façade system

Tests:

- bay grid;
- repeated window families;
- corner exceptions;
- vertical alignment.

---

# 15. Golden-model regression strategy

For each integration scene, store a sanitized JSON golden contract rather than a `.pln` file.

Golden contract contains:

- normalized semantic elements;
- canonical geometry fingerprints;
- intended connections;
- allowed collision classes;
- expected issue count;
- expected model-ready status.

A local Archicad validation run can compare actual read-back against the golden contract without uploading project files to GitHub.

---

# 16. Metrics dashboard

A build report should include measurable indicators.

Example:

```json
{
  "elements_owned": 428,
  "verified_pass": 428,
  "unresolved_writes": 0,
  "duplicate_elements": 0,
  "undeclared_collisions": 0,
  "boundary_gaps": 0,
  "non_manifold_morphs": 0,
  "roof_interface_errors": 0,
  "opening_host_errors": 0,
  "facade_alignment_errors": 0,
  "warnings": 3,
  "status": "MODEL_READY_WITH_WARNINGS"
}
```

This is substantially more useful than “script completed successfully”.

---

# 17. Recommended first automated gates to implement

Order by expected impact:

1. polygon normalization and equality;
2. canonical shared vertex/edge graph;
3. duplicate geometry fingerprints;
4. room/perimeter closure;
5. opening host containment;
6. wall reference-line junction validation;
7. AABB collision broad phase + typed matrix;
8. roof shared-edge/ridge-height checks;
9. Morph manifold validator;
10. Tapir trim/SEO relationship verification;
11. façade alignment rules;
12. final model metrics/report.

---

# 18. Definition of Done for the v2 generator

The v2 architectural generator is ready for serious use only when:

- the same design can be regenerated without accumulating duplicates;
- shared room walls are produced from shared topology;
- wall corners are based on reference-line connectivity;
- roofs connect to walls through verified relationships or exact geometry contracts;
- opening positions are host-local and stable;
- solid Morphs pass manifold checks before write;
- terrain is represented as coherent site geometry rather than accidental stacked surfaces;
- collisions and gaps are separate quality classes;
- visual/family alignment is checked;
- every write has a durable verified receipt;
- the final report can explain why the model is `MODEL_READY`.
