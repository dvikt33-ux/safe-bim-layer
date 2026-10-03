# Offline BIM-QA blocker package

`bim_qa.py` is a separate, read-only auditor. It imports no runtime controller and
performs no network or BIM writes. Existing SafeBIMLayer signatures, Tapir payloads
and operation receipts remain unchanged.

Implemented offline checks:

- BIM-QA-001 WALL_FRAGMENTATION
- BIM-QA-002 WINDOW_NATIVE_TYPE
- BIM-QA-003 DOOR_NATIVE_TYPE
- BIM-QA-008 STORY_ASSIGNMENT
- BIM-QA-009 DUPLICATES
- BIM-QA-010 PASS_DEPENDENCY
- BIM-QA-011 MINIMUM_ELEMENT_COUNT

Rules 004–007 remain `TO_IMPLEMENT`.

An operation receipt's `PASS` is **not** a modeling-pass audit or permission to
advance the pipeline. Callers must explicitly run the auditor and require its
overall `status == PASS` before progression. Automatic runtime wiring is not part
of this package; the legacy room generator does not yet enforce these gates.

## Input contract

`audit_snapshot(snapshot, stage, previous_audits=None)` returns every rule result
plus the stage result. Missing information is `NOT_VERIFIED`; an explicit
`transportError` is `BLOCKED_BY_TRANSPORT`. Neither authorizes progression.

The command line has exit code 0 only for a stage PASS; all other statuses exit 1:

```powershell
python -m unittest discover -v
python bim_qa.py --snapshot captured-snapshot.json --stage PASS_3_WINDOWS_DOORS --output audit.json
```

Snapshot fields:

| Field | Required evidence |
| --- | --- |
| `projectId`, `snapshotId`, `auditScope` | Project identity, model revision/capture identity and scope, retained by the collector |
| `elements`, `inventoryComplete` | Complete scoped read-back inventory; rows have `guid`, native `type`, `details`, and story/floor data where used by the rule |
| `openingIntents`, `openingIntentsComplete` | Complete intended windows/doors, including substitutes: `{kind: Window/Door, guid, hostGuid}` |
| `wallSystems`, `wallSystemsComplete` | Independently specified continuous sides; `{id, guids, begCoordinate, endCoordinate, floorIndex, zCoordinate, height}` |
| `storyIntents`, `storyIntentsComplete` | One record for every controlled GUID: `{guid, floorIndex, elevationMode}` and `baseElevation` when `elevationMode == ABSOLUTE_BASE` |
| `controlledGuids`, `controlledInventoryComplete` | Complete generated element scope; manual elements are excluded only by an evidenced ownership decision |
| `identityRegistry`, `identityRegistryComplete` | Read-back identity traces for every controlled GUID: `{guid, entityId, role, identityScope}` |
| `operationJournal`, `operationJournalComplete` | Complete journal: `{operationId, status: DONE/RECONCILED, guids}`; every controlled GUID is covered |
| `elementEconomyIntents`, `elementEconomyComplete` | Trusted semantic construction contract covering every controlled GUID; each intent declares `{id, semanticRole, guids, maxElementCount, strategyKind}` and `operationName` for `NATIVE_OPERATION` |

Completeness flags must be literal `true`. They are assertions by the trusted
collector, not facts that the auditor can discover from a JSON file. Do not set
them based on a create response, a selected subset, a successful HTTP request,
or planner intent inferred from the generated geometry.

The same restriction applies to `maxElementCount`: the generator is not allowed
to inspect its own fragmented output and then declare that count to be minimal.
The value must come from a trusted design/reference contract or reviewed
construction intent established before/independently from the generated result.

Keep raw requests/responses and ownership/identity evidence outside sanitized
fixture directories. This package does not authenticate files or prove that a
supplied snapshot is the currently open model.

## Existing read-back adapter

`snapshot_from_readback(response, requested_guids, metadata)` accepts the retained
Tapir `GetDetailsOfElements` HTTP envelope, its extracted add-on response, or an
existing SafeBIMLayer receipt containing `readbackResponse` and `guids`.

It uses the exact retained **read request** GUID order and checks cardinality,
unique GUIDs, response errors and available GUID correspondence. Tapir's `id`
is an element label, not a GUID. Do not supply an unrelated inventory's order.

The adapter never invents inventory completeness, semantic intent, story intent,
identity evidence, or element-economy intent.

## Rule boundaries

### BIM-QA-001 — WALL_FRAGMENTATION

Every scoped Wall must belong to exactly one independently specified continuous
system. Straight segments are projected onto that side; lengths, collinearity,
interval coverage, gaps/overlaps, story, absolute base Z and height are checked
with fixed 1e-6 metre tolerance.

Any split needs:

```json
{
  "fragmentationException": {
    "category": "material",
    "reason": "real construction reason",
    "reviewedBy": "reviewer",
    "approved": true
  }
}
```

Allowed categories are `construction`, `geometry`, `renovation`, `material`,
`story`, `ownership`, `api_limitation`. `api_limitation` additionally requires
`fallbackReviewed: true`; a transport limitation alone cannot silently authorize
a degraded model. Opening/gable/visual convenience is not an allowed reason.

Curved or unsupported wall geometry stays `NOT_VERIFIED`. This remains an
intent-relative detector; falsely partitioned intent can hide fragments and
therefore wall-system intent must not be derived from the generated fragments.

### BIM-QA-002 / 003 — WINDOW_NATIVE_TYPE / DOOR_NATIVE_TYPE

Every intended Window/Door must exist with that native type and its intended
owner GUID, whose actual inventory type is Wall. Missing host data stays
`NOT_VERIFIED`; proven substitutes or wrong hosts fail. Unmapped native openings
also prevent PASS.

### BIM-QA-008 — STORY_ASSIGNMENT

Every controlled GUID must have exactly one trusted `storyIntents` record.

`elevationMode` is explicit:

- `STORY_ONLY`: floor/story assignment is authoritative for this element;
- `ABSOLUTE_BASE`: floor/story assignment and absolute base elevation are both
  checked. The auditor accepts normalized `baseElevation` from the collector;
  for Wall it may read `details.zCoordinate` directly.

Missing actual floor/story data is `NOT_VERIFIED`; a proven mismatch is `FAIL`.

### BIM-QA-009 — DUPLICATES

Distinct actual GUIDs with the same `(identityScope, entityId)` or
`(identityScope, role)` fail. `role` means a unique semantic path such as
`house/south/window/2`, not a generic type such as `Window`.

Repeated read-back or journal references to the same GUID are not duplicate
elements. Unknown outcomes, incomplete traces, stale GUIDs or uncovered journal
elements prevent PASS.

Geometrically identical elements with different identities are not detected by
this semantic-identity check; BIM-QA-011 covers a different class of modeling
error where distinct legitimate IDs still represent unnecessary fragmentation.

### BIM-QA-010 — PASS_DEPENDENCY

Recomputes all current scoped blockers and the full predecessor chain from the
JSON pipeline. Predecessor PASS claims require every scoped rule result, matching
stage/project/snapshot/scope, and their own predecessors.

Status precedence is FAIL, BLOCKED_BY_TRANSPORT, NOT_VERIFIED, PASS. Rule 010
excludes itself to avoid recursive self-dependency. A new model revision requires
re-auditing predecessors; old PASS reports cannot be reused.

### BIM-QA-011 — MINIMUM_ELEMENT_COUNT

This check encodes the architectural rule **operations before fragmentation**.

For every controlled semantic role the trusted contract declares:

```json
{
  "id": "house/front/gable-wall",
  "semanticRole": "gable wall",
  "guids": ["..."],
  "maxElementCount": 1,
  "strategyKind": "NATIVE_OPERATION",
  "operationName": "TrimElementsToRoofShell"
}
```

Allowed `strategyKind` values are:

- `NATIVE_ELEMENT`
- `HOSTED_NATIVE`
- `NATIVE_OPERATION`
- `COMPLEX_PROFILE`
- `GDL`
- `MINIMAL_MULTI_ELEMENT`

The rule fails when the actual GUID count for a semantic role exceeds
`maxElementCount` without an approved exception. It also requires complete
coverage of `controlledGuids`; missing or overlapping intent coverage stays
`NOT_VERIFIED`.

Examples:

- one gable Wall + roof trim: PASS when max count is 1;
- several stacked gable Walls for the same role: FAIL;
- one host Wall + native Window: PASS;
- many wall fragments around a supposed opening: FAIL through 001/002/011;
- one/minimal porch Slab set + polygon edit/SEO: PASS when it matches the trusted
  max count;
- many small porch slabs merely because scripting them is easier: FAIL.

A reviewed fragmentation exception uses the same exception contract as rule 001.
For `api_limitation`, `fallbackReviewed: true` is mandatory.

## Validation state

Offline implementation does not equal live BIM validation.

`implementationState == IMPLEMENTED_OFFLINE` means the checker and regression
tests exist. `liveValidationState == NOT_VERIFIED` remains until a controlled
read-only live capture proves the evidence contract against Archicad.

Rules 004–007 remain `TO_IMPLEMENT`. Therefore roof, wall-top and rafter stages
cannot receive a complete final PASS yet.

No production PLN should be opened or modified merely to satisfy this package.
