# APA №2 — 00Z — 30 SOURCE-проверок, не 30 независимых сайтов
Коды: B issue192; P PR74 immutable documentation; S Tapir pinned 1.5.10 schema; G Graphisoft download; GG Graphisoft AC29 GC.pdf; M Rhino8 official GH attributes; R/RV Rhino ArchBench README/VALIDATION; A/AV/AS Archicad ArchBench README/VALIDATION/SECURITY.
| № | Предметно проверенное утверждение | Источник |
|---:|---|---|
| 01 | BUILD-01 требует новое native двухэтажное здание | B |
| 02 | G0 требует exact scratch identity, APX/stories/PLN | B |
| 03 | Только один writer DynamicCommands/BIM Graph/SceneWriter/SQLite | B |
| 04 | UNKNOWN запрещает повтор CREATE без read-only reconciliation | B |
| 05 | G4 требует GUI Close/Reopen и independent readback | B |
| 06 | G5 требует вторую модель с другим brief | B |
| 07 | PR74 описывает исторический 21-элементный прототип | P |
| 08 | PR74 CLI предусматривает --preflight и отдельно --execute/planHash | P |
| 09 | PR74 поддерживает параметрические Roof level и Window size edits | P |
| 10 | PR74 не квалифицирует произвольный Roof contour/slope edit и global story edit | P |
| 11 | Закреплённая Tapir schema содержит 262 commands | S |
| 12 | GetStories v1.1.5 READ | S |
| 13 | SetStories v1.1.5 WRITE, required stories | S |
| 14 | GetGeoLocation v1.1.6 READ | S |
| 15 | CreateWalls v1.4.0 requires wallsData | S |
| 16 | CreateSlabs v1.0.3 requires slabsData | S |
| 17 | ModifySlabs v1.4.0 requires slabsWithDetails | S |
| 18 | CreateColumns v1.0.3 requires columnsData | S |
| 19 | CreateBeams v1.4.0 requires beamsData | S |
| 20 | CreateRoofs v1.4.0 defaults MultiPlane without pivotLine | S |
| 21 | CreateWindows and CreateDoors v1.4.0 require input arrays | S |
| 22 | GetConnectedElements v1.1.4 requires elements+connectedElementType | S |
| 23 | GetIFCIdsOfElements v1.5.1 requires elements | S |
| 24 | GetModelDumpV1 absent from pinned Tapir command names | S |
| 25 | Graphisoft GH–AC29 build3000 supports Windows Rhino7/8, dated 01.10.2025 | G |
| 26 | GH Synchronize TRUE writes; FALSE returns Null, no generation | GG |
| 27 | Rhino8 GH Query/Model Object handles attributes/materials; Bake writes Rhino document | M |
| 28 | Rhino ArchBench MCP alpha.3 document-bound, 16 fixture tests, native pending | R,RV |
| 29 | Archicad ArchBench MCP alpha.3 explicit port 19723–19743, 7 fixture tests, native pending | A,AV |
| 30 | Archicad MCP arbitrary command gated; timeout not rollback | AS |

Sources:
B https://github.com/dvikt33-ux/safe-bim-layer/issues/192
P https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/docs/APA_MODEL_FIRST_BUILDING.md
S https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json ; Git blob e8ad53b6ea7c19dc34cbdcb723a79be995639cd7
G https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/
GG https://help.graphisoft.com/AC/29/INT/GC.pdf
M https://www.rhino3d.com/en/docs/guides/grasshopper/object-attributes/
R https://github.com/3d-mcp/rhino-mcp/blob/main/README.md
RV https://github.com/3d-mcp/rhino-mcp/blob/main/docs/VALIDATION.md
A https://github.com/3d-mcp/archicad-mcp/blob/main/README.md
AV https://github.com/3d-mcp/archicad-mcp/blob/main/docs/VALIDATION.md
AS https://github.com/3d-mcp/archicad-mcp/blob/main/SECURITY.md

**Доказательность:** 30 проверенных отдельных утверждений по прочитанным первичным контрактам, НЕ 30 LIVE и НЕ 30 независимых источников. SOURCE=30; OFFLINE=0; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0; ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
