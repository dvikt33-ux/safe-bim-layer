# PLANNING ENGINE v0

The offline `PlanningEngine` creates metre rectangles with actual XY coordinates,
then independently audits them. It extends the existing verified intake chain;
existing producer modules, normative base and BIM runtime are unchanged.

## Working entry points

```python
engine = PlanningEngine(verified_compilation, referenced_functional_program, policy)
result = engine.audit()
gate = engine.require_verified()       # live inputs + generation + independent audit rerun
candidate = engine.selected_candidate() # defensive copy, gated
engine.audit_candidate(candidate)      # ignores claimed checks/status/score
```

`python examples/planning_house_v0.py --output <directory>` reproduces the synthetic
two-floor house from `docs/examples/planning_engine_v0/house-inputs.json`. It verifies
all seven existing producers before invoking the planner, disables further global
library reads, writes coordinates and the text representation, and compares repeated
results. The synthetic library is a **producer test fixture**, not an additional
planner input or a real SP/GOST rule library.

## Inputs and progression

The only constraint/site input is the live VERIFIED compilation `planning_input()`.
Its entire content must equal the compilation's fingerprint-protected planningInput.
The referenced live Functional Program must match its reference and content hash.
No raw rules, copied VERIFIED JSON or additional project constraints are accepted by
the planner. The planner never reads the library; producer construction in the demo
is separate from planning.

Flow: REQUIRE VERIFIED CONSTRAINT COMPILATION → READ FUNCTIONAL SPACES → READ
MANDATORY CONSTRAINTS → READ PREFERENCES → READ SITE FACTS → DETERMINE FLOOR SET →
ASSIGN SPACES TO FLOORS → BUILD RELATIONSHIP GRAPH → GENERATE INITIAL RECTANGULAR
LAYOUT → RESOLVE OVERLAPS → CREATE CIRCULATION → CHECK HARD CONSTRAINTS SUPPORTED
BY V0 → SCORE PREFERENCES → AUDIT CANDIDATE → RETURN BEST VALID CANDIDATE → VERIFIED.

`VERIFIED` means abstract rectangular planning only. Geometry, required instances,
compiled supported hard constraints, relationships, site placement, reference
integrity and decision provenance must pass. The selected candidate is re-audited.
Constraint/provenance coverage must equal 1 for planning scope. Deferred constraints
are reported with their entire original record and named downstream scope. This is
not building compliance or physical stair verification.

Compilation/reference changes invalidate the session. `update_policy()` validates
the new declarative policy and invalidates a prior result. Progression rejects stale,
copied or internally tampered results by rerunning generation and validation and
comparing the exact result. No mutation of upstream sessions occurs.

## Geometry and search

All floors use local XY (0,0), x right, y up, metre units. Required program quantities
expand to stable `id#1` instances; singleton IDs stay unchanged. Circulation belongs
to a separate list, never the program's room count. The floor set comes from verified
FP Stage0 context; hard floor constraints and explicit `FLOOR:floor-n` locations are
audited. Aliases `ground`/`upper` are explicit configurable preference heuristics.

Area target: explicit mandatory exact/lower bounds or nonbinding requested targets,
clipped to hard bounds. Otherwise `defaultRoomArea` is a disclosed search heuristic.
Strict inequalities use twice `numericTolerance` as the arithmetic margin. No
physical/normative minimum is invented. Width = sqrt(area × configured ratio), depth
= area / width. Aspect ratios, room-area fallback and circulation width are all
PLANNER_HEURISTIC, never normative derivations.

Area-descending, relationship-first and compact-strip candidates use deterministic
row packing. Hard locations precede relationship degree/area/stable IDs. Bounded
swaps improve mandatory relationships; rooms in successive rows are separated by
circulation. Multiple row corridors connect through a separate collision-free spine.
Geometry duplicates are removed. The search enumerates column counts/aspect ratios
in stable order. `maxCandidates`, `maxGenerationAttempts`, `maxImprovementPasses`,
`maxPlacementAttempts`, `maxSpaces` and `maxFloors` bound work. The same placement
attempt budget bounds swaps per improvement pass and site trials per candidate.

`NO_VALID_PLAN_FOUND` means this bounded baseline found no valid plan, not a proof
that the architectural problem is unsatisfiable. Unsupported mandatory planning
semantics block before generation. Candidate statuses are VALID, INVALID_CONSTRAINT,
INVALID_GEOMETRY or UNSUPPORTED; an exhausted search returns NO_VALID_PLAN_FOUND.

## Supported checks and representation limits

The versioned `CAPABILITY_REGISTRY` explicitly lists SUPPORTED, NOT_PLANNING_DOMAIN
and UNSUPPORTED classifications. Numeric area (m2), envelope width/depth (m), floor
count and quantity (count) support eq/neq/gt/gte/lt/lte. Scope must identify the actual
subject; local envelope measurements are unsupported. No implicit unit conversion.
Existence, function and floor assignments are checked against actual instances.
Unknown planning hard constraints, detailed stair dimensions, setbacks, fire
calculations or arbitrary expressions cannot be silently discarded.

Adjacency is shared edge length > `adjacencyEpsilon`; corners do not qualify.
Required adjacency, mandatory avoidance and separation are hard checks. Separation
means no shared edge in this v0 representation, not a fire distance. Relations over
quantities conservatively check every endpoint-instance pair. Required access checks
actual room-to-circulation boundary links and connected circulation paths, without
traversing program rooms. Vertical relationships need different floors and the
abstract connector. Every multifloor candidate carries an abstract stair connector
with `dimensionalCompliance = NOT_EVALUATED`.

External access checks the relationship's **from** room against the exterior of the
global building envelope; `externalAccess` and `buildingEdge` must agree with geometry.
The current upstream compiler cannot compile the FP EXTERIOR endpoint: it flags
SPACE:EXTERIOR as dangling. No upstream workaround/mutation or phantom room is made.
The demo uses the existing normative adapter's explicit synthetic categorical rule
`RELATIONSHIP:EXTERNAL_ACCESS:living:EXTERIOR`, scope SPACE:living, with a verified
source-text receipt. This limitation remains fail-closed for an incompatible FP input.

Material, structural system, equipment, parking, occupancy, acoustics and phasing
metadata have explicit downstream deferrals. The registry also explicitly enumerates
nonplanning downstream scope codes (BIM_TRANSLATOR, ARCHICAD_EXECUTION,
STRUCTURAL_DESIGN, MEP_DESIGN, COST_ESTIMATION, MATERIAL_ASSIGNMENT); unknown scope
names do not excuse unknown hard constraints. Unknown subjects are UNSUPPORTED.
Mandatory Design Intent commitments without a geometric hard evaluator also block.

## Site placement

Site facts, including orientation, are retained exactly. Existing objects alone do
not imply preservation. Site placement is explicitly NOT_REQUIRED with null placement
unless compiled constraints request it. Explicit preserved OBJECT and prohibited ZONE
constraints trigger placement. CUSTOM `SITE_PLACEMENT REQUIRE REQUIRED` is supported.
Only confirmed axis-aligned rectangular boundaries and rectangle/point obstacles,
in metres in the same confirmed coordinate system, are supported. Other mandatory
geometry is UNSUPPORTED and blocks. The building's axis-aligned envelope must fit
inside the boundary and not intersect the closed obstacle sets.

Trial positions use boundary and obstacle events. Contact avoidance uses the disclosed
algorithm epsilon, not a clearance norm. No setback is created (`setbacks=[]`).
An explicit unsupported clearance constraint blocks. Rotation zero is an explicit
axis-aligned heuristic; orientation facts are retained, not falsely satisfied.

## Scoring and provenance

Hard checks are independent PASS/FAIL, never score terms. Versioned policy weights
multiply explicit preference terms and the source goal weight where present:
COMPACTNESS = negative bounding-box area; SPACIOUSNESS = sum(area / requested target);
STRUCTURAL_REGULARITY = count of aligned corresponding rectangle edges; REQUESTED_AREA
= negative absolute target error; preferred/avoided adjacency = +1 when satisfied,
-1 otherwise; preferred floor = number of matched instances. Best valid candidate
has highest score, then stable candidateId. Invalid candidates cannot win.

MASONRY_MODULARITY and LOW_COST are recognized UNSUPPORTED_PREFERENCE in v0, with no
invented module/cost model. Other unimplemented preferences are retained similarly.
Weights, tolerances and search limits are explicit policy, not norms. Policy, source
compilation, actual geometry, audit and score participate in candidate fingerprints;
the full result has a separate planningEngineFingerprint. No random/time/network/
model/eval/shell calls occur in the algorithm.

Floor-set, floor assignments, size, room/circulation placement, envelope, site placement
and abstract connector decisions all carry compiled IDs or a named PLANNER_HEURISTIC
policy plus policy fingerprint. Floor-count context references the exact verified FP.
Audit verifies decision values against geometry and retains deferred constraints.

## Validation

`python -m unittest tests.test_planning_engine -v` covers all 70 requested scenarios
and additional tamper, strict-bound, site-point, unsupported-scope, unit and goal
checks. Full previous suites run separately, including the Stage2/Stage3/Audit Pack
regression checkout. The offline demo must produce real coordinates before PASS.
No Archicad operations, BIM translator, UI, normative-library changes or runtime
integration are included.
