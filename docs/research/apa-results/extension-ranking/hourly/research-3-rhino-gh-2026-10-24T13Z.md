# APA R3 — Rhino 8 / Grasshopper: геометрия, параметрика, независимая BIM-проверка
**Цикл:** 2026-10-24 13Z (16:00 МСК). **Объект:** BUILD-01, issue #192. **Ветка:** `research/apa-extension-ranking-hub-20261018`.
**Роль:** R3 — вычислительная геометрия, параметрические и нормативные проверки. Не дублирует R1 (нативные команды Archicad) и R2 (мосты и ownership).
**Основание GitHub (прочитано):** `docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md` (канон P0); `docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md` (SHA `896fa3af0953468ca58fca710f32cb926504f582`); issue #192; R2 12Z index (SHA `2167e51c530b1e6c1f1920bc754603bd1bfad9b0`). Новый A5 текущего цикла ещё не должен существовать до фазы :40; поручения A5 = **PENDING**, не подменяются догадками. Исторический PROJECT_PLAN rev182 не изменялся.

## 0. Итог для I4
1. **Встроенный Grasshopper Rhino 8 уже закрывает параметрическое построение, Boolean, BREP-предпроверку и дерево вариантов без дополнительного платного плагина.** Однако геометрический Brep и Rhino Content Cache не равны native Archicad BIM и не заменяют SceneWriter.
2. **Две конкретные семантические границы Graphisoft GC29:** `Slab` принимает **горизонтальную planar Surface с отверстиями**, а `Roof` принимает **одну планарную наклонную грань** и создаёт `Single-plane Roof`. Криволинейный контур Slab сегментируется. Из этого следует воспроизводимый геометрический маршрут для многоскатной кровли **как набора отдельных планарных скатов**, но не доказанная единая `Multi-plane Roof`.
3. В `Roof` положение/уклон определяет **сама входная плоскость**, а не `Roof Pitch`/`Offset from Home Story` из Favorite. Поэтому в GH-источнике нужно фиксировать плоскость, нормаль, вершины, ориентацию, story и материал; только Favorite недостаточен.
4. **Новый кандидат независимого аудита:** IfcOpenShell **0.9.0.post1** (15.10.2026, LGPL, Windows wheels) + IfcTester **0.9.0** (29.09.2026, LGPL). Это read-only IFC-аудит **после** отдельного разрешённого экспорта из Archicad; связка конкретных версий вместе, экспорт и установленные пакеты **не тестировались**. IDS **не проверяет геометрию**.
5. **Ladybug Tools** полезен для климата/инсоляции/энергетических исследований (LBT 1.10.0 Rhino8; ветка 1.10.58 от 09.10.2026), но не заменяет проверку СП. **Karamba3D** поддерживает Rhino8, однако его бесплатная демоверсия ограничена; как обязательную постоянно бесплатную зависимость BUILD-01 не включать.

## 1. SOURCE-журнал — 32 отдельных предметных проверок
Каждая строка = конкретное утверждение, сопоставленное с реально открытым первоисточником/документацией; повторные утверждения не превращаются в OFFLINE или INSTALLED. Источники Graphisoft GC29 найдены как индексированные фрагменты официального PDF; полный PDF постранично не был загружен, поэтому ограничения из него относятся к **SOURCE**, а не локальной приёмке.

| ID | Источник | Проверенное утверждение / ограничение | URL |
|---|---|---|---|
| S01 | Graphisoft | AC29 Live Connection build 3000 (01.10.2025) заявлен совместимым с Rhino 7/8; установленность не проверена | https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ |
| S02 | Graphisoft | Live Connection не поддерживает Archicad Start Edition | https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ |
| S03 | Graphisoft GC29 | Slab требует горизонтальную плоскость XY либо параллельную ей | https://help.graphisoft.com/AC/29/INT/GC.pdf |
| S04 | Graphisoft GC29 | Slab допускает planar Surface с отверстиями — реальная возможность GH→native Slab, но не доказанный маршрут через SceneWriter | https://help.graphisoft.com/AC/29/INT/GC.pdf |
| S05 | Graphisoft GC29 | Криволинейный spline-контура Slab сегментируется при переводе в Archicad | https://help.graphisoft.com/AC/29/INT/GC.pdf |
| S06 | Graphisoft GC29 | Roof принимает planar polygon, в том числе наклонный в пространстве | https://help.graphisoft.com/AC/29/INT/GC.pdf |
| S07 | Graphisoft GC29 | Описанный Roof-компонент создаёт Single-plane Roof, а не доказанный native Multi-plane Roof | https://help.graphisoft.com/AC/29/INT/GC.pdf |
| S08 | Graphisoft GC29 | Геометрическая плоскость определяет pitch/elevation; соответствующие значения из Roof Favorite не управляют результатом | https://help.graphisoft.com/AC/29/INT/GC.pdf |
| S09 | McNeel | Grasshopper встроен в Rhino 8; отдельная лицензия Grasshopper не требуется, но сам Rhino коммерческий | https://www.rhino3d.com/features/ |
| S10 | McNeel | Rhino 8 Content Cache обновляет Rhino-объекты без прежнего удаления; это не BIM-синхронизация Archicad | https://www.rhino3d.com/features/grasshopper/content-cache/ |
| S11 | McNeel | Rhino 8 ShrinkWrap производит watertight mesh, что не эквивалентно native BIM-кровле/стене | https://www.rhino3d.com/en/8/new/ |
| S12 | McNeel | Rhino 8 Grasshopper имеет Object Attributes, UserText и Live Baking в Rhino | https://www.rhino3d.com/features/ |
| S13 | McNeel | Model units и absolute tolerance влияют на trim/offset/boolean; допуски должны фиксироваться до работы | https://docs.mcneel.com/rhino/8/help/fr-fr/documentproperties/units.htm |
| S14 | McNeel | GH DataTree — ветви GH_Path; пути/индексы не являются Archicad GUID | https://developer.rhino3d.com/en/guides/rhinopython/grasshopper-datatrees-and-python/ |
| S15 | RhinoCommon | Brep.IsSolid определяет closed oriented manifold | https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/issolid |
| S16 | RhinoCommon | Brep.IsValidTopology проверяет топологию BREP | https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/isvalidtopology |
| S17 | RhinoCommon | Brep.CreateBooleanDifference принимает tolerance и учитывает ориентацию тел | https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/createbooleandifference |
| S18 | RhinoCommon | Brep.JoinBreps может вернуть несколько BREP, не обязательно один замкнутый solid | https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/joinbreps |
| S19 | RhinoCommon | VolumeMassProperties.Compute(Brep) вычисляет объёмные характеристики; failure может дать null | https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.volumemassproperties/compute |
| S20 | RhinoCommon | Brep.CreateFromMesh создаёт геометрические грани из mesh, но не BIM-семантику | https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/createfrommesh |
| S21 | Grasshopper Docs (неофициальный каталог) | Solid Difference выполняет Boolean Difference для наборов Brep; не создаёт native hosted opening | https://grasshopperdocs.com/components/grasshopperintersect/solidDifference.html |
| S22 | Ladybug Tools | Стабильный LBT 1.10.0 от 25.02.2026 работает в Rhino 6–8 Windows/Mac | https://discourse.ladybug.tools/t/ladybug-tools-for-grasshopper-1-10-0-release/40026 |
| S23 | Ladybug Tools | Код Ladybug Tools распространяется преимущественно по GPL-3.0; проверять исключения конкретных пакетов | https://www.ladybug.tools/about |
| S24 | Ladybug Tools | Сборка lbt-grasshopper v1.10.58 выпущена 09.10.2026; наличие в локальной системе неизвестно | https://github.com/ladybug-tools/lbt-grasshopper/releases |
| S25 | Karamba3D | Karamba3D 3.1 заявляет Rhino 8 (минимум SR7) на Windows | https://karamba3d.com/get-started/ |
| S26 | Karamba3D | Бесплатный demo на один месяц; Pro/EDU — платные лицензии, поэтому не считать постоянно бесплатным | https://karamba3d.com/get-started/demo/ |
| S27 | IfcOpenShell | Версия 0.9.0.post1 опубликована 15.10.2026, есть win_amd64 wheels для Python 3.10–3.15; LGPL-3.0-or-later | https://pypi.org/project/ifcopenshell/ |
| S28 | IfcTester | Версия ifctester 0.9.0 опубликована 29.09.2026, LGPL-3.0-or-later | https://pypi.org/project/ifctester/ |
| S29 | IfcTester | Поддерживает проверку IFC по IDS и выдачу отчётов CLI/JSON/SQLite; не является нативным Archicad writer | https://docs.ifcopenshell.org/ifctester.html |
| S30 | buildingSMART | IDS охватывает алфавитно-цифровые свойства, количества, классификации, материалы, связи, но НЕ геометрию | https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/page/4/ |
| S31 | Graphisoft | Trim Elements to Roof/Shell ассоциативен, Crop to Single-plane Roof статичен; требуется проверка native join после создания | https://helpcenter.graphisoft.com/user-guide/76500/ |
| S32 | McNeel | Rhino 8 не бесплатен: полная evaluation 90 дней, после срока сохранение/плагины прекращают работу | https://www.rhino3d.com/en/download/ |

## 2. Шесть воспроизводимых графов Grasshopper (проектные маршруты, не выполненные тесты)
### GH-01 — перекрытие с отверстием, без потери нативного типа
`Rhino closed outer curve + closed inner loops` → `GH planar Surface with holes` → проверка `XY-parallel / closed / self-intersection / area` → **кандидат** `Graphisoft AC Slab` (native Slab) → AC readback `Slab GUID, story, thickness, composite/material, hole contours, BREP` → Save/Close/Reopen → повторное сравнение.
**Существенно:** официальный компонент GH умеет отверстия в Slab; но передача именно через **единственный APA SceneWriter** не доказана. Запрещено без допуска использовать GH как параллельного native writer в PLN. Пока R3 передаёт I4 только геометрию и спецификацию отверстий; подключение к PR74 = `NOT_FOUND`.

### GH-02 — сложная многоскатная кровля из планарных граней
`ridge/eave 3D points` → `GH polygon per facet` → `planarity test + winding/normal + shared-edge consistency` → `Roof facet records` → кандидат `Graphisoft Roof Single-plane` **для каждого ската** → проверка стыков и наличия нативных Roof GUID → ассоциативный Trim to Roof/Shell **только после разрешённого нативного создания** → Save/Open.
**Контроль:** 1 исходный скат ↔ 1 native Roof; площадь/наклон/высотные отметки; пары общих рёбер; отсутствующие/дублированные скаты; BREP после Trim. `Roof Pitch` в Favorite не заменяет проверку наклонной плоскости. Единый native Multi-plane Roof из произвольного GH BREP = `NOT_FOUND`. Отдельная native Shell для произвольной NURBS = `NOT_FOUND`.

### GH-03 — окна/двери/проёмы: геометрическая проверка без ложного BIM
`host wall envelope` + `opening cutter solid` → `GH Solid Difference` → `closed manifold + expected void volume + distance to wall edges` → **отдельная семантическая запись** `host_wall_key, opening_key, width, height, sill, offset, family` → существующие native Window/Door commands только через I4/SceneWriter → readback host GUID, opening GUID, type, params.
**Запрет подмены:** Boolean Difference/BREP-hole не создаёт hosted Window/Door в Archicad. Отдельный native generic Opening требует самостоятельной проверки контракта, `NOT_FOUND` до этого.

### GH-04 — два этажа, точные уровни, пересечения конструкций
`Story table (index, elevation_m)` → `GH tree {story;type;ordinal}` → `absolute Z in m` + `story-relative offset explicitly` → `floor slabs / wall envelopes / beam axes` → `collision intersections` → передать **типизированные намерения**, а не GH branch-path как GUID. Проверить замкнутость контуров, перекрытие этажей, координатный масштаб, host/story mapping. Изменение этажей должно пересчитать зависимые координаты, но это не доказательство автоматического изменения Archicad Stories.

### GH-05 — нормативная/эксплуатационная геометрия
`approved project requirement (source, revision, clause, units, threshold)` → `GH geometry (clear widths/heights, slopes, turning circles, distances)` → `numerical comparison + violation geometry + evidence`. Отдельно, при наличии лицензии/плагина, Ladybug для солнечной радиации, ориентации и климата. **Без утверждённого порога из применимого СП** результат `RULE_UNSPECIFIED`, не `COMPLIANT`. GH/ Ladybug не заменяют нормативную экспертизу и не покрывают все пожарные/доступностные требования.

### GH-06 — независимый IFC-аудит, после санкционированного экспорта
`AC29 native PLN` → `IFC export` → `IfcOpenShell read-only: entity types, GlobalId, spatial containment, material relations, openings/voids/fills` → `IfcTester IDS: properties, quantities, classifications, material, relations` → `geometry separately: solids, volumes, bbox, tolerance` → сравнить с AC native inventory после Save/Open. **IFC GlobalId нельзя без доказательства считать равным Archicad internal GUID.** Экспорт IFC, парсер, IDS и связка версий локально не проверены.

## 3. Контракт передачи I4 (спецификация, НЕ новый writer/router и НЕ утверждение, что PR74 уже принимает поля)
`source_key` — стабильный логический ключ исходного GH-элемента; `target_native_type` — Wall/Slab/Beam/Column/Roof/Window/Door; `story_index`, `z_abs_m`, `z_rel_m`; `host_source_key` — для проёмов; `geometry_role` — outer/inner/axis/roof_facet; `geometry_kind` — planar_curve/planar_surface/BREP; `is_closed`, `is_planar`, `normal`, `winding`; `units`, `abs_tol_m`; `material_key`, `composite_key`; `expected_area_m2`, `expected_volume_m3`, `expected_bbox_m`; `origin_document_id`, `definition_revision`.
**Принцип:** GH tree path и Rhino ObjectId не становятся AC GUID автоматически. Связь `source_key → AC GUID` должна проходить через **существующий** APA binding/SQLite после нативной записи. Нельзя выдавать описанный контракт за реализованный вход PR74: до проверки фактической схемы `CONTRACT_ADAPTER_NOT_VERIFIED`.
**Численные допуски:** не придумывать фиксированный `epsilon`. До тестов G0 зафиксировать Rhino model units + absolute/angle tolerance, AC units, единицы IFC и требуемую точность проекта; сравнения BREP/объёмов делать в согласованных единицах. `Brep.IsSolid=true` и `IsValidTopology=true` в Rhino — **предпроверка**, не нативный Archicad BREP PASS.

## 4. Два внутренних контрааудита
**CA-R3-01 / семантика:** `GH Solid Difference` создаёт только Brep → не hosted opening; `Content Cache` управляет Rhino-объектами → не AC native BIM; `ShrinkWrap` даёт mesh → не Roof/Slab; `Slab Surface with holes` **может** создать native Slab через официальный GH writer, но это конфликтует с требованием единого SceneWriter при одновременной записи; `IDS` не проверяет геометрию. **Итог:** ни один путь не объявлен трёхсторонней транзакционной синхронизацией.
**CA-R3-02 / точность:** геометрическая замкнутость Rhino BREP не гарантирует сохранение BIM-класса, слоёв, композитов, материалов, связей и GUID после AC Save/Open. Криволинейный контур Slab в GC29 сегментируется; Roof pitch определяется входной плоскостью; IFC GlobalId не равен автоматически AC GUID. **Итог:** требуется native readback после разрешённого G3/G4, а не только GH preview.

## 5. Приоритеты готовых решений
| Приоритет | Средство | Лицензия/совместимость | Функция | Вердикт |
|---|---|---|---|---|
| P0 | Rhino 8 Grasshopper 1 + стандартные GH-компоненты | включён в **лицензируемый Rhino 8** | параметрика, точные контуры, Boolean, DataTree, QC | SOURCE; без установки |
| P0 | Graphisoft GC29 build 3000 | официальный addon AC29/Rhino8; локальная установка неизвестна | Slab с отверстиями, Single-plane Roof; **сам native writer** | SOURCE; **запись только после отдельного разрешения и ownership-решения** |
| P1 | RhinoCommon (в Rhino 8) | API Rhino | BREP topology/volume/boolean; потенциально нужен существующий исполняющий граф или код | SOURCE, не новый writer |
| P1 | IfcOpenShell 0.9.0.post1 + IfcTester 0.9.0 | LGPL; Windows wheels; пара совместно не тестировалась | независимый IFC/IDS read-only аудит | SOURCE, INSTALL_NOT_VERIFIED |
| P2 | Ladybug Tools LBT 1.10.x | GPL-3.0, Rhino8 | климат/солнце/энергия, не строительные нормы | SOURCE, INSTALL_NOT_VERIFIED |
| EXCLUDE | Karamba3D 3.1 | demo 1 месяц, затем платная лицензия | FEM, не обязательный P0 | не считать бесплатно доступным постоянно |
| EXCLUDE | Elefront 5.x | неофициальный каталог Rhino Packages указывает Rhino7 и не подтверждает лицензию | bake/attributes в Rhino, не native AC | RHINO8/LICENSE_NOT_VERIFIED; не обязательная зависимость |
| EXCLUDE | Rhino.Inside.Revit / Rhino 3DM Hotlink | не native Archicad writer для Wall/Slab | межпрограммный перенос/геометрия | не выдавать за BIM-синхронизацию |

## 6. Поручения интегратору I4 на фазу :20
1. **I4-R3-P0-A:** на текущем PR74/SceneWriter найти **фактический существующий вход** для геометрии `Slab outer + inner loops` и `Roof facets`; указать точный путь/команду/schema и что делать, если прямого контракта нет. Не писать новый адаптер. Критерий: `SUPPORTED_BY_EXISTING_CONTRACT` или `NOT_FOUND`.
2. **I4-R3-P0-B:** выбрать один ownership-режим: (А) GH расчёт/preview/read-only → только APA SceneWriter пишет AC, либо (Б) отдельная **изолированная** GH-native проверка с разрешением, не одновременно с SceneWriter. Не утверждать, что оба writer транзакционно согласованы.
3. **I4-R3-P0-C:** включить в G0 манифест `Rhino 8 SR, units, absolute tolerance, GH definition hash, GC29 build, Archicad PLN/story, IFC exporter profile`. Пока нет — `INSTALLED_NOT_VERIFIED`.
4. **I4-R3-P1-D:** добавить к G1 offline-спецификации контрольный Slab с внутренним отверстием и 2–4 планарных ската кровли; в native BUILD-01 не делать их обязательными до подтверждения writer-контракта. Сохранить проверку `roof plane → pitch` и `Slab curve → segmented polygon`.
5. **I4-R3-P1-E:** в G4 разделить `IfcTester IDS information check` и `independent geometry BREP check`; не считать IDS сертификатом СП. До экспорта/установки оставить `NOT_RUN`.

## 7. Статусы и критерии ГОТОВО
- `SOURCE`: **32** предметных проверок по доступным источникам; отчёт без локального моделирования.
- `OFFLINE`: **0 новых выполненных** — GH definition не запускалась.
- `BUILD`: **0** — BUILD-01 не создавалось.
- `INSTALLED`: **NOT_VERIFIED** — нет доступа к Rhino/GC29/LBT/IfcOpenShell на пользовательском Windows.
- `LIVE`: **0 новых**; никаких записей.
- `ACCEPTED`: **0**.
- `G0`: BLOCKED_RUNTIME; `G1`: NOT_RUN; `G2`: SOURCE_PARTIAL; `G3`: NOT_AUTHORIZED; `G4/G5`: NOT_RUN.
- `NOT_FOUND`: готовая автоматическая трёхсторонняя AC↔GH↔Rhino BIM-транзакция; GH native Multi-plane Roof из произвольного Brep; существующий доказанный PR74-контракт для Slab holes/Roof facets; эквивалентность IFC GlobalId и AC GUID.
- **ГОТОВО R3 SOURCE:** переданы I4 6 схем, явные native/BREP/IFC границы, 2 контрааудита и 5 проверяемых поручений. **ГОТОВО BUILD-01** не достигнуто.
- **Ограничения соблюдены:** main, исходный код, PLN/APX, установки, LIVE, платные API, Work/Codex/Arena, merge не тронуты. `MODEL_MODE_NOT_VERIFIABLE`.
