# APA — task cards / durable cross-chat context

Generated from PROJECT_PLAN.json. Read before claiming a task.

## APA-P00.A01.S01

**Найти и прочитать исходный hub** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P00 → APA-P00.A01
- Topic: HUB_GOVERNANCE
- Work key: hub-discovery
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
- Topic: HUB_GOVERNANCE
- Work key: archive-research-inventory
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
- Topic: HUB_GOVERNANCE
- Work key: branch-ancestry-forensics
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
- Topic: HUB_GOVERNANCE
- Work key: local-git-sha-parity
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
- Topic: HUB_GOVERNANCE
- Work key: canonical-branch-policy
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
- Topic: HUB_GOVERNANCE
- Work key: hub-operating-documents
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
- Topic: HUB_GOVERNANCE
- Work key: legacy-evidence-dedup
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
- Topic: HUB_GOVERNANCE
- Work key: publication-completeness-audit
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
- Topic: PUBLISHER
- Work key: executor-capability-matrix
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
- Topic: PUBLISHER
- Work key: unattended-runner-selection
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
- Topic: PUBLISHER
- Work key: publisher-and-recovery
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
- Topic: PUBLISHER
- Work key: two-independent-source-publishes
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
- Topic: SDK_NATIVE
- Work key: sdk-native-signatures
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
- Topic: SDK_NATIVE
- Work key: sdk-attributes-stories
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
- Topic: SDK_NATIVE
- Work key: sdk-geometry-modeldump
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
- Topic: TAPIR_PYTHON
- Work key: tapir-python-compatibility
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
- Topic: GDL_TN
- Work key: gdl-tn-identity-and-92-errors
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
- Topic: IFC_MCP
- Work key: ifc-mcp-openbim
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
- Topic: MEP
- Work key: native-and-tapir-mep
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
- Topic: ARCHITECTURE
- Work key: architecture-option-matrix
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
- Topic: ARCHITECTURE
- Work key: architecture-constraints-cost
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
- Topic: TESTS
- Work key: ac29-sdk-apx-provenance
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
- Topic: TESTS
- Work key: read-only-command-capabilities
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
- Topic: TESTS
- Work key: raw-test-evidence-register
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
- Topic: TESTS
- Work key: isolated-live-test-plan
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
- Topic: TESTS
- Work key: owner-live-write-permission
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
- Topic: TESTS
- Work key: isolated-live-test-results
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
- Topic: ARCHITECTURE
- Work key: native-bim-shortest-path
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
- Topic: ARCHITECTURE
- Work key: architecture-blockers-fallbacks
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
- Topic: MVP
- Work key: mvp-implementation-milestones
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
- Topic: MVP
- Work key: mvp-acceptance-rollback
- Depends on: APA-P30.A02.S01
- Related, check before duplicating: none
- Acceptance: PASS/FAIL, readback, rollback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: PASS/FAIL, readback, rollback

## APA-P40.A01.S01

**Настроить запуск через ChatGPT Scheduled Tasks и разрешённый GitHub доступ** — CONTROL / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Topic: AUTOMATION
- Work key: always-on-executor-auth
- Depends on: APA-P00.A03.S02
- Related, check before duplicating: none
- Acceptance: Пользователь создал Scheduled Task; сохранены task ID, расписание/часовой пояс; реальный GitHub write/readback PASS; без Deep Research/платных API
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-OS-AUDIT](../../../../../docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md)
- Existing V2 runs: none
- Expected output: ChatGPT Scheduled task ID, расписание, часовой пояс, подтверждённый GitHub write/readback

## APA-P40.A01.S02

**Проверить Scheduled → IN_PROGRESS → результат → DONE_PUBLISHED/PARTIAL** — BUILD / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Topic: AUTOMATION
- Work key: unattended-research-cycle
- Depends on: APA-P40.A01.S01
- Related, check before duplicating: none
- Acceptance: Scheduled trigger реально сработал, в GitHub IN_PROGRESS записан до работы, затем verified receipt/evidence и DONE/PARTIAL, повторный чат не берёт тот же S-ID
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-PUBLISHER](../../../../../tools/apa_publisher/publisher.py)
- Existing V2 runs: none
- Expected output: Два реальных расписанных запуска с уникальным executor_run_id, status/readback и receipt

## APA-P40.A01.S03

**Watchdog пропусков Scheduled Task, зависших IN_PROGRESS и журнал ошибок** — BUILD / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Topic: AUTOMATION
- Work key: watchdog-and-error-journal
- Depends on: APA-P40.A01.S02
- Related, check before duplicating: none
- Acceptance: Heartbeat и alarm
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-OS-AUDIT](../../../../../docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md)
- Existing V2 runs: none
- Expected output: Heartbeat и alarm

## APA-P40.A01.S04

**Проверить 24 часа реальных запусков ChatGPT Scheduled Tasks без повторов** — VALIDATION / BLOCKED / P2

- Parent: APA-P40 → APA-P40.A01
- Topic: AUTOMATION
- Work key: 24h-continuity-proof
- Depends on: APA-P40.A01.S03
- Related, check before duplicating: none
- Acceptance: Реальные логи за 24h
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-OS-AUDIT](../../../../../docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md)
- Existing V2 runs: none
- Expected output: Реальные логи за 24h

## APA-P50.A01.S01

**Карта связей: исследования ↔ S-ID ↔ артефакты ↔ PR** — CONSOLIDATION / PARTIAL / P0

- Parent: APA-P50 → APA-P50.A01
- Topic: KNOWLEDGE_GRAPH
- Work key: cross-research-traceability
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P00.A01.S03
- Acceptance: Traceability matrix, orphan report list
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md), [ART-BRANCHES](../../../../../docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md), [ART-TRACE-REPORT](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-110048Z-legacy-traceability/REPORT.md)
- Existing V2 runs: [APA-RUN-20261010-110048Z-legacy-traceability](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-110048Z-legacy-traceability/REPORT.md) (receipt verified)
- Expected output: Published first source-backed traceability map: five legacy flat reports + one V2; four explicit S-ID links, one candidate; 72-branch ancestry still open

## APA-P50.A01.S02

**Дедупликация по work_key/source revision/claim** — CONSOLIDATION / READY / P0

- Parent: APA-P50 → APA-P50.A01
- Topic: KNOWLEDGE_GRAPH
- Work key: claim-and-evidence-dedup
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
- Topic: KNOWLEDGE_GRAPH
- Work key: theme-research-synthesis
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
- Topic: TOOL_INTEGRATION
- Work key: tool-capability-catalog
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
- Topic: TOOL_INTEGRATION
- Work key: tool-adapter-overlap-map
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
- Topic: TOOL_INTEGRATION
- Work key: tool-consolidation-roadmap
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
- Topic: SYNTHESIS
- Work key: research-to-mvp-synthesis
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
- Topic: SYNTHESIS
- Work key: integration-go-no-go
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
- Topic: CONTROLLER
- Work key: canonical-project-dag
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Структурированный план сохранён и readback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Структурированный план сохранён и readback

## APA-P60.A01.S02

**Валидатор DAG, статусов, duplicate work и gates** — BUILD / DONE_PUBLISHED / P0

- Parent: APA-P60 → APA-P60.A01
- Topic: CONTROLLER
- Work key: controller-dag-validator
- Depends on: APA-P60.A01.S01
- Related, check before duplicating: none
- Acceptance: Offline tests + fail-closed validation
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Offline tests + fail-closed validation

## APA-P60.A01.S03

**Генератор единого control board, next work, context pack** — BUILD / DONE_PUBLISHED / P0

- Parent: APA-P60 → APA-P60.A01
- Topic: CONTROLLER
- Work key: controller-generated-views
- Depends on: APA-P60.A01.S02
- Related, check before duplicating: none
- Acceptance: Автоматические views и provenance
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Автоматические views и provenance

## APA-P60.A01.S04

**End-to-end controller workflow и readback** — VALIDATION / DONE_PUBLISHED / P0

- Parent: APA-P60 → APA-P60.A01
- Topic: CONTROLLER
- Work key: controller-github-e2e
- Depends on: APA-P60.A01.S03
- Related, check before duplicating: none
- Acceptance: Actions success и generated views readback
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUB-WORKFLOW](../../../../../.github/workflows/apa-research-publisher.yml)
- Existing V2 runs: none
- Expected output: Actions success и generated views readback

## APA-P60.A02.S01

**Handoff protocol: каждый чат читает control plan, берёт S-ID** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P60 → APA-P60.A02
- Topic: CONTROLLER
- Work key: cross-chat-handoff
- Depends on: APA-P60.A01.S03
- Related, check before duplicating: none
- Acceptance: Контекст доступен без пересылки чатов
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Контекст доступен без пересылки чатов

## APA-P60.A02.S02

**Связать publisher inbox с controller plan, запретить orphan runs** — INTEGRATION / DONE_PUBLISHED / P1

- Parent: APA-P60 → APA-P60.A02
- Topic: CONTROLLER
- Work key: publisher-plan-claim-gate
- Depends on: APA-P60.A01.S02
- Related, check before duplicating: APA-P00.A03.S03
- Acceptance: Publisher rejects unknown S-ID
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-PUBLISHER](../../../../../tools/apa_publisher/publisher.py)
- Existing V2 runs: none
- Expected output: Publisher rejects unknown S-ID

## APA-P60.A02.S03

**Протестировать CAS-claim, lease, duplicate prevention** — VALIDATION / PARTIAL / P1

- Parent: APA-P60 → APA-P60.A02
- Topic: CONTROLLER
- Work key: claim-concurrency-test
- Depends on: APA-P60.A02.S01, APA-P60.A02.S02
- Related, check before duplicating: APA-P60.A02.S04
- Acceptance: Offline tests PASS; concurrent two-writer CAS and lease-expiry recovery NOT_VERIFIED
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json)
- Existing V2 runs: none
- Expected output: Два исполнителя не получают один work_key

## APA-P60.A02.S04

**Ввести сбор предложений задач исследователями и принятие аудитором в PROJECT_PLAN** — VALIDATION / PARTIAL / P1

- Parent: APA-P60 → APA-P60.A02
- Topic: CONTROLLER
- Work key: research-proposals-audit-approval
- Depends on: APA-P60.A02.S02
- Related, check before duplicating: APA-P60.A02.S03
- Acceptance: Процесс discovery proposal -> independent audit decision -> TASK registry admission задокументирован; CAS claim/readback и уникальность work_key/dependency DAG соблюдены; Scheduled instructions согласованы. End-to-end независимая публикация proposal, аудит, регистрация и валидатор контроллера подтверждены фактами. Не объявлять DONE по одним инструкциям.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json), [ART-PLAN](../../../../../docs/research/apa-results/MASTER_PLAN.md)
- Existing V2 runs: none
- Expected output: Публичный protocol предложений задач; Инструкции трёх Scheduled исполнителей; Первый проверенный GitHub proposal + review + admission; Проверенный controller DAG и readback
