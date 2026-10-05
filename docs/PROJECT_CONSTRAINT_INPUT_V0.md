# PROJECT CONSTRAINT INPUT MODEL v0

Independent offline compiler on top of `work/site-context-model-v0`,
`8cbbab827ee8a1bdde5e7d44ac3d1b06f5b4cc8b`.
Existing Stage 0, Functional Program, Design Intent and Site Context are read-only.
No runtime wiring, Archicad operations, normative bundle, UI or planning engine.

## Working flow

REQUIRE VERIFIED UPSTREAM → COLLECT CONSTRAINT SOURCES → NORMALIZE CONSTRAINTS
→ CLASSIFY HARD / SOFT BOUNDARY → RESOLVE SCOPE → NORMALIZE UNITS
→ DETECT INTERNAL CONFLICTS → DETECT CROSS-ARTIFACT CONFLICTS
→ IDENTIFY MISSING DECISIONS → RE-AUDIT → PROJECT_CONSTRAINT_INPUT VERIFIED.

`ProjectConstraintInput(stage0, functional_program, design_intent, site_context, sources)`
accepts four live audited sessions. Their gates and shared dependency fingerprints
must agree. Call `audit()`, inspect `result()`, and call `require_verified()` before
progression. `planning_constraints()` returns only binding active constraints and
binding derived constraints after checking the gate; it does not solve them.

## Explicit source boundary

Sources require stable `id`, nonempty `revision`, `category`, `approved:true`,
`inspected:true`, `verification:"CONFIRMED"`, `basis:"NON_NORMATIVE"` and a
`statements` array. Supported categories are USER_REQUIREMENT, CLIENT_REQUIREMENT,
APPROVED_PROJECT_DECISION, PROJECT_DOCUMENT and TECHNICAL_CONDITION.
Document status alone never establishes nonnormative applicability.
DERIVED_PROJECT_CONSTRAINT is emitted only by the bounded derivation below.
NORMATIVE_PENDING sources accept `{id, topic}` records only and emit deferred
topics with provenance; they cannot emit active numeric or binding constraints.
Confirmation/approval flags are caller-supplied evidence assertions, not an
independent verification of the physical project or a legal/normative opinion.

No generic questionnaire, free-text inference, defaults, typical project values,
arbitrary expressions or executable formulas are supported. Unrecognized fields,
malformed records, guesses and normative payloads fail closed. Opaque categorical
labels describe confirmed decisions and are never executed.

## Constraint record

```json
{
  "id": "budget",
  "kind": "CONSTRAINT",
  "constraintId": "client-budget",
  "type": "BUDGET_LIMIT",
  "scope": ["PROJECT"],
  "operator": "<=",
  "value": 15000000,
  "unit": "RUB",
  "binding": true
}
```

Output adds status ACTIVE, sourceCategory, claimId and complete raw evidence
provenance (source ID/revision, statement ID/hash, confirmation and approval).
`binding:false` goes into `nonBindingConstraints` with status NON_BINDING.
Binding must be explicit: absence becomes a missing decision, never a hard default.
Low-cost Design Intent never invents a budget limit or conflicts with one.

Supported types (25): BUDGET_LIMIT, AREA_LIMIT, DIMENSION_LIMIT, FLOOR_COUNT_FIXED,
HEIGHT_LIMIT_PROJECT, MATERIAL_REQUIRED, MATERIAL_PROHIBITED,
CONSTRUCTION_SYSTEM_REQUIRED, CONSTRUCTION_SYSTEM_PROHIBITED,
EXISTING_OBJECT_PRESERVE, EXISTING_OBJECT_REMOVE_REQUIRED, SITE_ZONE_PROHIBITED,
SITE_ZONE_REQUIRED, ACCESS_REQUIRED, ORIENTATION_REQUIRED, SPACE_LOCATION_REQUIRED,
SPACE_LOCATION_PROHIBITED, CAPACITY_FIXED, PARKING_COUNT_FIXED, PHASING_REQUIRED,
UTILITY_CONNECTION_FIXED, EQUIPMENT_REQUIRED, EQUIPMENT_PROHIBITED,
DEMOLITION_LIMIT, CUSTOM.

Operators: ==, !=, <, <=, >, >=, IN, NOT_IN, PRESERVE, PROHIBIT, REQUIRE.
Numeric types use numeric comparisons or explicit finite IN/NOT_IN arrays.
FIXED counts use ==. Categorical types use equality/set/require/prohibit operators;
REQUIRED and PROHIBITED types reject opposite operator semantics. PRESERVE uses
PRESERVE. Removing an existing object is incompatible with preserving the same
object. PHASING_REQUIRED accepts an ordered array of unique explicit phase labels.
UTILITY_CONNECTION_FIXED accepts a confirmed connection label with a SYSTEM scope.
Categorical CUSTOM requires a subject and opaque value; numeric CUSTOM requires an
explicit subject, numeric operator and a supported numeric unit.

## Units and measurement subjects

Budget uses RUB, area m2, dimensions/height m or mm, orientation degrees, counts
count, demolition count/m2/percentage. Percentage is 0..100; numeric values must
be finite and nonnegative, counts integers. Categorical unit is explicitly `none`.
No unit conversion is performed. Mixed units within an overlapping declared
domain block until the caller supplies consistent approved records; v0 has no
conversion derivation rule. Original values/units remain in provenance.

AREA_LIMIT, DIMENSION_LIMIT, CAPACITY_FIXED, DEMOLITION_LIMIT and CUSTOM require
an explicit stable `subject`. WIDTH and DEPTH never merge; total/net area and
space quantity/equipment capacity never become synonyms. The bounded FP cross
checks use subject REQUESTED_AREA for requestedArea and SPACE_QUANTITY for quantity.
These are input consistency checks, not normative thresholds or design feasibility.

## References and scope

PROJECT, SITE and BUILDING refer to the verified project, its physical site and
the proposed building as a whole. SPACE:id must exist in FP. OBJECT:id must exist
in Site Context. ZONE:id resolves either an FP functional zone or a confirmed
polygon context feature; SITE_ZONE_REQUIRED/PROHIBITED specifically require the
latter, so a preference label cannot invent a site geometry.
ACCESS_REQUIRED refers to an existing accessId in verified Site Context, including
an explicitly possible access; this does not establish legal/normative approval.

FLOOR:id and SYSTEM:id require explicit approved SCOPE_ENTITY declarations:

```json
{"id":"floor-ground","kind":"SCOPE_ENTITY","entityType":"FLOOR","entityId":"ground"}
```

v0 supports FLOOR and SYSTEM declarations only, never generated floors/systems.
No FLOOR:id is inferred from storey count. SPACE_LOCATION values must reference
declared FLOOR:id or registered ZONE:id. EXISTING_OBJECT values are explicitly
EXISTING_OBJECT and require OBJECT scopes; SITE_ZONE values are SITE_ZONE.
Dangling scopes/target references block even for nonbinding records.

## Conflicts, corrections and missing decisions

Overlapping domains match constraint family, explicit subject and scope. PROJECT
constraints also apply to declared narrower scopes; BUILDING constraints overlap
explicit FLOOR/SPACE targets. Upper/lower/equality/set contradictions are retained
with all candidates, including strict endpoints and discrete counts. Mixed units
block rather than silently compare. Revision/date never establishes precedence.
Distinct subjects are separate domains; v0 does not prove geometric feasibility.

FP requestedArea/quantity and required specialEquipment are checked against the
corresponding binding constraints. Verified Stage 0 floor_count is checked against
FLOOR_COUNT_FIXED. A conflict with a confirmed hard requirement blocks the gate.
Contradicting a preference creates an `overrides` record containing the upstream
evidence. **Existing FP always classifies preferredFloor as USER_PREFERENCE**, even
when supplied inside a USER_REQUIREMENT SPACE record. This module preserves that
existing contract; it does not reinterpret preferredFloor as a mandatory location.
Explicit hard locations can be supplied as project constraint records; conflicting
require/prohibit decisions then block. No upstream artifact is mutated.

Corrections use APPROVED_PROJECT_DECISION source statements with `supersedes`:

```json
[{"claimId":"client:budget","evidenceFingerprint":"exact hash of the old raw statement"}]
```

Old claims must exist, fingerprints must match, and references cannot point at
themselves. Cyclic/chained supersessions are blocked in v0: supply one final
explicit correction. The artifact records supersessions and requires full re-audit.
Changing old evidence makes a correction stale rather than silently replacing it.

An explicitly incomplete constraint produces MISSING_PROJECT_CONSTRAINT_INPUT.
For an absent budget value there is exactly one question with WHAT, WHY,
REQUIRED_BY, FORMAT including RUB, and raw provenance. No questions are emitted
for undeclared constraint categories. An empty set produces no invented constraints.

## Bounded derivation

DIMENSION_ENVELOPE with explicit positive width/depth and m/mm, approved scope and
binding, `derivationRule:"EXPLICIT_DIMENSION_ENVELOPE_V0"` and exact statement
`Дом максимум 12 × 10 m` emits WIDTH <= 12 m and DEPTH <= 10 m.
The exact statement must agree with the numeric fields. Output retains
derivationRule, exactInputStatement, inputEvidence and provenance. No dimensions
are extracted from project type, norms, preferences, geometry or statistical priors.

## Gate and invalidation

VERIFIED requires all four upstream gates, coherent dependency fingerprints,
valid binding records, resolved scopes/references, valid units, no conflicts,
no blocking missing decisions, traceable derivations and complete provenance.
No assumptions or normative constraints are invented. Output is deterministic,
sorted and fingerprinted without time/random identifiers. `result()` is a copy.

`update_source()` invalidates on any change to a source, value, unit, operator,
scope, binding or supersession. Every upstream fingerprint/status is refreshed
on result/gate access. INVALIDATED artifacts cannot progress until a full re-audit
and valid upstream gates. FP/DI/Site are never repaired or changed by this module.

## Offline CLI acceptance

```powershell
python -m project_constraints --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --functional-brief docs/examples/functional_program_v0/brief.json --intent docs/examples/design_intent_v0/ranked-intent.json --site-sources docs/examples/site_context_v0/site-sources.json --site-requirements docs/examples/site_context_v0/requirements.json --constraint-sources docs/examples/project_constraint_input_v0/constraints.json --output work/project-constraints.json
```

Exit 0 requires VERIFIED; otherwise exit 2. `--answers` updates explicit sources
and runs the complete audit again. Conflicting and missing fixtures are included.
`python -m unittest tests.test_project_constraints -v` covers 32 requested scenarios
plus robustness cases, all 25 types, supported operators, provenance, gates,
invalidation and read-only upstream behavior. Existing suites are run separately.
Evidence is offline synthetic acceptance, with no live Archicad or external transport.
