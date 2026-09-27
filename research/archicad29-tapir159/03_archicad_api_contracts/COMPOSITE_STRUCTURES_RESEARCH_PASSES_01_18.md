# Composite / Multilayer Structures Research — passes 01–18

Scope: Archicad 29 + Tapir Additional JSON Commands 1.5.9. Target: deterministic creation and use of multilayer Walls, Slabs, Roofs and Shells from a validated construction specification. Research only; production writes remain disabled unless separately audited.

## Core conclusion

Tapir 1.5.9 already exposes the essential attribute path. A new Tapir extension is **not required** for ordinary Composite creation:

`GetBuildingMaterials` / `CreateBuildingMaterials` → `CreateComposites` / `GetComposites` → create Wall/Slab/Roof with `structureType=Composite` + exact `compositeId`.

The Safe BIM work is mainly a compiler, resolver, verifier and safety layer around these commands.

## Passes

### 01 — Archicad data model
Graphisoft represents a multilayer construction as a Composite attribute (`API_CompWallType`). It contains total thickness and a number of skins. Header flags determine whether the Composite may be used with Wall, Slab, Roof and/or Shell.

### 02 — Skin model
Each skin (`API_CWallComponent`) has a Building Material, frame pen, Core/Finish flags and absolute thickness in meters.

### 03 — Separator model
A composite with N skins requires N+1 separator/contour line definitions.

### 04 — Tapir read contract
Tapir 1.5.9 `GetComposites` can return `useWith`, ordered `skins`, and `separators`, including Building Material IDs and thicknesses.

### 05 — Tapir create contract
Tapir 1.5.9 `CreateComposites` accepts `name`, `useWith`, ordered skins and separators. It calculates `totalThick` as the sum of skin thicknesses and creates/modifies the Archicad Composite attribute via `ACAPI_Attribute_CreateExt` / `ModifyExt`.

### 06 — Supported element classes
`useWith` maps to Archicad flags for Wall, Slab, Roof and Shell. Safe BIM must always send `useWith` explicitly; omission currently leaves no usage flag selected.

### 07 — Dependency validation gap
In Tapir 1.5.9 `CreateComposites`, an invalid `buildingMaterialId` or separator `lineTypeId` is not guaranteed to produce a local explicit error: the index is only assigned when lookup succeeds. Safe BIM therefore must pre-resolve every referenced attribute ID and reject the plan before physical composite creation if any dependency is missing.

### 08 — Building Materials
Tapir 1.5.9 exposes Building Material read/create with physical and graphic fields. However, a regulatory material label alone is not enough to author a trustworthy Building Material: cut fill, surface, intersection priority and physical values may be project-specific.

### 09 — Material resolution policy
A normative layer name is mapped to a project Building Material only through one of:
- `EXACT_MATCH`
- `USER_CONFIRMED_ALIAS`
- `SAFE_BIM_OWNED_TEMPLATE`

`MISSING` blocks the composite plan. No silent fuzzy match.

### 10 — ConstructionAssemblySpec
Normalize requested construction into a canonical ordered model:

```text
assembly_kind: Wall | Roof | Slab | Shell
layers[]:
  material_key
  building_material_id
  thickness_m
  role: Core | Finish | Other
separator_spec
source_refs[]
```

For a request derived from SP/normative text, keep the source layer wording and source reference separately from the Archicad Building Material mapping.

### 11 — Deterministic fingerprint
Fingerprint must include ordered layer Building Material GUIDs, exact thicknesses, roles, useWith set and separator settings. This prevents selecting a Composite merely because its name looks similar.

### 12 — Deterministic Safe BIM naming
Recommended owned name form:

`SBM::<KIND>::<hash8>::<human-label>`

Name is a reconciliation key, never sufficient ownership evidence by itself. Exact fingerprint must also match.

### 13 — Collision policy
`overwriteExisting=false` by default. If a name exists:
- exact fingerprint match → reuse after read verification;
- different fingerprint → do not overwrite; choose a new deterministic name/version or stop;
- never modify a foreign project Composite automatically, because every element using it would change.

### 14 — Receipt / reconciliation
Composite creation is a write with the same ambiguity rules as element creation:
prepare → dependency preflight → project identity → dispatchStarted → `CreateComposites` → durable attributeId receipt → `GetComposites` exact ID → exact fingerprint verification → VERIFIED.

Timeout after possible write: `UNKNOWN_OUTCOME`, no blind retry. Reconcile by deterministic Safe BIM name plus exact definition.

### 15 — Composite Roof
Tapir 1.5.9 `CreateRoofs` already accepts `structureType=Composite` and `compositeId`. `ApplyRoofStructure` selects `API_CompositeStructure` and assigns the composite. `GetDetailsOfElements` returns roof `structureType` and `compositeId`.

Therefore a future one-GUID native gable roof can also be multilayer without a second roof-specific composite mechanism.

### 16 — Composite Wall
Tapir 1.5.9 `CreateWalls`/`ModifyWalls` can select a Composite by exact ID. For Composite walls, the build-up and total thickness come from the Composite attribute; per-element `thickness` must not be treated as an independent way to resize the composite.

### 17 — Regulatory workflow
Desired high-level pipeline:

`SP / project requirement` → structured layer spec → validate required thickness/material evidence → resolve Building Materials → create/reuse verified Composite → create element referencing exact compositeId → element readback → composite readback → combined receipt.

The model should explicitly distinguish normative fact, designer assumption and project-library mapping.

### 18 — Production gate
No automatic Building Material invention from a material label. No Composite overwrite by name. No nearest-thickness selection unless a user explicitly requests approximation. Exact mode is the default.

## Example target

A requested roof build-up such as waterproofing + thermal insulation + vapor barrier + reinforced-concrete slab + finish becomes one verified Composite Roof attribute if those layers are intended to have constant thickness normal to the roof plane. The exact thickness/material values must come from the project's design/normative evidence, not from generic defaults.

## Sources

- Graphisoft C++ API `API_CompWallType`: https://archicadapi.graphisoft.com/documentation/api_compwalltype
- Graphisoft C++ API `API_CWallComponent`: https://archicadapi.graphisoft.com/documentation/api_cwallcomponent
- Graphisoft C++ API `API_WallType`: https://archicadapi.graphisoft.com/documentation/api_walltype
- Graphisoft C++ API `API_ShellBaseType`: https://archicadapi.graphisoft.com/documentation/api_shellbasetype
- Tapir 1.5.9 exact `AttributeCommands.cpp` (`GetComposites`, `CreateComposites`, `Get/CreateBuildingMaterials`).
- Tapir 1.5.9 exact `ExtendedElementCommands.cpp` / `ElementCommands.cpp` for Wall/Roof structure assignment/readback.
