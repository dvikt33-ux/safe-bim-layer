# APA №1 BUILD-01 — SOURCE 21–30 | 22.10.2026 18Z

Все 30 пунктов: SOURCE_ONLY, НЕ INSTALLED/LIVE/ACCEPTED. Проверены тексты/диффы конкретных upstream PR, а не установленный APX. Tapir 1.7.2 опубликован 19.10.2026; лицензия репозитория MIT (LICENSE tag1.7.2). Upstream merged не означает tested в AC29 build5101.

## 21. G2 — Почему неверные holes иногда молча игнорируются?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/608 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: Схема Hole2D противоречила сама себе: required polygonCoordinates при allowed polygonOutline; PR валидирует >=3 координат.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: не принимать успех без повторного чтения holes; сложные отверстия исключить из P0.

## 22. G2 — Есть ли прямой материал/композит в CreateSlabs?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: 1.7.1 upstream добавил structureType Basic/Composite, buildingMaterialId, compositeId; PR без build/test.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: в локальной 1.5.10 сохранить существующий CREATE→MODIFY и материальный readback.

## 23. G2 — Как контролировать базовую линию стены и плоскость Slab?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/421 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: CreateWalls referenceLineLocation, CreateSlabs referencePlaneLocation, CreateBeams anchorPoint, CreateColumns coreAnchor.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: учитывать привязки при проверке геометрии, не сравнивать только осевые координаты.

## 24. G2 — Почему явная высота стены/колонны может игнорироваться?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/446 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: Top-linked default relativeTopStory>0 перекрывал height; PR сбрасывает relativeTopStory при явной высоте.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: readback height и top-link после создания; не предполагать правильность по запросу.

## 25. G2 — Как исключить кратное увеличение размеров Object?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/719 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: При useFixSize=false xRatio/yRatio — отношение к A/B библиотечной детали; PR конвертирует размеры при Create/Modify.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: для обязательных библиотечных деталей читать GDL A/B и BBox; не полагаться на dimensions input.

## 26. G4 — Можно ли доверять Object dimensions из GetDetails?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/720 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: При useFixSize=false GetDetails раньше возвращал ratio вместо метров; PR конвертирует обратно; зависит от #719.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: сопоставить dimensions с GDL A/B и BBox, выявлять рассогласования.

## 27. G2 — Есть ли версия-зависимое смещение GenericOpening по Z?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/849 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: AC29 PlacePolygonal требовал Z-коррекцию, AC30 уже нет; PR ограничивает компенсацию AC29.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: не переносить схему AC30 на AC29; GenericOpening не обязательный для первого BUILD-01.

## 28. G4 — Может ли ошибка одного свойства испортить результаты следующих?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/629 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: В SetPropertyValuesOfElements прежний err переиспользовался между свойствами; PR отделяет getErr и per-item err.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: каждое свойство проверять отдельно, readback с типом статуса; без массовой записи.

## 29. G4 — Гарантирует ли success DeleteElements реальное удаление?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/679 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: Bulk ACAPI_Element_Delete может вернуть NoError и пропустить locked layer; PR возвращает per-element results.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: не делать DELETE; при будущей операции проверять отсутствие GUID и сохранение остальных.

## 30. G4 — Безопасен ли Slab BBox при другом активном этаже?
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/694 ; upstream Tapir MIT, PR merged (наличие локально НЕ доказано).
Факт/поля: ACAPI_Element_CalcBounds мог падать вне текущего draw context; PR использует solid-body bounds; в PR прямо отмечено no build/test.
Решение/ограничение: SOURCE для G0–G4; при несовпадении runtime/schema — BLOCKED, никаких новых записей.
Адресное задание №2: №2: не вызывать рискованный старый BBox на неизвестном APX; предпочесть независимый read-only путь после runtime gate.
