# APA №2 — BUILD-01 · 20.10.2026 23Z · матрица и контрааудиты

Экспертная полезность 0–100, НЕ benchmark. Все SOURCE_ONLY.

| Ворота | Готовый путь → минимальное звено | Приоритет | ГОТОВО |
|---|---|---:|---|
| G0 | PR97 runtime info + APX SHA + PR150 read-only inventory | 100 | binary/schema/port/PLN exact |
| G1 | PR74 authored → BIM Graph → preflight | 100 | новый DAG/planHash, без model write |
| G1 | GetStories → PR74 story bindings | 99 | index/floorId/level/name |
| G2 | PR74 Walls/Columns/Roof typed create | 96 | GUID/material/geometry readback |
| G2 | PR74 CreateSlabs → ModifySlabs | 100 | оба этажа, GUID, материал, BREP |
| G2 | PR131 hosted Doors/Windows | 99 | verified ownerWallId/library/story |
| G2 | PR149 Beam verifier → PR74 whitelist adapter | 90 | отдельная квалификация story1 |
| G3 | PR126 batch + PR162 groups | 88 | no duplicate/replay, runtime group provider |
| G4–G5 | PR175 snapshot + PR97 BREP + reopen adapter | 100 | Save/Close/Open, независимый BREP, второй brief |

**Контрааудит A:** PR74 Slab Modify payload имеет thickness; PR149 material-only verifier его запрещает и требует story0. Tapir source schema 1.5.10 snapshot не равна установленному APX; PR97 runtime info не возвращает APX SHA. Лицензии: Tapir MIT; Graphisoft SDK EULA; APA LICENSE не подтверждена.

**Контрааудит B:** PR159 содержит read-only forensic route для остановленного group clone inventory mismatch; нельзя объявлять групповой LIVE_ACCEPTED по SOURCE. PR175 lock кооперативный и reopen helper Hotlink-specific. PR97 BREP может быть неполным из-за 3D-фильтров. Поэтому G0–G5 BLOCKED до фактических квитанций.

Не добавлять второй Router/SceneWriter/CloneNativeGroupV1. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.
