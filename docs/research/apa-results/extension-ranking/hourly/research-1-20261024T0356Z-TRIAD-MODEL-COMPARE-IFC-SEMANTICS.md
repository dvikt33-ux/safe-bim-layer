# APA №1 — 2026-10-24 03:56Z | Model Compare AC29, IFC property-only и сохранение BIM-иерархии

**Исследователь №1; BUILD-01 #192; P0 = Archicad 29 build 5101 + Rhino 8 + Grasshopper.**
**Режим:** SOURCE_ONLY. **OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых.** G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. MODEL_MODE_NOT_VERIFIABLE. Существующий исторический PR74 LIVE не приравнивается к новому BUILD-01.

## 0. Реальное влияние на трёхстороннюю сборку BUILD-01

**Новая полезная дельта:** официальный Archicad 29 содержит штатный **Model Compare**, позволяющий независимо увидеть новые/изменённые/удалённые 3D-элементы и изменения параметров между сохранёнными PLN/PLA или временными версиями. Это готовый **контроль результата после** разрешённой операции, без нового writer, но НЕ синхронизатор и НЕ автоматический API-gate. Важный риск: сравнение зависит от View Settings (Design Options, Layers, Renovation, Partial Structure Display); видимые «изменения» могут оказаться отличиями видов, а не модели.

**Вторая дельта:** штатный Archicad 29 `Update with IFC Model` обновляет **IFC-атрибуты, свойства и классификационные ссылки** при совпадающем IFC GlobalId; **геометрия, размер, цвет, слой и удалённые элементы не обновляются**. Поэтому это не путь Rhino/GH→native BIM geometry и, если включить его на APA-owned элементах, появится **второй writer** — запрещено без отдельного решения. **Третья дельта:** IFC Export `Keep Hierarchy` для Curtain Wall/Stair/Railing сохраняет состав подэлементов в IFC; `single element` и некоторые `Explode Composite` меняют экспортную структуру. IFC GlobalId, Archicad Unique ID и Rhino Object ID — разные сущности.

**Оценка P0:** Model Compare может закрыть часть независимого визуального QA после будущего G4; IFC-транслятор помогает построить read-only матрицу сохранения семантики. Ни одно средство не доказывает P0: «операция в любой из трёх программ → автоматическое согласованное изменение остальных с сохранением native GUID». Прямую запись GH–AC для APA-owned элементов не разрешать. PR74/SceneWriter/SQLite остаются единственным APA-owned writer.

## 1. Пять карточек решений

### C01 — Archicad 29 Model Compare: готовый контроль изменения нативной модели
- **Операция BUILD-01:** после разрешённого Save/Close/Reopen сравнить контрольную scratch PLN «до/после» и найти изменённые, добавленные, удалённые Walls, Slabs, Roof, Doors, Windows, Objects.
- **Версия/лицензия:** встроенная функция Archicad **29** (коммерческая лицензия Archicad; не отдельный платный API). **SOURCE**, локальный build 5101 не опрошен.
- **Официальный первоисточник AC29:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-3.htm .
- **Точный контракт:** Design > Model Compare → Model 1 Current model → Model 2 saved PLN/PLA → Compare. Выделяет new/modified/deleted **3D** элементы; показывает изменённые наборы параметров; 2D не сравнивает. Результат фиксирован во времени; после нового редактирования сравнение запускают заново.
- **Направление:** Archicad PLN snapshot A + snapshot B → **read-only visual QA** в Archicad. Ни Rhino/GH, ни SceneWriter не обновляются. Создание Issue не входит в разрешённый сценарий.
- **Ограничение:** GUI-процедура; машинный API-результат и GUID/host/материал по всем типам не доказаны. Не подменяет независимый typed readback.
- **Поручение №2 / I04-01:** без LIVE описать G4 протокол «две сохранённые версии → одинаковые 3D View Settings → Model Compare → перечень различий → независимый GetDetails/IFC/GUID readback»; отделить визуальный PASS от native ACCEPTED.

### C02 — AC29 Select View + Filter by Parameter Sets: защита от ложного изменения
- **Операция:** при проверке сложной кровли или окон отличить реальную геометрию от эффекта активного Design Option, Layer Combination, Renovation Status и Partial Structure Display.
- **Версия/лицензия:** Archicad 29, штатно, лицензия Archicad.
- **Первоисточник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-7.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-8.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-9.htm .
- **Контракт:** `Apply Common View Settings` обеспечивает общие настройки вида; при отключении сравниваются разные виды. `Filter by Element Criteria` (в том числе slabs) и `Filter by Parameter Sets` ограничивают список. Формат списка поддерживает Status, Tool, ID, Source, Classification. Список и сравнение 3D — не полный machine-readable audit.
- **Направление:** Archicad→Archicad READ/visual compare; автоматического GH/Rhino обновления нет.
- **Ограничение:** без фиксации view configuration разница может быть ложноположительной; `ID` в списке не доказан как нативный GUID.
- **Поручение №2 / I04-02:** подготовить read-only checklist view signature (layer combination, design option, renovation, partial structure, 3D filter) и запрет утверждать geometry drift только по цвету/списку.

### C03 — AC29 IFC Export: `Keep Hierarchy` и различение native/IFC identity
- **Операция:** после создания Curtain Wall, Stair, Railing, composite Wall, окна/двери проверить, что IFC QA не «сплющил» структуру до одного объекта.
- **Версия/лицензия:** штатный IFC export Archicad 29, коммерческая лицензия Archicad; отдельного API не требуется. Настройки экспортного Translator локально неизвестны.
- **Первоисточник AC29:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-48.htm .
- **Контракт:** `Keep Hierarchy` экспортирует иерархический Curtain Wall/Stair/Railing как IFC Container + subelements; `Convert to single element` теряет иерархию. `Explode Composite and Complex Profile elements into parts` делает родительский IFC Container без собственной геометрии и дочерние части. IFC `GlobalId` не равен Archicad `Unique ID`; `Tag` может происходить из Unique ID. `IfcBuildingStorey` отражает home story по умолчанию, но часть объектов может быть отнесена к Zone/Site/Building.
- **Направление:** Archicad→IFC **экспорт для QA**, не IFC→native Archicad sync; Rhino/GH не получают сохранённую нативную BIM-параметрику автоматически.
- **Ограничение:** IFC Container/child count может отличаться от Archicad GUID count без потери исходных элементов; нельзя проверять native GUID простым равенством числа IFC entities. Экспорт — не G4 acceptance.
- **Поручение №2 / I04-03:** подготовить read-only таблицу `AC GUID / AC Tool / Home Story / IFC GlobalId / IfcType / IFC parent-child / export mode`, отдельные ожидания для CurtainWall/Stair/Railing/Composite; не менять Translator без допуска.

### C04 — AC29 `Update with IFC Model`: **только метаданные**, не геометрия
- **Операция:** оценить предложение синхронизировать классификации и свойства из IFC, созданного Rhino/GH, с существующими элементами Archicad.
- **Версия/лицензия:** встроенный Archicad 29, коммерческий продукт. Локальный запуск не разрешён.
- **Официальный первоисточник AC29:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-9.htm .
- **Контракт:** общий элемент определяется совпадающим IFC `GlobalId`; импортируются IFC Attributes/Properties/Classification References по mapping translators. **Deleted/modified elements ignored; geometry (size/color/layer) not updated; locked elements not updated.** Некоторые опции override/remove меняют существующие IFC-данные, поэтому это реальная запись.
- **Направление:** внешний IFC→Archicad **property-only write**; **НЕ** Rhino BREP→native Roof/Wall/Opening, **НЕ** двусторонняя синхронизация.
- **Ограничение:** для APA-owned элементов этот штатный импорт стал бы вторым writer вне SceneWriter; НЕ выполнять. Даже при совпавшем GlobalId не доказано сохранение всех Archicad native properties/GDL parameters.
- **Поручение №2 / I04-04:** пометить IFC Update как `SECOND_WRITER_PROHIBITED` в карте маршрутов; в будущих G0/G1 только проверить настройки Translator по документации, без импорта.

### C05 — Rhino.Inside: исключение ложного «готового Archicad-моста»
- **Операция:** выбрать программу-исполнитель для сложной кровли и выяснить, можно ли готовым Rhino.Inside загрузить Rhino внутрь Archicad 29.
- **Версия/лицензия:** Rhino.Inside — open-source технология McNeel для Windows; Rhino 8 коммерческий; официальный готовый продукт `Rhino.Inside.Revit` относится к Revit, **не Archicad**.
- **Первоисточник McNeel:** https://www.rhino3d.com/features/rhino-inside/ ; https://www.rhino3d.com/en/features/rhino-inside-revit/ .
- **Контракт:** общая технология встраивания Rhino/GH в 64-bit host не равна наличию готового host add-on для Archicad 29. В проверенном официальном списке готовый Archicad-specific host отсутствует; утверждать глобальное отсутствие сторонних разработок нельзя.
- **Направление:** host-specific, для Archicad 29 `NOT_PROVEN`. Официальный GH–AC29 Live Connection build3000 — отдельный продукт (https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/), направленный обмен, не Rhino.Inside.
- **Ограничение:** не устанавливать Revit-ориентированный продукт ради AC29 и не объявлять совместимость по общему названию.
- **Поручение №2 / I04-05:** исключить Rhino.Inside.Revit из обязательного стека BUILD-01; оставить Graphisoft GH–AC29 Live Connection как SOURCE-only, проверить точный локальный пакет при санкционированном G0.

## 2. Реестр 26 предметных SOURCE-сверок (не 26 независимых источников)

| № | Сверенный факт/контракт | Первоисточник/доказательство | Итог |
|---:|---|---|---|
| 01 | Исследовательская ветка существует, точное имя | GitHub search_branches | PASS |
| 02 | BUILD-01 #192: G0–G5 и единственный writer | https://github.com/dvikt33-ux/safe-bim-layer/issues/192 | PASS |
| 03 | PR74 draft/open, исторический 21-элементный прототип не новая BUILD-01 | https://github.com/dvikt33-ux/safe-bim-layer/pull/74 | PASS |
| 04 | P0 triad, запрет LIVE/нового writer | docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md, blob 896fa3af... | PASS |
| 05 | NEXT_RESEARCH_PRIORITIES существует по пути extension-ranking, rev182 только чтение | docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md, blob 6f074693... | PASS |
| 06 | Матрица декларирует count=61; источник без правок | docs/research/apa-results/extension-ranking/priority_matrix_20261018.json, blob 9cb5e6f... | PASS |
| 07 | Свежий №2 03Z: RhinoCode PID, PR74 ограниченный roof writer | hourly/research-2-integration-2026-10-24T03Z-report.md, blob 16285d21... | PASS |
| 08 | №2 03Z контрааудиты: Content Cache не AC transaction | hourly/research-2-integration-2026-10-24T03Z-audits.md, blob e8f0426... | PASS |
| 09 | Последний доступный №3 20.10 18Z: G0 без receipt | hourly/audit-2026-10-20-18-A.md, blob 5aa388a... | PASS / STALE |
| 10 | PROJECT_PLAN в verified-results ветке rev197, не переписывать; rev182 исторический | docs/research/apa-results/control/PROJECT_PLAN.json, blob b079bb94... | PASS |
| 11 | Model Compare AC29 сравнивает только 3D new/modified/deleted | https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm | PASS |
| 12 | Model Compare принимает Current/PLN/PLA/SAF, Hotlink before-after | тот же AC29 Model Compare | PASS |
| 13 | Model Compare timestamp immutable, нужен повторный запуск после изменений | тот же AC29 Model Compare | PASS |
| 14 | Saved version: Design > Model Compare → Current vs saved → Compare | https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-3.htm | PASS |
| 15 | View options/layers/renovation/partial structure меняют видимый diff | https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-7.htm | PASS |
| 16 | Common View Settings можно отключить для разных видов | тот же AC29 Select View | PASS |
| 17 | Filter by Element Criteria поддерживает выбор slabs | https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-8.htm | PASS |
| 18 | Filter by Parameter Sets, list Status/Tool/ID/Source/Classification | тот же AC29 Filter | PASS |
| 19 | Review Model Compare: red deleted, blue new, blended modified | https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-9.htm | PASS |
| 20 | IFC GlobalId не Archicad Unique ID, Tag может происходить из Unique ID | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-48.htm | PASS |
| 21 | IFC Keep Hierarchy для CurtainWall/Stair/Railing сохраняет subelements | тот же AC29 IFC Data Types | PASS |
| 22 | IFC Convert to single element теряет иерархию | тот же AC29 IFC Data Types | PASS |
| 23 | IFC Explode Composite создаёт IFC Container/parts | тот же AC29 IFC Data Types | PASS |
| 24 | IFC Update совпадает по GlobalId, property/classification-only | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-9.htm | PASS |
| 25 | IFC Update не меняет geometry/size/color/layer; не обновляет locked | тот же AC29 Update with IFC | PASS |
| 26 | Rhino.Inside общий Windows host framework, официальный готовый Revit add-on не Archicad | https://www.rhino3d.com/features/rhino-inside/ ; https://www.rhino3d.com/en/features/rhino-inside-revit/ | PASS |

**Подсчёт:** 26 проверенных утверждений/репозиторных сверок, 5 карточек (4 AC29 готовые возможности/ограничения + 1 отсев неподтверждённого моста), 2 контрааудита. SOURCE != OFFLINE/LIVE. Проверки 01–10 — доступность/контекст; 11–26 — официальные контракты. Локальных запусков нет.

## 3. Контрааудит A — «Model Compare заменяет cross-app GUID QA и синхронизацию?»

**Контртезис:** Model Compare 29 — визуальное сравнение двух AC 3D views по snapshot. Нет подтверждённого API для автоматического принятия/передачи изменений Rhino/GH; нет AC→GH→Rhino atomic commit, owner crosswalk, rollback. View Settings способны породить ложные изменения. Сопоставление по отображаемому `ID` не доказывает native GUID; только независимый GUID/IFC/BREP readback после разрешённого Save/Open. **Вердикт:** полезный G4 human QA; `FULL_TRIAD_SYNC=NOT_PROVEN`, `G4=NOT_RUN`.

## 4. Контрааудит B — «IFC roundtrip сохранит нативную кровлю, отверстия, свойства и GUID?»

**Контртезис:** `Update with IFC Model` в AC29 специально не обновляет geometry; IFC GlobalId != Archicad Unique ID, иерархические объекты могут быть экспортированы как single IFC entity или container+children. Даже успешная проверка свойств по IFC не доказывает, что остались нативные Roof, GDL window/door hosts и SEO. IFC Update — дополнительный writer, не разрешён. **Вердикт:** IFC пригоден для независимого **read-only семантического контроля** при закреплённом translator; `NATIVE_GEOMETRY_SYNC=NOT_FOUND`, `GUID_ROUNDTRIP=NOT_PROVEN`.

## 5. Передача №2 и строгие ворота

**№2 I04-01:** описать G4 сравнение двух сохранённых scratch PLN в штатном Model Compare; предусмотреть фиксацию одинаковых view settings и перечень изменённых 3D-элементов. **№2 I04-02:** view signature + список фильтров и запрет считать `Model Compare ID` доказанным native GUID. **№2 I04-03:** IFC export semantics checklist для parent-child, home story, materials, host opening, GlobalId, composite skins; без изменения Translator. **№2 I04-04:** `Update with IFC Model` в карте инструментов пометить `SECOND_WRITER_PROHIBITED` для APA-owned. **№2 I04-05:** не включать Rhino.Inside.Revit в установочный список AC29.

**Текущая цепочка:** Rhino8/GH геометрия (SOURCE) → freeze/typed authored JSON → PR74/SceneWriter (без LIVE) → AC29 native readback (будущий) → Guarded Save/Close/Reopen (будущий) → AC29 Model Compare + независимый GUID/BREP/IFC check (будущий). Любой отсутствующий GUID/host, изменение типа, неоднозначный owner, неизвестный active document, conflict или write timeout: STOP и read-only reconciliation. Ни один из этих шагов не выполнялся на Windows в данном исследовании.

**Изменения:** только новый Markdown-отчёт в исследовательской ветке. Никаких изменений main, исходного кода, APX/PLN, конфигурации, установок, merge, LIVE, Work/Codex/Arena, платных API или PROJECT_PLAN. Публикационный commit и повторный fetch должны подтверждаться отдельно.
