# APA №1 | 2026-10-23 09Z | BUILD-01 SOURCE S16–S30

**Режим:** SOURCE_ONLY. Никаких G0/G1/G2 PASS, без установки, LIVE и изменения проекта. Статусы issues/PR получены из GitHub на 2026-10-23. Лицензия исходников Tapir 1.5.9: MIT; официальный Graphisoft Help/SDK — справочные первоисточники, не дополнительный установленный продукт.

## S16 — Есть ли готовое прямое назначение Composite Slab при CREATE?

**Ворота:** G2. **Первоисточник:** [PR785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785). **Версия/статус/факт:** Merged 2026-10-11, но автор указал unbuilt/untested; добавлены structureType,buildingMaterialId,compositeId в поздний upstream, НЕ pinned Tapir1.5.10.

**Готовое решение или ограничение:** Существующий SceneWriter CreateSlabs→ModifySlabs (две отдельные write scopes); новый upstream нельзя копировать в installed schema.

**Адресное задание №2:** №2: точные схемы 1.5.10 и раздельные разрешения CREATE/MODIFY + material readback.

## S17 — Можно ли GetDetailsOfElements получить контур Roof?

**Ворота:** G2/G4. **Первоисточник:** [#569](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/569). **Версия/статус/факт:** OPEN; репорт AC27: RoofDetails не поддержан в switch и TypeSpecificDetails, ModifyRoofs только multi-plane; актуальность для 1.5.10 не подтверждена.

**Готовое решение или ограничение:** Не принимать bbox за полный roof BREP; планировать альтернативный native readback и геометрические критерии.

**Адресное задание №2:** №2: сверить установленную схему GetDetailsOfElements(Roof) и допустимый тип Roof.

## S18 — Возвращаются ли свойства ColumnSegment GUID?

**Ворота:** G4. **Первоисточник:** [#665](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/665). **Версия/статус/факт:** OPEN; AC29 Tapir1.5.9: GetPropertyValuesOfElements для ColumnSegment возвращал статусы без значений.

**Готовое решение или ограничение:** Не требовать property PASS сегмента, если API не поддерживает; использовать родительский Column + сегментные GUID и геометрию.

**Адресное задание №2:** №2: независимая inventory parent/segment и границы неопределённости.

## S19 — Безопасно ли GetDetailsOfElements по всему зданию?

**Ворота:** G4. **Первоисточник:** [#583](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/583). **Версия/статус/факт:** CLOSED; AC29 build3000 USA Win11 Tapir1.5.8: один элемент Hillside House вызывал завершение процесса; воспроизведено бисекцией.

**Готовое решение или ограничение:** Не переносить на локальный 5101; для G4 осторожный read-only scope на новой копии и fail-closed при crash.

**Адресное задание №2:** №2: исключить массовое неограниченное GetDetails до runtime qualification.

## S20 — Может ли AABB Slab завершить Archicad при другом этаже?

**Ворота:** G4. **Первоисточник:** [#686](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/686). **Версия/статус/факт:** CLOSED; AC28 macOS, Get3DBoundingBoxes→ACAPI_Element_CalcBounds на slab без draw environment приводил к crash.

**Готовое решение или ограничение:** Учитывать активное окно/этаж; не считать AABB универсально безопасным и не выдавать за BREP.

**Адресное задание №2:** №2: staged geometry readback с контролем версии и контекста.

## S21 — Есть ли исправление аварийного чтения Slab bounds?

**Ворота:** G4. **Первоисточник:** [PR694](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/694). **Версия/статус/факт:** Merged 2026-09-25; Slab направлен через solid-body path вместо CalcBounds; автор: unbuilt/untested in Archicad.

**Готовое решение или ограничение:** SOURCE upstream, не INSTALLED 1.5.10; готовая концепция безопасного readback.

**Адресное задание №2:** №2: проверить фактический загруженный APX и конкретный Get3DBoundingBoxes Slab code path.

## S22 — Зависит ли SaveProject от активного окна?

**Ворота:** G4. **Первоисточник:** [#681](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/681). **Версия/статус/факт:** CLOSED; AC29 build3000 CZE Win Tapir1.5.9: SaveProject из 3D возвращал ошибку, FloorPlan — success.

**Готовое решение или ограничение:** Готовый guard: перед санкционированным Save проверить FloorPlan; ответ API недостаточен, нужен файл на диске и reopen.

**Адресное задание №2:** №2: GuardedSave с точным scratch PLN и GUI-контекстом; исследователь не вызывает Save.

## S23 — Есть ли upstream fix SaveProject из любого окна?

**Ворота:** G4. **Первоисточник:** [PR683](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/683). **Версия/статус/факт:** Merged 2026-09-28, unbuilt/untested по автору; изменяет SaveProject для non-FloorPlan.

**Готовое решение или ограничение:** Не считать исправление доступным в Tapir1.5.10; пользоваться существующим GuardedSave.

**Адресное задание №2:** №2: read-only сверить установленную регистрацию/версию и предусмотреть FloorPlan fallback.

## S24 — Как проверять реальные host connections без ложной полноты?

**Ворота:** G2/G4. **Первоисточник:** [#371](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/371). **Версия/статус/факт:** OPEN; автор toolkit AC29 Win сообщает: GetConnectedElements требует отдельный connectedElementType для Window/Door/Skylight; in-process HTTP к Tapir может deadlock.

**Готовое решение или ограничение:** Готовый read-only приём: отдельные типовые запросы и объединение GUID; не строить in-process HTTP мост.

**Адресное задание №2:** №2: Window и Door host link проверять раздельно по типам.

## S25 — Можно ли стабильно записать BIM Element ID прямо в CREATE?

**Ворота:** G4. **Первоисточник:** [#902](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/902). **Версия/статус/факт:** OPEN; AC29 build3200 AUT Tapir1.7.1: Create* не принимает id; issue описывает существующий API.SetPropertyValuesOfElements General_ElementID как обход.

**Готовое решение или ограничение:** Для BUILD-01 отделить GUID от отображаемого Element ID; ID не входит в обязательный CREATE, отдельная запись требует разрешения.

**Адресное задание №2:** №2: сопоставлять элементы по GUID+тип+host, не по автоматическому Element ID.

## S26 — Надёжен ли DeleteElements на locked layer?

**Ворота:** G4. **Первоисточник:** [#666](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/666). **Версия/статус/факт:** CLOSED; AC27 macOS Tapir1.5.10: success при отсутствии удаления на locked layer.

**Готовое решение или ограничение:** Никаких удалений в исследовании; в будущем только независимая проверка эффекта и guarded scopes.

**Адресное задание №2:** №2: исключить cleanup/delete из BUILD-01 без отдельного разрешения.

## S27 — Исправлена ли ложная успешность удаления?

**Ворота:** G4. **Первоисточник:** [PR679](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/679). **Версия/статус/факт:** Merged 2026-09-28; per-element deletion results; автор unbuilt/untested, issue #749 сообщает остаточный ordering bug в 1.6.0.

**Готовое решение или ограничение:** SOURCE не локальная гарантия; delete не часть P0 first building.

**Адресное задание №2:** №2: не использовать DeleteElements как cleanup на UNKNOWN.

## S28 — Есть ли штатная диагностика отсутствующих/дублированных библиотек AC29?

**Ворота:** G2. **Первоисточник:** [Graphisoft AC29 Library Manager](https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-43.htm). **Версия/статус/факт:** Официальная справка Archicad29: Library Manager показывает missing/outdated library parts и позволяет найти библиотечный источник; штатный интерфейс, без отдельной лицензии.

**Готовое решение или ограничение:** Готовое встроенное средство AC29; не требует нового Tapir command, не меняет PLN при простом просмотре.

**Адресное задание №2:** №2: read-only зафиксировать предупреждения, точные названия библиотек и Favorites.

## S29 — Является ли Opening tool тем же, что hosted Window/Door?

**Ворота:** G2/G4. **Первоисточник:** [Graphisoft SDK29 Opening](https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_element_1_1_opening.html). **Версия/статус/факт:** Официальная страница Archicad29 C++ API, Opening::Get/Exists/GetConnectedOpenings, Since Archicad29; это API Opening-tool, а не контракт Tapir CreateWindows.

**Готовое решение или ограничение:** Готовый SDK интерфейс не даёт автоматического решения hosted window/door в локальном APX.

**Адресное задание №2:** №2: не подменять окно/дверь Generic Opening при выполнении BUILD-01.

## S30 — Разрешено ли использовать upstream Tapir без платной подписки?

**Ворота:** G0. **Первоисточник:** [Tapir LICENSE 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/LICENSE). **Версия/статус/факт:** Непосредственно прочитан tag 1.5.9, Git blob 1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd: MIT License; это лицензия кода, не доказательство установленной версии.

**Готовое решение или ограничение:** Готовый открытый код можно изучать по MIT; не устанавливать и не заменять APX без допуска.

**Адресное задание №2:** №2: фиксировать фактическую установленную версию, не путать лицензию с LIVE readiness.
