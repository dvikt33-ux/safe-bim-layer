# APA R2 — BUILD-01: граница сериализации SQLite и протокол сверки UNKNOWN (17Z)

**Дата:** 24.10.2026, 17:00 UTC / 20:00 МСК. **Роль:** R2 — готовые мосты и синхронизация. **Цель:** [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Режим:** SOURCE_ONLY; локальная среда Windows/Archicad/Rhino/SQLite недоступна; **MODEL_MODE_NOT_VERIFIABLE**.

## 1. Входы и границы доказательств

Прочитаны через GitHub connector на указанной ветке, получены фактические Git blob SHA-1:

| Источник | Проверенный путь / immutable объект | SHA-1 | Итог |
|---|---|---|---|
| A5, последний доступный | `hourly/audit-a5-20261024T16Z-BUILD01-G0-G1-GATE-DECISION.md` | `78bb38b2326025c5e3c72eed89567a6a2ae34a11` | FOUND, задание R2 P1/84 |
| R1, последний доступный | `hourly/research-1-20261024T1603Z-BUILD01-G0-RUNTIME-DECISION-GATES.md` | `10173bf788344de8a85a926c98cac44a6f6053c9` | FOUND |
| R3, последний доступный | `hourly/research-3-20261024T1655Z-BUILD01-GH-BASE-BREP-BOUNDARY-DELTA.md` | `ef9c99defe91b500bfcae194cde06ef9cb84988e` | FOUND |
| I4, последний доступный | `hourly/integrator-4-20261024T1620Z-BUILD01-G0-G1-RUNTIME-STOP-CONTRACTS.md` | `64b30c6fa9980c3633be2332d10c5d9fa4b853f4` | FOUND |
| Исходный SceneWriter | PR74 commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, `scripts/archicad_scene_run.py` | `ca91c1cfc41cee763c62d1f3a70337d74fbafd53` | SOURCE READ, строки 750–955 |
| Внешний транспорт | тот же PR74, `scripts/archicad_project_accelerator.py` | `8e0ce2fbb5441009925f0d9199e180e8670a5eea` | SOURCE READ |

Срез 17Z только начался: новые R1/R3 за 17Z **не подтверждены**; используются именно последние доступные 16Z. Это не утверждение MISSING о ещё не наступившем сроке их публикации. Содержимое входов прочитано; текущий R2 не выдаёт исходный Git blob SHA за SHA установленного ПО.

**Указание A5:** не повторять поиск GH→PR74 в ранее просмотренных 12 файлах; проверить ровно границы `BEGIN IMMEDIATE` и составить безопасный read-only reconciliation runbook. Новый writer/router/SQLite-код запрещён.

## 2. Новое уточнение по PR74: фактическая граница идемпотентности

В `archicad_scene_run.py` внутри `_execute_verified_plan` существующий код делает:

1. `PRAGMA synchronous=FULL`, `CREATE TABLE IF NOT EXISTS scenes (scene_id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)`, `CREATE TABLE IF NOT EXISTS steps (... PRIMARY KEY(scene_id,step_id))`, `db.commit()`.
2. `BEGIN IMMEDIATE` → `SELECT 1 FROM scenes WHERE scene_id=? OR plan_hash=?` → при совпадении `SCENE_ALREADY_RESERVED` → иначе `INSERT INTO scenes` → `db.commit()`.
3. Перед каждой native-командой отдельная транзакция `BEGIN IMMEDIATE` → `INSERT INTO steps` со статусом `ATTEMPTED`, точным intent, `operationHash` и approval → `db.commit()` → **только затем** `self.api(command,params)`.
4. После ответа: `CREATED_UNVERIFIED` с GUID → типизированный readback → `PASS`. Для Basic Slab есть отдельное долговечное `BASIC_MODIFY_ATTEMPTED` до `ModifySlabs`. Любая неоднозначность → `PARTIAL_OR_UNKNOWN_OUTCOME` + `manualReconciliationRequired=true`. Полное выполнение заканчивается `COMPLETE_UNSAVED`, не сохранённым PLN.

**Доказуемое свойство:** `BEGIN IMMEDIATE` сериализует начало пишущих транзакций *одного и того же файла SQLite* при обычном соблюдении блокировок SQLite. Поскольку проверка `scene_id OR plan_hash` и вставка находятся внутри одной транзакции, два кооперативных исполнителя с одним ledger не могут одновременно пройти этот guard для одинакового plan_hash. Отсутствие отдельного `UNIQUE(plan_hash)` **не является доказательством гонки в этом узком сценарии**. Но SQL-ограничение отсутствует, поэтому сторонние вставки в обход guard и разные журналы не покрыты этим инвариантом.

**Недоказуемое свойство:** общая транзакция SQLite ↔ Archicad PLN ↔ GH/Rhino, глобальная уникальность plan_hash между разными файлами SQLite, автоматическое восстановление после тайм-аута, защищённость от отдельного GH writer или другого API-клиента. `synchronous=FULL` повышает долговечность подтверждённых транзакций при нормальной работе хранилища, но не делает нативный вызов атомарным с SQLite.

| Топология | Что подтверждено по коду | STOP для BUILD-01 |
|---|---|---|
| **Один SceneWriter, один SQLite ledger, один PLN** | Guard по `scene_id OR plan_hash` под `BEGIN IMMEDIATE`; intent перед вызовом | ALLOW только после G0/G1 и отдельного G3-допуска; никаких повторов `CREATE` |
| **Два процесса, тот же SQLite ledger** | Транзакции guard сериализуются; второй тот же plan_hash будет отклонён, если первый commit успешен | Не использовать параллельный G3: даже разные plan_hash могут писать в один PLN; `SECOND_EXECUTOR_STOP` |
| **Разные SQLite ledger, один PLN** | Нет общего guard; оба процесса могут считать себя единственными | `MULTI_LEDGER_STOP`; один утверждённый `data-dir`/ledger |
| **Один ledger, но GH Design Create/Modify / Tapir GH Push** | GH-писатель не участвует в SQLite guard и owner GUID | `SECOND_WRITER_STOP`; GH только параметризация и READ |
| **Crash после reservation до native call** | `STARTED` может остаться при отсутствии нового GUID; reservation не означает созданный элемент | `RESERVED_UNRESOLVED_STOP`; ручная сверка, не обходить новым `scene_id` |
| **Timeout после native call до GUID journal** | `ATTEMPTED` может остаться, хотя элемент уже создан | `UNKNOWN_NATIVE_OUTCOME_STOP`; нельзя безопасно повторять `CREATE` |
| **CreateSlabs PASS, ModifySlabs UNKNOWN** | GUID первого CREATE известен, второе изменение отдельно неатомарно | `PARTIAL_SLAB_STOP`; проверить material по существующему GUID, не пересоздавать Slab |
| **После `COMPLETE_UNSAVED`** | Модель могла измениться в памяти Archicad, сохранение не доказано | `UNSAVED_NOT_ACCEPTED`; G4 Save/Close/Reopen только с разрешением |

## 3. Read-only reconciliation runbook для I4

**Предусловие:** при `UNKNOWN`, `TIMEOUT`, `HOST_DRIFT`, `PARTIAL_SLAB` или `SECOND_WRITER` немедленно прекратить dispatch; не менять scene_id, plan_hash, порт, scratch PLN, ledger, не вызывать Undo/Delete/Modify/Save. Если процесс Archicad недоступен — зафиксировать `READBACK_UNAVAILABLE` и остановиться, не считать модель пустой.

**R0. Фиксация идентичности.** Зафиксировать UTC, PR74 commit, exact scratch path и SHA до запуска (если имеется), port, `GetProjectInfo`, `GetStories`, активный этаж и текущий статус несохранённых правок. При смене PLN/story: `PROJECT_IDENTITY_STOP`.

**R1. Только чтение ledger.** Открыть **утверждённый** SQLite-файл в read-only режиме (`mode=ro`, без создания нового файла). Прочитать `SELECT scene_id,plan_hash,state,result FROM scenes WHERE scene_id=? OR plan_hash=?`; затем `SELECT scene_id,step_id,state,guid,output FROM steps WHERE scene_id=? ORDER BY step_id`. Сохранить исходный файл как evidence только без изменения/подмены; сравнить `operationHash` и `target` в `output.intent` с утверждённым plan hash и проектом. Пустой ledger при возможной нативной записи — не PASS.

**R2. Native inventory.** Через существующий READ transport: `GetProjectInfo`, `GetStories`, `GetAllElements`, `GetDetailsOfElements` по известным GUID, при необходимости `Get3DBoundingBoxes`/`GetModelDumpV1`. Сверить тип, story/floorId/level, геометрию, hostWall GUID для Window/Door, thickness/material для Slab, число и пространственный диапазон элементов. Если GUID отсутствует в ledger из-за тайм-аута, нельзя автоматически объявить, что элемент не создан: нужен diff с pre-run inventory, пространственный и типовой поиск кандидатов, ручное разрешение неоднозначностей.

**R3. Классификация:** `NO_NATIVE_WRITE_EVIDENCE` (только если полная доказательная база), `NATIVE_CREATED_UNVERIFIED`, `NATIVE_VERIFIED_UNSAVED`, `PARTIAL_MODIFY`, `CONFLICTED` либо `INDETERMINATE`. Ни один из этих исходов сам по себе не разрешает replay. Только отдельно утверждённый recovery-процесс может использовать существующий механизм `seeded_created` после exact old-ledger + native matching; это не общее автоматическое resume.

**R4. Сохранение/rollback:** SQLite rollback не откатывает PLN. Rhino Undo и GH solution не откатывают native изменения. Никакого межпрограммного atomic rollback не найдено в проверенном scope. Восстановление — только из заранее сохранённой и идентифицированной отдельной scratch-копии, после сверки и явной санкции. `Save/Close/Reopen` является отдельным G4, не частью аварийного read-only runbook.

**R5. Защита от циклов и удаления:** обратный AC→GH readback не инициирует GH Design Create/Modify; исчезновение GH reference не трактуется как `DELETE`; изменение Rhino ObjectId/GH path не переопределяет AC GUID; `UPDATE` без существующей локально проверенной Modify-команды — `UPDATE_UNAUTHORIZED_STOP`.

## 4. Восемь маршрутов: решение для BUILD-01

| ID | Готовый маршрут | Направление | Native BIM | Решение |
|---|---|---|---|---|
| M1 | GH параметры → ручной `apa-authored-project/1` | GH→PR74 input | Native только после SceneWriter | **P0** G1, без GH adapter |
| M2 | `GetProjectInfo/GetStories/GetAttributesByType` | AC→APA READ | Читает native metadata | **P0** G0 |
| M3 | Graphisoft GC29 Element Input/Deconstruct | AC→GH READ | Читает native геометрию | OPTIONAL; не второй writer |
| M4 | PR74 typed compiler → BIM Graph → **один** SceneWriter/SQLite → Tapir | APA→AC CREATE | Да, при G3 readback | **Единственный** будущий writer |
| M5 | Graphisoft GC29 Design Create/Modify | GH→AC WRITE | Потенциально native | EXCLUDE параллельно M4 |
| M6 | Tapir GH plugin/Yak → Add-On | GH→Tapir WRITE | Зависит от команд | EXCLUDE: local Rhino8 package не проверен |
| M7 | Rhino.Inside, GDL/GSM/LCF, Bake→Morph | геометрия/объект | Не эквивалент Wall/Slab/Roof | EXCLUDE для P0; AC29 Rhino.Inside host NOT_FOUND_IN_SCOPED_SOURCES |
| M8 | Native GUID/BREP readback → IFC/IfcOpenShell/IDS | AC→QA READ | Проверяет, не создаёт | P1 G4, без нового writer |

**Первоисточники и лицензии:** [Graphisoft официальный дистрибутив GC29](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) — build **3000**, Rhino **7/8**, Windows, дата **01.10.2025**, Start Edition не поддерживается; локальная установка/лицензии AC/Rhino неизвестны. [Tapir upstream](https://github.com/ENZYME-APD/tapir-archicad-automation) — готовый Archicad Add-On, GH plugin обозначен **work in progress**, репозиторий MIT; лицензия исходников не подтверждает установленную локальную сборку 1.5.10. [RhinoCommon/Rhino.Inside developer docs](https://developer.rhino3d.com/) — не дают в проверенном объёме готового Archicad 29 host. `NOT_FOUND` относится только к ограниченно просмотренным источникам, а не ко всему рынку.

## 5. Статусы и передача I4/A5

| Уровень | Подтверждённое состояние |
|---|---|
| SOURCE | A5/R1/R3/I4 16Z FOUND с указанными SHA; PR74 SOURCE read; уточнена точная граница `BEGIN IMMEDIATE` и UNKNOWN |
| OFFLINE | **0 новых исполнений** SQLite/GH/PR74 в этом цикле |
| BUILD | **0 новых BUILD-01** |
| INSTALLED | **NOT_VERIFIED** (ноутбук не подключён) |
| LIVE | **0 новых native operations**, G1/G3 не запускались |
| ACCEPTED | **0** |
| NOT_FOUND | GH→PR74 adapter не найден только в ранее просмотренных 12 файлах пяти PR; atomic cross-app rollback и AC29 Rhino.Inside host не подтверждены в проверенном scope |
| G0 | `BLOCKED_RUNTIME_NOT_OBSERVED` |
| G1 | `NOT_RUN` |
| G2 | `SOURCE_PARTIAL_LOCAL_NOT_VERIFIED` |
| G3 | `NOT_AUTHORIZED` |
| G4/G5 | `NOT_RUN` |

**I4 — точное следующее действие:** получить единственный фактический G0 manifest: AC29 build5101, порт и SHA scratch PLN, два native stories с index/floorId/level, Tapir GetAddOnVersion=1.5.10/APX SHA256 и local command schema, материалы/Favorites/библиотеки, локальный PR74 commit, Rhino8 units и GC29 installed status. Затем выполнить **один** G1 read-only preflight с неизменным target, sourcePlanHash и `modelWriteAttempts=0`; никакого G3 без отдельного разрешения. При отсутствии доступа не публиковать повторные обзоры вместо G0.

**A5 — решение для следующего цикла:** закрыть R2 SOURCE-часть как `SINGLE_LEDGER_GUARD_SCOPED_VERIFIED`; не повышать до `GLOBAL_IDEMPOTENCE`. Открытый P0 — не новые плагины, а реальный G0 и один G1 receipt. Учитывать возможность `STARTED` без native записи и `ATTEMPTED` после успешного native CREATE: ни один из них не разрешает автоматический повтор.

**Границы действий:** `main`, код, PLN/APX, установки, LIVE, merge, платные API, Work/Codex/Arena не изменялись и не запускались. Исследовательская публикация — единственная запись. **MODEL_MODE_NOT_VERIFIABLE.**
