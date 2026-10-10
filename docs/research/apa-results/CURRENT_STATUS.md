# APA — что делается сейчас

**Дата контрольного среза:** 2026-10-10. **Каноническая ветка:** [research/apa-verified-results-hub-20261010](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results).

## Текущая лестница

**ПЛАН:** [APA-P00 — Восстановление и централизация](MASTER_PLAN.md#apa-p00--восстановление-и-централизация-накопленных-материалов)

↳ **ДЕЙСТВИЕ:** APA-P00.A01 — Инвентаризация фактически опубликованного

↳ ↳ **ТЕКУЩИЙ ПОДШАГ:** **APA-P00.A01.S03 — Продолжить forensic inventory 72 веток (ancestry/unique artifacts/PR mapping)**

- Обычный чат с GitHub connector: **PASS** — несколько Markdown записаны и прочитаны обратно.
- Deep Research → GitHub: **NOT_VERIFIED / НЕ НАСТРОЕНО** — вывод в отдельном виджете не является GitHub commit.
- Постоянный планировщик / runner: **NOT_RUNNING**.
- Следующий подшаг после S01: APA-P00.A03.S02 — выбрать разрешённый always-on исполнитель без платных API и без изменений main.

## Режим, подтверждённый владельцем

**Исследования — в обычных чатах ChatGPT с GitHub connector и публикацией в canonical hub; Deep Research без отдельного запроса НЕ ЗАПУСКАТЬ.** Это выбранный способ исполнения, а не утверждение, что 24/7 runner работает. Проверка расписания и двух последовательных публикаций остаётся открытой; статус 24/7 **NOT_RUNNING**.

**Частичная техническая дельта APA-P10.A01.S01:** [AC29 Get3DInfo/contacts/Opening](runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md) сохранена, commit [d65c5bd](https://github.com/dvikt33-ux/safe-bim-layer/commit/d65c5bd327d077d7873ff720cda6dac3bf8a22cb), readback подтверждён. В официальной документации встречаются оба имени `ACAPI_Element_Get3DInfo` и `ACAPI_ModelAccess_Get3DInfo`; нельзя переименовывать код без SDK header/compile gate. Полный прежний Deep Research отчёт **не восстановлен**.

## Автоматический publisher — DEPLOYED / SYNTHETIC_E2E_PASS (2026-10-10)

**Проверено:** [GitHub Actions run 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) — success; 6 offline tests, автоматический report+manifest+evidence, [generated index](generated/INDEX.md), GitHub REST SHA-256/blob readback, [automatic DONE_PUBLISHED receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json). Повторный запуск [38046020069](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046020069) завершился success без нового коммита (idempotent no-op). [Workflow](../../.github/workflows/apa-research-publisher.yml), [publisher source](../../tools/apa_publisher/publisher.py), [операторская инструкция](../../tools/apa_publisher/README.md), [PUBLISH_REQUEST_V1](protocol/PUBLISH_REQUEST_V1.schema.json).

**Граница:** это автоматический **push-triggered GitHub publisher**, а не автономный исследователь ChatGPT; 24/7 research scheduler/heartbeat **NOT_RUNNING**. Тест SYNTHETIC, не Archicad LIVE/BUILD. Legacy manual индексы пока обновляются отдельно.

## APA Research OS — результат публикации переданного аудита

**Опубликовано и прочитано обратно:** [содержательно полная версия аудита](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md), commit [9b07679](https://github.com/dvikt33-ux/safe-bim-layer/commit/9b076792124d99d67dcc0f01554b4834fc3ed8cb); [readback receipt](receipts/APA-RUN-20261010-102800Z-research-os-audit-readback.json). Это **другой** документ, не прежний пропавший полный AC29 Deep Research отчёт.

**APA-P00.A01.S03 частично выполнен:** [снимок всех 72 веток с SHA и PR](inventories/FULL_BRANCH_INVENTORY.md) + [JSON](inventories/BRANCH_HEADS_20261010.json) опубликованы; ancestry, уникальные артефакты, superseded_by и локальные SHA остаются NOT_VERIFIED. Ни одна ветка не удалена.

**APA-P00.A03.S03 — PUBLISHER_DEPLOYED / SYNTHETIC_E2E_PASS:** [RUN_EVENT_V2.schema.json](protocol/RUN_EVENT_V2.schema.json), [publisher source](../../tools/apa_publisher/publisher.py), [workflow](../../.github/workflows/apa-research-publisher.yml), [generated V2 index](generated/INDEX.md), [receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json). GitHub Actions [38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) success; 6 offline tests + report/index/receipt API readback. **Publisher работает на push inbox, но scheduler/heartbeat/24h runner NOT_RUNNING.** Ручные legacy индексы ещё не переведены на generated projections.

**Исполнитель:** обычный ChatGPT + GitHub write/readback подтверждён в этой сессии. Deep Research не запускался и без отдельного разрешения запускаться не должен. Права Scheduled Tasks на unattended GitHub write — NOT_VERIFIED.

## Что завершено и где доказательства

- **APA-P00.A01.S01:** прочитаны 5 существовавших файлов research hub; [реестр](ARTIFACT_REGISTER.md).
- **APA-P00.A01.S02:** обнаружены и прочитаны 3 архивных документа/индекса; [реестр](ARTIFACT_REGISTER.md).
- **APA-P00.A02.S01:** зафиксирована каноническая ветка, новые research-ветки не создавать.
- **APA-P00.A02.S02:** опубликованы операционные документы [MASTER_PLAN](MASTER_PLAN.md), [BRANCH_REGISTRY](BRANCH_REGISTRY.md), [RESEARCH_TEMPLATE](RESEARCH_TEMPLATE.md), [AGENT_PROTOCOL](AGENT_PROTOCOL.md), [AUTOMATION_AND_GATES](AUTOMATION_AND_GATES.md), [RESEARCH_QUEUE](RESEARCH_QUEUE.md) и этот статус. Проверка readback — отдельные подтверждения GitHub API.

## Следующие действия без потери контекста

1. **APA-P00.A01.S03:** полная инвентаризация старых веток/коммитов, сопоставление дублей и пустых/отсутствующих документов.
2. **APA-P00.A02.S03:** связать старые находки с задачами P10/P20, пометить verified/reported/unknown.
3. **APA-P10.A01.S01:** первичный аудит SDK Archicad 29 с точными сигнатурами и ссылками.
4. **APA-P00.A03.S02:** решить, какой реально работающий исполнитель может запускаться 24/7 и публиковать.

## Нельзя считать выполненным

- Прежний полный технический AC29 Deep Research отчёт и шесть обещанных файлов: **НЕ ОПУБЛИКОВАНЫ**. Отдельный предоставленный владельцем аудит APA Research OS **ОПУБЛИКОВАН**.
- Непрерывное исследование и автоматическая публикация: **НЕ ЗАПУЩЕНЫ**.
- Автоматическая синхронизация всех чатов: **НЕ ПОДТВЕРЖДЕНА**.
- Изменения main/PLN/APX и merge: **НЕ ПРОВОДИЛИСЬ**.

**Правило:** если исполнитель не может прочитать и записать этот файл в GitHub, он обязан явно сообщить GITHUB_PUBLISH_BLOCKED и дать готовый Markdown, а не просить владельца искать результаты по чатам.
