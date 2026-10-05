# PROJECT NORMATIVE BUNDLE v0

Independent offline selection and snapshot module on base
`work/project-constraint-input-v0`, `c75665feb8029116245dd1ec76733e599ebdc24a`.
The five existing verified inputs remain read-only. This module is not a normative
calculation, compliance decision, constraint compilation or planning engine.
No runtime wiring, Archicad, UI, background monitoring or Internet search.

## Working flow

REQUIRE VERIFIED UPSTREAM → READ PROJECT CLASSIFICATION → DISCOVER NORMATIVE BRANCHES
→ FILTER BY APPLICABILITY → RESOLVE CONDITIONAL APPLICABILITY
→ SELECT VERIFIED RULE REVISIONS → VERIFY SOURCE TRACEABILITY
→ VERIFY SUPERSESSION STATE → DETECT NORMATIVE GAPS → DETECT RULE CONFLICTS
→ FREEZE PROJECT SNAPSHOT → BUILD IMPACT INDEX → RE-AUDIT
→ PROJECT_NORMATIVE_BUNDLE VERIFIED.

`GlobalRuleLibrary(data)` represents a copied global library revision.
`ProjectNormativeBundle(stage0, functional_program, design_intent, site_context,
constraint_input, library, scope)` binds a project to that library revision.
Call `audit()` and `require_verified()` before downstream progression.
`result()` returns a copy of live gate state; `snapshot()` returns the last
immutable verified historical artifact and cannot grant a live progression gate.
An initial blocked audit has no verified snapshot.

## Library registries and explicit coverage

Library data has libraryId/revision and separate branches, rules, sources,
applicabilityRegistry and domainRegistry. All fixtures under this document's
example directory are synthetic mechanics tests, not verified Russian standards.
They do not modify or assert completeness of any existing normative library.

Branch records declare branchId, projectClasses, domain, status, applicabilityId
and requiredRuleIds. Rules are keyed by branchId, so routing reads only matching
rule inventories. Unrelated class rules are never parsed or evaluated.
Unrelated branch metadata is retained in excludedBranches with a routing reason.
Unknown routing/status metadata fails closed. Missing unrelated rules create no gap.

Scope explicitly declares downstreamStage, requiredNormativeDomains and
optionalNormativeDomains. A separate VERIFIED versioned domainRegistry maps
downstreamStage/projectClasses to the required and permitted optional domains.
The caller cannot silently omit required registry domains. The library need only
cover the applicable domains of this scope, not all building classes or future work.
A required domain without a routed project branch is a NORMATIVE_GAP.
A proven NOT_APPLICABLE branch is an exclusion, not a gap.
Omitting optionalNormativeDomains means no optional domains were requested; it
does not change required coverage or assume any project fact.

Only lifecycle VERIFIED can compile. Supported earlier states are COLLECTED,
SOURCE_VERIFIED, RULE_PARSED, RULE_AUDITED; SUPERSEDED and RETIRED remain historical.
Unknown states and malformed rule/revision metadata cannot become production rules.
An applicable unfinished rule in a required domain produces a blocking gap.
Branch requiredRuleIds preserve explicit expected coverage even when a rule is
missing or only historical. There is no claim that this synthetic coverage profile
is sufficient for an actual Russian architectural project.

## Applicability DSL and project facts

Verified versioned applicabilityRegistry contains definitions and inputBindings.
The bounded DSL supports eq, neq, gt, gte, lt, lte, in, exists, all, any, not.
All syntax is validated, including short-circuited children. No Python/eval,
executable expressions, implicit boolean/numeric coercion or inferred values.
Ordered predicates require finite numeric facts.

```json
{"all":[{"input":"project.classification","eq":"IZHS"},
        {"input":"building.floorCount","gte":2}]}
```

Bindings explicitly specify artifact and acceptedFormat. STAGE0 uses datumId and
accepts only CONFIRMED/DERIVED values from its live VERIFIED result. Other inputs
use safe declarative field paths into verified project facts. Named list records
resolve through explicit spaceId/goalId/objectId/featureId/accessId/constraintId.
Normative-pending and audit-metadata paths cannot be consumed as project facts.
FP/Design Intent are consulted for facts only when a predicate references them;
their gate/fingerprint coherence is always required as requested upstream inputs.

Unknown/null is a third state, never a guessed false or an assumed flat terrain.
Even exists:false on an unknown fact remains unresolved. Known false in all, or
known true in any, can close the expression without an irrelevant missing-input
question. The proof retains project inputs actually used and artifact fingerprints.
Rule applicability results are retained, including NOT_APPLICABLE decisions.

Unresolved applicability yields CONDITIONAL and an evidenced NORMATIVE_GAP.
Required branches/rules block VERIFIED; explicitly optional unknown branches do
not block the scope. missingProjectInputs contain WHAT, WHY, REQUIRED_BY,
ACCEPTED_FORMAT and affected rule/branch, with provenance. They request verified
project facts only. No user question requests a normative value.

## Rule and source traceability

Rule identity is exact branchId/ruleId/revision. Each record includes status,
requirement, source, applicability, supersedes, dependencies, revisionMetadata,
and an audit receipt. The receipt must be VERIFIED, identify auditId and match
the canonical hash of the entire rule excluding the receipt itself.
Editing a parsed requirement, applicability, source or revision decision makes
that receipt stale until an external rule audit supplies a new exact receipt.

Source states: VERIFIED, NOT_VERIFIED, SUPERSEDED, CONFLICT, MISSING_SOURCE.
Every included rule must match an exact documentId/documentRevision/sourceHash
in the source registry. v0 accepts archived UTF-8 source text content and checks
its SHA-256, not filenames or implied trust in an SP/GOST label.
The location has section, paragraph, table and appendix; at least an exact
paragraph/table/appendix is mandatory. Section alone is insufficient.
A matching verifiedLocations record must carry the exact location, actual text,
textHash, sourceHash, VERIFIED status, verificationId and evidenceKind
VERIFIED_SOURCE_TEXT. The text must occur in the archived document content.
Search snippets, AI summaries and unverified PDF evidence kinds are rejected.

Source/rule VERIFIED receipts are asserted by the external verified library
workflow; this layer validates their consistency and traceability, not the
authenticity or legal currentness of Russian standards. It never marks a source
verified by reading its filename, searching the Internet or generating a summary.
Source documents are deduplicated by exact evidence; every rule keeps provenance.
The bundle preserves actual located text and hashes so selected revisions remain
reproducible without later registry lookups.

## Revision and dependency decisions

revisionMetadata declares ACTIVE_REVISION, SUPERSEDED_REVISION or RETIRED_REVISION
and explicit decisionId. supersedes/dependencies contain exact branchId, ruleId
and revision references. Revision/date sorting never chooses an active revision.
Multiple active revisions, unresolved supersession references, inconsistent target
states and supersession cycles block. Supersession history records replacing and
superseded revisions; only the declared active VERIFIED revision compiles.

Dependencies must resolve to active applicable VERIFIED rules in the selected
scope. This v0 does not silently widen project class/domain selection to load a
missing dependency. Missing dependencies create explicit gaps; their consumers
are removed transitively from compiledRules. Dependency cycles also block.
dependencyIndex and impactIndex retain exact revision links and downstream domains.

## Requirement preservation and conflicts

Requirements declare domain, subject, scope, operator, value, unit and
downstreamDomains. Supported operators are eq/neq/gt/gte/lt/lte/in/not_in.
The requirement is preserved as supplied by the verified rule receipt.
The compiler checks only contradictions among simultaneously applicable rule
declarations in the same domain/subject and overlapping scopes. Incompatible
bounds/equalities/sets, strict endpoints and count intervals are detected.
Mixed units create an unresolved conflict, not an implicit conversion.
PROJECT scope overlaps explicit narrower targets. Conflict records retain both
rules/revisions, applicability evidence, source provenance and conflict domain.
The compiler does not evaluate any requirement against actual project geometry
or issue actual >= required / compliance results.

## Snapshot, gate and refresh

Snapshots carry bundleId, snapshotId, createdFromLibraryFingerprint,
libraryFingerprint, projectFingerprint, selectedRuleRevisions, sourceHashes,
applicabilityFingerprint and normativeBundleFingerprint/bundleFingerprint.
No random IDs, clock or timestamps participate in canonical fingerprints.
The full library fingerprint identifies the archived global revision; changing
unrelated global content can change that fingerprint for a newly built snapshot,
but never changes the existing project snapshot.

VERIFIED requires the five upstream gates and coherent fingerprint chain,
resolved classification, resolved required coverage, VERIFIED production rules,
complete source chains, unambiguous active revisions, no blocking conditional/gap,
no conflicts, full provenance, no invented norms/assumptions and determinism.
Gate proof and every production rule's provenance are exported.

Upstream fingerprint/status changes invalidate live gate state; scope changes
invalidate it as well. Historical snapshot content remains unchanged.
`compare_library(new_library)` is a read-only offline operation returning:
UNCHANGED, UPDATE_AVAILABLE_NONBLOCKING, REQUIRES_REAUDIT or
BLOCKED_BY_NORMATIVE_CHANGE. It never automatically rewrites or adopts the snapshot.
Comparison projects registry/source/rule/applicability changes onto class/domain
dependencies, including new rules and newly relevant branches. Changes to unrelated
classes/domains and unrelated entries during a global registry revision increment
do not invalidate the project. Related source/hash/status, applicability, selected
rule/revision/supersession and coverage changes are detected with affected inputs,
existing bundle rules and downstream domains. Optional changes can be nonblocking.

`adopt_library(new_library)` explicitly adopts a relevant update and invalidates
the live gate until full re-audit. UNCHANGED is a no-op. The caller archives any
exported old snapshot before replacing its current snapshot reference; old exported
bytes remain reproducible. This separation avoids background updates to a project
while still allowing an explicit refresh to respect revoked source evidence.

## Offline acceptance

```powershell
python -m normative_bundle --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --functional-brief docs/examples/functional_program_v0/brief.json --intent docs/examples/design_intent_v0/ranked-intent.json --site-sources docs/examples/site_context_v0/site-sources.json --site-requirements docs/examples/site_context_v0/requirements.json --constraint-sources docs/examples/project_constraint_input_v0/constraints.json --library docs/examples/project_normative_bundle_v0/synthetic-library.json --scope docs/examples/project_normative_bundle_v0/scope.json --output work/normative-bundle.json
```

Optional --compare-library emits an impact report for a verified pinned bundle.
Exit 0 indicates VERIFIED or a successful nonblocked compare; exit 2 indicates
a blocked bundle/compare. All test normative values are explicitly synthetic.
Module acceptance covers all 48 requested scenarios plus robustness checks;
existing Stage 0/FP/DI/Site/Project Constraints/QA/Stage 2/Stage 3/Audit Pack suites
run without changes. No production normative-library content is edited for tests.
