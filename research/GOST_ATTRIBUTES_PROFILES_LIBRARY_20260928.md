# GOST/SPDS, attributes, profiles, composites and shared library research

Date: 2026-09-28
Scope: Archicad 29 + Tapir 1.5.9 + Safe BIM architecture.

This file consolidates the repeated audit/pass cycles on drawing standards, attribute authoring, dimensions, complex profiles, composites and cross-project library behavior.

---

# 1. GOST/SPDS design principle

Do not hard-code arbitrary Archicad pen indices, font indices or one model-space dimension offset and call that "GOST".

Safe BIM needs a standards profile that maps semantic roles to actual Archicad resources.

Example:

```text
SAFE_BIM_GOST_PROFILE
  standard/version
  scale policy
  font roles
  pen roles
  line-type roles
  text-height roles
  dimension rules
  hatch/fill roles
  annotation spacing rules
```

The standards engine should remain configurable because project/university requirements may select a specific permitted implementation while the BIM logic stays the same.

---

# 2. Fonts

## Current Tapir capability

Text and Label commands can use fields such as:

- `fontIndex`
- `penIndex`
- height
- bold
- italic
- underline
- angle/alignment-related style fields.

## Problem

`fontIndex` is installation/project-context dependent and must not be treated as durable identity.

## Recommended wrapper

```text
ResolveFontByName(name)
```

Safe BIM stores a role/family name, resolves the active index on session/project load, caches it, and fails closed if the required font is unavailable.

Do not silently substitute another font in standards-controlled output.

---

# 3. Pen Tables

Tapir 1.5.9 supports creating/overwriting Pen Table attributes and modifying selected pens while seeding the rest from an existing table.

Recommended semantic roles:

- `GOST_CUT`
- `GOST_VISIBLE`
- `GOST_THIN`
- `GOST_DIMENSION`
- `GOST_AXIS`
- `GOST_HIDDEN`
- `GOST_HATCH`
- `GOST_TEXT`

The standards profile maps roles to actual pen indices/colors/widths.

Safe BIM-owned Pen Tables should have deterministic names, e.g.:

- `SB_GOST_1_20`
- `SB_GOST_1_50`
- `SB_GOST_1_100`

if scale-specific presentation is desired.

---

# 4. Line Type attributes

Tapir supports creation of Line attributes including dashed and symbol patterns.

Safe BIM should ensure required semantic line types exist, for example:

- `SB_GOST_SOLID`
- `SB_GOST_DASHED`
- `SB_GOST_CENTER`
- `SB_GOST_SECTION`
- `SB_GOST_BREAK`

Dependencies must be resolved by Safe BIM-owned GUID/name registry, not by guessing existing project names.

---

# 5. Associative dimensions

Tapir supports associative linear dimensions using explicit witness references.

Core safety principle:

```text
real Archicad Dimension > drawn line/text imitation
```

A true associative Dimension should be preferred whenever the intent is dimensioning.

## Placement engine

Dimension placement needs a geometry/collision engine using paper-space policy.

Recommended stages:

```text
collect measured geometry
-> determine outward normal / preferred side
-> convert minimum paper offset through current view scale
-> place first dimension chain
-> collision test against contour/text/other dimensions
-> move outward until clear
-> place additional chains using minimum inter-chain gap
```

Do not assume one constant world-space offset works across scales.

## Post-create existence verification

Returned GUID alone is not sufficient.

For every dimension:

```text
create -> returned GUID -> query expected database -> verify real element exists -> PASS
```

This is mandatory because section/elevation workflows have had ghost-GUID failure modes.

---

# 6. Section/Elevation dimension acceleration

Use semantic presets where available instead of manually deriving every witness coordinate.

Important presets/concepts include:

- WallCompositeFaces
- WallSkinBorders
- SlabCompositeFaces
- SlabSkinBorders
- BeamOrColumnRefLineEndPoints
- BeamOrColumnBoundingBoxCorners
- DoorWindowWallHoleCorners
- DoorWindowModelHotspots

These should feed a GOST layout engine responsible for offset/collision/style, while Archicad supplies the semantic measured points.

---

# 7. View-controlled presentation

Saved View settings can encode presentation state including:

- layer combination;
- dimension style;
- pen set;
- model view options;
- graphic overrides;
- scale;
- structure display;
- other navigator/view settings.

Recommended Safe BIM working views:

```text
_AI_GOST_PLAN
_AI_GOST_SECTION_CORE
_AI_GOST_SECTION_FULL
_AI_GOST_ELEVATION
_AI_3D_QA
```

Do not modify user views unless explicitly requested.

---

# 8. GOST compliance audit

Future high-level command/report:

```text
GostComplianceAudit
```

Possible checks:

- wrong font family/height;
- wrong pen role/width;
- wrong line-type role;
- dimension chain too close to contour;
- insufficient gap between dimension chains;
- annotation collisions;
- non-associative dimensions where association is expected;
- missing/incorrect dimension style;
- wrong saved-view pen set/layer combination;
- missing Safe BIM standard attributes.

The report should distinguish:

- normative rule;
- project policy;
- observed Archicad state;
- violation / warning / unresolved.

---

# 9. Complex Profiles

## Static capability

Tapir 1.5.9 `CreateProfiles` can author more than simple copies.

Geometry sources:

- `sourceAttributeId` — copy an existing Profile geometry;
- `newSkins` — caller-authored geometry;
- both combined.

Supported source/test scenarios include:

- arbitrary polygon contours;
- arcs;
- multiple contours;
- holes;
- multiple skins;
- Building Material assignment;
- skin/edge properties;
- replacing existing skins.

Profile applicability includes element-type flags such as wall/beam/column use.

## High-level API

```text
ProfileBuilder.create(name, geometry, skins, useFor)
ProfileBuilder.clone_and_modify(source, overrides)
ProfileBuilder.replace_geometry(profile, geometry)
```

## Safety constraints

- read current profile geometry before modifications;
- canonicalize skin/edge identifiers;
- never write arbitrary edge indices without validating the exact target;
- skip/guard internal anchor bridge slots known to be crash-prone in source investigations;
- immediate `GetProfiles` readback after write.

## Live test matrix

When notebook access returns, create/readback:

- rectangle;
- L;
- T;
- U;
- profile with arc;
- profile with hole;
- multi-skin profile;
- assign to Wall/Beam/Column where valid;
- modify attribute and verify dependent BIM elements rebuild.

---

# 10. Composites

Tapir supports creation of Composite attributes with:

- use-with element categories;
- ordered skins;
- Building Material references;
- skin type (e.g. Core/Finish semantics where supported);
- frame pens;
- skin thickness;
- separator line type and pen.

## CompositeBuilder

```text
CompositeBuilder.create(
  name,
  skins=[...],
  separators=[...],
  useWith=[...]
)
```

## Mandatory preflight

For every requested Composite:

- every Building Material exists via exact/safe alias resolution;
- every thickness > 0;
- total thickness is computed from skins;
- separator Line Types exist;
- separator pens exist;
- use-with values are supported;
- duplicate/conflicting attribute name policy is explicit.

## Mandatory readback

After creation/overwrite:

- same attribute identity/name policy;
- same ordered skins;
- same Building Material GUIDs;
- same thicknesses;
- same separator line/pen values;
- recomputed total thickness exactly matches expected tolerance.

Do not use an element thickness field to try to override a Composite's physical skin sum.

---

# 11. Element recipes / favorites

Tapir element creation paths support `favoriteName` in several generic creation flows.

Recommended model:

```text
ElementRecipe
  favorite/base defaults
  BIM structure role
  layer role
  surface role
  pen/line role
  classification/properties
  element-specific overrides
```

Examples:

- `SB_WALL_EXTERIOR`
- `SB_WALL_INTERIOR`
- `SB_SLAB_STANDARD`
- `SB_BEAM_CONCRETE`
- `SB_COLUMN_STEEL`
- `SB_WINDOW_STANDARD`
- `SB_TEXT_GOST`
- `SB_DIM_GOST`

Favorites are valuable as tested baseline defaults, but Safe BIM must still explicitly verify critical semantics after creation.

---

# 12. Shared library across projects

## Exact Tapir 1.5.9 library commands

Available command family includes:

- `AddFilesToEmbeddedLibrary`
- `GetLibraries`
- `SetLibraries`
- `AddLibraries`
- `ReloadLibraries`
- `GetAvailableLibraryParts`

## Critical distinction

### Embedded Library

Project-local. Good for self-contained PLN delivery, not for the user's requirement of one object becoming available in later projects.

### Linked Local Library

A filesystem folder linked into multiple projects.

Recommended root:

```text
SAFE_BIM_LIBRARY/
  Objects/
  Furniture/
  Windows/
  Doors/
  Equipment/
  Details/
  User/
  _manifest/
```

## Auto-attach architecture

On project open/new:

```text
GetLibraries
-> is SAFE_BIM_LIBRARY already linked?
   yes: no-op
   no: AddLibraries(shared_path)
-> optional reload only when required
```

A project template may also prelink the library, but add-on auto-attach is the general solution for projects not created from the template.

## Identity

Never persist only a Library Part index as durable identity.

Use stable identity strategy (UniID/subtype/name registry) and resolve current runtime index as needed.

## Saving a newly created reusable object

Stock Tapir provides management/registration of files but does not yet provide the complete desired user workflow:

```text
select model geometry
-> save as reusable GSM/library object
-> write into shared library
-> update manifest
-> reload
-> use from another project
```

Recommended custom command:

```text
SaveSelectionAsSharedLibraryObject
```

Required policies:

- deterministic file/object name;
- subtype/type selection;
- dependency/macro handling;
- overwrite/versioning policy;
- manifest entry;
- shared-folder path guard;
- library reload;
- availability readback via `GetAvailableLibraryParts`.

---

# 13. Shared library versioning

Recommended manifest entry per Safe BIM-owned object:

```text
stable_id
name
type/subtype
version
source project GUID (optional provenance)
created_at
modified_at
file path
content hash
dependencies/macros
minimum Archicad version
```

Do not overwrite a widely used object silently when geometry/parameters change incompatibly.

Possible policy:

- compatible edit -> same stable object/version increment;
- breaking edit -> new stable object/version family;
- explicit user-approved replacement when existing projects may change appearance.

---

# 14. Combined standards architecture

```text
SAFE BIM STANDARDS ENGINE
  |
  +-- GOST/SPDS profile
  |     +-- font resolver
  |     +-- pen roles
  |     +-- line roles
  |     +-- dimension rules
  |     +-- collision/layout
  |
  +-- BIM attribute registry
  |     +-- Building Materials
  |     +-- Composites
  |     +-- Profiles
  |     +-- Surfaces
  |     +-- Layers
  |     +-- Favorites/recipes
  |
  +-- Shared library registry
        +-- auto-attach
        +-- part identity
        +-- manifest/versioning
        +-- reload/availability proof
```

---

# 15. Priority implementation list

## P0

1. `ResolveFontByName`
2. `EnsureGostPenTable`
3. `EnsureGostLineTypes`
4. `GostDimensionPlacementEngine`
5. `GostComplianceAudit`
6. `EnsureSharedLibrary`
7. automatic library attach on Project Open/New

## P1

8. `ProfileBuilder`
9. `CompositeBuilder`
10. `ElementRecipe/StyleApplier`
11. `SaveSelectionAsSharedLibraryObject`
12. Safe BIM-owned GOST Plan/Section/Elevation views

## P2

13. library manifest/versioning/dependency management
14. automatic standards migration between Safe BIM profile versions

---

# 16. Required live proof suite

1. resolve chosen standards font by name and create/read Text/Label;
2. create Safe BIM Pen Table and bind a test view;
3. create/read dashed/center/section Line Types;
4. create associative plan dimension and verify association after wall move;
5. verify paper-space dimension offset conversion at multiple scales;
6. section/elevation semantic dimension presets with existence readback;
7. create Profile shapes: rectangle/L/T/U/arc/hole/multi-skin;
8. assign Profiles to supported BIM elements;
9. create 3/5/7-skin Composites and verify ordered skins/separators;
10. apply a complete ElementRecipe and read back critical fields;
11. attach one shared library folder to project A;
12. open project B and prove automatic attach;
13. prove a part placed in the shared folder is discoverable in both projects;
14. after custom wrapper exists, save one selected object and prove availability in project B.

Each proof must record raw request/response, project identity, command version, affected GUID/attribute IDs, and postcondition readback.