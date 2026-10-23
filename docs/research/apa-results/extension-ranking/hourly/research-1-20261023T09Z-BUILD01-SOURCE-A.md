# APA №1 | 2026-10-23 09Z | BUILD-01 SOURCE S01–S15

**Режим:** SOURCE_ONLY, без Windows/PLN/APX/LIVE. Источник = непосредственное чтение issue/PR, не доказательство локального дефекта. Лицензия: Tapir 1.5.9 MIT (LICENSE blob 1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd); сообщения пользователей/Graphisoft — не отдельный лицензируемый компонент.

## S01 — Как не сдвинуть уровни при одновременном добавлении этажей?

**Ворота:** G1. **Первоисточник:** [#573](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/573). **Версия/статус/факт:** AC28 GER Windows; main после PR571, issue closed; подтверждён сдвиг абсолютных отметок при одном SetStories, несмотря на success.

**Готовое решение или ограничение:** Готовое решение: для BUILD-01 не вызывать SetStories; GetStories + заранее утверждённые существующие этажи. Двухпроходный workaround из issue только исполнителю после отдельного допуска.

**Адресное задание №2:** №2: сравнить storyBindings с GetStories; расхождение => G1 BLOCKED.

## S02 — Корректно ли SetStories обрабатывает отрицательные индексы?

**Ворота:** G1. **Первоисточник:** [#422](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/422). **Версия/статус/факт:** Tapir 1.5.x, AC28 Win; issue closed: старый код принимал позицию массива вместо индекса этажа.

**Готовое решение или ограничение:** Исправление PR423 существует, но не является подтверждением локальной 1.5.10; не изменять этажи без разрешения.

**Адресное задание №2:** №2: учитывать floorIndex<0, проверить GetStories и текущий APX.

## S03 — Существует ли готовый fix negative story index?

**Ворота:** G1. **Первоисточник:** [PR423](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/423). **Версия/статус/факт:** Merged 2026-06-19; две строки заменяют array position на story.index; автор сообщает LIVE AC28, не AC29 build5101.

**Готовое решение или ограничение:** Готовый upstream fix; статус SOURCE, бинарная локальная версия не сверена.

**Адресное задание №2:** №2: не писать новый SetStories; если требуется, доказать версию и тесты отдельно.

## S04 — Решён ли рост этажей вниз и проверены ли отметки?

**Ворота:** G1. **Первоисточник:** [PR571](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/571). **Версия/статус/факт:** Merged 2026-08-20; расширение SetStories с pinned index; в описании прямо 'not built, run or reviewed'.

**Готовое решение или ограничение:** #573 демонстрирует остаточный дефект отметок; merged не PASS.

**Адресное задание №2:** №2: исходное здание привязать к готовым этажам, не использовать SetStories для BUILD-01.

## S05 — Может ли CreateWindows вернуть GUID несуществующего окна?

**Ворота:** G2/G4. **Первоисточник:** [#481](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/481). **Версия/статус/факт:** OPEN; AC29 build5003 CHE macOS, Tapir1.5.5: успешный GUID, но GetElementsByType(Window,IncludeSubElemObjects)=0; host wall без проёма.

**Готовое решение или ограничение:** Это внешний репорт, не доказанный дефект локального 5101; готовый контроль — независимое наличие GUID + host-wall opening.

**Адресное задание №2:** №2: после каждого CREATE требовать GUID existence, elementType, hostWall; при 0 => STOP, без повторного CREATE.

## S06 — Достаточно ли валидного Favorite для создания окна AC29?

**Ворота:** G2. **Первоисточник:** [#399](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/399). **Версия/статус/факт:** CLOSED; AC29 build4006 JPN Win11, Tapir1.4.0: CreateWindows/Doors APIERR_BADPARS при валидных favorites; 13 других CREATE типов работали.

**Готовое решение или ограничение:** Нет универсальной гарантии от favoriteName; версия/локализация критичны.

**Адресное задание №2:** №2: проверить доступные favorites и локальные ошибки; не считать валидный Favorite гарантией CREATE.

## S07 — Точно ли размещается дверь в polygon wall?

**Ворота:** G2. **Первоисточник:** [#453](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/453). **Версия/статус/факт:** OPEN; AC29 build5003 GER mac ARM, Tapir1.5.3: centerOffset сохранялся, но игнорировался при размещении в polygon wall; разные favorites дают ошибки.

**Готовое решение или ограничение:** Для первой модели использовать прямолинейные стены-хосты; позицию проверять readback, не только параметр.

**Адресное задание №2:** №2: исключить polygon-wall hosted openings из обязательного BUILD-01.

## S08 — Сохраняются ли настройки маркера окна после CREATE?

**Ворота:** G2/G4. **Первоисточник:** [#551](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/551). **Версия/статус/факт:** CLOSED; AC29 build3100 NOR Win11, Tapir1.5.7/1.5.8: marker memo overwritten factory params, pen 166; favorite не помог.

**Готовое решение или ограничение:** Для BUILD-01 геометрию окна и его marker различать; нельзя объявлять 2D оформление ACCEPTED.

**Адресное задание №2:** №2: read-only проверить marker при необходимости; не делать GDL WRITE исследователем.

## S09 — Безопасен ли GDL 2D-array Get→Set round-trip?

**Ворота:** G2. **Первоисточник:** [#812](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/812). **Версия/статус/факт:** OPEN; AC29 build3200 AUT Win11 Tapir1.7.0: плоский список вместо 2D-array возвращает success и повреждает объект; nested list работает.

**Готовое решение или ограничение:** Запретить необязательные GDL array writes; если необходимы — shape+dimensions и readback.

**Адресное задание №2:** №2: в typed schema не превращать двумерные параметры в flat arrays.

## S10 — Можно ли штатно узнать происхождение библиотечной детали?

**Ворота:** G2. **Первоисточник:** [#1217](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1217). **Версия/статус/факт:** OPEN feature request: LibraryManager GetLibraryOfLibPart / flags embedded/package/missing, предложена GetLibrariesOfLibParts; не реализовано в проверенном issue.

**Готовое решение или ограничение:** Не выдавать proposal за команду 1.5.10; готовый штатный Library Manager AC29 — альтернативный источник диагностики.

**Адресное задание №2:** №2: проверить библиотечные источники/дубли через UI или существующие read-only команды.

## S11 — Можно ли получить имя выгруженной детали через Tapir?

**Ворота:** G2. **Первоисточник:** [#1218](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1218). **Версия/статус/факт:** OPEN request GetMissingLibPartNames на базе ACAPI_LibraryPart_GetUnloadedLibpartName; наличие команды не доказано.

**Готовое решение или ограничение:** Использовать AC29 Library Manager warnings; не писать новую команду.

**Адресное задание №2:** №2: список missing parts до разрешения CREATE.

## S12 — Можно ли получить дефолтные GDL параметры без размещения?

**Ворота:** G2. **Первоисточник:** [#1223](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1223). **Версия/статус/факт:** OPEN request GetLibPartParameters с dimensions1/2; SDK API упомянут, готовой команды в 1.5.10 не доказано.

**Готовое решение или ограничение:** Готовый путь: проверенный Favorite/Library Manager, без пробного CREATE.

**Адресное задание №2:** №2: фиксировать libraryPartName и размеры параметров по существующему read-only контракту.

## S13 — Безопасна ли пачка CreateSlabs разной сложности?

**Ворота:** G2/G4. **Первоисточник:** [#439](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/439). **Версия/статус/факт:** CLOSED; AC28 build7006 AUS macOS, Tapir1.5.3: смешанные vertex-count в одном запросе аварийно закрывали Archicad; single slab работал.

**Готовое решение или ограничение:** Не переносить crash на AC29 5101; готовое снижение риска — одиночные запросы сложных Slab в санкционированном будущем прогоне.

**Адресное задание №2:** №2: классифицировать полигоны, запретить mixed complex slab batch до installed qualification.

## S14 — Может ли Slab/roof payload приниматься и игнорироваться?

**Ворота:** G2/G4. **Первоисточник:** [#604](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/604). **Версия/статус/факт:** CLOSED meta-report; AC28 GER Win Tapir1.5.8: Slab holes принимаются только как holes:[{polygonCoordinates:...}]; outline без holes стирает holes; Roof thickness мог игнорироваться.

**Готовое решение или ограничение:** Точный nested schema + независимый readback; API succeeded не подтверждает эффект.

**Адресное задание №2:** №2: строгая валидация holes/roof thickness и readback после каждой санкционированной операции.

## S15 — Есть ли штатная нормализация самопересекающихся контуров?

**Ворота:** G1/G2. **Первоисточник:** [#1127](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1127). **Версия/статус/факт:** OPEN request RegularizePolygons через ACAPI_Polygon_RegularizePolygon; реализация Tapir не подтверждена.

**Готовое решение или ограничение:** Готовая функция SDK, но не готовая команда локального APX; G1 выполнять геометрическую проверку исходных полигонов без native write.

**Адресное задание №2:** №2: валидировать замкнутость, дубли и пересечения в существующем offline DAG.
