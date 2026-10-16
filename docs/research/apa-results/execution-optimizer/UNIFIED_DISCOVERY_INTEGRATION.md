# Unified catalog selection integrated into installed APA

Base: PR #131, `75ae71dc60176225bb71928fb805e5adcc688b2e`.
This delivers the missing catalog/graph/install integration; it does not claim
autonomous engineering design or native acceptance of every catalog command.

## What changed

The existing `archicad_strategy_discovery.py` now accepts
`apa-capability-task/1` in addition to the V1/V2 typed target formats. A task
provides source-qualified BIM inputs, desired effects/impacts, optional element
types and required output fields. It supplies **no command names or alternative
workflows**. The selector matches all existing command schemas and reviewed
effect policies, builds complete compatible assignments and sends each to
`APA.prepare_native_task` and the existing BIM Graph compiler.

There is no second executor, graph implementation, transport or schema catalog.
The catalog view is produced from the actual DynamicCommands object. Existing
snapshots are attached with `include_source_snapshot`; existing effect reviews
are loaded with `load_policies` only on exact command-contract hash matches.
Caller policies and current contracts take priority. Historical source-only
official placeholders can be upgraded to the installed AC29 SDK's actual typed
constructors; current/caller-reviewed contracts are preserved. Importing the
official SDK performs no connection or command dispatch. An installed SDK other
than version 29 is not attached.

## Measured local coverage

The [installed-process smoke](integration/installed-smoke.json) used the actual
preserved laptop installation and its Python 3.12 interpreter, not repository
imports masquerading as installed code:

| Layer | Confirmed result |
| --- | --- |
| Catalog metadata visible to common selector | **378 / 378 contracts** |
| Existing reviewed effect classification available | **372 contracts** |
| Effect unresolved | **6 contracts**, excluded from automatic assignment |
| Existing source-only contracts | **33**, previewable but not selectable for execution |
| Official API typed constructors | **73**, extracted from installed package 29.3000 |
| Current native registration probed | **0**; all 378 reported `NOT_PROBED` |

These counts do **not** mean 372 native tools were executed or every tool can
solve every BIM intent. Schema matching, source qualification, semantic rules,
runtime checks and exact operation scopes must all pass for a selected task.
The common view exposes purpose/category, input/output schemas, element hints,
reviewed policy, contract hash, availability and separate runtime registration.
Element hints from names/descriptions help discovery; they never establish a
reviewed effect or runtime capability.

## Dependent tasks and alternatives

The committed [wall/window example](../../../../examples/accelerator/auto-discovery-integration/wall-window-task.json)
lists the window input before its host. The existing `$result` binding points
to `/elements/0/elementId/guid` of the wall step. Discovery finds CreateWalls and
CreateWindows and the existing graph compiler orders **host -> window**.
The installed APA produced an original SceneWriter native-task preview for this
chain. The selector additionally connects the graph's existing generated-wall
host-fit and overlap checks to `$result` bindings, validates pointer contracts
and rejects a non-Wall host. Other typed result values continue through the
existing `_schema_at`, `prepare_workflow` and `run_workflow` implementation.
Cycles, unknown pointers and incompatible complete assignments are rejected.
An ambiguous generated Wall host must produce exactly one GUID.

This supports multi-step create -> hosted create, create/read -> typed result
consumer, and qualified create/modify/read sequences whose prepared schemas and
existing policies match. It does not invent geometry, missing attributes,
library names or the decomposition of a natural-language building brief.
The graph retains its existing 100-step bound. Complete assignment enumeration
is bounded by the existing optimizer's 32-alternative interface; ambiguous tasks
must provide narrower typed requirements instead of silently truncating plans.

All schema-qualified alternatives receive full original APA previews even when
timings are absent. `QUALIFIED_CATALOG_ALTERNATIVES_UNCALIBRATED` retains those
previews without falsely choosing the fastest. The original V2 copy-vs-create
mode now also retains full alternative previews. `select_catalog_alternative`
allows an explicit choice with no optimality/permission claim. A sole complete
assignment is automatically prepared.

When comparable complete-workflow timings exist, the existing Fast Downward
optimizer is called. Measurements are indexed by the complete graph hash and
must include matching command hashes, task/source hash, real end-to-end time,
`NATIVE_END_TO_END` and an evidence reference. No production speed comparison
was made during this integration pass.

Every selected task still runs through the unchanged installed
`run_auto_optimized_native_task -> run_native_task -> DynamicCommands.run_workflow
-> execute -> SceneWriter`. Each mutation still requires exact authorization,
fresh project/runtime identity, complete affected/retained GUID inventory,
saved-file hash, operation-specific preflight and independent result readback.
A later result consumer runs only after the producer's original guarded
execution and verification returned successfully. Unknown outcomes keep the
existing stop/no-replay behavior; no automatic rollback of a model is added.

## Special semantic rules and objective limits

| Family | Integration | Remaining acceptance or contract constraint |
| --- | --- | --- |
| Walls/slabs/beams/columns | Existing V1/V2 target recipes retained; general schema assignment also available | Exact prepared source data and operation scopes; V2 geometric limits remain explicit |
| Windows/doors | Existing contracts + graph host fit/overlap and typed generated GUID binding | Exact host/library/settings qualification must be freshly checked before writes |
| General Opening | Common mechanism now discovers/prepares CreateOpenings from exact owner/base/width/height data | No orientation or cut extent is invented; host geometry/default interpretation and the existing `archicad_native_operations.opening_readback` must be qualified by the operation scope; no native acceptance claimed |
| True native Grid and ExactStair | Existing `archicad_native_spatial_tools.qualify_operation` and its code-owned effect sets are connected | Source-only runtime schemas are previewable, not executable until actual installed runtime/schema identity is qualified; no lines/text substitute |
| Roof | Existing `archicad_native_roof_editing.qualify_operation` is called | Its source-derived creation requires `sourceRoofId`; the currently loaded pinned CreateRoofs schema does not expose that field. The mismatch is rejected, not bypassed. A matching current extended runtime contract is required |
| Morph | Existing provider schemas are discoverable; exact body/size and explicit native-alternative exhaustion evidence required | MORPH LAST RESORT remains binding; source body/material/placement and native readback are still required |
| Remaining commands | Common schema/effect/result matching without hundreds of handwritten adapters | Unknown effects, missing schemas, explicit execution blockers and semantic incompatibility remain excluded |

Runtime registration and geometry/material/host correctness are not inferred
from a source file, installed Python package or successful offline preview.

## Actual local additive update

Status: **INTEGRATED_DISCOVERY_INSTALLED_ORIGINAL_CORE_PRESERVED**.
See the [sanitized installation receipt](integration/local-install.json).

The updater replaces the unmodified V1 discovery adapter and patches **only**
the exact V1 `DynamicCommands.plan_reuse_existing` method to its V2 version.
The complete local APA core remains byte-identical:

`5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b`.

The DynamicCommands file retains 53,881 prefix bytes and 4,845 suffix bytes,
including its local functions and later additions. Existing core wrappers are
used as installed. The entire GitHub core is never copied over the local core.
Unique backups and a durable receipt precede replacement. Current hashes must
match before rollback, so a subsequent user edit cannot be blindly overwritten.
A controlled restoration of the preceding update was actually performed and
verified before the final version was installed. Original backups were retained.

The updater's exact source-method hash is portable between Python 3.11 and 3.12;
AST is used to locate the method, not as a cross-version binary signature.
The initial Python-version signature mismatch stopped before any file changes.
The new interpreter dependencies were additive: NumPy 2.4.6 and Shapely 2.2.0
were previously absent; no other package was upgraded. They supply the existing
slab polygon checker rather than a new geometry engine.

The full private receipt with local recovery paths is available in the task's
outputs. Recovery can be invoked using the staged updater and the receipt:

```powershell
python scripts/apa_update_strategy_discovery.py --rollback-receipt <receipt.json>
```

It is not necessary to reinstall on this laptop; the update was already applied.
The updater deliberately refuses a modified/already-updated V1 adapter. A new
Python process imports the integrated code. It does not hot-reload or restart
any active Archicad/APA process.

## Focused validation and handoff

[New integration validation](integration/validation.json) covers eight catalog,
selection, dependency, delegation and semantic-hook tests, plus three additive
update preservation/rollback/drift tests. These are glue tests, not repeated
functional tests of native Archicad tools. Fast Downward delegation is checked;
the existing solver is not re-tested functionally in the new suite. The changed
Python files compile. The actual installed process separately confirmed the
wall -> window preview, all 73 official constructors and the previous slab
preview through the preserved local APA wrappers.

Local integration is performed, not merely published. Native calls/writes in
this pass: **0**. BDD House, PLN files, APX binaries, existing user settings and
the original branches were not changed. Archicad 30 is not used.

The remaining work for native acceptance is a bounded integration scenario in
an explicitly authorized Archicad 29 test PLN with current runtime schemas,
model identity, GUID/BREP/attribute/host readback and the original journal/scope
guards. General building-brief decomposition and engineering acceptance remain
outside the evidence of this source-qualified integration.
