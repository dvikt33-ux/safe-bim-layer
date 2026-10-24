# APA №2 | BUILD-01 | 9 applicable routes | 07Z

Reuse existing compiler / DynamicCommands / BIM Graph / SceneWriter / SQLite. Scores are expert priorities, not benchmarks. Source Tapir snapshot 1.5.10 (262 commands, NOT installed proof), upstream Tapir MIT; Graphisoft proprietary; safe-bim-layer license not confirmed.

| ID / score | Barrier → existing function / source | Exact fields / minimum linkage | Safe route → READY criterion |
|---|---|---|---|
| I01 / 99 | G0 APX identity → Windows loaded-module path + Get-FileHash; DynamicCommands.probe_runtime, PR162 | PID/port/PLN, APX SHA256; API.IsAddOnCommandAvailable.addOnCommandId | SOURCE → INSTALLED read-only. READY exact installed binary/schema/registration |
| I02 / 99 | G2 hosted openings → compiler preflight, PR162 | CreateWindows/Doors: ownerWallId.guid.$createdGuid, centerOffset, explicit width,height,sillHeight (writer-required despite optional schema) | SOURCE → OFFLINE negative cases. READY reject incomplete payload before WRITE |
| I03 / 98 | G2 added Slabs → compiler + SceneWriter, PR74/162 | CreateSlabs.slabsData[0]: floorIndex,level,thickness,polygonCoordinates; ModifySlabs.slabsWithDetails: elementId,structureType,thickness,buildingMaterialId | SOURCE → G2 authorization both commands → readback both stories |
| I04 / 97 | G2 Beams → existing NativeAdapter CreateBeams, PR162 | archicad_connected_components.adapters(['beam']) conditionally added to SAME SceneWriter; exact basic beam fields | SOURCE → OFFLINE adapter selection → INSTALLED runtime → LIVE only scoped; no new writer |
| I05 / 97 | G2 Columns → compiler preflight, PR162 | columnsData[0]: coordinates xyz, floorIndex, height,width,depth, pinned material | SOURCE → OFFLINE missing-field refusal → readback |
| I06 / 98 | G1 story/envelope → compile_authored_intent / BRIEF.resolve_stories, PR74/162 | nativeStoryBindings architecturalStoryId/nativeIndex/floorId/level; added Slab/Beam floorIndex and XYZ | SOURCE → OFFLINE with real fixture or INSTALLED read-only preflight; 2 pinned stories + DAG/plan hash |
| I07 / 82 | G3 packed create → PR126 DynamicCommands.execute_batch | 1–200 source-qualified items, existing writer; cannot replace slab CREATE→MODIFY | DEFER until single-element G2; per-GUID native readback |
| I08 / 76 | G3 groups → PR162 group strategy | verified Column/Beam sourceRef, floor, coordinates, exact group members | CONDITIONAL; no duplicate CloneNativeGroupV1; not required first building |
| I09 / 98 | G4 Save/Reopen/BREP → existing guarded persistence + per-database inventory | GetAllElements(databases), executionResultForDatabases; GetModelDumpV1 only if runtime registered | INSTALLED BREP NOT_FOUND; READY Save/GUI Close/Open, independent GUID/host/material/true BREP |

No route is INSTALLED/LIVE/ACCEPTED in this cycle. IFC/DXF/Hotlink/MEP/SAF/Publisher are independent lanes.
