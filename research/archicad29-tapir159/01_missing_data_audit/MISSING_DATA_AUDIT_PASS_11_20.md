# Missing-data audit — passes 11–20

Scope: second pass after `MISSING_DATA_AUDIT_PASS_01_10.md`. No live Archicad writes were performed.

Primary Tapir source baseline: tag `1.5.9` (`d0dbb11b13942e014661e1402b07958b70cd9dba`).

## Pass 11 — Modify* command semantics

Tapir 1.5.9 exposes direct GUID-targeted modify commands for Walls, Beams, Slabs, Columns, Windows, Doors, Morphs, Roofs, Meshes, Objects, Lamps, Texts and Labels.

Confirmed properties useful to Safe BIM:

- modifications target an existing element ID/GUID, not a geometric search result;
- implementations use Archicad change APIs inside undoable commands for the model change;
- response is per-item execution status, not a durable transaction receipt;
- a transport loss after `ACAPI_Element_Change*` is still an unknown-outcome situation.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

Integration rule: every Modify operation needs `beforeFingerprint` + exact target GUID + intended patch + `afterFingerprint`, and reconciliation must reread that GUID. Never blind-retry a Modify after a possible dispatch.

## Pass 12 — Hotlink nodes and instances

Tapir 1.5.9 adds:

- `CreateHotlinkNodes`,
- `CreateHotlinkInstances`,
- `ChangeHotlinkInstances`,
- `SaveAsModuleFile`,
- richer `GetHotlinks` data including node GUID, name/type and source location.

The registration text states that `CreateHotlinkNodes` returns an existing node instead of duplicating it when it already points at the same file. This is a useful idempotency property for the node layer. Instance placement is still a model mutation and must be treated separately.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/hotlink_instances.py

Missing before production integration: exact instance read-back contract, timeout reconciliation for instance creation, and proof that node source-path normalization is stable enough to use as an idempotency key.

## Pass 13 — libraries, GDL parts, Objects and Lamps

Tapir 1.5.9 adds `SetLibraries` and `AddLibraries`. `SetLibraries` intentionally allows libraries to be configured before opening a project so a missing-library dialog can be avoided. `AddLibraries` skips already-present local libraries. `GetAvailableLibraryParts` enumerates parts by type.

Objects and Lamps have dedicated create/modify support, plus GDL parameter read/write commands.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementGDLParameterCommands.cpp

Integration value: Safe BIM can eventually place deterministic library parts by explicit library-part identity + parameters instead of relying on whichever tool default is active.

Missing: canonical library-part identity policy across locale/library updates, and strict read-back subset for dimensions/rotation/parameters.

## Pass 14 — Zones and spatial semantics

`CreateZones` supports two distinct modes:

- automatic/reference-position zone,
- manual polygon zone with arcs and holes.

It also supports explicit name, number, category, stamp position/angle and floor. Tapir exposes `GetZoneBoundaries`, `GetRelationsOfElements`, `UpdateZones`, and room-image generation.

Source:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp

Integration value: room program validation, area adjacency checks, automatic zone recalculation, and room-aware documentation.

Safety distinction: `UpdateZones` is a broad recalculation operation with effects beyond a single newly-created GUID. Treat it as a separate global/project operation, never a hidden side effect of a local primitive.

## Pass 15 — Stairs and hierarchical elements

Tapir creates Stairs from a baseline and parameters. Archicad hierarchical elements expose subelements through `GetSubelementsOfHierarchicalElements` and `GetConnectedElements`; Tapir's own Favorites implementation documents that Stair/Railing/Curtain Wall memo contains geometry and therefore applies special restrictions when applying Favorites to existing hierarchical elements.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/FavoritesCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/get_3d_bounding_box_of_stairs.py

Conclusion: Stairs are feasible, but they should not be promoted using only a 3D bounding box. Verification needs baseline + key stair parameters + hierarchy/subelement evidence. Favorite application to a Stair must not be assumed geometry-neutral in generic code.

## Pass 16 — documentation pipeline

Tapir 1.5.9 exposes a broad documentation toolchain:

- Sections and Interior Elevations,
- associative dimensions including section presets and wall-thickness dimensions,
- Layouts and Layout subsets,
- Drawings and drawing updates/relinks,
- View Map creation/cloning/folders,
- view settings/rotation and 2D transformations,
- Text and Label creation/modification,
- autotext keys/names.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9/archicad-addon/Examples

Important exception: `ChangeDrawingLink` recreates the Drawing and deletes the old one; the output GUID is new. Therefore it cannot be modeled as an ordinary in-place modify. Safe BIM must represent it as a replace operation with explicit old/new ownership transition.

## Pass 17 — semantic metadata layer

Tapir provides full project-level building blocks for:

- custom properties and enum/expression definitions,
- classifications/systems/items,
- Favorites,
- element categories/properties,
- project info/autotext,
- Keynotes and keynote labels.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/PropertyCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ClassificationCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/FavoritesCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/KeynoteCommands.cpp

This can become Safe BIM's durable semantic marker layer, but marker/property data must augment exact GUID receipts rather than replace them as ownership proof.

## Pass 18 — IFC, BCF issues and revision information

Tapir supports:

- IFC file operations,
- IFC ID ↔ element lookup,
- IFC type/properties read-back,
- Archicad Issue creation/comments/attachments,
- BCF import/export,
- read-only revision issue/change/document revision data.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IssueCommands.cpp

Integration value: external QA/BCF workflow, cross-file identity via IFC IDs, issue-based human review gates.

Caution: IFC IDs are external/interoperability identities, not a replacement for Archicad GUID receipts inside a live mutation transaction.

## Pass 19 — MEP

Tapir 1.5.9 exposes read/write MEP operations on Archicad 28+:

- enumerate MEP elements/routes/ports/distribution systems,
- create routing elements,
- create Terminal/Accessory/Equipment/Fitting,
- modify routes,
- connect routes/elements, including route merges/splits/branch creation,
- read MEP preference tables.

Source:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/MEPCommands.cpp

Integration value is high for future engineering automation, but `ConnectMEPElements` is structurally high-risk because one command may create/merge/split multiple elements. It requires a purpose-built multi-object receipt/reconciliation design before any Safe BIM production enablement.

## Pass 20 — project-global operations

Tapir exposes global project mutations including `SetStories`, `SetGeoLocation`, libraries, window/view switching, project open/close/save and publish.

The 1.5.9 `SetStories` implementation is particularly important: it may insert/delete stories, rename them and change elevations. Its source comments explicitly note that deleting a story deletes the elements on it and that Archicad story elevation behavior is anchored on the active story.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp

Safe BIM rule: project-global state changes require a separate risk class from element-local writes. `SetStories`, project open/close, library replacement, publish and similar commands must never be silently invoked as helpers of geometry operations.

# Second audit after pass 20

## Gaps closed relative to pass 10

- Confirmed large 1.5.9 expansion in documentation, metadata, hotlinks, libraries, MEP, trims and Design Options.
- Confirmed that 1.5.9 Roof read-back is strong enough for a future strict single-plane verifier.
- Confirmed a concrete reason to update the pinned schema from 1.5.8.
- Confirmed project-global operations need a distinct safety class.
- Confirmed several replace/multi-object operations cannot reuse the single-element mutation template unchanged.

## Material gaps still open

1. Exact machine-readable 1.5.8 → 1.5.9 command/schema delta is not yet checked into this research branch.
2. Arc wall sign convention still needs proof.
3. Roof `pivotLine` positive-angle side still needs proof.
4. Mesh absolute-Z formula needs canonicalized implementation/tests in Safe BIM.
5. Arbitrary Morph body canonicalization needs a deterministic normal form.
6. Hotlink instance exact read-back and timeout reconciliation still need a dedicated audit.
7. MEP connect multi-object result/reconciliation needs a dedicated audit.
8. Design Options are not yet proven as a safe transaction sandbox; membership is metadata, not rollback.
9. Documentation commands need classification into element-local / replace / global operations.
10. AI orchestration and development-speed architecture have not yet been audited; those are handled in separate research files.

Conclusion: implementation should wait for the expansion/integration and AI/dev-speed audits. The remaining geometry unknowns are now narrow enough to be handled by explicit probes rather than broad guesswork.
