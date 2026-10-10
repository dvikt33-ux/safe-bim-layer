# APA — task cards / durable cross-chat context

Generated from PROJECT_PLAN.json. Read before claiming a task.

## APA-P00.A01.S01

**Найти и прочитать исходный hub** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P00 → APA-P00.A01
- Work key: apa-p00-a01-s01
- Depends on: none
- Related, check before duplicating: none
- Acceptance: Перечень файлов с проверкой GitHub readback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Перечень файлов с проверкой GitHub readback

## APA-P00.A01.S02

**Найти архивные исследования и индекс** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P00 → APA-P00.A01
- Work key: apa-p00-a01-s02
- Depends on: none
- Related, check before duplicating: none
- Acceptance: Ссылки на архивные документы и происхождение
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Ссылки на архивные документы и происхождение

## APA-P00.A01.S03

**Инвентаризировать 72 ветки и PR, проверить уникальные результаты и ancestry** — CONSOLIDATION / PARTIAL / P0

- Parent: APA-P00 → APA-P00.A01
- Work key: apa-p00-a01-s03
- Depends on: APA-P00.A01.S02
- Related, check before duplicating: APA-P50.A01.S01
- Acceptance: Список уникальных артефактов, SHA, дубликатов и неизвестного
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-BRANCHES](../../../../../docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md), [ART-BRANCH-JSON](../../../../../docs/research/apa-results/inventories/BRANCH_HEADS_20261010.json)
- Existing V2 runs: none
- Expected output: Список уникальных артефактов, SHA, дубликатов и неизвестного

## APA-P00.A01.S04

**Сопоставить локальные и удалённые SHA без догадок** — VALIDATION / BLOCKED / P1

- Parent: APA-P00 → APA-P00.A01
- Work key: apa-p00-a01-s04
- Depends on: APA-P00.A01.S03
- Related, check before duplicating: none
- Acceptance: Подтверждённый доступ к локальным источникам
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-BRANCHES](../../../../../docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md)
- Existing V2 runs: none
- Expected output: Подтверждённый доступ к локальным источникам

## APA-P00.A02.S01

**Установить единственную каноническую исследовательскую ветку** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P00 → APA-P00.A02
- Work key: apa-p00-a02-s01
- Depends on: none
- Related, check before duplicating: none
- Acceptance: Каноническая ветка определена
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Каноническая ветка определена

## APA-P00.A02.S02

**Создать hub, план, реестр, очередь, протоколы** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P00 → APA-P00.A02
- Work key: apa-p00-a02-s02
- Depends on: none
- Related, check before duplicating: none
- Acceptance: Опубликованные документы с readback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md), [ART-QUEUE](../../../../../docs/research/apa-results/RESEARCH_QUEUE.md), [ART-STATUS](../../../../../docs/research/apa-results/CURRENT_STATUS.md)
- Existing V2 runs: none
- Expected output: Опубликованные документы с readback

## APA-P00.A02.S03

**Связать старые находки с S-ID и удалить логические дубли без удаления оригиналов** — CONSOLIDATION / READY / P0

- Parent: APA-P00 → APA-P00.A02
- Work key: apa-p00-a02-s03
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A01.S02
- Acceptance: Evidence map и superseded_by для дублей
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md), [ART-BRANCHES](../../../../../docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md)
- Existing V2 runs: none
- Expected output: Evidence map и superseded_by для дублей

## APA-P00.A02.S04

**Контролировать receipt/commit/readback всех завершённых отчётов** — VALIDATION / PARTIAL / P1

- Parent: APA-P00 → APA-P00.A02
- Work key: apa-p00-a02-s04
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Нет ложных DONE без квитанции
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUB-RECEIPT](../../../../../docs/research/apa-results/receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json)
- Existing V2 runs: none
- Expected output: Нет ложных DONE без квитанции

## APA-P00.A03.S01

**Проверить write/readback для всех классов исполнителей** — VALIDATION / PARTIAL / P0

- Parent: APA-P00 → APA-P00.A03
- Work key: apa-p00-a03-s01
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Capability matrix по каждому исполнителю
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUB-RECEIPT](../../../../../docs/research/apa-results/receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json)
- Existing V2 runs: none
- Expected output: Capability matrix по каждому исполнителю

## APA-P00.A03.S02

**Выбрать разрешённый периодический research runner без платных API** — CONTROL / BLOCKED / P1

- Parent: APA-P00 → APA-P00.A03
- Work key: apa-p00-a03-s02
- Depends on: APA-P00.A03.S01
- Related, check before duplicating: none
- Acceptance: Подтверждённый executor, бюджет, разрешения
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-OS-AUDIT](../../../../../docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md)
- Existing V2 runs: none
- Expected output: Подтверждённый executor, бюджет, разрешения

## APA-P00.A03.S03

**Publisher, дедупликация, retry, heartbeat и ошибки** — BUILD / PARTIAL / P0

- Parent: APA-P00 → APA-P00.A03
- Work key: apa-p00-a03-s03
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P60.A02.S02
- Acceptance: Publisher E2E + оставшиеся recovery/heartbeat gates
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUBLISHER](../../../../../tools/apa_publisher/publisher.py), [ART-PUB-RECEIPT](../../../../../docs/research/apa-results/receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json)
- Existing V2 runs: none
- Expected output: Publisher E2E + оставшиеся recovery/heartbeat gates

## APA-P00.A03.S04

**Два независимых SOURCE цикла с GitHub readback** — VALIDATION / PARTIAL / P1

- Parent: APA-P00 → APA-P00.A03
- Work key: apa-p00-a03-s04
- Depends on: APA-P00.A03.S03
- Related, check before duplicating: none
- Acceptance: Два разных SOURCE run_id, оба DONE_PUBLISHED
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUB-RECEIPT](../../../../../docs/research/apa-results/receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json)
- Existing V2 runs: [APA-RUN-20261010-104437Z-publisher-integration-smoke](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-104437Z-publisher-integration-smoke/REPORT.md) (receipt verified)
- Expected output: Два разных SOURCE run_id, оба DONE_PUBLISHED

## APA-P10.A01.S01

**AC29 SDK headers и native create/change/get сигнатуры** — RESEARCH / PARTIAL / P1

- Parent: APA-P10 → APA-P10.A01
- Work key: apa-p10-a01-s01
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Версии SDK, первоисточники, проверенные сигнатуры
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-SDK-SEO](../../../../../docs/research/apa-results/runs/2026-10-10/apa-discovery-20261010-102440-slinktrim-9f2b7.md)
- Existing V2 runs: none
- Expected output: Версии SDK, первоисточники, проверенные сигнатуры

## APA-P10.A01.S02

**Этажи, building materials, surfaces, composites, profiles, связи** — RESEARCH / READY / P1

- Parent: APA-P10 → APA-P10.A01
- Work key: apa-p10-a01-s02
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Матрица native elements/attributes и readback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Матрица native elements/attributes и readback

## APA-P10.A01.S03

**Morph/Roof/Shell/Openings/SEO/3D dump** — RESEARCH / READY / P1

- Parent: APA-P10 → APA-P10.A01
- Work key: apa-p10-a01-s03
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Матрица покрытия и побочных эффектов
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-SDK-SEO](../../../../../docs/research/apa-results/runs/2026-10-10/apa-discovery-20261010-102440-slinktrim-9f2b7.md)
- Existing V2 runs: none
- Expected output: Матрица покрытия и побочных эффектов

## APA-P10.A02.S01

**Tapir публичные версии и Python/JSON vs локальная 1.5.10** — RESEARCH / READY / P1

- Parent: APA-P10 → APA-P10.A02
- Work key: apa-p10-a02-s01
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A02.S01
- Acceptance: Compatibility matrix с source SHA
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Compatibility matrix с source SHA

## APA-P10.A02.S02

**GDL/TN, Unicode, target identity и 92 ошибок** — RESEARCH / READY / P1

- Parent: APA-P10 → APA-P10.A02
- Work key: apa-p10-a02-s02
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A02.S01
- Acceptance: Разбор blockers без ложного LIVE
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20)
- Existing V2 runs: none
- Expected output: Разбор blockers без ложного LIVE

## APA-P10.A02.S03

**MCP/IFC/openBIM и альтернативы** — RESEARCH / READY / P2

- Parent: APA-P10 → APA-P10.A02
- Work key: apa-p10-a02-s03
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A02.S01
- Acceptance: Матрица альтернатив с границами
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Матрица альтернатив с границами

## APA-P10.A02.S04

**Native MEP/Tapir MEP команды, трассы, порты** — RESEARCH / READY / P1

- Parent: APA-P10 → APA-P10.A02
- Work key: apa-p10-a02-s04
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A02.S01
- Acceptance: MEP command/route/port matrix
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: MEP command/route/port matrix

## APA-P10.A03.S01

**Сравнить native C++, Tapir/Python, IFC и hybrid** — INTEGRATION / READY / P2

- Parent: APA-P10 → APA-P10.A03
- Work key: apa-p10-a03-s01
- Depends on: APA-P10.A01.S01, APA-P10.A02.S01, APA-P10.A02.S03
- Related, check before duplicating: APA-P50.A02.S02
- Acceptance: Decision alternatives и зависимости
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Decision alternatives и зависимости

## APA-P10.A03.S02

**Сравнить performance, обратимость, тестируемость, стоимость** — INTEGRATION / READY / P2

- Parent: APA-P10 → APA-P10.A03
- Work key: apa-p10-a03-s02
- Depends on: APA-P10.A03.S01
- Related, check before duplicating: none
- Acceptance: Оценка без выдуманных измерений
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Оценка без выдуманных измерений

## APA-P20.A01.S01

**Read-only provenance AC29 SDK/APX/source SHA** — VALIDATION / READY / P1

- Parent: APA-P20 → APA-P20.A01
- Work key: apa-p20-a01-s01
- Depends on: APA-P10.A01.S01
- Related, check before duplicating: none
- Acceptance: Проверенные версии и commit
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20)
- Existing V2 runs: none
- Expected output: Проверенные версии и commit

## APA-P20.A01.S02

**Read-only доступность команд, GDL, MEP, model dump** — VALIDATION / READY / P1

- Parent: APA-P20 → APA-P20.A01
- Work key: apa-p20-a01-s02
- Depends on: APA-P20.A01.S01
- Related, check before duplicating: none
- Acceptance: Raw evidence, no write
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Raw evidence, no write

## APA-P20.A01.S03

**Сохранить PASS/FAIL с raw evidence** — VALIDATION / READY / P1

- Parent: APA-P20 → APA-P20.A01
- Work key: apa-p20-a01-s03
- Depends on: APA-P20.A01.S02
- Related, check before duplicating: none
- Acceptance: Полные воспроизводимые логи
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Полные воспроизводимые логи

## APA-P20.A02.S01

**План изолированных тестов, rollback, критерии** — CONTROL / READY / P2

- Parent: APA-P20 → APA-P20.A02
- Work key: apa-p20-a02-s01
- Depends on: APA-P20.A01.S03
- Related, check before duplicating: none
- Acceptance: Test plan с защитами
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Test plan с защитами

## APA-P20.A02.S02

**Получить отдельное разрешение на изменение BIM/APX** — CONTROL / BLOCKED / P2

- Parent: APA-P20 → APA-P20.A02
- Work key: apa-p20-a02-s02
- Depends on: APA-P20.A02.S01
- Related, check before duplicating: none
- Acceptance: Явное разрешение владельца
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Явное разрешение владельца

## APA-P20.A02.S03

**Протоколировать разрешённые live тесты** — VALIDATION / BLOCKED / P2

- Parent: APA-P20 → APA-P20.A02
- Work key: apa-p20-a02-s03
- Depends on: APA-P20.A02.S02
- Related, check before duplicating: none
- Acceptance: LIVE PASS только с разрешением и raw evidence
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: LIVE PASS только с разрешением и raw evidence

## APA-P30.A01.S01

**Decision matrix для нативной BIM-геометрии** — INTEGRATION / READY / P2

- Parent: APA-P30 → APA-P30.A01
- Work key: apa-p30-a01-s01
- Depends on: APA-P10.A03.S02, APA-P20.A01.S03
- Related, check before duplicating: none
- Acceptance: Выбран shortest credible path
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Выбран shortest credible path

## APA-P30.A01.S02

**Блокировки и альтернативные маршруты** — INTEGRATION / READY / P2

- Parent: APA-P30 → APA-P30.A01
- Work key: apa-p30-a01-s02
- Depends on: APA-P30.A01.S01
- Related, check before duplicating: none
- Acceptance: Fallback plan
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Fallback plan

## APA-P30.A02.S01

**MVP: этажи → атрибуты → геометрия → библиотека → MEP** — BUILD / READY / P2

- Parent: APA-P30 → APA-P30.A02
- Work key: apa-p30-a02-s01
- Depends on: APA-P30.A01.S01
- Related, check before duplicating: APA-P50.A03.S01
- Acceptance: Milestones и входные условия
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Milestones и входные условия

## APA-P30.A02.S02

**Acceptance gates и rollback по этапам MVP** — VALIDATION / READY / P2

- Parent: APA-P30 → APA-P30.A02
- Work key: apa-p30-a02-s02
- Depends on: APA-P30.A02.S01
- Related, check before duplicating: none
- Acceptance: PASS/FAIL, readback, rollback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: PASS/FAIL, readback, rollback

## APA-P40.A01.S01

**Утвердить 24/7 executor и GitHub auth** — CONTROL / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Work key: apa-p40-a01-s01
- Depends on: APA-P00.A03.S02
- Related, check before duplicating: none
- Acceptance: Внешний runner, бюджет и доступ
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-OS-AUDIT](../../../../../docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md)
- Existing V2 runs: none
- Expected output: Внешний runner, бюджет и доступ

## APA-P40.A01.S02

**Периодический research→publish→readback цикл** — BUILD / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Work key: apa-p40-a01-s02
- Depends on: APA-P40.A01.S01
- Related, check before duplicating: none
- Acceptance: Наблюдаемые unattended циклы
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-PUBLISHER](../../../../../tools/apa_publisher/publisher.py)
- Existing V2 runs: none
- Expected output: Наблюдаемые unattended циклы

## APA-P40.A01.S03

**Watchdog пропусков и журнал ошибок** — BUILD / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Work key: apa-p40-a01-s03
- Depends on: APA-P40.A01.S02
- Related, check before duplicating: none
- Acceptance: Heartbeat и alarm
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-OS-AUDIT](../../../../../docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md)
- Existing V2 runs: none
- Expected output: Heartbeat и alarm

## APA-P40.A01.S04

**24-часовое доказательство непрерывности** — VALIDATION / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Work key: apa-p40-a01-s04
- Depends on: APA-P40.A01.S03
- Related, check before duplicating: none
- Acceptance: Реальные логи за 24h
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-OS-AUDIT](../../../../../docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md)
- Existing V2 runs: none
- Expected output: Реальные логи за 24h

## APA-P50.A01.S01

**Карта связей: исследования ↔ S-ID ↔ артефакты ↔ PR** — CONSOLIDATION / READY / P0

- Parent: APA-P50 → APA-P50.A01
- Work key: apa-p50-a01-s01
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P00.A01.S03
- Acceptance: Traceability matrix, orphan report list
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md), [ART-BRANCHES](../../../../../docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md)
- Existing V2 runs: none
- Expected output: Traceability matrix, orphan report list

## APA-P50.A01.S02

**Дедупликация по work_key/source revision/claim** — CONSOLIDATION / READY / P0

- Parent: APA-P50 → APA-P50.A01
- Work key: apa-p50-a01-s02
- Depends on: APA-P50.A01.S01
- Related, check before duplicating: APA-P00.A02.S03
- Acceptance: Duplicate map и superseded_by
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Duplicate map и superseded_by

## APA-P50.A01.S03

**Сводить несколько исследований одной темы в решение** — INTEGRATION / READY / P1

- Parent: APA-P50 → APA-P50.A01
- Work key: apa-p50-a01-s03
- Depends on: APA-P50.A01.S01
- Related, check before duplicating: none
- Acceptance: Theme synthesis с conflicts/unknown
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Theme synthesis с conflicts/unknown

## APA-P50.A02.S01

**Единый каталог AC29 SDK/Tapir/Python/GDL/IFC/MEP инструментов** — RESEARCH / READY / P1

- Parent: APA-P50 → APA-P50.A02
- Work key: apa-p50-a02-s01
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P10.A02.S01, APA-P10.A02.S02, APA-P10.A02.S03, APA-P10.A02.S04
- Acceptance: Capability matrix, версии, пересечения
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Capability matrix, версии, пересечения

## APA-P50.A02.S02

**Выявить дубли функций между инструментами и выбрать adapter boundaries** — INTEGRATION / READY / P1

- Parent: APA-P50 → APA-P50.A02
- Work key: apa-p50-a02-s02
- Depends on: APA-P50.A02.S01
- Related, check before duplicating: APA-P10.A03.S01
- Acceptance: Integration architecture + canonical interfaces
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Integration architecture + canonical interfaces

## APA-P50.A02.S03

**Спланировать безопасное объединение инструментов** — BUILD / READY / P2

- Parent: APA-P50 → APA-P50.A02
- Work key: apa-p50-a02-s03
- Depends on: APA-P50.A02.S02, APA-P30.A01.S01
- Related, check before duplicating: none
- Acceptance: Non-invasive integration sequence
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Non-invasive integration sequence

## APA-P50.A03.S01

**Синтез тем: источник → решение → MVP → тесты** — INTEGRATION / READY / P2

- Parent: APA-P50 → APA-P50.A03
- Work key: apa-p50-a03-s01
- Depends on: APA-P50.A01.S03, APA-P50.A02.S02
- Related, check before duplicating: APA-P30.A02.S01
- Acceptance: One implementation map
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: One implementation map

## APA-P50.A03.S02

**Проверка готовности интеграции и отсутствия повторов** — VALIDATION / READY / P2

- Parent: APA-P50 → APA-P50.A03
- Work key: apa-p50-a03-s02
- Depends on: APA-P50.A03.S01
- Related, check before duplicating: none
- Acceptance: Evidence-backed go/no-go
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: none
- Expected output: Evidence-backed go/no-go

## APA-P60.A01.S01

**Зафиксировать единый машинный костяк проекта и ID** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P60 → APA-P60.A01
- Work key: apa-p60-a01-s01
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Структурированный план сохранён и readback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Структурированный план сохранён и readback

## APA-P60.A01.S02

**Валидатор DAG, статусов, duplicate work и gates** — BUILD / READY / P0

- Parent: APA-P60 → APA-P60.A01
- Work key: apa-p60-a01-s02
- Depends on: APA-P60.A01.S01
- Related, check before duplicating: none
- Acceptance: Offline tests + fail-closed validation
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Offline tests + fail-closed validation

## APA-P60.A01.S03

**Генератор единого control board, next work, context pack** — BUILD / READY / P0

- Parent: APA-P60 → APA-P60.A01
- Work key: apa-p60-a01-s03
- Depends on: APA-P60.A01.S02
- Related, check before duplicating: none
- Acceptance: Автоматические views и provenance
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Автоматические views и provenance

## APA-P60.A01.S04

**End-to-end controller workflow и readback** — VALIDATION / READY / P0

- Parent: APA-P60 → APA-P60.A01
- Work key: apa-p60-a01-s04
- Depends on: APA-P60.A01.S03
- Related, check before duplicating: none
- Acceptance: Actions success и generated views readback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUB-WORKFLOW](../../../../../.github/workflows/apa-research-publisher.yml)
- Existing V2 runs: none
- Expected output: Actions success и generated views readback

## APA-P60.A02.S01

**Handoff protocol: каждый чат читает control plan, берёт S-ID** — CONTROL / READY / P0

- Parent: APA-P60 → APA-P60.A02
- Work key: apa-p60-a02-s01
- Depends on: APA-P60.A01.S03
- Related, check before duplicating: none
- Acceptance: Контекст доступен без пересылки чатов
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Контекст доступен без пересылки чатов

## APA-P60.A02.S02

**Связать publisher inbox с controller plan, запретить orphan runs** — INTEGRATION / READY / P1

- Parent: APA-P60 → APA-P60.A02
- Work key: apa-p60-a02-s02
- Depends on: APA-P60.A01.S02
- Related, check before duplicating: APA-P00.A03.S03
- Acceptance: Publisher rejects unknown S-ID
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUBLISHER](../../../../../tools/apa_publisher/publisher.py)
- Existing V2 runs: none
- Expected output: Publisher rejects unknown S-ID

## APA-P60.A02.S03

**Протестировать CAS-claim, lease, duplicate prevention** — VALIDATION / READY / P1

- Parent: APA-P60 → APA-P60.A02
- Work key: apa-p60-a02-s03
- Depends on: APA-P60.A02.S01, APA-P60.A02.S02
- Related, check before duplicating: none
- Acceptance: Два исполнителя не получают один work_key
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Два исполнителя не получают один work_key
