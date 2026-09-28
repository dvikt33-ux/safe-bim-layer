# Archicad execution architecture and acceleration audit

Date: 2026-09-28
Scope: Safe BIM execution model for Archicad 29 + Tapir 1.5.9.

This document consolidates the repeated audit/pass cycles focused on performance, database/view context, transaction design, verification, and how to use Plan/Section/Elevation/3D as specialized working environments rather than merely UI windows.

---

# A0 — Initial audit

The current control style tends to overuse UI-like sequences:

```text
open/switch view
-> perform one command
-> read back
-> switch view
-> perform next command
-> rebuild
```

This is correct for human navigation but inefficient for machine execution.

The key Archicad distinction is:

```text
Front Window != Current Database
```

Many API operations are database-dependent but do not require the user-facing window to change.

Target design:

```text
user stays in useful view
Safe BIM temporarily routes operations to the required database
Safe BIM returns to document database
rebuild once
```

---

# Cycle 1 — Context routing

## Pass 1 — execution context

Add one authoritative snapshot:

```text
GetExecutionContext
```

Response should include at least:

- active/front window type and identifier;
- current database identifier/type;
- current story;
- active navigator/view ID if applicable;
- model origin/transformation context where needed;
- project identity/version;
- current 3D state identifiers if applicable.

This removes ambiguity between "what the user sees" and "where an API call will execute".

## Pass 2 — background database execution

Add:

```text
RunInDatabase(databaseId, commands, rebuild=false, restore=true)
```

Desired behavior:

1. capture current database;
2. switch database only;
3. execute one or more operations;
4. optional rebuild once;
5. restore captured database;
6. leave Front Window unchanged unless explicit UI navigation was requested.

This should be the default primitive for background model/document work.

## Pass 3 — lazy database prewarm

Some generated document databases may not be available until Archicad has generated/opened them at least once.

Policy:

```text
try background DB
if unavailable because not generated:
    open/generate once
    restore prior front window
    mark database warm for session
retry background operation
```

Do not repeatedly navigate the UI after a database is warm.

## Pass 4 — context scheduler

Before executing a plan, group operations by context:

```text
FloorPlan DB batch
Section A DB batch
Elevation North DB batch
3D/offscreen verify batch
Layout batch
```

Do not execute in original conversational order if a safe reordering preserves semantics and drastically reduces context switches.

---

# A1 — Audit after context passes

Main finding:

The optimization target is not "make Python faster". The expensive part is often the number of Archicad command scopes, context switches, rebuilds, and repeated derived recalculations.

Therefore Safe BIM requires explicit scheduling and transaction boundaries.

---

# Cycle 2 — Transaction and rebuild strategy

## Pass 5 — preflight before write

Every multi-element operation should perform a complete read-only preflight first:

- project identity;
- capability/version gate;
- referenced GUID existence;
- referenced attributes/materials/profiles/composites;
- layer/library dependencies;
- database availability;
- input geometry validation;
- lifecycle/destructive-operation policy.

Only if all items pass should the write phase begin.

This reduces partial-write risk.

## Pass 6 — one logical command scope

Where the Archicad API allows it, group logically related edits into a single undoable command scope.

Preferred:

```text
BEGIN SAFE TRANSACTION
  create/modify model elements
  create relations/openings/SEO
  create annotations
  perform readback metadata needed inside scope
END SAFE TRANSACTION
REBUILD ONCE
DEEP VERIFY
```

Avoid:

```text
write -> rebuild -> write -> rebuild -> write -> rebuild
```

## Pass 7 — fail-fast batch behavior

Current batch wrappers may loop items independently; a later item can fail after earlier writes already succeeded.

Required high-level behavior:

- validate all payloads first;
- if runtime item N fails, stop immediately;
- evidence must explicitly list committed items;
- do not describe the request as atomic unless true rollback semantics are implemented/proven.

## Pass 8 — explicit rebuild policy

Rebuild is a planned operation, not an automatic reflex after every edit.

Use:

- model edit batch;
- document edit batch;
- one rebuild per affected generated database;
- visible redraw only if the user needs to inspect immediately.

---

# Cycle 3 — Section/Elevation specialization

## Pass 9 — generated representation as semantic geometry

Use `GetSectionElements` to map:

```text
raw generated section element GUID
-> owner model GUID
```

Generated representation can be used for:

- witness geometry;
- visible/cut representation;
- annotation association;
- owner resolution.

Do not treat generated section elements as the authoritative model elements to modify.

## Pass 10 — owner edit from Section/Elevation

Future workflow example:

```text
Front Window = Elevation
user asks: raise window head 200 mm

resolve visible/generated representation
-> owner Window GUID
-> RunInDatabase(FloorPlan/model DB)
-> modify owner Window
-> restore Elevation DB
-> rebuild Elevation once
```

The user's view remains stable.

## Pass 11 — section/elevation dimension presets

Exploit Archicad/Tapir semantic presets instead of manually solving all witness geometry:

- WallCompositeFaces;
- WallSkinBorders;
- SlabCompositeFaces;
- SlabSkinBorders;
- BeamOrColumnRefLineEndPoints;
- BeamOrColumnBoundingBoxCorners;
- DoorWindowWallHoleCorners;
- DoorWindowModelHotspots.

This should be the primary path for automatic vertical documentation.

## Pass 12 — ghost-GUID guard

Historical Tapir issues demonstrate that section/elevation dimension creation can report a GUID even when the element is absent.

Mandatory postcondition:

```text
create -> GUID -> resolve element in expected database -> PASS
```

Returned GUID alone is never enough.

## Pass 13 — generic 2D documentation in document DB

Where supported live, create Text/Line/Polyline/Hatch/Label directly in the target Section/Elevation/Worksheet/Detail database.

Each element type must first pass one live create/readback/delete-free sandbox proof for each relevant database type.

---

# A2 — Audit after Section/Elevation passes

Sections/elevations should not be treated only as output views. They are useful specialized semantic workspaces because Archicad has already solved projection, skins, openings and cut representation.

However:

- model edits go to owner model elements;
- generated elements serve representation/association/documentation;
- document writes require explicit target database proof.

---

# Cycle 4 — 3D verification without user-visible navigation

## Pass 14 — verification hierarchy

Use cheapest sufficient proof first:

```text
1. identity / type / property readback
2. AABB preflight
3. Quantity-based verification
4. ModelAccess evaluated geometry
5. visible 3D human review
```

AABB proves only possible overlap, never evaluated boolean intersection.

## Pass 15 — Quantity verifier

Add a wrapper that can retrieve appropriate evaluated quantities for supported element types:

- volume;
- area/surface;
- length where relevant;
- Morph face/edge statistics;
- other element-specific quantities.

Use it for fast before/after verification.

Example SEO test:

```text
wall volume before
-> create associative subtraction
-> wall volume after
```

A relation plus expected quantity change is stronger evidence than a relation alone.

## Pass 16 — ModelAccess verifier

Add:

```text
EvaluateElements3D([GUID...], options)
```

Potential response:

- bodies;
- vertices/polygons;
- materials/surfaces;
- evaluated bounds;
- component relationships;
- connection polygons;
- hashes/canonical summaries.

This is the preferred deep verifier for:

- SEO result;
- native Opening result;
- roof/shell geometry;
- complex profile result;
- collisions/junctions;
- Morph booleans.

## Pass 17 — temporary off-screen model/sight

When Archicad requires a generated 3D model context, use a temporary/non-user-visible model/sight for selected GUIDs rather than switching the user's 3D window and generating the whole project.

Benchmark target:

- 1 element;
- 10 elements;
- 100 elements;
- 1000 elements.

## Pass 18 — visible 3D as QA UI

Visible 3D remains valuable for the human.

Add convenience wrappers later:

- `ShowElementsIn3D`
- `ShowAllIn3D`
- 3D filter preset
- camera/projection management
- cut-plane debug view.

But visible 3D should not be the machine's primary truth source.

---

# Cycle 5 — caches and capability negotiation

## Pass 19 — session caches

Cache stable/session-level data:

- project identity;
- stories;
- attribute GUID/name/index maps;
- library list;
- navigator/database mappings;
- font resolution;
- Safe BIM-owned attributes and views;
- capability matrix.

## Pass 20 — event invalidation

Invalidate only the affected caches when Archicad reports relevant changes:

- project change/open/new;
- story change;
- attribute change;
- library reload;
- current window/database change;
- element change where a cached derived result depends on it.

Event handlers should invalidate/queue work, not run expensive operations inside callbacks.

## Pass 21 — runtime capability handshake

Add:

```text
GetCapabilities
```

Include:

- Archicad version/build;
- Tapir/add-on version;
- supported custom wrapper versions;
- known disabled features (`rotationDegreesZ`, Morph body replacement, etc.);
- database/document write support proven live;
- optional feature flags.

Planner should select workflows from capabilities instead of version guesses.

---

# A3 — Predicted high-value acceleration

Highest-value changes, ordered by expected architectural impact:

1. background `RunInDatabase` instead of UI window switching;
2. context scheduler grouping operations by DB;
3. one logical transaction/rebuild per batch;
4. Quantity + ModelAccess verifier instead of repeated visible 3D checks;
5. attribute/story/library/context cache with event invalidation;
6. high-level composite commands that reduce JSON/API round-trips;
7. semantic section/elevation presets for dimensions/documentation.

---

# Cycle 6 — Proposed high-level commands

## `BatchModelTransaction`

Input:

- operations;
- required database;
- destructive-policy declaration;
- verification plan.

Behavior:

- preflight all;
- execute one command scope where possible;
- fail fast;
- rebuild once;
- verify;
- return evidence ledger.

## `CreateAndVerifyAssembly`

For repeated workflows such as:

```text
wall + openings + windows/doors + SEO + dimensions
```

Perform them as one semantic operation rather than a chain of unrelated external calls.

## `RunInDatabase`

Background model/document execution primitive.

## `EvaluateElements3D`

Deep evaluated geometry primitive.

## `GetElementQuantities`

Fast geometry verifier.

## `ResolveSectionOwner`

Raw Section/Elevation representation -> owner BIM element.

## `RebuildDatabases`

Batch rebuild affected generated databases only.

---

# Final audit

The target execution architecture is:

```text
USER REQUEST
     |
PLANNER / POLICY
     |
CAPABILITY RESOLVER
     |
CONTEXT SCHEDULER
     |
PRE-FLIGHT
     |
SAFE TRANSACTION
     |
MODEL / DOCUMENT DATABASE
     |
MINIMAL REBUILD
     |
FAST VERIFY (readback/quantity)
     |
DEEP VERIFY (ModelAccess when required)
     |
EVIDENCE LEDGER
     |
OPTIONAL HUMAN-VISIBLE VIEW
```

The system must distinguish three truths:

```text
BIM/database truth       = native elements/attributes/relations
Evaluated geometry truth = Quantity/ModelAccess
UI/view truth            = representation for human interaction
```

No layer is allowed to substitute for another.

---

# Live benchmark suite still required

When notebook access is restored:

1. compare `ChangeWindow` vs background current-database switch timing;
2. modify a model owner while Section remains the Front Window;
3. verify whether explicit rebuild is required for immediate Section update;
4. create Text/Line/Label in Section and Elevation databases and verify real existence;
5. benchmark Quantity and ModelAccess for 1/10/100/1000 GUIDs;
6. verify SEO-evaluated wall geometry and volume;
7. verify native Opening evaluated geometry;
8. benchmark one high-level transaction vs equivalent individual calls.

After these benchmarks, optimization claims should be based on measured timings rather than expectation.