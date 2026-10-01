# Reusable architectural modules and tower families

## Status
Research note for Safe BIM architectural-model-quality v2.

## Observation from the current gothic tower test
The current pointed-window repair is still represented by Morph/SEO geometry. It is geometrically cleaner than the earlier rectangular Opening + filler workaround, but it is not yet a hosted Archicad Window library part. Therefore the next Window milestone remains: extend Tapir so `CreateWindows`/`CreateDoors` can resolve a specific `libraryPartName`, then replace temporary Morph/SEO assemblies with real Window instances.

## Key reuse rule
Do not rebuild repeated architecture element-by-element if its topology is already validated. Reuse at the highest level that preserves useful BIM semantics.

There are three preferred reuse levels:

1. **Library Part (.gsm)** — for hosted or standalone repeated components such as windows, doors, gates, cornices, capitals, pinnacles, dormers, furniture, lighting and decorative assemblies.
2. **Hotlink Module (.mod/.pln)** — for repeated assemblies made from native Archicad elements whose BIM identity must remain Wall/Roof/Slab/Column/Window/etc. Typical examples: tower bases, staircase cores, facade bays, room modules, entrance blocks, roof turrets.
3. **Safe BIM recipe/family definition** — for families that share topology but vary by parameters. A recipe instantiates native elements and references reusable Library Parts, instead of flattening the whole assembly into one object.

## Why whole towers should usually NOT become one GDL Object
A complete tower can technically be saved as an Object, but that flattens its internal architecture into a library part. The host project then loses direct Wall/Roof/Window/Slab semantics and local editability.

For repeated architectural tower assemblies, prefer a Hotlink Module when instances are identical or nearly identical. Archicad can save selected elements as a `.mod` file and immediately replace the selection with the resulting hotlinked module. `.mod` keeps model/Floor Plan content and only references attributes actually used by its elements, so it remains relatively lightweight.

For towers that share the same topology but differ in radius, stage height, number of windows, roof pitch or decoration, prefer a parameterized Safe BIM tower recipe rather than a single frozen module.

## Tower family architecture

Example registry:

```json
{
  "familyId": "tower.gothic.octagonal.v1",
  "topologyVersion": 1,
  "parameters": {
    "radius": 6.4,
    "stageHeight": 10.8,
    "roofPitchDeg": 63,
    "windowFamily": "window.gothic.lancet.large.v1",
    "corniceFamily": "cornice.gothic.a.v1",
    "pinnacleFamily": "pinnacle.gothic.a.v1"
  },
  "reuseMode": "recipe",
  "moduleVariant": null
}
```

The recipe creates only the native structural shell and places reusable components:

```text
Tower family
├── native Walls
├── native Slabs
├── native Roofs
├── native Columns/Beams
├── Window library-part instances
├── Cornice library-part/run
├── Pinnacle library-part instances
└── material-role bindings
```

## Variant policy

### Exact repeated tower
If geometry is identical except translation/rotation:
- save as `.mod`;
- place as Hotlink Module;
- keep one source of truth;
- update all instances by updating the module source.

### Same topology, small dimensional changes
Use a Safe BIM recipe with parameters:
- radius;
- number of sides;
- stage height;
- roof pitch;
- opening count/spacing;
- material role map;
- selected decorative component families.

### Same base, different upper termination
Split into nested reusable assemblies:

```text
tower.base.octagonal.v1
├── wall ring
├── floor/crown
├── buttress grid
└── window bay positions

+ tower.top.spire.v1
or tower.top.battlement.v1
or tower.top.dome.v1
```

This allows reuse without duplicating the whole tower.

## Nested reuse
Safe BIM should support component dependencies and assembly composition:

```text
tower.gothic.octagonal
├── window.gothic.lancet.large
│   ├── tracery.y.a
│   └── glazing.lancet.a
├── cornice.gothic.a
│   └── corbel.gothic.a
├── pinnacle.gothic.a
└── finial.gothic.a
```

Compile/ensure dependencies first, then the parent assembly.

## Performance strategy
Cache three things independently:

1. **component cache** — compiled `.gsm` + fingerprint + version;
2. **module cache** — `.mod`/`.pln` source + fingerprint + version;
3. **recipe cache** — topology/version + parameter schema + generated receipts.

Do not regenerate a component if its fingerprint and dependencies are unchanged.

## Immediate window correction
The screenshot from the gothic tower confirms the current replacement is still Morph-based. That is expected from the interim V4 strategy and must not be treated as a final Window implementation.

Final target:

```text
compiled .gsm Window
→ Embedded Library
→ `CreateWindows(libraryPartName=...)`
→ hosted Window instance
→ optional Favorite creation
```

Until the `libraryPartName` extension exists, Morph/SEO pointed-window assemblies are temporary geometry only.

## Tapir extension roadmap related to reuse

1. Add `libraryPartName` to `CreateWindows` and `CreateDoors`.
2. Add `SB_EnsureLibraryPart`.
3. Add `SB_EnsureModule` / `SB_PlaceModule` when API support is verified.
4. Add typed component/module registry.
5. Add `SB_InstantiateTowerFamily` high-level command or versioned recipe.
6. Add `SB_ReconcileFamilyInstances` for updates after family version changes.

## Architectural rule
Use the highest-level reusable representation that does not destroy required BIM semantics:

- ornament / repeated component → Library Part;
- repeated native-element assembly → Hotlink Module;
- parameterized architectural system → Safe BIM recipe/family;
- one-off structural geometry → native Archicad elements.

This hierarchy should become a core Safe BIM generation rule.
