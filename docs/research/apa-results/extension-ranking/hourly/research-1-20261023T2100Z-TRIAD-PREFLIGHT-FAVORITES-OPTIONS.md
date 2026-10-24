# APA №1 — 2026-10-23 21:00 UTC — TRIAD / готовые preflight, Favorites, Design Options и риск GH-классификаций

## Реальное влияние на BUILD-01 (#192) — P0, ДО перечня находок

**НОВОЕ, SOURCE_ONLY:** В уже закреплённой схеме Tapir 1.5.10 обнаружены три практически применимых, ранее не выделенных в TRIAD механизма: (1) GetAllElements/GetElementsByType с фильтрами IsEditable/IsVisibleByLayer/OnActualFloor/InMyWorkspace/HasAccessRight для проверки допустимости изменений; (2) ApplyFavoritesToElements v1.5.4 — выборочное применение **настроек, классификаций, категорий, свойств к существующему GUID без перемещения/изменения размеров**, вместо удаления/повторного создания; (3) GetDesignOptionForElements v1.5.1 — выявление элементов, скрытых альтернативой Design Option, до BIM-readback и IFC-экспорта. Это не автоматический выбор приложения и не полноценная трёхсторонняя синхронизация.

**НОВЫЙ upstream-риск:** [Tapir PR #1141](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1141) (merged 23.10.2026) исправляет GH GetClassificationsOfElements, который до исправления возвращал null для успешно классифицированных элементов; также исправлен недопустимый JSON null для unclassified. Локальный GH plugin неизвестен; **нельзя принимать null от GH как доказательство отсутствия классификации**. Релиз 1.7.2 датирован 19.10.2026, то есть исправление после релиза, не pinned 1.5.10.

**G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN.** Для **нового** BUILD-01: SOURCE=30 отдельных проверок контрактов/источников; OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0. Исторические 21 элемента PR74 не обнуляются, но не являются новым TRIAD LIVE. FULL_THREE_WAY_SYNC=NOT_FOUND_IN_CHECKED_SOURCES. Никаких записей в PLN, кода, APX, установки, LIVE, merge.

## Прочитанная база и источники (версии и лицензии)

- [BUILD-01 issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74): существующий DynamicCommands → BIM Graph → SceneWriter/SQLite; PR74 исторический 21-элементный native building, но не новое здание тройной связки.
- [TRIAD-PIVOT 11Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md), [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md), [№2 20Z report](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T20Z-triad-report.md), [№2 20Z matrix](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T20Z-triad-matrix.md), [№3 20.10 18Z A](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md) и [B](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-B.md); свежего №3 23.10 по листингу hourly не найдено. Матрица 61 прочитана по blob 9cb5e6f2a59f80762cc77073eeb10404829af75a, count=61. PROJECT_PLAN rev182 не изменялся и напрямую не извлекался.
- [Закреплённая схема 262 команд Tapir 1.5.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json), Git blob **e8ad53b6ea7c19dc34cbdcb723a79be995639cd7**. Это исторический snapshot GenerateDocumentation, **не доказательство текущего INSTALLED/APX**. Tapir: [официальная документация](https://enzyme-apd.github.io/tapir-archicad-automation/archicad-addon/), [MIT](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE).
- [Graphisoft Archicad 29 — Design Options](https://help.graphisoft.com/AC/29/INT/_AC29_Help/071_DesignOptions/071_DesignOptions-2.htm); [Graphisoft AC29 Grasshopper Live Connection guide](https://help.graphisoft.com/AC/29/INT/GC.pdf). Graphisoft GH add-on бесплатен при отдельно лицензируемых Archicad и Rhino; прямой контракт AC↔GH ограничен поддерживаемыми типами.
- Upstream Tapir [#412](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/412) (LockElements/UnlockElements 1.5.2); [#929](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/929) и [#964](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/964)/[#1025](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1025)/[#1028](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1028)/[#1030](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1030) (Project Preferences); [#944](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/944) и [#968](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/968)/[#1140](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1140)/[#1141](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1141) (property/classification defaults и GH bug). **PR ≠ локальный релиз или испытание**.

## 30 конкретных SOURCE-проверок (не 30 независимых источников и не LIVE-тесты)

| ID | Проверенный контракт или граница | Основание |
|---|---|---|
| S01 | Issue192 требует G0→G5, новая scratch PLN, полное здание, независимый Save/Close/Reopen. | BUILD |
| S02 | PR74 исторически создал 10 Wall, 2 Slab, 6 Window, 2 Door, 1 Roof; не Rhino/GH TRIAD. | PR74 |
| S03 | Pinned snapshot содержит 262 команды Tapir, provider_version=1.5.10, не текущий APX. | PIN |
| S04 | GetAllElements v1.0.7 допускает optional filters/databases и не требует elementType. | PIN |
| S05 | GetElementsByType v1.0.7 требует elementType, допускает optional filters/databases. | PIN |
| S06 | ElementFilter enum содержит IsEditable; он даёт отбор, не объясняет причину не-редактируемости. | PIN |
| S07 | ElementFilter содержит IsVisibleByLayer и IsVisibleIn3D; видимость и право записи — разные признаки. | PIN |
| S08 | ElementFilter содержит OnActualFloor и OnActualLayout; текущий этаж/вид может сузить инвентарь. | PIN |
| S09 | ElementFilter содержит InMyWorkspace и HasAccessRight; это фильтры, не Teamwork lease. | PIN |
| S10 | В enum нет IsLocked; сравнение IsEditable не доказывает, что причина именно manual lock. | PIN |
| S11 | LockElements v1.5.2 принимает обязательный elements и меняет состояние проекта. | PIN |
| S12 | UnlockElements v1.5.2 — manual lock, **не Teamwork reservation**. | PIN + #412 |
| S13 | #412 подтверждает: снятие блокировки слоя само по себе не разблокирует вручную locked element. | #412 |
| S14 | ApplyFavoritesToElements v1.5.4 принимает массив {elementId,favorite}. | PIN |
| S15 | Четыре независимых флага: applySettings, applyClassifications, applyCategories, applyProperties. | PIN |
| S16 | Все четыре флага по умолчанию true: отсутствие флагов может изменить больше ожидаемого. | PIN |
| S17 | По контракту ApplyFavoritesToElements не перемещает элемент и не меняет floor/dimensions; изменение атрибутов требует readback. | PIN |
| S18 | Для Stair/Railing/Curtain Wall настройки подэлементов Favorite **не** применяются. | PIN |
| S19 | GetFavoritesByType v1.2.2 получает имена Favorite заданного elementType; read-only. | PIN |
| S20 | ApplyFavoritesToElementDefaults v1.1.2 меняет defaults инструмента, а не один выбранный элемент; WRITE. | PIN |
| S21 | GetCalculationUnits v1.4.0 отдаёт length/area/volume/angle calculation units, не весь набор WorkingUnits/Dimensions. | PIN + #929 |
| S22 | #929 описывает недостающие WorkingUnits/Dimensions/ReferenceLevels/Zones; GetProjectPreferences отсутствует в PIN. | PIN + #929 |
| S23 | PR #964 (open) вводит Get/SetProjectPreferences с WorkingUnits/CalculationUnits/ReferenceLevels, upstream без Archicad LIVE. | #964 |
| S24 | PR #1025 (merged) добавляет Dimensions; #1028 (open) — Zones; #1030 (open) — GH components; не в локальной 1.5.10. | PR |
| S25 | GetDesignOptionForElements v1.5.1 возвращает тип связи NotExistingElement/MissingDesignOption/NotLinkedToAnyDesignOption/LinkedToDesignOption. | PIN |
| S26 | GetElementsOfDesignOptions v1.5.1 read-only, но PIN output schema использует ключ **#ref**, не **$ref**; автоматическую JSON-schema валидацию не считать доказанной. | PIN |
| S27 | Graphisoft AC29: новые элементы могут попадать в default Design Option; неактивные Options скрыты, а не удалены. | G29 Options |
| S28 | GH PR #1141 (merged 23.10) исправляет GetClassificationsOfElements: до исправления успешные классификации могли выходить null из-за неверного wrapper. | #1141 |
| S29 | GH PR #1141 также исправляет JSON classificationItemId:null (нужно пропустить поле для unclassified); #968 property-default commands всё ещё open, #1140 classification-default merged. | #1141/#968/#1140 |
| S30 | AC29 GH Deconstruct требует Send Changes для ручных AC edits; Deconstruct Roof только SinglePlane, поэтому полной автоматической 3-way sync нет. | G29 GH |

## Семь адресных карточек: операция → версия/лицензия/контракт/направление → ограничение → №2

### C2100-01 P0 — Read-only editability/visibility inventory (ГОТОВО В PIN, runtime не подтверждён)
**Операция:** до редактирования стен/окон/кровли собрать GUID-множества GetAllElements без фильтра и с IsEditable/IsVisibleByLayer/IsVisibleIn3D/OnActualFloor/InMyWorkspace/HasAccessRight, затем сравнить. **Источник:** PIN v1.0.7, Tapir MIT. **Направление:** AC29 → JSON/GH/APA, только READ. **Контракт:** filters — непустой массив ElementFilter, databases optional; GetElementsByType требует elementType. **Ограничение:** фильтр может скрыть существующий элемент; IsEditable не является правом на безусловную запись, а отсутствие IsLocked запрещает угадывать причину. **№2:** G0 таблица full set / filtered sets с конкретными GUID и диагностикой разницы; ни одного WRITE.

### C2100-02 P0 — Применение BIM-семантики без ReplaceExisting (ГОТОВО В PIN, путь SceneWriter НЕ ДОКАЗАН)
**Операция:** применить утверждённый Favorite к существующему Wall/Slab/Roof/Window, не перестраивая контур. **Источник:** PIN ApplyFavoritesToElements v1.5.4, Tapir MIT, официальный docs. **Направление:** APA/SceneWriter → AC29 native WRITE, **не** обратная синхронизация; не вызывать напрямую вне существующего writer. **Контракт:** favoritesToApply=[{elementId:{guid},favorite:name}]; explicit applySettings/applyClassifications/applyCategories/applyProperties. Для только свойств: false/false/false/true, если это согласовано с моделью. **Ограничение:** неизменность геометрических параметров по контракту не доказывает неизменность GUID, физических стыков и BREP; у иерархических типов не применяются настройки subelements; Favorite должен существовать. **№2:** проверить существующую SceneWriter allowlist/bound operation, без нового writer; если нет готового маршрута — NOT_WIRED, не обходить SQLite. Подготовить readback GUID/material/classification/properties/host/SEO.

### C2100-03 P0 — Design Option membership до IFC/G4 (ГОТОВО В PIN, runtime не подтверждён)
**Операция:** проверить, что каждое ожидаемое native тело находится в Main Model или нужной активной альтернативе, а не скрыто. **Источник:** PIN GetDesignOptionForElements v1.5.1 и Graphisoft AC29 Design Options; Tapir MIT. **Направление:** AC29 → read-only QA, **не** sync. **Контракт:** elements GUIDs → designOptionForElements с четырьмя типами статуса; GetDesignOptions/GetDesignOptionCombinations дополнительный READ. **Ограничение:** неактивная альтернатива может быть скрыта при 3D Publisher/IFC; GetElementsOfDesignOptions в PIN содержит #ref typo. **№2:** дополнить G0/G4 инвентарь колонкой option status и fail-closed для неожиданного LinkedToDesignOption/MissingDesignOption; не менять активные комбинации.

### C2100-04 P0 GUARD_NOT_LEASE — Manual LockElements (ГОТОВО В PIN, но не применять без допуска)
**Операция:** защитить чужие элементы от случайного редактирования или выявить причину IsEditable=false. **Источник:** PIN LockElements/UnlockElements v1.5.2 и issue #412, Tapir MIT. **Направление:** AC29 WRITE состояния lock, **не** транзакционный lock трёх приложений. **Контракт:** {elements:[{elementId:{guid}}]} → ExecutionResult. **Ограничение:** manual lock не Teamwork; может заблокировать и собственный SceneWriter; не гарантирует остановку GH в других файлах. **№2:** в текущем G0 использовать только READ IsEditable; Lock/Unlock оставить запрещённым WRITE до отдельного разрешения.

### C2100-05 P0 HOLD_VERSION — GH classification null bug и native readback (новое исправление upstream)
**Операция:** после GH→APA→AC проверить классификацию Wall/Slab/Roof/Window. **Источник:** Tapir PR #1141 merged 23.10.2026, #968 open, #1140 merged; PIN GetClassificationsOfElements v1.0.7; Tapir MIT. **Направление:** AC29 → Tapir native JSON read; GH component может иметь дефект; не 3-way sync. **Контракт:** GetClassificationsOfElements {elements,classificationSystemIds} → native classification data; GH старого plugin мог вернуть null для существующей классификации. **Ограничение:** merged #1141 после release 1.7.2, installed GH plugin неизвестен; новое GH defaults UI требует совместимые add-on commands, а #968 ещё open. **№2:** для G2/G4 использовать native JSON readback классификаций, а не старый GH component как единственный источник; не менять версии.

### C2100-06 P1 HOLD_VERSION — Project Preferences/Working Units (upstream готовый PR, НЕ готовый релиз)
**Операция:** исключить неверные рабочие единицы/формат размеров при GH↔AC. **Источник:** PIN GetCalculationUnits v1.4.0, #929, #964(open), #1025(merged), #1028(open), #1030(open); Tapir MIT. **Направление:** в PIN AC→read calculation units; новые upstream Get/SetProjectPreferences предлагают read/write preferences и GH components, но **не в 1.5.10**. **Ограничение:** GetCalculationUnits не удостоверяет WorkingUnits/Dimensions, проектные reference levels и zone reductions; PR без локального DevKit/AC LIVE не ACCEPTED. **№2:** G0 раздельно фиксировать GH document units, PR74 units=meters, AC calculation units и вручную утверждённые working/dimension settings; не писать SetProjectPreferences.

### C2100-07 P1 CONDITIONAL — Favorites defaults вместо глобальных property-defaults (ГОТОВО В PIN, но WRITE)
**Операция:** задать заранее утверждённые значения для будущих native элементов при создании нового scratch. **Источник:** PIN ApplyFavoritesToElementDefaults v1.1.2, GetFavoritesByType v1.2.2, upstream #944/#968; Tapir MIT. **Направление:** AC defaults WRITE, не обновление существующего GUID и не синхронизация. **Контракт:** {favorites:[name]} → executionResults; альтернативный per-element ApplyFavoritesToElements см. C02. **Ограничение:** изменяет глобальные defaults инструмента, что затрагивает последующие операции и чужие процессы; GH автоматический solver может породить конфликт. **№2:** не применять на активном BDD; только после разрешения отдельной scratch, с до/после readback и восстановлением defaults; предпочесть per-element route через SceneWriter при наличии.

## Контрааудит A — источники, лицензии, совместимость, новизна
1. C01–C04 и C07 — **новые способы использования существующих команд** pinned 1.5.10, не новый релиз и не новая установка. Не повторяют уже опубликованные GetConnectedElements/IFC IDs/Content Cache/MCP/Get3DGeometry. C05 — **новое исправление upstream**, которое не доказано в локальном GH. C06 — upstream work-in-progress, не выдавать за установленную функцию.
2. Даты и состояния GitHub проверены напрямую: #1141 merged=true (updated 23.10), #1140 merged=true, #968 open, #964 open, #1025 merged, #1028 open, #1030 open. Нельзя вывести совместимость всех PR из одного merged=true; релиз 1.7.2 19.10 предшествует этим изменениям.
3. PIN GetElementsOfDesignOptions.returns содержит #ref вместо $ref; это недостаток сохранённой схемы, **не доказанный дефект работающей команды**. Требуется независимый native readback.
4. Tapir MIT; официальная GH–AC Connection не заменяет лицензии Rhino/Archicad; новых платных API не требуется. Версии Rhino8/AC29 build5101/Tapir1.5.10 указаны как целевые, но локально в этом проходе не считаны.
5. 30 SOURCE — ровно 30 строк с фактическими проверками контрактов, не 30 внешних ресурсов и не benchmark.

## Контрааудит B — эксплуатационная безопасность и трёхсторонняя модель
1. ApplyFavoritesToElements — потенциально нативный UPDATE свойств, но пока нет подтверждения, что existing SceneWriter умеет этот конкретный bound command; прямой Tapir вызов обошёл бы единственный writer и SQLite. **STOP при NOT_WIRED**, новый writer не создавать.
2. IsEditable=true не доказывает верный проект, owner, hostWall, GUID, библиотеку или отсутствие конфликта с GH. Перед любым будущим WRITE нужны immutable target PLN/port/build/planHash, owner table и READ-before/READ-after. Нельзя считать LockElements cross-app mutex.
3. Design Option membership — отдельная ось помимо layer/story/renovation. Визуально отсутствующий элемент может быть скрыт, а не удалён; IFC export через View может быть неполным. В G4 сравнивать полный native inventory, visible View и IFC IDs.
4. GH null classification не доказывает unclassified: PR #1141 прямо описывает defect. Нативные JSON классификации и свойства нужно читать отдельно и сверять GUID.
5. Отдельные Rhino, GH, Archicad процессы не имеют готового доказанного атомарного commit/rollback и cycle prevention. Полная двусторонняя синхронизация **не найдена**. GH geometry staging → PR74 compiler → SceneWriter остаётся предложенным направленным маршрутом, а не завершённой тройной системой.
6. Нормативные формулы в GH, IFC QA и правильные BIM-классификации не равны доказательству соблюдения СП; G4/G5 не проходили.

## Передача исследователю №2 / безопасный следующий шаг
**Приоритет:** G0 read-only inventory GetProjectInfo+APX SHA+port+stories+GetAllElements (full/filter)+GetDesignOptionForElements+GetFavoritesByType+GetCalculationUnits; отдельная фиксация GH/Rhino document units. Затем G2 без записи: проверить, разрешён ли существующим SceneWriter ApplyFavoritesToElements; проверить native classification readback без старого GH getter; проверить output schema GetElementsOfDesignOptions. Результат — таблица команд с ACTUAL_REGISTERED/SCHEMA_MATCH/BOUND_WRITER/NOT_WIRED и точными ссылками. Без нового кода, установки, LIVE или обхода guard.

**Никаких действий:** main, PR merge, код, PLN/APX, PROJECT_PLAN rev182, ПО, Work/Codex/Arena, платные API не тронуты. MODEL_MODE_NOT_VERIFIABLE.
