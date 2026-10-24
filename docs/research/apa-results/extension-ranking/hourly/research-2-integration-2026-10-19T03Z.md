# APA AC29 — исследователь №2, 2026-10-19 03:00 UTC

## Главный результат
Найден **готовый read-only мост для сохранённых настроек видов**: Tapir 1.5.9 `GetViewSettings(navigatorItemIds)` возвращает `layerCombination`, `penSetName`, `graphicOverrideCombination`, `drawingScale`, `structureDisplay` и `renovationFilterGuid`. Код в тегах 1.5.9 и 1.7.1 содержит одинаковые поля; наличие команды именно в локальном Tapir 1.5.10 требует runtime inventory. Это устраняет потребность в новом APX для частичной проверки C5/C8, но НЕ доказывает видимость каждого слоя.

Первоисточники: [Tapir 1.5.9 NavigatorCommands.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp), [Graphisoft AC29 Python b3000](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html), [SDK29](https://github.com/GRAPHISOFT/archicad-api-devkit/tree/29.3100).

## Матрица готовых способов подключения
Баллы — экспертная польза 0–100, НЕ измеренное ускорение. Везде новые проверки только SOURCE.

| Кандидат | Балл | Цепочка без второго исполнителя | Решение / трудность / ограничение |
|---|---:|---|---|
| C1 Zone relations | 95 | APA Router → официальный AC29 JSON GetElementsRelatedToZones → GUID list | REUSE/БЫСТРО; related ≠ геометрическая смежность |
| C2 Component QTO | 93 | Router → AC29 GetComponentsOfElements → GetPropertyValuesOfElementComponents → typed JSON QA | REUSE/БЫСТРО; elementId+componentId, SI units |
| C4 Layout preflight | 91 | Router → GetNavigatorItemsType → GetLayoutSettings → Publisher gate | REUSE/БЫСТРО; mm, revision; не доказывает PDF |
| C5 Saved renovation view | 88 | Router → существующий Tapir GetViewSettings → renovationFilterGuid | REUSE/БЫСТРО; список всех фильтров SDK_ONLY |
| C8 View presentation | 85 | Router → Tapir GetViewSettings → pen/layer/graphicOverride labels | REUSE/БЫСТРО; layerCombination не содержит per-layer visibility |
| C7 AABB cross-check | 84 | Router → AC29 Get2DBoundingBoxes/Get3DBoundingBoxes → существующий PR170 B3 bounds | REUSE/АДАПТАЦИЯ; global origin, unsupported type, bbox≠BREP |
| C3 Hotlink source/proxy | 79 | Existing PR173 owner evidence → SDK29 GetHotlinkProxyElementTable | DEFER/ДОЛГО; готовый JSON binding NOT_FOUND_IN_CHECKED_PATHS |
| C6 Property syntax lint | 70 | SDK29 CheckPropertyExpressionString → ??? → Router | DEFER/ДОЛГО; готовый AC29 JSON/Tapir binding NOT_FOUND_IN_CHECKED_PATHS |

## Установленные ограничения
1. `GetLayoutSettings` возвращает `horizontalSize/verticalSize` в **миллиметрах**, а обычные AC29 свойства типа length/area/volume — в **м/м²/м³**. Не смешивать.
2. `LayerCombinationAttribute` AC29 имеет `layerAttributeIds`, но **не раскрывает per-layer visibility state**. `GetLayerAttributes` имеет глобальный `isHidden`, не состояние слоя в каждой комбинации.
3. `ElementsOrError`, `ElementComponentsOrError`, `BoundingBox*OrError` содержат error-ветку: пустой список не равен ошибке.
4. `GetViewSettings` проверяет `API_PublicViewMap` и возвращает error для не-вида. `SetViewSettings` и `SetActualRenovationFilter` запрещены.
5. Tapir `GetHotlinks` возвращает узлы `hotlinkNodeId/name/type/location/children`, **не** таблицу proxy→source GUID.
6. PR173 содержит `LIVE_NATIVE_HOTLINK_BATCH_SAVED_REOPENED_PASS`: 69→119 GUID, 2 roots/48 children, один CreateHotlinkInstances, один SaveProject, readback. Это ранее выполненная операция; новых LIVE здесь нет, независимый ACCEPTED не установлен. Очередь №3 20Z ошибочно содержит устаревшее «batch не LIVE».
7. SDK29 C++ proprietary EULA, Tapir 1.5.9 MIT; локальная 1.5.10 идентичность не доказана. GPU 8GB не нужен для JSON read-only; RAM48GB не заменяет ограничений AC29.

## Ворота и выбор пути
SOURCE: API/tag/license/поле; OFFLINE: фикстуры пустой/ошибочной зоны, composite/single компонент, два формата листов, сохранённые View, bbox rotated; BUILD: только после разрешения, Python/JSON version pin; INSTALLED: actual local build5101 и Tapir command inventory/hash; LIVE: только отдельное разрешение, read-only scratch PLN; ACCEPTED: независимый GUID/unit/geometry/issued-revision readback. Ничего не устанавливали и не меняли.

Для C5 два пути: (A) готовый Tapir GetViewSettings — выбран для saved-view GUID; (B) SDK29 GetRenovationFilters + custom APX — отложен. Для C3: (A) существующий PR173 owner-map — reuse для owner, НЕ source; (B) SDK29 proxy map с новым binding — отложен. Для C8: Tapir view labels — выбран для preflight; SDK29 per-layer detail — NOT_FOUND как готовый мост.

## Контрааудит A
Проверены Graphisoft AC29 b3000 (не AC30), SDK29 tag29.3100, Tapir 1.5.9/1.7.1 исходники и MIT license, Graphisoft SDK EULA. Локальный Tapir1.5.10/ABI/build5101 не проверены. `GetViewSettings` — tagged source, не установленная команда.

## Контрааудит B
Новый Router/SceneWriter/IFC engine не нужен; C1 related не adjacency; C7 bbox не BREP; C8 имена комбинаций не гарантируют реальную видимость. PR173 batch не повторять. Не использовать прямой SDK-only API без существующего binding. Никаких заявлений о 100×.

## Передача №3
Рассмотреть C1, C2, C4, C5(saved-view), C8(view labels), C7; C3/C6 оставить DEFER. №1 запросить: допустимые zone elementTypes; component propertyIds и negative status; источник master layout linkage; готовый proxy→source binding; точный per-layer visibility contract; единицы bbox.

**Стадии:** SOURCE — выполнено, OFFLINE/BUILD/INSTALLED/LIVE — новых нет, ACCEPTED — нет. MODEL_MODE_NOT_VERIFIABLE. Канонический PROJECT_PLAN.json revision182 прочитан (blob c2ab2f9d), не изменён. Main/PLN/APX/code/NEXT_RESEARCH_PRIORITIES не изменены.
