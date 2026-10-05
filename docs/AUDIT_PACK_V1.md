# Deterministic historical Audit Pack, schema 1

Full dumps remain primary evidence. This tool only reads local files. It imports no
Archicad runtime, makes no network requests, and dispatches no commands. The pack
adds derived evidence to the existing Stage 1 and Stage 3 runs without editing them.

## Build and verify

From the repository root, with historical LFS files downloaded:

```powershell
git lfs pull
python scripts/build_audit_pack.py --historical-stage 3 --deterministic --output work/stage3-audit
python scripts/verify_audit_pack.py work/stage3-audit
python scripts/build_audit_pack.py --historical-stage 1 --deterministic --output work/stage1-audit
python scripts/verify_audit_pack.py work/stage1-audit
python -m unittest discover -s tests_audit_pack -v
```

Output must be new or empty. Every build is deterministic, including the manifest:
timestamps are omitted. `--deterministic` documents this mode explicitly; it is also
the default. CLI results are JSON with `status: PASS`, `FAIL`, or `CONFLICT`. Both
negative statuses exit with code 1. An interrupted build cannot pass verification.

For another archived run use `--contract recipe.json`. A schema 1 recipe contains:

```json
{
  "schemaVersion": 1,
  "goalId": "archived-goal",
  "modelIdentity": "identity from the archived project record, or null",
  "initial": "initial",
  "snapshots": [
    {"id": "initial", "path": "before.json", "sha256": "EXACT_SHA256", "bytes": 123},
    {"id": "before", "path": "before.json", "sha256": "EXACT_SHA256", "bytes": 123},
    {"id": "after", "path": "after.json", "sha256": "EXACT_SHA256", "bytes": 456}
  ],
  "iterations": [
    {"iteration": 1, "before": "before", "after": "after", "sourceGuid": "SOURCE_GUID",
     "createdGuid": "CREATED_GUID", "expectedLength": 1.0, "expectedAddedCount": 1,
     "compactEvidence": [{"path": "summary.json", "sha256": "EXACT_SHA256", "bytes": 789}]}
  ],
  "requireDependency": true
}
```

Paths are relative POSIX paths under `--root`. Snapshot IDs name output folders;
iterations are consecutive from 1. Add before/after snapshots and another iteration
for a longer sequence. Historical mode obtains pins from the original manifest and
GUIDs/expected lengths from archived action/result records (Stage 3) or the archived
typed request (Stage 1). Identity is attributed to a separately pinned project
identity record; it is not claimed to be embedded in the model JSON itself.

## Content and hashing

- `source.json`: recipe, source SHA-256/byte sizes, pinned historical manifest and
  compact evidence records, schema and extractor versions. No timestamp.
- `hash-chain.json`: initial -> before 1 -> after 1 -> before 2 -> after 2, with
  raw SHA-256, model fingerprint and element count for each node.
- Each snapshot has a `model-summary.json` with independently counted elements,
  type totals, materials, stories, unresolved-owner count and reported totals.
- Each summary's `elementIndex` points to the complete index for that snapshot.
  Identical indexes share one file; there are no omitted GUIDs or partial indexes.
  Index and changed-element arrays put one record per line for Connector range reads.
- Index entries retain GUID/type/homeStory/bbox only when present, and hashes of
  exact existing placement, bodies and properties groups. Missing properties/bbox
  are omitted. `fullElementHash` covers **every** field, including material bindings
  and relationships. Index entries are sorted by GUID; duplicate GUIDs fail.
- `before-after-delta.json` compares full canonical element hashes by GUID. It
  reports added, removed, changed and unchanged counts without filtering native
  body indices. Exactly one expected added GUID and no removal are required.
- Source/created walls and changed elements contain the complete JSON objects
  extracted from the full dump. `changed-fields.json` describes the exact differing
  paths; classification does not remove entries from `changed` or alter hashes.
- `geometry-check.json` recomputes straight Wall reference-line length, endpoint
  joint distance and direction cosine. Story/height/thickness/bottom offset and
  material bindings are extracted from the raw objects. It identifies the geometry
  basis explicitly. Polygon bodies remain in the full extracted objects. This is
  the historical Wall continuation check, not a general physical clash or normative
  compliance audit. Curved/degenerate lines and missing required geometry fail.
- `dependency-check.json` checks the previous created GUID against the next source
  GUID present in both dumps. Model fingerprint continuity is checked too.
- Stage 3 checks all ten normalized live dumps: six observations, two executor
  before and two executor after dumps. Archived fingerprints, pre-write hashes,
  factual read-back hashes and source/created records must agree with full dumps.
- `compact-evidence-check.json` records comparisons; disagreements return CONFLICT.
- Pack-local `.gitattributes` preserves JSON and its own bytes with `-text`, even
  under Windows `autocrlf`. It is generated and hashed in the manifest.
- `audit-pack-manifest.json` hashes every other file and gives its exact originating
  full-dump paths. The manifest does not hash itself (no circular checksum); the
  verifier re-extracts and compares the manifest bytes as well.

Canonical element/group hashing uses Python JSON serialization with sorted object
keys, preserved array order, UTF-8, compact separators and finite numbers only.
Raw dump SHA-256 hashes original bytes, including whitespace. The model fingerprint
reproduces Stage 3's algorithm: exclude only `nativeSeconds`, hash and sort entries
in elements/materials/unresolvedBodyOwners, then hash the remaining model metadata.
This is not RFC 8785 or a claimed cross-language number canonicalization scheme.

Each pack is bounded at 9 MiB. Model-wide indexes are compact; full objects are
retained only for touched/changed elements. A larger pack fails rather than silently
truncating evidence. Hash/size errors fail before writing output.

## Independent verification and trust

The verifier checks the exact file set and manifest SHA/size, then rebuilds all
derived files in a temporary directory from pinned sources. This detects an edited
audit file even if its manifest entry is updated, as well as wrong GUIDs, unexpected
additions, source edits and compact/full conflicts. A trusted Git commit supplies
the external integrity anchor; a bundle of files whose sources, pins and manifest
were all replaced is not a digital signature.

GitHub Connector can inspect these ordinary Git JSON files without resolving LFS.
Recomputing the pack requires the primary full dumps through Git LFS. No new live
run is necessary and this task does not start Stage 4.
