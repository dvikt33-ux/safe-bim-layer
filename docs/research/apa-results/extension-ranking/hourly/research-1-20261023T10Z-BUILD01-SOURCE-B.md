# APA №1 | 2026-10-23 10Z | BUILD-01 | SOURCE S15–S28

14 дополнительных разных PR/issues прочитаны непосредственно 23.10.2026. Итого S01–S28 = **28 отдельных SOURCE-проверок**, не 30. Upstream Tapir MIT, license blob `1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd`; лицензии иных компонентов не проверялись. SOURCE не означает INSTALLED/LIVE/ACCEPTED.

## S15 — G2 — Есть ли готовая проверка значения property до WRITE?
**Источник:** [PR #1147](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1147). **Версия/поля/факт:** OPEN; CheckPropertyValues 1.7.2; {propertyValues:[{propertyId,propertyValue:{value}}]} → isValid/error; ACAPI_Property_IsValidValue.
**Решение/ограничение:** Не проверено в Archicad, не установлено 1.5.10; свойства не заменяют проверку атрибутов Slab.
**Адресное задание №2:** №2: использовать существующий read-only GetPropertyValuesOfElements, не требовать нового property API.

## S16 — G2 — Можно ли прочитать доступность свойства в native tool defaults?
**Источник:** [PR #1279](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1279). **Версия/поля/факт:** OPEN; GetPropertyAvailabilityOfDefaults 1.7.3, AC26+; {elementType,properties}→{available,visible}.
**Решение/ограничение:** Не проверено в Archicad; Favorite учитывается только после применения к tool default; риск изменения состояния.
**Адресное задание №2:** №2: не включать в обязательный G2; проверять конечные свойства фактических элементов.

## S17 — G2 — Можно ли отличить невидимое свойство от недоступного и неизменяемого?
**Источник:** [PR #1238](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1238). **Версия/поля/факт:** OPEN; GetPropertyEditability 1.7.3; editable/visible по GUID элемента, tool defaults, definition default.
**Решение/ограничение:** Untested, API сигнатуры AC25–30 не проверены DevKit; это свойства, не geometry/material.
**Адресное задание №2:** №2: NOT_APPLICABLE для первичной native сборки.

## S18 — G2 — Можно ли прочитать property values из текущего default инструмента?
**Источник:** [PR #1336](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1336). **Версия/поля/факт:** OPEN; GetPropertyValuesOfElementDefaults 1.7.3; elementType+properties→propertyValues; API_Element_GetPropertyValuesOfDefaultElemByGuid.
**Решение/ограничение:** Untested; Favorite only if applied; default tool не доказывает параметры размещённого элемента.
**Адресное задание №2:** №2: проверять post-create readback, не default вместо результата.

## S19 — G4 — Есть ли готовый быстрый поиск по критериям внутри процесса?
**Источник:** [PR #1292](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1292). **Версия/поля/факт:** OPEN; GetElementsByCriteria, propertyCriteria, floorIndices/layerIndices/types, typed length m/area m²/angle rad; заявлена экономия JSON на 1000+ элементах.
**Решение/ограничение:** Нет benchmark для APA/AC29 build5101; не локально; скорость не закрывает BREP или ошибку GUID.
**Адресное задание №2:** №2: пока использовать существующие read-only batch API и точные GUID; 100× не заявлять.

## S20 — G2 — Всегда ли optional поле JSON-схемы действительно необязательно?
**Источник:** [Issue #1402](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1402). **Версия/поля/факт:** OPEN; Tapir1.7.2 AC27/29/30 macOS: CreatePropertyDefinitions без defaultValue возвращает ошибку, хотя schema marks optional.
**Решение/ограничение:** Не доказывает ошибку CreateSlabs или Tapir1.5.10; но предупреждает о расхождении runtime semantics/schema.
**Адресное задание №2:** №2: G0 фиксировать runtime schema, G2 тестировать реальные разрешённые параметры отдельно; не использовать CreatePropertyDefinitions в BUILD-01.

## S21 — G2 — Может ли omitted holes незаметно уничтожить отверстия при Modify?
**Источник:** [Issue #1403](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1403). **Версия/поля/факт:** OPEN; Tapir1.7.2 AC27/29/30 macOS: ModifyMeshes polygonCoordinates без holes удаляет holes; holes-only сообщает success без эффекта.
**Решение/ограничение:** Это Mesh, не Slab; перенос поведения на ModifySlabs запрещён; реального BUILD-01 Mesh blocker нет.
**Адресное задание №2:** №2: отдельно читать holes до/после ModifySlabs, не выводить bug Slab из Mesh issue.

## S22 — G2 — Безопасно ли менять массивные GDL-параметры сторонних окон?
**Источник:** [Issue #557](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/557). **Версия/поля/факт:** CLOSED; AC28 build6003 Windows11, Tapir1.5.7, Cadimage CI Tools Window: glazingPanelType зависание, glazingPanelN success + повреждение GDL параметров.
**Решение/ограничение:** Другие версия/производитель, не доказано на AC29 5101; закрытый issue не означает фикс в локальной 1.5.10.
**Адресное задание №2:** №2: исключить arbitrary GDL parameter mutation для окон BUILD-01; применять проверенные Favorites/part defaults и readback.

## S23 — G4 — Равен ли GetAllElements полному списку физических 3D элементов?
**Источник:** [Issue #347](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/347). **Версия/поля/факт:** CLOSED; репорт: IsVisibleIn3D зависит от текущего 3D окна, IsIndependent применим ограниченно; возможны ghost GUID; API фильтры не эквивалентны BREP.
**Решение/ограничение:** Исторический репорт без доказательства на AC29 build5101; нельзя делать универсальный вывод о всех элементах.
**Адресное задание №2:** №2: независимый inventory: GUID+type+story+host и geometry, отдельно errors/hidden/subelements; не считать число GetAllElements достаточным G4.

## S24 — G2/G4 — Доступны ли диагностические сообщения ошибок GDL-скриптов?
**Источник:** [Issue #1400](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1400). **Версия/поля/факт:** OPEN; запрос command GDL errors/warnings (script, line, message), AC29 Windows Tapir1.7.2; текущий CheckLibraries возвращает только success/error по описанию.
**Решение/ограничение:** Запрос, не реализация; нельзя выдавать GDL error diagnostics за доступный инструмент локально.
**Адресное задание №2:** №2: при пустой библиотечной геометрии — маркировать GDL_DIAGNOSTICS_NOT_FOUND, проверять part loaded и видимую геометрию.

## S25 — G0/G4 — Может ли API сообщить NoError без фактического изменения?
**Источник:** [PR #674](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/674). **Версия/поля/факт:** OPEN DRAFT; GetProjectInfoFields фильтрует созданные autotext GUID; Create/DeleteProjectInfoFields могли возвращать NoError без изменения на AC29.
**Решение/ограничение:** Не проверено build/review; касается Project Info fields, не GetProjectInfo path; принцип readback применим, но не переносить bug на SaveProject.
**Адресное задание №2:** №2: любое WRITE квалифицировать независимым readback; ProjectInfo mutation не использовать.

## S26 — G4 — Как идентифицировать GUID ошибочного элемента в batch readback?
**Источник:** [PR #1406](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1406). **Версия/поля/факт:** OPEN; GetDetailsOfElements error message с GUID, один result на каждый input по порядку; schema описывает alignment.
**Решение/ограничение:** Untested, не локальная 1.5.10; успешность batch без GUID недостаточна.
**Адресное задание №2:** №2: сохранять input GUID array и связывать ответ по index; при расхождении длины STOP/UNKNOWN.

## S27 — G0 — Всегда ли GetProjectInfo.projectLocation присутствует?
**Источник:** [PR #792](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/792). **Версия/поля/факт:** OPEN; Teamwork location_team вместо location; автор LIVE проверил AC27 macOS BIMcloud teamwork:// reference.
**Решение/ограничение:** Для локального scratch PLN не подтверждённый blocker; изменение проекта не требуется.
**Адресное задание №2:** №2: G0 использовать projectLocation плюс идентичность реального файла/окна, Teamwork кейс NOT_APPLICABLE.

## S28 — G4 — Можно ли штатно прочитать настройки Layout Subset для контроля модели?
**Источник:** [PR #1430](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1430). **Версия/поля/факт:** CLOSED UNMERGED; GetLayoutSubsetSettings, API SubSet; автор live AC27 macOS для Layout Book.
**Решение/ограничение:** Это чертёжный Layout, не нативная 3D модель; unmerged, отсутствует в локальном 1.5.10.
**Адресное задание №2:** №2: исключить из BUILD-01 G4; не подменять Save/Open.
