# APA №2 — 00Z — два документарных контрааудита
## A: направление, BIM и identity
1. GH–AC Synchronize TRUE — самостоятельная native GH→AC запись; она не проходит SQLite APA. Нельзя разрешать два writer на один GUID. FALSE возвращает Null, не подтверждает сохранённый PLN.
2. Rhino Brep, GH Model Object, IFC mesh, GDL Object и native AC Wall/Slab/Roof не равны. Сходная геометрия не доказывает host, story, SEO, материал или BIM type.
3. Archicad element GUID, Rhino object GUID, GH component GUID, IFC GlobalId и floorId — разные пространства. Требуется explicit mapping/readback.
4. CreateBeams и MultiPlane CreateRoofs существуют в pinned Tapir, но не доказывают authored PR74 support. Отсутствующий маршрут NOT_WIRED/NOT_FOUND.
5. Два MIT MCP предоставляют отдельные endpoints, не общий event bus/transaction/owner/version/conflict resolution. Full native three-way sync NOT_FOUND.
**Вердикт A:** SOURCE_CANDIDATE для однонаправленной сборки; G0–G5 не повышены.

## B: лицензии, безопасность, фактическая приёмка
1. Graphisoft add-on build3000 не равен локальному Archicad build5101; официальная Rhino8 совместимость не INSTALLED/LIVE evidence.
2. ArchBench Rhino MCP alpha — 16 fixture tests; Archicad MCP alpha — 7; native AC29/Rhino8 qualification pending. Новая установка P0 не оправдана.
3. AC MCP explicit port не идентифицирует SHA PLN; Rhino MCP document-bound не связывает этот документ с PLN. Нужен полный fail-closed identity tuple.
4. Timeout/cancel/confirm:true не дают rollback или пользовательское разрешение. SetStories и GH native Synchronize — WRITE, запрещены.
5. Исторический PR74 21 элементов не новый BUILD-01. SOURCE=30 не OFFLINE_PASS. Нет нового planHash, typed DAG, native receipt или Save/Open.
6. Прочитаны NEXT, TRIAD PIVOT, №1 00Z, №2 23Z, №3 20.10 18Z, matrix61; PROJECT_PLAN rev182 не извлекался/не менялся.
**Вердикт B:** G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.

**Критерии следующих gate:** G0 actual read-only AC port/build/GetProjectInfo/stories/Tapir/APX SHA/command inventory/scratch SHA плюс Rhino .3dm/GH .gh; G1 один новый brief с реальным preflight DAG/planHash; G3/G4 только после отдельного допуска scratch и native Save/Close/Reopen/IFC/BREP.
