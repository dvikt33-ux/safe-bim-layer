# APA TN-GDL-CREATE-01 — Blocker 1 offline forensic audit

Date: 2026-10-09 (MSK)

Status: **BLOCKED / NOT_VERIFIED**.

This audit covers only the `libraryPartName` resolver and the 92 library
inventory read errors. It does not investigate geometry, placement, collision
coverage, creation, saving, PLN state, library files, or installed software.
No Archicad call was made during this audit.

## Result

The saved evidence establishes the meaning of the reported code and the exact
source-level call sites:

* `-2130313112` is `APIERR_BADPARS`, documented as “the passed parameters are
  inconsistent”. For `ACAPI_LibPart_Get`, the official return-value
  documentation specifically includes an invalid `index` in this condition.
* The 92 errors were emitted by the inventory loop's
  `ACAPI_LibraryPart_Get(&libPart)` call after assigning `libPart.index = i`.
  The saved request had no type filter. The five retained samples are indices
  7491–7495 with the same code.
* `CreateObjects` does not consume the inventory result. Its source fills
  `libPart.docu_UName` from `libraryPartName`, calls
  `ACAPI_LibraryPart_Search(&libPart, false, true)`, and assigns the returned
  `libPart.index` to `element.object.libInd`.

The target name occurs once in the 7,490 readable inventory entries, at index
7224, with the expected ownUnID. That proves a readable candidate, not the
result of the `CreateObjects` search. The unreadable portion is unresolved,
the full skipped-index list and `partCount` were not saved, and the inventory
response does not expose the placeable/missing-definition fields that affect
the search. Source and the installed Add-On are also not byte-identity proof.

Therefore the Blocker 1 clearance criterion is **not met**.

## Saved evidence inspected

The private saved session was checked through its structured files; raw dumps
and personal paths are intentionally absent from this publication.

| Evidence | Observation | Boundary |
| --- | --- | --- |
| `07-library-request.json` | `GetAvailableLibraryParts` with `{}` (no `filterByTypeId`) | Historical read-only request |
| `07-library-response.json` | 7,490 readable entries; readable indices are 1–7490; one target-name match at index 7224; `skippedCount=92`; five samples 7491–7495, all `-2130313112` | Only five skipped indices were retained; no full skipped list or `partCount` |
| `RESULT.json` | Target ownUnID and one readable-name match; zero model writes, created GUIDs and saves | Saved-session assertion, not a new live check |
| `contract-verification.json` | `CreateObjects` schema matches the PR #16 contract; required identity input is a string `libraryPartName` | Schema does not prove binary behavior |
| `APA_TN-GDL-CREATE-01_CHECKPOINT_2026-10-09.md` | Prior checkpoint correctly marked this blocker NOT_VERIFIED | Publication is a summary, not new live evidence |

The retained JSON has 7,490 readable records and a maximum readable index of
7490. Because the response stores only a five-item error sample, it is not
valid to claim that every skipped index is 7491–7582 or to reconstruct the
native `partCount` from the response alone. The only safe statement is that
each sampled error came from the inventory loop at the shown index, and that no
readable record after 7490 was returned.

## Source forensic trace

The local C++ source snapshot contains the following relevant operations.

### Inventory path

`GetAvailableLibraryPartsCommand::Execute`:

1. Calls `ACAPI_LibraryPart_GetNum(&partCount)`.
2. Loops `for (Int32 i = 1; i <= partCount; ++i)`.
3. Zero-initializes `API_LibPart`, assigns `libPart.index = i`, and calls
   `ACAPI_LibraryPart_Get(&libPart)`.
4. On any non-zero error, records the index and numeric error in
   `skippedSample` (up to five) and increments `skippedCount`.
5. On success, serializes the main GUID derived from `ownUnID`, index,
   document/file names, raw/effective type and tool-lookup diagnostics.

The source does not turn a failed `Get` into a synthetic record and does not
retry it. The relevant source lines are 705, 717–730 and 770 in the local
`LibraryCommands.cpp` snapshot.

### CreateObjects path

`ResolveLibraryPartName`:

1. Reads `libraryPartName` into a `GS::UniString`.
2. Copies it to `libPart.docu_UName`.
3. Calls `ACAPI_LibraryPart_Search(&libPart, false, true)`.
4. Frees `libPart.location`.
5. On success assigns `element.object.libInd = libPart.index`.

`CreateObjectsCommand::SetTypeSpecificParameters` invokes this helper before
the common object placement fields. The relevant source lines are 1630–1646
and 1855–1861 in the local `ElementCreationCommands.cpp` snapshot.

The compatibility wrapper in `MigrationHelper.hpp` forwards these calls to the
legacy `ACAPI_LibPart_*` API family. The local source advertises Add-On version
1.5.10 and registers `CreateObjects` as command version 1.5.7, but those strings
do not identify the bytes loaded by the earlier live session.

## API semantics and resolver equivalence

Graphisoft documents `ACAPI_LibPart_Get` as an index-based read: fields other
than `index` are output fields, and `APIERR_BADPARS` includes an invalid index.
Graphisoft documents `ACAPI_LibPart_Search` as a loaded-library search where
document names are not unique; a search by document name can be narrowed with
`parentUnID`, while `onlyPlaceable=true` restricts the result to placeable
parts.

The two paths therefore have different inputs and coverage:

| Question | Inventory evidence | CreateObjects resolver |
| --- | --- | --- |
| Primary key | Numeric index from `GetNum` | `docu_UName` passed to `Search` |
| Placeability gate | Not serialized by this command | Explicit `onlyPlaceable=true` |
| Identity returned | Main GUID from readable `ownUnID` | Search-populated `ownUnID` and index, but not returned by the command before creation |
| Duplicate-name behavior | One match among readable records | Documentation says document names are not unique; selected match is not proven |
| Failed/unreadable entries | Counted, only five samples retained | No evidence of how an unreadable entry participates in name search |
| Creation input | `libraryPartName` string only | No ownUnID/index field in the PR #16 schema |

This is why “one matching readable row at index 7224” cannot be promoted to
“`CreateObjects` will resolve ownUnID X at index 7224”. The current evidence does
not show the same native resolver result.

## Counterexamples checked

The following explanations remain possible from the saved material and are not
interchangeable:

* The registry count could include slots that `Get` rejects as inconsistent
  indices. This would explain a trailing run of `APIERR_BADPARS`, but the
  complete skipped-index list and native count were not saved, so it is only a
  hypothesis.
* An unreadable or omitted entry could share the target document name. The
  readable subset cannot disprove that duplicate.
* The readable candidate could fail the resolver's `onlyPlaceable` criterion;
  the inventory response does not expose `isPlaceable`.
* A readable row could carry a missing or otherwise unusable definition while
  still exposing catalog metadata. The saved inventory did not perform the
  name-search read-back required by the clearance criterion.
* The source snapshot may differ from the loaded APX. Matching version strings
  and a matching PR schema are not binary identity evidence.

No one of these possibilities is asserted as the cause of the 92 errors.

## Offline verification

The existing saved-evidence verifier was run without an endpoint:

```text
manifestFilesVerified: 47
baselineParametersIdentical: 96
inventoryIdentical: 22
readableLibraryParts: 7490
libraryReadErrors: 92
bodies: 2
schemaReferencesMatched: 11
writesAndSaves: reported zero; no live revalidation
```

This confirms the saved evidence and PR contract relationship. It does not
confirm the installed binary, clear the resolver gate, or authorize a write.

## Minimal bounded future probe

Only after separate authorization and identity-first verification of the exact
disposable PLN, run one read-only resolver diagnostic that executes the same
native call used by `CreateObjects`:

```text
API_LibPart probe = {};
copy exact libraryPartName -> probe.docu_UName;
err = ACAPI_LibraryPart_Search(&probe, false, true);
read back: err, probe.index, probe.ownUnID, probe.parentUnID,
           probe.docu_UName, probe.file_UName, probe.isPlaceable,
           probe.missingDef, probe.typeID;
```

The probe must fail closed unless `err == NoError`, `index == 7224` (or the
current preflight candidate), main ownUnID equals the expected identity,
`isPlaceable` is true, `missingDef` is false, and the returned document name
matches exactly. It must also preserve the complete before/after inventory and
record the full `GetNum` count plus every skipped index/code in the same read-
only pass. A mismatch, unexplained skipped entry, modal state or timeout is
`NOT_VERIFIED`/`UNKNOWN_OUTCOME`; no create retry follows.

This probe is intentionally not run here. The current stock
`GetAvailableLibraryParts` command does not expose an equivalent name-search
read-back, and the source snapshot is not proof that such a diagnostic is
installed.

## References

* [Graphisoft API error codes](https://archicadapi.graphisoft.com/documentation/error-codes)
* [Graphisoft `ACAPI_LibPart_Get`](https://archicadapi.graphisoft.com/documentation/acapi_libpart_get)
* [Graphisoft `ACAPI_LibPart_Search`](https://archicadapi.graphisoft.com/documentation/acapi_libpart_search)

Conclusion: **Blocker 1 remains BLOCKED / NOT_VERIFIED.** The next practical
step is the bounded read-only native name-search probe above; Blocker 2 remains
out of scope for this pass.
