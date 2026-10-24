# APA №1 — BUILD-01, SOURCE 11–20 · 2026-10-22 20Z

**Метод:** фактически прочитаны тела соответствующих PR через GitHub `fetch_issue` в этом проходе. Это 10 предметных проверок, а не 10 подтверждённых функций. Источник upstream Tapir (MIT), большинство PR открыты для 1.7.3; локальная 1.5.10 не проверена. Graphisoft SDK лицензируется отдельно. **SOURCE_ONLY**.

### 11. G2 — Можно ли узнать оригинальный путь GSM библиотечной детали?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1371 (PR #1371). **Контракт/факт:** GetLibraryPartOriginalLocations(index) -> path/ErrorItem, AC27+. **Решение/ограничение:** Источник происхождения, но путь не доказывает загрузку/совместимость; open 1.7.3. **Адресное задание №2:** №2: сначала GetAvailableLibraryParts и реальный library inventory; отложить.

### 12. G2 — Можно ли сменить маркер окна/двери, не теряя элемент?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1383 (PR #1383). **Контракт/факт:** SetMarkerLibraryPartOfElements: elementId,libraryPartName; заменяет параметры на defaults новой детали. **Решение/ограничение:** Мутирующая команда open 1.7.3, не блокирует нативный проём. **Адресное задание №2:** №2: не включать в первый BUILD-01; маркеры оставить default.

### 13. G0/G4 — Можно ли безопасно переключить окно базы по databaseId?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1385 (PR #1385). **Контракт/факт:** ChangeWindow(databaseId) без windowType; schema anyOf; storyIndex по-прежнему требует FloorPlan. **Решение/ограничение:** Переключение UI не доказывает нужный PLN и может нарушить preflight. **Адресное задание №2:** №2: GetProjectInfo до любой смены окна; избегать ChangeWindow.

### 14. G4 — Почему Favorite не меняет размеры текста уже созданных размеров?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1391 (PR #1391). **Контракт/факт:** CreateAssociativeDimensions/OnSection/WallThicknessDimensions favoriteName применяется ДО создания dimElem.note. **Решение/ограничение:** Документация/чертежи вне первого 3D BUILD-01; не доказано на AC29 Win. **Адресное задание №2:** №2: сохранить для стадии чертежей, не добавлять в G1.

### 15. G2 — Почему создание свойства без defaultValue ошибочно?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1407 (PR #1407). **Контракт/факт:** CreatePropertyDefinitions defaultValue отсутствует -> UserUndefined вместо Null. **Решение/ограничение:** Open 1.7.3, мутация свойства; не требуется для модели с существующими атрибутами. **Адресное задание №2:** №2: не создавать определения свойств в G0/G1, пользоваться существующими.

### 16. G4 — Может ли ModifyMeshes молча стереть отверстия?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1408 (PR #1408). **Контракт/факт:** ModifyMeshes polygonCoordinates/polygonArcs/holes: omitted holes preserve, holes:[] removes. **Решение/ограничение:** Open 1.7.3, не проверен в AC29; относится к Mesh, не Slab. **Адресное задание №2:** №2: не переносить правило Mesh на Slab; при необходимости readback отверстий.

### 17. G0 — Достоверен ли upstream coverage как доказательство команды?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1409 (PR #1409). **Контракт/факт:** API coverage по добавленным строкам PR; 151 notApplicable C++ API, которые не могут быть JSON-командами. **Решение/ограничение:** Статический анализ, не установленная команда; PR closed, merge не проверен. **Адресное задание №2:** №2: использовать runtime IsAddOnCommandAvailable и schema, не проценты coverage.

### 18. G1/G2 — Есть ли готовая карта имен полей стены для параметрического задания?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1410 (PR #1410). **Контракт/факт:** ToolSettings/Wall.json: 52 полей, begThickness vs thickness; проверка against schema. **Решение/ограничение:** Это статическая таблица и компонент GH, не runtime адаптер APA; PR closed. **Адресное задание №2:** №2: сверить только полезные поля с локальной 1.5.10; не переносить автоматически.

### 19. G1/G2 — Есть ли такие карты для Slab/Roof/Window/Door?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1416 (PR #1416). **Контракт/факт:** ToolSettings для 23 инструментов; Slab 8/19, Roof 10/17, Door/Window 3/12 полей имеют UI labels. **Решение/ограничение:** Неполное покрытие; GH не гарантирует создание; PR closed, merge не проверен. **Адресное задание №2:** №2: применять как справочник для типизированного задания, проверять local schema.

### 20. G0/G4 — Поможет ли Action Center подтвердить актуальность Hotlink?
**Первичный источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1417 (PR #1417). **Контракт/факт:** RunActionCenterChecks(Hotlinks) возвращает код запуска, не результат проверки; Get/SetArchicadVisibility Win only. **Решение/ограничение:** Open 1.7.3, UI side effects; Hotlink не P0. **Адресное задание №2:** №2: не использовать как acceptance; не скрывать Archicad.
