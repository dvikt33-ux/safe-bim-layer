# APA Research OS — независимый аудит системы исследований, публикации и управления ветками

## Итог аудита

Главная проблема APA сейчас **не отсутствие ещё одного исследования**, а отсутствие гарантированного контура **«исследовал → сохранил → проверил сохранение → проиндексировал → передал следующему исполнителю»**. По репозиторию уже создана правильная основа: каноническая исследовательская ветка `research/apa-verified-results-hub-20261010`, draft PR #22, единый master plan, текущий статус, очередь, реестр артефактов, карта веток, протокол для агентов и шаблон исследования. PR #22 сейчас открыт, не слит в `main`, имеет 16 коммитов и 13 изменённых файлов. fileciteturn13file0L2-L13 fileciteturn13file0L32-L37

То есть **структуру начинать заново не надо**. Её надо довести до операционной системы проекта.

Текущая обязательная лестница уже правильно сформулирована:

> **ПЛАН → ДЕЙСТВИЕ → ТЕКУЩИЙ ПОДШАГ**

`MASTER_PLAN.md` требует стабильные ID вида `APA-P10.A02.S03`, причём один исследовательский запуск должен выполнять ровно один подшаг. Новая тема сначала должна появляться в плане, а не порождать очередную ветку. fileciteturn16file0L2-L2

`CURRENT_STATUS.md` уже служит единой точкой ответа на вопрос «что сейчас делается». Текущая лестница там:

**ПЛАН:** `APA-P00 — Восстановление и централизация`  
↳ **ДЕЙСТВИЕ:** `APA-P00.A03 — Режим работы и публикации`  
↳ ↳ **ТЕКУЩИЙ ПОДШАГ:** `APA-P00.A03.S01 — проверить реальный GitHub write/read у каждого исполнителя`. fileciteturn17file0L2-L2

Мой основной вывод после аудита:

**не надо строить «ещё один исследовательский бот». Надо построить APA Research OS, в котором GitHub является единственной долговременной памятью, а чат, Deep Research, Slack и будущие агенты являются только исполнителями.**

Сейчас это выполнено примерно наполовину:

| Компонент | Реальное состояние |
|---|---|
| Каноническая research-ветка | **ГОТОВО** |
| ПЛАН → ДЕЙСТВИЕ → ПОДШАГ | **ГОТОВО** |
| Единый CURRENT_STATUS | **ГОТОВО** |
| Очередь исследований | **ГОТОВО** |
| Реестр опубликованных материалов | **ГОТОВО** |
| Запрет хаотичных research-веток | **ГОТОВО** |
| Протокол `commit → readback` | **ГОТОВО как правило** |
| Полная инвентаризация старых веток | **НЕ ГОТОВО** |
| Автоматическая публикация каждого результата | **НЕ ГОТОВО** |
| Автономный publisher | **НЕ ГОТОВО** |
| 24/7 research runner | **НЕ ЗАПУЩЕН** |
| Автоматическое восстановление после сбоя | **НЕ ГОТОВО** |
| Deep Research → GitHub напрямую | **НЕВОЗМОЖНО текущим механизмом Deep Research** |
| Opera в этой сессии | **`NOT_VERIFIED — OPERA_NOT_CONNECTED`** |

Это соответствует и тому, что сам `CURRENT_STATUS.md` честно фиксирует: непрерывное исследование и автоматическая публикация не запущены, Deep Research → GitHub не подтверждён, а полный предыдущий Deep Research-отчёт не опубликован. fileciteturn17file0L2-L2

## Что уже правильно сделано на GitHub

Канонический центр сейчас находится в `docs/research/apa-results/` ветки `research/apa-verified-results-hub-20261010`. `README.md` прямо определяет эту папку как **единственное место публикации новых APA-исследований** и запрещает создавать новую research-ветку на каждый запуск. Он также указывает GitHub Issue #23 как постоянную точку входа. fileciteturn28file0L2-L2

Состав центра уже очень близок к тому, что ты описал:

| Файл | Роль |
|---|---|
| `README.md` | одна точка входа |
| `MASTER_PLAN.md` | полный план с P/A/S-ID |
| `CURRENT_STATUS.md` | что происходит прямо сейчас |
| `RESEARCH_QUEUE.md` | что выполнять дальше |
| `ARTIFACT_REGISTER.md` | что **реально** сохранено |
| `BRANCH_REGISTRY.md` | где и зачем находятся ветки |
| `AGENT_PROTOCOL.md` | инструкция каждому новому чату/агенту |
| `RESEARCH_TEMPLATE.md` | единая форма каждого исследования |
| `PUBLISHING_PROTOCOL.md` | правила commit/readback |
| `AUTOMATION_AND_GATES.md` | проект 24/7-контура |
| `CURRENT_BLOCKERS.md` | активные блокировки |
| `runs/...` | отдельные неизменяемые результаты исследований |

`AGENT_PROTOCOL.md` особенно важен: любой новый исполнитель обязан сначала прочитать контрольные документы, выбрать ровно один `APA-PXX.AYY.SZZ`, показать лестницу ПЛАН → ДЕЙСТВИЕ → ПОДШАГ, выполнить работу, записать результат в `runs/`, получить SHA коммита, прочитать файл обратно через GitHub и только после этого говорить `SAVED_TO_GITHUB`. fileciteturn25file0L2-L2

Это именно то правило, которого раньше не хватало.

`RESEARCH_TEMPLATE.md` уже задаёт правильный формат отдельного прохода: `RUN_ID`, P/A/S, входное состояние, исполнитель, версии Archicad/SDK/Tapir, source SHA, таблицу claims, точные доказательства, статусы `SOURCE_VERIFIED / REPORTED / NOT_VERIFIED / TEST_REQUIRED`, процедуру проверки и отдельный блок публикации с branch/path/commit/readback. fileciteturn26file0L2-L2

`ARTIFACT_REGISTER.md` также решает важнейшую проблему ложного ощущения, что «раз где-то это обсуждали — значит сохранено». Он разделяет **«файл найден и прочитан»** и **«его техническое утверждение независимо подтверждено»**. В нём отдельно зафиксировано, что полный предыдущий Deep Research результат не найден среди проверенных GitHub-артефактов, а непушенные локальные файлы остаются `LOCAL_ACCESS_REQUIRED`. fileciteturn27file0L2-L2

Это всё **оставить**.

Проблема начинается дальше: существующая система пока слишком сильно полагается на дисциплину исполнителя.

## Где система всё ещё ломается

Первый серьёзный разрыв — **веточная структура всё ещё фактически значительно сложнее, чем её канонический реестр**.

`BRANCH_REGISTRY.md` сам честно предупреждает, что это «не полный git-forensic audit всех refs». fileciteturn22file0L2-L2

При отдельной инвентаризации через подключённый GitHub в этой сессии я получил **72 ветки**. По префиксам они распределены примерно так:

| Семейство | Количество |
|---|---:|
| `chatgpt/*` | 19 |
| `work/*` | 16 |
| `research/*` | 11 |
| `arena/*` | 8 |
| `feature/*` | 7 |
| `audit/*` | 4 |
| `prototype/*` | 3 |
| `docs/*` | 1 |
| без группового префикса | 3 |
| **Всего** | **72** |

Поэтому твоя субъективная проблема «непонятно, где какие ветки, что к чему относится» абсолютно соответствует фактическому состоянию репозитория.

При этом **сейчас ничего удалять нельзя**. Сначала для каждой ветки надо получить:

`branch → head SHA → base/ancestry → PR → назначение → уникальные артефакты → что уже superseded → что нужно сохранить → окончательная классификация`.

Только после этого ветку можно переводить в `ARCHIVE`, закрывать связанный PR или предлагать удаление.

Второй разрыв — **текущая публикационная транзакция слишком хрупкая**.

Существующий `PUBLISHING_PROTOCOL.md` требует последовательно:

`отчёт → commit → readback → ARTIFACT_REGISTER → RESEARCH_QUEUE → CURRENT_STATUS`. fileciteturn20file0L2-L2

Логически это правильно. Технически есть опасность:

1. отчёт успел сохраниться;
2. `ARTIFACT_REGISTER` обновился;
3. `CURRENT_STATUS` не обновился из-за сбоя;
4. следующий чат получает противоречивое состояние.

То есть сейчас несколько Markdown-файлов одновременно являются mutable state.

**Я бы изменил архитектуру здесь.**

Единственным первичным состоянием должен стать **append-only журнал событий/запусков**. `CURRENT_STATUS`, `RESEARCH_QUEUE`, `ARTIFACT_REGISTER` и `BRANCH_REGISTRY` должны в конечном счёте быть **проекциями**, которые можно автоматически восстановить из первичных immutable records.

Третий разрыв — PR #21 решает только часть задачи.

Я прочитал не только описание PR #21, но и код `coordinator.py`, `step_sync.py`, `socket_mode.py`. Координатор уже реализует полезные механизмы: структурированный `APA_EVENT_V1`, уникальные `event_id`, SQLite-журнал, разделение `SOURCE/OFFLINE/SYNTHETIC/BUILD/LIVE`, конфликтные состояния и `supersedes`; локальный API предоставляет `/health`, `/v1/state`, `/v1/changes`, `/v1/wait`. fileciteturn8file0L2-L2

`step_sync.py` умеет читать сообщения Slack, преобразовывать их в события и имеет явный publish-gate; `socket_mode.py` рассчитан на Slack Socket Mode с отдельными bot/app tokens и локальным API. fileciteturn9file0L2-L2 fileciteturn10file0L2-L2

Но PR #21 **не является исследовательским агентом и не является GitHub publisher**. Он — event/conflict ledger и транспорт.

Его не надо выбрасывать. Из него надо **взять алгоритмы**:

**взять алгоритм / интегрировать**, а не «взять целиком как готовое решение 24/7».

Четвёртый разрыв — **в этой конкретной сессии подключённый GitHub даёт мне чтение, поиск, diff, PR/issue/branch/commit inspection, но не предоставляет action `create/update/push`**. Поэтому я могу проверить репозиторий, но не могу честно сказать, что этот отчёт сейчас закоммичен. Это должно трактоваться ровно так, как предписывает ваш же протокол:

**`GITHUB_PUBLISH_BLOCKED — WRITE_ACTION_NOT_EXPOSED_IN_CURRENT_SESSION`**.

Opera я тоже проверил. Connector ответил, что браузер не подключён. Следовательно:

**`NOT_VERIFIED — OPERA_NOT_CONNECTED`**.

Я не использовал содержимое якобы открытых в Opera страниц как доказательство.

## Целевая архитектура APA Research OS

Я сравнил четыре варианта.

| Архитектура | Сохранность | 24/7 | Сложность | Зависимость от ручной работы | Вердикт |
|---|---:|---:|---:|---:|---|
| Только Markdown + дисциплина чатов | средняя | нет | низкая | высокая | **оставить как базу, недостаточно** |
| GitHub-only automation | высокая | частично | средняя | средняя | **интегрировать для housekeeping** |
| ChatGPT → Slack → PR #21 → publisher | высокая | потенциально | средне-высокая | низкая после настройки | **резервный транспорт** |
| Разделённый Research / Publish / Control plane | максимальная | потенциально да | средняя | минимальная | **ВЫБРАТЬ** |

Рекомендуемая архитектура состоит из трёх независимых контуров.

**Research plane** выполняет интеллектуальную работу: обычный ChatGPT, Deep Research, scheduled research tasks, конкретные технические исследования Archicad. Он **никогда не считается хранилищем**.

**Publish plane** ничего «не исследует». Его работа детерминирована:

```text
получить RUN_EVENT
        ↓
проверить схему
        ↓
проверить run_id / idempotency
        ↓
записать immutable report + manifest
        ↓
git commit
        ↓
прочитать файл обратно
        ↓
сравнить hash
        ↓
обновить производные индексы
        ↓
commit
        ↓
readback
        ↓
PUBLISHED_VERIFIED
```

**Control plane** показывает человеку и любому следующему агенту текущее состояние:

```text
Issue #23
   ↓
CURRENT_STATUS
   ↓
PLAN → ACTION → SUBSTEP
   ↓
последний VERIFIED run
   ↓
следующий разрешённый S-ID
```

Это означает, что чат больше **не должен решать, куда положить результат**. Путь вычисляется автоматически из ID:

```text
APA-P10.A02.S04
        ↓
docs/research/apa-results/runs/2026-10-10/
        ↓
APA-RUN-20261010-.../
        ├── REPORT.md
        ├── manifest.json
        └── evidence.json
```

Я бы расширил существующую структуру так:

```text
docs/research/apa-results/
├── README.md
├── MASTER_PLAN.md
├── CURRENT_STATUS.md              # generated projection
├── RESEARCH_QUEUE.md              # generated projection
├── ARTIFACT_REGISTER.md           # generated projection
├── BRANCH_REGISTRY.md             # generated projection
│
├── protocol/
│   ├── AGENT_PROTOCOL.md
│   ├── PUBLISHING_PROTOCOL.md
│   ├── EVIDENCE_POLICY.md
│   └── RUN_EVENT_V2.schema.json
│
├── state/
│   ├── current.json
│   ├── queue.json
│   └── heartbeat.json
│
├── inventories/
│   ├── branches.json
│   ├── pull_requests.json
│   └── artifact-map.json
│
└── runs/
    └── YYYY-MM-DD/
        └── APA-RUN-.../
            ├── REPORT.md
            ├── manifest.json
            └── evidence.json
```

### Ключевое изменение — `RUN_EVENT_V2`

Вместо нескольких свободно интерпретируемых сообщений каждый проход должен выдавать один объект примерно такого вида:

```json
{
  "schema": "APA_RUN_EVENT_V2",
  "run_id": "APA-RUN-20261010-143001-sdk-create",
  "plan_id": "APA-P10",
  "action_id": "APA-P10.A01",
  "substep_id": "APA-P10.A01.S01",

  "executor": "chatgpt",
  "phase": "SOURCE",
  "status": "EVIDENCE_READY",

  "started_at": "2026-10-10T11:00:00Z",
  "finished_at": "2026-10-10T11:30:01Z",

  "scope": {
    "archicad": "29",
    "sdk": "29.x",
    "repository": "dvikt33-ux/safe-bim-layer"
  },

  "inputs": [],
  "claims": [],
  "evidence": [],

  "files_to_publish": [
    "REPORT.md"
  ],

  "next_substep": "APA-P10.A01.S02",

  "safety": {
    "main_modified": false,
    "pln_modified": false,
    "apx_modified": false
  }
}
```

Идемпотентность должна определяться минимум через:

```text
substep_id
+ source revision/SHA
+ evidence fingerprint
+ executor run ID
```

Повторный запуск с теми же входами не должен создавать пять одинаковых Markdown-файлов.

### Состояния

Я бы унифицировал статусы до следующего автомата:

```text
QUEUED
  ↓
CLAIMED
  ↓
RUNNING
  ↓
EVIDENCE_READY
  ↓
PUBLISHING
  ↓
COMMITTED
  ↓
READBACK_VERIFIED
  ↓
INDEXED
  ↓
DONE_PUBLISHED
```

Отдельные terminal/error:

```text
NOT_VERIFIED
DOCUMENT_NOT_READ
SOURCE_UNAVAILABLE
CONFLICT
BLOCKED_EXTERNAL
GITHUB_PUBLISH_BLOCKED
PUBLISH_READBACK_FAILED
RUNNER_OFFLINE
SUPERSEDED
```

Главное правило:

**`EVIDENCE_READY ≠ DONE_PUBLISHED`.**

А значит ситуация «исследование уже сделано, но потом ответ пропал» больше не должна уничтожать информацию: либо имеется `COMMITTED/READBACK_VERIFIED`, либо система прямо показывает, что публикация не состоялась.

## Как должны выглядеть ветки и коммиты

Существующее решение сделать `research/apa-verified-results-hub-20261010` одной канонической веткой правильное. `BRANCH_REGISTRY.md` уже запрещает новые research-ветки по умолчанию и допускает новую ветку только для отдельного изменения кода, опасного эксперимента или независимой сборки. fileciteturn22file0L2-L2

Это правило надо ужесточить до следующей модели.

**`main`** — защищённая основная линия. Никаких автоматических research-коммитов.

**`research/apa-verified-results-hub-20261010`** — единственная долговременная ветка исследовательских документов и состояния.

**Новые code branches** — только когда реально меняется код:

```text
feature/<task-id>-<slug>
fix/<task-id>-<slug>
experiment/<task-id>-<slug>
```

Никаких новых:

```text
research/random-topic-date
chatgpt/random-topic
audit/random-topic
```

для обычного исследования.

Новые исследования становятся **run-файлами**, а не ветками.

Старые 71 неканонические ветки сейчас не удалять. Сначала полный forensic inventory.

Минимальная строка для каждой:

| Поле | Пример |
|---|---|
| branch | `research/...` |
| head_sha | exact SHA |
| last_commit | timestamp |
| open_pr | `#20` |
| base | exact ref |
| class | CODE / RESEARCH / ARCHIVE |
| unique_artifacts | paths |
| superseded_by | branch/run |
| evidence_migrated | yes/no |
| recommendation | KEEP / FREEZE / CLOSE_PR / DELETE_LATER |
| deletion_authorized | **NO** |

После этого получится не 72 «непонятных ветки», а, например:

```text
1 MAIN
1 CANONICAL_RESEARCH
N ACTIVE_CODE
N WAITING_TEST
N ARCHIVE_READ_ONLY
N SUPERSEDED_CANDIDATE
```

То же с коммитами.

Каждый исследовательский commit:

```text
research(APA-P10.A02.S04): verify AC29 MEP route API
```

Каждый status commit:

```text
ops(APA): rebuild research indexes after APA-RUN-...
```

Никаких `update`, `fix stuff`, `research new` и подобных неидентифицируемых сообщений.

Issue #23 уже можно считать постоянным **APA Control Center**: он ссылается на master plan, status, queue, artifact register, branch registry и explicitly запрещает закрытие до полной инвентаризации, публикации потерянного Deep Research результата и доказанного 24/7-контура. fileciteturn24file0L2-L2

## Круглосуточное исследование: что реально возможно

Здесь есть один крайне важный новый подтверждённый вывод.

**Deep Research нельзя использовать как механизм автоматической GitHub-публикации.**

Текущая документация OpenAI прямо говорит: Deep Research может использовать connected apps как источники, но использует **read actions** и **не использует write actions** во время исследования. citeturn18view0

Следовательно архитектура:

```text
Deep Research
    ↓
GitHub commit
```

сама по себе **не существует**.

Это объясняет, почему идея «пусть Deep Research закончил — значит результат уже в GitHub» принципиально ненадёжна.

Более того, OpenAI указывает, что Deep Research-результаты подчиняются retention самого разговора и при удалении чата связанный Deep Research output также удаляется. Отчёты можно скачивать как Markdown, Word или PDF. citeturn18view0

Поэтому для APA:

**чат/Deep Research — вычислительная среда, GitHub — память. Никогда наоборот.**

Scheduled Tasks подходят лучше для непрерывной разведки: OpenAI сейчас поддерживает одноразовые и повторяющиеся задачи; на подходящих платных планах доступны hourly schedules. Они также могут использовать поддерживаемые connected apps, включая GitHub. citeturn18view1

Но есть второе ограничение: если connected-app действие меняет внешние данные, оно **может потребовать approval**, и тогда Scheduled Task приостанавливается до подтверждения человеком. citeturn18view1

Поэтому нельзя честно назвать Scheduled Task + обычный GitHub connector гарантированно автономным publisher.

Кроме того, webhook/event-triggered GitHub tasks, например по PR activity, OpenAI сейчас привязывает к **Work**. citeturn18view2 Поскольку ты отдельно запретил Work, этот маршрут для APA исключается.

Есть ещё один интересный путь — **GitHub MCP Server**.

Я прочитал официальный репозиторий `github/github-mcp-server`. GitHub позиционирует его как MCP server, способный не только читать репозитории, но и управлять issues/PR и workflows. fileciteturn30file0L2-L6

В исходниках/документации присутствуют реальные write-tools:

- `create_or_update_file`
- `push_files`

причём `push_files` предназначен для отправки нескольких файлов одним коммитом. Для write-операций документация указывает OAuth scopes `repo` / `workflow`. fileciteturn31file1L19-L28 fileciteturn31file3L48-L57 fileciteturn31file4L64-L76

**Это потенциально очень полезный готовый компонент publisher — не надо самим писать весь слой GitHub API.**

Но это пока не решение «включить сейчас»:

OpenAI указывает, что полный MCP с modify/write actions находится в beta и сейчас относится к ChatGPT Business, Enterprise и Edu. citeturn18view3

И главное — даже наличие write-capable MCP не меняет правило самого Deep Research: Deep Research всё равно не использует connected-app write actions. citeturn18view0

Поэтому техническое решение по инструментам выглядит так:

| Инструмент | Решение |
|---|---|
| Deep Research | **ИНТЕГРИРОВАТЬ как глубокого исследователя** |
| Обычный ChatGPT | **ИНТЕГРИРОВАТЬ как исследователя/координатора** |
| Scheduled Tasks | **ИНТЕГРИРОВАТЬ для периодической разведки** |
| Текущий GitHub connector | **ИСПОЛЬЗОВАТЬ для чтения/аудита; write проверять каждый сеанс** |
| GitHub MCP Server | **ИСПОЛЬЗОВАТЬ АЛГОРИТМ / кандидат publisher** |
| PR #21 coordinator | **ИСПОЛЬЗОВАТЬ АЛГОРИТМ + расширить** |
| Slack | **только транспорт/уведомления, не source of truth** |
| Opera | **NOT_VERIFIED — сейчас disconnected** |
| GitHub Actions | **только deterministic housekeeping, не исследователь** |
| Work | **ОТКЛОНИТЬ по требованию** |
| Codex | **ОТКЛОНИТЬ по требованию** |
| платный OpenAI API | **ОТКЛОНИТЬ по требованию** |
| сторонние платные LLM | **ОТКЛОНИТЬ** |

Отсюда честный статус настоящего режима 24/7:

> **`BLOCKED_EXTERNAL`: пока нет одного подтверждённого unattended write-канала между Scheduled Research и GitHub Publisher, обещать полностью автономное «исследует + пушит 24/7» нельзя.**

Но **систематизацию, сохранение, восстановление, дедупликацию и отсутствие хаоса можно решить уже независимо от этого**.

## Кратчайший план перехода к нормальной системе

Главное — не продолжать сейчас плодить новые исследовательские направления. Сначала завершить `APA-P00`.

### Немедленный приоритет

**ПЛАН:** `APA-P00 — Восстановление и централизация`  
↳ **ДЕЙСТВИЕ:** `APA-P00.A01 — Инвентаризация фактически опубликованного`  
↳ ↳ **ПОДШАГ:** `APA-P00.A01.S03 — полный forensic inventory веток/PR/commits/artifacts`

Это уже стоит в master plan как `QUEUED`. fileciteturn16file0L2-L2

На выходе должен появиться:

```text
FULL_BRANCH_INVENTORY.md
FULL_BRANCH_INVENTORY.json
```

со всеми 72 ветками, а не выборочный список.

После этого:

**`APA-P00.A02.S03`** — дедупликация старых результатов. Один факт = один canonical claim ID; старые отчёты остаются evidence, а не копируются десятки раз.

Затем:

**`APA-P00.A03.S01`** — закончить capability matrix исполнителей:

```text
Executor              READ     RESEARCH    WRITE    READBACK    SCHEDULED
ChatGPT current        PASS     PASS        BLOCKED  PASS        N/A
Deep Research          PASS     PASS        NO*      N/A         manual
Scheduled task         ?        PASS        ?        ?           PASS
GitHub MCP publisher   PASS     N/A         CAPABLE  CAPABLE     external
PR21 coordinator       Slack    NO          NO Git   local       daemon
```

`* Deep Research write через connected apps запрещён самим продуктовым контрактом.` citeturn18view0

Дальше вместо расширения нынешней цепочки ручных Markdown-обновлений:

**`APA-P00.A03.S03`** должен стать реализацией `RUN_EVENT_V2 + Publisher + Index Builder`.

Порядок публикации:

```text
REPORT CREATED
      ↓
IMMUTABLE RUN SAVED
      ↓
COMMIT SHA
      ↓
READBACK + HASH
      ↓
INDEX REBUILD
      ↓
SECOND READBACK
      ↓
DONE_PUBLISHED
```

Если процесс падает после первого commit:

```text
report НЕ потерян
→ index builder позже обнаружит неиндексированный run
→ восстановит CURRENT_STATUS / REGISTER / QUEUE
```

Это принципиально лучше существующей схемы, где исполнитель обязан вручную правильно обновить три разных mutable документа.

После этого провести требуемый самим master plan тест:

**два последовательных полностью автоматизированных цикла**:

```text
research
→ report
→ commit
→ readback
→ index
→ next task
```

Только после двух проходов — разрешать `P00.A03.S04 = DONE`.

И лишь затем `APA-P40`:

```text
hourly scheduler
→ RUNNING heartbeat
→ research lane
→ publisher
→ verified commit
→ next_run
```

Успех 24/7 определяется **не тем, что где-то существует scheduled task**, а реальным журналом:

```text
timestamp
run_id
S-ID
source revision
outcome
report commit
index commit
readback hash
next_run
```

и watchdog:

```text
now - last_heartbeat > allowed_interval
→ RUNNER_OFFLINE
```

### Как должны выглядеть будущие исследовательские проходы

С этого момента каждый проход должен буквально начинаться так:

```text
ПЛАН
APA-P10 — Независимый технический аудит Archicad 29

└─ ДЕЙСТВИЕ
   APA-P10.A02 — Инструменты и интеграции

   └─ ТЕКУЩИЙ ПОДШАГ
      APA-P10.A02.S04 — Native MEP / Tapir MEP
```

И заканчиваться не сочинением на две страницы о проделанной работе, а машинно проверяемым receipt:

```text
STATUS: DONE_PUBLISHED

RUN:
APA-RUN-20261010-...

GITHUB:
branch: research/apa-verified-results-hub-20261010
path: docs/research/apa-results/runs/...
commit: <sha>
readback: VERIFIED
content_hash: <sha256>

CLAIMS:
3 SOURCE_VERIFIED
1 TEST_REQUIRED
2 NOT_VERIFIED

NEXT:
APA-P10.A02.S04.<next>
```

Если SHA нет:

```text
STATUS: GITHUB_PUBLISH_BLOCKED
```

и **никакого `DONE`**.

Это должно стать фундаментальным инвариантом APA.

## Что считать окончательным решением

Архитектурный выбор после аудита:

**выбрать Split-Plane APA Research OS.**

Не заменять существующий PR #22. **PR #22 должен стать фундаментом.**

Не переписывать PR #21. **Из него использовать event schema, idempotency, append-only ledger, конфликтную модель и `supersedes`.**

Не пытаться заставить Deep Research напрямую пушить результаты. Это противоречит текущей документации OpenAI: Deep Research использует connected apps только для read actions. citeturn18view0

Не делать Slack хранилищем.

Не создавать research-ветку на каждое исследование.

Не удалять существующие 72 ветки до forensic inventory.

Не заставлять тебя вручную определять «что из трёх чатов куда запушить».

Конечная модель должна быть такой:

```text
                   APA MASTER PLAN
                         │
                         ▼
                    RESEARCH QUEUE
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        ChatGPT Research       Deep Research
              │                     │
              └──────────┬──────────┘
                         ▼
                  APA_RUN_EVENT_V2
                         │
                         ▼
              DETERMINISTIC PUBLISHER
                         │
                         ▼
                    GITHUB COMMIT
                         │
                         ▼
                       READBACK
                         │
                         ▼
               IMMUTABLE RUN STORE
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
   CURRENT_STATUS  ARTIFACT_REGISTER  RESEARCH_QUEUE
          │              │               │
          └──────────────┼───────────────┘
                         ▼
                 ISSUE #23 / DASHBOARD
```

Исследователь может исчезнуть. Чат может сломаться. Ответ может пропасть из UI. Slack может быть недоступен. Другой агент может прийти через неделю.

**Система при этом не должна потерять ни одного результата, потому что состояние APA находится не в голове агента и не в истории чата, а в проверенном Git-коммите.**

На текущий момент канонический hub, master plan и протокол уже существуют и прочитаны. fileciteturn28file0L2-L2 `RESEARCH_QUEUE.md` уже ставит полную инвентаризацию, дедупликацию, AC29 SDK, Tapir, GDL, MEP, архитектурное сравнение и MVP в единую очередь. fileciteturn23file0L2-L2

**Текущий операционный статус этого исследования:** `GITHUB_PUBLISH_BLOCKED — WRITE_ACTION_NOT_EXPOSED_IN_CURRENT_SESSION`. Поэтому я не утверждаю, что этот новый аудит закоммичен. Уже существующая система управления находится в GitHub и подтверждена readback; именно её нужно продолжать, а не создавать ещё одну ветку или ещё один параллельный план.