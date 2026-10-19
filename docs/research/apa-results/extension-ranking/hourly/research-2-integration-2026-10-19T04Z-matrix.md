# APA №2 04Z — матрица подключения (10 решений)

Все баллы — экспертная полезность 0–100, не benchmark. Только SOURCE; ни одно новое подключение не выполнялось.

| Инструмент | Готовая цепочка APA → интерфейс → библиотека | Решение / оценка / сложность | ГОТОВО |
|---|---|---|---|
| IfcTester | Existing Router → PR154 IfcTester JSON → coverage gate | REUSE 98 БЫСТРО | 0 executed=NOT_VERIFIED |
| Tapir attribute values | Router → GetPropertyValuesOfAttributes → per-cell JSON | ADAPTER 94 БЫСТРО | local command inventory, error/readback |
| Whole-plan inventory | Router → Tapir GetAllElements → Native Model Dump | REUSE 94 БЫСТРО | scope whole-plan, GUID diff |
| XML ведомостей | Existing file QA → tagged v0.8.0 scheme parser → JSON | ADAPTER 91 АДАПТАЦИЯ | 2 XML, SHA, byte roundtrip |
| Property definitions | Router → Tapir GetAllProperties → GUID/name | REUSE 91 БЫСТРО | no property value evaluation |
| IFC property QA | Exported IFC copy → existing B2/IfcOpenShell | REUSE 90 БЫСТРО | IFC SHA, timestamp, GlobalId |
| Hotlink QA | PR173 receipt → BIM Graph owner/BREP | REUSE 92 БЫСТРО | 69 retained, 2 roots/48 children |
| GDL | archicad-gdl CLI → AC29 LP_XMLConverter → GSM | DEFER 84 ДОЛГО | explicit units, license, isolated geometry |
| Terrain QA | Existing Mesh/Slab read → drape.py/CDT → deviation | ADAPTER 80 АДАПТАЦИЯ | holes, 5mm tol, max500 |
| Element properties | Router → Tapir GetPropertyValuesOfElements | DEFER 77 ДОЛГО | crash safety not established |

Лицензии: v0.8.0 MIT, Python>=3.12; Tapir tagged 1.5.9 MIT; Graphisoft proprietary. Local Tapir 1.5.10 command availability unknown. GPU 8GB and RAM48GB not a compatibility test. No second Router/SceneWriter/MCP.
