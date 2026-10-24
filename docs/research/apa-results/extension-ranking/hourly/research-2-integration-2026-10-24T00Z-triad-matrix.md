# APA №2 — 00Z — девять операций BUILD-01, только SOURCE
Общий порядок: выбор owner/программы → изменение → freeze → направленная передача → GUID/BIM-type/параметры/материалы/BREP readback → Save/Close/Reopen → compare → rollback. Ни один маршрут не испытан LIVE в этом проходе.

| ID | Готовый инструмент и направление | Контроль и ГОТОВО | Статус |
|---|---|---|---|
| 01 | Rhino8 Query Model Objects → GH Model Object → замороженный JSON (jSwan candidate) → PR74 | .3dm/.gh SHA, Rhino object IDs, units, schema/list/null/JSON hash, повторное открытие | SOURCE_CANDIDATE |
| 02 | AC29 GetProjectInfo/GetStories/GetAddOnVersion/command registration → G0 | actual port, PLN path/name/hash, floorId/index/level, APX SHA; unknown→STOP | BLOCKED_RUNTIME |
| 03 | GH curves → PR74 CreateWalls → native Wall | Relative wall Z, floorIndex, GUID/type/story/material, junction BREP after reopen | SOURCE_ONLY |
| 04 | GH polygon+holes → PR74 CreateSlabs / qualified ModifySlabs | Absolute slab level, all holes retained, GUID/material/thickness/BREP | SOURCE_PARTIAL |
| 05 | GH axes → PR74 CreateColumns; Tapir CreateBeams separate | Column native profile/story; Beam authored NOT_WIRED | PARTIAL |
| 06 | GH roof → PR74 SinglePlane CreateRoofs; Tapir MultiPlane only source | Roof GUID, slope/plane count/underside/SEO/BREP; MultiPlane NOT_FOUND | PARTIAL |
| 07 | GH host coordinates → PR74 CreateDoors/CreateWindows → AC GDL | Native host Wall GUID, libPart identity, sill/size, Wall BREP opening | SOURCE_ONLY |
| 08 | AC existing Zone → Tapir GetZoneBoundaries/GetRelationsOfElements/GetConnectedElements READ | Zone→Wall→Door/Window relations; boundary.area NOT floor area; no Zone→N/A | READ_QA_NOT_WIRED |
| 09 | APA GuardedSave → GUI Close/Reopen → Publisher IFC → IfcOpenShell/Rhino QA | Native GUID/type/story/material/holes/SEO/host, IFC GlobalId mapping, independent geometry | G4_NOT_RUN |

**Двусторонность и конфликты:** GH Synchronize TRUE и APA SceneWriter не должны писать один GUID. GH FALSE — gate, не commit receipt. Rhino Data Dam и два ArchBench alpha MCP не дают cross-app exactly-once. Любое удаление, расхождение owner/host/material, циклический feedback или UNKNOWN → STOP/read-only reconciliation. Full automatic GUID-preserving triad NOT_FOUND. Проверки размеров/уклонов/площадей и IFC IDS — формальные, не экспертиза СП.

**Версии:** Graphisoft GH–AC29 build3000 Windows Rhino7/8, 01.10.2025; Tapir pinned 1.5.10 MIT; Rhino8/AC29 коммерчески лицензируются; ArchBench MCP 0.1.0-alpha.3 MIT, не устанавливать. https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/ ; https://github.com/3d-mcp/rhino-mcp ; https://github.com/3d-mcp/archicad-mcp .
