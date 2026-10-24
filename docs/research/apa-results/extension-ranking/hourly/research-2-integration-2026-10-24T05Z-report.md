# APA №2 — 2026-10-24 05Z | BUILD-01: двухпрофильная IFC-приёмка без второго writer

**Режим:** SOURCE_ONLY; G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. **MODEL_MODE_NOT_VERIFIABLE.** Исходный код, main, PLN/APX, установки, merge, Work/Codex/Arena, платные API и LIVE не изменялись/не запускались. PROJECT_PLAN rev182 только чтение.

## P0-дельта: почему одного IFC недостаточно для приёмки BUILD-01

Официальный Archicad 29 **Geometry Conversion for IFC Export** устанавливает несовместимые цели одного режима экспорта:
1. **BREP:** точная геометрия и junctions; но в IFC теряются редактируемые параметры элементов (это НЕ потеря параметров в исходном PLN). Визуальные цвета зависят от активного вида и Graphic Overrides.
2. **Parametric Extruded/Revolved:** сохраняются параметры (толщина, высота, reference line), но специализированные подрезки/стыки могут теряться; composite skins не всегда сохраняются полностью. Morph/Object/Shell и ряд сложных элементов всегда BREP.
3. **Parametric with exceptions:** может включать BREP для SEO/junctions, но это отдельный preset, не доказательство полного сохранения обеих семантик.
4. **Export gross geometry of elements (Export holes separately):** стены экспортируются без вычитания проёмов; при отключении возможен BREP вместо extrusion. Наличие IfcOpeningElement зависит также от Model Filter.
5. **Export only geometries which Participate in Collision Detection:** фильтрует материалозависимую геометрию; контроль IFC может не увидеть части модели.
6. **Explode/Split composites:** исходный IfcWall/IfcSlab может стать IFC Container без собственного тела, а тела оказываются в IfcBuildingElementPart. Наивная проверка «каждый IfcWall имеет BREP» ошибочна.

**Инженерный вывод:** G4 требует (A) нативный readback из AC29, (B) IFC-BREP профиль геометрии и (C) отдельный IFC-parametric профиль параметров, либо native-параметры при запрете второго экспорта. Два IFC профиля — не два writer: оба являются **read-only экспортом из одного сохранённого PLN**, выполняются только после отдельного разрешения на G4 и с фиксированными настройками. В текущем исследовании ничего не экспортировалось и настройки не изменялись.

Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-37.htm

## Ещё три критических условия G4

**Тип IFC ≠ native Tool.** В AC29 при mapping `by Element Type` и Roof, и Shell становятся `IfcSlab` / `PredefinedType=ROOF`; Slab становится `IfcSlab.FLOOR`, Window и Skylight — `IfcWindow`. При `by Classification` значения зависят от настроек. Поэтому `IfcSlab.ROOF` нельзя принимать за доказательство native Roof: проверять `GetDetailsOfElements` (native tool/type), GUID, параметр, SEO и BREP в Archicad. Источники: https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-51.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-35.htm .

**IFC-материалы и параметры опциональны.** В Data Conversion надо отдельно включать Element Properties, Building Material Properties, Element/Component Parameters, Door-Window Parameters и Base Quantities. IFC2x3 привязывает экспортируемые свойства Building Material к элементам, IFC4/4.3 — к IFC Materials. Отсутствие поля в IFC при отключённом preset НЕ доказывает отсутствия native материала. IFC Units (coordinates, measures) имеют отдельный preset. Источники: https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-43.htm .

**IfcBuildingStorey.GlobalId не идентификатор проекта.** AC29 выводит spatial GlobalId из Project Info ID; одинаковые Building ID + Story Number в двух проектах могут дать одинаковые IFC Story GlobalId. `Archicad GUID`, `Archicad Unique ID`, `IFC GlobalId`, `Rhino Object ID` и `GH definition provenance` — разные идентификаторы. Для G4 crosswalk ключ должен включать фактический PLN путь/снимок, story index/elevation, native GUID и проверенный IFC GlobalId; не менять Project Info. Источник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-48.htm .

## Версии / лицензии / направление

| Инструмент | Подтверждённая SOURCE версия и лицензирование | Направление и предел |
|---|---|---|
| Archicad 29 | ожидаемый build5101, коммерческий; локальный runtime NOT_VERIFIED | native BIM, readback, IFC export |
| Graphisoft Grasshopper–Archicad 29 Live Connection | официальный Windows build **3000**, Rhino 7/8, 01.10.2025; бесплатное дополнение при лицензированных AC/Rhino | GH→AC native supported types; ограниченный AC→GH, НЕ атомарная трёхсторонняя синхронизация |
| Rhino 8 + Grasshopper 1 | Rhino коммерческий; GH включён; точный Rhino 8 SR NOT_VERIFIED | Rhino geometry/attributes→GH; Rhino Object ID ≠ AC GUID |
| APA PR74/SceneWriter/SQLite/Tapir | PR74 immutable head `5a3a9201a715a5528c93bed4a5318e2acb32eea7`; локальный Tapir 1.5.10 заявлен, но runtime NOT_VERIFIED | один разрешённый writer для APA-owned BIM; limited authored typed contract |
| Archicad IFC Translator + IfcOpenShell | штатный IFC экспорт AC29 + уже изученный open-source IFC reader; точная локальная версия IfcOpenShell NOT_VERIFIED | AC→IFC→read-only QA; не native writer, не roundtrip |

Graphisoft: https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ . PR74: https://github.com/dvikt33-ux/safe-bim-layer/pull/74 . BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/issues/192 .

## Десять маршрутов BUILD-01 (готовые средства, без нового кода)

Для каждого: **выбор инструмента → завершение → обратная сверка → ГОТОВО**. Все пункты SOURCE-документированы; новые OFFLINE/INSTALLED/LIVE/ACCEPTED отсутствуют.

| № | Операция / готовый маршрут | Контроль завершения и критерий ГОТОВО | Текущий статус |
|---|---|---|---|
| 1 | **G0 identity:** AC29 `GetProjectInfo`, `GetStories`, `GetAddOnVersion`, registration; Rhino 8 `rhinocode list --json` только при SR≥8.11 и работающем Script Server; `.gh/.3dm` | read-only совпадение порт/PLN/build/APX/schema, paths/SHA, Rhino document, GH definition, единиц, story index/elevation; иначе STOP | SOURCE / INSTALLED_NOT_VERIFIED |
| 2 | **Rhino/GH source:** штатные `Query Model Objects` → `Group Content` → `Match Text Filter` → `Filter Content` | по слоям/UserText отобрать APA_Type/APA_Story/APA_Owner; freeze `.3dm + .gh`, уникальность external ID; GH filter не запускает Archicad writer | SOURCE / OFFLINE_NOT_RUN |
| 3 | **Этажи:** AC `GetStories` → GH уровни → authored `storyHeights`/story bindings | точное соответствие floorIndex/floorId/elevation; authored `SetStories` не найден: изменять этажи автоматически через PR74 = NOT_FOUND | SOURCE / STORY_WRITE_NOT_FOUND |
| 4 | **Стены:** GH контур → `apa-authored-project/1` → PR74 `CreateWalls` → SceneWriter | после разрешённой записи native Wall GUID, floor, material, thickness, intersection BREP; Save/Open; GH не пишет APA-owned Wall | SOURCE_WIRED / LIVE_NOT_RUN |
| 5 | **Перекрытия:** authored прямоугольник → PR74 `CreateSlabs` c absolute `level` | native Slab, level, thickness, material readback; отверстия/freeform/сложный composite через этот authored вход NOT_FOUND | SOURCE_RECT_ONLY |
| 6 | **Колонны/балки:** PR74 `CreateColumns` в nativeComponents; GH Beam/Column только отдельно GH-owned | native GUID/profile/material/axes; `CreateBeams` в authored allowlist отсутствует → BEAM_NOT_WIRED | SOURCE_COLUMN / BEAM_NOT_FOUND |
| 7 | **Сложная кровля:** Rhino/GH BREP как reference, либо PR74 `CreateRoofs` Basic SinglePlane + `nativeRoofJunctions`/SEO | native Roof Tool, GUID, angle, pivot, material, Roof→Wall SEO, фактический BREP после изменения; единый MultiPlane через PR74 NOT_FOUND | SOURCE_SINGLEPLANE / MULTIPLANE_NOT_FOUND |
| 8 | **Окна/двери:** `CreateWalls` прежде `CreateDoors/CreateWindows`, проверенная GDL библиотека и host GUID | native Door/Window, library part, width/height, host wall BREP, no Missing Objects, Save/Open | SOURCE_CONDITIONAL |
| 9 | **Rhino .3dm Hotlink/библиотеки:** AC File→External Content→Place Hotlink; только reference-owned | `Rhino original ID` + Layer→imported GDL Object; обновление модуля, не native Wall/Roof; проверка скрытых объектов, Undo, Missing Objects | SOURCE_REFERENCE / NATIVE_NOT_FOUND |
| 10 | **G4 QA/нормы/откат:** native GUID/type/material readback + IFC-BREP profile + IFC-parametric profile + IfcOpenShell + `GetIFCIdsOfElements` если доступна | native/IFC crosswalk, BREP, holes, SEO, IFC mapping/units/export filters, численные проверки СП по конкретным редакциям; Guarded Save/Close/Reopen, повтор inventory; cross-app atomic rollback NOT_FOUND | SOURCE_PROPOSED / G4_NOT_RUN |

**Общий transaction rule:** до операции — снимок `.gh/.3dm`, plan hash и GUID inventory; один владелец записи. После — остановить пересчёт/зафиксировать GH definition, проверить native readback; лишь затем разрешённый Save/Open. При UNKNOWN/timeout/удалении/конфликте — STOP, read-only reconciliation, без повторного CREATE. GH-owned элементы и APA-owned GUID не должны пересекаться. Teamwork reservation-риски из исторических источников нельзя автоматически переносить на одиночный PLN.

**Нормы:** GH численно проверяет размеры/площади/просветы, но не выдаёт нормативную экспертизу. Для помещений `IfcRelSpaceBoundary` (границы) ≠ IFC Space Containment (только Object/Lamp/Morph/Slab) ≠ hosted Door/Window relation; для hosted openings нужны native Wall GUID и IfcRelVoids/IfcRelFills при наличии экспорта. Источник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm .

## Конкретный G4 preflight для будущего санкционированного испытания

**G4-0:** проверить G0 receipt и exact PLN/SHA, разрешение G3/G4, список GUID/этажей/материалов; проверить настройки 3D вида и IFC Translator (Type Mapping, Data Conversion, Geometry Conversion, Unit Conversion, Model Filter, export view visibility). Без совпадения STOP.

**G4-A native:** `GetDetailsOfElements` / `GetModelDumpV1` если фактически зарегистрирован / `GetSolidElementLinks` для junction; снимок `AC GUID→native Tool→floor→material/composite→host/SEO→BREP`. Схема Tapir 1.5.10 не гарантирует `GetModelDumpV1`, нужен runtime check.

**G4-B IFC geometric:** отдельный заранее одобренный preset с BREP и junctions, holes represented correctly; не включать gross host geometry при проверке реальных вырезов; записать hash preset/translator, схему IFC, units, Model Filter, visible view. Проверять тела включая parts/containers и IFC GlobalId mapping; не принимать цвет за Building Material.

**G4-C IFC parametric:** отдельный заранее одобренный preset Parametric либо native readback как источник параметров; фиксировать ожидаемую потерю отдельных junctions и composite skin structure. Если два preset отсутствуют и запрещено менять конфигурацию, **G4_IFC_DUAL_PROFILE_BLOCKED**, а не подмена BREP параметрической моделью.

**G4-D Save/Close/Reopen:** только на разрешённой scratch PLN; сравнить native GUID sets, native tool, story, dimensions, material, host, SEO, body signatures и соответствующие IFC crosswalk; UNKNOWN→STOP, откат только из согласованных сохранённых копий, не полагаться на общий Undo.

**Критерий ГОТОВО:** два различных новых задания BUILD-01 (G5), у каждого подтверждённые G0–G4 receipts, native BIM и независимый BREP после Save/Open. Текущий статус **НЕ ГОТОВО**.

## Два важных контрапримера

- IFC `IfcSlab.ROOF` проходит типовую проверку, но native элемент — Shell: **ложный PASS**, нужен native Tool.
- IFC `IfcWall` без BREP при включённом `Split Complex Building Elements`: возможно IFC Container + IfcBuildingElementPart, а не потеря стены. Нужен обход частей и native GUID crosswalk.

## Источники, границы и следующее P0

Прочитаны: issue #192, PR74, NEXT, triad pivot, матрица 61, свежий №1 04:58Z, доступный №3 20.10 18Z, код PR74 (immutable), официальные Graphisoft AC29 Type Mapping / Data Conversion / Geometry Conversion / IFC Data Types / Unit Conversion / Predefined Property Mapping, Graphisoft downloads. Отдельный файл checks содержит **26 предметных SOURCE-сверок**, два документарных контрааудита — отдельный файл audits. Это НЕ 26 независимых источников и НЕ нативные испытания.

**Следующий P0:** read-only G0 manifest фактической среды и квалификация существующих IFC Translator presets; затем authored PR74 read-only preflight G1. Без разрешения G3/LIVE не запускать.
