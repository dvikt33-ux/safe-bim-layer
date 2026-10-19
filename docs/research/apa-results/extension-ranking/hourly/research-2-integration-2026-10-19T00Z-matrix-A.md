# APA №2 — матрица интеграции A

| Готовый инструмент | Цепочка через APA | Версия, контракт, лицензия | Решение, балл, сложность | Риски и ГОТОВО |
|---|---|---|---|---|
| IDS Audit CLI | Router→ids-tool audit→IDS report→existing IfcTester | 1.0.124, .NET8, MIT; --omitContent запрещён | ADAPTER 95 БЫСТРО | runtime unknown; XSD/semantic negative fixtures |
| Ifc2Sql | APA IFC→IfcPatch recipe→SQLite→BIM Graph QA | IfcOpenShell 0.8.5 LGPL3+; psets(ifc_id,pset_name,name,value) | ADAPTER 89 АДАПТАЦИЯ | geometry=True default; existing DB warning; new output+GlobalId join |
| IFC CRS QA | B2/B3→util.geolocation→JSON QA | IfcOpenShell 0.8.5 LGPL3+; auto_xyz2enh/auto_enh2xyz/get_crs | REUSE 92 БЫСТРО | missing MapConversion returns XYZ; 3 fixtures |
| Design Options | Bridge→готовый binding NOT_FOUND→native read-only→BIM Graph | Graphisoft SDK29 29.3100 EULA; GetAllDesignOptions/GetElementsOfDesignOption | DEFER 88 ДОЛГО | ABI/Teamwork; GUID+view+Hotlink readback |
| Native SAM | Bridge→готовый binding NOT_FOUND→native read-only→BIM Graph | Graphisoft SDK29 EULA; GetCurveElements/GetSurfaceElements/GetAnalyticalMemberConnections | DEFER 84 ДОЛГО | variation, not solver/SAF; A11.S08 BLOCKED |
