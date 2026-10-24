# APA №1 | 23.10.2026 10Z | BUILD-01 | 6 полных карточек

**Состояние:** SOURCE_ONLY. Оценки 0–100 — экспертная важность для BUILD-01, не измеренная скорость. Лицензия исходного Tapir: MIT ([LICENSE](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE), blob `1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd`). Установленная версия 1.5.10 не отождествляется с upstream 1.7.2/1.7.3. Нет INSTALL/LIVE/ACCEPTED.

## C01 | RegularizePolygons — точные контуры Slab | G2 | 96/100 при доказанном дефекте
- **Вопрос/блокер:** составной контур с повторными вершинами, самопересечениями или касающимися holes может не пройти CreateSlabs.
- **Готовый исходник:** [Tapir PR1134](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1134), MERGED 2026-10-23 10:46:57Z; [issue1127](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1127); patch `PolygonCommands.cpp/.hpp` и `Examples/regularize_polygons.py`.
- **Контракт:** `RegularizePolygons({polygons:[{polygonCoordinates,polygonArcs?,holes?}],withAncestry?}) → results[{polygons:[...],ancestry?}]`; возвращает 0, 1 или N полигонов; read-only операция над входными координатами, не над PLN; AC27+, регистрация upstream 1.7.2.
- **Совместимость:** код в upstream MERGED, но команда отсутствует в подтверждённом pinned-каталоге локальной 1.5.10. В PR нет независимой LIVE-квитанции на AC29 build5101.
- **Недублирование:** не заменять compiler PR74 и геометрические preflight; использовать только при реально выявленном дефекте входного контура.
- **Риск:** regularization может разделить один slab на два и изменить площадь/holes; требуется сравнить площади, топологию, ancestry и утвердить изменение; автоматическая подмена запрещена.
- **Задание №2:** доказать конкретный невалидный контур в новом BUILD-01; если нет — пометить NOT_REQUIRED. Если есть — передать контракт инженерному исполнителю без INSTALL/WRITE.
- **ГОТОВО:** сначала точный дефект входных координат, затем локальная доступность команды и утверждённая геометрия; сейчас SOURCE_ONLY.

## C02 | Project Health Check — дополнительный аудит здания | G4 | 88/100
- **Вопрос:** можно ли получить готовую независимую диагностику ошибок ID, дублей, мелких элементов, пустых этажей и скрытых слоёв?
- **Готовый исходник:** [Tapir PR1434](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1434), MERGED 2026-10-22 21:05:41Z, `builtin-scripts/ProjectHealthCheck.py` (Python>=3.11, tkinter, стандартная библиотека).
- **Контракт:** девять проверок: missing Element ID, duplicate Zone number, unclassified, duplicates by type/story/3D box, <1cm, distant origin, hidden layers, empty stories, unused layers; CSV/XLSX export; selectable findings.
- **Совместимость:** upstream script ≠ установленный builtin script в 1.5.10; локальный GUI не трогали. Копия результатов в файл/Issues — отдельные операции, не разрешены исследователю.
- **Недублирование:** дополнительный диагностический слой после независимого GUID/type/story/host/BREP readback; не заменяет G4.
- **Риск:** duplicate AABB — эвристика; hotlinked elements skipped; нет нормативной экспертизы.
- **Задание №2:** подготовить read-only сопоставление существующих проверок APA с девятью checks; отметить missing capability, не устанавливать.
- **ГОТОВО:** отдельный разрешённый read-only прогон на scratch с версионированной квитанцией; пока SOURCE_ONLY.

## C03 | Solid Operation Explorer — анализ SEO без удаления | G2/G4 | 87/100
- **Вопрос:** может ли Roof/Wall связь оказаться геометрически неэффективной?
- **Готовый исходник:** [PR1434](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1434), `builtin-scripts/SolidOperationExplorer.py`, MERGED 22.10.
- **Контракт:** перечисляет target/operator/operation, подсвечивает пары; `boxes_touch` с TOLERANCE 0.001m, специальные правила для upwards/downwards subtraction.
- **Совместимость:** не подтверждён локально; скрипт умеет `RemoveSolidElementLinks` (WRITE), запуск такого действия запрещён.
- **Недублирование:** existing GetSolidElementLinks и PR74 остаются каноном; Explorer — опциональный UI и эвристика.
- **Риск:** AABB не доказывает реальный BREP contact и не доказывает Trim to Roof; нативные операции не выполнялись.
- **Задание №2:** сопоставить API link graph с ожидаемыми связями Roof/Wall; не удалять links.
- **ГОТОВО:** только read-only verified links и независимый geometry result; сейчас SOURCE_ONLY.

## C04 | Part-own defaults для библиотечных объектов | G2 | 94/100 при обязательном Object
- **Вопрос:** может ли библиотечный объект получить размеры другого GDL part?
- **Готовый кандидат:** [PR1395](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1395), OPEN; AC29 build5101, upstream Tapir1.7.2: Bed Double 01 размещался 5.4×2.0×0.2м вместо 1.8×2.0×0.66м. Предложено `ACAPI_LibraryPart_GetParams`, `parameters`, `layerIndex`, исправление ZZYZX case.
- **Версия/лицензия:** Tapir MIT; PR OPEN и не в 1.5.10.
- **Недублирование:** не писать свой GDL loader и не менять libraries; использовать уже подтверждённые Favorite/part/default readback.
- **Риск:** в PR явно отмечено, что Windows/Doors имеют другой путь; вывод нельзя переносить на все проёмы.
- **Задание №2:** для окон/дверей BUILD-01 проверить реальные libraryPart, A/B/Z, hostWall GUID; Object не включать обязательным без задания.
- **ГОТОВО:** точные библиотечные размеры после native CREATE+readback; пока SOURCE_ONLY.

## C05 | Сопоставление batch errors с входными GUID | G4 | 99/100
- **Вопрос:** как избежать ложного PASS, если ошибка GetDetailsOfElements не содержит GUID?
- **Готовый контракт:** [PR1406](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1406), OPEN; документирует ровно один ответ на вход, в том же порядке, и добавляет GUID в error.message.
- **Версия/лицензия:** upstream Tapir MIT; локальная 1.5.10 без этого PR; PR не тестировался в Archicad.
- **Недублирование:** existing GUID list + ordered readback в SceneWriter/SQLite, не новый verifier.
- **Риск:** если длина ответа отличается или часть entries ошибочна, нельзя назначать статус ACCEPTED.
- **Задание №2:** хранить ordered input GUID, проверять cardinality, связывать error по позиции; при расхождении `UNKNOWN_STOP`, без повторного CREATE.
- **ГОТОВО:** 1:1 GUID→result+error и независимая геометрия на каждом этаже; пока SOURCE_ONLY.

## C06 | Проверка schema/runtime без доверия к optional и success | G0/G2 | 98/100
- **Вопрос:** достаточно ли pinned schema и success flag для уверенного CREATE/MODIFY?
- **Первоисточники:** [issue1402](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1402) — optional defaultValue не работает в CreatePropertyDefinitions на 1.7.2 AC27/29/30; [issue1403](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1403) — omitted Mesh holes удаляются; [PR674](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/674) — NoError для ProjectInfo без readback; [R2-10Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T10Z-report.md) — доказан dual-write Slab guard gap.
- **Готовое решение:** не новое расширение, а уже существующий `DynamicCommands → SceneWriter → SQLite` с обязательной сверкой runtime schema, двумя отдельными санкциями для Slab и readback material/holes.
- **Совместимость:** внешние баги относятся к другим командам/версиям; прямой баг Slab на AC29 build5101 ими не доказан. Нет разрешения на кодовый patch.
- **Недублирование:** PR74/SceneWriter остаётся единственным writer.
- **Задание №2:** предъявить реальный loaded APX+schema, зафиксировать два отдельных permissions `CreateSlabs` и `ModifySlabs`; до этого WRITE_BLOCKED.
- **ГОТОВО:** G0 RUNTIME_READY + G2 DUAL_WRITE_APPROVAL_ENFORCED + независимый readback. Сейчас G0 BLOCKED / G2 WRITE_BLOCKED.

## Общий вывод
Из шести карточек только C01–C03 относятся к новым upstream merged возможностям, **ни одна не подтверждена в локальной 1.5.10**. C04/C05 — открытые PR; C06 — существующий безопасный маршрут, а не новая функция. Нового BUILD-01 OFFLINE/LIVE/ACCEPTED нет.