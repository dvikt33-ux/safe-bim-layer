# Missing-data audit — passes 01–10

Scope: Safe BIM on Archicad 29 with Tapir Additional JSON Commands 1.5.9. No live writes were performed for this audit.

## Evidence baseline

- Research branch baseline: `1d9c58f05b3c6c23f9443766c4099c3274cdbf46`.
- Current production/offline house work being audited is based on `c6ab4749e8784cc65170167d166daa6cc219a931`.
- The repository still pins `tapir-1.5.8.json` in `safe_bim_house_primitives.py`, while prior live capability evidence in `bimexec/examples/capability_matrix.example.json` records Tapir add-on version `1.5.9`.
- Tapir tag `1.5.9` points to commit `d0dbb11b13942e014661e1402b07958b70cd9dba`.

Primary sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9
- https://github.com/dvikt33-ux/safe-bim-layer/blob/c6ab4749e8784cc65170167d166daa6cc219a931/safe_bim_house_primitives.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/c6ab4749e8784cc65170167d166daa6cc219a931/bimexec/examples/capability_matrix.example.json

## Pass 01 — runtime/schema version contract

### Confirmed

Safe BIM currently validates future house primitives against `tapir-1.5.8.json`, not the actually installed 1.5.9 contract. Tapir exposes `GetAddOnVersion`, so runtime version detection is available and should become part of preflight.

### Missing data / required action

1. Import/pin the exact 1.5.9 command schema in the research branch before implementation work.
2. Diff 1.5.8 → 1.5.9 at command and field level.
3. Add a runtime gate: `GetAddOnVersion == expected schema version` before any production write whose verification depends on version-specific fields.
4. Do not silently accept a newer/older add-on under a mismatched pinned schema.

Risk if omitted: schema-valid payload/read-back expectations may describe the wrong version.

## Pass 02 — Arc Wall contract

### Confirmed

- Tapir `CreateWalls` uses `arcAngle` directly for the Archicad wall angle.
- `arcAngle` is radians.
- With explicit `floorIndex`, wall `zCoordinate` is written as the wall bottom offset relative to that story; this is consistent with the already live-proven wall Z contract in Safe BIM.
- Archicad `API_WallType` documents `bottomOffset` as base height relative to floor level, `height` relative to bottom, and `angle` in radians.
- Tapir read-back includes wall geometry fields sufficient to compare chord endpoints, Z, height, thickness, and angle.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp
- https://archicadapi.graphisoft.com/documentation/api_walltype

### Still missing

The sign convention required to choose the intended side of a curved wall between a fixed chord (`+angle` versus `-angle`) is not established by the sources reviewed so far. Do not infer it from unrelated `PolyArc` rules.

Minimal eventual evidence: one isolated live arc write, exact GUID read-back, and geometric side check. No automatic opposite-sign retry.

## Pass 03 — Mesh vertical semantics

### Confirmed

Tapir 1.5.9 `CreateMeshes` separately assigns:

- `floorIndex` → home story,
- `level` → `element.mesh.level`,
- each 3D polygon coordinate → mesh polygon/memo geometry.

The official Archicad mesh model treats the mesh base/reference plane and per-vertex mesh elevations as distinct values. Tapir 1.5.9 supports read-back/modification of mesh `level`, polygon XYZ, holes, polygon arcs, sublines, skirt and ridge/display data.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/test_modify_meshes.py
- https://archicadapi.graphisoft.com/documentation/api_meshtype
- https://archicadapi.graphisoft.com/documentation/acapi_element_getmemo

### Confirmed Safe BIM gap

`prepare_flat_mesh` in `c6ab474` defaults polygon vertex Z to the same numeric value as `level`. That is not a justified representation of a flat mesh whose absolute surface elevation equals the base/reference level; the two quantities are semantically separate and can compound.

### Required action

Replace the current `requested_level/requested_vertex_z` ambiguity with an explicit contract containing:

- story elevation,
- mesh base-plane offset (`level`),
- per-vertex relative Z values,
- expected absolute vertex Z.

For a flat surface exactly on the mesh reference plane, per-vertex offsets should be zero unless source evidence for a different contract is obtained.

## Pass 04 — Morph geometry and read-back

### Confirmed

Tapir 1.5.9 materially exceeds the old box-only assumption:

- `CreateMorphs` supports arbitrary `body` geometry (vertices, polygons, holes, edge behavior and per-face surface overrides).
- `ModifyMorphs` can replace body geometry.
- `GetDetailsOfElements` can return Morph transform/origin/axes and full body geometry.
- Tapir's box shortcut builds a cuboid body from dimensions; arbitrary bodies are not limited to the shortcut.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/create_modify_delete_morph.py
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp

### Confirmed Safe BIM gap

The current offline Morph assessor is designed around synthetic echo fields such as requested size/bottom/top rather than the actual 1.5.9 full body read-back contract. It should verify transform + body vertices/polygons (or a strict body fingerprint), not fields Tapir does not promise.

### Missing data

Need exact 1.5.9 `MorphBody` schema copied into the pinned contract and canonicalization rules for vertex/polygon ordering before strict equivalence is declared. Bounding-box equivalence alone is insufficient for arbitrary Morph ownership/geometry verification.

## Pass 05 — Roof contract/read-back

### Confirmed

Tapir 1.5.9 has first-class roof read-back. Its own `roof_details.py` example creates both multi-plane and single-plane roofs and reads them back. Example output confirms:

- common: `roofClass`, `structureType`, `thickness`, `level`/`zCoordinate`, polygon outline and holes;
- single-plane: `angle`, `pivotLine`;
- multi-plane: `eavesOverhang`, `levels`, `pivotPolygonOutline`.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/roof_details.py
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Test/ExpectedOutputs/roof_details.py.output
- https://archicadapi.graphisoft.com/documentation/api_polyroofdata

### Development consequence

The old `SCHEMA_ONLY` conclusion for all Roof verification is obsolete under 1.5.9. A single-plane gable-half can be strongly verified by exact GUID using `roofClass + level + angle + pivotLine + polygonOutline + structure/thickness`.

For the test house, two separately created single-plane roofs are a better fit for Safe BIM than one opaque multi-plane gable attempt because each physical dispatch can own one GUID and one independent receipt.

### Still missing

Need an exact source-level proof of which side of the directed `pivotLine` rises for a positive roof `angle`, or one isolated live probe. Do not infer ridge direction until proven.

## Pass 06 — creation defaults and Favorites

### Confirmed

Tapir 1.5.9 `CreateElementsCommandBase` supports per-item `favoriteName`. The implementation:

1. snapshots tool defaults,
2. applies a named Favorite when requested,
3. starts every item from fresh defaults,
4. restores defaults after the command.

This is important because Tapir comments document a live-proven failure mode where values from one create item could otherwise bleed into the next (for example arc/slant values).

Tapir also exposes Favorite read/create/update/apply commands; Archicad Favorites can include element settings, memo, properties, classifications and categories.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/FavoritesCommands.cpp
- https://archicadapi.graphisoft.com/documentation/api_favorite

### Integration opportunity

Favorites can become a deterministic style/profile/template input layer above primitive geometry. Safe BIM should record `favoriteName` and a resolved Favorite fingerprint/version surrogate in the prepared contract. Never rely on mutable global tool defaults without a read-back/fingerprint.

## Pass 07 — element notifications

### Confirmed

Tapir 1.5.9 exposes `SetElementNotificationClient` / removal. It can POST local HTTP notifications for new, changed, deleted, reserved and released elements. The implementation uses Archicad element observers/new-element notifications and reservation-change notifications.

Source:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NotificationCommands.cpp
- https://archicadapi.graphisoft.com/documentation/notification-manager

### Integration opportunity

Notifications can reduce polling and detect external/manual changes that invalidate receipts or cached read-back. However, they must be treated as hints/events, not proof of successful ownership or write completion:

- delivery is best-effort HTTP;
- Tapir's sender catches communication exceptions;
- event arrival/order must not replace exact GUID read-back;
- callback messages can be missed if listener is unavailable.

Recommended Safe BIM role: cache invalidation / external-change alarm / trigger for re-read, never APPLIED/DONE evidence.

## Pass 08 — Teamwork reserve/release

### Confirmed

Tapir exposes `ReserveElements` and `ReleaseElements`; it calls Archicad Teamwork APIs with dialogs disabled and reports conflicts. Official API documentation confirms reservations are non-undoable Teamwork data-structure modifiers and can return conflicting users.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/TeamworkCommands.cpp
- https://archicadapi.graphisoft.com/documentation/acapi_teamworkcontrol_reserveelements
- https://archicadapi.graphisoft.com/documentation/acapi_teamworkcontrol_releaseelements

### Integration consequence

This is useful only for actual Teamwork projects; it is not a replacement for the existing Safe BIM single-flight/OS lock in solo PLN work. If later integrated, reservation itself needs its own state transition and reconciliation policy because it is non-undoable and independent of model geometry writes.

## Pass 09 — Design Options (Archicad 29)

### Confirmed

Tapir 1.5.9 exposes read and write access to Archicad 29 Design Options, including:

- list options and option sets,
- list combinations and active options,
- get elements in options,
- get option for elements,
- create option sets,
- create options,
- create combinations,
- set active options in combinations,
- move elements to/from design options.

The write commands use Archicad 29 `DesignOptionManager` and most are wrapped in `ACAPI_CallUndoableCommand`.

Source:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/DesignOptionCommands.cpp

### Integration opportunity

Design Options are a strong candidate for a future Safe BIM experimentation/sandbox layer: alternatives can be segregated from the main model instead of being mixed into production geometry.

### Missing data

Before using them as a safety sandbox, we still need to prove whether creation/move operations can be reconciled deterministically after timeout and whether the option membership read-back is sufficient to distinguish a half-applied multi-item command. Prefer one option/set/element move per physical dispatch until proven otherwise.

## Pass 10 — Solid Element Operations and trims

### Confirmed

Tapir 1.5.9 exposes:

- create/remove/query Solid Element Operation links,
- trim elements by roof/shell,
- query existing trims.

The implementation exposes target/operator GUIDs, operation type and flags for solid links, which provides a direct relationship read-back suitable for verification.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/SolidElementOperationCommands.cpp
- https://archicadapi.graphisoft.com/documentation/element-manager

### Integration opportunity

This can extend Safe BIM beyond primitive placement into deterministic boolean/trim relationships. Relationship operations should be modeled as their own receipt type (`targetGuid`, `operatorGuid`, operation/trim type, flags) and reconciled by relationship read-back, not by geometry similarity.

## Audit after pass 10

### Data gaps that remain material

1. Exact 1.5.9 schema must be pinned into the research branch and mechanically diffed against 1.5.8.
2. Arc-wall sign convention remains unresolved.
3. Single-plane roof positive-angle side relative to directed `pivotLine` remains unresolved.
4. Mesh Z contract needs a source-level canonical formula and corresponding Safe BIM builder correction.
5. Morph canonical body comparison rules need specification for arbitrary bodies.
6. Modify command timeout semantics are not yet audited across wall/slab/mesh/morph/roof/object/label/text.
7. Hotlink creation/instance identity and timeout reconciliation need audit.
8. Library/GDL object placement and Favorites interaction need audit.
9. Zone, stair, beam/column advanced geometry need a capability/read-back audit.
10. Navigator/layout/drawing/documentation, IFC/issues/revisions/keynotes/MEP remain outside this first pass.

Conclusion: the research is not complete. A second 10-pass block is required before implementation recommendations are considered stable.
