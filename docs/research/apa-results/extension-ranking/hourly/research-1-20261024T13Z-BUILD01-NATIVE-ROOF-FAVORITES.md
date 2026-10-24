# APA R1 | 2026-10-24 13Z | BUILD-01: нативная многоскатная кровля Tapir, Favorites и ограничения GH BREP

**Назначение:** SOURCE-исследование готовых средств Archicad 29 build5101 + Rhino 8 + Grasshopper для BUILD-01 (#192). Без установок, LIVE, изменения исходников, PLN/APX, main, merge или новых writer/router/synchronizer. Исследование НЕ является построенной моделью. `MODEL_MODE_NOT_VERIFIABLE`.

**Главная новая находка (F13-01):** ошибочно считать, что Tapir умеет создавать только односкатную кровлю. В официальном исходном коде ENZYME-APD Tapir **tag 1.5.6 и tag 1.5.9** команда `CreateRoofs` создаёт **native API_PolyRoofID** по умолчанию, если не указан `pivotLine`. С `pivotLine` создаётся `API_PlaneRoofID`. Это уже готовый *нативный* API, а не GDL/Morph. Но не доказано, что текущий PR74 принимает эту ветвь и что локальный APX, называемый «1.5.10», соответствует указанным тегам. **Следовательно: CAPABILITY_SOURCE_FOUND; BUILD-01_ROUTE_NOT_YET_VERIFIED**, а не безусловное «сложная кровля невозможна».

## 1. Новые проверенные карточки (не дублируют Speckle/Worksession R1 10:56Z)

### F13-01 | Два штатных режима CreateRoofs (приоритет 100)
- **Источник:** upstream ENZYME-APD/tapir-archicad-automation, `archicad-addon/Sources/ExtendedElementCommands.cpp`, tag **1.5.9**, blob `bd5cd197e9ad2c0db9e40c1baff877bbdcbfae30`, методы `CreateRoofsCommand::GetInputParametersSchema`, `CreateRoofsCommand::Execute`. Сверен также tag **1.5.6**, blob `61da5547366d63d7321c8c21b9f2b4e82ebbd6f0`. Release 1.5.6 (31.07.2026) включает PR #482 «single- and multi-plane roofs».
- **Готовая команда:** `TapirCommand.CreateRoofs`, `roofsData[]`. Обязательны `level` (число, абсолютная отметка) и `polygonCoordinates` (минимум три 2D точки). Без `pivotLine`: `API_PolyRoofID` (многоскатная). С `pivotLine.begCoordinate/endCoordinate`: `API_PlaneRoofID` (односкатная); `angle` допустим **только** с pivotLine. Многоскатная принимает `eavesOverhang` и `levels[]` (1–16, `levelHeight`, `levelAngle`), а также `polygonArcs`, `holes`, `floorIndex`, `thickness`, `structureType: Basic|Composite`, `buildingMaterialId`, `compositeId`.
- **Геометрия:** native `API_RoofID`; внутри `roofClass` выбирается `API_PlaneRoofID` / `API_PolyRoofID`, затем `ACAPI_Element_Create`. Для multi-plane формируется `API_PolyRoofData` pivot polygon и режим `API_OffsetOverhang`.
- **Маршрут без нового writer:** Rhino/GH вычисляет плановый контур/уклоны → существующий typed intent/PR74 (только если существующий компилятор поддерживает поля) → единственный SceneWriter → существующий Tapir `CreateRoofs` → независимый AC readback. Если PR74 не передаёт `levels`/отсутствие `pivotLine`, это **контрактный пробел PR74**, не отсутствие native-команды Tapir. Никаких прямых GH-native записей в BUILD-01.
- **Критерий ГОТОВО:** G0 schema+APX SHA подтверждены; G1 offline typed payload для двух режимов; G2 локальный native schema PASS; после отдельного разрешения G3 на scratch: Roof GUID/type=Roof, polyRoof geometry, этаж, материал/композит, гребни/ендовы и SEO; G4 Save/Close/Reopen и BREP без расхождений.
- **Ограничение:** наличие API_PolyRoofID **не** доказывает автоматическую реконструкцию произвольной NURBS-кровли Rhino в один Roof, ни сохранение всех гребней/ендов, ни локальный LIVE. До приёмки `SOURCE_ONLY`.

### F13-02 | Воспроизводимость через существующие Favorites (приоритет 95)
- **Источник:** upstream tag 1.5.9 `archicad-addon/Sources/FavoritesCommands.cpp`, blob `a935ff412b6e6bbc85540be3ee381b6f091f1c65`.
- **Готовые команды:** `GetFavoritesByType` (read-only), `ApplyFavoritesToElementDefaults` (запись в defaults), `ImportFavorites`/`ExportFavorites` (.prefs, запись файлов/проекта). У `CreateWalls`, `CreateBeams`, `CreateWindows`, `CreateDoors` есть `favoriteName` в публичных schemas. `ApplyFavoritesToElements` существует, но **изменяет модель**.
- **Практический вывод:** для G0 можно составить read-only список доступных имен Favorites и проверить библиотеки/атрибуты; для G2 документировать имя и источник каждой настройки. Применение Favorite и импорт .prefs — **не G0 READ**, а санкционированная будущая операция. Для многоскатной `CreateRoofs` в проверенном schema **нет поля favoriteName**, поэтому нельзя предполагать его наличие: нужны заранее фиксированные defaults/материалы + readback.
- **Ограничение:** `GetFavoritesByType` не даёт автоматически полного дампа каждого default property. См. F13-04.

### F13-03 | Deconstruct Brep: ограниченный, но готовый AC→GH контроль (приоритет 90)
- **Источник:** официальный Graphisoft AC29 Grasshopper–Archicad Live Connection User Guide, раздел «Use Deconstruct Component to Extract Brep Data», стр. 41.
- **Восемь явно названных типов:** **Beam, Column, Slab, Wall, Mesh, Zone, Shell, Single-Plane Roof**. Выход `Brep` описан как **список поверхностей**, а не гарантия одного закрытого solid.
- **Маршрут:** после native SceneWriter CREATE → GH AC Reference/Deconstruct → Brep + Settings/selected surfaces → независимое сравнение с Rhino/GH геометрией и исходным заданием. Для Window/Door/Generic Opening и **Multi-Plane Roof** не считать Deconstruct-Brep поддержанным только на основании этого перечня: их native геометрию проверять через существующий APA/Tapir readback, если фактически доступен.
- **Критерий ГОТОВО:** GH readback не меняет PLN; сравниваются поверхности/оболочка, тип, параметры, GUID через отдельный native inventory, а не только GH preview.

### F13-04 | Свойства и классификации *defaults* ещё не готовый универсальный API (приоритет 95)
- **Источник:** upstream issue #944 от 17.10.2026, статус OPEN при чтении; запрашиваются `Get/SetPropertyValuesOfElementDefaults` и `Get/SetClassificationsOfElementDefaults`. Существующие `Get/SetPropertyValuesOfElements` относятся к **размещённым элементам**, не к defaults.
- **Следствие:** невозможно объявить полную машинную инвентаризацию всех Tool Defaults только по `GetFavoritesByType`/списку атрибутов. До подтверждённого local API использовать read-only manifest шаблона и Favorites, явные значения в typed intent, и независимый readback после записи.
- **Важно:** поздние PR по issue #944 не равны установленному Tapir 1.5.10. Ни новую команду, ни автоматическую классификацию defaults не считать `INSTALLED`.

### F13-05 | Zero-length Wall guard уже исправлен upstream, но local binary неизвестен (приоритет 92)
- **Источник:** upstream issue #433 (Tapir 1.5.3, AC26 Win, 28.06.2026): `CreateWalls` с beg=end приводил к аварийному завершению Archicad; закрыто PR #443 15.07.2026. В tag 1.5.6 и tag 1.5.9 проверен `IsSame2DCoordinate` guard, возвращающий ошибку без создания элемента.
- **Вывод:** офлайн-проверка ненулевой длины стен остаётся обязательной для BUILD-01 независимо от наличия upstream исправления. Локальную APX-сборку 1.5.10 и её связь с исходниками не проверяли. Не утверждать, что она уязвима или исправлена.

### F13-06 | Компоненты и версии/лицензии (приоритет 90)
- **Graphisoft официальный каталог:** Grasshopper–Archicad **29** Live Connection **build 3000**, Windows 16.8 MB, 01.10.2025, поддерживает Rhino **7/8**; не для Start Edition. Add-on распространяется отдельно, но лицензии Archicad/Rhino необходимы. Это не доказательство совместимости конкретной локальной APX-сборки и Rhino8 SR.
- **Tapir upstream:** официальный Add-On расширяет Archicad JSON API, Grasshopper plugin называется `tapir` в Rhino Package Manager. Это **два отдельных компонента**; GH Tapir plugin не равен Graphisoft Live Connection и не заменяет SceneWriter.
- **Версионный риск:** публичный upstream release list на 24.10.2026 показывает 1.5.9 → 1.6.0 → 1.7.x; **тег `1.5.10` / `v1.5.10` не найден** в GitHub contents по проверенному пути. Название «локальный Tapir 1.5.10» принимается как заданное пользователем, но происхождение бинарника, schema и SHA = `NOT_VERIFIED`. Не обновлять/заменять APX автоматически.

### F13-07 | Более широкий typed-контракт стен и балок без новой архитектуры (приоритет 88)
- **Upstream tag 1.5.9:** `CreateWalls` принимает `structureType=Basic|Composite|Profile`, `buildingMaterialId`, `compositeId`, `profileId`, `referenceLineLocation`, `floorIndex`, `arcAngle`, `favoriteName`, помимо beg/end/height/thickness. Для стен `floorIndex` меняет трактовку `zCoordinate` на **offset от этажа**.
- `CreateBeams` принимает `floorIndex`, `slantAngle`, `isSlanted`, `profileAngle`, `arcAngle`, `verticalCurveHeight`, `width`, `height`, `buildingMaterialId`, `profileId`, `favoriteName`. Условие схемы: `begCoordinate`, `endCoordinate`, `zCoordinate` обязательны.
- **Ограничение:** наличие полей в upstream Tapir не означает, что authored PR74 или существующий connected Beam CLI принимает/передаёт все поля. Это задача сопоставления G2, не разрешение добавлять второй writer.

## 2. Десять маршрутов BUILD-01 — строго один SceneWriter

| № | Операция | Готовый инструмент и путь | Граница / будущая приёмка |
|---|---|---|---|
| 01 | Этажи | AC29 Story Settings, Tapir GetStories → PR74 storyBindings | read-only index/floorId/elevation, повторить после reopen; программная GH CreateStory в существующем PR74 NOT_FOUND |
| 02 | Стены | PR74/SceneWriter→Tapir CreateWalls, upstream typed Basic/Composite/Profile | floorIndex vs zCoordinate, favorite, ненулевая длина, native Wall GUID/material/height/BREP |
| 03 | Перекрытия | PR74→Tapir CreateSlabs, AC Favorites/defaults | толщина/структура/holes после readback; PR149 local schema material fields NOT_VERIFIED |
| 04 | Колонны | существующий PR74 CreateColumns, AC29 native Column | story/axis/section/material/children/BREP; local registration NOT_VERIFIED |
| 05 | Балки | существующий connected CLI→Tapir CreateBeams→SceneWriter | Beam/BeamSegment GUID, profile/material/curve, G2 контракт PR74 vs connected CLI NOT_VERIFIED |
| 06 | Односкатная кровля | CreateRoofs с pivotLine + angle, через существующий writer при поддержке schema | Roof GUID, угол, опорная линия, материал, Save/Open |
| 07 | Многоскатная кровля **НОВОЕ** | CreateRoofs БЕЗ pivotLine; polygonCoordinates, levels/eavesOverhang, API_PolyRoofID | native API SOURCE_FOUND, PR74 routing/local APX/actual ridges+valleys NOT_VERIFIED |
| 08 | Окна/двери | CreateWindows/CreateDoors c ownerWallId GUID, centerOffset, sillHeight, favoriteName | hosted native type, opening cut, library part/material, Save/Open; generic Opening отдельный |
| 09 | Библиотеки/атрибуты | AC Library Manager/Favorites; Tapir GetFavoritesByType read-only | Library Part identity, отсутствующие объекты, exact defaults; Import/Apply только после разрешения |
| 10 | Параметрика/нормы | Rhino8/GH расчёт→typed PR74 intent; AC→GH Deconstruct BREP (ограниченные типы); IFC/APA QA read-only | точные единицы/этажи/габариты/эвакуация/доступность; нормативная экспертиза NOT_FOUND |

**Единый порядок каждой будущей операции:** выбор инструмента/источника → расчёт GH/Rhino или authored intent → фиксация результата → существующий SceneWriter (только после отдельного G3 допуска) → read-only AC→GH/APA → GUID/type/story/host/material/geometry/BREP → GuardedSave → Close/Open → independent inventory → при сбое STOP+read-only reconcile, не повторять CREATE. Rhino Object ID ≠ AC GUID; native three-way synchronization/atomic rollback **NOT_FOUND**.

## 3. Журнал реальных SOURCE-проверок — 22 утверждения, не 22 независимых сайта и не LIVE

| ID | Предмет | Проверенный источник | Результат |
|---|---|---|---|
| S01 | BUILD-01 G0–G5, 2 этажа, один writer | GitHub issue #192 | SOURCE |
| S02 | Исследовательский P0 TRIAD | research-1-20261023T11Z-TRIAD-PIVOT.md, blob 896fa3af | SOURCE |
| S03 | Канонический путь приоритетов | extension-ranking/NEXT_RESEARCH_PRIORITIES.md, blob 6f074693 | SOURCE |
| S04 | Matrix 61 и TAPIR-EXISTING | priority_matrix_20261018.json, GitHub fetch | SOURCE |
| S05 | R1 10:56Z Speckle sidecar, не native writer | research-1-20261024T1056Z-TRIAD-SPECKLE-RHINO-REFERENCE-QA.md, blob 0b113aca | SOURCE |
| S06 | R2 12Z G0 blocked/SceneWriter single writer | research-2-integration-2026-10-24T12Z-report.md, blob 1e2e2aa6 | SOURCE |
| S07 | Graphisoft AC29 Live Connection build3000/Rhino7-8 | Graphisoft official download catalogue, 01.10.2025 | SOURCE |
| S08 | Live Connection not Start Edition | Graphisoft official download catalogue | SOURCE |
| S09 | Deconstruct Brep supports eight listed types | AC29 GC.pdf, p.41 | SOURCE |
| S10 | Deconstruct Brep returns list of surfaces | AC29 GC.pdf, p.41 | SOURCE |
| S11 | CreateRoofs multi-plane by default | Tapir ExtendedElementCommands.cpp tag1.5.9, blob bd5cd197 | SOURCE |
| S12 | pivotLine creates single-plane | same tag1.5.9 source | SOURCE |
| S13 | levels 1..16, eavesOverhang, structure/composite fields | same tag1.5.9 source schema | SOURCE |
| S14 | native API_PolyRoofID + ACAPI_Element_Create | same tag1.5.9 source Execute | SOURCE |
| S15 | native multi-plane already in 1.5.6 | tag1.5.6 blob 61da5547 + release #482 | SOURCE |
| S16 | GetFavoritesByType is read-only inventory | FavoritesCommands.cpp tag1.5.9 blob a935ff41 | SOURCE |
| S17 | ApplyFavoritesToElementDefaults mutates defaults | same FavoritesCommands.cpp | SOURCE |
| S18 | Import/ExportFavorites .prefs exists | same FavoritesCommands.cpp | SOURCE |
| S19 | Missing direct default-property/classification API | Tapir upstream issue #944 OPEN 17–19.10.2026 | SOURCE |
| S20 | Zero-length wall crash in 1.5.3/AC26 | Tapir upstream issue #433 | SOURCE |
| S21 | Zero-length wall guard in tag1.5.6/1.5.9 | ExtendedElementCommands.cpp + PR #443 | SOURCE |
| S22 | CreateWalls structure/composite/profile and CreateBeams profiles | ExtendedElementCommands.cpp tag1.5.9 schemas | SOURCE |

**Первичные URL:** 
- https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
- https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/FavoritesCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/releases
- https://github.com/ENZYME-APD/tapir-archicad-automation/issues/433
- https://github.com/ENZYME-APD/tapir-archicad-automation/issues/944
- https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- https://help.graphisoft.com/AC/29/INT/GC.pdf

## 4. Два внутренних контрааудита

**A — Версии/источники.** Официальный upstream `1.5.9` source и release `1.5.6` доказывают поддержку PolyRoof в этих версиях, но **не** доказывают, что установленный на ноутбуке бинарник действительно upstream `1.5.10`. По запросу tag `1.5.10` и `v1.5.10` GitHub contents вернул «No commit found». Нельзя переносить весь нынешний online-docs schema на локальный APX. Вывод: `LOCAL_APX_PROVENANCE_BLOCKED`, не «обновить немедленно».

**B — Архитектура/приёмка.** Native `API_PolyRoofID` в Tapir устраняет только **capability blocker**. Доказательств, что authored PR74→SceneWriter маршрутизирует multi-plane payload, нет; прямой вызов Tapir в обход SceneWriter запрещён. GH Deconstruct не подтверждает Brep для multi-plane roof и не гарантирует watertight solid. Следовательно, нет права объявлять `G2 PASS`, `BUILD` или `ACCEPTED`.

## 5. Передача интегратору I4 — четыре адресных действия

1. **I4-R1-01 P0/100:** на G0 (только после разрешённого read-only подключения) запросить `GetAddOnVersion`, список реально зарегистрированных команд/schema и SHA локального APX. Сопоставить заявленную 1.5.10 с upstream tags. **ГОТОВО:** immutable manifest `build/command/schema/apxSha`; до этого `BLOCKED_RUNTIME`.
2. **I4-R1-02 P0/100:** на G1/G2 сравнить существующий PR74 roof typed contract с **двумя** payload `CreateRoofs`: без `pivotLine` и с `pivotLine`; строго без нового writer и без LIVE. **ГОТОВО:** точная матрица полей `SOURCE_SCHEMA/PR74_ACCEPTS/SCENEWRITER_PASSES/LOCAL_REGISTERED` с доказательствами, `NOT_FOUND` для неподдержанных полей.
3. **I4-R1-03 P0/95:** read-only инвентаризация `GetFavoritesByType`/атрибутов и библиотеки, зафиксировать, что `ApplyFavoritesToElementDefaults` и `ImportFavorites` являются writes. **ГОТОВО:** source manifest + точные missing defaults, без изменения PLN.
4. **I4-R1-04 P1/90:** для QA выбрать GH Deconstruct-Brep только на 8 документированных типах; для окон/дверей/PolyRoof — существующий Tapir/APA readback. **ГОТОВО:** readback plan по GUID/type/story/host/material/geometry с отдельным Save/Open; никакой ложной «3-way sync».

## 6. Статус на конец SOURCE-прохода

`SOURCE=22 предметные сверки; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0.`
`G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4=NOT_RUN; G5=NOT_RUN.`
`NOT_FOUND:` универсальная трёхсторонняя native sync, GUID-preserving arbitrary Rhino NURBS→native PolyRoof, атомарный rollback, автоматический доступ к полному default-property manifest в подтверждённом локальном API.
`MODEL_MODE_NOT_VERIFIABLE.`

**Примечание:** текущий аудит A5 нового цикла запланирован позднее исследовательской фазы; его новые задания ещё не могли быть прочитаны. Это не означает, что аудит отсутствует в принципе. Исторический PROJECT_PLAN rev182 не изменялся.
