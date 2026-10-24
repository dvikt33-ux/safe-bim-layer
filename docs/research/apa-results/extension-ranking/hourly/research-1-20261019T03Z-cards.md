# APA №1 20261019T03Z — 8 карточек для исследователя интеграции №2

## C1 — Зоны→связанные элементы (94/100)
**Готовая функция и версия:** AC29 Python b3000 GetElementsRelatedToZones(zones,elementTypes) → ElementsOrError; lines 700–718; union elements/error lines 2654–2669. [Первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Почему не дубликат:** Не дублирует создание зон или PR159/162: native read-only relation evidence.
**Что подключить, неизвестные API/ABI/данные/лицензия:** Штатный JSON; неизвестны supported elementTypes, семантика related, runtime build5101.
**Вопрос №2:** №2: какие Wall/Door/Window types допустимы, что вернётся для empty и invalid zone?.
**Критерий ГОТОВО:** ГОТОВО: три read-only fixtures с GUID readback, без PLN write.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.

## C2 — Компонентные свойства/QTO (92/100)
**Готовая функция и версия:** AC29 Python b3000 GetComponentsOfElements + GetPropertyValuesOfElementComponents; ElementComponentId(elementId,componentId), lines 548–565,1018–1037,2549–2594. [Первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Почему не дубликат:** Существующий IFC/QTO не заменяется; это нативная проверка послойных свойств.
**Что подключить, неизвестные API/ABI/данные/лицензия:** Штатный JSON; неизвестны property IDs, единицы, пустые компоненты, runtime.
**Вопрос №2:** №2: какие свойства доступны для композита и как выглядит ошибочная пара?.
**Критерий ГОТОВО:** ГОТОВО: композит/однослойный/invalid component, тип+единица+GUID сверены.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.

## C3 — Hotlink source↔proxy GUID provenance (91/100)
**Готовая функция и версия:** SDK29 GetHotlinkProxyElementTable: key=proxy GUID, value=source GUID, lines 735–766; GetHotlinkInstances/GetContainingHotlinkGuid. [Первоисточник](https://github.com/GRAPHISOFT/archicad-api-devkit/tree/29.3100).
**Почему не дубликат:** PR173 batch Hotlink уже LIVE saved/reopened; новый writer не нужен.
**Что подключить, неизвестные API/ABI/данные/лицензия:** C++ SDK29 EULA; JSON/Tapir1.5.10 binding NOT_FOUND; не компилировать.
**Вопрос №2:** №2: есть ли готовая установленная read-only команда для proxy mapping?.
**Критерий ГОТОВО:** ГОТОВО: при binding 2 roots/48 children mapping readback; без binding SDK_ONLY/DEFER.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.

## C4 — Размеры листов перед Publisher (87/100)
**Готовая функция и версия:** AC29 Python b3000 GetLayoutSettings(layoutNavigatorItemId) → LayoutParameters; GetNavigatorItemTree/GetNavigatorItemsType, lines 814–886. [Первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Почему не дубликат:** №2 уже изучает Publisher preflight; новая узкая проверка формата/ориентации/параметров.
**Что подключить, неизвестные API/ABI/данные/лицензия:** Штатный JSON; неизвестны поля/единицы LayoutParameters и master linkage.
**Вопрос №2:** №2: что уже проверяется в текущем preflight, что реально отсутствует?.
**Критерий ГОТОВО:** ГОТОВО: два формата, master, invalid item, без публикации.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.

## C5 — Фильтры реконструкции (83/100)
**Готовая функция и версия:** SDK29 GetRenovationFilters/GetActualRenovationFilter/GetRenovationFilterName, lines 159–250. [Первоисточник](https://github.com/GRAPHISOFT/archicad-api-devkit/tree/29.3100).
**Почему не дубликат:** Не дублирует создание элементов, PDF/IFC/Hotlink.
**Что подключить, неизвестные API/ABI/данные/лицензия:** C++ only; готовый JSON binding NOT_FOUND; SetActual меняет состояние и запрещён.
**Вопрос №2:** №2: доступен ли read-only wrapper без переключения current filter?.
**Критерий ГОТОВО:** ГОТОВО: GUID/имена/current vs saved view или DEFER.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.

## C6 — Синтаксис выражений свойств (82/100)
**Готовая функция и версия:** SDK29 CheckPropertyExpressionString → NoError/APIERR_BADEXPRESSION, lines 2269–2296; GetPropertyExprReferenceString. [Первоисточник](https://github.com/GRAPHISOFT/archicad-api-devkit/tree/29.3100).
**Почему не дубликат:** Не повторяет классификации атрибутов №2; проверяет syntax.
**Что подключить, неизвестные API/ABI/данные/лицензия:** SDK EULA; JSON binding NOT_FOUND; syntax не равно вычислимости.
**Вопрос №2:** №2: готовый binding или SDK_ONLY?.
**Критерий ГОТОВО:** ГОТОВО: valid/invalid expression и код ошибки, без записи.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.

## C7 — 2D/3D AABB cross-check (80/100)
**Готовая функция и версия:** AC29 Python b3000 Get2DBoundingBoxes/Get3DBoundingBoxes, lines 195–229, global origin. [Первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Почему не дубликат:** PR154/160 PDF geometry и native BREP уже существуют; только независимая AABB диагностика.
**Что подключить, неизвестные API/ABI/данные/лицензия:** Штатный JSON; только Element Information, bbox ≠ BREP.
**Вопрос №2:** №2: какие типы поддержаны и как отличаются bounds от native BREP?.
**Критерий ГОТОВО:** ГОТОВО: rotated object, multi-floor, unsupported type, без геометрической записи.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.

## C8 — Перья/комбинации слоёв выпуска (76/100)
**Готовая функция и версия:** AC29 Python b3000 GetActivePenTables/GetLayerCombinationAttributes, lines 231–244,795–813. [Первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Почему не дубликат:** №2 уже имеет Attribute inventory; только cross-check с документацией.
**Что подключить, неизвестные API/ABI/данные/лицензия:** Штатный JSON; неизвестны flags LayerCombinationAttribute, возможны допустимые различия.
**Вопрос №2:** №2: есть ли достаточные поля для QA visibility без новых инструментов?.
**Критерий ГОТОВО:** ГОТОВО: две конфигурации и whitelist отличий; никаких изменений атрибутов.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; speed=NOT_MEASURED.
