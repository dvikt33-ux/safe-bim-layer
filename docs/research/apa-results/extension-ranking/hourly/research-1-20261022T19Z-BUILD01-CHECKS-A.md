# APA №1 — BUILD-01 · CHECKS-A · 22.10.2026 19Z

**Источник:** 8 реальных GitHub fetch_pr upstream ENZYME-APD/Tapir. Все указанные PR на момент чтения OPEN, not merged; большинство заявлено для unreleased 1.7.3, не для установленного 1.5.10. Upstream лицензия MIT (LICENSE main), Graphisoft DevKit отдельный. Никаких LIVE/BUILD/INSTALLED/ACCEPTED. SOURCE_ONLY. Важность не является benchmark.

### SOURCE 01 — Можно ли сверять GDL-точки привязки библиотечных объектов?
**Ворота:** G4. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1335 (PR #1335, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** GetHotspotsOfElements: элементы GUID → массив x/y; координатная система не установлена. **Решение/ограничение:** Только дополнительный 2D-контроль, не BREP. **Задание №2:** №2: не включать в обязательную приёмку, пока не подтверждены координаты.

### SOURCE 02 — Как до создания узнать свойства текущего инструмента?
**Ворота:** G2. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1336 (PR #1336, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** GetPropertyValuesOfElementDefaults(elementType,properties), NotAvailable/NotEvaluated → ErrorItem. **Решение/ограничение:** Кандидат read-only defaults, Favorite не учтён без применения. **Задание №2:** №2: сравнить с текущим GetPropertyValuesOfElements; исключить неподтверждённые defaults.

### SOURCE 03 — Как идентифицировать Library Part после Save/Open?
**Ворота:** G2. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1337 (PR #1337, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** GetLibraryPartIdentities: unId, mainGuid, revisionGuid, refGuid, lockStatus, index/path. **Решение/ограничение:** Кандидат для устойчивой идентичности, raw compare code не трактовать. **Задание №2:** №2: сопоставить unId с текущим библиотечным inventory, без изменения библиотек.

### SOURCE 04 — Можно ли автоматически диагностировать отсутствие библиотек?
**Ворота:** G2. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1341 (PR #1341, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** CheckLibraries/ResetLibraries → ExecutionResult, ACAPI_LibraryManagement_*; reset меняет состояние. **Решение/ограничение:** CheckLibraries потенциально полезен; ResetLibraries исключить из read-only G0. **Задание №2:** №2: только исследовать CheckLibraries, не запускать ResetLibraries.

### SOURCE 05 — Можно ли хранить план в add-on объектах PLN?
**Ворота:** G0. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1345 (PR #1345, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** Get/Set/DeleteProjectData, имена/UTF-8, add-on-owned, сохранение в PLN. **Решение/ограничение:** Дублирует SQLite/журнал, мутации не разрешены. **Задание №2:** №2: не интегрировать новый store, оставить существующий SQLite.

### SOURCE 06 — Можно ли надёжно выбрать модельный элемент человеком?
**Ворота:** G0. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1348 (PR #1348, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** GetElementFromUser(prompt,elementTypes) → GUID/type/position или cancelled. **Решение/ограничение:** Интерактивная команда, не подходит автономному preflight. **Задание №2:** №2: оставить вне обязательного G0.

### SOURCE 07 — Нужно ли вручную запускать GDL parameter script?
**Ворота:** G2. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1350 (PR #1350, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** RunParameterScriptOfElements → per-element ExecutionResult; undoable, меняет параметры. **Решение/ограничение:** Не read-only; не использовать без G3. **Задание №2:** №2: отметить опасный side-effect и не включать в проверку G0.

### SOURCE 08 — Можно ли сравнить площади сложных контуров без нового геометрического движка?
**Ворота:** G4. **Официальный версионированный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1351 (PR #1351, open, upstream Tapir; версия 1.7.3/PR, не установленная 1.5.10). **Поля/факт:** TriangulatePolygonsOfElements: Slab/Zone/Hatch/Mesh/Roof → треугольники x/y; 2D без Z. **Решение/ограничение:** Потенциальная независимая 2D-проверка площадей; не объём/3D BREP. **Задание №2:** №2: сравнить площадь треугольников с исходным планом, только после версии.

Контроль источника: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE (MIT); https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/tools/package_info.json (1.7.3).
