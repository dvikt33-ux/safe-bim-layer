# APA №2 · BUILD-01 · 2026-10-20T19Z · Матрица девяти маршрутов

Оценка 0–100 — экспертная полезность, не измеренное ускорение. Все решения SOURCE, пока G0 не подтверждён.

| Ворота | Существующий путь | Приоритет | Критерий |
|---|---|---:|---|
| G0 | PR97 runtime identity + SHA APX + PR150 read-only bridge | 100 | REUSE; installed identity and command inventory before anything else. |
| G1 | PR74 authored compiler + existing BIM Graph | 100 | REUSE; new two-floor brief, read-only preflight and plan hash. |
| G1 | PR74 GetStories/story binding | 99 | REUSE; native index/floorId/name/level exact. |
| G2 | PR74 Wall/Column/Roof typed SceneWriter | 96 | REUSE; schema+GUID/material/geometry verification. |
| G2 | PR74 Slab Create→Modify→readback | 100 | REUSE; PR149 story0 verifier not universal. |
| G2 | PR131 hosted Door/Window placement | 99 | REUSE; ownerWallId GUID and overlap check. |
| G2 | PR149 Beam + PR74 whitelist adapter | 91 | DEFER; minimal compiler extension only after qualification. |
| G3 | PR126 batch + PR162 group-first | 89 | DEFER; same SceneWriter/SQLite, no second writer. |
| G4–G5 | PR175 guarded save + PR97 ModelDump | 100 | ADAPTER; Hotlink-specific reopen and filtered BREP require independent acceptance. |

Минимум внешних звеньев: Graphisoft AC29 JSON/Python → существующий Router → SceneWriter; BREP из отдельного native provider только после проверки установленного APX. Лицензии: Tapir MIT; Graphisoft SDK29 EULA; внутренний APA LICENSE NOT_FOUND. SOURCE→OFFLINE→BUILD→INSTALLED→LIVE→ACCEPTED, без перескакивания ворот. MODEL_MODE_NOT_VERIFIABLE.
