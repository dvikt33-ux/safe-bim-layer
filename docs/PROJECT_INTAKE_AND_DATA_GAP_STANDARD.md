# Stage 0 — Project Intake and Data Gap Standard

Status: **draft normative workflow rule**  
Version: **0.1**  
Scope: Safe BIM project orchestration before normative analysis, design, BIM generation, and documentation.

## 1. Purpose

Stage 0 exists to prevent Safe BIM / GPT from starting design work on incomplete, contradictory, or weakly classified project data.

Before normative research or any design stage begins, the agent MUST first inspect the complete project information already available to it, determine what project class and regulatory branches are applicable, identify which required inputs are already known, derive what can be derived, detect conflicts, and ask the user only for the remaining information that is actually required.

Stage 0 is not a generic questionnaire. It is an evidence-based project intake audit.

## 2. Mandatory sequence

The agent MUST execute Stage 0 in this order:

```text
COLLECT AVAILABLE PROJECT INFORMATION
-> NORMALIZE AND INDEX SOURCES
-> CLASSIFY PROJECT
-> BUILD APPLICABILITY MATRIX
-> BUILD REQUIRED INPUT MATRIX
-> MAP EXISTING DATA TO REQUIREMENTS
-> DERIVE SAFE DERIVABLE VALUES
-> DETECT CONFLICTS
-> IDENTIFY GAPS
-> PRIORITIZE USER QUESTIONS
-> RE-AUDIT AFTER USER ANSWERS
-> STAGE_0 VERIFIED
```

The agent MUST NOT begin the dependent normative/design stage while Stage 0 has unresolved required gaps or unresolved input conflicts.

## 3. Sources the agent MUST inspect before asking the user

Where accessible in the active project context, the agent MUST inspect relevant information from:

- the current user task / technical brief;
- project files and drawings;
- project-specific GitHub repositories;
- existing Safe BIM project state;
- existing Archicad model read-back;
- prior approved project decisions and structured project records;
- already compiled normative/project rule registries;
- explicit user corrections that supersede earlier data.

The agent MUST NOT ask the user for information that is already available and sufficiently trustworthy in these sources.

## 4. Project classification

The agent MUST classify the project before choosing regulatory or design branches.

Classification MAY include, where relevant:

- project type / functional class;
- country and jurisdiction;
- region / municipality / site location;
- building purpose;
- building class / category;
- number of storeys;
- area / volume bands;
- occupancy / users;
- fire and evacuation significance;
- structural system family;
- renovation/new-build status;
- site / plot status;
- special conditions or protected zones.

Classification MUST be evidence-backed. An unresolved classification conflict blocks dependent normative routing.

## 5. Applicability matrix

After classification, the agent MUST create an applicability matrix defining which knowledge/rule branches are relevant to the project.

The matrix MUST be selective. A project MUST NOT automatically load or evaluate unrelated classes merely because they exist in the common rule base.

Example principle:

```text
IZHS project
-> load/apply IZHS-relevant branches
-> do not pull MKD / industrial / retail rules unless a verified condition makes them applicable
```

The applicability matrix SHOULD record:

- branch / rule family;
- status: APPLICABLE / NOT_APPLICABLE / CONDITIONAL / UNKNOWN;
- applicability basis;
- evidence source;
- unresolved conditions.

`UNKNOWN` on a branch that can materially change design requirements blocks progression until resolved.

## 6. Required input matrix

For every applicable branch and planned downstream stage, the agent MUST determine which project inputs are required.

Each required input SHOULD contain:

- stable input id;
- human-readable name;
- data type / units / accepted formats;
- whether it is blocking;
- which downstream rule/stage uses it;
- why it is needed;
- acceptable evidence/source types;
- whether it can be derived;
- derivation method, when allowed.

Required inputs MUST be driven by the actual project classification and applicable rules, not by a universal fixed questionnaire.

## 7. Input statuses

Every identified project datum MUST be assigned one of these statuses:

### `CONFIRMED`
The datum is present, sufficiently trustworthy, and unambiguous.

### `DERIVED`
The datum was not supplied directly but was computed or inferred by an approved deterministic method from confirmed evidence.

### `UNKNOWN_BUT_DERIVABLE`
The datum is absent as a direct value but can be derived from available evidence. The system SHOULD derive it before asking the user.

### `CONFLICT`
Two or more relevant sources contain incompatible values or meanings and precedence cannot be resolved automatically.

### `MISSING_REQUIRED`
The datum is required for a dependent rule or stage and cannot currently be resolved or safely derived.

### `MISSING_OPTIONAL`
The datum is useful but does not block the next required stage.

### `NOT_APPLICABLE`
The datum is not required for the verified project classification / applicability matrix.

The system MUST NOT convert `CONFLICT`, `MISSING_REQUIRED`, or unresolved `UNKNOWN_BUT_DERIVABLE` into an assumed value merely to continue.

## 8. Source precedence and provenance

Every `CONFIRMED` or `DERIVED` datum MUST retain provenance sufficient to explain where it came from.

At minimum, provenance SHOULD record:

- source kind;
- source identifier/path/document;
- source revision/date where available;
- extraction or derivation method;
- confidence / verification status;
- supersession relation when a later user-approved value replaces an earlier one.

When sources disagree, the system MUST either:

1. resolve the conflict using an explicit approved precedence rule; or
2. mark the datum `CONFLICT` and ask for resolution.

Silent source selection is forbidden for blocking inputs.

## 9. Derivable data

The agent SHOULD calculate values itself when the derivation is deterministic, traceable, and based only on confirmed evidence.

Examples may include:

- area derived from an accepted closed polygon;
- building count from a trusted model inventory;
- floor count from verified storey data;
- distances measured from trusted coordinates;
- sums or ratios derived from confirmed schedules.

A `DERIVED` datum MUST retain:

- formula/method;
- input evidence references;
- units;
- result;
- validation status.

The agent MUST ask the user instead when the derivation would require an unverified assumption, subjective interpretation, or unavailable evidence.

## 10. User question policy

The user MUST NOT receive a generic exhaustive questionnaire.

Questions MUST be generated only after the complete available project context has been inspected and data gaps have been classified.

Questions MUST be ordered by dependency / blocking priority:

1. classification blockers;
2. regulatory applicability blockers;
3. site / geometry blockers;
4. structural / engineering blockers;
5. functional planning blockers;
6. documentation blockers;
7. optional preferences.

For every `MISSING_REQUIRED` or user-resolved `CONFLICT`, the question SHOULD state:

- exactly what is needed;
- why it is needed;
- which rule/stage depends on it;
- acceptable units/formats or source documents;
- whether an approximate value is acceptable (only when explicitly allowed).

The system SHOULD ask the minimum set of questions required to unblock the next dependency layer, then re-run Stage 0 rather than dumping all possible future questions at once.

## 11. Stage 0 states

Recommended machine states:

```text
NOT_STARTED
RESEARCHING
CLASSIFYING
BUILDING_INPUT_MATRIX
DERIVING
AUDITING_GAPS
WAITING_FOR_USER_DATA
RECHECKING
VERIFIED
INVALIDATED
```

## 12. Acceptance gate

Stage 0 MAY become `VERIFIED` only when all mandatory conditions are true:

```text
project_classification == VERIFIED
applicability_matrix_complete == true
required_input_matrix_complete == true
missing_required_count == 0
unresolved_conflict_count == 0
blocking_unknown_derivable_count == 0
unapproved_assumption_count == 0
provenance_complete_for_blocking_inputs == true
```

`MISSING_OPTIONAL` does not block Stage 0 unless the downstream stage explicitly promotes that input to required.

## 13. Fail-closed progression rule

The next dependent stage MUST NOT start when Stage 0 is:

- `WAITING_FOR_USER_DATA`;
- `INVALIDATED`;
- carrying any unresolved `MISSING_REQUIRED`;
- carrying a blocking `CONFLICT`;
- carrying a blocking unresolved `UNKNOWN_BUT_DERIVABLE`;
- based on unapproved assumptions.

No placeholder, guessed, typical, default, or statistically likely value may silently replace a blocking missing datum.

## 14. Re-entry and invalidation

Stage 0 is not one-time-only.

It MUST be re-opened when new information changes a material project classification, applicable rule branch, or blocking project input.

Examples:

- project function changes;
- site/municipality changes;
- storey count changes;
- building class changes;
- a previously unknown protected zone is discovered;
- a new source invalidates an earlier confirmed value.

The orchestrator SHOULD invalidate only dependent downstream outputs when impact can be scoped safely. Unaffected verified outputs SHOULD remain valid.

## 15. Relationship to later stages

Stage 0 provides a verified input contract to downstream stages.

Suggested high-level sequence:

```text
STAGE 0  PROJECT INTAKE + DATA GAP AUDIT
-> STAGE 1  NORMATIVE BASE
-> STAGE 2  CONSTRAINT COMPILATION
-> STAGE 3  CONSTRUCTION FEASIBILITY
-> STAGE 4  FUNCTIONAL / LAYOUT DESIGN
-> STAGE 5  COORDINATION
-> STAGE 6+ BIM / ARCHICAD PASSES + READ-BACK QA
-> FINAL RELEASE AUDIT
```

Each downstream stage MAY discover a new blocking input. In that case the orchestrator MUST return the relevant dependency to Stage 0 instead of inventing the value locally.

## 16. Minimum Stage 0 output contract

A successful Stage 0 result SHOULD contain at least:

```json
{
  "stage": "PROJECT_INTAKE_DATA_GAP",
  "status": "VERIFIED",
  "projectClassification": {},
  "applicabilityMatrix": [],
  "inputs": [],
  "missingRequired": [],
  "missingOptional": [],
  "conflicts": [],
  "derived": [],
  "questions": [],
  "provenanceComplete": true
}
```

When status is not `VERIFIED`, the output MUST explain which exact blockers prevent progression.

## 17. Core invariant

**Research first. Ask second. Design only after the required project data are verified.**

The agent MUST prefer explicit `MISSING_REQUIRED`, `CONFLICT`, or `NOT_VERIFIED` over silently designing from incomplete assumptions.
