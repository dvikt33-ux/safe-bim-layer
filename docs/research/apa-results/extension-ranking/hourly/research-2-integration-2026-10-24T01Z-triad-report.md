# APA №2 / 2026-10-24 01Z — BUILD-01: выбор безопасного компилятора и проверка высоты Slab
**Режим:** SOURCE / статический анализ, без установки, без LIVE, без изменений исходного кода, main, PLN/APX, без Work/Codex/Arena, merge или платных API. MODEL_MODE_NOT_VERIFIABLE.

## P0 — новый предметный результат: legacy building-shell-v1 не использовать для нового двухэтажного BUILD-01 без устранения Z-расхождения
Сопоставлены **два существующих пути PR #74**, которые нельзя считать эквивалентными:
1. `scripts/archicad_building_shell.py` (immutable PR74 head `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, строка 120) для **каждого** этажа передаёт `CreateSlabs: {level:0.0, floorIndex:idx}`. Для этажа с `GetStories.level=3.0` получается `floorIndex=1, level=0.0`.
2. `scripts/archicad_authored_native_plan.py` (тот же commit, строка 108) передаёт `{level:float(s["level"]),floorIndex:native}`, а строка 238 объявляет `slabLevelConvention="PROJECT_ABSOLUTE"`. Для второго этажа +3.000 это `floorIndex=1, level=3.0`.
3. **Механизм Tapir подтверждён исходным C++ релиза 1.5.9**: `CreateSlabsCommand::SetTypeSpecificParameters` передаёт `inputLevel` в `ResolveFloorIndexAndOffset`, где при явном `floorIndex` вычисляется `offset=zPos-storyElevation`. Значит `(floorIndex=1,level=0)` на этаже +3 даёт внутренний offset −3 и абсолютную Z=0, а `(floorIndex=1,level=3)` даёт offset 0 и абсолютную Z=3. Pinned schema 1.5.10 описывает `level` как Z координату опорной плоскости, а `floorIndex` как необязательный этаж.
4. `archicad_scene_run.py` (строки 404–413) в **legacy** режиме сравнивает readback `details.level` с ожидаемым 0, а **authored** — с `expected.level-storyElevation` и `details.zCoordinate=expected.level`. Поэтому ошибочная legacy-геометрия должна вызвать `SLAB_READBACK_MISMATCH` при честном нативном readback, но **после CREATE**. Это не безвредная офлайн-ошибка.
5. `tests/test_archicad_building_shell_integration.py` (строки 85–102) подтверждает лишь **synthetic** 25-элементную сборку; синтетический `NamedStoriesNative` не пересчитывает Slab Z как настоящий Tapir. Этот тест **не опровергает** найденное расхождение. `tests/test_archicad_authored_native_plan.py` (строки 103–111) отдельно требует `Slab.level=[0,3]`.

**Доказательность:** `SOURCE_STATIC_CONTRACT_MISMATCH`; физический дефект в Archicad 29 build5101 **не испытывался**, так как LIVE запрещён. Точный tag 1.5.10 в публичном upstream GitHub недоступен; сравнение реализации выполнено на tag 1.5.9 и 1.6.0, а ожидаемый API взят из сохранённой схемы 1.5.10. Не писать `LIVE_BUG_CONFIRMED`.

**Готовое решение без нового writer:** для BUILD-01 использовать только существующий **authored** путь `apa-authored-project/1 → compile_authored_intent → archicad_authored_native_plan → BIM Graph → SceneWriter/SQLite → Tapir`. Legacy `building-shell-v1` пометить `SOURCE_RISK_NOT_APPROVED_FOR_BUILD01`. Не исправлять код в исследовательском прогоне. Если для старого пути нужна отдельная правка — только отдельное инженерное решение/PR с разрешением.

## Пошаговая воспроизводимая цепочка без второго исполнителя
**G0 / READ:** проверить фактический `GetProjectInfo`, порт, build5101, `GetStories` (index, floorId, level), `GetAddOnVersion`, регистрацию команд, путь и SHA защищённой scratch PLN, материалы/Favorites/GDL и APX. Константы кода не являются runtime receipt. Отсутствие пути, смена active PLN или неизвестный APX → BLOCKED.
**GH/Rhino / PARAMETRIC:** открыть согласованные `.3dm` и `.gh`, проверить единицы метров и локальные XY/Z, зафиксировать SHA обоих, Rhino Object IDs и версии компонентов. Геометрия Rhino не равна BIM GUID.
**GH / SERIALIZATION:** готовый MIT `jSwan` (Serialize Keys and Values, явные `x,y`, массивы, без `null` вместо boolean/list). Rhino 8 совместимость конкретной установленной сборки jSwan НЕ ПРОВЕРЕНА. Можно использовать проверенный исходный JSON-пример PR74 как шаблон без нового writer. Проверить `schemaVersion=apa-authored-project/1`, `units=meters`, `brief.targetProjectPath=RUN.EXPECTED_PATH`, реальные story bindings, материал по GUID, hosted `$createdGuid` и уникальные IDs. Исходный JSON SHA обязателен.
**PR74 / G1:** штатный `run_project(...,mode="preflight",transport=read_only)`; для authored `mode="offline"` отклоняется. Результат `READY_FOR_EXPLICIT_TEST_RUN` возможен только после фактического выполнения, не выводится из схемы. Read-only preflight создаёт локальные evidence файлы, но не меняет PLN. Запись не разрешена.
**G2:** подтвердить typed DAG/topological order/planHash, absolute Slab Z, relative Wall bottomOffset, hostWall, native material/roof class, не допускать `CreateBeams` в `nativeComponents` (текущий authored allowlist не включает), `MultiPlane` в `CreateRoofs` (требует `pivotLine`).
**G3:** только после отдельного согласования новой scratch PLN, её SHA, порта, planHash и явного WRITE допуска. Единственный writer SceneWriter/SQLite. При тайм-ауте/UNKNOWN — остановить, read-only reconciliation, не повторять CREATE.
**G4:** native GUID/readback + BIM type + floorIndex + absolute Z + building material GUID + hosted parent GUID + реальная геометрия/SEO/IFC; GuardedSave → закрыть GUI → повторно открыть → независимая инвентаризация, BREP/IFC, журнал и откат из защищённой копии. IFC mesh не считать нативным BREP.
**G5:** второе исходное задание и новый план, не повторение старого CREATE.

## Десять приоритетных сценариев (маршрут → проверка → статус)
| Сценарий | Выбор готового инструмента / завершение операции / направление | Проверка «ГОТОВО» | Статус |
|---|---|---|---|
| 1. Исходные координаты | Rhino8/GH → jSwan JSON → authored PR74; до передачи solver/AC Synchronize выключены | `.3dm/.gh/JSON` SHA, единицы, XY/Z, schema, planHash | SOURCE_CANDIDATE |
| 2. Этажи | Archicad scratch GetStories → GH таблица levels → PR74; `SetStories` Tapir есть, но WRITE и не wired | index/floorId/level совпадают после Save/Open | EXISTS_NOT_WIRED |
| 3. Стены | GH линии → `CreateWalls` authored; `zCoordinate` при floorIndex — смещение от этажа | GUID, Wall, абсолютная Z, толщина, материал, joins | SOURCE_WIRED_NOT_RUN |
| 4. Slab/отверстия | GH полигоны → authored `CreateSlabs` level=absolute Z; полигональные holes только при доказанном контракте | GUID, Slab, Z, material, thickness, hole count, BREP | SOURCE_WIRED_NOT_RUN; LEGACY_Z_RISK |
| 5. Колонны | GH точки → authored `CreateColumns` при корректном floorIndex | GUID, Column, origin Z, width/depth/height, material | SOURCE_PARTIAL |
| 6. Балки | GH линии → Tapir `CreateBeams` существует, но отсутствует в authored allowlist | typed Beam, GUID, profile, elevation, connections | NOT_WIRED |
| 7. Простая кровля | GH контур+поворот → authored `CreateRoofs` с pivotLine | SinglePlane, GUID, slope, material, SEO/BREP | SOURCE_WIRED_NOT_RUN |
| 8. Сложная кровля | Rhino/GH расчёт → Tapir `CreateRoofs` без pivotLine; authored PR74 требует pivotLine | единый native MultiPlane GUID + полный readback | NOT_WIRED; FULL_ROUTE_NOT_FOUND |
| 9. Двери/окна/GDL | GH размеры/host → authored `CreateDoors/Windows` по `$createdGuid`; библиотеки заранее проверены в AC | host GUID, тип, размеры, sill, library availability, Save/Open | SOURCE_CONDITIONAL |
| 10. QA/нормативы | Archicad readback + IFC/IfcOpenShell, GH численные ограничения; без автоматического нормативного сертификата | GUID/IFC ID, solids, коллизии, площади, доступность, эвакуация; экспертная проверка | SOURCE_ONLY / LIVE_NOT_RUN |

## Реальная двусторонность и управление конфликтами
- Официальный Graphisoft Grasshopper–Archicad 29 Live Connection **build 3000**, Windows, Rhino7/8; доступен как бесплатное дополнение, **не лицензия Rhino 8**. `Synchronize=True` создаёт/меняет нативные AC элементы **напрямую, минуя SceneWriter**; использовать только для отдельных GH-owned элементов, не для APA-owned. Штатный Boolean Toggle выключать при правке входов. Изменения AC→GH для поддерживаемых параметров требуют штатной процедуры `Send Changes`/режима синхронизации, не гарантируют передачу всех BIM параметров.
- Rhino8 `Content Cache` Push/Pull сохраняет Rhino ID при корректной модели данных; Bake без ID может создать дубликаты. **Rhino Object ID ≠ Archicad GUID.** Это локальная связь Rhino↔GH, не глобальный синхронизатор.
- **Ownership:** один native Archicad GUID имеет только одного writer; для BUILD-01 это SceneWriter. Прямую запись Graphisoft GH–AC в APA-owned элемент отключить. При конфликте, цикле или удалении — STOP и read-only reconciliation; автоматического merge/rollback между тремя программами не найдено.
- **Неизвестное:** полная автоматическая трёхсторонняя native GUID-preserving синхронизация с двусторонним редактированием, удалением, конфликтами и атомарным откатом: `NOT_FOUND`.

## Лицензии, версии, ограничения
| Средство | Источник и версия | Лицензия / статус |
|---|---|---|
| Graphisoft GH–AC Live Connection | AC29 build3000, Rhino7/8, Windows, 01.10.2025 | официальная бесплатная загрузка; INSTALLED_NOT_VERIFIED |
| Rhino 8 + встроенный Grasshopper/Content Cache | McNeel Rhino8 | Rhino коммерческий продукт; GH/Cache входят в Rhino8; локальная версия не проверена |
| Tapir | pinned APA 1.5.10; upstream GitHub MIT | командный каталог SOURCE; actual APX/command registration не проверены |
| jSwan | GitHub `andrewheumann/jSwan`, MIT | бесплатный исходник, Rhino8 runtime не проверен |
| APA PR74/SceneWriter | immutable head `5a3a9201...`, draft, не merged | существующий исполнитель, без нового writer |

## Два обязательных контрааудита
См. соседний файл `research-2-integration-2026-10-24T01Z-triad-audits.md`. 30 предметных SOURCE-проверок (не 30 независимых сайтов) — `...-checks.md`. Никаких synthetic/offline/live тестов **в этом проходе** не запускалось.

## Фактический итог
**G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN.**
**SOURCE=30 документарных сверок; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0.**
**Следующее конкретное действие инженера:** не запускать legacy `building-shell-v1`; квалифицировать реальный scratch PLN и вызвать authored preflight; отдельно сверить `CreateSlabs.level` против `GetStories.level` до любого разрешённого WRITE.

### Первоисточники
- Issue #192: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- PR74: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
- Legacy Slab Z: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_building_shell.py#L110-L123
- Authored Slab Z: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L100-L112
- Readback: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L400-L413
- Tapir 1.5.9 CreateSlabs C++: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp
- Tapir 1.5.9 ResolveFloorIndexAndOffset C++: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/CommandBase.cpp
- Pinned Tapir schema: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- Official Graphisoft: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- Graphisoft GH Boolean Toggle: https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
- McNeel Content Cache: https://discourse.mcneel.com/t/content-cache-updated-guide/181883
- jSwan: https://github.com/andrewheumann/jSwan
