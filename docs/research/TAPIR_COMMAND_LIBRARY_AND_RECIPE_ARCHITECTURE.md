# Tapir command library and recipe architecture

## Status
Research note for Safe BIM architectural-model-quality v2.

## Key finding
Tapir is not limited to a fixed set of JSON operations. Its Archicad add-on registers commands as C++ classes derived from `API_AddOnCommand` through `CommandBase`, and command groups are registered in `AddOnMain.cpp`. Therefore Safe BIM can extend Tapir with its own high-level commands rather than emitting hundreds of low-level operations from Python.

The upstream repository explicitly documents the extension path: add a command class in `Sources/*Commands.{cpp,hpp}` (or a new command group), implement schemas, and register it in `AddOnMain.cpp` with the version in which it was introduced.

## What this enables
Instead of Python calling:

- CreateWall
- CreateWall
- CreateSlab
- CreateColumn
- CreateBeam
- CreateMorph
- CreateSolidElementLinks
- CreateWindow
- verification calls

Safe BIM can expose a high-level command such as:

```json
{
  "command": "SB_CreateGothicLancetWindowFamily",
  "parameters": {
    "family": "SB_Gothic_Lancet_v01",
    "large": {"width": 1.48, "height": 4.32},
    "narrow": {"width": 0.98, "height": 3.60},
    "materialRoles": {
      "frame": "TRIM_STONE",
      "glass": "GLAZING"
    }
  }
}
```

The add-on can then perform the internal Archicad API operations inside one undoable/high-level command and return one structured receipt.

## Recommended 3-layer command model

### Layer A — primitive Tapir commands
Keep upstream-style element primitives such as `CreateWalls`, `CreateSlabs`, `CreateColumns`, `CreateRoofs`, `CreateMorphs`, `CreateSolidElementLinks`, library and favorite commands.

### Layer B — Safe BIM atomic architectural commands
Add compact domain commands implemented in the add-on, for example:

- `SB_EnsureLibraryPart`
- `SB_CreateWindowFamily`
- `SB_PlaceWindowFamily`
- `SB_CreateCorniceRun`
- `SB_CreateBalustradeRun`
- `SB_CreateGothicTowerTop`
- `SB_CreateTerrainFromContours`
- `SB_ApplyMaterialRoles`
- `SB_ReconcileComponentInstances`

Each command should be deterministic, versioned, resumable and independently verifiable.

### Layer C — recipes
A recipe registry composes Layer-B commands into larger tasks without hard-coding an entire building into one C++ method.

Example:

```yaml
id: gothic_tower_top_v1
version: 1
steps:
  - command: SB_EnsureLibraryPart
    component: window.gothic.lancet.large
  - command: SB_EnsureLibraryPart
    component: cornice.gothic.a
  - command: SB_CreateGothicTowerTop
  - command: SB_ReconcileComponentInstances
  - command: SB_RunArchitecturalQA
```

Recipes should live in the Safe BIM repository, be source-controlled and referred to by stable ID/version. C++ should supply reliable primitives; recipe content should stay data-driven where possible.

## Why this is faster
A large Python program currently pays per-operation costs repeatedly:

1. JSON construction
2. Python-to-HTTP/Tapir transport
3. gateway admission
4. Archicad add-on dispatch
5. undo context
6. read-back
7. Python reconciliation

A higher-level add-on command can execute many related ACAPI operations within one command call while still returning detailed per-substep results. This reduces transport overhead and produces shorter, clearer generated code.

## Safety rule
Do not add one unrestricted generic command such as `ExecuteArbitraryScript`. Prefer a registry of typed, versioned recipes and high-level commands with JSON schemas. This preserves Safe BIM's fail-closed behavior and allows validation before physical writes.

Every high-level command should return:

```json
{
  "status": "PASS | FAIL | UNKNOWN_OUTCOME",
  "recipeId": "...",
  "recipeVersion": 1,
  "created": [{"guid": "...", "role": "..."}],
  "modified": [],
  "links": [],
  "verification": {...},
  "reconciliationToken": "..."
}
```

## Library-first implications
Tapir already exposes useful pieces:

- files can be copied into the Embedded Library and registered with a requested library-part type;
- libraries can be reloaded;
- available library parts can be listed;
- Favorites can be created from existing elements;
- `CreateWindows` can place windows from a Favorite.

The current missing link for a fully automated custom Window pipeline is direct selection of a specific Window library part when creating a Window. Current `CreateWindows` obtains its library part from Window tool defaults or `favoriteName`.

Recommended Tapir extension:

```json
{
  "windowsData": [{
    "ownerWallId": {"guid": "..."},
    "centerOffset": 2.4,
    "sillHeight": 2.0,
    "libraryPartName": "SB_Gothic_Lancet_Large_v01"
  }]
}
```

Implementation should resolve the named Window library part and set the window library-part index before element creation. The same pattern should later be available for Doors and Skylights.

A stronger long-term command is `SB_EnsureLibraryPart`: compile/register a versioned component if missing, verify availability, then make it usable by placement commands.

## Component registry
Store reusable parts in a registry rather than rediscovering them for every building:

```json
{
  "componentId": "window.gothic.lancet.large",
  "version": 1,
  "kind": "Window",
  "libraryPartName": "SB_Gothic_Lancet_Large_v01",
  "favoriteName": "SB_WIN_GOTHIC_LANCET_LARGE_V01",
  "dependencies": [
    "macro.archivolt.gothic.a",
    "macro.tracery.y.a"
  ],
  "materialRoles": ["TRIM_STONE", "GLAZING"],
  "status": "READY"
}
```

Use dependency-ordered compilation: atomic macros first, assemblies second, Favorites third, model instances last.

## Immediate model-repair strategy before the Window-library extension exists
Until direct `libraryPartName` placement is implemented, do not use rectangular Openings plus stone filler Morphs for pointed windows. That creates the rectangular niches seen in the tower test.

For an interim one-script repair:

1. remove the old V3 rectangular Opening and window-detail assemblies;
2. create a pointed solid cutter as one Morph for each window position;
3. use `CreateSolidElementLinks` with `Subtraction` to cut the actual pointed void from the host Wall;
4. move the cutter Morph to a dedicated hidden `SB_SEO_OPERATORS` layer;
5. create a compact frame/glazing assembly with a small number of reusable geometry functions;
6. persist GUIDs and SEO links in state;
7. verify every Wall has exactly one intended SEO operator and no legacy rectangular Opening.

This is geometrically superior to the existing V3 workaround, but remains an interim representation. Once direct library-part Window placement is available, replace it with real hosted Window instances.

## Next implementation milestones

1. Add `libraryPartName` support to `CreateWindows` and `CreateDoors`.
2. Add command-level tests for library-part resolution, missing names, wrong type, and read-back.
3. Implement `SB_EnsureLibraryPart`.
4. Implement component registry with version/fingerprint/dependencies/status.
5. Implement typed recipe registry.
6. Move repeated architecture generation from Python loops to versioned Safe BIM commands/recipes.
7. Keep Python primarily as orchestration, design intent, parameter generation and QA control.
