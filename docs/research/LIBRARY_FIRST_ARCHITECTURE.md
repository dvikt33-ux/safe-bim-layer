# Library-first architectural modeling strategy

## Decision

For architectural-grade Safe BIM generation, repeated or reusable architectural geometry should be promoted into reusable Archicad library components before large model assembly whenever that promotion improves consistency, performance, placement, or maintainability.

This changes the preferred workflow from `model everything instance-by-instance` to:

`analyze vocabulary -> build component masters -> validate -> publish to library -> create favorites/placement recipes -> assemble model -> refine -> audit`.

## Important boundary

Library-first does **not** mean converting every repeated element into a generic object.

Prefer native Archicad system elements when their native behavior is important:

- Wall for walls
- Slab for slabs and floors
- Roof / Shell for roofs and shells
- Column / Beam for structural linear members
- Stair / Railing for stairs and railings
- Mesh for terrain
- Window / Door for hosted openings

Promote geometry to a library part when it is a reusable architectural component with stable internal geometry or behavior, for example:

- pointed Gothic windows
- doors and gates
- cornice modules
- capitals and column heads
- pinnacles and finials
- gargoyles / waterspouts
- balustrade modules
- custom brackets / corbels
- façade ornaments
- dormers
- lanterns
- decorative roof elements
- furniture and equipment
- repeated technical assemblies

## Component hierarchy

Use a hierarchy rather than a flat library.

Suggested logical structure:

```text
SafeBIM_Library/
  Openings/
    Windows/
      Gothic/
        Lancet/
        Tracery/
        Rose/
      Classical/
    Doors/
    Gates/

  Facade/
    Cornices/
    Pilasters/
    Capitals/
    Sills/
    Archivolts/
    Tracery/
    Balustrades/

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
    Retaining_Elements/
    Street_Furniture/

  Interiors/
    Furniture/
    Lighting/
    BuiltIn/
```

The physical Archicad library organization may differ by Library Package / Embedded Library / linked source, but the generator should preserve this semantic taxonomy in its own registry.

## Nested components

Composite architectural elements should be built from reusable subcomponents where practical.

Example:

```text
SB_WIN_GOTHIC_LANCET_LARGE
  -> window wall-hole definition
  -> stone jamb module
  -> pointed archivolt module
  -> sill module
  -> mullion module
  -> Y-tracery module
  -> glazing module
```

Likewise:

```text
SB_CORNICE_GOTHIC_A
  -> base moulding
  -> repeated dentil/corbel module
  -> drip edge
  -> end/corner modules
```

The generator should distinguish between:

1. **Atomic component** - smallest reusable detail.
2. **Assembly component** - reusable grouping of atomic components.
3. **Hosted component** - Window/Door/Opening-hosted component.
4. **Linear repeat component** - cornice, balustrade, parapet, railing module.
5. **One-off sculptural component** - Morph or custom library part used only where native tools are unsuitable.

## Required component lifecycle

### Phase A - Vocabulary extraction

Before modeling a building, identify repeated architectural vocabulary:

- window families
- door families
- cornice families
- column / capital families
- balustrade modules
- roof ornaments
- façade ornaments
- furniture / equipment families

Do not begin large-scale placement until the vocabulary is classified.

### Phase B - Master component creation

Create exactly one master of each family/size variant.

The master should be authored using native Archicad elements whenever possible. Morph is a fallback for shapes that cannot reasonably be represented by a native element or by a saved library part workflow.

### Phase C - Master audit

A master component must pass before publication:

- topology / closed geometry
- no unintended overlaps
- no holes except intentional voids
- correct host relationship
- correct insertion origin
- correct orientation
- exterior inspection
- interior inspection
- section inspection
- plan inspection
- material-role assignment
- appropriate LOD
- reasonable polygon count

For hosted windows/doors additionally verify the wall-hole, reveal and interior/exterior behavior.

### Phase D - Publish

Publish approved geometry as an Archicad library element when supported.

Recommended identities:

```text
SB_<CATEGORY>_<FAMILY>_<VARIANT>_vNN
```

Examples:

```text
SB_WIN_GOTHIC_LANCET_LARGE_v01
SB_WIN_GOTHIC_LANCET_NARROW_v01
SB_CORNICE_GOTHIC_A_v02
SB_CAPITAL_GOTHIC_CLUSTERED_v01
SB_PINNACLE_OCTAGONAL_A_v01
```

### Phase E - Favorite / placement recipe

For Window/Door and other tools where Tapir supports Favorites, create a Favorite for the approved library element and place it by stable favorite name.

Persist the mapping:

```json
{
  "componentRegistry": {
    "GOTHIC_LANCET_LARGE": {
      "libraryPart": "SB_WIN_GOTHIC_LANCET_LARGE_v01",
      "favorite": "SB_FAV_WIN_GOTHIC_LANCET_LARGE",
      "category": "WINDOW",
      "version": 1
    }
  }
}
```

### Phase F - Assembly

Only after component publication should the building generator place repeated instances.

Placement code should contain only semantic placement data:

```text
family = GOTHIC_LANCET_LARGE
host = wall_guid
position = bay_04
sill = 2.10
orientation = exterior
```

It must not redraw the entire component geometry per instance.

## Material-role rule

Library components must follow the same stable semantic material-role system as the rest of Safe BIM.

Example:

```text
STRUCTURAL_STONE
TRIM_STONE
DECORATIVE_STONE
ROOF
METAL
GLAZING
WOOD
FLOOR
```

The component should expose or preserve distinct render groups instead of baking unrelated parts into one material.

## Parametric vs fixed variants

Do not stretch a saved geometric library part across a large dimensional range unless it was explicitly authored parametrically.

Prefer a small family of validated variants over destructive scaling:

```text
Lancet_Narrow
Lancet_Medium
Lancet_Large
```

If a component needs continuous dimensional variation, it should eventually become a deliberately parametric GDL / Library Part Maker component rather than a stretched saved selection.

## Performance consequence

A reusable component should replace dozens of independent geometric write operations.

Example:

```text
old Gothic window:
~20-25 Archicad elements per window

library-first Gothic window:
1 Window instance per window
```

This reduces:

- API calls
- duplicated geometry
- collision opportunities
- retry/reconciliation complexity
- model size
- placement drift
- material inconsistency

## Generator architecture consequence

Add a library compilation stage before building compilation:

```text
architectural brief
      ↓
style vocabulary extraction
      ↓
component dependency graph
      ↓
component master generation
      ↓
component QA
      ↓
library/favorite publication
      ↓
BUILDING SKELETON
      ↓
PRIMARY SYSTEM ELEMENTS
      ↓
LIBRARY COMPONENT PLACEMENT
      ↓
SECONDARY DETAIL
      ↓
QA / COLLISION / GAP
      ↓
FINALIZATION
```

## Component dependency graph

Nested components require explicit dependencies.

Example:

```text
GOTHIC_WINDOW_LARGE
  depends on:
    ARCHIVOLT_A
    JAMB_A
    SILL_A
    Y_TRACERY_A
    GLASS_LANCET_A
```

Compilation order must be topological: atomic components first, assemblies second, building placement last.

A component is not publishable if one of its dependencies is missing or has failed QA.

## Versioning

Never silently replace a component geometry used by an existing generated model.

Use semantic versions or explicit revisions:

```text
SB_WIN_GOTHIC_LANCET_LARGE_v01
SB_WIN_GOTHIC_LANCET_LARGE_v02
```

The model-generation state should record the exact component version used.

## Library readiness gate

Before `BUILDING_ASSEMBLY_READY = true`, require:

- all requested repeated component families resolved
- all required masters pass QA
- all component dependencies resolved
- material-role map complete
- placement origin/orientation validated
- hosted opening behavior validated where applicable
- exact component versions persisted

Only one-off geometry and genuinely context-dependent geometry may be deferred to model assembly.

## Consequence for current Gothic tower experiment

The existing multi-element pointed windows should be treated as prototype geometry, not the final placement strategy.

The next correct workflow is:

1. choose one successful pointed-window geometry;
2. rebuild/clean it as a master;
3. provide an exact wall-hole;
4. audit exterior/interior/section/plan;
5. save it as a Window library part;
6. create a Favorite;
7. replace all repeated tower windows with Window instances;
8. remove prototype construction geometry;
9. keep only non-repeatable sculptural details as Morphs.

The same approach should then be applied to cornices, capitals, pinnacles, balustrades and other repeated Gothic vocabulary before modeling a full castle.