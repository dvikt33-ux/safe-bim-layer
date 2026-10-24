# APA №2 — 24.10.2026 03Z | BUILD-01: воспроизводимый G0 Rhino и геометрический предел PR74

**Режим:** SOURCE_ONLY; OFFLINE=0 новых, BUILD=0, INSTALLED=NOT_VERIFIED, LIVE=0 новых, ACCEPTED=0. **MODEL_MODE_NOT_VERIFIABLE.** Никаких установок, запуска Windows/Rhino/Archicad, изменения исходного кода, main, PLN/APX, Work/Codex/Arena, платных API, merge или нативных записей. Роль №2: инженер готовой интеграции, не исполнитель BUILD-01.

## 1. Новая P0-дельта — три точных ограничения/возможности

**P0-I03-01 — штатный read-only идентификатор экземпляра Rhino 8.** Официальный McNeel `rhinocode list --json` (Rhino **>=8.11**, Windows: `%PROGRAMFILES%\Rhino 8\System\rhinocode`) возвращает PID, уникальный ID процесса/pipe, `processVersion`, `activeDoc.title` и `activeDoc.location`. Это готовый способ связать конкретный Rhino-процесс с `.3dm` и версией без собственного MCP/router. Но `StartScriptServer` не запускается автоматически: отсутствие записи в `rhinocode list` **не доказывает**, что Rhino не запущен. Это инструкция для будущего санкционированного G0, в этом проходе команду не выполняли. Источник: https://developer.rhino3d.com/en/guides/scripting/advanced-cli/ (McNeel, обновление 28.05.2026). Не использовать `rhinocode command`: это уже управление Rhino, а не read-only inventory.

**P0-I03-02 — явный предел кровли в authored PR74.** В immutable `scripts/archicad_project_accelerator.py` (commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, строки 291–318) `nativeComponents` допускает только `CreateColumns/CreateDoors/CreateWindows/CreateWalls/CreateRoofs`, максимум **100 steps**; для `CreateRoofs` требуется **ровно одна** строка `roofsData`, `pivotLine`, `structureType=Basic`, `buildingMaterialId`. Каждая точка `polygonCoordinates` обязана находиться в пределах `layout.outline` с запасом **0.35 м** по X/Y. Значит явный контур карнизного свеса **0.50 м** за прямоугольным outline будет отвергнут этим authored-контрактом. Это **SOURCE_STATIC_LIMIT**, а не тест Tapir/Archicad. Исходный пример имеет свес ~0.15 м; не объявлять 0.35 универсальным пределом всех средств Archicad. Один MultiPlane Roof здесь **NOT_FOUND**. Строгие комнаты/outline и X/Y bearingLines подтверждены `archicad_semantic_spatial.py`. Отдельные `CreateBeams/CreateSlabs/SetStories` в `nativeComponents` **NOT_WIRED**, хотя некоторые команды могут существовать в Tapir.

**P0-I03-03 — Rhino Content Cache не является транзакцией и имеет версионные границы.** Руководство разработчика McNeel от 17.05.2024 относится к **Rhino 8.8 RC**, не к любой установленной 8.x. `Push` отслеживает и заменяет объект с ID; `Bake` без ID создаёт новый; `Push` и `Bake` с входным Model Object ID заменяют исходный. `Action=False` блокирует действие, **но видимый Result продолжает Pull**; `Purge` затрагивает неиспользуемые объекты/слои/материалы/определения блоков. `Content Details` выдаёт `ID/Cache Name/Cached/Referenced/Path/Attributes`. `Branch Names` изолирует слои/имена, не BIM GUID. В этой же ветке разработчики отметили исправление сброса Content Cache в **8.9** и сценария добавления элементов в **8.11**; локальный SR неизвестен. Источник: https://discourse.mcneel.com/t/content-cache-updated-guide/181883 (посты #1, #16, #20). До локального G0 не обещать identity-preserving update. Это не автоматическая связь с Archicad.

## 2. Готовые средства, версии, лицензии и границы

| Средство | Проверенная SOURCE-версия | Лицензия/состояние | Что реально обеспечивает |
|---|---|---|---|
| Archicad 29 | ожидаемый executable build 5101 | коммерческий продукт; runtime NOT_VERIFIED | нативная BIM-модель, этажи, элементы, атрибуты |
| Graphisoft GH–AC29 Live Connection | Windows **29 build 3000**, 01.10.2025; Rhino 7/8 | бесплатный add-on, не лицензия Archicad/Rhino; INSTALLED NOT_VERIFIED | GH→AC создание поддержанных элементов; AC→GH Deconstruct/Send Changes, не общий трёхсторонний commit |
| Rhino 8 + Grasshopper 1 | Rhino 8; локальный SR NOT_VERIFIED | Rhino коммерческий, GH штатный | геометрия/параметры, Query Model Objects, Content Cache |
| RhinoCode CLI | штатный в Rhino **>=8.11** | входит в Rhino; runtime NOT_VERIFIED | `list --json`: read-only PID/instance/version/active .3dm |
| jSwan | MIT (репозиторий); точная версия/Rhino8 локально NOT_VERIFIED | бесплатный | сериализация GH JSON, но не native writer и не гарантированный typed schema PASS |
| APA PR74 + SceneWriter/SQLite + Tapir | PR74 immutable `5a3a9201...`; ожидаемый Tapir 1.5.10 | существующий код; локальные APX/schema NOT_VERIFIED | единственный APA-owned writer после отдельного допуска |

Официальные ссылки: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://developer.rhino3d.com/en/guides/scripting/advanced-cli/ ; https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/ ; https://github.com/andrewheumann/jSwan/blob/master/LICENSE ; https://github.com/dvikt33-ux/safe-bim-layer/pull/74 .

## 3. Единый G0-манифест: без нового кода, только штатные команды

1. **AC29**: существующие read-only `GetProjectInfo/GetStories/GetAddOnVersion`, actual port, `projectPath`, build, story index/floorId/level, APX/command inventory, материалы/Favorites/библиотеки. Сверить с `RUN.EXPECTED_PATH` и ожидаемым Tapir 1.5.10. Константа порта не является runtime receipt.
2. **Rhino8**: после отдельного разрешения на read-only inventory `rhinocode list --json` (только если версия >=8.11 и уже работает script server), выбрать **точный PID+activeDoc.location**; сверить существующий `.3dm`, SHA256, units, координаты и Rhino Object IDs. Не запускать script server в этом исследовании. При отсутствии ответа: UNKNOWN, а не NOT_RUNNING.
3. **Grasshopper**: `.gh` путь/SHA, определения и версии компонентов; `Query Model Objects → Model Object/User Text → Group Content/Match Text Filter/Filter Content`; проверить `APA_Owner/APA_Type/APA_Story/APA_ExternalId` как пользовательскую дисциплину, не штатную BIM-схему.
4. **Права записи**: APA-owned AC GUID изменяются только через SceneWriter; `GH–AC Synchronize` для них выключен. Rhino Content Cache может обновлять **только Rhino-owned** объекты. Запретить `Purge`, не допускать feedback loop `Pull→Move→Push`.
5. **Готовность**: `G0_READY` только при подтверждении AC instance/PLN/APX, Rhino PID/document/SR, GH definition, единиц, story mapping и owner crosswalk; в данном проходе `G0=BLOCKED_RUNTIME`.

## 4. Девять операций BUILD-01: программа → изменение → синхронизация → контроль → ГОТОВО

| № | Операция / программа / готовый инструмент | Завершение и передача в другие | Контроль/критерий ГОТОВО | Статус |
|---|---|---|---|---|
| 1 | Rhino8/GH: геометрия и атрибуты; Query Model Objects + Model Object + GH filters | Freeze geometry → типизированный authored JSON → PR74 preflight; обратное в Rhino только отдельный readback | `.3dm/.gh/JSON` SHA, units, уникальные ExternalId, нет неизвестных BREP; идентичность источника | SOURCE_ONLY |
| 2 | AC29: этажи; GetStories READ, story planes в GH | AC→GH чтение этажей, GH→JSON существующие nativeIndex/floorId; `SetStories` не подключён | index/floorId/level точно после Save/Open | EXISTS_NOT_WIRED |
| 3 | GH→AC29: ортогональные стены; bearingLines → PR74 CreateWalls | Freeze→preflight→(только G3 с допуском) SceneWriter; AC→GH Deconstruct/Send Changes READ | GUID/Wall/host story, relative Z, толщина, материал, BREP/junctions | SOURCE_WIRED_NOT_RUN |
| 4 | GH→AC29: базовые Slabs; прямоугольный outline → PR74 CreateSlabs | один Slab на story, absolute level; отверстия/freeform не проходят этот вход | GUID/Slab, level, thickness, material, отверстия/BREP; если holes требуются — STOP | RECT_ONLY; HOLES_NOT_WIRED |
| 5 | GH→AC29: Column через nativeComponents CreateColumns; Beam отсутствует | Column 1 row/step; Beam через этот authored вход нельзя; не переключать на второй writer | GUID/Column/geometry/story/material; Beam NOT_FOUND | COLUMN_PARTIAL; BEAM_NOT_WIRED |
| 6 | GH→AC29: SinglePlane Basic Roof через nativeComponents CreateRoofs | pivotLine, 1 roof/step, polygon внутри outline±0.35; AC29 MultiPlane штатно создаётся GUI, но не этим writer | GUID/Roof, slope, level, material, roof BREP, SEO; свес >0.35 в явном polygon — STOP | SINGLE_PLANE_ONLY; MULTIPLANE_NOT_FOUND |
| 7 | GH→AC29: Door/Window, существующие CreateDoors/CreateWindows с `$createdGuid` host | после wall creation; libraries verified; AC→GH readback после `Send Changes` | host GUID, размеры/sill, GDL part, openings после Save/Open | CONDITIONAL |
| 8 | AC29→GH/Rhino: изменение уже созданного элемента | `Send Changes→Deconstruct` поддержанных типов; Rhino Content Cache лишь Rhino↔GH, не AC GUID; запрет обратной прямой GH→AC записи | before/after AC GUID/type/params/material + Rhino ID + geometry hash; MultiPlane Deconstruct NOT_FOUND | PARTIAL_READ_ONLY |
| 9 | GH/AC29: численные проверки, независимая геометрия, откат | GH constraints → preflight → после санкционированной записи native readback/IFC → guarded Save/Close/Reopen | сравнить GUID/IFC ID/BREP, атрибуты, этажи, отверстия, коллизии; при UNKNOWN только READ | QA_SOURCE_ONLY; ACCEPTED=0 |

**Общий транзакционный протокол:** редактировать только один owner за операцию → остановить GH/AC Synchronize для APA-owned → завершить GH definition и Rhino Content Cache (Result скрыт при freeze) → сформировать typed JSON и plan hash → read-only G0/G1/G2 → только по отдельному допуску G3 → GUID/native type/material/BREP readback → guarded Save/Close/Reopen → повторный readback. При изменении числа элементов, удаления, смены типа, несовпадении source ID, цикле, конфликте writers или UNKNOWN: STOP и read-only reconciliation; **автоматический cross-app rollback NOT_FOUND**.

## 5. Нормативные/параметрические проверки

GH проверяет численные ограничения (площади из горизонтальных контуров, ширины/высоты/уклоны, проходы, допустимые отклонения, единицы), PR74 — свой строгий spatial contract и plan hash; AC29 — нативный GUID/type/host/material и IFC/BREP после записи. `ZoneBoundaries.area` не подменять площадью пола. СП/редакция/условия применения и расчётная методика должны быть зафиксированы отдельно; ни GH, ни IFC не являются сами по себе нормативной экспертизой. Для кровли дополнительно проверять целостность MultiPlane/SinglePlane, дочерние Opening/Skylight, SEO, материал и объём.

## 6. Контрааудит A — автоматическая синхронизация (проведён SOURCE)

Проверены `Content Cache` McNeel, официальная GH–AC29 документация по Deconstruct/Send Changes и authored allowlist PR74. **Вывод:** Rhino↔GH Push/Pull не равен AC GUID preservation; AC→GH Send Changes — направленное чтение, GH→AC Synchronize — другой writer; в PR74 нет универсального двустороннего merge. Встроенного согласованного трёхстороннего атомарного commit, разрешения конфликтов и удаления **NOT_FOUND**. Противоположный вывод был бы подменой понятия синхронизации.

## 7. Контрааудит B — native BIM и геометрия (проведён SOURCE)

Сопоставлены `archicad_semantic_spatial.py` (rectangles/X/Y), `archicad_project_accelerator.py` (5-command allowlist, roof polygon margin 0.35, max 100) и официальный AC29 MultiPlane Roof GUI. **Вывод:** существование нативного MultiPlane в Archicad не доказывает его создание через PR74; разделение MultiPlane на SinglePlane меняет структуру элементов и не доказывает GUID сохранение; Morph/mesh/IFC не подменяет native Roof. Для BUILD-01 G1 возможен только в доказанном ограниченном envelope, универсальная Rhino BREP→native BIM **NOT_FOUND**. Это не LIVE-тест.

## 8. Gate, источники, следующий P0

G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4=NOT_RUN; G5=NOT_RUN. Никаких новых PASS. Исторический 21-элементный PR74 не засчитывать за новое BUILD-01. Следующий шаг **без записи**: G0 RhinoCode `list --json` + AC GetProjectInfo/GetStories/actual command inventory на разрешённой среде, затем authored read-only preflight `model-first-building.json` с проверенными project path/story/material; **не** выдавать прямоугольный макет за универсальный Rhino BREP compiler.

Поручения и контроль: https://github.com/dvikt33-ux/safe-bim-layer/issues/192 ; https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md ; https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md ; №1 03Z https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T03Z-TRIAD-DUPLICATE-CONTENT-CACHE-IDENTITY.md ; последний обнаруженный №3 20.10 18Z https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md ; матрица 61 https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json . Исторический PROJECT_PLAN rev182 не изменялся.
