# APA R1 — BUILD-01: G0 runtime decision gates и четыре STOP-контракта (16Z)

**Срез:** 24.10.2026, 16Z / 19:00 МСК. **Роль:** R1, нативный BIM. **Цель:** [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Режим:** SOURCE_ONLY; ноутбук/Archicad/Rhino не подключались; `MODEL_MODE_NOT_VERIFIABLE`.

## 1. Поручение A5 и правило приёмки

Прочитан последний доступный [A5 15:43Z](audit-a5-20261024T1543Z-BUILD01-G0G1-STRICT-COUNTERAUDIT.md), Git blob `af0ab17e54b556001a47572a5d858e8c9eda76a8`. Выполняются **R1-16A P0/98** (один применимый шаблон G0, не новый каталог API) и **R1-16B** (Window/Door/Slab/Roof: local/frozen/upstream и точные STOP). Предыдущий [R1 14:58Z](research-1-20261024T1458Z-BUILD01-G0-READONLY-INVENTORY.md), blob `5c036f238ae65afd3a0f338eb98d0884aaad7805`, является исходной таблицей; здесь добавлены **машинно-проверяемые правила решений** и обнаруженный барьер этажности.

**Главная новая проверка исходника:** `scripts/archicad_semantic_brief.py` (PR74 immutable `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, blob `e431016f796bb8052487478dde3b2ed2752e7c00`) прямо указывает: `GENERATE_FROM_ZERO` **описывает требуемые этажи, но не создаёт PLN или этажи Archicad**. Следовательно, G0 должен обнаружить уже существующие **две соответствующие native stories** в утверждённой scratch PLN; название режима не является командой создания этажей. В `archicad_scene_run.py` (blob `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`) `guarded_project` дополнительно требует `actStory == nativeIndex`, точные `floorId/level` и при заданной привязке точное имя. Без этого G1 STOP.

## 2. R1-16A: единый G0 manifest — поля, реальные команды, STOP

Все значения `observed` должны поступить с ноутбука **после разрешённого чтения**, а не из документации. `NOT_OBSERVED` не превращать в `PASS`. Фиксировать timestamp, порт, полный ответ команды/GUI evidence, SHA256 локального файла (когда применимо), путь и локальный git commit.

| ID | SOURCE: существующий способ / фактическое поле | Evidence в `G0-manifest` | Строгий STOP |
|---|---|---|---|
| G0-PRODUCT | `API.GetProductInfo {}`: `version`; build 5101 сверяется **отдельно** по локальному About/достоверному product evidence — `archicad29()` проверяет лишь version 29 | `product.version`, `product.build`, источник build | `BLOCKED_PRODUCT_OR_BUILD_UNVERIFIED` |
| G0-PROJECT | `GetProjectInfo {}`: `projectPath,projectName,isUntitled,isTeamwork`; `RUN.EXPECTED_PATH` — exact match | `activeProject.path/name/port/sha256/isUntitled/isTeamwork` | `WRONG_PROJECT`, `UNTITLED`, `TEAMWORK`, `PLN_HASH_UNKNOWN` |
| G0-STORIES | `GetStories {}`: `actStory`, `stories[].index/floorId/level/name/uName`; сравнить **каждую** story с brief и `storyHeights` | `nativeStories[]`, `activeIndex`, `storyBindings[]`, `requiredStoryCount=2` | `BLOCKED_STORY_MISSING_OR_MISMATCH`; нет двух native stories; active index не совпадает |
| G0-TAPIR | `GetAddOnVersion {}`: `version`; локальный Add-On Manager и SHA256 фактического `.apx` | `tapir.version/apxPath/apxSha256/registeredCommands` | `TAPIR_VERSION_MISMATCH` или `BLOCKED_LOCAL_APX_OR_SCHEMA` |
| G0-SCHEMA | локально существующий каталог команд/полей; frozen `schemas/tapir-live-1.5.10/tapir-scene-live.json` PR74 blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7` — **исторический**, не runtime | `schema.localPath/localSha256/providerVersion/provenance/commandFields` | `BLOCKED_LOCAL_SCHEMA` при отсутствии фактического каталога |
| G0-MATERIAL | `GetAttributesByType {attributeType:"BuildingMaterial"}` → `GetBuildingMaterials {attributeIds:[...]}`; аналогично Surface/Composite/Profile **только если используются** | `materials[].name/attributeId/projectGuid/details`, точное соответствие CSE | `BLOCKED_ATTRIBUTE_BINDING` при ошибке, неоднозначности или отсутствии |
| G0-FAVORITES | `GetFavoritesByType {elementType:...}` в frozen Tapir, **но НЕ в `EvidenceAPI.READS` PR74**; разрешён только отдельный существующий read-only Tapir/UI путь | `favorites[].elementType/name/readMethod/evidence`; отдельно `status` | `BLOCKED_FAVORITE_READ` или `BLOCKED_FAVORITE_NOT_FOUND`; НЕ расширять router |
| G0-LIBRARY | `GetAvailableLibraryParts {}` / `{filterByTypeId:...}`: `libraryParts[]`, `skippedCount`, `skippedSample` | `libraryParts[].guid/index/documentName/fileName/typeId`, `skippedCount`, нужные Window/Door | `BLOCKED_LIBRARY_PART` при отсутствии; `PARTIAL_LIBRARY_INVENTORY` при `skippedCount>0` или отсутствии достоверного счётчика |
| G0-SPATIAL | `GetAllElements {}`, `Get3DBoundingBoxes {elements:[...]}`; при проблемных native bbox — существующий `GetModelDumpV1 {}` | `inventory.guids/count/coverage/envelope/collisionVerdict` | `BLOCKED_SPATIAL_PREFLIGHT` при неполном чтении/коллизии |
| G0-APA | локальный git checkout PR74 и точные `scripts/` + schema; не считать ветку исследований установленной сборкой | `apa.localCommit/workingTreeStatus/schemaPath/targetBinding` | `BLOCKED_LOCAL_CHECKOUT` при неизвестной версии/расхождении |

**Два дополнительных безусловных ограничения:** (1) `GetGDLParametersOfElements` читает **размещённые** элементы, не defaults/Favorites; (2) ни `ApplyFavoritesToElementDefaults`, ни импорт Favorites, ни `GenerateDocumentation` не запускать в этом цикле как «чтение». Если команда отсутствует в разрешённом read-only маршруте — записать `BLOCKED`, а не обходить ограничение новым writer/router.

**Точный target PR74:** `--scratch-port` связывает только `C:\LocalAI\APA_Test_House_01.pln`; `--isolated-port` — только `C:\LocalAI\APA_Isolated_Writer_Test_01.pln`. В коде также есть `bind_authorized_saved_copy(...)` с отдельным authorization reference и saved SHA, **но CLI не предоставляет произвольный флаг PLN**. Ни один путь не разрешает запись без отдельного допуска. Исторический default `Тест MER .pln` не использовать как новый scratch. Проверить `brief.targetProjectPath == RUN.EXPECTED_PATH` до G1.

### Минимальный шаблон записи (не фактические измерения)

```json
{
  "schema": "apa-build01-g0-readonly-manifest/1",
  "captureUtc": null,
  "runtimeObserved": false,
  "archicad": {"version": null, "build": null, "port": null, "productEvidence": null},
  "activeProject": {"path": null, "name": null, "sha256": null, "isUntitled": null, "isTeamwork": null},
  "nativeStories": [], "activeStoryIndex": null, "storyBindings": [],
  "tapir": {"version": null, "apxPath": null, "apxSha256": null, "schemaSha256": null, "registeredCommands": null},
  "materials": [], "favorites": {"status": "NOT_OBSERVED", "items": []},
  "library": {"status": "NOT_OBSERVED", "skippedCount": null, "parts": []},
  "spatialInventory": {"status": "NOT_OBSERVED", "guids": [], "collisionVerdict": null},
  "apa": {"localCommit": null, "schemaPath": null, "workingTreeStatus": null},
  "verdict": "BLOCKED_RUNTIME_NOT_OBSERVED"
}
```

Это **спецификация evidence-файла для I4**, не новый исполняемый интерфейс APA и не утверждение, что файл уже существует на ноутбуке. Каждый `null` требует фактического измерения; незаполненный manifest не закрывает G0.

## 3. R1-16B: четыре локальных STOP-контракта (local → frozen → upstream)

| Нативный тип | SOURCE frozen / существующий PR74 | Что сравнить с локальным 1.5.10 | Решение |
|---|---|---|---|
| **Window** `CreateWindows` | Frozen требует `ownerWallId,centerOffset`, `libraryPartName` опционален; upstream 1.5.9 в R1-14Z отмечен без `libraryPartName`. PR74 требует `ownerWallId.guid.$createdGuid` + `width,height,sillHeight` и проверку host | Фактический список допустимых полей, выбранный library part/Favorite, размеры, host, marker после разрешённой записи | Если нет local schema → `BLOCKED_LOCAL_SCHEMA_WINDOW`; drift → `WINDOW_SCHEMA_DRIFT`; библиотека/marker без readback → `WINDOW_FAMILY_UNVERIFIED` |
| **Door** `CreateDoors` | Аналогичный host-контракт, зависимость от ранее созданной Wall; `libraryPartName` drift | Local command schema + библиотека + параметры открытия/marker + native GUID host | `BLOCKED_LOCAL_SCHEMA_DOOR`, `DOOR_SCHEMA_DRIFT`, `DOOR_FAMILY_UNVERIFIED` |
| **Slab** `CreateSlabs` | Frozen `level,polygonCoordinates`; PR74 authored создаёт slab **сам**, не через `nativeComponents`; Basic material в одном SceneWriter реализован как `CreateSlabs → readback → ModifySlabs` | Реальный floorIndex, absolute `level` vs relative readback, толщина, GUID материала, наличие `ModifySlabs` и подтверждение второй операции | `BLOCKED_SLAB_SCHEMA_OR_MATERIAL`; при неизвестном результате CREATE/MODIFY → `UNKNOWN_PARTIAL_SLAB_STOP_NO_RETRY`; holes НЕ подтверждены |
| **Roof** `CreateRoofs` | PR74 authored принимает только typed Basic SinglePlane с `pivotLine,buildingMaterialId,floorIndex,polygonCoordinates,level`; verifier проверяет `roofClass=SinglePlane` | Local поля + материал GUID + pivot/angle/level/полигон, story binding и typed readback | `BLOCKED_ROOF_SCHEMA` или `BLOCKED_ROOF_TYPED_READBACK`; PolyRoof/NURBS/GDL/Morph **не** заменяют native Roof |

**Правило сравнения:** `local schema` — единственный допустимый источник допустимости runtime payload. `frozen 1.5.10` — эталон ожидаемой совместимости, `upstream` — источник для диагностики, не доказательство работоспособности локального APX. `SCHEMA_MATCH` можно выдать только при полном сравнении реально зарегистрированных команд/типов/полей, не по строке версии. Даже `SCHEMA_MATCH` не означает `LIVE` или `ACCEPTED`.

## 4. Дополнительный контрааудит: не путать этажи, GUID, узлы и BIM

1. **Этажность:** `GENERATE_FROM_ZERO` не создаёт этажи; `GetStories` обязателен до компиляции. Первый архитектурный этаж `label="1 этаж"`, `level=0`, высота 2.4–4.5 м, последующий уровень строго согласован с высотой (PR74 `archicad_semantic_brief.py` и `archicad_authored_native_plan.py`).
2. **GUID/host:** G1 может содержать только ссылку `$createdGuid`; реальный Wall GUID появляется после санкционированного G3. Отсутствие GUID в G1 не ошибка; выдуманный GUID — ошибка.
3. **Балка:** `CreateBeams` существует в Tapir и в `EXTENDED_WRITES` SceneWriter, но **не** в authored `nativeComponents` allowlist. Нельзя обещать её в G1 без подтверждённого существующего маршрута; это не основание создавать новый writer.
4. **Материалы и узлы:** `GetAttributesByType`/CSE-пакет подтверждают локальную привязку материала, **не** конструктивную несущую способность, пригодность узла, пожарные требования или соответствие СП. Узлы/стыки остаются `ENGINEERING_UNVERIFIED` до отдельной проверки.
5. **Rollback:** SQLite `ATTEMPTED` фиксируется до native write, но не делает транзакцию PLN атомарной. При UNKNOWN/timeout запрещён повтор CREATE; только read-only reconciliation и отдельное разрешение на восстановление scratch.
6. **Build 5101:** `archicad29()` проверяет `version=29`, а не build 5101; поэтому build — **внешний обязательный G0 факт**, а не «PASS компилятора».

## 5. Первоисточники, версии, лицензии

- PR74 immutable `5a3a9201a715a5528c93bed4a5318e2acb32eea7`: [compiler](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py), [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py), [brief](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_semantic_brief.py), [native plan](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py). Фактически прочитаны соответствующие исходные диапазоны; Git blob hashes указаны выше.
- [Graphisoft официальный каталог](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/): **Grasshopper–Archicad 29 Live Connection build 3000**, Windows, Rhino 7/8, выпуск **01.10.2025**, несовместим с Start Edition. Это доступность дистрибутива, не `INSTALLED`. Не подменять GC29 новой GC30.
- [Tapir официальный upstream](https://github.com/ENZYME-APD/tapir-archicad-automation): Archicad Add-On готов, GH plugin обозначен `work in progress`; исходный код MIT. Бинарник APX, лицензии Archicad 29 и Rhino 8, а также конкретная сборка GH-плагина локально не проверены. Бесплатный Tapir не делает платные хост-приложения бесплатными.

## 6. Передача I4 и A5: только действия, закрывающие blocker

| ID | Получатель | Действие | Критерий **ГОТОВО** |
|---|---|---|---|
| R1-16-I4-01 P0 | I4 | Снять реальный `G0-manifest` из разрешённого read-only Archicad 29 и файлового окружения ноутбука; зафиксировать exact scratch, port, active story, две native stories, APX/schema SHA и локальный commit | Все обязательные поля ненулевые, SHA фактические, `RUNTIME_READY` либо **один точный** `BLOCKED_<reason>` |
| R1-16-I4-02 P0 | I4 | Сравнить local/frozen/upstream Window/Door/Slab/Roof без установки/изменения router; проверить `skippedCount` и Favorites отдельным существующим READ | Четыре решения `MATCH/DRIFT/BLOCKED` с файлами evidence; нет ложного PASS |
| R1-16-I4-03 P0 | I4 | Только после G0 подготовить **один** новый authored JSON для двух этажей, Wall/Slab/SinglePlane Roof/Window/Door (+Column при подтверждении), без Beam в nativeComponents | Exact `targetProjectPath`, реальные story/material/library bindings; `G1 --preflight` только READ, writes=0, inventory before=after |
| R1-16-A5-01 P0 | A5 | Проверить новый G0 receipt, а не количество SOURCE-документов; не считать `GENERATE_FROM_ZERO` созданием этажей | `G0=READY` только по фактическому manifest; иначе `STALLED_EXTERNAL_DEPENDENCY` |

**Итог:** `SOURCE` — PR74 compiler/SceneWriter/brief/native plan, A5, предыдущий R1, Graphisoft, Tapir. `OFFLINE` — 0 новых запусков. `BUILD` — 0. `INSTALLED` — NOT_VERIFIED. `LIVE` — 0 новых. `ACCEPTED` — 0. `NOT_FOUND` (ограниченно) — текущий G0 manifest, локальный APX/schema evidence, GetFavoritesByType в PR74 READS, Beam в authored allowlist. `G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN`. **MODEL_MODE_NOT_VERIFIABLE.**
