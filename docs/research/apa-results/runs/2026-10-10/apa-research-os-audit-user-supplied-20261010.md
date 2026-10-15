# APA Research OS — независимый аудит системы исследований, публикации и управления ветками

**ПЛАН:** APA-P00 — восстановление и централизация.  
**ДЕЙСТВИЕ:** APA-P00.A03 — режим работы и публикации.  
**ПОДШАГ:** APA-P00.A03.S01 — матрица write/read исполнителей; смежные APA-P00.A01.S03, APA-P00.A02.S03 и APA-P00.A03.S03.  
**Происхождение:** текст аудита, **предоставленный владельцем 2026-10-10** (вложение «Вставленный текст.txt»).  
**Статус:** USER_SUPPLIED_REPORT / REPORTED. Этот файл фиксирует **содержательные выводы и технические предложения исходного текста**, а не повторную независимую верификацию всех его ссылок. В исходнике есть временные маркеры filecite/cite из другого сеанса; они не являются постоянными ссылками в GitHub. Прямые GitHub/официальные URL сохранены ниже.  
**Важно:** исходный аудит предлагал использовать Deep Research как необязательный research plane. **Приоритетная инструкция владельца** — исследования в обычных чатах ChatGPT с GitHub, Deep Research не запускать без отдельного разрешения. Историческое «GITHUB_PUBLISH_BLOCKED — WRITE_ACTION_NOT_EXPOSED_IN_CURRENT_SESSION» относится к сессии автора аудита, а **не** к текущему чату, где write/read доступен.

## 1. Главный вывод

Проблема APA — не отсутствие ещё одного исследования, а отсутствие гарантированного контура **исследовал → сохранил → проверил сохранение → проиндексировал → передал следующему исполнителю**.

Существующая основа правильная: canonical branch **research/apa-verified-results-hub-20261010**, draft [PR #22](https://github.com/dvikt33-ux/safe-bim-layer/pull/22), [Issue #23](https://github.com/dvikt33-ux/safe-bim-layer/issues/23), MASTER_PLAN, CURRENT_STATUS, RESEARCH_QUEUE, ARTIFACT_REGISTER, BRANCH_REGISTRY, AGENT_PROTOCOL, RESEARCH_TEMPLATE, PUBLISHING_PROTOCOL, AUTOMATION_AND_GATES, CURRENT_BLOCKERS, immutable runs. **Не создавать систему заново, не плодить research branches.**

Обязательная лестница: **ПЛАН → ДЕЙСТВИЕ → ТЕКУЩИЙ ПОДШАГ**, ID формата APA-P10.A02.S03; один исследовательский проход = один подшаг.

| Компонент | Состояние в исходном аудите |
| --- | --- |
| Canonical research branch, master plan, status, queue, register, branch policy | ГОТОВО |
| Правило commit → readback | ГОТОВО как протокол |
| Полная инвентаризация старых веток | НЕ ГОТОВО |
| Автоматическая публикация и автономный publisher | НЕ ГОТОВО |
| 24/7 research runner и восстановление после сбоя | НЕ ЗАПУЩЕНО |
| Deep Research → GitHub write | Не поддерживается как прямой путь |
| Opera в исходной сессии | NOT_VERIFIED — OPERA_NOT_CONNECTED |

## 2. Существующая система: сохранить, не переписывать

- README — точка входа; MASTER_PLAN — стабильные P/A/S-ID; CURRENT_STATUS — текущее исполнение; RESEARCH_QUEUE — следующие задачи.
- ARTIFACT_REGISTER отличает «файл найден/прочитан» от «утверждение независимо проверено»; BRANCH_REGISTRY — назначение веток.
- AGENT_PROTOCOL — каждый исполнитель читает план/статус/реестр, выбирает один S-ID, пишет отчёт, получает commit SHA, выполняет GitHub readback, затем сообщает SAVED_TO_GITHUB.
- RESEARCH_TEMPLATE — RUN_ID, среда, версии Archicad/SDK/Tapir, source SHA, claims, evidence, SOURCE_VERIFIED/REPORTED/NOT_VERIFIED/TEST_REQUIRED, процедура тестирования, branch/path/commit/readback.
- PUBLISHING_PROTOCOL — отчёт → commit → readback → реестр → очередь → статус.
- runs/YYYY-MM-DD/ — самостоятельные исследовательские результаты. Slack — транспорт, не первичное хранилище.

## 3. Четыре разрыва

### 3.1. Веточная структура

Исходный аудит **сообщает** о 72 ветках (эти числа здесь не переверифицированы):

| Префикс | Число |
| --- | ---: |
| chatgpt/* | 19 |
| work/* | 16 |
| research/* | 11 |
| arena/* | 8 |
| feature/* | 7 |
| audit/* | 4 |
| prototype/* | 3 |
| docs/* | 1 |
| без группового префикса | 3 |
| **Итого** | **72** |

Ничего не удалять до полной инвентаризации. Для каждой ветки получить: branch → head SHA → base/ancestry → PR → назначение → уникальные артефакты → superseded → evidence migrated → рекомендация. Старые ветки — READ_ONLY/ARCHIVE, пока не доказано обратное.

### 3.2. Несогласованная многошаговая публикация

Отчёт может сохраниться, реестр обновиться, а CURRENT_STATUS — нет. Следующий чат получит противоречивое состояние. Нужен **append-only журнал immutable run records**, а CURRENT_STATUS, RESEARCH_QUEUE, ARTIFACT_REGISTER, BRANCH_REGISTRY — **восстанавливаемые проекции**. Не переключать действующие документы на generated до работающего, протестированного index builder.

### 3.3. PR #21 — не publisher

[PR #21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21) содержит coordinator.py, step_sync.py, socket_mode.py; структурированные APA_EVENT_V1, event_id, SQLite, фазы SOURCE/OFFLINE/SYNTHETIC/BUILD/LIVE, conflicts/supersedes, API /health, /v1/state, /v1/changes, /v1/wait. Это полезный **event/conflict ledger и транспорт**, но **не** исследователь и **не** GitHub publisher. Заимствовать алгоритмы, не объявлять daemon развёрнутым.

### 3.4. Права инструментов зависят от сессии

В исходной сессии автора аудита GitHub write отсутствовал: GITHUB_PUBLISH_BLOCKED — WRITE_ACTION_NOT_EXPOSED_IN_CURRENT_SESSION. В других обычных чатах GitHub write/read подтверждён. Следовательно **capability probe в каждом запуске**, никаких глобальных обещаний. Opera в исходной сессии была disconnected.

## 4. Архитектурное решение: Split-Plane APA Research OS

| Вариант | Оценка |
| --- | --- |
| Только Markdown и дисциплина чатов | Оставить как базу, недостаточно для восстановления |
| GitHub-only automation | Подходит для детерминированного housekeeping |
| ChatGPT → Slack → PR #21 → publisher | Резервный транспорт |
| **Раздельные Research / Publish / Control planes** | **ВЫБРАТЬ** |

**Research plane:** обычные чаты ChatGPT выполняют техническую работу; никакой чат не считается хранилищем. Deep Research только по отдельному запросу владельца.

**Publish plane:** получает RUN_EVENT → валидирует schema → проверяет run_id/idempotency → сохраняет immutable report/manifest/evidence → commit → readback + hash → пересобирает индексы → commit + readback → PUBLISHED_VERIFIED. Не занимается исследованием.

**Control plane:** Issue #23 → CURRENT_STATUS → ПЛАН/ДЕЙСТВИЕ/ПОДШАГ → последний VERIFIED run → следующий разрешённый S-ID.

Целевая структура (проект, **не утверждение, что она создана**):

    docs/research/apa-results/
      README.md
      MASTER_PLAN.md
      CURRENT_STATUS.md                 # generated projection, после gate
      RESEARCH_QUEUE.md                # generated projection, после gate
      ARTIFACT_REGISTER.md             # generated projection, после gate
      BRANCH_REGISTRY.md               # generated projection, после gate
      protocol/
        AGENT_PROTOCOL.md
        PUBLISHING_PROTOCOL.md
        EVIDENCE_POLICY.md
        RUN_EVENT_V2.schema.json
      state/
        current.json
        queue.json
        heartbeat.json
      inventories/
        branches.json
        pull_requests.json
        artifact-map.json
      runs/YYYY-MM-DD/APA-RUN-.../
        REPORT.md
        manifest.json
        evidence.json

## 5. RUN_EVENT_V2

Исходный аудит предложил следующую сущность (пример, не реальный run):

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
      "scope": {"archicad": "29", "sdk": "29.x", "repository": "dvikt33-ux/safe-bim-layer"},
      "inputs": [],
      "claims": [],
      "evidence": [],
      "files_to_publish": ["REPORT.md"],
      "next_substep": "APA-P10.A01.S02",
      "safety": {"main_modified": false, "pln_modified": false, "apx_modified": false}
    }

**Idempotency key:** substep_id + source revision/SHA + evidence fingerprint + executor run ID. Повтор с теми же входами не должен создавать новые отчёты.

**State machine:**

    QUEUED → CLAIMED → RUNNING → EVIDENCE_READY → PUBLISHING
    → COMMITTED → READBACK_VERIFIED → INDEXED → DONE_PUBLISHED

Ошибки/особые состояния: NOT_VERIFIED, DOCUMENT_NOT_READ, SOURCE_UNAVAILABLE, CONFLICT, BLOCKED_EXTERNAL, GITHUB_PUBLISH_BLOCKED, PUBLISH_READBACK_FAILED, RUNNER_OFFLINE, SUPERSEDED.

**Инвариант:** EVIDENCE_READY ≠ DONE_PUBLISHED. Наличие текста в чате/Slack не равно GitHub commit.

## 6. Ветки, коммиты и инвентаризация

- main/master — защищены, никакой автоматической записи.
- research/apa-verified-results-hub-20261010 — единственный долговременный исследовательский hub.
- Новые code branches — только по реальной необходимости: feature/<task-id>-<slug>, fix/<task-id>-<slug>, experiment/<task-id>-<slug>; без создания новых research/random-topic-date.
- Старые ветки не удалять, не force-push, не закрывать PR автоматически.
- Обязательные поля FULL_BRANCH_INVENTORY: branch, head_sha, last_commit, open_pr, base, class, unique_artifacts, superseded_by, evidence_migrated, recommendation, deletion_authorized=NO.
- Формат коммитов: research(APA-P10.A02.S04): verify AC29 MEP route API; ops(APA): rebuild research indexes after APA-RUN-...
- Issue #23 — стабильный Control Center, не копия актуального статуса.

## 7. 24/7: фактические ограничения и варианты

Исходный аудит ссылается на документацию OpenAI о том, что Deep Research использует connected apps как read-only источники и не выполняет connected-app write actions. Прямой Deep Research → GitHub commit **не принимать как поддерживаемый путь**.

Scheduled Tasks могут запускать периодические обычные исследования на доступных тарифах, но внешняя запись через connected apps может требовать approval; следовательно без реальных unattended write/readback **24/7 не доказан**. Work/webhook route исключён по запрету владельца. Наличие расписания ≠ работающий publisher.

GitHub MCP Server (официальный github/github-mcp-server) имеет инструменты create_or_update_file и push_files; это кандидат для будущего publisher, **не доказательство, что текущий ChatGPT connector использует этот сервер или что write доступен всем исполнителям**. Нельзя предполагать доступность платных beta-возможностей.

PR #21 — event ledger, Slack — уведомления, GitHub Actions — deterministic housekeeping (для schedule обычно нужен workflow в default branch), Opera — NOT_VERIFIED в исходной сессии. Work/Codex/платный OpenAI API/сторонние платные LLM — отклонить.

Матрица из исходного аудита (историческая, не переносить без новой проверки):

| Executor | Read | Research | Write | Readback | Scheduled |
| --- | --- | --- | --- | --- | --- |
| ChatGPT в исходной сессии | PASS | PASS | BLOCKED | PASS | N/A |
| Deep Research | PASS | PASS | NO direct connected-app write | N/A | manual |
| Scheduled Task | ? | PASS | ? | ? | potentially |
| GitHub MCP publisher | capability | N/A | candidate | candidate | external |
| PR #21 coordinator | Slack | NO | NO Git | local | daemon not deployed |

**Статус:** BLOCKED_EXTERNAL — unattended write-канал от периодического обычного исследовательского исполнителя до publisher не подтверждён. Никаких обещаний 24/7 до логов.

## 8. Приоритет внедрения и gates

1. **APA-P00.A01.S03:** FULL_BRANCH_INVENTORY.md + FULL_BRANCH_INVENTORY.json по всем доступным refs, PR, SHA, уникальным артефактам. Никаких удалений.
2. **APA-P00.A02.S03:** дедупликация claims, один canonical claim ID, старые источники остаются evidence.
3. **APA-P00.A03.S01:** матрица возможностей каждого исполнителя: READ/RESEARCH/WRITE/READBACK/SCHEDULED, проверять в его сессии.
4. **APA-P00.A03.S03:** RUN_EVENT_V2 + Publisher + Index Builder; детерминированная, идемпотентная публикация и восстановление после сбоя.
5. **APA-P00.A03.S04:** два последовательных цикла research → report → commit → readback → index → next task. Только затем DONE.
6. **APA-P40.A01.S01–S04:** scheduler, heartbeat, retry/backoff, max concurrency=1, watchdog, 24-часовая проверка по реальным событиям.

**Crash recovery:** если отчёт закоммичен, но index commit сорвался, index builder должен найти неиндексированный immutable run, достроить проекции и подтвердить readback; никогда не требовать повторного исследования для этого.

## 9. Формат receipt каждого прохода

    STATUS: DONE_PUBLISHED
    RUN: APA-RUN-...
    GITHUB:
      branch: research/apa-verified-results-hub-20261010
      path: docs/research/apa-results/runs/...
      commit: exact SHA
      readback: VERIFIED
      content_hash: SHA-256
    CLAIMS:
      3 SOURCE_VERIFIED
      1 TEST_REQUIRED
      2 NOT_VERIFIED
    NEXT: APA-P10.A02.S04

Если commit/readback не подтверждён — GITHUB_PUBLISH_BLOCKED, а не DONE. Статусы доказательств не повышать без первоисточников/тестов.

## 10. Итоговые решения исходного аудита

- **Выбрать Split-Plane APA Research OS.**
- **Сохранить PR #22** как фундамент GitHub hub; не заменять новым репозиторием/веткой.
- **Из PR #21 взять** event schema, idempotency, append-only ledger, conflict/supersedes; не выдавать его за research agent или publisher.
- **Обычный ChatGPT + GitHub write/readback — стандартный исследователь/публикатор** по указанию владельца; Deep Research без явного разрешения не запускать.
- Slack — транспорт, GitHub — долговременная память.
- Не создавать research-ветки для каждого прохода; не удалять старые 72 ветки без forensic inventory.
- Автоматизация публикации и восстановление проекций важнее расширения числа исследовательских агентов.
- Не просить владельца вручную разносить результаты по чатам.
- Не трогать main/master, PLN, установленный APX, протестированные ветки, не запускать платные модели/Work/Codex и не делать auto-merge.

## 11. Прямые постоянные ссылки

- [Canonical research hub](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results)
- [PR #22 — research hub](https://github.com/dvikt33-ux/safe-bim-layer/pull/22)
- [PR #21 — event coordinator](https://github.com/dvikt33-ux/safe-bim-layer/pull/21)
- [Issue #23 — APA Control Center](https://github.com/dvikt33-ux/safe-bim-layer/issues/23)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [OpenAI Help — Deep Research](https://help.openai.com/en/articles/10500283-deep-research-faq)

## 12. Границы достоверности публикации

Этот файл — **нормализованная, содержательно полная передача ключевых разделов предоставленного текста**, а **не побайтовая копия вложения**. Исторические утверждения «72 ветки», «16 коммитов PR #22», возможности OpenAI/Tasks и прежние citation markers остаются **REPORTED/NOT_VERIFIED**, пока не проведена отдельная сверка. В частности, отсутствие GitHub write у автора исходного аудита не означает отсутствия write в этом чате.

**Следующий безопасный шаг:** сохранить decision record и протокол V2, затем выполнить полную read-only инвентаризацию; внедрение publisher/индексов и scheduler только после отдельного теста без изменения main.
