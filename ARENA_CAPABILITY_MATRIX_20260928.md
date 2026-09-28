# ARENA CAPABILITY MATRIX — Archicad 29 API × Tapir 1.5.9 × Safe BIM

Date: 2026-09-28. Companion to `ARENA_FULL_SYSTEM_AUDIT_20260928.md`. Grades: LIVE_CONFIRMED (user's committed live docs, not reproduced by Arena) / STATIC_CONFIRMED (source or official docs read by Arena) / INFERRED / UNRESOLVED_LIVE_REQUIRED (→ `LT-nn` in `ARENA_LIVE_TEST_PLAN_20260928.md`) / CONTRADICTED.

Columns: **API** = official Archicad 29 C++ API (graphisoft.github.io/archicad-api-devkit); **Tapir 1.5.9** = tag `1.5.9` (`d0dbb11`), 250 commands — full generated inventory in `audit/arena-full-system-audit-20260928/TAPIR_1.5.9_COMMAND_INVENTORY.md`; **v0.1** = `safe_bim_layer.py` on the audit branch; **Arena rt** = `arena/tapir159-compat-geometry-c6ab474`.

Rule reminder: a "yes" in the API column is not a Tapir capability; a "yes" in the Tapir column is not live behaviour.

## 1. Session / safety primitives

| Capability | API | Tapir 1.5.9 | v0.1 | Arena rt | Grade | Notes / experiment |
|---|---|---|---|---|---|---|
| Add-on version handshake | — | `GetAddOnVersion` | not called | not called | STATIC_CONFIRMED gap | required before first write |
| Project identity | — | `GetProjectInfo.projectPath`, `GetProjectInfoFields`/`SetProjectInfoField` (sandbox token) | none | path equality guard | STATIC_CONFIRMED | add token check |
| Current window type | `ACAPI_Window_*` | `GetCurrentWindowType` | — | used for modal detection | STATIC_CONFIRMED | |
| Current database query | `ACAPI_Database_GetCurrentDatabase` | **none** (`GetExecutionContext` proposed) | — | — | STATIC_CONFIRMED gap | Tapir PR |
| Command allowlist / envelope check | — | — | none | none | STATIC_CONFIRMED gap | P0 |
| Undo from JSON | `ACAPI_CallUndoableCommand` scopes | **no Undo command** | — | — | STATIC_CONFIRMED | compensation only |
| Atomic batch | lambda error → rollback | only `TrimElements` (and single-item commands); create/modify executors always commit partials | — | — | STATIC_CONFIRMED | Tapir `atomic` flag; LT-A2 |
| Modal dialog detection | — | transport timeout / error | — | `ModalStateError` | STATIC_CONFIRMED | |
| Open/Close/Save project | `ACAPI_ProjectOperation_*` | `OpenProject`, `CloseProject`, `SaveProject` | `cleanup_copy` unchecked open → mass delete | not used | STATIC_CONFIRMED **P0** | delete `cleanup_copy` |

## 2. Element creation / modification (subset relevant to the audit)

| Element / operation | API | Tapir 1.5.9 | Safe BIM (v0.1 / Arena rt) | Grade | Notes |
|---|---|---|---|---|---|
| Wall (basic/composite/profile) | yes | `CreateWalls` (`thickness` required; `structureType`, `compositeId`, `profileId`), `ModifyWalls` | v0.1 `create_wall`; Arena rt wall loop/plinth with readback | LIVE_CONFIRMED (R4/W3) | composite: `thickness` must equal skin sum |
| Window/Door | yes; requires current DB = floor plan (#532) | `CreateWindows`/`CreateDoors` switch DB internally | v0.1 room openings in `walls[0]` only | STATIC_CONFIRMED | |
| Slab | yes | `CreateSlabs`, `ModifySlabs` | v0.1 | LIVE_CONFIRMED (R4) | **`Get3DBoundingBoxes` on Slab may SIGSEGV in 1.5.9** (LT-F3) |
| Beam / Column | yes | `CreateBeams`, `CreateColumns`, modify | — | LIVE_CONFIRMED (R4; beam profile DIFF) | `circleBased` beam missing in 1.5.9 |
| Roof multi-plane / single-plane | yes | `CreateRoofs` (uniform `levels`, or `pivotLine+angle`), `ModifyRoofs` | — | LIVE_CONFIRMED (W4) | |
| Roof per-edge gable (one GUID) | yes (`API_PivotPolyEdgeData`/`API_RoofSegmentData.angleType`) | **no** | — | STATIC_CONFIRMED gap | Tapir PR spec in audit §6 |
| Shell (extruded/revolved/ruled) | yes (`API_ShellType`, `API_RevolvedShellData`) | **no `CreateShells`** | — | STATIC_CONFIRMED gap | Tapir PR |
| Stair | yes | `CreateStairs` (baseline, risers, treads, favorite) | — | STATIC_CONFIRMED (ledger omitted it) | detail readback unsupported |
| Mesh | yes | `CreateMeshes`, `ModifyMeshes` | — | LIVE_CONFIRMED (R4) | |
| Morph box / arbitrary body | `ACAPI_Body_*` | `CreateMorphs` (`size` xor `body`; `floorIndex`; **no `layerIndex`**) | — | LIVE_CONFIRMED (W7) | layer via `SetDetailsOfElements` |
| Morph body replace | `ACAPI_Element_Change` + memo | `ModifyMorphs(body)` | — | LIVE_CONFIRMED defect (W7D `isClosed:false`) | LT-B1/B2 |
| Morph rotation | tmx | `ModifyMorphs.rotationDegreesZ` **wrong axis/pivot**; `xAxis/yAxis/zAxis` correct | — | STATIC+LIVE CONFIRMED | forbid parameter |
| Morph edge type (all edges) | `ACAPI_Element_ChangeMorphEdgeType` | sets `elem.morph.edgeType` via Create/Change only → discarded (per Tapir comment) | — | CONTRADICTED comment / STATIC gap | Tapir PR; LT-B3 |
| Morph per-edge fillet/chamfer | no API | no | — | STATIC_CONFIRMED | display overrides only |
| Destructive Morph boolean | `ACAPI_Element_SolidOperation_Create` (deletes operands, returns results) | **no** | — | STATIC_CONFIRMED gap | Tapir PR; lineage record |
| Objects / Lamps / Texts / Labels | yes | `CreateObjects`, `CreateLamps`, `CreateTexts` (`favoriteName`, `style.fontIndex`), `CreateLabels`, modify | — | LIVE_CONFIRMED (R4) | `ModifyTexts` height-only ignored in 1.5.9 |
| 2D: Line/PolyLine/Arc/Circle/Spline/Hatch/Hotspot | yes | all present | — | LIVE_CONFIRMED (R4; `PolyLine` spelling; hatch duplicate closing point) | |
| Zones | yes | `CreateZones`, `UpdateZones`, `GetZoneBoundaries` | — | LIVE_CONFIRMED (R4) | |
| Move / Rotate with copy | yes | `MoveElements{copy}`, `RotateElements{copy}` (2D rotation) | — | STATIC_CONFIRMED | arrays at planner level; no scale |
| Delete | yes | `DeleteElements` (batch, partial commit) | v0.1 mass delete | STATIC_CONFIRMED | compensation must be verified |
| Layer assignment on create | yes | most creates: `layerIndex`; `CreateMorphs`: no | — | STATIC_CONFIRMED | |
| Favorites | `ACAPI::Favorite` | `GetFavoritesByType`, `CreateFavoritesFromElements`, `ApplyFavoritesToElements`, `Import/ExportFavorites` | — | STATIC_CONFIRMED | font-by-role route |

## 3. Openings / SEO / trims / collisions

| Capability | API | Tapir 1.5.9 | Grade | Notes |
|---|---|---|---|---|
| Rectangular Opening | `OpeningDefault::Place/PlacePolygonal` | `CreateOpenings{ownerElementId, basePoint, width, height}` | LIVE_CONFIRMED present (R4; readback unsupported) | |
| Circular / polygonal Opening | `ShapeType` Rectangular/Circular; `PlacePolygonal` = custom polygon (official) | **no** | STATIC_CONFIRMED gap; Tapir "extents only" inference CONTRADICTED as general | LT-C4 |
| Opening readback | `ACAPI::Element::Opening::GetOpeningGeometry` | `GetDetailsOfElements` **unsupported** for Opening | LIVE_CONFIRMED (R4) | existence via `GetElementsByType` |
| SEO links | `ACAPI_Element_SolidLink_Create` | `CreateSolidElementLinks`, `RemoveSolidElementLinks`, `GetSolidElementLinks` | LIVE_CONFIRMED (W8, link-level) | evaluated proof missing |
| Roof/Shell trim | `ACAPI_Element_Trim_*` | `TrimElements` (atomic), `RemoveElementTrims`, `GetElementTrims` | STATIC_CONFIRMED | |
| Evaluated collision test | `ACAPI_Element_GetCollisions` | `GetCollisions{volumeTolerance, performSurfaceCheck, surfaceTolerance}` | STATIC_CONFIRMED existence; SEO-awareness UNRESOLVED | LT-C1 |
| Quantities (volume/area) | `ACAPI_Element_GetQuantities` | not exposed; built-in properties via `GetAllProperties` + `GetPropertyValuesOfElements` | STATIC_CONFIRMED existence; SEO-awareness UNRESOLVED | LT-C2 |
| Merge elements | `ACAPI_Element_Merge_Elements` | no | STATIC_CONFIRMED | not needed |

## 4. Verification primitives

| Primitive | Mechanism | Grade | Safe for which types in 1.5.9 |
|---|---|---|---|
| Typed readback | `GetDetailsOfElements` | LIVE_CONFIRMED | Wall, Beam, Slab, Zone, Column, Door, Window, Label, Text, Object, Lamp, Detail, Worksheet, PolyLine, Hatch, Line, Arc, Circle, Hotspot, Spline, CurtainWall(+Segment/Panel/Frame), Mesh, Drawing, Morph, Roof, Hotlink. **Not** Opening, Stair, Shell, Skylight, Dimensions, Railing (returns `error: Not yet supported element type`) |
| Existence in a database | `GetElementsByType`/`GetAllElements` with `databases:[…]` | STATIC_CONFIRMED | all |
| AABB | `Get3DBoundingBoxes` (`CalcBounds`; Roof/Zone/Stair via ModelAccess) | STATIC_CONFIRMED crash risk for Slab (#686) | never Slab in 1.5.9; prefer analytic AABB from readback |
| Evaluated overlap | `GetCollisions` | UNRESOLVED_LIVE_REQUIRED (LT-C1) | all 3D |
| Quantity | built-in property values | UNRESOLVED_LIVE_REQUIRED (LT-C2) | construction elements |
| ModelAccess deep check | `EvaluateElements3D` (proposed PR; precedent `AccumulateSolidBodyBounds`) | STATIC_CONFIRMED feasible | all with 3D model |
| Section-generated elements + owners | `GetSectionElements` | STATIC_CONFIRMED | section/elevation/IE DBs |
| Relations | `GetConnectedElements`, `GetRelationsOfElements`, `GetSubelementsOfHierarchicalElements` | STATIC_CONFIRMED | |
| Preview image | `GetElementPreviewImage`, `GetRoomImage` | STATIC_CONFIRMED | human review only |

## 5. Databases / windows / navigator / documents

| Capability | Tapir 1.5.9 | Grade | Notes |
|---|---|---|---|
| Switch front window + current DB | `ChangeWindow{windowType, storyIndex|databaseId}` or `{navigatorItemId}` (GoToView, AC27+) | STATIC_CONFIRMED | always changes the window |
| Current DB switch without window change | internal only (`ExecuteActionForEachDatabase`, `SwitchCurrentDatabaseToFloorPlan`) — exposed via `databases` param on list commands | STATIC_CONFIRMED | Tapir PR for write executors |
| Database ids | `GetDatabaseIdFromNavigatorItemId`; FloorPlan/3D fixed GUIDs, others `databaseUnId` | STATIC_CONFIRMED | durable identity rule in audit §E |
| Navigator tree / views | `GetNavigatorItemTree`, `CreateViewsInViewMap`, `CloneProjectMapItemToViewMap`, `Get/SetViewSettings`, `GetModelViewOptions`, `SetViewRotation`, `Set3DCutPlanes`, `FitInWindow`, `CreateSections`, `CreateInteriorElevations`, `Move/Rename/DeleteNavigatorItems` | STATIC_CONFIRMED | `sourceNavigatorItemId` only post-1.5.9 |
| Rebuild | `RebuildView{regenerate}` (current view) | STATIC_CONFIRMED | |
| Dimensions | `CreateAssociativeDimensions`, `CreateAssociativeDimensionsOnSection` (8 presets; creates in current DB), `CreateWallThicknessDimensions`, `GetDimensionData` | STATIC_CONFIRMED | ghost-GUID check via `GetElementsByType(databases)` (LT-E3) |
| Layouts / drawings / publishing | `CreateLayout`, `CreateLayoutSubset`, `CreateDrawings`, `ChangeDrawingLink`, `UpdateDrawings`, `Get/SetLayoutSettings`, `GetLayoutCustomScheme`, `PublishPublisherSet`, `PrintView` | STATIC_CONFIRMED | Drawing `isCutWithFrame` flag-only ignored in 1.5.9 |
| Stories | `GetStories`, `SetStories` | LIVE_CONFIRMED (R0) | |

## 6. Attributes

| Attribute | Create | Read | Grade | Notes |
|---|---|---|---|---|
| Layer / Layer combination | `CreateLayers`, `CreateLayerCombinations` | `GetLayers`, `GetLayerCombinations` | STATIC_CONFIRMED | |
| Line type | `CreateLines` (Solid/Dashed/Symbol, `dashItems`, `lineItems`, `scaleWithPlan`) | `GetLines` | STATIC_CONFIRMED | |
| Fill | `CreateFills` | `GetFills` | STATIC_CONFIRMED | |
| Pen table | `CreatePenTables` (`sourceAttributeId`, `pens[]`, active flags) | `GetPenTables` | STATIC_CONFIRMED | |
| Building material | `CreateBuildingMaterials` | `GetBuildingMaterials`, `GetBuildingMaterialPhysicalProperties` | LIVE_CONFIRMED (trusted BM GUID) | |
| Composite | `CreateComposites` (skins, separators = skins+1, `useWith`, overwrite) | `GetComposites` | LIVE_CONFIRMED (W3 0.287 m) | |
| Profile | `CreateProfiles` (`sourceAttributeId` and/or `newSkins` AC27+, `skinOverrides`, type flags) | `GetProfiles` | STATIC_CONFIRMED | R4 beam DIFF with profile |
| Surface | `CreateSurfaces` | `GetSurfaces` | STATIC_CONFIRMED | |
| Zone category / MEP system | `CreateZoneCategories`, `CreateMEPSystems` | `GetZoneCategories`, `GetMEPSystems` | STATIC_CONFIRMED | |
| Font | **none** (`AttributeType` enum has no Font) | none | STATIC_CONFIRMED gap | favorites route; `GetFonts` PR |
| Delete | `DeleteAttributes` | — | STATIC_CONFIRMED | indices shift → GUIDs only |

## 7. Library / reuse

| Capability | Tapir 1.5.9 | Grade | Notes |
|---|---|---|---|
| List / attach / reload libraries | `GetLibraries`, `AddLibraries`, `SetLibraries` (replaces local set), `ReloadLibraries` | STATIC_CONFIRMED | use `AddLibraries` only |
| Embedded library add | `AddFilesToEmbeddedLibrary` | STATIC_CONFIRMED | project-local |
| Library parts | `GetAvailableLibraryParts{filterByTypeId}` | STATIC_CONFIRMED | resolve per session |
| Elements → reusable module | `SaveAsModuleFile{moduleFilePath, elements}` (front window must be plan/section/elevation/detail) | STATIC_CONFIRMED | assemblies route |
| Place module in another project | `CreateHotlinkNodes` (dedupe by path, AC26+), `CreateHotlinkInstances`, `ChangeHotlinkInstances`, `GetHotlinks` | STATIC_CONFIRMED | LT-J1 |
| Elements → GSM | none | STATIC_CONFIRMED gap | deferred |

## 8. Post-1.5.9 items (present in research baseline `b1dc828`, ABSENT live)

`ImportClassificationsXml`, `ImportPropertiesXml`, `UpdateClassificationItems`, `UpdateClassificationSystems`, `UpdatePropertyGroups`; behavioural: Slab `Get3DBoundingBoxes` crash fix (#686), Label-on-Slab crash fix, `ModifyTexts` height-only, Drawing `isCutWithFrame` flag-only (#651), Beam `circleBased`, navigator `sourceNavigatorItemId`. Any Safe BIM design relying on these must gate on `GetAddOnVersion ≥ 1.5.10` (once released).
