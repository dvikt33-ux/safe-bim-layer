# Windows SQLite lifecycle gap repair

The combined native package passed Linux regression, while local Windows
discovery produced28SQLite temporary-file cleanup errors. SQLite's connection
context manager commits/rolls back a transaction but does not close its handle.
Legacy fixtures retained those handles until garbage collection, which prevents
Windows from removing the test directory.

Five legacy fixture modules now use `closing(connection)` outside the existing
transaction context. Eleven connections close deterministically after the same
commit/rollback behavior. The read-only suffix wall diagnostic also closes its
connection on every return/error. Its existing failure/readback scenario verifies
unchanged diagnosis and zero native writes. Assertions and transaction outcomes
remain intact; cleanup errors are not ignored and garbage collection is not forced.

The existing offline contract workflow runs the same complete suite on Ubuntu
and Windows, including native-shaped readback, journal, no-replay, source-hash,
IFC and optional provider contracts. New path filters include the repaired files.
Actual Archicad is not contacted by these regression tests.

Local Windows host discovery passes all340tests in57.492seconds; schema and
sample graph contracts pass. The restricted Windows sandbox separately denies
atomic replacement of temporary watcher state files (WinError5); the same tests
pass on the actual Windows host. This environmental denial is preserved as raw
evidence and is not worked around by weakening the watcher or its assertions.

This repairs system gapG01 only. The bounded native22primary/48GUID acceptance
and saved PLN remain unchanged. Details context adapters/missing source
dimensions, connected MEP networks, Shell/Opening/SEO, structural solver/normative
acceptance, full IFC semantics and installer gaps remain open. No full product
or engineering acceptance is implied.
