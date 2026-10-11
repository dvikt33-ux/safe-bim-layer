# APA — инженерный план доведения ускорителя до рабочего продукта

**Дата среза:** 2026-10-11. **Тип:** предлагаемый delivery-roadmap на базе существующего реестра, **не второй диспетчер задач**.  
**Единый источник выполнения/статусов:** [PROJECT_PLAN.json](PROJECT_PLAN.json), revision 44 на момент подготовки.  
**Связанные задачи:** APA-P70.A01.S01 (сопоставление исходников), APA-P70.A01.S03 (границы интеграции), APA-P70.A02–A08, APA-P30.A02, APA-P50.A02.S01.  
**Статус документа:** PROPOSED_FOR_INDEPENDENT_AUDIT. **Никаких заданий не CLAIMED/IN_PROGRESS/DONE этим документом; PROJECT_PLAN.json не изменён.** После независимого аудита критерии и приоритеты должны быть внесены в существующие S-ID посредством контроллера с CAS/lease/readback. Только при доказанном отсутствии S-ID — TASK_PROPOSAL → TASK_REVIEW → изменение реестра.

## 0. Финишная цель и границы

APA — **один локальный исполняемый ускоритель Archicad 29**, управляемый пользовательским техническим заданием и в перспективе из обычного ChatGPT, без ручного ввода GUID/хешей/PowerShell для каждой стены. Два полноценных режима: **GENERATE_FROM_ZERO** (новый проект) и **ADAPT_EXISTING** (только единственный открытый PLN; без сканирования/переключения других PLN). Сначала минимально рабочая редактируемая модель, затем архитектурная комплектация, расчёты, MEP, нормативное сопровождение и выпуск проекта. Архитектурная метрика первого этажа — **«1 этаж» на ±0,000**, native `floorIndex` определяется только `GetStories`/StorySettings; не вводить фиктивный «0 этаж». Не расширять на Archicad 30 до стабильности 29.

**KPI конечного продукта:** время человека от принятого задания до согласованного полного набора BIM/IFC/PDF, включая изменения и инженерную обратную связь. Отдельные показатели: время до первого редактируемого здания, % verified native elements, число ручных CLI-действий, минуты на правку, число дубликатов/неопределённых записей, число незакрытых нормативных/инженерных пунктов. **Не выдумывать ускорение:** benchmark только на одном оборудовании и сопоставимом baseline, минимум 5 прогонов, с разбросом.

**Модель качества:** `SOURCE_VERIFIED` ≠ `OFFLINE_PASS` ≠ `LIVE_READBACK_PASS` ≠ `SAVED_REOPENED_PASS` ≠ `ENGINEERING_PASS` ≠ `RELEASE_PASS`. Каждый gate публикует доказательства отдельно. Нет требования полной нормативной базы для первого рабочего BIM, но «готов к строительству» без проверенных норм/расчётов запрещено.

## 1. Что уже есть и что НЕ подтверждено

| Направление | Фактически есть | Дефицит до продукта |
|---|---|---|
| Единый intent/controller | PR #16: `archicad_project_accelerator.py`, capability registry; PR #34: `building-shell-v1`, 10×8 м, 2 этажа, 25 операций | General/live multi-story execution; контракт произвольных помещений, материал/конструкции, надёжная модификация |
| Единая BIM DAG | `archicad_bim_graph.py`, зависимые GUID, hosted openings и схемная проверка | Семантика конструктивных систем, spatial collision в реальном проекте, стабильная повторная компиляция |
| Единственный writer | `archicad_scene_run.py`, SQLite intent-before-write, exact PLN guard, typed native readback | Включить адаптеры имеющихся возможностей, типизированные композиции, **resume/reconcile** вместо нового полного Create |
| Писатели и атрибуты | `archicad_executor.py` CreateSlabs→ModifySlabs(Basic), `archicad_template_builder.py` разрешение материалов, прежние Wall/Slab/Window/Roof/Morph cycles | Подключить к тому же writer (не делать второй); межтиповые проверки и одинаковая модель ошибок |
| LIVE fixed pavilion | 12/12 GUID/readback из user-supplied API JSON, пользователь подтвердил Save As → close → reopen; специальный test PLN | Не доказана универсальность; не повторять тест или не превращать его в продукт |
| LIVE PR #34 | 108/108 CI (по описанию PR), scratch PLN port 19726: 4 walls PASS, slab GUID создался, но 0.2 м → Composite 0.3 м; последующие операции не выполнялись | Сначала typed slab/recovery; полный live building 25/25 отсутствует |
| Прикладные данные | CSE/PLP/узлы v2.12, MEP инструменты доступны пользователю вручную, нормативные исследования | Ни список узлов, ни MEP UI не доказывают подключение к GPT или пригодность проекта |
| Control/Research OS | `PROJECT_PLAN.json` rev44: 74 tasks; 10 DONE_PUBLISHED, 15 PARTIAL, 8 BLOCKED, 41 READY; publisher push-triggered, задачи Scheduled `CONFIGURED_UNVERIFIED` | Нет подтверждённого непрерывного autonomous 24/7 выполнения; не ставить инфраструктуру выше архитектурного MVP |

**Иерархия приоритета:** рабочий вертикальный срез → расширяемое здание → контроль изменений → управление GPT → конструктив/инженерия/выпуск. Никакие 106/108 offline tests или 25 операций PR #34 не равнозначны live-ready проекту.

## 2. Архитектура, которую сохраняем

```text
ChatGPT / локальная форма (позднее direct GPT transport)
   ↓ техническое задание с версией/явным проектом
Project Accelerator: нормализация intent, проверка требований
   ↓
Project-scoped resolver: GetStories + BM/Composite/Favorite/Profile + CSE/PLP
   ↓
Один BIM Graph: зависимости, host, story, расположение, порядок
   ↓
Один SceneWriter / native executor: guarded target → WAL/SQLite state journal
   ↓
Tapir 1.5.10 и при необходимости существующий native AC29 Add-On
   ↓
GUID + геометрия + материал + этаж + связи → typed readback / reconciliation
   ↓
Результат, проверенные отчёты и приватное локальное состояние
```

**Никаких** второго диспетчера, второго графа или автономного альтернативного писателя. `archicad_executor.py` и Template Builder — доноры функций/малых адаптеров для существующего графа/SceneWriter. Локальный bridge работает лишь с разрешённым открытым файлом. GitHub — исходники, tests, source-safe evidence и реестр; **не** публичное хранилище секретов, полного PLN и персональных данных.

**Граница безопасности:** запросы native API к localhost не становятся доступными ChatGPT автоматически. До проверенного защищённого транспорта «управление из GPT» означает ChatGPT→валидируемый intent→локальный исполнитель, а не недоказанный прямой доступ к компьютеру. UI может скрыть команды; на доверенной стороне остаётся авторизация изменения PLN, верификация, журнал и no-replay.

## 3. Рабочие этапы, порядок и критерии ГОТОВО

### D0. Зафиксировать рабочую базу и объединить code paths — P70.A01.S01 → S03

**Объём:** source/SHA/PR16/PR34/Native MVP/Template Builder, фактические capabilities, лицензии и ограничения. Привязать existing code к единственной точке входа и выделить отсутствующие тонкие адаптеры. Исторические 70+ веток — использовать по найденным уникальным способностям; полная археология веток не должна блокировать доказанный вертикальный срез.

**Deliverable:** карта entrypoint→resolver→BIM graph→writer→native calls→readback, матрица CODE_EXISTS / OFFLINE_PASS / LIVE_PASS / BLOCKED, назначенные владельцы конкретных адаптеров, список только реальных пробелов. Утверждённый «запрет на параллельный executor».  
**ГОТОВО:** ни один создаваемый элемент не идёт по незарегистрированному второму writer; fixtures и исходные SHA воспроизводимы, CI PASS, технический аудитор принял карту.

### D1. Исправить типизированные конструкции и восстановление сцен — P70.A03.S02/S03, P30.A02.S01/S02 (в рамках зависимостей)

**Вход:** известная **двойная** ошибка на двух disposable проектах: `CreateSlabs(thickness=0.2)` фактически создаёт `Composite 0.3`. PR #34 scratch scene и старый pavilion — разные PLN/сцены; pavilion уже восстановлен и readback PASS; scratch PR #34 остаётся PARTIAL.

**Реализация:**
1. До записи разрешить проектный BM/Composite/Favorite GUID и semantic role. Composite — толщина из реально проверенных skin/layers; Basic — 0.2 м только при явно подтверждённом Basic + BM. Без неизвестных «дефолтов».
2. Для Tapir 1.5.10 использовать уже существующий `CreateSlabs → ModifySlabs(structureType=Basic,buildingMaterialId,thickness)` **с сохранением неатомарности**. Состояния в SQLite до каждого native call: PREPARED/ATTEMPTED/NATIVE_SUCCESS_UNVERIFIED/READBACK_PASS/BLOCKED. Любая неоднозначность → STOP + manual reconciliation, никакого повторного Create.
3. Привязать существующие четыре стены и slab по GUID из журнала; по изменённому slab использовать отдельный operation journal и one-off authorization. Подтвердить тип, толщину, Z/bbox, polygon, story/material; только затем создаются **не созданные** dependents. Никакого удаления существующих GUID и общего рестарта.
4. Отрицательные тесты: incorrect PLN/port/story/material, Composite вместо Basic, partial native write, loss of response, duplicate hash, invalid polygons, stale journal, repeated run. Проверить сохранение GUID и восстановление после процесса.
5. Устранить схожие default-attribute сюрпризы для Wall/Column/Roof, не переписывая архитектуру.

**ГОТОВО:** disposable multi-storey scene имеет planned=actual `structureType/thickness/material/story/host` для всех созданных GUID, 0 непроверенных записей по завершённому сценарию, positive/negative tests и LIVE readback, сохранение/повторное открытие отдельного тестового PLN. Не выдавать `DONE`, если только локальный ZIP или offline tests.

### D2. Параметрическое редактируемое здание, одна модель — P70.A02.S01/S03 → P70.A03.S01/S02/S03

**MVP-ядро (без сползания к полной стройке):**
- Этажи: произвольное число в пределах явно поддерживаемого диапазона, базовый тест 2 этажа; этаж `1` на 0.000, `2` на +3, transport-native index из активного `GetStories`.
- Геометрия: заданные X/Y, высоты, толщина/тип стен, перекрытия, внутренние перегородки, колонны, hosted двери/окна. Длинная непрерывная стена остаётся одним Wall, не режется ради проёмов.
- Свойства: реальный Building Material / Composite и толщина каждого элемента, единицы SI, привязка этажей/homeStory, источник атрибута и названная конструкция; отсутствие атрибута = BLOCKED, а не silent fallback.
- Input: brief/schema `building-shell-v1` расширять, а не создавать второй generator; `GENERATE_FROM_ZERO` и `ADAPT_EXISTING` отличаются resolver-ом исходного состояния, но используют один граф/писатель.
- Контроль изменений: стабильные semantic object IDs → actual GUID; при изменении размеров обновляются затронутые объекты и зависимые проёмы, а не создаётся здание рядом. Защита от коллизий учитывает нативные 3D объекты и неизвестную геометрию.

**Контрольный учебный сценарий:** текст «2 этажа, 10×8 м, высота этажей 3 м, наружные стены 300 мм, указанные внутренние стены, 6 окон и 5 дверей» → deterministic compiled DAG → реальный PLN. Числа окон/дверей — конкретная проверочная конфигурация PR #34, а не универсальный шаблон архитектуры.

**ГОТОВО:** согласованная модель с проверенными GUID, story, bounding boxes, editable types, материальными атрибутами и хозяевами проёмов; 100% planned changed elements имеют readback. Затем изменение X 10→12 м и 1 окна: `diff` + readback, **без нового полного создания и без дублирующих GUID**. Save As → close → reopen → повторный readback. Полная инженерная пригодность пока НЕ заявляется.

### D3. Нормальное управление: сначала один клик, затем ChatGPT — P70.A03.S03, P60 tasks; отдельный transport gate

**Сейчас:** пользователь не должен проходить цикл «ZIP→CMD→GUID→hash→новый ZIP» для каждого элемента. Локальный `APA Runner` с простой командой `Build/Update/Inspect` и readable status (проект, preflight, операции, неизменённые объекты, частичные записи). Сохранять risk-gated подтверждение **один раз на ограниченную модель/операцию**, не на каждый GUID.

**Следом:** подобрать реально исполнимый транспорт `ChatGPT intent → локальный APA` с проверенными правами, а не предполагать, что облачный GPT напрямую вызывает localhost: через подходящий подтверждённый connector/локальный broker и **непубличную** очередь, подписанный job, scope в один PLN, audit trail, idempotent transaction key, consent. Возможность прямой записи через конкретный коннектор — `NOT_VERIFIED` до испытания. Существующий PR #21 Slack/Sync — исследовать как event plane, **не** автоматически приравнивать к безопасному командному каналу.

**ГОТОВО локально:** один пользовательский запрос и один осмысленный approval дают все необходимые native операции, итоговую сводку без ручной перепечатки кодов. **ГОТОВО GPT:** произнесённая в обычном чате команда создаёт typed intent, локальный runner получает её через проверенный разрешённый transport, выполняет и возвращает достоверный report. Никаких скрытых платных API и мнимого 24/7.

### D4. Довести архитектурную модель — P70.A04, P70.A02.S03

В той же BIM DAG подключить уже существующие Roof/Morph/Stair/Shell/cycles и части template/detail resolver, фундамент, стропильную/конструктивную схему, балки, лестницы, кровлю, узлы примыкания и окна/врезки. До выбора детали — применимость CSE/PLP, source/version/license, geometry/material compatibility. Реализовывать блоками **Roof/Slab → Stair/Foundation → Junctions** (порядок уточняется объективной зависимостью модели), не повторяя работающие Wall/Window tests.

**ГОТОВО:** как минимум один законченный геометрический вариант здания с крышей и конструктивными системами, natively editable, с фактическими примыканиями, materials/host/readback и без необоснованных пересечений; список недоказанных расчётов отдельно. Не называть это полноценным рабочим проектом.

### D5. Инженерные подсистемы и актуальные нормы — P70.A05/A06 и P70.A02.S02

**Структура:** SAM/SAF/IFC к проверенному доступному инженерному пакету. Проверить наличие/лицензию/версии; **не** писать собственный FEM вместо доступного solver. Reverse-sync исправлений и версионирование элементов.  
**MEP:** использовать подтверждённо рабочие у пользователя штатные MEP-инструменты AC29; отдельно доказать native API для труб/воздуховодов/оборудования/портов, network graph, проходки, коллизии, расчет. UI availability ≠ APA command coverage.  
**Нормы:** версии СП/ГОСТ, область применимости, источники, `PASS/FAIL/NOT_VERIFIED/NEEDS_SPECIALIST`, влияние редакций на пересчёт. Критическое нарушение блокирует соответствующий выпуск, но не ранний моделирующий MVP.

**ГОТОВО:** инженерные/MEP элементы обратимо связаны с единой моделью, есть provenance тестов/расчётов и `NEEDS_SPECIALIST` для неподтверждённых решений, нет ложных нормативных PASS.

### D6. Документация, выпуск и сквозная приёмка — P70.A07/A08

Из единой модели: native Views (планы, фасады, разрезы), спецификации, IFC/PDF, комплект стадий/разделов по проектной задаче; пересборка при изменении стен/окон/MEP; контроль количества/маркировок/revisions, сохранение PLN и повторное открытие (только по разрешению оператора). Полный контрольный цикл **новый проект** и **изменение открытого существующего проекта**, затем ещё один тип здания без форка исполнителя.

**ГОТОВО:** связный выпуск с поэлементным provenance и согласованными revision IDs, независимая проверка сохранённой/повторно открытой модели и доступных отчётов; инженерная/нормативная аттестация только при фактическом соответствующем gate.

## 4. Порядок работы по неделям / трудоёмкость

Это **рабочие итерации**, а не обещание календарных сроков. Неделя условно означает один рабочий цикл с review, PR, CI и, при наличии пользователя у Archicad, live witness. Если доступ к локальному PLN отсутствует, любой LIVE gate останавливается без фальсификации.

| Итерация | Непосредственный измеримый результат | Минимальный критерий |
|---|---|---|
| I0 — baseline / интеграция | Reuse map, консолидация PR #16/#34/Native MVP, один owner writer | Нет нового writer, PR + CI и readback source |
| I1 — slab/recovery | Сборка typed Basic/Composite и checkpoint resume в существующий SceneWriter | Original GUIDs preserved; slab 0.2 planned=actual, no replay |
| I2 — building live | 10×8 м, 2 этажа, 25-операционная shell-модель в disposable PLN | ALL steps native readback, сохранение и повторное открытие; не просто CI |
| I3 — update | Увеличение габарита и перенос проёма без пересоздания | Expected GUID mapping, no duplicates, journal replay rejection |
| I4 — пользовательский интерфейс | Один запуск Build/Update/Inspect; команда из GPT в переносимом typed-intent формате | Нет ручных команд на уровне элементов; транспорт только при проверке |
| I5+ — расширения | Roof/Foundation/Junctions → MEP/Engineering → Release | Покрытие нового native scope + отдельные отраслевые PASS |

Приоритет на ближайший результат: **I0 → I1 → I2**, а не новые массовые исследования, очереди или очередной павильон с теми же стенами. Исследование допустимо, когда у конкретного шага появился `BLOCKED` и есть чёткий вопрос (API/schema/attribute/contract).

## 5. Общая приёмка каждого шагa и диагностика ошибок

**Обязательные до native write:** указан единственный открытый PLN; `GetProjectInfo`, runtime/APX/Tapir version, `GetStories`, URI/путь identity, исходный scene intent hash, разрешение, 3D spatial bounds (неизвестные/невалидные bounds = BLOCKED), проверенные атрибуты, existing GUID/diff.  
**Запись:** исходный intent и unique operation ID durable committed **до** каждого call; этапы ATTEMPTED → GUID_Native_Returned → READBACK_PASS, но GUID alone не означает геометрическую верность. Не допускать blind retry.  
**Readback:** type, GUID, actual story level, geometry bbox and polygon, thickness/structureType, BM/Composite/Surface IDs, host wall and hole relationships; явно отметить 2D-only types/unsupported.  
**После:** actual vs planned diff, локальный сохранённый отчёт, GitHub source-safe report с PR/S-ID/source SHA/evidence classification, проверенный commit/readback. Явно: `PASS`, `PARTIAL`, `BLOCKED`, `NOT_VERIFIED`.  
**При сбое:** никаких повторных Create, смены PLN, тихого Undo или удаления. Восстановить по SQLite GUID + typed readback; создать **только отсутствующее**, изменять существующее только при authorization и доказанном diff.

## 6. Процесс задач, исследований и независимого аудита

1. **Source of truth `PROJECT_PLAN.json`**: P→A→S, зависимости, status, work_key; есть Controller, publisher, generated CONTROL_BOARD. Этот roadmap **не создаёт второй реестр** и не делает ни одну задачу IN_PROGRESS без CAS claim.
2. Любой исполнитель перед работой читает current HANDOFF/PLAN, claim-ит одну eligible задачу (для Scheduled через CAS), фиксирует S-ID. Не совершает незарегистрированную работу.
3. Каждое исследование начинается с поиска существующих исходников/отчётов, содержит узкий question/gap и проверяемое доказательство. Если обнаружено новое направление — `TASK_PROPOSAL_V1`; отдельный аудитор принимает `TASK_REVIEW_V1` в реестр после дедупликации.
4. **Build PR** из существующей codebase, CI, offline simulation и только затем user-authorized live. Не считать полноту CI доказательством работы Archicad.
5. Публикация source-safe findings, tests/report, commit SHA и GitHub API readback обязательна. Только затем аудитор закрывает S-ID. Нельзя «исследовать» без публикации.
6. Параллельно вести строго независимые ветки: **CORE** (slab+resume), **INTENT/STORIES+ATTRIBUTES**, **READBACK/QA**, **GPT/LOCAL-TRANSPORT feasibility**, **CSE/MEP/normative research**. Сводить только после прохождения общего interface contract, не создавать конкурирующие writer.
7. Запланированные ChatGPT Scheduled Tasks в реестре: `CONFIGURED_UNVERIFIED`, а не доказанная бесперебойная 24/7 система. Не объявлять работу выполненной по расписанию без commit/receipt/status transition.

## 7. Решения и ограничения

- **DEC-01:** Архитектура гибридная Python orchestrator + существующий AC29 Tapir/native Add-On; никакой второй исполнитель.
- **DEC-02:** Первый release target — Archicad 29; только после acceptance рассматривать 30.
- **DEC-03:** Первая готовая продуктовая поставка — **редактируемое параметрическое здание**, не стеновой smoke-test; полный проект — отдельные последующие gates.
- **DEC-04:** Геометрический Basic/Composite/Attribute resolver должен выбрать тип до записи и проверить после, без доверия к default favorites.
- **DEC-05:** GitHub research + delivery docs канонические; local journal/cache приватные; никакие токены/PLN в публичном репозитории.
- **DEC-06:** Отличать условную однократную тестовую запись от постоянного полномочия на любые проекты; право пользователя на disposable target не переносится автоматически на production PLN.
- **DEC-07:** Контроль моделей не строить на «количество элементов выросло». Доказательство — typed native GUID/readback/persistence.
- **DEC-08:** Интеграция GPT требует отдельно проверенной связности/permissions; нельзя считать GitHub или Slack event log локальным executor по умолчанию.

## 8. Где начать прямо сейчас (без новых массовых CLI-тестов)

**План:** APA-P70. **Первое управление:** APA-P70.A01.S01 → A01.S03 (с учётом зависимости).  
**Первый инженерный patch (после допуска по реестру):** в существующем codebase PR #34 (stacked on PR #16) интегрировать уже написанную `archicad_executor.py` typed slab strategy и раздельную journaled continuation; написать regression test на точно наблюдавшемся `Composite 0.3` при требовании `Basic 0.2`. Не исполнять старую scene повторно.  
**Первое продуктовое demo после patch:** новый однократно разрешённый disposable PLN, 2 этажа 10×8 м → создание, native readback, сохранение/переоткрытие, изменение одного размера/окна без дубликатов. Только тогда менять статус D2.

**Входные ссылки:**
- [PR #16 — existing integration](https://github.com/dvikt33-ux/safe-bim-layer/pull/16)
- [PR #34 — parametric two-storey shell and live partial](https://github.com/dvikt33-ux/safe-bim-layer/pull/34)
- [D0 existing assembly/reuse plan](APA_ASSEMBLY_INTEGRATION_PLAN.md)
- [Native anti-dup audit](../runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md)
- [Fixed pavilion persisted geometry evidence](../runs/2026-10-11/apa-p20-a02-s03-saved-pln-live-readback-20261010-222136.md)
- [PR #34 scratch native partial slab reconciliation](../runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md)
- [Full-cycle requirements](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
