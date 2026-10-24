# APA A5 — независимый контрааудит и диспетчеризация BUILD-01, цикл 15Z

**Срез:** 24.10.2026, 15:43 UTC / 18:43 МСК. **Цель:** [BUILD-01, issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), OPEN при чтении. **Исследовательская ветка:** `research/apa-extension-ranking-hub-20261018`. **Разрешённая область:** SOURCE, GitHub READ и создание только настоящего markdown-аудита. **MODEL_MODE_NOT_VERIFIABLE.**

## A. Приёмка отчётов и проверка происхождения

Существование проверено фактическим `fetch_file` на исследовательской ветке. Для всех пяти файлов независимо пересчитан Git blob SHA-1 по UTF-8 содержимому (`SHA1("blob "+byte_length+"\0"+content)`); значение совпало с SHA, возвращённым GitHub. Это проверка содержимого Git, **не** проверка исполняемого результата на ноутбуке.

| Источник | Срез / файл в `hourly/` | Git blob SHA-1, независимо MATCH | Оценка времени |
|---|---|---|---|
| R1 | [research-1-20261024T1458Z-BUILD01-G0-READONLY-INVENTORY.md](research-1-20261024T1458Z-BUILD01-G0-READONLY-INVENTORY.md) | `5c036f238ae65afd3a0f338eb98d0884aaad7805` | **FOUND_SHA_MATCH / PARTIAL_CURRENT_HOUR**: 14:58Z, на 2 минуты раньше границы 15Z; принять как вход данного цикла с оговоркой |
| R2 | [research-2-20261024T1504Z-BUILD01-SCOPED-BRIDGE-CLOSURE.md](research-2-20261024T1504Z-BUILD01-SCOPED-BRIDGE-CLOSURE.md) | `1407b1d013d59f73738614ed09c33e057d4b6e3b` | FOUND_SHA_MATCH / 15Z |
| R3 | [research-3-20261024T15Z-BUILD01-A5-STRICT-GH-CONTRACT-QA.md](research-3-20261024T15Z-BUILD01-A5-STRICT-GH-CONTRACT-QA.md) | `ac9a9b8d80def329a29915755603801fa5c98465` | FOUND_SHA_MATCH / 15Z; точная минута в имени не указана |
| I4 | [integrator-4-20261024T1522Z-BUILD01-G0G1-ONE-WRITER-READONLY-RUNBOOK.md](integrator-4-20261024T1522Z-BUILD01-G0G1-ONE-WRITER-READONLY-RUNBOOK.md) | `702bb038a8078297ee9a0ddb4ee1d07b98e7461b` | FOUND_SHA_MATCH / 15:22Z |
| Предыдущий A5 | [audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md](audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md) | `2b9079c78c226f4c01cb05b6957e993c6f4e0d12` | Контекст, **не** новый вход R1–I4 |

**Честная классификация:** четыре известных входа реально существуют и имеют корректный blob SHA; в строгом календарном окне 15:00–15:59 UTC подтверждены **3/4**, R1 — **PARTIAL_CURRENT_HOUR**, а не MISSING-файл. Список всех возможных файлов каталога на ветке не выгружался, поэтому утверждать, что другого R1-15Z нет, нельзя. Новых G0/G1 квитанций во входных отчётах нет. Канонический `NEXT_RESEARCH_PRIORITIES.md` прочитан: blob `6f074693360231c5cb42ada815984a6b0dd504c0`; **не изменялся**.

## B. Контрааудит CA-A5-15A — первоисточники, версии, лицензии, границы утверждений

1. **Graphisoft**: [официальная страница Rhino–Grasshopper–Archicad](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) указывает Grasshopper–Archicad **29 Live Connection, build 3000, Windows, Rhino 7/8, 01.10.2025**, не для Start Edition. Это подтверждает наличие официального дистрибутива, **не** локальную установку, совместимость конкретного ноутбука/AC29 build 5101, режим одного writer или лицензии Rhino/Archicad.
2. **Tapir**: [официальный upstream](https://github.com/ENZYME-APD/tapir-archicad-automation) различает готовый Archicad Add-On и Grasshopper Plugin `work in progress`; исходный репозиторий MIT. Лицензия исходников не доказывает локальную лицензию/совместимость отдельного Yak-пакета. `Tapir 1.5.10` — заявленная локальная версия, но `GetAddOnVersion`, APX SHA256 и зарегистрированные команды в этом цикле **не получены**. Frozen 1.5.10 schema ≠ runtime schema; upstream 1.5.9 ≠ локальный бинарник.
3. **Rhino 8 / RhinoCommon / GH**: геометрический движок и API требуют лицензированного Rhino; наличие штатного Grasshopper не означает исполнение конкретного `.gh`. R3 подтвердил только численный Python-пример 96−4=92 м² и угол 21.801409486°, **не** исполненный NURBS/BREP и не нормативный PASS.
4. **Immutable APA PR74**: перепроверены файлы на commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`: `scripts/archicad_project_accelerator.py` (blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`), `scripts/archicad_scene_run.py` (blob `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`), `scripts/archicad_connected_components.py` (blob `c5a99f59a90369ff622807574677cf11ca0a2225`). **Не установлено**, что PR74/126/131/149/162 объединены в локальном checkout.
5. **Фактический источник G0**: R1 показывает `GetFavoritesByType` в frozen Tapir, но **не** в `EvidenceAPI.READS` PR74. В G0 нужен существующий независимый read-only способ или честный `BLOCKED_FAVORITE`. `GetAvailableLibraryParts.skippedCount>0` означает PARTIAL. У окон/дверей `libraryPartName` в frozen схеме против upstream 1.5.9 — риск `SCHEMA_DRIFT`, не доказанный runtime FAIL.
6. **Обязательные расширения**: для первого G1 нет основания требовать Yak Tapir GH, Rhino.Inside Archicad host, Karamba, Honeybee, IFC/IDS. Они не закрывают P0 runtime blocker и не являются доказанным бесплатным native BIM writer. Наличие официального GC29 не разрешает его GH Design Create/Modify одновременно с APA SceneWriter.

**Вердикт CA-A5-15A:** `SOURCE_PARTIAL_PASS / VERSIONS_SOURCE_CONFIRMED / LOCAL_INSTALL_AND_LICENSE_NOT_VERIFIED`. Нельзя повышать SOURCE до INSTALLED.

## C. Контрааудит CA-A5-15B — инженерная воспроизводимость, конфликты, отсутствие дублирования

**Проверено непосредственно в PR74:**
- `compile_authored_intent`, строки 265–296: `apa-authored-project/1` требует `schemaVersion,projectId,units,brief,cseCandidate,layout,storyHeights` и допускает только ограниченные дополнительные поля. `nativeComponents` allowlist: `CreateColumns/CreateDoors/CreateWindows/CreateWalls/CreateRoofs`. `CreateSlabs` формируется authored compiler; `CreateBeams` **не** в этом allowlist. Roof проверяется как `SinglePlane/Basic`; PolyRoof и произвольный NURBS/BREP не принимаются автоматически.
- `run_project`, строки 438–447: authored intent **не поддерживает автономный offline**; `--preflight` требует callable transport и реальный guarded Archicad для READ. В `--preflight` запись нативных элементов запрещена существующим `EvidenceAPI`. В результате evidenceKind может называться `LIVE` из-за транспорта, но это **LIVE_READ**, не разрешённая нативная запись и не G3.
- CLI, строки 609–649: `--intent`, `--schema`, обязательный `--output`, `--preflight`, `--scratch-port`/`--isolated-port`; каталог `--output` должен быть **новым, не существовать до запуска** (`mkdir(exist_ok=False)`). Путь `brief.targetProjectPath` обязан равняться `RUN.EXPECTED_PATH`, а не произвольной строке.
- `SceneWriter`, строки 776–787: SQLite резервирует `scene_id/plan_hash`; повторный ambiguous CREATE запрещён. Строки 856–893: Slab Basic проходит `CreateSlabs → GUID/readback → ModifySlabs(material)`, две native mutations в **одном** writer. SQLite **не** атомарная транзакция PLN; при UNKNOWN — STOP, чтение ledger и AC, **не** повтор CREATE.
- `ConnectedComponent.verify`, строки 184–196: Roof typed readback требует `roofClass=SinglePlane` и точных level, pivot, material, angle, polygon. Источник Rhino BREP и GH preview не доказывает native Archicad Roof.

**Владение и идентичность:** Rhino ObjectId, GH component/path, APA `projectId/stepId/sourcePlanHash/scene_id`, Archicad GUID, IFC GlobalId — отдельные пространства. Нативный GUID и host Wall GUID выдаёт Archicad; GH не может объявить их заранее. `ownerWallId.guid.$createdGuid` должен разрешаться после CREATE родительской Wall. `floorIndex/floorId/level` брать из реального `GetStories`. При host drift/удалении стены, потере GH reference, конфликте material/story, изменении проекта, тайм-ауте или рассогласовании Save/Open — **STOP**, затем независимый read-only reconciliation; без автоматического удаления, перепривязки, повтора и «лечения» новым `scene_id`.

**Один writer:** единственный допустимый путь нативной записи после разрешения — существующий `PR74 → BIM Graph → SceneWriter/SQLite → Tapir → Archicad`. GH формирует параметры/QA; GC29 `Element Input/Deconstruct` — read-only. GH Design Create/Modify, Tapir GH Push и любой параллельный writer запрещены в том же проекте. Автоматический `GH DataTree → typed PR74` **NOT_FOUND только в 12 проверенных Python-файлах пяти PR head commits**; R2 закончил этот ограниченный поиск. Временный G1 путь — ручной перенос проверенных параметров в существующий authored JSON. Это **не** трёхсторонняя автоматическая синхронизация.

**Независимая приёмка:** `GH_GEOMETRY` (контуры/плоскости/допуски/BREP), `AC_NATIVE` (GUID/type/story/host/material/BREP после Save/Open), `IFC_STRUCTURE` (IFC-типы/GlobalId/containment/voids/fills), `IDS_INFORMATION` (информационные требования), `NORMATIVE_REVIEW` (конкретный СП/редакция/пункт/измерение) — **пять разных** verdict. Отсутствие доказательств = UNKNOWN, не PASS. Cross-app atomic rollback **NOT_FOUND**; восстановление только из отдельно санкционированного snapshot scratch после reconciliation, без автоматического отката.

**Вердикт CA-A5-15B:** `SOURCE_ONE_WRITER_CONTRACT_CONFIRMED / BUILD_NOT_REPRODUCED / RUNTIME_REQUIRED / NO_ATOMIC_ROLLBACK`. R1/R2/R3/I4 закрыли часть SOURCE-поручений, но не G0 и не G1.

## D. G0–G5: ворота, реальные результаты и критерии ГОТОВО

| Gate | Доказательство ГОТОВО | Фактический статус на 15:43Z |
|---|---|---|
| **G0** | С ноутбука: AC29 **29/5101** и активный port/project/approved scratch PLN SHA256; Tapir `GetAddOnVersion`/APX SHA/schema; `GetStories`, materials/Favorites/library `skippedCount`; Rhino8 SR/license/units/tolerances, GC29 installed; локальный APA commit и отсутствие чужих несохранённых изменений | **BLOCKED_RUNTIME**: локальный manifest отсутствует |
| **G1** | **Реальный** `--preflight` нового двухэтажного `apa-authored-project/1` на точном scratch target, с работающим Archicad **только READ**; typed DAG, host/story bindings, collision, `confirmPlanHash`, `plan.json/preflight.json/result.json/inventory-before.json/inventory-after.json/SHA256.json`, before=after, native writes=0 | **NOT_RUN**; SOURCE runbook ≠ квитанция |
| **G2** | Сопоставлены фактические зарегистрированные команды Tapir 1.5.10, frozen schema, материалы/Favorites/library, host/story; Wall/Slab/Column/SinglePlane Roof/Window/Door; Beam отдельно как вне authored allowlist | **SOURCE_PARTIAL / BLOCKED_LOCAL_SCHEMA** |
| **G3** | Отдельное разрешение на **точный** scratch PLN/port/plan hash, SQLite intent-before-write, native GUID/type/story/host/material/BREP, один SceneWriter, no duplicate writes | **NOT_AUTHORIZED / NOT_RUN** |
| **G4** | Разрешённый GuardedSave → Close → no-open check → Reopen → независимый diff GUID/type/story/host/material/BREP/geometry, SHA receipts | **NOT_RUN** |
| **G5** | Другая scratch PLN и иное исходное здание; повтор G1–G4 без reuse старого fixture/sceneId | **NOT_RUN** |

**BUILD-01:** нет нового native здания, Save/Open или второго здания. Исторические APA LIVE прототипы из issue #192 — **не** новые квитанции BUILD-01. Нативный BIM не `ACCEPTED`; G0/G1 блокируют дальнейшую работу. Не подменять проектирование доказательствами математического GH-образца.

## E. Реестр блокеров и управленческое решение

| ID | Ответственный | Открытый blocker | Следующее закрывающее действие |
|---|---|---|---|
| **A5-15-B01 P0** | Владелец ноутбука / I4 | Нет фактического доступа к G0 runtime, scratch PLN/port/APX/checkout | Read-only G0 manifest с точными значениями и SHA; иначе один `BLOCKED_<reason>` |
| **A5-15-B02 P0** | I4 | Нет нового schema-valid authored fixture, зависящего от story/material/target/origin | После G0 — **один** новый двухэтажный JSON из PR74 example; без выдуманных локальных bindings |
| **A5-15-B03 P0** | I4 | Нет G1 receipt | Один `--preflight` с READ transport, новым output directory, inventory unchanged, writes=0, SHA manifest |
| **A5-15-B04 P0** | R1 / I4 | Локальная Tapir 1.5.10 schema, Favorites, libraryPartName, APX SHA неизвестны | Frozen/upstream/local матрица и STOP на drift, без изменения router |
| **A5-15-B05 P1** | R2 | GH→PR74 auto bridge отсутствует в scoped 12-file search | **SOURCE_SCOPED_CLOSED**: не искать снова без нового конкретного кандидата; ручной JSON для G1 |
| **A5-15-B06 P1** | R3 | GH-BASE не исполнен, holes/PolyRoof вне базового G1 | **SOURCE_SPEC_CLOSED**: QA/negative-case спецификация достаточна до G1; не создавать writer |
| **A5-15-B07 P0** | I4 / A5 | G3/G4/G5 без допуска и native receipts | Сохранить STOP и будущую матрицу readback; не проводить LIVE без отдельного разрешения |
| **A5-15-B08 P0** | A5 | Повторение SOURCE без инженерного прогресса | Следующий аудит измеряет новые G0 manifest/G1 receipts и закрытие B01–B04, а не число файлов/проверок |

**Решение A5:** принять R2-15A/B и R3-15A/B как `SOURCE_SCOPED_DONE`, R1-15A как `SOURCE_INVENTORY_READY`; **не** как G0/G1. Принять I4 runbook как `SOURCE_RUNBOOK_READY`, не как G1. `G1=READ_ONLY_PREFLIGHT_REQUIRES_ARCHICAD`; не использовать термин «полностью автономный offline» для authored PR74. При отсутствии G0/G1 зафиксировать `STALLED_EXTERNAL_DEPENDENCY`, а не расширять набор исследований. Не требовать установки дополнительных плагинов до закрытия G0.

## F. Четыре адресных поручения на следующий час (16Z)

### R1 — нативные BIM-инструменты, **P0 / 98**

**R1-16A:** закончить **ровно один** готовый к применению G0 inventory template: поля AC29 build/port/PLN SHA, Tapir version/APX SHA/registered command schema, GetStories nativeIndex/floorId/level, materials, Favorites отдельным существующим READ, library `skippedCount`. **ГОТОВО:** таблица `command → actual field → evidence file → STOP`, без пустых «PASS» и без нового исследования команд.

**R1-16B:** для Window/Door/Slab/Roof дать компактный local-vs-frozen-vs-upstream decision tree: если локальной схемы нет — `BLOCKED_LOCAL_SCHEMA`, не подставлять значения из upstream. **ГОТОВО:** четыре конкретных STOP-контракта и передача I4; никакой разработки API.

### R2 — мосты/синхронизация, **P1 / 85**

**R2-16A:** **не повторять** поиск GH bridge в уже проверенных 12 файлах. Закрепить существующий один writer в матрице `source ID → native GUID → ledger → readback` и семь событий: CREATE, UPDATE, DELETE, UNKNOWN, PARTIAL_SLAB, HOST_DRIFT, FEEDBACK_LOOP. **ГОТОВО:** у каждого события владелец, действующий guard, STOP и разрешённое READ действие; `NOT_FOUND_IN_SCOPED_PR_HEADS` остаётся точным, без абсолютного NOT_FOUND.

**R2-16B:** если нет нового конкретного адаптера, завершить час статусом `SOURCE_CLOSED_NO_NEW_CANDIDATE`. **ГОТОВО:** I4 получает только готовую conflict matrix, не предложение второго synchronizer.

### R3 — Grasshopper/геометрия/нормативы, **P1 / 82**

**R3-16A:** не расширять GH-OPT, PolyRoof и список плагинов. Сжать GH-BASE до одной проверяемой таблицы `GH parameter → exact authored JSON field → units → precheck → evidence`, со всеми P0 Wall/Slab/SinglePlane Roof/Window/Door и stories. **ГОТОВО:** один schema-bound input checklist без фиктивного `.gh PASS`.

**R3-16B:** передать I4 только пять независимых QA verdict и 3 критические негативные проверки (wrong Z, missing host, mm↔m drift). **ГОТОВО:** ожидаемый STOP, требуемый readback, что именно не доказывается; никаких новых нормативных PASS без СП/редакции/пункта.

### I4 — единая исполнимая схема, **P0 / 100**

**I4-16A:** главный deliverable — **один исполнимый G0→G1 runbook**, не новый исследовательский обзор. На G0: локальный manifest с точным scratch PLN/port/immutable PR74, Tapir APX/schema/attributes/stories, Rhino/GC29. Если ноутбук недоступен — явно `BLOCKED_RUNTIME` и **не** имитировать инвентаризацию. **ГОТОВО:** реальные G0 значения/хеши либо исчерпывающий перечень неизвестных, привязанный к одному внешнему blocker.

**I4-16B:** подготовить **одно** новое authored двухэтажное задание только из существующего PR74 example с правильным `brief.targetProjectPath=RUN.EXPECTED_PATH`, реальными `GetStories`/материалами и свободным origin. Пока локальные bindings неизвестны — `UNRESOLVED` в спецификации, не в выдаваемом как валидный JSON. **ГОТОВО:** schema-valid intent **после G0** либо точный `BLOCKED_LOCAL_BINDINGS`, без нового writer/router.

**I4-16C:** после фактического G0 — единственный `--preflight` (НЕ `--execute`) с новым, ранее не существовавшим `--output` и явным `--scratch-port` или `--isolated-port`, только на разрешённой копии. **ГОТОВО:** `READY_FOR_EXPLICIT_TEST_RUN` + `confirmPlanHash` + DAG + SHA256 manifest + `inventoryUnchanged=true` + native writes=0, иначе `G1_BLOCKED` с точной причиной. Без G0 — запуск запрещён.

## G. Строгие статусы и ограничения

- **SOURCE:** R1/R2/R3/I4 по известным путям FOUND, blob SHA independently MATCH; R1 `PARTIAL_CURRENT_HOUR` по отметке 14:58Z. Два контрааудита выполнены на проверенных исходниках и официальных страницах.
- **OFFLINE:** R3 только арифметика `OFFLINE_NUMERIC_ONLY`; **G1 preflight NOT_RUN**.
- **BUILD:** 0 новых зданий.
- **INSTALLED:** NOT_VERIFIED; нет доступа к локальному Windows/Archicad/Rhino.
- **LIVE:** 0 новых native writes; `--preflight` с read-only transport пока также не выполнялся.
- **ACCEPTED:** 0.
- **NOT_FOUND (только scope):** GH→PR74 converter в 12 Python-файлах пяти PR, PR74 PolyRoof/hole verifier, Rhino.Inside AC29 host в проверенных материалах, атомарный cross-app rollback.
- **G0/G1/G2/G3/G4/G5:** `BLOCKED_RUNTIME / NOT_RUN / SOURCE_PARTIAL / NOT_AUTHORIZED / NOT_RUN / NOT_RUN`.
- **Запреты соблюдены:** main, исходный код, PLN/APX, установки, native LIVE, merge, платные API, Work/Codex/Arena не изменялись и не запускались. `NEXT_RESEARCH_PRIORITIES.md` прочитан и оставлен без изменений во избежание гонки/перезаписи чужих правок.
- **Публикационный статус** устанавливается только после фактического create → fetch по commit и по ветке → независимый blob SHA. При сбое: `WRITE_BLOCKED`.

**Решение:** `STALLED_EXTERNAL_DEPENDENCY` до реального G0; следующий измеримый прогресс — **runtime manifest, затем G1 preflight receipt**, а не количество новых SOURCE-отчётов. **MODEL_MODE_NOT_VERIFIABLE.**
