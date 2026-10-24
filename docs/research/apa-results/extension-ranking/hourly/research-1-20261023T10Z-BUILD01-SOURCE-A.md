# APA №1 | 2026-10-23 10Z | BUILD-01 | SOURCE S01–S14

**Факт:** 14 разных PR/issues прочитаны напрямую через GitHub API 23.10.2026. Все находки SOURCE_ONLY; GitHub PR merged ≠ INSTALLED/LIVE. Лицензия upstream Tapir — MIT, `LICENSE` blob `1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd`; не переносить лицензию автоматически на APA или сторонние библиотеки. Экспертные оценки отдельно в CARDS. Все изменения кода/PLN/APX запрещены.

## S01 — G2 — Есть ли штатная нормализация сложных контуров Slab до CREATE?
**Источник:** [PR #1134](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1134). **Версия/поля/факт:** MERGED 2026-10-23 10:46:57Z; AC27+; команды RegularizePolygons / RegularizePolylines, регистрация 1.7.2; вход polygons[{polygonCoordinates,polygonArcs?,holes?}], withAncestry; выход results с 0..N polygons и ancestry; no project mutation.
**Решение/ограничение:** Нет в подтверждённом pinned Tapir 1.5.10; превращение одного контура в несколько меняет проектную геометрию и требует явного решения.
**Адресное задание №2:** №2: проверить реальный malformed contour в BUILD-01; если такого нет — не включать как блокер G2; если есть — SOURCE-only контракт для отдельного инженерного допуска.

## S02 — G2 — Подтверждает ли независимый issue требуемую семантику регуляризации?
**Источник:** [Issue #1127](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1127). **Версия/поля/факт:** CLOSED после PR1134; SDK ACAPI_Polygon_RegularizePolygon / RegularizePolyline / DisposeRegularizedPoly; 0..N результатов, происхождение рёбер/вершин; request описывает ошибки самопересечений, дубликатов, отверстий.
**Решение/ограничение:** Issue — постановка, не Archicad29 LIVE; схема предложения отличается от реализованного поля polygonCoordinates.
**Адресное задание №2:** №2: сверять реализованный PR1134, не копировать предложенный в issue JSON.

## S03 — G4 — Есть ли готовая дополнительная диагностика модели без второго writer?
**Источник:** [PR #1434](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1434). **Версия/поля/факт:** MERGED 2026-10-22 21:05:41Z; builtin-scripts/ProjectHealthCheck.py, SolidOperationExplorer.py, PropertyHighlighter.py, BatchPublisher.py; Python>=3.11, tkinter, standard library; 9 checks (IDs, duplicates by type/story/3D box, tiny, distant, hidden, empty stories etc).
**Решение/ограничение:** Скрипты upstream не подтверждены локально; duplicate AABB — эвристика, не BREP; интерфейс содержит операции CREATE Issues / RemoveSolidElementLinks, их запуск запрещён.
**Адресное задание №2:** №2: рассмотреть read-only checks как необязательное дополнение G4; не запускать палитру и не выдавать 3D box за BREP.

## S04 — G2 — Сохраняет ли CreateObjects размеры библиотеки при замене имени part?
**Источник:** [PR #1395](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1395). **Версия/поля/факт:** OPEN, AC29 build5101 пример Tapir1.7.2: Bed Double 01 ошибочно 5.4×2.0×0.2 вместо 1.8×2.0×0.66 м; предложены part-own defaults, GDL parameters, layerIndex.
**Решение/ограничение:** PR не объединён; доказательство автора относится к объектам/лампам 1.7.2, не автоматически к дверям/окнам и не к 1.5.10.
**Адресное задание №2:** №2: для любых обязательных библиотечных объектов требовать readback dimensions A/B/Z и actual libraryPart; для BUILD-01 Object не делать обязательным.

## S05 — G2 — Можно ли готовой командой сменить missing library part без пересоздания GUID?
**Источник:** [PR #1394](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1394). **Версия/поля/факт:** OPEN, proposed ChangeLibraryPartOfElements 1.7.3; name/index/mainGUID; keepParameters/keepSize; Object/Lamp/Window/Door/Skylight/Zone/Label; сохраняет GUID.
**Решение/ограничение:** Нет подтверждённой команды локально; mutating, запрещено исследователю; Stair/Railing excluded.
**Адресное задание №2:** №2: при missing part сначала инвентаризировать library/Favorite, не планировать смену libraryPart в обязательном G2.

## S06 — G2 — Есть ли независимое описание проблемы отсутствующих библиотечных деталей?
**Источник:** [Issue #1393](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1393). **Версия/поля/факт:** OPEN; постановка сохранения GUID/labels/properties при смене отсутствующей библиотечной детали после миграции AC30→AC28.
**Решение/ограничение:** Не доказано, что BUILD-01 scratch AC29 содержит missing parts; issue не готовая функция.
**Адресное задание №2:** №2: фиксировать loaded library parts и отсутствующие зависимости; NOT_APPLICABLE при отсутствии дефекта.

## S07 — G4 — Можно ли штатно получить триангуляцию контура Slab для независимого BREP?
**Источник:** [PR #1351](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1351). **Версия/поля/факт:** OPEN; TriangulatePolygonsOfElements 1.7.3, Slab/Zone/Hatch/Mesh/Roof, API Polygon_TriangulatePoly; возвращает плоские треугольники XY.
**Решение/ограничение:** Автор: не тестировалось в Archicad, layout handle не подтверждён DevKit; 2D triangulation ≠ 3D BREP; не годится для закрытия G4.
**Адресное задание №2:** №2: не использовать как замену отсутствующего GetModelDumpV1/независимого 3D readback.

## S08 — G4 — Можно ли фиксировать воспроизводимый масштаб 3D-окна?
**Источник:** [PR #1277](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1277). **Версия/поля/факт:** MERGED 2026-10-23 10:45:12Z; Get3DWindowSettings/Set3DWindowSettings; hSize,vSize,zoomScaleX/Y,zoomDispX/Y; зарегистрировано 1.7.3.
**Решение/ограничение:** Untested in Archicad; изменение окна — не read-only; визуальная картинка не BREP и не контроль Save/Open.
**Адресное задание №2:** №2: только optional G4 screenshot reproducibility после основных GUID/geometry проверок.

## S09 — G4 — Может ли стиль 3D заменить независимую геометрию?
**Источник:** [PR #1130](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1130). **Версия/поля/факт:** MERGED 2026-10-23 10:59:47Z; Get3DStyleDetails, Create3DStyles, Change3DStyles 1.7.2; API_3DStyle, цвета/толщины/тени.
**Решение/ограничение:** Стиль — отображение, не геометрия; Create/Change мутируют настройки; зависит от ещё OPEN #954 для части цепочки.
**Адресное задание №2:** №2: исключить из P0; не считать альтернативой BREP.

## S10 — G4 — Есть ли bbox для Drawing и релевантен ли он зданию?
**Источник:** [PR #1131](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1131). **Версия/поля/факт:** MERGED 2026-10-23 10:50:34Z; GetDrawingContentBoxes; Drawing GUID → BoundingBox2D; AC27+; 1.7.2.
**Решение/ограничение:** Untested; координатное пространство Drawing не подтверждено; не 3D-объект и не блокер BUILD-01.
**Адресное задание №2:** №2: исключить из G4 здания, оставить для будущей документации.

## S11 — G2 — Решает ли Favorite размеры текста ассоциативных размеров после CREATE?
**Источник:** [PR #1391](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1391). **Версия/поля/факт:** OPEN; favoriteName для CreateAssociativeDimensions / OnSection / WallThicknessDimensions; defNote копируется в dimElem.note.
**Решение/ограничение:** Тема размерных цепочек/чертежей, не обязательное нативное здание; не подтверждено DevKit.
**Адресное задание №2:** №2: NOT_APPLICABLE к P0, не расширять G2.

## S12 — G2 — Есть ли смена маркера окна/двери без замены самого проёма?
**Источник:** [PR #1383](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1383). **Версия/поля/факт:** OPEN; SetMarkerLibraryPartOfElements 1.7.3; elementId.guid, libraryPartName; Main Marker via ACAPI_Element_ChangeExt.
**Решение/ограничение:** Untested; маркер ≠ host wall/opening geometry; изменение маркера — WRITE.
**Адресное задание №2:** №2: не включать маркер в блокеры первого здания, если пользователь не требовал оформления.

## S13 — G2 — Может ли скриптовая правка GSM заменить готовые семейства?
**Источник:** [PR #1233](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1233). **Версия/поля/факт:** MERGED 2026-10-23 08:16:10Z; SetLibraryPartScripts 1.7.3 AC28+; editable GSMObject scripts master/parameter/2D/3D/properties.
**Решение/ограничение:** Untested; write to library part, частичная модификация возможна; пользователь запретил кодовые/библиотечные изменения.
**Адресное задание №2:** №2: EXCLUDE, пользоваться готовыми library parts и Favorites.

## S14 — G2 — Готова ли атомарная запись одного свойства на набор элементов?
**Источник:** [PR #1148](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1148). **Версия/поля/факт:** OPEN; proposed ModifyPropertyValueOfElements AC27+; propertyId + propertyValue + elements; all-or-nothing if unavailable.
**Решение/ограничение:** Untested, не локальный Tapir1.5.10; свойства не устраняют Slab material/dual-write.
**Адресное задание №2:** №2: исключить из P0; не использовать как обход native material/Slab.
