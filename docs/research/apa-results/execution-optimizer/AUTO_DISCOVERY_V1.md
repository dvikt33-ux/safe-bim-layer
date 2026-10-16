# Automatic Native Strategy Discovery — APA v1

**Source branch:** `feature/apa-capability-auto-discovery-20261017`, draft PR #130.
**Delivery:** additive sidecar + two optional entrypoints; no changes to native
executor, SceneWriter SQLite, Archicad, opened PLN, or `main`.

## Why

The first Fast Downward adapter required callers to pre-enumerate competing
strategies. That leaves the key question — whether to use individual create,
batch create, copy-first, or domain-specific native command — unresolved.

`scripts/archicad_strategy_discovery.py` starts moving strategy generation
into APA itself, without inventing a second command catalog or BIM writer.

## Supported recipe families (explicit V1 limit)

The adapter scans the **entire existing dynamic command catalog** and policy
review records. For repetitive source-qualified targets, it currently knows
how to construct typed native alternatives from **two** operation contracts:

- `MoveElements(copy=true)`: all target families match verified live native
  prototypes through existing `DynamicCommands.plan_reuse_existing` (Column,
  Beam or Object) and produce <=200 native copies in one batch.
- `CreateColumns`: the caller supplies complete per-target
  `nativeCreateData`, matching target anchors/story and with explicit
  material, section and height; the adapter groups all rows in one native
  `CreateColumns` batch. No dimensions/materials/favorites are inferred.

For each candidate, the **existing** `DynamicCommands.prepare_workflow`
validates the same native catalog schema, reviewed policy and BIM Graph.
Unknown/unregistered command effects are rejected.

**Limit:** reviewing the full catalog does NOT mean every command can already
be compiled into a strategy. Other element types (Beam create, Wall,
morph, GDL object, IFC, MEP, stairs, drawing/issue commands, axis grids) need
their own safe recipe adapters, source qualification and measurement.

## Cost comparison and correctness

- Two or more qualified complete strategies: Fast Downward chooses only
  if **all** have independently supplied **end-to-end measured cost** for the
  **exact same batch cardinality** and **matching reviewed contract hash**.
  Native transport time by itself is NOT end-to-end cost.
- Missing or stale measurements: return
  `COST_COMPARISON_BLOCKED_UNCALIBRATED_ALTERNATIVES`, no selected executor.
  **Do not claim speed improvement.**
- One schema-validated and source-qualified route: prepare it without
  pretending that Fast Downward optimized anything.
- Already fulfilled model: `NO_CHANGES_REQUIRED`, no model write.
- Missing families, incomplete construction attributes, unsupported
  command, unknown effect, source conflict or schema validation failure:
  FAIL CLOSED, no silent partial construction.
- All return values are **planning previews**. Upstream receipts/source refs
  are caller supplied and are not independently verified against a live model
  by this step. Actual build still requires validated scopes and independent
  BREP, GUID and attribute readback in existing SceneWriter.

## Input contract

```python
from archicad_project_accelerator import prepare_auto_optimized_native_task

preview = prepare_auto_optimized_native_task(router, {
    "schemaVersion": "apa-native-auto/1",
    "request": "Source-qualified 100x50 timber studs in the framed house",
    "existing": [
        # Actual existing native GUID, type, familySignature, storyIndex,
        # anchor: {x,y,z}, nativeReadbackVerified=True
    ],
    "targets": [
        # type, familySignature, storyIndex, anchor, sourceRef (KR drawing)
        # Optional: nativeCreateData complete column data for comparison
    ],
    "benchmarks": {
        # "MoveElements": {"batchSize": 100, "endToEndMs": ...,
        #  "evidenceRef": "actual end-to-end receipt",
        #  "contractHash": router.contract_hash("MoveElements")},
        # "CreateColumns": ... analogous, same job size
    }
})
```

NativeCreateData must be available from source-qualified drawings and native
element specifications; the adapter does not generate BIM from natural
language. `run_auto_optimized_native_task` can be invoked only with separate
explicit authorization, configured original SceneWriter scopes and readbacks.
No automatic execution occurs after discovery.

## Safe local installation

The user's previous local APA was recovered with all local source bytes
intact and only two previous optimizer entrypoints appended. The exact
user-confirmed source SHA is:
`e7d9ae310f7a7022a2262b8d7c3944a1b23c8feed49c20ec933190ba583ff727`.

`scripts/apa_install_strategy_discovery.py` never replaces the main core
with GitHub source. It refuses SHA drift, duplicate installation or missing
backups. It appends only two new wrappers to the existing local bytes,
installs one sidecar module, creates a new backup without touching the earlier
recovery backup, compiles/imports modules and rolls back on failure.
Read-only preflight is default; `--apply` is explicit. The installer never
talks to Archicad, SceneWriter, or any PLN.

## Test status

`tests/test_apa_strategy_discovery.py` uses the real solver for the
costed alternatives and checks no-cost uncertainty, command-policy guards,
unmatched families, invalid columns, duplicate anchors, wrong model story,
stale benchmark contract and unchanged native execution route. The offline
cost values in tests are **synthetic** and cannot be cited as live speedups.

`tests/test_apa_install_strategy_discovery.py` checks exact source-byte
preservation, backup creation, dry-run, hash drift and idempotency refusal.
