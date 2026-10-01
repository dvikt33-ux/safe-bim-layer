# Automated library-part compilation for Safe BIM

## Why manual `Save Selection As` should disappear

The current pilot used a manual Archicad step only because Tapir 1.5.9 does not expose a JSON command equivalent to `Save Selection As -> Window/Object` or to direct Library Part creation from generated geometry. This is a transport/API exposure gap, not a fundamental Archicad limitation.

Archicad's native C++ API can create and save library parts programmatically. Relevant API families include:

- `ACAPI_LibPart_Create`
- `ACAPI_LibPart_AddSection`
- `ACAPI_LibPart_NewSection`
- `ACAPI_LibPart_WriteSection`
- `ACAPI_LibPart_EndSection`
- `ACAPI_LibPart_Save`
- `ACAPI_LibPart_Register`
- `ACAPI_Automate(APIDo_SaveID, ...)`
- `API_SavePars_Object`
- `APIFType_ObjectFile`, `APIFType_DoorFile`, `APIFType_WindowFile`

Therefore Safe BIM should automate library creation rather than asking the user to save each master manually.

## Preferred architecture

### Option A — deterministic Library Part compiler (preferred)

Generate the library part from a semantic component definition instead of depending on the current Archicad UI/view/selection.

Pipeline:

```text
ComponentDefinition
  -> geometry compiler
  -> GDL / library-part sections
  -> ACAPI_LibPart_Create
  -> AddSection / WriteSection
  -> ACAPI_LibPart_Save
  -> register/reload
  -> create test instance
  -> QA read-back
  -> CreateFavoritesFromElements
  -> component registry READY
```

Advantages:

- no manual UI steps;
- deterministic and repeatable;
- independent from current 3D selection/window;
- supports nested reusable components/macros;
- easy to version in Git;
- suitable for automatic rebuilds and CI-like QA;
- can preserve semantic material-role parameters.

### Option B — automate Archicad's save-as-object/window workflow

Use `ACAPI_Automate(APIDo_SaveID, ...)` with `API_SavePars_Object` and `APIFType_WindowFile`/`DoorFile`/`ObjectFile` to save current 3D content as a library part.

This is closer to `Save Selection As`, but depends more heavily on the current active 3D window and view contents. It is useful as a transitional implementation or for converting manually/model-generated masters, but it is less deterministic than Option A.

## Safe BIM command surface to add

Proposed add-on commands:

### `CompileLibraryPart`

Input:

```json
{
  "name": "SB_Gothic_Lancet_Large_v01",
  "kind": "Window",
  "componentId": "window.gothic.lancet.large",
  "version": 1,
  "parameters": {...},
  "geometry": {...},
  "materialRoles": {...},
  "wallhole": {...},
  "dependencies": [...]
}
```

Output:

```json
{
  "libraryPartName": "SB_Gothic_Lancet_Large_v01",
  "libraryPartIndex": 1234,
  "unId": "...",
  "contentHash": "...",
  "status": "CREATED"
}
```

### `EnsureLibraryPart`

Idempotent command. If the same `componentId + version + contentHash` already exists, reuse it. Otherwise compile and register a new version.

### `CreateFavoriteFromLibraryPartInstance`

Place one verified instance, then call Tapir's existing `CreateFavoritesFromElements` so subsequent placement can use `favoriteName`.

### `GetLibraryComponentRegistry`

Returns known Safe BIM library parts, hashes, dependencies, versions, QA state and favorite names.

## Nested components

Safe BIM should support dependency graphs rather than flat objects.

Example:

```text
window.gothic.lancet.large
  -> macro.archivolt.gothic.a
  -> macro.tracery.y.a
  -> macro.sill.stone.a
  -> macro.glazing.lancet.a
  -> wallhole.lancet.large
```

Compilation must be topological: atomic dependencies first, assembly last.

## Material rule

Library parts inherit the project's persistent material-role map. Parameters should use semantic roles rather than hard-coded material names:

```text
STRUCTURAL_STONE
TRIM_STONE
DECORATIVE_STONE
ROOF
METAL
GLAZING
FLOOR
```

Same role => same material/surface. Different requested render role => different attribute where available.

## QA loop for every compiled component

A component is not `READY` immediately after compilation.

1. Compile/register.
2. Place exactly one specimen.
3. Verify element type and library-part identity.
4. For hosted elements, verify host relation and wallhole/reveal behavior.
5. Inspect/read back size, position, orientation and parameters.
6. Verify material-role assignments.
7. Check duplicate/ghost creation.
8. Create Favorite from verified specimen.
9. Place second specimen using Favorite.
10. Compare first and second specimens.
11. Mark `READY` only after equivalence passes.

States:

```text
MISSING -> COMPILING -> COMPILED -> TESTING -> READY
                                   -> FAILED
```

## Acceleration strategy

The biggest speed gain comes from never compiling the same component twice.

Cache key:

```text
hash(
  component semantic definition,
  geometry version,
  material-role schema version,
  dependency hashes,
  Archicad major version
)
```

When a building requests 300 identical cornice modules or 80 windows, Safe BIM resolves one library part and places instances only.

## Immediate implementation target

First end-to-end automatic component:

`SB_Gothic_Lancet_Large_v01`

The user should eventually issue one command and Safe BIM should:

```text
generate master definition
-> compile Window library part
-> register it
-> place test window
-> audit wallhole/interior/exterior/section
-> create Favorite
-> replace prototype V3 window assemblies
-> place all tower windows as real Window instances
-> remove old prototype geometry
```

No manual `Ctrl+T`, `Save Selection As`, Embedded Library selection, or Favorite creation should remain in the final workflow.
