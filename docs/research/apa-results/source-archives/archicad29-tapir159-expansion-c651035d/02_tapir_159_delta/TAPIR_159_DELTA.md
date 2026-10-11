# Tapir 1.5.9 delta relevant to Safe BIM

Source compare: `ENZYME-APD/tapir-archicad-automation` tag `1.5.8` (`ce033d6bdcc90b538b3c5f7ab62f676099b96823`) → tag `1.5.9` (`d0dbb11b13942e014661e1402b07958b70cd9dba`). GitHub compare reports 258 commits ahead.

Canonical compare:
https://github.com/ENZYME-APD/tapir-archicad-automation/compare/1.5.8...1.5.9

## Why this matters

`safe_bim_house_primitives.py` currently pins `tapir-1.5.8.json`, while the user's Archicad 29 installation runs Tapir 1.5.9. 1.5.9 is not a cosmetic release: major command source and schema files changed substantially. The compare includes roughly:

- `ElementCreationCommands.cpp`: +1167 / -23
- `ElementCommands.cpp`: +369 / -74
- `ProjectCommands.cpp`: +1188 / -101
- `ExtendedElementCommands.cpp`: +241 / -26
- `SolidElementOperationCommands.cpp`: +295
- `CommonSchemaDefinitions.json`: +873 / -60
- generated `command_definitions.js`: +730 / -30

Safe BIM must not use 1.5.8 as its authoritative contract for 1.5.9-only behavior.

## High-value 1.5.9 additions / changes

### 1. Roof details became verifiable

1.5.9 adds/expands Roof details returned by `GetDetailsOfElements`, and ships `roof_details.py` plus expected output. Single-plane roofs expose enough geometry for strict post-write verification: roof class, level/Z, angle, pivot line, polygon geometry, structure and thickness. Multi-plane roofs expose levels, overhang and pivot polygon data.

Consequence: the old global `Roof = SCHEMA_ONLY` classification is too pessimistic for 1.5.9. Single-plane roofs are candidates for strict receipt/read-back verification after offline implementation and one semantic probe.

### 2. Mesh became substantially richer

1.5.9 Mesh creation/modify supports and documents:

- polygon XYZ,
- polygon arcs,
- holes,
- leveling sublines,
- skirt type/level,
- ridge mode,
- plan line visibility and pens/line type.

This is enough for terrain modeling beyond a flat rectangle. It also makes the exact distinction between mesh base `level` and per-vertex `meshPolyZ` important for Safe BIM.

### 3. Morph supports arbitrary bodies

1.5.9 contains explicit arbitrary Morph body construction and body read-back, rather than limiting the useful contract to a box shortcut. This opens deterministic freeform geometry where a normal form can be defined for vertices/polygons/holes/material overrides.

### 4. Hotlink workflows expanded

New 1.5.9 project commands include creation/change of hotlink nodes/instances and saving elements/selection as `.mod`. `CreateHotlinkNodes` is explicitly designed to return an existing node when the same source file is already represented, reducing duplicate-node risk.

### 5. Libraries can be configured before project use

1.5.9 adds `SetLibraries` / `AddLibraries`. The command registration explicitly calls out avoiding missing-library dialogs by setting libraries before opening a dependent file.

This is valuable to Safe BIM because dialogs are a fail-closed blocker for automation.

### 6. Text/Label modification and autotext

1.5.9 adds `ModifyTexts`, `ModifyLabels`, `GetAutoTextKeys` and `GetAutoTextName`, enabling a stronger documentation pipeline and dynamic labels based on project/element properties.

### 7. Trim relations became first-class

1.5.9 adds `TrimElements`, `RemoveElementTrims`, `GetElementTrims`. These provide relationship read-back rather than relying on visual geometry changes.

### 8. More deterministic creation defaults

The 1.5.9 create base explicitly re-fetches defaults for each item and supports per-item `favoriteName`, with snapshot/restore of tool defaults. Source comments record live failures where omitted fields otherwise inherited values from the previous item (e.g. arc/slant). This is a major correctness improvement for batched create calls.

Safe BIM should still prefer one physical mutation per resumable step for ownership/reconciliation, but the underlying Tapir behavior is now less prone to cross-item parameter bleed.

### 9. Documentation and coordination surface expanded

The release adds/examples/changes around:

- associative dimensions and dimension read-back,
- Sections / Interior Elevations,
- hotlinks,
- layouts/drawings/view settings,
- BCF issues and revision data,
- Keynotes,
- MEP,
- Favorites,
- attributes/properties/classification.

### 10. Grasshopper components expanded in parallel

The 1.5.8→1.5.9 compare shows many Grasshopper component changes matching the JSON API additions. This is useful as a secondary usage example/source of field semantics, but it is not a separate safety backend. The authoritative write path for Safe BIM remains Tapir JSON + exact read-back.

## Compatibility rules for Safe BIM

1. Pin a 1.5.9 schema snapshot in the repo before enabling 1.5.9-specific operations.
2. Preflight `GetAddOnVersion` before writes.
3. Store `tapirVersion` in the prepared contract and durable receipt.
4. Refuse production writes when runtime version and certified schema version differ unless an explicit compatibility entry exists.
5. Keep operation-specific verifiers versioned where 1.5.9 read-back differs from 1.5.8.
6. Do not treat a successful 1.5.8 test as proof of 1.5.9 semantics or vice versa.

## Remaining delta work

A machine-readable full command/field diff should be generated from the 1.5.8 and 1.5.9 generated command/common-schema definitions. The current research has established enough high-value deltas to block implementation against the old schema, but a full generated diff will improve maintenance and CI drift detection.
