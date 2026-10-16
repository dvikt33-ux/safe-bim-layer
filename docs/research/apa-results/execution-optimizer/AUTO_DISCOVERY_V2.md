# APA Automatic Tool Discovery V2 — partial implementation delivered

Base: PR #130, `331a8d4f4ca96e031a562406923ac91a28fd4b63`.
This change is stacked on that exact V1 commit. It does not install a new APA
core on the laptop. V1's installed files and backups remain in place.

V2 automatically discovers applicable reviewed commands from the **existing
DynamicCommands catalog**, builds a complete homogeneous batch from prepared
typed BIM data, validates it with the existing BIM Graph and prepares the
original APA native task. Execution remains:

`prepare_auto_optimized_native_task -> prepare_native_task -> run_auto_optimized_native_task -> run_native_task -> DynamicCommands.run_workflow -> DynamicCommands.execute -> SceneWriter`.

The added command names/array slots are typed recipe bindings, not copied
schemas, another command catalog, a second executor or another transport.

## Confirmed inventory

The [inventory report](v2/contract-inventory.json) records paths, content hashes,
command contract hashes, reviewed-effect state and snapshot availability:

| Source inspected | Commands | What this establishes |
| --- | ---: | --- |
| Pinned Tapir 1.5.10 modified export | 262 | Existing input/return schemas, not current runtime registration |
| Same export + existing functional SDK/local module attachment | 291 | Code-owned contract attachment and source-hash checks |
| Existing extended runtime snapshot | 348 | Includes real native Grid/ExactStair contracts; historic snapshot only |
| Installed official Python JSON API package 29.3000 | 73 | Typed constructor inspection without creating a connection or dispatching a command |

The installed official JSON API exposes attribute/layout/view creation and
property/classification operations, but no general Wall/Slab create method.
Those operations therefore use the already integrated Tapir contracts. Native
Grid and ExactStair C++ implementations exist in
`archicad-addon/Sources/NativeGridCommands.cpp` and `NativeStairCommands.cpp`.
Their presence in the extended snapshot is not live acceptance, and the default
pinned-export router does not attach these commands automatically.

## Operation acceptance matrix

`DONE` below means the indicated **source/offline layer** is implemented and
checked. Every native column is `NOT_RUN`; none of these rows claims LIVE_PASS.
Overall V2 remains **PARTIAL** until native acceptance and remaining adapters.

| Operation | Command discovery / schema | Strategy preparation | Original execution route | Offline evidence | Native verification | Overall |
| --- | --- | --- | --- | --- | --- | --- |
| Wall batch create | DONE: CreateWalls | DONE: explicit segment, story elevation/offset, dimensions, structure/material, reference line | DONE: original preview and authorized runner binding | DONE: pinned schema, nonzero story, bad Z rejection | NOT_RUN | PARTIAL |
| Wall copy | DONE: MoveElements(copy=true) | DONE: same family/story; complete empty dependent GUID inventory required | DONE: original route | DONE: copy vs create candidates; children block copy | NOT_RUN | PARTIAL |
| Wall modify | DONE: ModifyWalls | DONE: unique exact GUID, baseline signature, empty dependent inventory; conflicting top rules rejected | DONE: original route | DONE: real schema and baseline mismatch rejection | NOT_RUN | PARTIAL |
| Slab batch create | DONE: CreateSlabs | DONE: explicit plane/thickness/story/outline/holes; qualified Favorite required for attributes | DONE: original route | DONE: schema, Favorite failure, self-intersection rejection | NOT_RUN | PARTIAL |
| Slab copy | DONE: MoveElements(copy=true) | DONE: same family/story, no dependent children | DONE: original route | DONE: copy vs create candidates | NOT_RUN | PARTIAL |
| Slab outline/attribute modify | DONE: ModifySlabs | DONE: exact baseline; complete outline requires explicit holes AND arcs; existing polygon validator reused | DONE: original route | DONE: omitted holes rejection, valid explicit replacement | NOT_RUN | PARTIAL |
| Column/Beam create and copy | DONE: existing V1 commands | DONE: V1 recipes preserved; Beam creation still limited to story zero | DONE: original route | DONE: existing V1/copy/optimizer regressions | NOT_RUN in this pass | PARTIAL |
| Window/Door batch create | DONE: CreateWindows/CreateDoors | DONE: verified existing straight Wall, exact owner GUID/story/base, placement, dimensions, handedness and qualified library/Favorite; fit and overlap checks | DONE: original route | DONE: pinned schemas, two-item batches, wrong host, collision and size rejection | NOT_RUN | PARTIAL |
| General Opening | DONE: CreateOpenings schema found | BLOCKED: no V2 semantic adapter; owner/base/size schema does not establish orientation, cut extent and complete host semantics | Not emitted | Inventory only | NOT_RUN | BLOCKED |
| Editable native Grid | DONE in extended snapshot and C++ source | BLOCKED: not attached by default router; native defaults/library mapping, reviewed policy and runtime identity must be qualified before discovery adapter | Existing `archicad_native_spatial_tools` retained | Inventory only | NOT_RUN | BLOCKED |
| Roof | DONE: CreateRoofs/ModifyRoofs schemas | BLOCKED: no V2 roof geometry/attribute adapter | Not emitted | Inventory only | NOT_RUN | BLOCKED |
| Morph | DONE: native contracts exist | BLOCKED: no V2 adapter; MORPH LAST RESORT remains binding | Not emitted | Inventory only | NOT_RUN | BLOCKED |
| Stair/ExactStair | DONE: source/snapshot contracts exist | BLOCKED: no V2 adapter and current native identity/rules qualification | Existing exact-stair tools retained | Inventory only | NOT_RUN | BLOCKED |

## Input and qualification

V1 input `apa-native-auto/1` remains supported for Column/Beam/Object.
New types require `apa-native-auto/2`; the top-level fields stay
`schemaVersion`, `request`, `existing`, `targets`, `benchmarks`.

Each V2 target retains `type`, `familySignature`, `storyIndex`, absolute `anchor`
and `sourceRef`. It additionally carries `sourceVerification` with status
`SOURCE_VERIFIED`, an evidence reference and `dataHash=source_data_hash(target)`.
That hash covers all prepared target fields, including geometry, story, host,
library and material qualification. A hash establishes consistency of supplied
data; it does not independently prove the evidence is true or re-read Archicad.
The discovery report states this qualification boundary explicitly.

Creation uses exact `nativeCreateData`. Wall `zCoordinate` is story-relative
when `floorIndex` is supplied; `storyElevation + zCoordinate` must equal the
absolute anchor. Slab `level` is checked against its absolute anchor. The pinned
CreateSlabs schema has **no buildingMaterialId or structureType input**: V2
requires a named Favorite with a qualified settings hash and verified
attributes. It does not inject an unsupported material parameter or assume the
current tool defaults are correct.

Straight slab polygons reuse `archicad_building_shell.source_floor_polygon`
and its existing Shapely dependency (`scripts/requirements-geometry.txt`).
Self crossings, invalid holes and degeneracy fail; curved slab edges are
blocked until an analytic qualifier is connected. Source geometry is not
silently normalized or replaced by an approximation.

Modification targets set `operation: MODIFY`, `nativeModifyData` and
`baselineSignatureSHA256`. Their GUID must identify a supplied, independently
read-back existing source with the same baseline signature and home story.
Walls/slabs with dependent children are excluded from generic copy/edit.
Hosted Window/Door reuse requires the exact owner GUID as well as family and
anchor; hosted elements are never independently translated as copy candidates.

Window/Door targets include `hostContext` with complete existing-opening spans,
straight host geometry and verified identity/story; and `libraryQualification`
bound to the exact library part/Favorite and settings hash. Existing BIM Graph
host-fit validation is reused. V2 also rejects overlaps within the requested
batch and with supplied existing host openings. Clearance is conservatively
checked along the wall span; this is not a full 3D collision proof.

One preview contains one complete homogeneous native batch (1–200 targets).
Mixed types, mixed create/edit intent, future host result references and
incomplete strategies fail before execution. Automatic heterogeneous task
decomposition and wall-create-then-window-create are not implemented here.

## Costs and execution boundaries

A sole feasible strategy is prepared with
`SOLE_FEASIBLE_TYPED_OPTION_NOT_COST_OPTIMIZATION` and `calibrationStatus:
UNCALIBRATED` when no measurement exists. Competing unmeasured candidates return
`COST_COMPARISON_BLOCKED_UNCALIBRATED_ALTERNATIVES` and no executable preview.
Comparable measured candidates still go through the existing Fast Downward
selector. V2 measurement records require exact batch size, command contract
hash, `measurementKind: NATIVE_END_TO_END`, evidence reference and the exact
`benchmarkWorkloadHash` emitted by discovery (existing sources + targets).
The caller must supply real evidence for the complete preflight/provider/
independent readback cycle. Test costs are explicitly synthetic fixtures and
provide no production speed claim. No production benchmarks were collected.

Discovery grants no write permission. The existing runner still requires every
operation's explicit scope and callbacks, exact project/model identity, saved
file hash, complete GUID inventory, retained BREP checks, provider/runtime
identity and independent result verification. Settings/library hashes and the
host/baseline context must be rechecked in the operation-specific preflight;
the discovery source declaration is insufficient for a write. Readback must
verify created/modified GUIDs, native type, story, BREP, attributes and hosts.
Ambiguous/partial outcomes retain the existing UNKNOWN/no-replay behavior.

## Reproduce an offline preview

The committed examples contain **synthetic test geometry**, test GUIDs and
offline-only policy evidence. They are not construction data or authorization.
From the repository root, with the existing JSON Schema and geometry
dependencies available:

```powershell
python scripts/archicad_strategy_discovery.py `
  --schema schemas/tapir-live-1.5.10/tapir-scene-live.json `
  --reviewed-policies examples/accelerator/auto-discovery-v2/offline-reviewed-policies.json `
  --intent examples/accelerator/auto-discovery-v2/walls.json
```

Use `slab.json` or `windows.json` for the other examples. The CLI only prepares
a preview; it has no native run option. Reviewed policies are bound to the
actual loaded contract hash. The checked-in policies must not be treated as a
review of the laptop's current installed runtime.

Programmatic integration uses the same existing router and explicit scopes:

```python
preview = APA.prepare_auto_optimized_native_task(router, prepared_intent)
# Only the existing separately authorized execution context may do this:
result = APA.run_auto_optimized_native_task(
    router, api, preview, writer, exact_step_scopes, checkpoint)
```

The laptop's original V1 installer remains a first-install additive installer;
it intentionally refuses an existing installation. This PR does not run it or
replace the recovered laptop core. V2 deployment must apply the reviewed
discovery/copy-family changes to that preserved installation and retain its
existing wrappers, rather than copy the repository core over it.

## Validation and BDD handoff

See [focused validation](v2/validation.json), the retained
[initial environment result](v2/validation-initial-environment.json),
[CLI smoke evidence](v2/cli-smoke.json) and committed preview JSON files.
The local build check compiles the changed Python modules. No C++ was changed;
an APX build/load is not claimed. Fast Downward uses its installed isolated
environment. Windows sandbox TEMP failures were investigated with a separate
workspace TEMP; final results distinguish that retry from the initial run.

No Archicad process was available during this pass. Native calls/writes: **0**.
Model GUID/BREP/attribute acceptance and save/reopen acceptance: **NOT_RUN**.
No installed-runtime, production-performance or engineering PASS is claimed.

Before returning to BDD construction, finish the adapter backlog above, deploy
the reviewed V2 delta additively, and validate against a specifically authorized
Archicad 29 test PLN: current runtime/schema and identity, baseline, one bounded
operation at a time, independent GUID/type/geometry/material/host readback and
save/reopen where required. Then collect comparable full-cycle timings. BDD
requires its own prepared geometry, source and library/material qualifications,
host/story mappings and explicit model-write scope. The building was not edited
in this pass and is not ready for automatic construction on this evidence.
