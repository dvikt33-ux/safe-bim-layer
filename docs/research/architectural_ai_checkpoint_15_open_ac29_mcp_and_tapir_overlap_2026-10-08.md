# Architectural AI checkpoint 15 — open AC29 MCP stack and Tapir overlap audit

Date: 2026-10-08  
Status: ACTIVE RESEARCH CHECKPOINT  
Target: Archicad 29 first  
Branch: feature/working-archicad-mvp  
Supersedes for execution-layer decisions: checkpoint 14 where contradicted by this file

## Executive change

This pass changes the AC29 execution priority more strongly than checkpoint 14.

The previous hypothesis was:

`HuskyBIM first -> native/Tapir only for residual gaps`.

The new evidence supports a different order:

`Tapir open execution substrate -> open MCP/safety wrapper -> residual native gap -> HuskyBIM comparative benchmark`.

Reason: the Tapir revision already used by this project, commit
`d2dfeec7936dd1dbed4e2412f406b30291959c26`, already contains a much broader
read/write surface than we treated it as having. Several writer cycles we recently
implemented and verified independently overlap with commands that were already present
in that exact upstream revision.

This does not make the native work useless: the cycles proved live AC29 behavior,
read-back assumptions, material behavior and our ability to build native commands.
But they must no longer be treated as evidence that those generic writers need to stay
custom SBIM code.

The core architectural question is therefore no longer "HuskyBIM or our Add-On?".
It is:

1. how much can current Tapir provide directly;
2. which open MCP wrapper gives the best discovery, validation and safety semantics;
3. which exact functions still require our native gap bridge;
4. whether HuskyBIM offers enough additional capability, robustness or UX to justify
   becoming a runtime dependency.

---

## 1. Critical finding — the project already had overlapping Tapir writers

Project history records Tapir commit:

`d2dfeec7936dd1dbed4e2412f406b30291959c26`

Upstream commit:
https://github.com/ENZYME-APD/tapir-archicad-automation/commit/d2dfeec7936dd1dbed4e2412f406b30291959c26

Direct inspection of `archicad-addon/Sources/AddOnMain.cpp` at that commit confirms
the following commands were already registered:

- `CreateWindowsCommand` — 1.4.0
- `CreateDoorsCommand` — 1.4.0
- `CreateOpeningsCommand` — 1.4.0
- `CreateMorphsCommand` — 1.4.0
- `CreateRoofsCommand` — 1.4.0
- `ModifyWindowsCommand` — 1.4.0
- `ModifyDoorsCommand` — 1.4.0
- `ModifyMorphsCommand` — 1.4.0
- `ModifyRoofsCommand` — 1.4.0

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d2dfeec7936dd1dbed4e2412f406b30291959c26/archicad-addon/Sources/AddOnMain.cpp

### Implication for our recent live cycles

The following recent SBIM proof cycles overlap with functionality already present in
our Tapir base:

- hosted Window create;
- generic Roof create;
- Morph create/move;
- generic Roof material/structure assignment;
- several generic create/modify element paths.

Therefore these capabilities should be moved out of the presumed native-gap list until
a benchmark proves that Tapir is insufficient for the exact semantic contract we need.

The value of our proof cycles remains:

- independent live confirmation on the actual AC29 environment;
- exact geometry/material read-back experiments;
- proof that our build and native command path works;
- test fixtures that can now be reused as an apples-to-apples Tapir benchmark;
- discovery of where evaluated result geometry differs from editable source parameters.

---

## 2. Roof overlap is broader than expected

At the exact project Tapir revision `d2dfeec`, `RoofDetails` already exposes:

- `roofClass` — SinglePlane / MultiPlane;
- `structureType` — Basic / Composite;
- `thickness`;
- `level`;
- `zCoordinate`;
- `buildingMaterialId`;
- `compositeId`;
- single-plane `angle` and `pivotLine`;
- multi-plane eaves/levels;
- polygon outline/arcs/holes.

`CreateRoofsCommand` already accepts:

- floor / level;
- thickness;
- polygon geometry;
- single-plane pivot line + angle;
- multi-plane eaves + levels;
- `structureType`;
- `buildingMaterialId`;
- `compositeId`.

`ModifyRoofsCommand` already accepts:

- level;
- thickness;
- eaves and levels;
- `structureType`;
- `buildingMaterialId`;
- `compositeId`;
- polygon replacement.

The current implementation explicitly limits `ModifyRoofs` to multi-plane roofs,
while `CreateRoofs` can create both single- and multi-plane roofs.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d2dfeec7936dd1dbed4e2412f406b30291959c26/archicad-addon/Sources/ExtendedElementCommands.cpp

### Roadmap correction

Our previous "Roof material native writer is blocked" result must not be interpreted as
"AC29 lacks an available roof material writer".

The narrower correct statement is:

> our own experimental native writer did not yet implement the material change, while
> the Tapir revision already in the stack exposes roof Basic/Composite structure and
> building-material/composite writes.

Required next action is a live Tapir read/write/read-back test, not more custom roof
writer implementation.

---

## 3. Morph overlap is also extensive

At `d2dfeec`, Tapir's Morph schema is not a toy box-only API.

`MorphDetails` / `MorphBody` already cover:

- placement transform;
- `buildingMaterialId`;
- default `surfaceId`;
- arbitrary indexed vertex geometry;
- face polygons;
- per-face Surface overrides;
- body round-trip shape shared by Get/Create/Modify;
- display / floor-plan / visibility parameters;
- texture projection fields.

`CreateMorphs` supports either a simple box or a supplied arbitrary body.

`ModifyMorphs` supports:

- translation;
- Z rotation;
- whole-body replacement;
- building material;
- default surface;
- transform axes;
- multiple visibility / representation fields.

Tapir also documents and works around an Archicad SDK quirk where a Morph default
surface can be discarded by the initial create and therefore requires a follow-up
change.

Schema:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d2dfeec7936dd1dbed4e2412f406b30291959c26/archicad-addon/Sources/RFIX/Images/CommonSchemaDefinitions.json

Implementation:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d2dfeec7936dd1dbed4e2412f406b30291959c26/archicad-addon/Sources/ExtendedElementCommands.cpp

### Roadmap correction

Remove from active custom writer work unless a gap is proven:

- generic Morph translation;
- generic Morph building-material assignment;
- generic default-surface assignment;
- generic arbitrary Morph body create/replace;
- per-face appearance writing that Tapir already handles correctly on AC29.

Our native Model Dump may still remain valuable for evaluated geometry and provenance;
that is a separate requirement from editable Morph source geometry.

---

## 4. Tapir itself becomes a first-class execution candidate

Upstream:
https://github.com/ENZYME-APD/tapir-archicad-automation

Current release observed during this pass:

- Tapir `1.7.0`
- published 2026-10-04
- AC29 Windows and macOS builds are published
- upstream also added AC30 build support, but AC30 remains outside the active target

The 1.7.0 release also includes continued expansion around IFC, MEP, stories/window
activation and installer/update behavior.

### Decision

`TAKE_AS_PRIMARY_OPEN_EXECUTION_SUBSTRATE_PENDING_LIVE_BENCHMARK`

This is stronger than checkpoint 14.

Tapir is not merely a helper below our Add-On. It is now the first thing to test for
every generic Archicad operation before adding another native command.

### 4A. Second critical finding — Tapir already has element events and single-undo batches

Inspection of the exact project Tapir revision `d2dfeec` found another overlap that
was previously assigned to the native gap.

`AddElementNotificationClient` is already registered (since Tapir 1.2.8) and accepts
a callback host/port plus switches for new-element, modification/deletion and Teamwork
reservation-change notifications.

Its native implementation uses Archicad observer APIs including
`ACAPI_Element_CatchNewElement`, `ACAPI_Element_AttachObserver`,
`ACAPI_Element_InstallElementObserver` and reservation-change callbacks.

The callback payload distinguishes new, changed, deleted, reserved and released
elements and carries element GUID + type, with old/copied parent GUID where Archicad
supplies one. Undo/redo create/modify/delete notifications are also mapped into those
event classes.

Source at the project revision:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d2dfeec7936dd1dbed4e2412f406b30291959c26/archicad-addon/Sources/NotificationCommands.cpp

This means the **native observer itself is not currently a justified custom gap**.
What may still be custom is our higher-level revision accumulator, causal invalidation,
event persistence and stale-plan rejection.

The same audit found that Tapir's generic extended create/modify helpers already wrap a
whole command call in `ACAPI_CallUndoableCommand`. A multi-element command therefore
already has a single Archicad undo scope.

Important distinction:

- this gives one undoable command for the successful mutations inside that call;
- it does **not** prove all-or-none atomic rollback, because item-level failures are
  collected while successful sibling mutations can remain committed;
- it does not make a multi-command AI plan atomic or idempotent.

So the remaining transaction gap is narrower:

`cross-command plan identity + stale guard + idempotency + optional all-or-none policy`

—not "invent batch undo for every writer".

### 4B. Deep-geometry boundary — Model Dump still has a real reason to exist

I then searched Tapir's command/source surface for a general command equivalent to our
Model Dump:

`element -> evaluated 3D bodies -> vertices -> polygons/faces -> material/surface`

No general command exposing that full evaluated 3D topology was found in the inspected
Tapir revision/current source surface.

Tapir does call `ACAPI_ModelAccess_Get3DInfo` and
`ACAPI_ModelAccess_GetComponent` internally, but in the generic element path this is
used to calculate robust 3D bounding boxes; the body topology itself is not returned to
the caller.

That preserves a concrete native gap for our Model Dump:

- evaluated 3D bodies for arbitrary model elements;
- global/world vertices;
- faces/polygons;
- face -> material/surface provenance;
- GUID -> body association;
- cross-type geometry in one normalized payload.

This is narrower than "native geometry bridge" in general, because Tapir already
returns rich editable/type-specific geometry for many types and a complete Morph body.

### 4C. Tapir already exposes evaluated floor-plan cut polygons

At the same exact `d2dfeec` revision, `GetDetailsOfElements` can return
`floorPlanPolygons`.

The implementation regenerates Archicad drawing primitives and captures cut-fill
polygons. Its schema explicitly describes them as:

- polygons **as drawn on the floor plan**;
- wall joins already resolved by Archicad;
- available at that revision for cut-fill elements such as Walls, Columns and Beams.

This is important for the older Q4 geometry work. We should test these polygons before
using 3D body decomposition for wall connectivity/fragmentation.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d2dfeec7936dd1dbed4e2412f406b30291959c26/archicad-addon/Sources/ElementCommands.cpp

Practical split after this finding:

- **2D resolved wall plan geometry** -> try Tapir `floorPlanPolygons` first;
- **generic evaluated 3D topology/material provenance** -> keep our Model Dump until an
  equivalent upstream command is proven.

---

## 5. New candidate — alesdev88/Archicad-MCP

Repository:
https://github.com/alesdev88/Archicad-MCP

Current release observed: `v0.7.1` (2026-09-30).

This is materially more important than a generic MCP wrapper because it adds a safety
and QA layer around Archicad 29.

### Useful implemented layers

- Archicad 29-specific server;
- curated read/write/create tools;
- gateway to official JSON API + Tapir commands;
- YAML office QA rules;
- criteria-like element search;
- classifications/properties/attributes;
- issues + BCF;
- publishing;
- schedule XML tooling;
- optional script + changeset workflow;
- explicit coverage handling when official JSON API sees only a subset of the plan.

### Safety semantics worth reusing

- writes are dry-run by default;
- destructive movement/deletion requires explicit confirmation;
- script execution is disabled by default;
- `run_script` can plan a changeset;
- `apply_changeset(confirm=true)` applies the planned writes;
- project identity is checked before applying a stored changeset;
- changeset is one-shot and expires;
- write/read-back mismatch is reported.

### Important limitations

This is NOT a true atomic transaction engine.

If an apply sequence partially succeeds and a later whole request fails, already
applied changes stay applied.

Optional scripts are ordinary unsandboxed Python running as the OS user.

The project also documents a severe AC29 risk:
`GetPropertyValuesOfElements` has crashed Archicad even for a single
property/element combination. Their element ceiling limits blast radius; it does not
make the API safe.

They also measured an important coverage difference in a real plan:

- official `API.GetAllElements`: model elements only;
- Tapir `GetAllElements`: much broader whole-plan enumeration including many
  documentation/2D entities.

### Decision

`WRAP_OR_USE_METHOD_FOR_SAFETY_QA`

Before we write our own generic preflight/changeset UX, reproduce this server's safety
contract and determine whether it can simply become the outer safety wrapper around
Tapir.

Do not adopt its unsandboxed script mode as the SBIM production transaction path.

---

## 6. New candidate — SzamosiMate/tapir-archicad-MCP

Repository:
https://github.com/SzamosiMate/tapir-archicad-MCP

Current release observed: `v0.6.3` (2026-10-03).

The project exposes official Archicad JSON + Tapir through generated, validated MCP
tools and currently advertises 191+ commands.

### Strong reusable layer

- command models generated from API schemas;
- Pydantic runtime validation;
- progressive discovery:
  - list commands;
  - fetch exact schema;
  - call command;
- avoids putting all tool schemas into model context;
- multi-instance control;
- stdio / SSE / streamable HTTP;
- bearer authentication for network transports;
- long-running job handles;
- generated command surface already includes broad element create/modify families.

The generated source visibly covers creation/modification for substantially more
element types than the narrow Archi Automate AC29 writer.

### Limitations

- cancellation does not stop an Archicad command that has already started;
- retry after a lost response can duplicate a mutating operation;
- job state is lost on server restart;
- this is command transport/validation, not atomic transaction management.

### Decision

`TAKE_AS_MCP_SURFACE_CANDIDATE`

This may remove the need to write our own generic MCP command registry, schema
discovery and validation layer.

---

## 7. Boti-Ormandi/archicad-mcp — useful pattern, not production transaction path

Repository:
https://github.com/Boti-Ormandi/archicad-mcp

The design deliberately keeps the MCP surface very small:

- `list_instances`;
- `get_docs`;
- `get_properties`;
- `execute_script`.

The model discovers exact JSON/Tapir schemas, then composes a multi-step Python
workflow locally.

This is an elegant answer to tool-count/context explosion.

However, `execute_script` is unsandboxed Python running as the user's OS account.

### Decision

`USE_METHOD_NOT_PRODUCTION_RUNTIME`

Reuse:

- compact progressive command discovery;
- exact-schema lookup;
- local multi-step execution concept.

Do not use free-form OS-level Python as the trusted production mutation path.

---

## 8. chronista-club/archicad-mcp — native architecture benchmark only

Repository:
https://github.com/chronista-club/archicad-mcp

Architecture:

`MCP server -> local socket -> C++ Archicad Add-On -> Archicad API`

This is interesting because it directly resembles the architecture we independently
built toward.

But the current public tool surface is tiny compared with Tapir/Husky/open wrappers.

### Decision

`BENCHMARK_ONLY`

Use it as confirmation that a thin local socket/native bridge is a sensible pattern,
not as the execution dependency.

---

## 9. HuskyBIM is repositioned, not discarded

Official HuskyBIM pages currently still conflict:

- product/platform/FAQ pages: 733 Archicad 29 tools;
- another current products/learn page: 687 operations/tools.

It remains a serious candidate and claims broad coverage over elements, attributes,
classifications, layouts/drawings, issues, stories and properties.

But after discovering the open Tapir stack, "Husky first by default" is no longer
justified.

### Revised decision

`BENCHMARK_PARALLEL_NOT_PRIMARY_BY_DEFAULT`

HuskyBIM must now beat or materially extend the open stack on one or more of:

- missing API coverage;
- reliability;
- performance;
- better write semantics;
- documentation production;
- easier AI-client integration;
- safer mutations;
- lower maintenance;
- capabilities absent from Tapir.

If it does, wrap it behind the same execution capability interface.

If it does not, avoid adding a closed runtime dependency just to duplicate open
functionality.

---

## 10. Native Gap Bridge shrinks again

### Remove from presumed native ownership now

Unless live tests disprove upstream behavior:

- generic Window create/modify;
- generic Door create/modify;
- generic Opening create;
- generic Roof create;
- generic Roof Basic/Composite material assignment;
- generic multi-plane Roof modify;
- generic Morph create;
- generic Morph translation;
- generic Morph material/default-surface writes;
- arbitrary Morph body create/replace;
- generic native element-change observer, if Tapir notification reliability is confirmed live;
- generic per-command single-undo wrapper;
- generic MCP schema/tool registry.

### Keep custom only where evidence still supports it

1. **Revision accumulator / causal invalidation over upstream events**
   - consume Tapir element notifications rather than reimplementing the native observer;
   - turn event batches into our canonical project revision;
   - persist enough event identity to invalidate stale plans.

2. **Project revision / stale-operation guard**
   - reject operations planned against obsolete state;
   - bind planned changes to the canonical project state.

3. **Evaluated/deep result geometry gaps**
   - body/face/vertex data where Tapir does not expose equivalent evaluated result;
   - evaluated geometry rather than only editable parameter geometry.

4. **Material provenance gaps**
   - exact face -> material/surface provenance where generic APIs do not supply enough
     information.

5. **Cross-command transaction policy**
   - idempotency and operation identity across retries;
   - optional all-or-none compensation/rollback if required;
   - do not reimplement per-command single-undo scopes that Tapir already supplies.

6. **Exact read-back verifier**
   - only for data not already robustly returned by Tapir/wrapper.

7. **Performance instrumentation**
   - timing and regression evidence.

This should be proved with a capability diff, not assumed.

---

## 11. New benchmark order

### TEST-TAPIR-01 — first, before Husky

Use the existing live-cycle fixtures against the Tapir revision already associated
with the project.

Test:

- Wall create/modify;
- hosted Window;
- hosted Door;
- Opening;
- Slab;
- Roof create;
- Roof building material / composite;
- Roof modify;
- Morph box;
- Morph arbitrary body;
- Morph default surface;
- Morph per-face surface;
- Morph translation;
- stories;
- properties/classifications;
- layouts/drawings where supported;
- 100-element homogeneous batch;
- exact read-back.

Outcome:
`native_gap = required_semantics - verified_tapir_semantics`.

### TEST-TAPIR-02 — current upstream

Repeat only compatibility-critical tests on Tapir 1.7.0 in a scratch copy.

Do not upgrade the production/test baseline blindly; compare behavior first.

### TEST-MCP-01 — wrapper comparison

Compare:

- SzamosiMate generated MCP surface;
- alesdev safety/QA wrapper;
- Boti compact discovery pattern.

Dimensions:

- tool discovery;
- schema fidelity;
- prompt/context cost;
- dry run;
- confirmation;
- read-back;
- project identity guard;
- retry/idempotency;
- HTTP authentication;
- long-running operations;
- failure reporting.

### Q4-TAPIR-01

Use `GetDetailsOfElements(fields=["type","floorIndex","floorPlanPolygons"])` on the
existing wall audit sample and compare against our Q4 wall-connectivity inputs.

Verify:

- joined-wall cut polygons;
- T/L/X junctions;
- curved walls where present;
- walls outside the active story/window;
- hidden-layer behavior;
- batch runtime;
- whether the polygons are sufficient for `WALL_FRAGMENTATION` and
  `WALL_CONNECTIVITY`.

Do not route Q4 through the 104 MB Model Dump if this smaller evaluated 2D representation
is sufficient.

### EVENT-01

Register Tapir's `AddElementNotificationClient` against a local callback and verify on
AC29:

- new / changed / deleted;
- property/classification change;
- undo/redo;
- copy parent/old GUID semantics;
- Teamwork reserve/release where available;
- event ordering and grouping around a Tapir batch;
- missed-event behavior across callback restart.

If this passes, remove the native event-observer command from active custom scope.

### TRANSACTION-01

Deliberately force failure mid-batch and verify:

- partial apply;
- undo behavior;
- retry duplication;
- stale-project rejection;
- active-window/database behavior;
- crash recovery.

This is likely where custom SBIM semantics remain genuinely valuable.

### BIM-EXEC-01 — Husky comparative benchmark

Only after the open stack is measured.

Compare Husky against the now-known open baseline, not against an artificially weak
native CRUD layer.

---

## 12. Revised AC29 ownership hypothesis

| Layer | Current candidate | Custom SBIM |
|---|---|---|
| Broad AC29 execution | Tapir | only proven gaps |
| MCP command exposure | SzamosiMate/tapir-archicad-MCP candidate | likely no generic registry |
| Safety / QA / dry-run UX | alesdev88/Archicad-MCP candidate | project-specific policy only |
| Alternative broad closed executor | HuskyBIM | adapter only if it wins benchmark |
| Resolved floor-plan cut geometry | Tapir floorPlanPolygons | likely no custom layer for Walls/Columns/Beams |
| Deep evaluated 3D topology | native Model Dump only where Tapir has no equivalent | residual but currently justified |
| Element events | Tapir notification client | custom consumer/revision logic only |
| Project revision/invalidation | canonical kernel over event stream | yes |
| Transaction policy | Tapir single-undo command + wrapper safety | cross-command semantics only if required |
| Russian Rule IR | SBIM | yes |
| Healing objective/extensions | SBIM over Design Healing method | yes |
| Cross-host AEC orchestration | Archi Automate optional | no generic gateway |
| IFC parsing/IDS | IfcOpenShell / existing tools | no generic parser/validator |

---

## 13. Roadmap deletions from this pass

Add to STOP / DO NOT IMPLEMENT GENERICALLY:

- native generic Roof writer;
- native generic Roof material writer;
- native generic Morph writer;
- native Morph movement writer;
- native generic Window/Door writer;
- native generic Opening writer;
- native generic element observer if EVENT-01 passes;
- custom per-command single-undo wrappers;
- custom MCP registry over Tapir;
- custom Tapir schema-discovery layer.

PAUSE until benchmark:

- large custom execution adapter;
- custom preflight/changeset UI;
- broad custom read-back layer.

The adapter may collapse into a thin capability map because the open wrappers already
standardize much of the transport/schema surface.

---

## 14. Main lesson

The strongest finding is not that "another MCP exists".

It is that the **execution functionality we thought was still ours was already present
inside the exact Tapir revision we were building on**.

Therefore the operating rule for the rest of AC29 work becomes:

> Before implementing any native Archicad read/write command, search the exact current
> Tapir command/schema/source first, then search the open MCP wrappers, then benchmark,
> and only then create a custom gap command.

That rule should be treated as mandatory for the remaining MVP.

---

## Sources inspected in this pass

- Tapir Archicad automation:
  https://github.com/ENZYME-APD/tapir-archicad-automation
- Exact project Tapir commit:
  https://github.com/ENZYME-APD/tapir-archicad-automation/commit/d2dfeec7936dd1dbed4e2412f406b30291959c26
- alesdev88/Archicad-MCP:
  https://github.com/alesdev88/Archicad-MCP
- SzamosiMate/tapir-archicad-MCP:
  https://github.com/SzamosiMate/tapir-archicad-MCP
- Boti-Ormandi/archicad-mcp:
  https://github.com/Boti-Ormandi/archicad-mcp
- chronista-club/archicad-mcp:
  https://github.com/chronista-club/archicad-mcp
- HuskyBIM Archicad:
  https://mcp.huskybim.com/products/archicad
  https://huskybim.com/products
