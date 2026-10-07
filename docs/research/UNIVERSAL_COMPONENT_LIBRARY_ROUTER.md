# Universal Component Library Router for Safe BIM / Tapir

## Goal

Safe BIM should not treat every reusable architectural asset as raw geometry that must be recreated for every instance. Before model assembly, reusable components are compiled into the native Archicad mechanism that best matches their BIM semantics, then placed by short, stable recipes.

The rule is **semantic routing**, not “put everything in one GSM library.”

## Native destination matrix

| Safe BIM component role | Native Archicad destination | Typical examples |
|---|---|---|
| Hosted wall opening | Window / Door Library Part | lancet window, gate, custom door |
| Roof-hosted opening | Skylight Library Part | dormer skylight, rooflight |
| Reusable free-standing detail | Object Library Part | gargoyle, pinnacle, finial, bracket, furniture, equipment |
| Reusable nested helper | Macro Library Part | archivolt fragment, tracery macro, modular decorative helper |
| Light source | Lamp Library Part | lantern, luminaire |
| Annotation | Label / PlanSign Library Part | custom tags and symbols |
| Repeating linear moulding with constant section | Complex Profile attribute | cornice section, metal section, sill profile, custom beam/column section |
| Homogeneous construction material | Building Material attribute | stone, concrete, steel |
| Render-only finish | Surface attribute | stone finish, glazing, patinated metal |
| Layered wall/slab/roof build-up | Composite attribute | masonry + insulation + lining |
| Reusable multi-element building assembly | Hotlink Module (.mod) | complete tower, stair core, entrance pavilion |
| Parametric family with varying dimensions/topology | Safe BIM Recipe + native elements | octagonal tower family, façade bay family |
| Placement/configuration preset | Favorite | window preset, wall preset, object preset |

### Important consequence

A “metal profile” normally should **not** be a GSM Object if it is intended to behave as a beam/column/wall profile. It belongs in the Archicad Profile attribute system. Likewise, a façade cornice may be either:

- a **Complex Profile** when it is a continuous linear extrusion, or
- an **Object/Macro** when it is a discrete or sculptural repeating module.

The router must choose by semantic behavior, not by appearance.

---

## Existing Tapir capability we can reuse

Tapir already has `AddFilesToEmbeddedLibrary`, which can register a copied file as one of several Archicad library-part types. Upstream code already maps the `type` string to `APILib_WindowID`, `APILib_DoorID`, `APILib_ObjectID`, `APILib_LampID`, `APILib_RoomID`, `APILib_PropertyID`, `APILib_PlanSignID`, `APILib_LabelID`, `APILib_MacroID`, `APILib_PictID`, `APILib_ListSchemeID`, `APILib_SkylightID`, and `APILib_OpeningSymbolID` before calling `ACAPI_LibraryPart_Register`.

Therefore Safe BIM does **not** need a separate “add window to library / add door to library / add object to library” command for each case. The existing embedded-library command is already a universal file registrar for GSM-style assets.

What is missing is the next stage: **native placement by an explicit library-part identity** for hosted and library-based element types.

---

## Required Tapir extension 1: explicit library part selection

### Current limitation

`CreateWindows` / `CreateDoors` currently select their GDL library part through the Window/Door tool defaults or an existing `favoriteName`.

That is not sufficient for a self-compiling library pipeline because Safe BIM needs to register a new part and immediately place that exact part without a manual Favorite step.

### Required new optional field

Add to each Window/Door item:

```json
{
  "libraryPartName": "SB_Gothic_Lancet_Large_v01"
}
```

Resolution order should be deterministic:

1. clone normal tool defaults;
2. if `favoriteName` exists, apply it;
3. if `libraryPartName` exists, resolve it and override the Window/Door `openingBase.libInd`;
4. apply explicit placement fields such as width/height/sill/offset/orientation;
5. create element and marker;
6. read back the created element and report `libPart.name`.

If both favorite and libraryPartName are supplied, libraryPartName is the final authority for the hosted GDL part; the favorite may still provide marker and other defaults.

### Shared resolver

Tapir already contains a resolver for Objects/Lamps that performs:

```cpp
API_LibPart libPart = {};
GS::ucscpy (libPart.docu_UName, uName.ToUStr ());
GSErrCode err = ACAPI_LibraryPart_Search (&libPart, false, true);
...
element.object.libInd = libPart.index;
```

Refactor this into a generic function returning `libPart.index`, then use it for Object, Lamp, Window and Door creation.

For Window/Door the target is:

```cpp
element.window.openingBase.libInd = libPart.index;
```

The resolver must also validate the requested part’s compatible type/subtype before creation and fail closed when it is not a Window/Door-compatible part.

---

## Required Tapir extension 2: EnsureLibraryPart

`AddFilesToEmbeddedLibrary` already performs registration. Safe BIM should wrap it with an idempotent higher-level command/recipe:

```json
{
  "componentId": "window.gothic.lancet.large",
  "version": "1.0.0",
  "libraryPartName": "SB_Gothic_Lancet_Large_v01",
  "type": "Window",
  "inputPath": "C:/.../SB_Gothic_Lancet_Large_v01.gsm",
  "outputPath": "SafeBIM/Windows/Gothic/SB_Gothic_Lancet_Large_v01.gsm",
  "overwriteExisting": true,
  "sourceFingerprint": "sha256:..."
}
```

Behavior:

1. query `GetAvailableLibraryParts` filtered by expected type;
2. compare component/version/fingerprint registry;
3. if same version exists: return `REUSE`;
4. if missing or stale: use `AddFilesToEmbeddedLibrary`;
5. reload libraries only when necessary;
6. query again and verify exact name/type exists;
7. return durable receipt.

This can initially live as a Python Tapir recipe and later become a C++ command once the contract stabilizes.

---

## Required Tapir extension 3: universal component registry

Safe BIM needs one registry independent of Archicad’s internal folder layout:

```json
{
  "window.gothic.lancet.large": {
    "version": "1.0.0",
    "kind": "Window",
    "nativeDestination": "EmbeddedLibrary",
    "libraryPartName": "SB_Gothic_Lancet_Large_v01",
    "outputPath": "SafeBIM/Windows/Gothic/SB_Gothic_Lancet_Large_v01.gsm",
    "status": "READY",
    "fingerprint": "..."
  },
  "profile.gothic.cornice.a": {
    "version": "1.0.0",
    "kind": "Profile",
    "nativeDestination": "ProfileAttribute",
    "attributeName": "SB_Gothic_Cornice_A",
    "status": "READY",
    "fingerprint": "..."
  },
  "module.gothic.tower.octagonal": {
    "version": "1.0.0",
    "kind": "HotlinkModule",
    "nativeDestination": "MOD",
    "path": "SafeBIM/Modules/Gothic/Tower_Octagonal_v01.mod",
    "status": "READY",
    "fingerprint": "..."
  }
}
```

A single registry lets the generator ask for a semantic component without caring whether it is a GSM, Profile attribute, Favorite or Hotlink Module.

---

## Component lifecycle

Each component has explicit states:

```text
MISSING
  -> DRAFT
  -> VALIDATED
  -> COMPILED
  -> REGISTERED
  -> PLACEMENT_TESTED
  -> READY
  -> DEPRECATED
```

A building assembly may use only `READY` components unless an explicit experimental flag is enabled.

---

## Dependency graph and nesting

Reusable components may depend on lower-level components:

```text
window.gothic.lancet.large
  -> macro.tracery.y01
  -> macro.archivolt.a
  -> surface.glazing
  -> surface.trim-stone

module.gothic.tower.octagonal
  -> window.gothic.lancet.large
  -> profile.gothic.cornice.a
  -> object.gothic.pinnacle.a
  -> object.gothic.finial.a
```

Safe BIM resolves dependencies topologically. A parent cannot become READY until all required children are READY.

---

## Performance strategy

The expensive stage must happen once:

```text
component definition
 -> compile
 -> validate
 -> register
 -> placement smoke test
 -> cache READY
```

Normal modeling then becomes short placement recipes:

```python
sb.place_component(
    component="window.gothic.lancet.large",
    host=wall_guid,
    center_offset=3.8,
    sill_height=2.0,
)
```

or:

```python
sb.place_component(
    component="module.gothic.tower.octagonal",
    origin=(100, 200, 0),
    rotation=1.5708,
)
```

The architectural model should never regenerate a library component per instance.

---

## Material-role invariant

Reusable parts use semantic material roles rather than ad-hoc material names:

```text
STRUCTURAL_STONE
TRIM_STONE
DECORATIVE_STONE
ROOF
METAL
GLAZING
WOOD
```

The project resolves roles to actual Building Materials/Surfaces once and stores the mapping. Identical semantic groups use the same material; distinct groups use distinct roles when possible. This preserves renderer post-processing and avoids random per-instance materials.

---

## Window pilot acceptance criteria

The gothic lancet window is the first integration test for this system.

A pilot passes only when:

1. the component is present in the project library as a Window-compatible library part;
2. `CreateWindows` can select it by explicit `libraryPartName`;
3. the created element read-back reports `type == Window`;
4. read-back `libPart.name` equals `SB_Gothic_Lancet_Large_v01`;
5. the host wall id matches the intended wall;
6. all eight tower windows are instances of the same library part family;
7. the GDL part itself defines the pointed `WALLHOLE` so the wall opening is pointed on both exterior and interior faces;
8. only after all new Window instances pass read-back are the old Morph/SEO prototypes deleted;
9. a Favorite may then be created from a verified instance for faster subsequent placement and user-facing workflows.

---

## Next implementation milestones

### M1 — libraryPartName for hosted library elements

- Window
- Door
- later Skylight where applicable
- tests for unknown name, wrong subtype, correct part, marker preservation, explicit width/height override

### M2 — EnsureLibraryPart recipe

- compile/import/register
- idempotent fingerprinting
- exact type/name read-back

### M3 — ComponentRegistry

- semantic id
- version
- dependencies
- native destination
- READY status

### M4 — non-GSM routes

- Profile attributes for continuous cornices / metal sections
- material/surface/composite routes
- Hotlink Module route for tower assemblies

### M5 — Recipe palette

Stable recipes are stored in GitHub and exposed through the Tapir script palette, so the user can invoke operations such as:

```text
SB / Compile Missing Components
SB / Replace Prototype Windows
SB / Build Gothic Tower Family
SB / Audit Component Registry
```

without pasting large PowerShell blocks.

---

## Design principle

**Library-first does not mean GSM-first.**

Safe BIM first identifies the semantic class of the reusable component, routes it to the correct native Archicad system, validates it once, and then reuses it by reference. This keeps the final model editable, lightweight and BIM-native while still allowing highly detailed architectural libraries.