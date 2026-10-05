# DESIGN INTENT / PROJECT GOALS v0

An independent, offline description of **how the user wants the project to turn
out**. It consumes VERIFIED Stage 0, VERIFIED Functional Program and explicit
user intent. It neither edits Functional Program nor solves numerical norms,
constraints, geometry, layouts, construction or BIM execution.

## Working end-to-end scenario

The checked-in examples are synthetic user-approved acceptance fixtures.

```powershell
python -m design_intent --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --functional-brief docs/examples/functional_program_v0/brief.json --intent docs/examples/design_intent_v0/ranked-intent.json --output work/design-intent.json
# Exit 0: LOW_COST priority 1, SPACIOUSNESS priority 3, traceable PRIORITY_ORDER.

python -m design_intent --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --functional-brief docs/examples/functional_program_v0/brief.json --intent docs/examples/design_intent_v0/equal-intent.json --output work/design-intent-missing.json
# Exit 2: equal-priority COMPACTNESS/SPACIOUSNESS, one precise decision question.

python -m design_intent --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --functional-brief docs/examples/functional_program_v0/brief.json --intent docs/examples/design_intent_v0/equal-intent.json --answers docs/examples/design_intent_v0/answers.json --output work/design-intent-answered.json
# Exit 0: approved answer -> full re-audit -> DESIGN_INTENT VERIFIED.
python -m unittest tests.test_design_intent -v
```

The answers fixture is bound to those exact goals. A change to a goal or source
revision requires a newly approved answer with current goal fingerprints.

## Flow and gate

REQUIRE VERIFIED STAGE 0 -> REQUIRE VERIFIED FUNCTIONAL PROGRAM -> COLLECT DESIGN
INTENT -> NORMALIZE GOALS -> CLASSIFY GOALS -> ASSIGN PRIORITIES -> BUILD TRADEOFF
MATRIX -> DETECT CONFLICTS -> IDENTIFY MISSING DECISIONS -> RE-AUDIT -> DESIGN_INTENT
VERIFIED.

`DesignIntent(stage0, functional_program, sources)` accepts live audited sessions,
not dictionaries with an arbitrary VERIFIED string. The dependency fingerprints
must describe the same Stage 0. The CLI rebuilds and audits both dependencies
from their explicit sources before extracting goals. No new upstream behavior is
implemented here.

`audit()` reconstructs the goal set, priorities, tradeoffs, resolutions and gate
from current evidence. `require_verified()` returns permission proof only if both
upstream gates and this gate remain valid; it launches no downstream stage.
`result()` also detects upstream invalidation. `update_source()` immediately
revokes the prior gate, including changes in goal source, priority or resolution.
Source/goal fingerprints and stable IDs prevent stale decisions from silently
applying to changed goals. Returned copies cannot mutate or forge a gate.

## Source and goal records

Sources have stable id, kind, revision, approved:true, inspected:true, statements.
Kinds are USER_BRIEF, USER_CORRECTION, APPROVED_PROJECT_DECISION. Approval and
inspection are the caller's evidence boundary; this module does not approve LLM
inferences or assert inspection of unlisted sources.

GOAL statements supply stable id and goalId, explicit type, source and scope;
priority is an explicit positive integer. Missing priority creates a decision
gap. Optional weight must be finite and positive and is never defaulted to 1.
Boolean, string and fractional priorities, invalid weights and nonfinite JSON
are blocked. Explicit user target/tolerance accept only a finite nonnegative
value plus unit. Their values remain user optimization intent, not normative
constraints. Absent target/tolerance/weight remain null.

Goal types: COMPACTNESS, SPACIOUSNESS, MINIMIZE_CIRCULATION, PRIVACY, OPEN_PLAN,
SITE_CONNECTION, DAYLIGHT_PREFERENCE, VIEW_PRIORITY, LOW_COST, LOW_OPERATING_COST,
CONSTRUCTION_SIMPLICITY, STRUCTURAL_REGULARITY, MASONRY_MODULARITY, FLEXIBILITY,
FUTURE_EXPANSION, ACCESSIBILITY_PREFERENCE, ACOUSTIC_COMFORT,
ENERGY_EFFICIENCY_PREFERENCE, AESTHETIC_DIRECTION, CUSTOM. CUSTOM requires the
user's actual description; unknown types do not become guesses.

Scopes are PROJECT, SITE, space:<stable spaceId>, zone:<explicit functional zone>.
Space/zone references are checked against the verified Functional Program.
Priority order is represented as ordered tiers with goalIds, so equal numeric
priorities do not acquire an invented ordering from ID sort order.

Sources are separated: USER_REQUIREMENT, USER_PREFERENCE,
APPROVED_PROJECT_DECISION, DERIVED_DESIGN_INTENT, NORMATIVE_PENDING.
USER_REQUIREMENT means MANDATORY; USER_PREFERENCE means PREFERRED.
SACRIFICABLE must be explicitly declared on an eligible nonmandatory goal.
APPROVED_PROJECT_DECISION requires matching approved source evidence and may
declare commitment. A preference cannot become mandatory, and a requirement
cannot silently become sacrificable. Every goal retains its original evidence.

NO_DESIGN_GOALS is an explicit user decision with a reason. Without explicit
goals or that decision, one intent-scope question is returned. Project type never
creates design tastes. INACTIVE goals are retained but do not participate in
optimization tradeoffs. A NO_DESIGN_GOALS decision conflicts with active goals.

NORMATIVE_PENDING is supported only as a separate nonnumerical topic marker.
It never enters active goals or the priority order. Numerical normative payloads,
geometry/layout fields and unapproved assumption fields are rejected. There is
no automatic import of normative requirements into Design Intent.

## Safe derivation

DESIGN_STATEMENT supports one bounded, versioned exact statement rule:
«Хочу максимально простой и дешёвый дом без сложных конструкций».
It yields LOW_COST, CONSTRUCTION_SIMPLICITY and STRUCTURAL_REGULARITY, each with
DERIVED_DESIGN_INTENT, derivation rule, exact input statement, source evidence and
confidence EXACT_RULE_MATCH. Confidence describes an exact lexical rule match,
not a statistical estimate. The rule's PROJECT scope follows the explicit whole
house statement. An explicit priority may apply to that statement or a supplied
per-goal priorities map; absent priorities remain unresolved.

Unrecognized statements create a normalization decision gap. There is no
subjective interpretation, project-type taste inference or broad prose parser.

## Tradeoffs and decisions

The fixed versioned heuristic matrix contains potential optimization tensions:
SPACIOUSNESS/LOW_COST, OPEN_PLAN/ACOUSTIC_COMFORT, DAYLIGHT_PREFERENCE/LOW_COST,
FUTURE_EXPANSION/COMPACTNESS, PRIVACY/OPEN_PLAN, COMPACTNESS/SPACIOUSNESS.
Only present active goals with overlapping scopes are evaluated. No unrelated
goals are added and disjoint functional scopes do not produce tradeoffs.

The matrix makes no geometric infeasibility claim. Resolved means **the user's
optimization policy is known**, not that a layout exists or both targets are
feasible. All goals remain active and all mandatory requirements are retained.

Different explicit priorities derive RESOLUTION_POLICY=PRIORITY_ORDER with the
actual goal priorities and provenance. Equal priorities stay unresolved even
when weights differ: no weight-based resolution is assumed. One minimal
MISSING_DESIGN_DECISION question asks which goal matters more and carries the
exact goal IDs and fingerprints. Other gaps are retained in the full ledger;
questions show one blocker at the earliest dependency layer, followed by re-audit.

TRADEOFF_DECISION requires two goal IDs, their exact current fingerprints, and
PREFER_GOAL or KEEP_BOTH. PREFER_GOAL names one of those goals. KEEP_BOTH explicitly
retains both without choosing a winner. Contradicting an existing priority order
requires explicit overridePriorityOrder:true; otherwise it is a conflict.
Neither policy authorizes relaxing mandatory goals. relaxationAuthorized is true
only when the lower-preference goal was explicitly marked SACRIFICABLE.

Conflicting definitions under one goalId or conflicting decisions block VERIFIED.
Explicit USER_CORRECTION/APPROVED_PROJECT_DECISION can supersede source:statement
references; revisions/dates never silently choose a winner. Decisions retain
their source provenance. Stale fingerprint bindings require re-approval.

## VERIFIED and future planning boundary

VERIFIED requires both current upstream VERIFIED gates, valid blocking goals,
zero conflicts/unresolved blocking tradeoffs/missing blocking decisions, complete
goal and resolution provenance, no invented normative values or unapproved
assumptions in the output, and deterministic canonical data. Stable IDs, content
fingerprints and sorted records yield identical repeated output; no clock or
random ID is used.

Functional Program, Design Intent and a future Normative Constraints artifact
remain independent inputs to a future Planning Engine. Design Intent refers to
Functional Program by fingerprint and space IDs; it never edits spaces, areas,
user requirements or normative markers. This change implements no planning,
constraint compilation, geometry, UI, Archicad or Closed Loop operation.

## Acceptance boundary

20 required scenarios and additional boundary tests cover CLI answer/re-audit,
all goal types, scope selection, stale resolutions, source corrections, upstream
immutability, approved decisions, sacrificable goals, user numeric targets,
forged gates and explicit no-goals decisions. Existing Stage 0, Functional Program
and QA regressions run unchanged. Existing Stage 2/3/Audit Pack suites run from
03c64733bb2b4f59970f5247a3ed89e1236f3090 with only the new offline modules/tests
overlaid, using synthetic adapters and existing evidence. No live BIM proof is
claimed or required by this offline layer.
