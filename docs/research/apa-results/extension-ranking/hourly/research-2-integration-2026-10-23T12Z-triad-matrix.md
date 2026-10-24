# APA №2 — 23.10.2026 12Z — 9 BUILD-01 triad scenarios

**Legend:** APA-WRITE = existing SceneWriter/SQLite; GH-WRITE = separate official Live Connection writer; READ = no native writes. All SOURCE_ONLY, no actual LIVE. Priority expert judgment 0–100, not benchmark.

| ID | Scenario / priority | Existing commands and direction | Gate and DONE |
|---|---|---|---|
| T01 | G0 story/attributes 100 | AC GetProjectInfo, GetStories, GetAddOnVersion, GetAttributesByType -> APA; GH Story Plane/Settings reads AC | READ; DONE exact installed APX SHA/command inventory, AC29 build5101, story index/levels; BLOCKED |
| T02 | Walls 100 | PR74 typed DAG -> CreateWalls(wallsData: floorIndex,zCoordinate,begCoordinate,endCoordinate,height,thickness) -> native GUID; GH Wall Design alternative | APA-WRITE OR GH-WRITE, never both on same object; DONE GUID/type/floor/material/geometry readback |
| T03 | Slabs 100 | CreateSlabs(slabsData) -> GUID -> ModifySlabs(slabsWithDetails: structureType,buildingMaterialId) -> readback; GH Slab Design alternative | Two APA mutation approvals; DONE native polygon/holes/thickness/material/floor after reopen |
| T04 | Columns/Beams 98 | CreateColumns(columnsData); existing NativeAdapter(CreateBeams) but run_project wires roof only; GH Beam/Column Design alternative | Beam APA route BLOCKED_ADAPTER_WIRING; DONE beam endpoints/profile/story/native GUID |
| T05 | Single-plane Roof 99 | CreateRoofs(roofsData: pivotLine,angle,structureType=Basic,buildingMaterialId) + existing roof adapter; GH Roof Design/Deconstruct | Separate writers; DONE SinglePlane slope/material/junction/BREP |
| T06 | Multi-plane Roof 97 | Tapir CreateRoofs default MultiPlane; Rhino NURBS/GH can produce Morph as fallback, not Roof | AC MultiPlane -> GH Deconstruct NOT_FOUND; native symmetric roundtrip NOT_FOUND |
| T07 | Doors/Windows 99 | Generated Wall GUID -> CreateDoors/CreateWindows(ownerWallId,centerOffset,sillHeight,width,height,favoriteName,libraryPartName); GH Wall Parameter -> Door/Window Design | DONE host GUID, actual GDL identity, floor/size/offset; GDL identity readback NOT_FOUND |
| T08 | AC -> GH -> Rhino 96 | AC Wall/Beam Parameter -> Deconstruct -> Extract Settings -> Send Changes -> GH/Rhino geometry | READ/reference; no automatic inverse GH sliders or same-GUID native write; AUTO_THREE_WAY NOT_FOUND |
| T09 | Save/Open and conflict 100 | Rhino Grasshopper Solver Disable/Enable; GH Synchronize FALSE/TRUE; APA journal/readback; GuardedSave/reopen | Neither toggle is transaction; DONE no duplicate/echo, native GUID/type/host/material/BREP and independent reopen; NOT_RUN |

## Connection procedure (not executed)
1. READ verify Archicad29 build5101, Rhino8 license/version, Tapir1.5.10 installed binary SHA/command registration, exact scratch PLN/port, official GH add-on AC29 build3000 (not AC30).
2. Only after installation approval: Graphisoft Windows AC29 build3000 installer; launch AC/Rhino8/GH, establish Live Connection, read real AC stories/composites/materials/Favorites; keep GH Synchronize FALSE for APA-owned elements.
3. Strict single-writer profile: GH geometry/preview/AC Deconstruct, native mutations solely PR74 -> BIM Graph -> SceneWriter/SQLite -> Tapir. Automatic arbitrary GH output -> PR74 typed plan NOT_FOUND, no code written.
4. Owner-approved LIVE only: scratch PLN and plan hash; phased native CREATE; readback; GuardedSave, GUI close/reopen, independent BREP and host verification; stop on UNKNOWN, never blindly repeat CREATE.
5. Do not treat GH Synchronize FALSE as rollback. Do not use Morph/3DM Hotlink to claim native Wall/Roof. Automatic three-way conflict resolution NOT_FOUND.

Sources: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json ; https://github.com/dvikt33-ux/safe-bim-layer/issues/192
