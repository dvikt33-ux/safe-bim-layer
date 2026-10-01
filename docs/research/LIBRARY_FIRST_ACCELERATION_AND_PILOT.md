# Library-first acceleration and pilot workflow

## Goal

Turn repeated architectural geometry into reusable, audited Archicad library parts before full building assembly. The immediate pilot is a gothic pointed window, then the same workflow expands to cornices, capitals, pinnacles, balustrades, dormers, gates and other repeated components.

## Why this is faster

The previous direct-generation approach rebuilt each window from ~20+ Walls/Beams/Columns/Morphs/Openings every time. A library-first workflow pays the geometry cost once, audits it once, publishes it once, then places a single hosted Window/Object instance for every repetition.

The target pipeline is:

1. `STYLE_VOCABULARY`
2. `COMPONENT_REGISTRY`
3. `MISSING_COMPONENT_DETECTION`
4. `MASTER_COMPONENT_BUILD`
5. `MASTER_COMPONENT_QA`
6. `LIBRARY_PUBLISH`
7. `FAVORITE_PUBLISH`
8. `BUILDING_ASSEMBLY`
9. `INSTANCE_QA`

`BUILDING_ASSEMBLY` must not begin until all components required by the current architecture package have reached `READY` or are explicitly waived.

## Component levels

### Atomic components

Small reusable details that may become nested parts of larger assemblies:

- sill
- jamb
- archivolt
- tracery
- mullion
- corbel
- capital
- finial
- drip edge
- decorative bracket

### Assembly components

Compositions of atomic components:

- gothic lancet window
- rose window
- gothic door
- gate
- cornice module
- dormer
- pinnacle assembly
- balustrade module

### Building instances

Placed Window/Object/Door instances that reference published library parts or favorites. The building generator should prefer these over rebuilding geometry.

## Dependency graph

Every component has a manifest:

```json
{
  "componentId": "SB_WIN_GOTHIC_LANCET_LARGE_V01",
  "kind": "Window",
  "version": 1,
  "dependencies": [
    "SB_ARCHIVOLT_GOTHIC_A_V01",
    "SB_TRACERY_Y_A_V01",
    "SB_GLASS_LANCET_A_V01"
  ],
  "materialRoles": [
    "TRIM_STONE",
    "DECORATIVE_STONE",
    "GLAZING"
  ],
  "placement": {
    "host": "Wall",
    "favoriteName": "SB_WIN_GOTHIC_LANCET_LARGE"
  },
  "qaStatus": "READY"
}
```

Dependency resolution is topological: atomic components first, then assemblies, then building placement.

## Material-role rule

Library parts must use semantic material roles, not ad-hoc searches during every generation run. The mapping is selected once and persisted:

- `STRUCTURAL_STONE`
- `TRIM_STONE`
- `DECORATIVE_STONE`
- `ROOF`
- `METAL`
- `GLAZING`
- `FLOOR`
- `TERRAIN`
- `ROAD`

Same role => same Archicad attribute assignment. Different render groups => different attribute IDs when the project contains enough attributes.

## Pilot: gothic pointed window

### Phase A — prototype master

Build exactly one window in a dedicated component work area. Do not build eight copies.

Master contains:

- exact pointed `Wallhole` cutting body
- stone jambs
- sill
- pointed archivolt
- mullion/tracery
- glazing
- optional drip mould/decor

Morph is allowed only where native tools cannot reasonably represent the geometry.

### Phase B — Wallhole correctness

For a custom-shape Archicad Window, use a Slab or Roof whose ID is `Wallhole` and whose contour exactly matches the desired wall cut.

Important placement rule for the Wallhole slab: its top reference must be at project Z=0 before Save Selection As Window. If slab thickness is `t`, place its bottom at `-t`. This avoids the published library part being offset from the host wall.

### Phase C — master QA before publish

The master must pass all of these before saving:

1. exterior elevation silhouette
2. interior elevation silhouette
3. section through jamb
4. section through pointed apex
5. plan/reveal alignment
6. exact Wallhole contour
7. no disconnected solids
8. no duplicate coplanar geometry
9. material-role separation
10. origin/reference-plane correctness

Failure means `qaStatus=BLOCKED`; never publish and never multiply instances.

### Phase D — publish

Preferred first pilot path:

`File -> Libraries and Objects -> Save Selection As -> Window`

Save project-specific prototypes to Embedded Library during experimentation.

Then place one instance manually, verify it, and create a Window Favorite. Tapir `CreateWindows` can subsequently place the Window using `favoriteName`.

The first pilot names should be stable and versioned:

- `SB_Gothic_Lancet_Large_v01`
- Favorite: `SB_WIN_GOTHIC_LANCET_LARGE_V01`

Do not stretch a non-parametric saved component far outside the dimensions at which it was authored. Create `NARROW`, `MEDIUM`, `LARGE` variants until a genuinely parametric GDL/LPM version exists.

## Faster generation strategy

### Cache by component fingerprint

A component build request gets a deterministic fingerprint from:

- component type
- geometric dimensions
- style parameters
- material roles
- dependency versions
- LOD

If an identical fingerprint is already `READY`, reuse the library part instead of rebuilding.

### Separate authoring from placement

`component authoring` may be expensive and iterative.

`instance placement` must be cheap and idempotent.

Never combine both in the same mass-generation loop.

### Batch placement only after prototype validation

For a facade with 100 windows:

1. validate one master
2. validate one hosted instance
3. validate orientation on one mirrored/opposite wall
4. only then place remaining 98 instances

### Progressive LOD

Maintain distinct library parts or LOD branches for:

- `LOD_COARSE`
- `LOD_DESIGN`
- `LOD_RENDER`

Do not load expensive sculptural geometry into every design-stage instance if it is not visible.

### Nested modules

Use nested components when a detail repeats inside several larger assemblies. Example: one archivolt component may be referenced by multiple window families.

If a nested object cannot be reliably controlled by the available API, flatten it at publish time while retaining the dependency graph in Safe BIM metadata.

## Library structure

Recommended logical registry:

```text
SafeBIM_Library/
  Openings/
    Windows/
      Gothic/
        Lancet/
        Tracery/
        Rose/
    Doors/
    Gates/
  Facade/
    Cornices/
    Pilasters/
    Capitals/
    Sills/
    Archivolts/
    Balustrades/
    Tracery/
  Roof/
    Dormers/
    Pinnacles/
    Finials/
    Gutters/
    Waterspouts/
  Structural_Decor/
    Corbels/
    Brackets/
    Buttress_Details/
  Landscape/
    Street_Furniture/
  Interiors/
    Furniture/
    Lighting/
    BuiltIn/
```

The physical Archicad library layout may differ; this logical registry remains the source of truth for Safe BIM.

## Component registry status machine

```text
MISSING
  -> DRAFT
  -> GEOMETRY_READY
  -> QA_PENDING
  -> READY
  -> DEPRECATED
```

Additional terminal/blocking state:

```text
BLOCKED
```

A building generation job may only consume `READY` components.

## Audit loop

Every new component family follows this loop:

```text
build one
-> exterior audit
-> interior audit
-> section audit
-> collision/gap audit
-> material audit
-> publish
-> place one instance
-> hosted-instance audit
-> opposite-orientation audit
-> mark READY
-> mass placement
```

## Immediate experiment

1. Stop further mass-generation of the current V3 pointed windows.
2. Use their geometry only as visual reference.
3. Rebuild one clean large lancet master in a dedicated work area at/near project zero.
4. Create exact `Wallhole` geometry.
5. Save as `SB_Gothic_Lancet_Large_v01` Window.
6. Create Favorite `SB_WIN_GOTHIC_LANCET_LARGE_V01`.
7. Place one via Tapir `CreateWindows(favoriteName=...)`.
8. Audit exterior/interior/section/plan.
9. If PASS, replace the eight tower windows with library instances.
10. Record creation time, placement time, element count and failure rate versus the old V3 method.

## Future automation

The GUI `Save Selection As -> Window/Object` step is the current manual publish stage. A later Safe BIM module can automate library compilation with one of these approaches:

- dedicated Archicad Add-On using Library Part APIs
- generated GDL source + library-part creation
- Library Part Maker assisted workflow

Until then, Safe BIM should automate master geometry preparation, manifests, QA, Favorites discovery and mass placement, while keeping publish as a short explicit manual step.

## Performance metrics to collect

For every pilot record:

- master build time
- manual publish time
- first hosted-instance time
- average subsequent placement time
- generated Archicad element count per instance
- PLN size delta
- 3D regeneration time
- collision/gap count
- correction cycles
- number of render material roles preserved

The library-first workflow is successful only if it improves both geometry quality and total iteration time, not merely placement speed.
