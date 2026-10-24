# APA AC29 — исследователь №2 — 2026-10-19 13Z: готовые способы подключения, новый релиз Tapir 1.7.2

**Режим:** SOURCE ONLY. 30 адресных технических source-inspection, 2 собственных контрааудита. Никаких установок, API-вызовов к живому AC29, PLN/APX, правок рабочего кода, main, слияний PR или изменений очереди/плана. `MODEL_MODE_NOT_VERIFIABLE`.

## 0. Исходные материалы и актуальность

Прочитаны ПЕРВЫМИ: [очередь №3](../NEXT_RESEARCH_PRIORITIES.md) blob `2cb49edc410632c65503d8f17e93c58bc2d971d1` (последняя 2026-10-18 20Z), [матрица 61](../priority_matrix_20261018.json) blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`, [реестр 61](../candidates.json) blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`, [поручения №2 A](audit-2026-10-18-20-tasks-2A.md)/[B](audit-2026-10-18-20-tasks-2B.md). №1: последние [09Z source checks](research-1-20261019T09Z-checks.md); основной 09Z отсутствует; последний полный [07Z](research-1-20261019T07Z.md); заявленные 07Z-cards.md отсутствуют при точном fetch. №2 предыдущий [12Z](research-2-integration-2026-10-19T12Z.md). №3 свежее 20Z не найдено. Канон `PROJECT_PLAN.json` [revision 182](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json) blob `c2ab2f9d606db1412c4031076103c267fc463f83` прочитан только для сверки.

**СУЩЕСТВЕННО НОВОЕ ПОСЛЕ 12Z:** официальный релиз [Tapir 1.7.2](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2) опубликован **2026-10-19 11:49:43 UTC**. Содержит готовый `TapirAddOn_AC29_Win.apx` (5 914 112 байт, GitHub asset SHA256 `4714fcbfadb47307b0b3cecf578fe18ff326f3c06ee0b8e7db5a31a979a01bf7`), а также команды нативных осей, количеств, 3D-геометрии и исправления ошибок. **Никакой замены локального Tapir «1.5.10» не выполнялось и не разрешено; версия и SHA установленного APX неизвестны.** Публичного релиза 1.5.10 среди последних 20 тегов не найдено; это не опровергает локальную сборку. В релизе есть AC30-only изменения — НЕ считать их доказательством AC29.

### Пинованные первоисточники и существующий APA

- **T0** [Tapir 1.7.2 release / assets / SHA / unsigned installer](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2), [MIT license at tag](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/LICENSE).
- **T1** [PR879 GridElements, C++/JSON/пример, merged 2026-10-16](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/879).
- **T2** [PR860 GetQuantitiesOfElements](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/860).
- **T3** [PR865 Get3DGeometryOfElements](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865).
- **T4** [PR776 обязательный parentNavigatorItemId](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/776).
- **T5** [PR861 Move/Rotate per-element failure](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/861).
- **T6** [PR851 RenameNavigatorItem readback](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/851).
- **T7** [PR882 ошибки регистрации команд](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/882).
- **T8** [PR835 SaveCurrentWindowAsImage](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/835).
- **G29** [официальный Graphisoft AC29 b3000commands/b3000types](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html), [SDK29 29.3000](https://github.com/GRAPHISOFT/archicad-api-devkit/releases/tag/29.3000), [Graphisoft license](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/LICENSE).
- **I4** [IfcOpenShell 0.8.5 util.sequence.py](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py), **I5** [util.cost.py](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py), **IM** [util.system.py](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py).
- **APA V2** [PR165 исходник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5c0dc009e729db9834301b4a369512490a205ef7/scripts/apa_high_density_readonly_v2.py#L170-L190): перечисляет все `IfcRelConnectsPorts`, выдаёт `nativeMEPConnectionVerified:false`. **APA C1** [PR168 исходник](https://github.com/dvikt33-ux/safe-bim-layer/blob/7589c5dcee1fb71edae64e1d3bc9b1de14693e8e/scripts/apa_dxf_geometry_c1.py): `ezdxf==1.4.5`, `recursive_decompose`, SHA и предел 50 000. PR154/160 PDF и PR164 SceneWriter, PR171/173 Hotlink — существующие; не повторять живые действия.

## 1. 30 фактических проверок (вопрос → первоисточник → точный контракт → адаптер/блокер → вердикт → следующая проверка)

01. **Есть ли готовый AC29 APX?** T0 release assets: `TapirAddOn_AC29_Win.apx` 5 914 112 байт, SHA256 выше. Не подменять AC30 бинарником. **SOURCE_CONFIRMED / DEFER install**; далее локальный SHA и подпись файла.
02. **Релиз опубликован когда?** T0 `published_at=2026-10-19T11:49:43Z`, тег `1.7.2`; 1.5.10 публично не найден. **VERSION_GAP / DEFER**; далее provenance локального APX.
03. **Лицензия всей цепочки?** T0 `LICENSE` — MIT для Tapir; G29 SDK — Graphisoft Software License Agreement, не MIT; лицензия Archicad отдельно. **LEGAL_SPLIT / ADAPTER**; далее условия SDK/распространения, без перепаковки.
04. **Можно ли слепо запускать installer?** T0: Windows installer `not code signed`; есть отдельный готовый AC29 APX. **REJECT automatic installer**; далее только будущий контролируемый backup/hash/rollback.
05. **Готовое чтение дефолтов осей?** T1 `GetGridElementDefaults` (зарегистрирован как 1.7.2), результат library part, размеры, GDL parameters. **ADAPTER через текущий Router/Tapir**; далее runtime `IsAddOnCommandAvailable`, read-only.
06. **Готовое перечисление нативных осей?** T1 `GetGridElements` возвращает `gridElements[]`: `elementId,variation,floorIndex,layerIndex,pos,angle,length,xRatio,yRatio,useXYFixSize,level,libInd,libraryPartName`; `includeParameters:boolean` default false. **REUSE BIM Graph**; далее GUID/type/count против native dump.
07. **Готовое массовое создание осей?** T1 `CreateGridElements` принимает `gridElements:[{begCoordinate:{x,y},endCoordinate:{x,y},...}]`, ответ `elements` + `warnings`; нужен AC26+. **ADAPTER будущий, LIVE запрещён**; далее OFFLINE schema 2×2.
08. **Точный способ задания длины оси?** T1 `lengthMode: "length"|"none"`; `length` пишет GDL `AC_Length`, если нет — A/xRatio; `none` оставляет параметры. Длина в метрах, угол в радианах. **ADAPTER unit/parameter gate**; далее две разные grid library parts.
09. **Как отличить частичное создание осей?** T1 возвращает поэлементные `elements` и `warnings[]` с индексом параметра; успешный общий вызов не равен отсутствию warnings. **FAIL_CLOSED**; далее count input=output и zero-warning fixture.
10. **Можно ли использовать сетку на AC29?** T1 C++ description: `Needs Archicad 26 or later`; релиз T0 содержит AC29 APX. Это **source-compatible range**, не проверка AC29 build 5101. **DEFER runtime**; далее OFFLINE→INSTALLED gate.
11. **Есть ли нативные количества?** T2 `GetQuantitiesOfElements({elements:[ElementId],minOpeningSize?:number})` возвращает `quantitiesOfElements[]` по типам, с поэлементными errors. **ADAPTER в существующий Router/BIM Graph**, без нового QTO-движка; далее fixture 1 wall/1 slab.
12. **Какие элементы покрывает QTO?** T2 register description: Wall, Column, Beam, Slab, Roof, Shell, Morph, Zone, ColumnSegment, BeamSegment. Прочие типы — `NOT_SUPPORTED`. **REUSE**; далее type coverage inventory.
13. **Что означает `minOpeningSize`?** T2 input `minOpeningSize` >=0, пример 0.5; влияет на conditional quantities. Без фиксации порога сравнения объёмов недостоверны. **ADAPTER metadata threshold**; далее 0/0.5 fixture.
14. **Можно ли получать послойный объём?** T2 `composites[]`: buildingMaterialId GUID, volume, projectedArea, core/finish; для базового элемента одна запись. **REUSE native quantities**, не смешивать с IFC QTO без сопоставления GUID; далее skin sum vs element total.
15. **Есть ли готовая 3D геометрия?** T3 `Get3DGeometryOfElements({elements:[...]})` → `geometries3D[]`, `bodies[]` с `vertices` и `polygons` (loops/holes/surfaceId). **ADAPTER для независимого QA, не второй SceneWriter**; далее compare bbox vs native dump.
16. **Координаты и вложенные компоненты?** T3 C++ register description: vertices in world coordinates; включает subelements Stair/Railing/CurtainWall; массив результатов соответствует входу. **ADAPTER origin+GUID**; далее hole/mirror/compound fixture.
17. **Подтверждена ли BUILD-приёмка T3?** T3 PR body прямо сообщает `unbuilt and untested` при открытии; наличие merged PR и release APX не доказывает AC29 5101 runtime/geometry correctness. **DEFER high-risk**; далее CI/release trace + независимый test.
18. **Что с масштабом памяти геометрии?** T3 register: 3D модель генерируется по необходимости, много элементов может быть долго; 48 GB RAM/8 GB VRAM не измерены. **ADAPTER bounded batches**, VRAM не заявлять обязательной; далее max element/bytes/time budget.
19. **Безопасно ли клонировать вид в корень?** T4 PR776: Tapir ранее fallback на View Map root мог создавать вид, который нельзя удалить/переместить даже UI; исправление делает `parentNavigatorItemId` обязательным. **REJECT root fallback**; далее проверить папку до клона.
20. **Какой официальный альтернативный путь?** G29 `CreateViewMapFolder(FolderParameters(name), parent?,previous?) -> NavigatorItemId`, затем `CloneProjectMapItemToViewMap(projectMapNavigatorItemId,parentNavigatorItemId)->NavigatorItemId`. **REUSE official API first**; далее readback дерева и parent GUID.
21. **Готова ли безопасная переименовка?** T6 PR851: `RenameNavigatorItem` для Project Map schedule мог вернуть success без изменения; исправление делает readback и failure. **ADAPTER verify actual name**; далее view/schedule negative cases.
22. **Есть ли ложный PASS в Move/Rotate?** T5 PR861: `ACAPI_Element_Edit` мог вернуть NoError на hidden/locked, не сдвинув элемент; исправление — поэлементная проверка. **DEFER writes**, будущий GUID+coordinate readback обязателен; далее offline refusal.
23. **Как проверить регистрацию новой команды?** T7 PR882: `RegisterCommand` пишет в Archicad report `Tapir: the <name> command could not be registered (error <code>)`. **ADAPTER capability gate**, не полагаться только на список документации; далее `IsAddOnCommandAvailable` и журнал.
24. **Готовый снимок окна?** T8 `SaveCurrentWindowAsImage({imageFilePath,format?,colorDepth?,entireDrawing?})`, PNG/JPG/BMP/TIFF/GIF, для 2D возвращает zoom/rotation; запись на диск. **DEFER until explicit output permission**; далее allowlisted path+SHA, не принимать за CAD-чертёж.
25. **Штатное создание листа без Tapir?** G29 `CreateLayout(layoutName,layoutParameters,masterNavigatorItemId,parentNavigatorItemId)->NavigatorItemId`; новый APX не нужен. **REUSE official JSON**; далее master/subset GUID, negative duplicate ID.
26. **Единицы и ревизии листа?** G29 `LayoutParameters.horizontalSize/verticalSize` в **мм**, `hasIssuedRevision/hasActualRevision` boolean; эти флаги не доказывают PDF на диске. **ADAPTER mm→m only at BIM boundary**; далее layout readback + publisher file SHA.
27. **Можно ли проверить структуру атрибутов?** G29 `GetAttributeFolderStructure(attributeType,path?:string[])`, `GetAttributeFolders(ids)`, `GetAttributesIndices(ids)`. **REUSE read-only**, без `DeleteAttributeFolders` (удаляет вложенные удаляемые атрибуты); далее GUID + path readback.
28. **Достаточно ли LayerCombination для видимости?** G29 `LayerCombinationAttribute` содержит `attributeId,name,layerAttributeIds`; `LayerAttribute` содержит `isHidden,isLocked,isWireframe`, но это не полная матрица состояния каждого слоя в комбинации. **NOT_FOUND для полного per-combination state через данный контракт**; минимальный адаптер — проверенный API29/Tapir endpoint чтения состояний конкретной комбинации; далее поиск SDK29 read-only sample.
29. **Безопасно ли читать IFC 4D расписания?** I4 `get_task_work_schedule` строки 272–280 рекурсивно вызывает parent, а затем `get_task_work_schedule(task)`; `get_all_nested_tasks` строки 290+ рекурсивен без visited. **ADAPTER только bounded/visited traversal в существующий B1 JSON**, без нового scheduler; далее parent cycle/3 tasks.
30. **Безопасно ли читать IFC 5D стоимость?** I5 `calculate_applied_value` строки 63+ подавляет `ZeroDivisionError` при DIVIDE; `get_cost_rate` строки 337+ разыменовывает `get_cost_schedule(...).PredefinedType` без null-guard. **ADAPTER fail-closed `DIV_ZERO`/`MISSING_COST_SCHEDULE` + currency/unit evidence**, без `assign_cost_value`; далее zero/missing/valid fixtures.

## 2. Матрица 10 конкретных способов подключения

**Шкала:** польза 0–100 экспертная (НЕ ускорение), сложность БЫСТРО/АДАПТАЦИЯ/ДОЛГО; доказанность SOURCE, risk низкий/средний/высокий. Все цепочки используют существующий APA Router/Bridge; максимум один внешний готовый Add-On либо библиотека, новый конкурентный исполнитель запрещён.

| Готовый инструмент → способ подключения | Версия/контракт, reuse APA | Выбор, польза, сложность, риск | ГОТОВО (будущий gate) |
|---|---|---|---|
| **Нативные оси Grid** T1 → Tapir command | 1.7.2 AC29 asset; `GetGridElementDefaults/GetGridElements/CreateGridElements`; Router→Tapir→BIM Graph/SceneWriter | **ADAPTER 97**, АДАПТАЦИЯ, высокий (локально 1.5.10) | 2×2 нативные оси, GUID, длины, предупреждения=0, сохранение/readback |
| **Native QTO** T2 → Tapir read-only | 1.7.2; `elements,minOpeningSize`; Router→Tapir→существующий QA | **ADAPTER 96**, АДАПТАЦИЯ, средний | wall/slab/skins/threshold, native GUID, без IFC смешения |
| **3D geometry** T3 → Tapir read-only | 1.7.2; `geometries3D,bodies,vertices,polygons`; Router→Tapir→BIM Graph | **DEFER 83**, ДОЛГО, высокий (PR unbuilt claim) | проверенная сборка+AC29 5101, bounds/holes/surface, лимиты памяти |
| **Clone ViewMap** T4/G29 → официальный JSON API | AC29 b3000; `CreateViewMapFolder`→`CloneProjectMapItemToViewMap`; Router→official JSON | **REUSE 98**, БЫСТРО после допуска, высокий при root fallback | parent GUID не root; новый view GUID, дерево readback, нет orphan |
| **Layout/revisions** G29 → официальный JSON API | AC29; `CreateLayout/GetLayoutSettings`, мм, revision flags; Router→JSON→BIM Graph | **REUSE 93**, АДАПТАЦИЯ, средний | master+subset GUID, размеры мм, revision readback, PDF SHA отдельно |
| **Атрибуты и слои** G29 → JSON read-only | AC29; `GetAttributeFolderStructure/GetLayerCombinationAttributes/GetLayerAttributes` | **REUSE 90**, БЫСТРО, средний | tree/attribute GUID; per-combination hidden state = UNKNOWN |
| **Безопасные Move/Rotate** T5 → Tapir с readback | 1.7.2 fixes; Router→Tapir→SceneWriter receipt | **DEFER 94**, АДАПТАЦИЯ, высокий (модельная запись) | hidden/locked failure; coords unchanged; permitted success GUID readback |
| **Снимок текущего окна** T8 → Tapir file output | 1.7.2; `SaveCurrentWindowAsImage`, path allowlist | **DEFER 79**, АДАПТАЦИЯ, средний | PNG file SHA + view transform, не BIM геометрия |
| **IFC 4D read-only** I4 → существующий B1/V2 | IfcOpenShell 0.8.5 LGPL-3.0+; Router→B1→`util.sequence` bounded | **ADAPTER 93**, БЫСТРО, средний | 3-task/parent-cycle, нет бесконечной рекурсии, no schedule writes |
| **IFC 5D read-only** I5 → существующий B1/V2 | IfcOpenShell 0.8.5 LGPL-3.0+; Router→B1→`util.cost` guarded | **ADAPTER 92**, БЫСТРО, высокий | zero/missing/unit/currency fixtures, no false PASS |

**Дублирование:** AC29 native QTO ≠ IFC экспорт QTO; обе стороны сохранять с происхождением и сверять, не выдавать одно за другое. Grid Tool нативные оси ≠ DXF MINSERT ≠ Hotlink; не строить новую систему осей. 3D geometry — диагностическое чтение, не альтернативный SceneWriter. Новые команды 1.7.2 не становятся INSTALLED от наличия публичного APX.

## 3. Сравнение архитектурных альтернатив

**A. Оси:** (A1) новый SDK29 APX для Grid — высокий ABI/сборочный риск и дублирование; (A2) готовый Tapir 1.7.2 `CreateGridElements` через существующий Router — минимум внешних звеньев, но нужен отдельный разрешённый upgrade gate; (A3) линии/объекты как имитация осей — потеря нативной семантики. **Выбор A2 после проверки локальной версии/AC29 5101, пока SOURCE/DEFER.** Для только чтения без обновления использовать существующий native dump/JSON, где покрытие доказано; не подменять им Grid API.

**B. Листы/виды:** (B1) официальный AC29 JSON `CreateViewMapFolder`→`CloneProjectMapItemToViewMap`→`GetNavigatorItemTree` — меньше звеньев, не нужен APX; (B2) Tapir clone с обязательным parent (PR776) — fallback при необходимости специфичных свойств, требует runtime проверки. **Выбор B1**. Запрет root fallback обязателен в обоих путях.

**C. 4D/5D:** (C1) существующий B1/V2+пинованный IfcOpenShell `util.sequence/cost` с fail-closed guard — reuse; (C2) новый scheduler/cost engine — отклонён, лишние зависимости и несоответствие существующему Router. **Выбор C1**. Полная проверка СП, валют, ставок, нагрузок не заявляется.

**NOT_FOUND:** публичный готовый механизм, который без обновления установленного Tapir «1.5.10» гарантированно создаёт *нативные* GridElements в AC29 через существующий Router, не подтверждён. Минимально недостаёт доказанной доступности `CreateGridElements` в конкретном локальном APX либо утверждённого безопасного обновления до проверенного AC29 asset 1.7.2. Это НЕ приглашение писать новый Grid engine. Полная матрица состояний слоёв внутри комбинации через `LayerCombinationAttribute` также NOT_FOUND.

## 4. Независимый контрааудит А — версии, код, лицензии, доказательность

1. GitHub release API T0 подтверждает **дату, AC29 asset, размер и digest**, но не runtime, AC29 build 5101 ABI или точность геометрии. Наличие AC30-specific PR в release — исключить из AC29 выводов. 
2. Тег 1.7.2 — новый относительно локальной метки 1.5.10; `IsAddOnCommandAvailable` и локальный APX SHA **НЕ ВЫПОЛНЕНЫ**. Ни один новый Tapir метод не объявлен INSTALLED.
3. T1 C++ регистрация Grid commands имеет версию `1.7.2`, `Needs Archicad 26 or later`; T2/T3 тоже `1.7.2`. Нельзя переносить их на 1.5.9/«1.5.10».
4. T3 PR body говорит об отсутствии build/review на этапе открытия; release asset не является независимой AC29 5101 приёмкой. Это ограничение сохранено.
5. Tapir MIT, Graphisoft SDK proprietary, IfcOpenShell LGPL-3+ — три разные лицензии. Никакого права распространять SDK из MIT не следует. Установки/загрузки бинарника не было.
6. G29 — версия AC29 b3000; документированная команда не подтверждает успешное выполнение в build 5101. Размеры LayoutParameters **мм**, длины обычных property **м**; никакого автоматического unit inference.
7. Сверка APA V2: уже есть `IfcRelConnectsPorts` и статус `nativeMEPConnectionVerified:false`; не объявлять новый MEP движок. Канонический revision182 не изменён.

## 5. Независимый контрааудит Б — монтажный граф, дублирование, безопасность

1. Все цепочки Router→официальный JSON или Router→уже установленный/позже разрешённый Tapir→BIM Graph/SceneWriter, либо Router→B1/V2→IfcOpenShell. **Ни одного второго оркестратора/writer.**
2. Главные ложные PASS: root clone orphan (T4), Move/Rotate NoError без фактического изменения (T5), Rename success без изменения (T6), частичные Grid warnings (T1), Cost divide-by-zero silent (I5), 3D геометрия без independent runtime (T3). Каждый закрывается fail-closed и readback, а не успехом HTTP.
3. Пакетные Grid operations требуют отдельного учёта GUID каждой оси, ошибок каждого элемента, единиц м/рад, библиотечного GDL `AC_Length`, layerIndex и floorIndex. Никакого обещания 100× без одинаковой базы измерений.
4. Никаких destructive calls `DeleteAttributeFolders`, `DeleteNavigatorItems`, `MoveElements`, `CreateGridElements`, `CreateLayout` сейчас. Даже «read-only» геометрия T3 может нагружать память; 48 GB RAM и 8 GB VRAM не измерены.
5. Публикация файлов/скриншотов требует allowlisted path, существования файла, SHA256, версии источника, rollback. `hasIssuedRevision=true` ≠ опубликованный PDF.
6. PR173 scratch saved/reopened не считать независимым ACCEPTED; PR164 STOPPED/LIVE_UNSAVED не воспроизводить. Очередь №3 20Z по PR173 устарела относительно более позднего receipt, но этот отчёт очередь не редактирует.

## 6. Воспроизводимый будущий план подключения (НЕ выполнять сейчас)

- **SOURCE:** этот отчёт, SHA/PR/схемы, сравнительная матрица; версия локального Tapir не верифицирована.
- **OFFLINE:** без Archicad проверить JSON-схемы Grid/QTO/3D, 2×2 оси, units, warnings/errors, orphan-parent denial, 4D cycles и 5D zero/missing. Зафиксировать pinned assets/hashes, backup/rollback plan.
- **BUILD:** только если потребуется адаптер; сборка/статический аудит в отдельной ветке после утверждения №3, JUnit; для готового APX вместо выдуманного build — независимая проверка опубликованного build/CI и SHA.
- **INSTALLED:** только после отдельного разрешения; backup исходного APX, SHA до/после, AC29 build 5101 `GetProductInfo`, `IsAddOnCommandAvailable`, log registration; при несовместимости возврат оригинала.
- **LIVE:** только с отдельным разрешением, scratch PLN, native GUID+параметры+Save/Open readback, никаких production моделей и массового клонирования без предварительного gate.
- **ACCEPTED:** независимая проверка координатором №3 по артефактам, правильным версиям, единицам, журналу и воспроизводимым тестам; без измерений нет claim speedup.

## 7. Адресные вопросы №1 и передача координатору №3

**№1 (6 вопросов):** (1) существует ли документированный runtime способ прочитать регистрацию `CreateGridElements` на локальном Tapir 1.5.10 без запуска мутации; (2) имеются ли официальные AC29 SDK29 samples для GridElements без своего APX; (3) проверить T3 AC29 5101 build evidence/CI и реальные geometry fixtures; (4) уточнить `GetQuantitiesOfElements` единицы и conditional opening threshold по C++ schemas; (5) есть ли готовый read-only API per-layer visibility именно *в комбинации*, не текущие LayerAttribute flags; (6) имеются ли готовые rollback/side-by-side APX migration guides для AC29 1.5.x→1.7.2.

**№3 на утверждение будущих исследований/проверок (7):** G01 Grid native 1.7.2 read+create capability gate; G02 native QTO 1.7.2 vs IFC QTO provenance; G03 3D geometry 1.7.2 build/ABI/limits; G04 official AC29 ViewMap clone root-orphan prevention; G05 Layout/revisions mm and Publisher SHA; G06 IFC4D visited/recursion guard; G07 IFC5D division/missing schedule fail-closed. Приоритет первых безопасных OFFLINE: G04/G06/G07; G01/G02/G03 требуют особого version gate.

**Статус:** SOURCE 30 проверок / 2 контрааудита. OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO. `MODEL_MODE_NOT_VERIFIABLE`.
