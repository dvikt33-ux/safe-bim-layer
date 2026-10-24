# APA R1 — BUILD-01: G0 read-only инвентаризация и контракт нативного BIM
**Срез:** 24.10.2026, 14:58 UTC (17:58 МСК). **Роль:** R1 / нативные BIM-инструменты. **Цель:** [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка публикации:** `research/apa-extension-ranking-hub-20261018`.

**Классификация:** SOURCE — новые проверки исходников/документации; OFFLINE — новый прогон не выполнялся; BUILD — 0; INSTALLED — NOT_VERIFIED; LIVE — 0; ACCEPTED — 0. **MODEL_MODE_NOT_VERIFIABLE.** Никаких установок, PLN/APX, исходников, main, merge, LIVE, платных API, Work/Codex/Arena.

## 1. Полученное поручение A5
Прочитан [A5 14:39Z](audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md), blob `2b9079c78c226f4c01cb05b6957e993c6f4e0d12`. Поручение **R1-15A P0/98**: прекратить повторный каталог команд; дать таблицу `command → source → expected → runtime evidence → BLOCKED`, отдельно frozen Tapir 1.5.10 / upstream 1.5.9 / runtime UNKNOWN. G0 — только чтение; следующий производственный барьер — фактический G1 read-only preflight с Archicad, не «чистый offline».

## 2. Точное происхождение исходников
- PR74 immutable commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`. Файлы: `scripts/archicad_project_accelerator.py` blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`; `scripts/archicad_scene_run.py` blob `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`; `scripts/archicad_connected_components.py` blob `c5a99f59a90369ff622807574677cf11ca0a2225`.
- **Frozen schema находится в PR74 commit**, а не в проверенной исследовательской ветке: `schemas/tapir-live-1.5.10/tapir-scene-live.json`, blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`, 262 документированные команды. Прямое чтение этого пути из `research/apa-extension-ranking-hub-20261018` вернуло NOT_FOUND; из immutable PR74 — FOUND/SHA_MATCH. **Следствие:** G0/G1 должен указать реальный локальный checkout и путь к provenance-файлам, не подставлять относительный путь к исследовательской ветке.
- В `_metadata` frozen schema: `origin=live TapirCommand.GenerateDocumentation`, `provider_version=1.5.10`, историческая привязка `C:\\LocalAI\\SafeBIM_Global_Library_Test_Projects\\Тест MER .pln`, порт 19723, `storyIndex=0`, исходные SHA256 `command_definitions.js=bca5ee36484ad501b8cb3b2edaffd00a2a897363fb9ec35179ea2adcbbb6f604`, `common_schema_definitions.js=140f3ccc33f62cfb82429f03b9324622c084a5948f247edc8e230f52c076ee8d`. Это **архивный SOURCE-снимок**, а не свидетельство текущего APX/PLN/порта.
- `archicad_project_accelerator.py:31–38` — read-only allowlist `EvidenceAPI.READS`; `:438–447` authored требует preflight/execute + callable transport; `archicad_scene_run.py:25–90` — точные допустимые scratch-targets, `:140–168` — identity guard, `:707–746` — read-only preflight. Исторические прогоны не повышают G0/BUILD-01.

## 3. Матрица R1-15A: команды фактической инвентаризации G0
Все строки SOURCE из frozen schema PR74, если не сказано иное. `runtime evidence` — **требуемый будущий артефакт**, НЕ уже полученный.

| ID / команда и аргументы | SOURCE / ожидаемые поля | Требуемый runtime evidence | STOP / BLOCKED |
|---|---|---|---|
| G0-01 `API.GetProductInfo {}` | PR74 `archicad29()` требует `version=29`; фактический build 5101 сверять с локальным About/достоверным product manifest | product/version/build + timestamp + порт | Не 29, build неизвестен или не 5101 → `BLOCKED_PRODUCT` (не делать вывод о версии из названия файла) |
| G0-02 `GetProjectInfo {}` | `isUntitled,isTeamwork,projectPath,projectName`; frozen schema делает path/name условными, но `guarded_project` требует точные строки | project path/name, isUntitled=false, isTeamwork=false, file SHA256, active port | Любое расхождение exact target / незаписанный или Teamwork PLN → `WRONG_PROJECT` |
| G0-03 `GetStories {}` | `firstStory,lastStory,actStory,skipNullFloor,stories[]`; для каждой story нужны `index,floorId,level,name/uName` | полный список этажей и активный index; сопоставление `nativeIndex/floorId/level/label` | `STORY_MISMATCH` / `UNVERIFIED_NAMED_STORY`, нельзя угадывать ordinal/index или абсолютную Z |
| G0-04 `GetAddOnVersion {}` | `version` строго `1.5.10` по PR74 guard; версия не заменяет SHA бинарника | ответ API + локальный APX SHA256 и путь, список зарегистрированных команд/схем | `TAPIR_VERSION_MISMATCH`; нет APX SHA/schema → `BLOCKED_LOCAL_SCHEMA` |
| G0-05 `GetAttributesByType {attributeType:"BuildingMaterial"}` | `attributes[]`: `attributeId,index,name,modificationTime` **или error**; повторить для `Composite,Profile,Surface` при использовании | точные GUID/имена материалов и атрибутов по активному PLN, без изменения defaults | error, дубликат имени, отсутствующий GUID → `BLOCKED_ATTRIBUTE_BINDING` |
| G0-06 `GetBuildingMaterials {attributeIds:[...]}`, аналогично `GetComposites/GetProfiles/GetSurfaces` | Только **с ранее полученными attributeIds**; `fields` опционален; команды есть в `EvidenceAPI.READS` | характеристики выбранных существующих атрибутов, тип, GUID, запрошенные поля | несуществующий ID/неполные поля → `BLOCKED_ATTRIBUTE_DETAILS` |
| G0-07 `GetFavoritesByType {elementType:"Wall"/"Slab"/"Roof"/"Column"/"Beam"/"Window"/"Door"}` | Frozen command 1.2.2; `favorites[]` **или ErrorItem**. **НО команда отсутствует в `EvidenceAPI.READS` PR74** | отдельный read-only G0 список имен через существующий Tapir/интерфейс Archicad, с источником; НЕ считать это вызовом через G1 EvidenceAPI | `BLOCKED_EXISTING_READ_WHITELIST` для G1; отсутствие Favorite или ошибка → `BLOCKED_FAVORITE`; **не расширять router без отдельного решения** |
| G0-08 `GetAvailableLibraryParts {}` или `{filterByTypeId:...}` | Frozen command 1.5.0: `libraryParts[]` с `guid,index,documentName,fileName,typeId`, плюс **`skippedCount`** и `skippedSample` | перечень Window/Door library parts, точные имена/GUID и `skippedCount` | `skippedCount>0` = PARTIAL, отсутствие нужной части → `BLOCKED_LIBRARY_PART` |
| G0-09 `GetAllElements {}` / `Get3DBoundingBoxes` / `GetModelDumpV1` | существующий PR74 `READS`; проверка свободного объёма и независимых GUID/тел до записи | baseline GUID inventory, BREP/bbox coverage, collision envelope | неполная инвентаризация/пересечение → `BLOCKED_SPATIAL_PREFLIGHT` |
| G0-10 `GetDetailsOfElements {elements:[...]}` и `GetGDLParametersOfElements {elements:[...]}` | возвращают сведения **у размещённых элементов**; не заменяют чтение настроек Favorite/инструмента по умолчанию | отдельный typed/host/story/material/libPart readback на уже существующих допустимых элементах | нет GUID/типов/параметров → `BLOCKED_NATIVE_READBACK` |

**Новая проверенная несовместимость маршрутов:** `GetFavoritesByType` документирован в frozen Tapir, но не допущен текущим `EvidenceAPI.READS`. Не объявлять, что G1 автоматически инвентаризирует Favorites. Не добавлять новую команду в router в исследовательском цикле; I4 может использовать существующий read-only Tapir/UI G0 вне контура native write, либо оставить доказательство `BLOCKED`. `GetGDLParametersOfElements` не читает defaults.

**Ограничение provenance:** `GenerateDocumentation` пишет файлы на машине Archicad, поэтому его не запускали в этом read-only исследовании. Схема frozen — не живое подтверждение локального 1.5.10. Отсутствие schema в research branch — не отсутствие её в PR74.

## 4. Native BIM G2: точная граница семи команд
| Команда | Frozen schema required на элемент | Обязательное усиление PR74 / приёмка | Статус |
|---|---|---|---|
| `CreateWalls` | `begCoordinate,endCoordinate,height,thickness` | story floorIndex, локальный zCoordinate, Basic/material, ненулевая длина; `GetDetailsOfElements` проверяет координаты, тип, этаж, материал | SOURCE / LOCAL UNKNOWN |
| `CreateSlabs` | `level,polygonCoordinates` | absolute Z, thickness, material; Basic может потребовать `CreateSlabs→readback→ModifySlabs`; hole-loop не проверен | SOURCE_PARTIAL / LOCAL UNKNOWN |
| `CreateColumns` | `coordinates` | `height,width,depth,floorIndex` и при наличии material/profile GUID; G1 `nativeComponents` разрешает | SOURCE_PARTIAL / LOCAL UNKNOWN |
| `CreateBeams` | `begCoordinate,endCoordinate,zCoordinate` | optional typed adapter; `nativeComponents` authored allowlist **не включает `CreateBeams`**; не объявлять базовым G1 без доказанного существующего пути | SOURCE_PARTIAL / NOT_IN_AUTHORED_ALLOWLIST |
| `CreateRoofs` | `level,polygonCoordinates` | PR74 требует `pivotLine,structureType=Basic,buildingMaterialId,floorIndex`; `ConnectedComponent.verify` требует `roofClass=SinglePlane`; PolyRoof не G1 | SOURCE_PARTIAL / LOCAL UNKNOWN |
| `CreateWindows` | `ownerWallId,centerOffset` | `$createdGuid` родительской Wall, `width,height,sillHeight`; frozen `libraryPartName` optional, upstream 1.5.9 без этого поля по R1 13:55Z; проверка `libPart/marker` после Create отсутствует в базовом hosted readback | SOURCE_SCHEMA_DRIFT / LOCAL UNKNOWN |
| `CreateDoors` | `ownerWallId,centerOffset` | те же host/size/favorite/library риски; в исходном `verify_readback` проверяются host и размеры, не family/marker | SOURCE_SCHEMA_DRIFT / LOCAL UNKNOWN |

**Критическая граница:** `archicad_project_accelerator.py:265–275` допускает в authored intent только ограниченный набор верхних полей, а `:292–296` в `nativeComponents` только `CreateColumns/CreateDoors/CreateWindows/CreateWalls/CreateRoofs`. `CreateSlabs` формируются штатным authored candidate. `CreateBeams` не включать как обязательное условие BUILD-01 G1.

**Favorite ≠ библиотечная часть ≠ параметры marker.** `GetFavoritesByType` возвращает имена, не полный снимок параметров. Указание `favoriteName` само по себе не доказывает установленную GDL-семью или маркер. Отдельный readback после разрешённого G3 обязателен. Нельзя использовать `ApplyFavoritesToElementDefaults`, `CreateFavoritesFromElements`, `ImportFavorites` в G0 — это мутации. У upstream Tapir [issue #944](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/944), открытая 17.10.2026, отдельно обсуждаются API свойств/классификаций **defaults**; это предложение функции, а не доказательство её наличия в локальной 1.5.10.

## 5. Первоисточники, совместимость, лицензии — CA-R1-15A
1. [Graphisoft Rhino–Grasshopper–Archicad Toolset](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/): **Grasshopper–Archicad 29 Live Connection build 3000**, Windows, Rhino 7/8, дата 01.10.2025; несовместим с Start Edition. Наличие AC30 build3000 в текущем каталоге **не заменяет AC29**. Локальная установка/совместимость именно с AC29 build5101 не проверена.
2. [Tapir upstream](https://github.com/ENZYME-APD/tapir-archicad-automation): исходники MIT; Add-On готов, Grasshopper Plugin — work in progress. Лицензия исходников не доказывает наличие нужного установленного бинарника; не устанавливать.
3. [Tapir #399](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/399): документирован частный отказ Windows/Doors в AC29 JPN build4006; **не экстраполировать** на build5101/локализацию пользователя. [Tapir #551](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/551): историческая проблема маркеров; исправление upstream не равно локальному PASS.
4. Rhino 8 и Archicad требуют собственных действующих лицензий; бесплатность исследуемого open-source кода не означает бесплатность этих хост-приложений. Никаких платных API не требуется для описанного G0.

**Вердикт CA-R1-15A:** `SOURCE_VERIFIED / FROZEN_SCHEMA_VERIFIED / LOCAL_APX_AND_LICENSE_NOT_VERIFIED`.

## 6. Контрааудит воспроизводимости — CA-R1-15B
- `RUN.EXPECTED_PATH` по умолчанию исторический `Тест MER .pln`, `PORT=19723`; CLI PR74 поддерживает **только** `--scratch-port` для `C:\\LocalAI\\APA_Test_House_01.pln` и `--isolated-port` для `C:\\LocalAI\\APA_Isolated_Writer_Test_01.pln`. Произвольный новый PLN нельзя назначить CLI-флагом. Требуются фактические разрешённые path/port/active story; без этого G0 BLOCKED. Исторический файл не запускать.
- `--preflight` authored не является offline: нужен Archicad read-only transport. `--output` обязан указывать **несуществующий** каталог; `EvidenceAPI` при `execute=False` запрещает native mutations. G1 не проводился.
- Native Wall/Window/Door GUID появляются только после CREATE; G1 может подготовить `$createdGuid` dependency, но **не фактический GUID**. На UNKNOWN после CREATE не повторять CREATE; SQLite не откатывает PLN.
- `GetFavoritesByType` whitelist gap, неполный library inventory (`skippedCount`), `libraryPartName` schema drift и отсутствие hosted libPart/marker verification — **разные** блокеры. Нельзя закрывать их одним сообщением «Tapir работает».
- Для нативной приёмки нужны тип, этаж, host GUID, размеры, материал, библиотека/маркер (для openings), BREP, затем Save/Close/Reopen. Rhino BREP/Grasshopper preview не равны Archicad native acceptance.

**Вердикт CA-R1-15B:** `ONE_SCENE_WRITER_PRESERVED / G0_RUNTIME_BLOCKED / G1_NOT_RUN`.

## 7. Передача I4 — ровно закрывающие действия
| ID / приоритет | Что сделать без второго writer/router | ГОТОВО |
|---|---|---|
| R1-I4-01 / P0 | На ноутбуке собрать G0 read-only manifest: actual Archicad 29 build/port/project/PLN SHA, GetStories, GetAddOnVersion, APX SHA, local checkout commit, schema provenance | Файл с конкретными значениями либо одним точным BLOCKED reason; не SOURCE как INSTALLED |
| R1-I4-02 / P0 | Проверить Favorites отдельным существующим read-only способом; **не** вызывать `GetFavoritesByType` через EvidenceAPI, где команды нет в READS | Имена Favorites и источник, либо `BLOCKED_EXISTING_READ_WHITELIST` |
| R1-I4-03 / P0 | `GetAvailableLibraryParts`: Window/Door names+GUID и `skippedCount`; отдельно материалы `GetAttributesByType` и floorId/elevation | 0 ошибок/пропусков для нужных библиотек и GUID либо BLOCKED |
| R1-I4-04 / P0 | Сравнить локально зарегистрированные CreateWindows/CreateDoors fields с frozen 1.5.10 и upstream; не угадывать `libraryPartName` | Таблица local/frozen/upstream + точный `SCHEMA_MATCH` или `SCHEMA_DRIFT` |
| R1-I4-05 / P0 | Подготовить новый authored G1 с Wall/Slab/SinglePlane Roof/Window/Door и при возможности Column, но **без Beam в nativeComponents**; использовать только предустановленные approved scratch targets | schema-compatible intent + G1 read-only receipt после G0, native writes=0, inventory before=after |

**A5:** признать R1-15A выполненным **на уровне SOURCE и подготовленного G0-листа**, не G0 runtime; при отсутствии ноутбука `STALLED_EXTERNAL_DEPENDENCY`. Новых функций и writer не разрабатывать. Следующая полезная проверка — не новая подборка плагинов, а получение фактического G0 manifest.

## 8. Итог и реестр доказательств
**SOURCE:** A5 blob, immutable PR74 compiler/SceneWriter/connected-components, frozen 262-command Tapir schema, официальный Graphisoft, upstream Tapir и три upstream issues; число «проверок» не используется как метрика готовности. **OFFLINE:** 0 новых прогонов. **BUILD:** 0. **INSTALLED:** NOT_VERIFIED. **LIVE:** 0. **ACCEPTED:** 0. **NOT_FOUND (ограниченно):** frozen schema по пути research branch, `GetFavoritesByType` в PR74 EvidenceAPI.READS, `CreateBeams` в authored nativeComponents allowlist, локальный runtime manifest. **G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.**
