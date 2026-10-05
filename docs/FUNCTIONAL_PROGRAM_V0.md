# FUNCTIONAL PROGRAM v0

Functional Program formalizes **what the user wants designed**. It consumes the
existing verified Stage 0 session. It does not decide where spaces go, construct
walls, execute Closed Loop/BIM operations or compile numerical regulations.

## Working scenario

From the repository root, using the checked-in synthetic acceptance fixtures:

```powershell
python -m functional_program --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --brief docs/examples/functional_program_v0/brief.json --output work/functional-program.json
# Exit 0: FUNCTIONAL_PROGRAM VERIFIED.

python -m functional_program --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --brief docs/examples/functional_program_v0/missing-brief.json --output work/functional-program-missing.json
# Exit 2: one explicitly requested bedroom has no quantity; one precise question.

python -m functional_program --stage0-registry docs/examples/design_stage0/registry.json --stage0-sources docs/examples/functional_program_v0/stage0-sources.json --brief docs/examples/functional_program_v0/missing-brief.json --answers docs/examples/functional_program_v0/answers.json --output work/functional-program-answered.json
# Exit 0: answer ingested, full re-audit, VERIFIED.

python -m unittest tests.test_functional_program -v
```

No sample value is a default, normative value or live project fact.

## Flow and dependency

`VERIFIED STAGE 0 -> EXTRACT USER PROGRAM -> NORMALIZE FUNCTIONS -> BUILD SPACE
PROGRAM -> BUILD RELATIONSHIPS -> IDENTIFY FUNCTIONAL GAPS -> RE-AUDIT ->
FUNCTIONAL_PROGRAM VERIFIED`

The API accepts a `Stage0` session, not a dictionary containing a user-written
`status: VERIFIED`. The file entry point reconstructs and audits that same Stage 0
from its registry and sources. A failed gate yields BLOCKED with no program.

```python
program = FunctionalProgram(stage0, approved_brief_sources)
result = program.audit()
permission_proof = program.require_verified()  # Raises unless both gates pass.
program.update_source(user_answer)             # Immediately invalidates old gate.
result = program.audit()                      # Answers never bypass re-audit.
```

Stage 0 changes invalidate the existing program even when Stage 0 has subsequently
been verified again. Read and progression methods check the dependency fingerprint.
A fresh functional audit is required. Brief updates likewise invalidate the gate.
Returned copies cannot mutate the session or attach normative values to it.

## Explicit user sources and extraction

Each source has stable `id`, `kind`, `revision`, `approved: true`, `inspected: true`
and `statements` and/or `text`. Accepted kinds are USER_BRIEF, USER_CORRECTION and
APPROVED_PROJECT_DECISION. These flags are the caller's evidence boundary: the
module does not assert approval for unreviewed LLM extraction or unlisted files.

Structured statements use stable IDs and these kinds:

| Kind | Explicit content |
| --- | --- |
| SPACE | spaceId, function, quantity, optional user attributes |
| SPACE_ATTRIBUTE | spaceId, field, value, USER_REQUIREMENT or USER_PREFERENCE |
| USER_GROUP | userId, quantity, optional label |
| RELATIONSHIP | type, from, to, user category |
| ACCESS_GROUP | explicit shared access hub and members |
| CONTEXT | value tied to a known Stage 0 input; disagreements block |
| EXCLUDE_FUNCTION | function, reason, NOT_APPLICABLE |

Space attributes support requested area/value/range in m2, preferred floor,
access/privacy levels, noise sensitivity/generation, daylight preference, special
equipment and explicit functional zone. Quantity is a positive integer. Unknown
optional attributes remain null, not guessed. Identity fields are plain function
code and quantity; their categorized evidence is retained in identityRequirements.
Other supplied attributes are categorized records with provenance.

The text parser is deliberately bounded: one explicit statement per line, such as
`Дом для семьи из 4 человек, два этажа.`, `2 спальни по 18 м2.` or `1 кухня 12 м2.`.
Quantities must be explicit; areas are per requested space, not an inferred total.
The parser supports the aliases defined in the module and preserves exact line
spans. It does not pretend to understand arbitrary prose: unrecognized lines are
blocking normalization questions, never silently discarded or converted into
requirements. Multiple distinct spaces of one function need explicit structured
space IDs; the parser does not invent their identities.

Normalization translates explicit function labels through a deterministic lexical
alias map, and also accepts explicit uppercase custom function codes. It never
adds a room because of a project class, household size or a typical house template.

## Categories, graph and zones

Requirements and preferences are separate lists and separate claims. An explicit
18 m2 requested area remains USER_REQUIREMENT. A 20 m2 preference can coexist
without replacing that requirement. Preferred floor and daylight preference are
always USER_PREFERENCE. A preference cannot declare mandatory adjacency/access.

Supported categories are USER_REQUIREMENT, USER_PREFERENCE, DERIVED_RELATIONSHIP,
NORMATIVE_REQUIREMENT_PENDING, MISSING_FUNCTIONAL_INPUT and NOT_APPLICABLE.
Conflicting candidate values are retained with source evidence. Only explicit
USER_CORRECTION/APPROVED_PROJECT_DECISION references can supersede a specific
claim, e.g. `program:bedroom_master-intent:requestedArea`. Dates alone do not choose
between requirements.

The separate relationship graph supports REQUIRED_ADJACENCY, PREFERRED_ADJACENCY,
AVOID_ADJACENCY, REQUIRED_ACCESS, VISUAL_CONNECTION, EXTERNAL_ACCESS,
VERTICAL_CONNECTION and SEPARATION_REQUIRED. Endpoints must identify explicit
spaces; EXTERIOR is an explicit external endpoint for EXTERNAL_ACCESS. Dangling
references cause targeted gaps, not invented rooms. Required adjacency conflicting
with required avoidance/separation blocks verification.

The sole relationship derivation is EXPLICIT_ACCESS_GROUP_EXPANSION_V1: the user's
explicit instruction to access named spaces through a named hub expands to
required-access edges. Each edge is DERIVED_RELATIONSHIP and retains that rule and
its input evidence. No transitive, typical or normative adjacency is invented.

Zones public, private, service, technical, staff, circulation and
outdoor/site-related are emitted only when explicitly assigned to actual spaces.
There is no automatic assignment from a function label or an unrelated zone list.

## Gaps, gate and provenance

Blocking functional gaps are driven by explicit program content: missing function
or quantity, unresolved relationship endpoint or unsupported brief line. If the
brief contains only household size/floors, one program-scope question asks which
functions and quantities are required. No bedroom count, office or garage is
inferred from household size. Optional attributes create no unsolicited questions.
The question set covers the earliest blocking priority; each question explains
WHAT, WHY, REQUIRED_BY, FORMAT and provenance. Conflicts and validation failures
are reported explicitly and block the gate. Competing requirements produce
targeted conflict-resolution questions with their actual candidate evidence;
answers must explicitly supersede the conflicting claim IDs before re-audit.

VERIFIED requires current Stage 0 VERIFIED, no blocking functional gaps, no
conflicts/validation errors, evidence for every confirmed requirement/preference,
space and relationship, and zero invented normative values or unapproved
assumptions in the output. Canonical ordering, explicit stable IDs and content
fingerprints yield deterministic repeated output. No timestamps/random IDs enter
the program. Exact input yields byte-identical canonical JSON.

## Future PROJECT NORMATIVE BUNDLE boundary

User Program is independent of normative constraints. Every space has a
`normativeMinimum` marker with NORMATIVE_REQUIREMENT_PENDING and **no numerical
value**. Pending entries carry only space IDs and scope markers, not regulations.
Missing normative numbers do not block verification of the user's program.

A future PROJECT NORMATIVE BUNDLE must be a separate versioned artifact referencing
the programFingerprint and stable space IDs. A later Constraint Compilation may
consume both artifacts; it must not overwrite requestedArea, userRequirements,
userPreferences or Functional Program provenance. This v0 has no normative bundle
compiler, attachment mutator or numeric constraint engine. Normative/geometric
payload fields are rejected by the brief schema.

## Acceptance and regressions

All 15 requested scenarios are executable in RequiredScenarios. Additional tests
cover the CLI answer/re-audit scenario, all relationship types, explicit zones,
normative/geometric payload rejection, requirement/preference separation,
contradictory adjacency, unsupported/negative prose, explicit corrections,
missing endpoints, Stage 0 disagreement, exclusions and gate forgery.

Existing Stage 0 and QA tests run in this branch unchanged. Existing Stage 2/3/
Audit Pack tests run unchanged at `03c64733bb2b4f59970f5247a3ed89e1236f3090` with
the new intake/program modules and tests overlaid. Only offline adapters and
existing evidence are used. Runtime, Closed Loop and main stay unchanged.
