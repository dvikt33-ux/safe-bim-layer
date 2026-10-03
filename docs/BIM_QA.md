# First offline BIM-QA blocker package

`bim_qa.py` implements BIM-QA-001/002/003/009/010 as a separate, read-only
auditor. It imports no runtime controller and performs no network or BIM writes.
Existing SafeBIMLayer signatures, payloads and operation receipts are unchanged.
An operation receipt's `PASS` is **not** a modeling-pass audit or permission to
advance the pipeline. Callers must explicitly run the auditor and require its
overall `status == PASS` before progression. Automatic runtime wiring is not
part of this package; the legacy room generator does not enforce these gates.

## Input contract

`audit_snapshot(snapshot, stage, previous_audits=None)` returns all ten rule
results plus a stage result. Missing information is `NOT_VERIFIED`; an explicit
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
| `elements`, `inventoryComplete` | Complete scoped read-back inventory; rows have `guid`, native `type`, `details`, and wall `floorIndex` |
| `openingIntents`, `openingIntentsComplete` | Complete intended windows/doors, including substitutes: `{kind: Window/Door, guid, hostGuid}` |
| `wallSystems`, `wallSystemsComplete` | Independently specified continuous sides; `{id, guids, begCoordinate, endCoordinate, floorIndex, zCoordinate, height}` |
| `controlledGuids`, `controlledInventoryComplete` | Complete generated element scope; manual elements are excluded only by an evidenced ownership decision |
| `identityRegistry`, `identityRegistryComplete` | Read-back identity traces for every controlled GUID: `{guid, entityId, role, identityScope}` |
| `operationJournal`, `operationJournalComplete` | Complete journal: `{operationId, status: DONE/RECONCILED, guids}`; every controlled GUID is covered |

Completeness flags must be literal `true`. They are assertions by the trusted
collector, not facts that the auditor can discover from a JSON file. Do not set
them based on a create response, a selected subset, a successful HTTP request,
or planner intent. Keep raw requests/responses and ownership/identity evidence
outside this sanitized fixture directory. This package does not authenticate
files or prove that a supplied snapshot is the currently open model.

An explicitly complete empty scope may pass an individual check. An absent or
incomplete scope cannot. Intents must include Morph/Object substitutes; neither
names nor library filenames are used to infer semantic type. A native type
without its intended and actual wall host is insufficient.

## Existing read-back adapter

`snapshot_from_readback(response, requested_guids, metadata)` accepts the retained
Tapir `GetDetailsOfElements` HTTP envelope, its extracted add-on response, or an
existing SafeBIMLayer receipt containing `readbackResponse` and `guids`.
It uses the exact retained **read request** GUID order and checks cardinality,
unique GUIDs, response errors and available GUID correspondence. Tapir's `id`
is an element label, not a GUID. Do not supply an unrelated inventory's order.
The adapter never invents inventory completeness or intent/identity evidence.
Type, ownerElementId, floorIndex and wall geometry come from actual read-back.
Safe BIM v0.1 has no complete identity registry/journal export: DUPLICATES stays
NOT_VERIFIED until the caller supplies independently captured complete traces.

`tests/fixtures/tapir_readback_partial.json` is a sanitized historical capture
from paired local requests/responses (2026-10-02). It retains one Wall and two
Window rows with native types, geometry and host relation, removes machine GUIDs
and unused metadata, and includes hashes of its raw sources. It proves adapter
compatibility only. It does not prove project identity, scope completeness,
Door behavior in a live model, or a full-house PASS. Other test inputs are
explicitly synthetic.

## Rule boundaries

- **001:** every scoped Wall must belong to exactly one independently specified
  continuous system. Straight segments are projected onto that side; lengths,
  collinearity, interval coverage, gaps/overlaps, story, absolute base Z and height
  are checked with fixed 1e-6 metre tolerance. Any split needs
  `fragmentationException: {category, reason, reviewedBy, approved: true}`.
  Categories are construction, geometry, renovation, material, story, ownership,
  api_limitation. Opening/gable/visual excuses fail. Curved or unsupported wall
  geometry stays NOT_VERIFIED. This is an intent-relative detector, not an
  automatic reconstruction of facade systems; falsely partitioned intent can
  hide fragments and therefore must not be derived from the generated fragments.
- **002/003:** every intended Window/Door must exist with that native type and
  its intended owner GUID, whose actual inventory type is Wall. Missing host
  data stays NOT_VERIFIED; proven substitutes or wrong hosts fail. Unmapped native
  openings also prevent PASS.
- **009:** distinct actual GUIDs with the same `(identityScope, entityId)` or
  `(identityScope, role)` fail. `role` means a unique semantic path such as
  `house/south/window/2`, not a generic type such as `Window`. Repeated read-back
  or journal references to the same GUID are not duplicate elements. Unknown
  outcomes, incomplete traces, stale GUIDs or uncovered journal elements prevent
  PASS. Geometrically identical elements with different identities are not
  detected by this semantic-identity check.
- **010:** recomputes all current scoped blockers and the full predecessor chain
  from the JSON pipeline. Predecessor PASS claims require every scoped rule
  result, matching stage/project/snapshot/scope, and their own predecessors.
  Status precedence is FAIL, BLOCKED_BY_TRANSPORT, NOT_VERIFIED, PASS. Rule 010
  excludes itself to avoid recursive self-dependency. A new model revision
  requires re-auditing predecessors; old PASS reports cannot be reused.

Rules 004–008 remain TO_IMPLEMENT/NOT_VERIFIED. In particular, mandatory rule
008 means the public auditor cannot yet grant a complete pipeline stage PASS.
Rule 010's positive behavior is tested using explicitly synthetic external
checker results; this is not live evidence. Implementation state is
IMPLEMENTED_OFFLINE for only the five delivered checks; liveValidationState is
NOT_VERIFIED. No production PLN was opened, modified or audited for this work.
