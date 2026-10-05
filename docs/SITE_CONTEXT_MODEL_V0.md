# SITE / CONTEXT MODEL v0

An independent, offline record of **where the object is designed and the confirmed
physical conditions around it**. It consumes VERIFIED Stage 0, confirmed site
sources and an explicit current-downstream input contract. It references Stage 0
by fingerprint and does not consume/mutate Functional Program or Design Intent.

## Working end-to-end example

All checked-in examples are synthetic acceptance evidence, not a survey, legal
boundary or project defaults. From the repository root:

```powershell
python -m site_context --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --site-sources docs/examples/site_context_v0/site-sources.json --requirements docs/examples/site_context_v0/requirements.json --output work/site-context.json
# Exit 0: SITE_CONTEXT VERIFIED. Physical rectangle 30 x 20 m, derived area 600 m2.
# Terrain remains TERRAIN_DATA_MISSING, nonblocking for this input contract.

python -m site_context --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --site-sources docs/examples/site_context_v0/missing-north.json --requirements docs/examples/site_context_v0/requirements.json --output work/site-missing.json
# Exit 2: exactly one confirmed-north question.

python -m site_context --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --site-sources docs/examples/site_context_v0/missing-north.json --requirements docs/examples/site_context_v0/requirements.json --answers docs/examples/site_context_v0/answers.json --output work/site-answered.json
# Exit 0: correction -> full re-audit -> VERIFIED.
python -m unittest tests.test_site_context -v
```

## Flow and input boundary

REQUIRE VERIFIED STAGE 0 -> COLLECT SITE SOURCES -> NORMALIZE SITE GEOMETRY ->
NORMALIZE ORIENTATION -> MAP ACCESS -> MAP EXISTING OBJECTS -> MAP CONTEXT FEATURES
-> DERIVE SAFE SITE METRICS -> DETECT CONFLICTS / GAPS -> RE-AUDIT -> SITE_CONTEXT
VERIFIED.

The API is `SiteContext(stage0, sources, requirements)`. It accepts a live Stage0
session and checks require_verified(); the CLI rebuilds/audits Stage 0 using its
existing module. A copied VERIFIED string cannot open the gate.

Source records contain id, kind, revision, inspected:true, verification:CONFIRMED,
and structured statements with stable IDs. Source kinds are PROJECT_FILE, DRAWING,
COORDINATES, USER_SITE_OBSERVATION, APPROVED_DERIVED_GEOMETRY, USER_CORRECTION.
Approval/confirmation is the caller's evidence boundary: collectors must inspect
the actual file/observation and supply trustworthy facts. This module neither
extracts survey geometry from arbitrary images nor claims unlisted source access.

APPROVED_DERIVED_GEOMETRY additionally requires approved:true, a derivation rule
and confirmed input evidence references with source IDs/revisions. All records
retain raw statements as evidence as well as normalized values.

## Geometry, orientation and physical records

Statement kinds: SITE, COORDINATE_SYSTEM, BOUNDARY, ORIENTATION, ACCESS, OBJECT,
CONTEXT, PREFERENCE, ELEVATION_POINT, CONTOUR, MEASUREMENT, NORMATIVE_PENDING.
Unknown fields, assumed/default physical values, legal/numerical norm fields and
room/wall/layout payloads are rejected, rather than silently ignored.

Geometry uses Point, LineString or Polygon with explicit coordinates,
coordinateSystemId and unit m/mm. A Polygon has one closed ring; v0 rejects holes,
open rings, self-intersections, zero area, repeated vertices and overlapping
adjacent edges. Normalization changes ring start/direction only, never a physical
coordinate or closure. The original ring remains in source provenance. Reversed
or cyclically shifted identical boundaries coalesce without a false conflict.

Coordinate metadata requires id, LOCAL_CARTESIAN or PROJECTED_CARTESIAN, unit,
axisOrder:XY and explicit orientation label. Geometry must match that confirmed
frame/unit exactly. V0 rejects geographic degrees, implicit unit conversion,
coordinate transformation and inferred georeferencing.

ORIENTATION supplies a nonzero northVector and matching CRS/orientation metadata.
Only vector magnitude is normalized. North is never guessed from an image, a
site type or a generic grid label. Missing north stays MISSING_SITE_DATA.

Access types: VEHICLE_ACCESS, PEDESTRIAN_ACCESS, SERVICE_ACCESS, EMERGENCY_ACCESS,
EXISTING_ENTRANCE, POSSIBLE_ACCESS. Access is a confirmed point/entry line. Every
access has normativeApproval:NORMATIVE_CONSTRAINT_PENDING with no numeric value;
POSSIBLE_ACCESS remains a physical possibility, never a legal/regulatory approval.

Existing objects: BUILDING, STRUCTURE, ROAD, PATH, PARKING, TREE, WATER, UTILITY,
FENCE, TERRAIN_FEATURE, OTHER. Each retains stable objectId, physical geometry,
status:EXISTING, source, provenance and verification status.

Context types: NEIGHBOURING_BUILDING, STREET_ROAD, PEDESTRIAN_ROUTE,
SIGNIFICANT_VIEW, UNDESIRABLE_VIEW, NOISE_SOURCE, LANDSCAPE_FEATURE, WATER,
MAJOR_VEGETATION, SITE_ENTRANCE, ADJACENT_FUNCTIONAL_AREA. Each requires confirmed
geometry or an explicit confirmed description. A preference for a view is stored
separately as USER_SITE_PREFERENCE; it cannot create a confirmed view feature.
No unrelated feature is added from the catalog or site class.

## Terrain and deterministic metrics

Elevation points/contours require confirmed XY geometry, explicit finite elevation,
elevationUnit m/mm and verticalDatum. Different vertical units/datums conflict;
no vertical conversion is assumed. Known points and contours are retained.
Min/max/range summarize **observed samples only**, not the whole surveyed surface.
Unknown terrain is TERRAIN_DATA_MISSING with null elevations/range/slope, never a
flat or zero-elevation assumption.

All derived metrics have metricId, DERIVED_SITE_METRIC, derivationRule,
inputEvidence, unit, result, scope and provenance. Core metrics are closed-polygon
area, perimeter, bbox and centroid. The existing Stage 0 polygon validator is
reused; translation to a local origin reduces numerical cancellation. Coordinate
units are preserved (m2/mm2 for area); no legal extent is derived from them.

MEASUREMENT statements explicitly request allowed calculations and reference
confirmed record keys, e.g. ELEVATION_POINT:e1 or OBJECT:frontage-line:

- DISTANCE: two confirmed Point geometries; no bbox/centroid proxy for object gaps.
- LINE_ORIENTATION: a confirmed directed two-point line, degrees counterclockwise
  from positive X; it does not infer compass north.
- FRONTAGE_LENGTH: a line explicitly identified as frontage by the measurement
  source; frontage is not inferred from proximity to a road.
- SLOPE_DIRECTION: the descending direction of one confirmed segment between
  unequal elevation points. Scope is CONFIRMED_SEGMENT_ONLY_NOT_GLOBAL_TERRAIN;
  it asserts no global terrain plane, gradient or hidden surface interpolation.

Requests with missing/conflicting evidence, wrong geometry kinds, incompatible
frames or nonfinite arithmetic block the gate. Geologic/topographic completeness
and a global terrain surface are outside v0.

## Site facts, norms, gaps and conflicts

Categories stay separate: SITE_FACT, USER_SITE_PREFERENCE, DERIVED_SITE_METRIC,
NORMATIVE_CONSTRAINT_PENDING, MISSING_SITE_DATA, CONFLICT. Physical boundary
verification says nothing about ownership or legal boundary; those remain explicit
MISSING_SITE_DATA markers with null values. NORMATIVE_PENDING accepts only a topic
marker; it has no numerical constraint or automatic inclusion rule.

No setbacks, fire distances, insolation/sanitary zones, red lines, protected zones,
legal access, ownership or buildable envelope are computed. Confirmed metrics are
inputs to a future planner, not design/QA PASS evidence for numerical regulations.

The input contract has id, revision, approved:true, downstreamStage, requiredInputs.
Core inputs are siteId, boundary, coordinateSystem. Optional current dependencies
are orientation, access, access:<type>, terrain, context:<type>. They are selected
explicitly, not loaded as a universal survey questionnaire. Unknown optional
terrain/north stays in the gap ledger but creates no question or blocker unless
declared required. Required access types require the actual requested type;
POSSIBLE_ACCESS cannot satisfy VEHICLE_ACCESS.

Questions cover only the earliest current blocking layer with WHAT, WHY,
REQUIRED_BY, FORMAT and requirement/source provenance. Conflicts keep actual
candidate evidence and create one targeted correction question. Only explicit
USER_CORRECTION supersedes named source:statement records. Source date/revision
alone never chooses a blocking value. Invalid/unconfirmed sources block verification
and suppress premature data questions.

## Gate, invalidation and future boundary

VERIFIED requires current Stage 0 VERIFIED, resolved site identity/core geometry,
required access/context inputs, no conflicts/blocking gaps/validation errors,
traceable metrics, complete provenance, no invented legal/normative constraints,
no unapproved assumptions and deterministic output. Exact input yields identical
canonical JSON and siteContextFingerprint.

update_source() revokes the old gate for boundary, orientation, access, terrain,
objects/context or source revision changes. update_requirements() also invalidates
the gate. result()/require_verified() detect a Stage 0 change even after Stage 0
is verified again. Answers or updates require a full audit(); copied result data
cannot forge the internal permission gate.

Functional Program + Design Intent + Site Context + future Normative Constraints
remain separate artifacts for a future Planning Engine. This layer implements no
planner, layout, BIM operation, Closed Loop, UI or normative compilation.

24 mandatory scenarios plus boundary/CLI tests cover all physical catalogs,
selected dependencies, metrics, coordinate/vertical units, equivalent rings,
approved derivation evidence and unchanged upstream artifacts. All existing Stage
0/Functional Program/Design Intent/QA tests run unchanged; existing Stage 2/3/Audit
Pack tests run at 03c64733bb2b4f59970f5247a3ed89e1236f3090 with new offline
modules/tests overlaid. Tests make no live Archicad calls.
