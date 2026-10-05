# CONSTRAINT COMPILATION v0

Independent module on `work/project-normative-bundle-v0`,
`6901fe69d834f8d571c53d3bbda57f46d2106943`.
Six live VERIFIED upstream sessions and coherent fingerprint chains are required:
Stage 0, Functional Program, Design Intent, Site Context, Project Constraint Input,
Project Normative Bundle. No existing layer is rewritten or mutated.

## Working API and flow

`ConstraintCompilation(stage0, fp, intent, site, project_constraints, bundle,
domain_registry, reference_registry)` accepts no external constraint injection.
`audit()` imports verified inputs, normalizes domains/subjects/scopes/operators,
preserves units, records source precedence, merges compatible declarations,
detects contradictions, builds dependency/traceability graphs and planning input,
then re-audits to CONSTRAINT_COMPILATION VERIFIED. `require_verified()` is the
progression gate. `planning_input()` returns a defensive copy only after that gate.

`result()` returns a copy. Output mutation cannot authorize progression.
Project Constraint artifact content is checked against its exact artifact hash;
Normative Bundle content must equal its pinned VERIFIED snapshot. Normative
requirements come only from compiledRules, never the global library. The compiler
does not re-evaluate normative applicability or run a library refresh.

## Versioned registries and normalization

Domain registry has id/revision/VERIFIED status, extensible domains with explicit
SINGLE_VALUE or MEMBERSHIP comparison semantics, projectTypes/functionalFields
adapters, normativeDomainAliases, subjectAliases and subjectReferences. The example
registry is synthetic and includes all 17 requested domains and 25 project types.
Alias/adaptation decisions are explicit versioned inputs; the compiler cannot
infer synonyms by label similarity or building class. Unknown adapters fail closed.
Subject templates support only literal text, {subject} and {scopeId} substitution.
No arbitrary expression/function/script evaluation. Ordered confirmed PHASING
labels remain an ordered declarative literal rather than executable instructions.

Reference registry declares bounded directional scope overlaps. PROJECT can cover
BUILDING and declared narrower scopes; BUILDING can cover FLOOR/SPACE. Named peer
SPACE scopes stay separate. Entity references come from the verified FP, physical
Site Context and PCI scopeEntities; floors are never generated from floor_count.
Registered subject-reference prefixes and explicit entity values, including set
values, are checked. Dangling mandatory scope/subject/value references block.
Optional unresolved references remain disclosed and do not become hard constraints.

Project operators map to eq/neq/gt/gte/lt/lte/in/not_in/require/prohibit/preserve.
Existing-object removal normalizes to prohibition of the preserved object state.
Numeric/categorical literals are bounded and finite; executable operators and
extra executable registry fields cannot enter the compiler.
Units remain exactly as supplied. No conversion registry is implemented in v0.
Mixed mandatory units produce UNIT_RECONCILIATION_REQUIRED and block, including
1 m versus 1000 mm. Optional preferences with unreconciled units are disclosed
without numeric comparison. Normalization registry IDs/revisions/fingerprints and
PRESERVE_NO_CONVERSION policy remain attached to each compiled constraint.

## Strength and origin

Binding PCI inputs and VERIFIED normative requirements become MANDATORY.
Nonbinding PCI inputs remain PREFERENCE. FP USER_REQUIREMENT records remain
MANDATORY, USER_PREFERENCE records remain PREFERENCE. Explicit required spaces
produce existence requirements; requestedArea scalar/ranges preserve their stated
units, quantity stays a count, special equipment stays a membership requirement.
Other confirmed qualitative FP attributes and relationships stay declarative,
not invented geometry. Unsupported functional shapes block instead of disappearing.
Class/context inputs remain gated factual dependencies, without reinterpreting
classification as a new numeric design requirement.

Design Intent goals remain qualitative planning preferences with priority/weight
metadata and no invented area/width target. An explicitly MANDATORY commitment
retains that strength as a qualitative declaration; preferred/sacrificable goals
are not promoted. Existing FP preferredFloor semantics are preserved.
Site facts remain INFORMATIONAL planning facts, including existing objects/access,
boundary/north, context, explicit terrain status and traceable site metrics.
An existing tree is not a preservation requirement. Existing geometry is copied
as source evidence, never generated. Missing terrain remains explicitly missing.

No universal user-over-norm or norm-over-user priority exists. Incompatible
MANDATORY declarations block regardless of origin. An incompatible optional
preference creates an evidenced override with OVERRIDES_PREFERENCE graph edges,
and never blocks solely by being a preference.

## Raw, effective and conflicts

mandatoryConstraints preserve every raw declaration and source. effectiveConstraints
contain separate domain/subject/scope groups, exact selected lower/upper records,
allowed/required values, exclusions and sourceConstraints IDs. Choosing the strongest
bound never deletes a weaker raw record. Valid lower/upper declarations form an
interval. Bounds, equality, require/prohibit, sets, strict endpoints and discrete
count intervals are compared only as declarations, never against actual geometry.
SINGLE_VALUE domains treat required alternatives as a single property; MEMBERSHIP
domains permit multiple required equipment items while retaining prohibitions.
Conflict records keep both origins, provenance, scopes and exact bounds.

## Graph and traceability

Graph nodes include upstream inputs, project constraints, normative rules,
functional requirements, compiled constraints, planning preferences and site facts.
DERIVED_FROM edges point compiled → source → upstream; SUPPORTS records the reverse
source → compiled link. APPLIES_TO links resolved scopes. Exact normative rule
dependencies and project facts used in applicability have DEPENDS_ON links.
Site object references link physical facts; NARROWS, CONFLICTS_WITH and
OVERRIDES_PREFERENCE disclose comparison results. Derivation/dependency cycles
and dangling graph edges are rejected. Reverse SUPPORTS edges do not form a
derivation chain and are not interpreted as circular provenance.

traceabilityIndex provides byCompiledConstraintId, byOrigin (exact revision) and
byOriginalId. `lookup_origin(origin_type, original_id)` returns affected compiled
IDs. Normative source refs retain ruleId/revision/branch, original requirement,
exact document revision/hash/location, full source evidence, applicabilityBasis
and projectInputsUsed. Project and FP refs retain artifact/source revisions and
evidence. No raw origin is lost by merge.

## Planning gate, fingerprint and invalidation

VERIFIED requires six coherent upstream gates, resolved mandatory references,
trusted origins, compatible mandatory units, zero conflicts, complete provenance,
valid graph, no invented constraints or preference promotions, no compliance claim
and deterministic output. Blocked/invalidated planningInput is WITHHELD;
planning_input() raises instead of exporting unsafe mandatory constraints.
A verified planningInput contains raw mandatory constraints, effective summaries,
preferences, site facts, FP/DI references and sourceCompilationFingerprint.

Canonical compilation fingerprint excludes its own field and the nested planning
sourceCompilationFingerprint to avoid a self-reference, then both are assigned
the same hash. No timestamp/random identifier participates. Registry changes via
update_registries() and every upstream fingerprint/status change invalidate the
gate; a full audit is required before another planning packet can be exported.

## Acceptance boundary

Tests use TEST_RULE_A and synthetic requirements, not real Russian normative
values. Acceptance runs the full offline API path from verified upstream producers
to exported planningInput. The task-local CLI acceptance runner builds a verified
synthetic Normative Bundle first; the compiler itself never accesses its library.
Existing Stage 0/FP/DI/Site/PCI/Normative Bundle/QA/Stage 2/Stage 3/Audit Pack tests
are unchanged. Runtime, Archicad, Closed Loop, UI, geometry/adjacency solving,
layout generation, compliance calculations, normative-library mutation and main
changes are outside this implementation. Planning Engine is the next separate stage.
