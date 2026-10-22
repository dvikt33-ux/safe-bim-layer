# APA №1 BUILD-01 — 6 карточек готовых решений | 22.10.2026 18Z

Все 30 пунктов: SOURCE_ONLY, НЕ INSTALLED/LIVE/ACCEPTED. Проверены тексты/диффы конкретных upstream PR, а не установленный APX. Tapir 1.7.2 опубликован 19.10.2026; лицензия репозитория MIT (LICENSE tag1.7.2). Upstream merged не означает tested в AC29 build5101.

## 1. Native Grid Tool (важность экспертно 86/100)
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/879 ; версия upstream 1.7.2, MIT, AC26+. Команды GetGridElementDefaults/GetGridElements/CreateGridElements. Вход: координаты оси, GDL/слой/этаж; выход: нативный Grid GUID и warnings. Польза: настоящие оси с IFC и маркерами разрезов, а не только координатные пересечения. Не дублирует PR184 (там выбранные координатные пересечения). Ограничение: локальная 1.5.10 не подтверждена; не обязательный блокер G1. №2: только read-only capability check.

## 2. Автоматические Zone на неактивном этаже (75/100)
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/854 ; upstream 1.7.2, MIT; репорт AC29 build3200, не 5101. Вход: geometry.referencePosition+floorIndex; выход: Zone GUID. Решение: исправление временно активирует story. Риск: не построенные замкнутые стены, изменение активного окна, upstream PR без тестов. №2: не включать Zone в обязательный первый BUILD-01, использовать ручные контуры позже.

## 3. Создание нативных Curtain Walls (70/100)
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/867 ; upstream 1.7.2 MIT. Вход: curtainWallsData.coordinates/favoriteName/zCoordinate/floorIndex + pattern; выход: CW GUID с панелями/рамами по шаблону. Польза: реальные витражи вместо имитации колоннами. Ограничение: не доказывает локальную схему, не требуется для BUILD-01. №2: проверить возможность будущего использования, не запускать LIVE.

## 4. Гарантированная геометрия Roof/Slab (100/100)
Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/482 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/504 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785 ; MIT, upstream 1.5.6–1.7.1. Вход: roof pivotLine/angle(rad), slab polygon/holes, structureType/buildingMaterialId/compositeId (поздний контракт); выход: GUID/контур/атрибут. Решение: для первого BUILD-01 Basic Roof + простой Slab, существующий CREATE→MODIFY и readback; никакого нового writer. №2: сравнить точные схемы локального APX.

## 5. Контроль высот, этажей и привязок (100/100)
Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/423 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/448 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/446 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/670 . MIT, upstream 1.5.3–1.6.0. Вход: story index/level/height, absolute z, relativeTopStory; выход: этаж/offset/actual height. Ограничение: локальный API/данные неизвестны, SetStories не вызывать. №2: read-only manifest с действительными индексами, абсолютными Z, top link.

## 6. Независимый readback против ложного success (100/100)
Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/861 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/720 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/882 , https://github.com/ENZYME-APD/tapir-archicad-automation/pull/694 . MIT, upstream 1.6.0–1.7.2. Вход: command results/GUID, реальный элемент/геометрия/атрибут; выход: согласованная инвентаризация. Ограничение: BBox Slab старой сборки потенциально опасен, новые PR не равны локальным. №2: прежде всего APX SHA/command registration и независимый readback; никаких операций записи.

Оценки 0–100 — экспертная полезность, не измеренное ускорение. Ни одна карточка не даёт разрешения на установку/изменение PLN.
