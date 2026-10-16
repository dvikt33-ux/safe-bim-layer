# Source-qualified native batch in the installed APA

`DynamicCommands.execute_batch()` packs one reviewed group into one existing
SceneWriter operation. It preserves the router's schemas, complete inventory
scope, SQLite intent before dispatch and no replay rule. The method is taken
from `feature/apa-native-bulk-writer-20261016` at
`f12aeba017ecd34a13989998f0b7700f6a0107d2`.

`scripts/apa_source_qualified_native_batch.py` is the bounded deployment entry
for a reviewed thirteen-member timber-stud manifest. It reads the source PDF
hash, saved working PLN hash, protected source hash, exact accepted GUID set,
existing journal and verified backups before allowing the one `CreateColumns`.
Each stud is a rectangular native Column with explicit section, position,
story, rotation, anchor and structural timber material.

The manifest remains private with the source project evidence. It must include
the fields used by the runner: `target`, `protectedSource`, `sourcePDF`,
`knownGuids`, `affectedGuids`, `existingWindows`, `items`, `material`,
`authorization`, `baselineBackup`, `sceneId` and `saveSceneId`.

The runner performs one batched native Details verification of the new members
and affected existing objects, reconciles native segment ownership and checks
the router's post-batch BREP response. Column physical bodies belong to owned
ColumnSegment objects. Empty Column root bodies do not imply missing geometry.
Every segment must have the correct SDK host GUID, native type, material,
section, height and absolute bounds.

SaveProject uses the same router, SceneWriter and ledger only after PASS. Its
successful response advances the authorization hash to the actual saved bytes
of the same path before the writer's post-save identity guard. Source bytes,
inventory and native geometry are checked after saving. Saved/reopened and
engineering acceptance are separate statuses.

The live deployment created thirteen physical studs with one native call, plus
thirteen automatic ColumnSegment identities. A root-only supplemental body
inspection initially stopped before save. The read-only reconciliation proved
the existing batch and its owned segment bodies; Create was not repeated.
`scripts/apa_reconcile_source_batch_save.py` is bounded to that exact historical
inspection failure. It allows only the first journaled SaveProject after a
matching recorded create PASS, unchanged live state and fresh reconciliation.

Validation is limited to four inherited batch smoke checks, one regression for
owned ColumnSegment bodies and the real Archicad 29 build 5101 batch. Measured
native creation latency was 0.171392 seconds; the complete guarded create
operation was 3.1213 seconds. These are one measured run, without a claimed
100x speedup. Detailed source, GUID, timing, saved hash and retention evidence
is stored in the private execution report.
