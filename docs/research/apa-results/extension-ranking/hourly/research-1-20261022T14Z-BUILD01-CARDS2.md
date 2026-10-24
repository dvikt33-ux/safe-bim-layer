# APA №1 BUILD-01 — карточки решений 4–6

## C4 — безопасная запись GDL array (G2, не для первого здания)
**Источник:** [PR558](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/558), Tapir 1.7.2, MIT. **Вход:** имя параметра, index1/index2 либо массив той же dimension1×dimension2. **Выход:** execution result, повторное чтение. **Ограничение:** resize запрещён; автор PR пишет unbuilt/untested и возможный hang скрипта. **Интеграция:** после отдельной проверки installed APX; для первого BUILD-01 использовать проверенные library defaults. **№2:** запретить несанкционированные GDL writes. **Решение:** EXCLUDE_P0.

## C5 — CreateSlabs с materialId (G2, версия-дрейф)
**Источник:** [PR785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785), Tapir 1.7.2, MIT. **Вход:** structureType Basic/Composite + buildingMaterialId/compositeId. **Выход:** Slab GUID (по схеме). **Ограничение:** PR unbuilt/unreviewed; pinned 1.5.10 этих CREATE-полей не имеет. **Интеграция:** не заменять существующий PR74 CREATE→MODIFY+material readback. **№2:** сопоставить фактический APX schema, не писать код. **Решение:** DEFER.

## C6 — официальный независимый типо-материальный readback (G4)
**Источник:** [Graphisoft API29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html), Python 29.3000, лицензия Graphisoft. **Вход:** GUID элементов, GUID атрибутов, component IDs. **Выход:** GetTypesOfElements, GetAttributesIndices, GetPropertyValuesOfElementComponents с OrError. **Интеграция:** после G3 сравнить typed DAG/материал GUID/индекс и ошибки по каждому GUID. **Риск:** onlySupportedTypes фильтрует часть объектов; GetElementsByType не доказывает охват всех databases. **№2:** строгий fail-closed reconciliation после Save/Open. **Решение:** SOURCE_RECOMMENDED, не LIVE.
