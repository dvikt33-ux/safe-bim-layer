# APA №2 · BUILD-01 · 18Z — 9 маршрутов и 2 контрааудита

Оценка 0–100 — экспертный приоритет, не измеренная производительность.

| Ворота | Готовая функция → барьер | Приоритет | Решение / ГОТОВО |
|---|---|---:|---|
| G0 | Graphisoft IsAddOnCommandAvailable + PR97 GetAPARuntimeInfoV1 + SHA APX | 100 | REUSE; совпали runtime/schema/binary hashes |
| G0 | Tapir GetStories/GetBuildingMaterials/GetAvailableLibraryParts | 99 | REUSE; точные story/material/library GUID |
| G1 | PR74 authored compiler → BIM Graph | 100 | REUSE; новый typed DAG, sourcePlanHash |
| G2 | PR74 CreateSlabs→ModifySlabs→readback | 100 | REUSE; оба этажа и material GUID |
| G2 | PR131 host-qualified Doors/Windows | 99 | REUSE; Wall GUID/story/fit/readback |
| G2 | PR149 scoped Beam + PR74 whitelist | 90 | ADAPTER LATER; не story0-only |
| G3 | PR126 packed CREATE через тот же SceneWriter | 88 | DEFER; verified GUID, no replay |
| G3 | PR162 native group-first через BIM Graph | 85 | DEFER; provider registration proven |
| G4–G5 | PR175 snapshot + PR97 ModelDump + new reopen receipt | 100 | ADAPTER; Save/Close/Open, BREP, второй brief |

**Контрааудит A:** PR74/126/149/162/175 — draft source, не installed. Pinned Tapir schema 262 команд не равна бинарнику. Upstream PR785 merged, но NOT BUILT/NOT REVIEWED. PR97 GetAPARuntimeInfoV1 сообщает source buildIdentity, не SHA фактического APX.

**Контрааудит B:** rev197 содержит 104 задачи, BUILD-01/#192 отсутствует; до lease требуется запись штаба. PR97 ModelDump вызывает ShowAllIn3D/Rebuild и зависит от фильтров вида; это не гарантированно полная инвентаризация. PR175 reopen специализирован под Hotlink. Не делать G3 без допуска.

SOURCE only. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.