# Universal Library System — implementation plan

## Immediate objective

Turn the gothic lancet pilot into the first true hosted Window and generalize the mechanism so the same architecture can later support Doors, Skylights, Objects, Macros, Lamps, Profiles, materials and Hotlink Modules.

## Phase A — Tapir hosted-libpart selection

1. Refactor Tapir’s existing Object/Lamp `libraryPartName` resolver into a reusable helper that returns a validated `libInd`.
2. Add optional `libraryPartName` to `CreateWindows.windowsData[]`.
3. Add optional `libraryPartName` to `CreateDoors.doorsData[]`.
4. Apply favorite first, explicit libraryPartName second, then explicit placement/size fields.
5. Validate compatible type/subtype and fail closed on mismatch.
6. Preserve Window/Door marker defaults.
7. Extend read-back tests to require exact `libPart.name`.

## Phase B — universal import wrapper

Implement Python recipe `SB_EnsureLibraryPart` around existing Tapir commands:

- `GetAvailableLibraryParts`
- `AddFilesToEmbeddedLibrary`
- `ReloadLibraries`

The recipe takes `componentId`, `version`, `type`, `inputPath`, `outputPath`, `libraryPartName`, and `fingerprint`, then returns `REUSE | CREATED | UPDATED` plus verification data.

## Phase C — component router

Implement a Safe BIM semantic router:

- Window/Door/Skylight -> GSM Library Part
- Object/Macro/Lamp/Label -> GSM Library Part
- continuous cornice / metal section -> Profile attribute
- Building Material / Surface / Composite -> native attributes
- repeated multi-element architectural assembly -> Hotlink Module
- parametric building family -> Safe BIM recipe that composes native elements and READY components
- Favorite -> placement/configuration cache after verified placement

## Phase D — gothic window pilot

1. compile/register `SB_Gothic_Lancet_Large_v01` as Window;
2. verify it appears in available Window library parts;
3. create one Window instance by `libraryPartName` in a known tower wall;
4. verify `type == Window`, exact owner, exact libPart.name, correct offset and sill;
5. create remaining tower windows;
6. verify all instances;
7. only then remove Morph/SEO prototype window assemblies;
8. create Favorite from a verified instance;
9. mark component READY.

## Phase E — tests

Mandatory negative tests:

- missing library part name;
- Object part passed to CreateWindows;
- Window part passed to CreateDoors;
- favoriteName and libraryPartName disagree;
- invalid owner wall;
- polygonal owner wall refusal;
- repeated run must not duplicate windows;
- registered GSM exists but wrong semantic type;
- failure before replacement leaves prototypes untouched.

## Definition of done

The pilot is complete only when selecting a resulting tower element in Archicad reports it as **Window**, not Morph/Object, and its wall opening is produced by the Window library part itself.