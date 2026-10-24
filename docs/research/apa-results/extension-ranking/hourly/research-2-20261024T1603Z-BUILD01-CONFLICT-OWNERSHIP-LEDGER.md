# APA R2 — BUILD-01: владение GUID, журнал операций и закрытая матрица конфликтов
**Срез:** 24.10.2026, 16:03 UTC / 19:03 МСК. **Исполнитель:** R2, мосты и синхронизация. **Цель:** [BUILD-01, issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка:** research/apa-extension-ranking-hub-20261018. **Режим:** SOURCE_ONLY; MODEL_MODE_NOT_VERIFIABLE.

## 1. Поручение A5 и проверенные входы
Прочитан актуальный [аудит A5 15:43Z](audit-a5-20261024T1543Z-BUILD01-G0G1-STRICT-COUNTERAUDIT.md), Git blob SHA-1 af0ab17e54b556001a47572a5d858e8c9eda76a8. Поручения R2-16A/16B: (а) закрытая матрица source ID → native GUID → SQLite ledger → readback для семи событий CREATE, UPDATE, DELETE, UNKNOWN, PARTIAL_SLAB, HOST_DRIFT, FEEDBACK_LOOP; (б) без повторного поиска уже проверенных 12 Python-файлов и без второго writer/router/synchronizer.

Прочитаны на исследовательской ветке:
- [R1 G0, 14:58Z](research-1-20261024T1458Z-BUILD01-G0-READONLY-INVENTORY.md), blob 5c036f238ae65afd3a0f338eb98d0884aaad7805;
- [R3 GH, 15Z](research-3-20261024T15Z-BUILD01-A5-STRICT-GH-CONTRACT-QA.md), blob ac9a9b8d80def329a29915755603801fa5c98465;
- [I4 runbook, 15:22Z](integrator-4-20261024T1522Z-BUILD01-G0G1-ONE-WRITER-READONLY-RUNBOOK.md), blob 702bb038a8078297ee9a0ddb4ee1d07b98e7461b;
- [R2 предыдущий, 15:04Z](research-2-20261024T1504Z-BUILD01-SCOPED-BRIDGE-CLOSURE.md), blob 1407b1d013d59f73738614ed09c33e057d4b6e3b.

Повторно прочитаны immutable исходники PR74 commit 5a3a9201a715a5528c93bed4a5318e2acb32eea7: scripts/archicad_project_accelerator.py (blob 8e0ce2fbb5441009925f0d9199e180e8670a5eea), scripts/archicad_scene_run.py (blob ca91c1cfc41cee763c62d1f3a70337d74fbafd53). Указанные blob SHA получены из GitHub; отдельная локальная инвентаризация не выполнялась.

## 2. Первичные факты: что реально обеспечивает один writer
1. PR74, archicad_project_accelerator.py:31–38 — явный список EvidenceAPI.READS, в нём нет GetFavoritesByType; :262–296 — schemaVersion=apa-authored-project/1 и allowlist nativeComponents (CreateColumns/CreateDoors/CreateWindows/CreateWalls/CreateRoofs). CreateSlabs формируется authored candidate; CreateBeams в этом allowlist отсутствует.
2. Там же :438–447 — authored требует mode preflight/execute и callable transport; для G1 нужен реальный Archicad READ. Это не полностью автономный OFFLINE.
3. PR74, archicad_scene_run.py:776–787 — SQLite scenes(scene_id PRIMARY KEY, plan_hash, state, result), steps(scene_id,step_id,state,guid,output). Резервирование по совпадению scene_id ИЛИ plan_hash отклоняется SCENE_ALREADY_RESERVED. В коде виден SELECT, а не отдельный SQL UNIQUE constraint на plan_hash: защиту следует оценивать в контексте существующего процесса, не объявлять универсальной межпроцессной атомарностью.
4. Там же :823–849 — перед нативным вызовом вычисляется operationHash из resolved parameters/target и долговечно записывается шаг ATTEMPTED. :849–853 — native call, извлечение GUID, состояние CREATED_UNVERIFIED.
5. Там же :856–893 — для Basic Slab возможны две native mutations: CreateSlabs → GUID/readback → BASIC_MODIFY_ATTEMPTED → ModifySlabs(material). Это один SceneWriter, но НЕ одна атомарная операция.
6. Там же :894–919 — typed readback после создания, запись PASS в steps. :920–939 — любая ошибка после неопределённого native call переводит сцену в PARTIAL_OR_UNKNOWN_OUTCOME и manualReconciliationRequired=true. :941–952 — COMPLETE_UNSAVED не означает сохранение PLN.
7. CLI archicad_project_accelerator.py:609–649 требует --output в новом каталоге и для execute отдельные run-id/confirm-plan-hash/data-dir; scratch/isolated port связывают только заранее предусмотренные локальные PLN. Это не разрешение LIVE.

## 3. Пространства идентификаторов: один источник истины
| Сущность | Кто создаёт и владеет | Где хранить связь | Правило |
|---|---|---|---|
| Rhino ObjectId | Rhino | Входная reference/QA-ведомость, только если Rhino объект действительно создан | Не подменяет AC GUID; изменение Rhino не разрешает native UPDATE |
| GH document/component/tree path | Grasshopper | GH parameter snapshot/источник геометрии | Нестабильный индекс дерева не использовать как постоянный native ID |
| APA projectId / stepId | Typed authored plan PR74 | plan.json + DAG | Логическая идентичность задания, не идентификатор размещённого элемента |
| sourcePlanHash / scene_id / operationHash | Существующий SceneWriter | SQLite scenes/steps + evidence | Повтор с новым scene_id после UNKNOWN запрещён как обход защиты |
| Native GUID | Archicad после успешного CREATE | SQLite steps.guid + GetDetailsOfElements/readback | Единственный авторитет для native элемента |
| ownerWallId / host GUID | Archicad после CREATE Wall | Разрешение $createdGuid в DAG + hosted readback | Window/Door не создаются до достоверного GUID родительской Wall |
| story nativeIndex / floorId / level | Активный PLN / GetStories | G0 manifest + plan bindings | Не выводить из GH порядка ветвей или предполагаемой высоты |
| IFC GlobalId | IFC-модель/экспорт | Независимый IFC QA manifest | Не считать равным AC GUID; нужна явная доказанная карта соответствия |

**Граница управления:** Rhino/GH владеют исходными параметрами и вычисленной геометрией; APA владеет заданием, журналом и порядком операций; Archicad владеет размещёнными native элементами и GUID. Graphisoft GC29 Element Input/Deconstruct — только чтение. GH Design Create/Modify и Tapir GH Push в том же PLN запрещены, иначе появляется второй writer.

## 4. Семь событий: исполнимая матрица конфликтов R2-16A
| Событие | Owner / идентификатор | Существующий guard (SOURCE) | STOP / состояние | Разрешённое READ для I4 |
|---|---|---|---|---|
| CREATE | SceneWriter stepId → AC GUID | project binding, plan hash, operationHash, SQLite ATTEMPTED до native call | Если вызов/ответ/verification неясен: UNKNOWN_STOP, никогда не повторять CREATE | SELECT scenes/steps; GetAllElements; GetDetailsOfElements для найденного GUID; сравнить тип/story/material/bbox |
| UPDATE | AC GUID; единственный SceneWriter, если команда поддержана | Явно доказан только двухшаговый ModifySlabs(material) в текущем пути; общего UPDATE из GH не подтверждено | UPDATE_NOT_AUTHORIZED или SCHEMA_DRIFT_STOP при неизвестной команде/target | Прочитать текущие атрибуты GUID и ledger; сравнить с исходным планом, ничего не изменять |
| DELETE | AC GUID/host, не GH Null | Отсутствие разрешённого DELETE в рассматриваемом BUILD-01; no implicit deletion | DELETE_UNAUTHORIZED_STOP; потеря GH reference не означает удаление AC | GetAllElements/GetDetailsOfElements + host children; ledger сверить вручную |
| UNKNOWN/TIMEOUT | scene_id/plan_hash/stepId/operationHash | ATTEMPTED до вызова, PARTIAL_OR_UNKNOWN_OUTCOME после исключения; automaticRetry=false | MANUAL_RECONCILIATION_REQUIRED, не менять scene_id и не выполнять повторный CREATE | SQLite steps.state/guid/output, GetProjectInfo, GetAllElements, GetDetailsOfElements; snapshot diff |
| PARTIAL_SLAB | AC Slab GUID, существующий SceneWriter | CREATED_UNVERIFIED → промежуточный readback → BASIC_MODIFY_ATTEMPTED → ModifySlabs | При неизвестном Modify — SLAB_MATERIAL_UNKNOWN_STOP, CreateSlabs НЕ повторять | По сохранённому GUID прочитать thickness, material, story, polygon; сопоставить с journal |
| HOST_DRIFT | AC Wall GUID → Window/Door ownerWallId | DAG parent $createdGuid и проверка hosted readback | HOST_DRIFT_STOP при исчезновении/смене host/story; без автоматической перепривязки | GetDetailsOfElements для Wall и openings, сверка parent GUID и story |
| FEEDBACK_LOOP | GH input reference + AC GUID | Правило одного writer: GH только reference/QA, native write через PR74 | SECOND_WRITER_STOP при активном GH Design Create/Modify или Tapir GH Push | Разорвать/выключить write branch GH без изменения AC; затем read-only inventory |

**Восстановление:** SQLite — журнал намерений/результатов, не транзакция PLN. GH Undo не откатывает AC, а AC Undo не гарантирует согласованность Rhino/SQLite. ATOMIC_CROSS_APP_ROLLBACK_NOT_FOUND в проверенном scope. Восстановление допускается только из заранее утверждённого scratch snapshot после отдельной read-only сверки и разрешения; автоматический rollback запрещён.

## 5. Восемь маршрутов и решение для I4
| Маршрут | Направление / готовое средство | Native BIM? | Решение |
|---|---|---|---|
| M1 | GH параметры → ручная проверка → существующий authored JSON PR74 | После SceneWriter, не в GH | P0 для G1, без GH adapter |
| M2 | Archicad GetProjectInfo/GetStories/GetAttributesByType → G0/G1 | READ native metadata | P0; exact story/material bindings |
| M3 | GC29 Element Input/Deconstruct → GH geometry QA | Только чтение AC native | P1 после INSTALLED, не G0 blocker |
| M4 | PR74 → BIM Graph → SceneWriter/SQLite → Tapir → Archicad | Да, при санкционированном G3 и readback | Единственный будущий writer |
| M5 | GH Design Create/Modify через официальный GC29 | Может создать native BIM, но параллельный writer | EXCLUDED из BUILD-01 |
| M6 | Tapir Grasshopper Yak → Tapir Add-On | Потенциальный writer, Rhino8 distribution не подтверждён | EXCLUDED, не обязательная установка |
| M7 | Rhino.Inside host / GDL / Morph import | Готовый AC29 host не доказан; GDL/Morph не эквивалент Wall/Slab | EXCLUDED из native acceptance |
| M8 | AC GUID/BREP readback → IFC/IfcOpenShell/IDS QA | Проверяет, но не пишет native BIM | P1 для G4, только READ |

**Нового конкретного готового GH DataTree → PR74 adapter за этот цикл не установлено.** Прежний ограниченный поиск 12 Python-файлов на пяти PR head commits остаётся: GH_TO_PR74_ADAPTER_NOT_FOUND_IN_12_INSPECTED_FILES_5_PR_HEADS. Это НЕ утверждение об отсутствии во всём GitHub. **Решение R2-16B: SOURCE_CLOSED_NO_NEW_CANDIDATE.**

## 6. Первоисточники, версии и лицензии (контрааудит SOURCE)
- [Graphisoft официальный дистрибутив](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/): Grasshopper–Archicad 29 Live Connection build 3000, Windows, Rhino 7/8, 01.10.2025; Start Edition не поддерживается. AC29 build5101 + конкретный ноутбук не проверены; доступность загрузки ≠ INSTALLED.
- [Tapir upstream](https://github.com/ENZYME-APD/tapir-archicad-automation): MIT для репозитория, готовый Archicad Add-On, GH plugin work in progress; frozen 1.5.10 не равен локальной runtime schema.
- [Rhino Packages Tapir](https://rhinopackages.github.io/package/tapir): GH 1.7.2, 19.10.2026, только опубликованная rh7_21 Yak, Rhino8 build не указан, license в каталоге not declared. Отсутствие отдельного Yak ≠ доказательство невозможности работы Rhino8.
- [McNeel Rhino.Inside](https://www.rhino3d.com/features/rhino-inside/): Windows embedded Rhino для host-приложений; поддерживаемый готовый Archicad 29 host в проверенных материалах не установлен. Rhino и Archicad — лицензируемые хост-приложения; бесплатный open-source компонент не заменяет их лицензии.
- [Tapir upstream guidance](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/CLAUDE.md): исходники GH plugin multi-target net7.0-windows/net7.0/net48; это возможность сборки из исходников, НЕ опубликованный Rhino8 Yak и НЕ разрешение разрабатывать или устанавливать ПО.

## 7. Передача I4: точный вход, тесты, ворота
**Передать без новой разработки:** (1) G0 actual project path/port/PLN SHA, Tapir GetAddOnVersion/APX SHA/schema, GetStories index/floorId/level, attributes, Favorites существующим отдельным READ, library skippedCount, Rhino8/GC29/local PR74 commit; (2) после G0 один новый authored JSON по примеру PR74 с реальным targetProjectPath=RUN.EXPECTED_PATH, без выдуманных binding; (3) один --preflight с работающим AC29, только READ, новым output dir, без --execute; (4) plan hash/DAG/host dependencies, before/after GUID inventory, nativeWriteCalls=0 и SHA evidence; (5) G2 schema drift для Window/Door/Slab/Roof; (6) G3/G4/G5 только после отдельного допуска.

**Контрольные негативные тесты для будущего G1/G2:** T01 чужой project path → WRONG_PROJECT; T02 storyIndex из GH вместо GetStories → STORY_MISMATCH; T03 missing host Wall GUID → HOST_DRIFT_STOP; T04 duplicate scene_id/plan_hash → SCENE_ALREADY_RESERVED; T05 UNKNOWN после CreateSlabs до ModifySlabs → не повторять CREATE; T06 активный GH Design writer → SECOND_WRITER_STOP; T07 skippedCount>0 → LIBRARY_INVENTORY_PARTIAL; T08 попытка автономного offline authored → AUTHORED_NATIVE_REQUIRES_EXPLICIT_READ_ONLY_PREFLIGHT. Это **ожидаемые результаты спецификации**, тесты не запускались.

**Save/Open и QA:** G3 native GUID/type/story/host/material/BREP; G4 GuardedSave→Close→Reopen и независимый diff persisted model; G5 другое исходное здание. Отдельные verdict: GH_GEOMETRY, AC_NATIVE, IFC_STRUCTURE, IDS_INFORMATION, NORMATIVE_REVIEW. Ни GH BREP, ни IFC GlobalId не заменяют AC native GUID/тип. Ни одна проверка не объявлена PASS без runtime receipts.

## 8. Статусы и закрывающие блокеры
| Уровень/ворота | Фактическое состояние |
|---|---|
| SOURCE | A5/R1/R3/I4/предыдущий R2 и PR74 прочитаны; конфликтная матрица документирована |
| OFFLINE | 0 новых запусков; G1 не запускался |
| BUILD | 0 новых зданий |
| INSTALLED | NOT_VERIFIED, ноутбук недоступен |
| LIVE | 0 новых native calls; никаких установок/записей |
| ACCEPTED | 0 |
| NOT_FOUND | Только scoped GH adapter, Rhino8 Yak distribution, AC29 Rhino.Inside host, atomic rollback |
| G0/G1/G2/G3/G4/G5 | BLOCKED_RUNTIME / NOT_RUN / SOURCE_PARTIAL / NOT_AUTHORIZED / NOT_RUN / NOT_RUN |

**Открытые P0:** I4 получить фактический G0 manifest; после этого schema-valid fixture и G1 read-only preflight; R1 сверить локальные Tapir 1.5.10 schema/Favorites/library; A5 проверять квитанции, а не число отчётов. **R2 SOURCE-задача данного цикла закрыта**, но BUILD-01 по-прежнему STALLED_EXTERNAL_DEPENDENCY.

**Запреты:** main, исходники, PLN/APX, установки, LIVE, merge, платные API, Work/Codex/Arena не затрагивались. Изменение — только этот новый markdown-файл в исследовательской ветке. NEXT_RESEARCH_PRIORITIES.md не изменялся. MODEL_MODE_NOT_VERIFIABLE.
