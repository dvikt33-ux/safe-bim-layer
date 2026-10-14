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

**Инвентаризировать 72 ветки и PR, проверить уникальные результаты и ancestry** — CONSOLIDATION / PARTIAL / P8

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

**Сопоставить локальные и удалённые SHA без догадок** — VALIDATION / BLOCKED / P8

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

**Связать старые находки с S-ID и удалить логические дубли без удаления оригиналов** — CONSOLIDATION / PARTIAL / P0

- Parent: APA-P00 → APA-P00.A02
- Topic: HUB_GOVERNANCE
- Work key: legacy-evidence-dedup
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A01.S02
- Acceptance: Evidence map и superseded_by для дублей
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md), [ART-BRANCHES](../../../../../docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md)
- Existing V2 runs: [APA-RUN-20261010-234200Z-slack-legacy-three-audit](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-234200Z-slack-legacy-three-audit/REPORT.md) (receipt verified), [APA-RUN-20261010-235301Z-branch-evidence-dedup](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-235301Z-branch-evidence-dedup/REPORT.md) (receipt verified), [APA-RUN-20261011-001922Z-eighty-head-blob-inventory](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-001922Z-eighty-head-blob-inventory/REPORT.md) (receipt verified), [APA-RUN-20261011-092155Z-source71-byte-archive](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-092155Z-source71-byte-archive/REPORT.md) (receipt verified), [APA-RUN-20261011-190658Z-roof-comp-context-map](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-190658Z-roof-comp-context-map/REPORT.md) (receipt verified)
- Expected output: Evidence map и superseded_by для дублей

## APA-P00.A02.S04

**Контролировать receipt/commit/readback всех завершённых отчётов** — VALIDATION / PARTIAL / P8

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

## APA-P00.A02.S05

**Обновить действующий план CORE FIRST → EXPANSION по рабочей инструкции v2** — CONTROL / DONE_PUBLISHED / P0

- Parent: APA-P00 → APA-P00.A02
- Topic: HUB_GOVERNANCE
- Work key: core-first-operating-plan-v2
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Сохранены все прежние ID/статусы/доказательства; последовательный CORE FIRST DAG валиден; карта компонентов находится в каноническом реестре; инструкция и план опубликованы и прочитаны обратно
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-CONTROLLER](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md), [ART-APA-WORK-INSTRUCTION-V2](../../../../../docs/research/apa-results/control/WORK_OPERATING_INSTRUCTION.md)
- Existing V2 runs: none
- Expected output: IMPLEMENTATION_ROADMAP.md; WORK_OPERATING_INSTRUCTION.md; согласованный PROJECT_PLAN.json; GitHub CAS/readback

## APA-P00.A03.S01

**Проверить write/readback для всех классов исполнителей** — VALIDATION / PARTIAL / P8

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

**Выбрать разрешённый периодический research runner без платных API** — CONTROL / BLOCKED / P8

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

**Publisher, дедупликация, retry, heartbeat и ошибки** — BUILD / PARTIAL / P8

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

**Два независимых SOURCE цикла с GitHub readback** — VALIDATION / PARTIAL / P8

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

**AC29 SDK headers и native create/change/get сигнатуры** — RESEARCH / PARTIAL / P7

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

**Этажи, building materials, surfaces, composites, profiles, связи** — RESEARCH / PARTIAL / P7

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

**Morph/Roof/Shell/Openings/SEO/3D dump** — RESEARCH / PARTIAL / P7

- Parent: APA-P10 → APA-P10.A01
- Topic: SDK_NATIVE
- Work key: sdk-geometry-modeldump
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Матрица покрытия и побочных эффектов
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-SDK-SEO](../../../../../docs/research/apa-results/runs/2026-10-10/apa-discovery-20261010-102440-slinktrim-9f2b7.md)
- Existing V2 runs: [APA-RUN-20261010-143940Z-opening-shell-geom](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md) (receipt verified)
- Expected output: Матрица покрытия и побочных эффектов

## APA-P10.A02.S01

**Tapir публичные версии и Python/JSON vs локальная 1.5.10** — RESEARCH / PARTIAL / P7

- Parent: APA-P10 → APA-P10.A02
- Topic: TAPIR_PYTHON
- Work key: tapir-python-compatibility
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A02.S01
- Acceptance: Compatibility matrix с source SHA
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: [APA-RUN-20261010-163950Z-tapir-compat-6f29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md) (receipt verified)
- Expected output: Compatibility matrix с source SHA

## APA-P10.A02.S02

**GDL/TN, Unicode, target identity и 92 ошибок** — RESEARCH / READY / P7

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

**MCP/IFC/openBIM и альтернативы** — RESEARCH / READY / P7

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

**Native MEP/Tapir MEP команды, трассы, порты** — RESEARCH / PARTIAL / P7

- Parent: APA-P10 → APA-P10.A02
- Topic: MEP
- Work key: native-and-tapir-mep
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: APA-P50.A02.S01
- Acceptance: MEP command/route/port matrix
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md)
- Existing V2 runs: [APA-RUN-20261010-200823Z-mep-route-port-gate](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md) (receipt verified)
- Expected output: MEP command/route/port matrix

## APA-P10.A03.S01

**Сравнить native C++, Tapir/Python, IFC и hybrid** — INTEGRATION / READY / P8

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

**Сравнить performance, обратимость, тестируемость, стоимость** — INTEGRATION / READY / P8

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

**Read-only provenance AC29 SDK/APX/source SHA** — VALIDATION / READY / P8

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

**Read-only доступность команд, GDL, MEP, model dump** — VALIDATION / READY / P8

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

**Сохранить PASS/FAIL с raw evidence** — VALIDATION / READY / P8

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

**План изолированных тестов, rollback, критерии** — CONTROL / READY / P8

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

**Получить отдельное разрешение на изменение BIM/APX** — CONTROL / BLOCKED / P8

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

**Протоколировать разрешённые live тесты** — VALIDATION / BLOCKED / P8

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

**Decision matrix для нативной BIM-геометрии** — INTEGRATION / READY / P8

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

**Блокировки и альтернативные маршруты** — INTEGRATION / READY / P8

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

**MVP: этажи → атрибуты → геометрия → библиотека → MEP** — BUILD / READY / P8

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

**Acceptance gates и rollback по этапам MVP** — VALIDATION / READY / P8

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

**Настроить запуск через ChatGPT Scheduled Tasks и разрешённый GitHub доступ** — CONTROL / BLOCKED / P8

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

**Проверить Scheduled → IN_PROGRESS → результат → DONE_PUBLISHED/PARTIAL** — BUILD / BLOCKED / P8

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

**Watchdog пропусков Scheduled Task, зависших IN_PROGRESS и журнал ошибок** — BUILD / BLOCKED / P8

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

**Проверить 24 часа реальных запусков ChatGPT Scheduled Tasks без повторов** — VALIDATION / BLOCKED / P8

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

**Карта связей: исследования ↔ S-ID ↔ артефакты ↔ PR** — CONSOLIDATION / PARTIAL / P8

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

**Дедупликация по work_key/source revision/claim** — CONSOLIDATION / READY / P8

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

**Сводить несколько исследований одной темы в решение** — INTEGRATION / READY / P8

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

**Единый каталог AC29 SDK/Tapir/Python/GDL/IFC/MEP инструментов** — RESEARCH / PARTIAL / P7

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

**Выявить дубли функций между инструментами и выбрать adapter boundaries** — INTEGRATION / READY / P8

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

**Спланировать безопасное объединение инструментов** — BUILD / READY / P8

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

**Синтез тем: источник → решение → MVP → тесты** — INTEGRATION / READY / P8

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

**Проверка готовности интеграции и отсутствия повторов** — VALIDATION / READY / P8

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

**Протестировать CAS-claim, lease, duplicate prevention** — VALIDATION / PARTIAL / P8

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

**Ввести сбор предложений задач исследователями и принятие аудитором в PROJECT_PLAN** — VALIDATION / PARTIAL / P8

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

## APA-P70.A01.S01

**Сопоставить полный продуктовый контракт с существующим кодом и исследованиями** — CONSOLIDATION / DONE_PUBLISHED / P1

- Parent: APA-P70 → APA-P70.A01
- Topic: PRODUCT_DEVELOPMENT
- Work key: product-contract-and-code-baseline
- Depends on: APA-P00.A02.S02
- Related, check before duplicating: none
- Acceptance: Таблица требований полного цикла → исходные файлы/SHA → подтверждённые функции и ограничения; без новой реализации
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-PR16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md), [ART-APA-LIVE-SCRATCH-PARTIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md)
- Existing V2 runs: [APA-RUN-20261011-091905Z-p70-source-integration-map](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-091905Z-p70-source-integration-map/REPORT.md) (receipt verified)
- Expected output: Таблица требований полного цикла → исходные файлы/SHA → подтверждённые функции и ограничения; без новой реализации

## APA-P70.A01.S02

**Привязать все значимые наработки к функциям продукта, выявить пробелы** — CONSOLIDATION / READY / P8

- Parent: APA-P70 → APA-P70.A01
- Topic: PRODUCT_DEVELOPMENT
- Work key: product-evidence-to-capability-trace
- Depends on: APA-P70.A01.S01, APA-P50.A01.S01
- Related, check before duplicating: none
- Acceptance: Матрица research → S-ID → код/PR → тест → функциональная возможность; дубликаты и пробелы явно отмечены
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md), [ART-TRACE-REPORT](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-110048Z-legacy-traceability/REPORT.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Матрица research → S-ID → код/PR → тест → функциональная возможность; дубликаты и пробелы явно отмечены

## APA-P70.A01.S03

**Утвердить минимальные границы интеграции и порядок сквозных поставок** — INTEGRATION / DONE_PUBLISHED / P2

- Parent: APA-P70 → APA-P70.A01
- Topic: PRODUCT_DEVELOPMENT
- Work key: product-integration-boundaries
- Depends on: APA-P70.A01.S01
- Related, check before duplicating: none
- Acceptance: Проверенный маршрут полного цикла, reuse map, отсутствие дублирования SceneWriter/графа/исполнителя, приёмочные ворота
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)
- Existing V2 runs: [APA-RUN-20261011-160327Z-p70-a01-s03-integration-freeze](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-160327Z-p70-a01-s03-integration-freeze/REPORT.md) (receipt verified)
- Expected output: Проверенный маршрут полного цикла, reuse map, отсутствие дублирования SceneWriter/графа/исполнителя, приёмочные ворота

## APA-P70.A02.S01

**Собрать семантический контракт задания, участка, этажей и помещений** — BUILD / DONE_PUBLISHED / P1

- Parent: APA-P70 → APA-P70.A02
- Topic: PRODUCT_DEVELOPMENT
- Work key: project-brief-and-story-contract
- Depends on: APA-P70.A01.S03
- Related, check before duplicating: none
- Acceptance: Два режима GENERATE_FROM_ZERO/ADAPT_EXISTING; требования/ограничения, первый этаж на ±0.000, index только по GetStories
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)
- Existing V2 runs: [APA-RUN-20261011-161511Z-p70-semantic-brief-getstories](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md) (receipt verified)
- Expected output: Два режима GENERATE_FROM_ZERO/ADAPT_EXISTING; требования/ограничения, первый этаж на ±0.000, index только по GetStories

## APA-P70.A02.S02

**Связать проектные требования с версиями нормативов и проверяемыми правилами** — BUILD / PARTIAL / P3

- Parent: APA-P70 → APA-P70.A02
- Topic: PRODUCT_DEVELOPMENT
- Work key: normative-applicability-pack
- Depends on: APA-P70.A02.S01, APA-P70.A08.S04
- Related, check before duplicating: none
- Acceptance: Rule pack с юрисдикцией/редакцией СП/ГОСТ, применимостью, требованиями, источниками и явными NOT_VERIFIED
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md), [ART-P70-A02-TDK-MACHINE-SOURCE-20261012](https://github.com/dvikt33-ux/tdk-course-project/tree/67f17d407d14aebb091daaf79f11c10178b87440/01_Normative_Base/_Machine)
- Existing V2 runs: [APA-RUN-20261012-191815Z-normative-bindings](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-191815Z-normative-bindings/REPORT.md) (receipt verified), [APA-RUN-20261012-203851Z-verified-roof-rules](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-203851Z-verified-roof-rules/REPORT.md) (receipt verified), [APA-RUN-20261012-210815Z-machine-normative](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-210815Z-machine-normative/REPORT.md) (receipt verified)
- Expected output: Rule pack с юрисдикцией/редакцией СП/ГОСТ, применимостью, требованиями, источниками и явными NOT_VERIFIED; Historical published draft PR66 head e43bc6055d648270b72dc573a22c9d52c71a83f8 on exact PR64 parent b056cb76929a62047c82fd66961b72eb4d9078a8.18newtests;513Windows host and Windows/LinuxCI38296039263 PASS. All5code and8source/report blobs match GitHub; publisher receipt DONE_PUBLISHED.; Working compile_project_normative_pack attaches an immutable source/edition/applicability digest to the existing provisional CSE/project pack. Actual native GUID/material/context/body signatures invalidate stale CSE evidence; existing selections and approval states remain unchanged. Cached current109GUID/fourjunction evidence reused, zero new native calls.; Six conditional requirement bindings reference five official registry metadata records verified2026-10-12: SP50.13330.2024, SP230.1325800.2015, SP17.13330.2017, SP2.13130.2020, GOST30971-2012. Full clauses and exact system/project applicability NOT_VERIFIED; metadata ACTIVE is not engineering compliance. No numerical norm or engineering class/load/result is invented.; Existing four actual Wall/Roof targets yield24rows:20NOT_VERIFIED and4window-familyNOT_APPLICABLE. Jurisdiction is not inferred from brief region or file name; native SinglePlane is not roofing technology. Unknown or stale system data never excludes a specific rule. Engineering remains ENGINEERING_NOT_VERIFIED.; External dependencies retained within A02.S02: source-backed actual site/jurisdiction, project thermal/fire/roof design facts, certified source-bound CSE layer/system evidence and qualified full clauses/table rows. Adapter is working and published; project-specific normative acceptance remainsPARTIAL. Native A11.S03PARTIAL and S10BLOCKED are independent and unchanged. Exact next available native step remains approved SinglePlane contour qualification followed by four-target remeasurement; no source-junction writes authorized or executed.; Current draft PR67 head 633c799da125622be6317ea9d09a9b7eb83fb98a on exact PR66 parent e43bc6055d648270b72dc573a22c9d52c71a83f8.33newtests,546Windows host/Windows+LinuxCI38305091756 PASS.7code and11source/report GitHub blobs exactly match; publisher receipt DONE_PUBLISHED.; Working existing normative adapter executes primary displayed roofing/thermal scope conditions and SP17 amendment5 thermal-reference replacement instruction against actual native bodies and a source-linked dependency graph. Four original targets yield12checks:4PASS_DOCUMENTED edition-reference edges only and8NOT_VERIFIED scope checks. Document PASS never certifies roof construction, thermal performance or engineering.; User directly confirmed jurisdiction RU/Central Russia and federal norms. Region confirmation supplies no city/climate design values, roof covering/layers/role, total building area, purpose or loads. Prior 24source bindings and CSE approvals remain unchanged; no invented normative or engineering value.; Primary current sources: SP17 registry amendments1-5, amendment5 effective2025-01-10 and its explicit current thermal reference; SP50.13330.2024 effective2024-06-16. Exact displayed source scope/conditions were reviewed, full consolidated technical slope/parapet/thermal clauses were not obtained. Official ministry/FCS fetches and local registry TLS retrieval failed. Existing GitHub research blob3396bfafb8e5bbfe4b539c5184f0ee0bd0c27561 retained without promoting research-only dimensions.; LIVE_READ_ONLY_PASS freshly verifies five target GUID/BREP/material/story signatures against accepted109 baseline, exact project identity/saved hash and unchanged existing SQLite journal. Actual shared Roof slope8.594366924degrees/15.1135218percent measured once; normative slope limit/verdict NOT_VERIFIED. No Create/Modify/Save/Open/IFC export/APX changes.; External dependencies retained within existing A02.S02: full primary applicable technical clauses/table rows, source-bound actual roof technology/layers, building work/purpose/area/regime/exclusions, engineering evidence. Next functional normative step uses these inputs in the existing evaluator, not a new library. A02.S02 remainsPARTIAL; A05.S01 requires its DONE_PUBLISHED dependency and cannot be dispatched or populated with invented loads.; Published draft PR68 head 29aa06a6e9bbef0d991bea922e1ad4101ab29bdd on exact PR67 base633c799da125622be6317ea9d09a9b7eb83fb98a;27newtests,573Windows host/Windows+LinuxCI38308362910 PASS.37code blobs and28pinned source files match GitHub; publisher receipt/readback verified.; Existing machine normative database dvikt33-ux/tdk-course-project normative-recovery-2026-10-06 commit67f17d407d14aebb091daaf79f11c10178b87440 is connected through the existing APA normative executor. Mandatory protocol read first; original source policies/schemas/routes/compiled blocks/aliases/evidence/rules unchanged. Byte-exact scoped source snapshot supplies existing CompiledBlockResolver and validate_confirmed, not a second normative engine.; Current project building type IZHS directly confirmed by user. Exact Project Profile -> Object/Module Route -> Applicable Rule -> Evidence Gate -> BIM Facts -> Rule Evaluation -> Result interface enforces defaultdeny and object/function/module/depth/stage isolation. MKD/TRC cannot borrow IZHS roof rules; one roof rules file read, inactive engineering libraries not loaded.; Four existing actual Wall/Roof junctions bind to nine existing canonical SP17 rules:36NOT_VERIFIED results. Stored evidence-field checks pass but source quarantine/design_only, unknown source-bound roof construction/applicability and declared-not-implemented upstream roof calculators prohibit authoritative stage pack, numeric evaluation or engineering acceptance. No normative values inferred or applied.; PR66/67 remain operational:24legacy bindings and12source checks preserved by digest and mapped to machine source identities without promotion. SP17 amendment1-5 chain and exact changed-table-row overlay gate retained; SP50.2024 passport identity is distinct from occurrence-level dependency resolution. No blanket pinning/floating or edition upgrade.; Prior109GUID native baseline, five source target signatures/material/story data and measured gaps reused as cached evidence. Zero new native calls, zero geometry rechecks, no PLN/APX modifications. Current live state is not independently refreshed in this package. NativeA11.S03PARTIAL/S10BLOCKED and prior accepted A04 evidence remain unchanged.; Next within existing A02.S02: source-bound actual roof system/layers/role and required block inputs; exact per-rule revision/clause/evidence/applicability closure and reviewed authoritative release; qualify an available existing roof calculator through the same interface. Unknown locality/load/engineering inputs remain unverified. Other domains extend the same reviewed exact route/source interface; no full library load or second engine. A02.S02PARTIAL; downstreamA05.S01 dependency remains unsatisfied.

## APA-P70.A02.S03

**Собрать проектный Library Pack из проверяемых строительных систем и узлов** — BUILD / DONE_PUBLISHED / P2

- Parent: APA-P70 → APA-P70.A02
- Topic: PRODUCT_DEVELOPMENT
- Work key: project-library-pack-assembly
- Depends on: APA-P70.A02.S01, APA-P70.A01.S03
- Related, check before duplicating: none
- Acceptance: Отобранные CSE, источники/хэши/лицензии, интерфейсы, совместимые AC29 объекты и список неподтверждённых узлов
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)
- Existing V2 runs: [APA-RUN-20261011-163145Z-p70-a02-s03-library-pack](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-163145Z-p70-a02-s03-library-pack/REPORT.md) (receipt verified)
- Expected output: Отобранные CSE, источники/хэши/лицензии, интерфейсы, совместимые AC29 объекты и список неподтверждённых узлов

## APA-P70.A02.S04

**Интегрировать реальные материалы, Composite/Profile и выбранные GDL-библиотеки** — INTEGRATION / DONE_PUBLISHED / P3

- Parent: APA-P70 → APA-P70.A02
- Topic: PRODUCT_DEVELOPMENT
- Work key: verified-project-material-library-integration
- Depends on: APA-P70.A09.S01
- Related, check before duplicating: none
- Acceptance: Проверенные CSE/PLP и реальные проектные BM/Composite/Profile/Surface/GDL применены и прочитаны обратно; Unicode и стабильная identity Library Parts проверены; источники/лицензия/AC29 совместимость учтены; найденный файл не равен LIVE_VERIFIED.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md)
- Existing V2 runs: [APA-RUN-20261011-211000Z-native-material-library-integration](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md) (receipt verified)
- Expected output: Проверенные CSE/PLP и реальные проектные BM/Composite/Profile/Surface/GDL применены и прочитаны обратно; Unicode и стабильная identity Library Parts проверены; источники/лицензия/AC29 совместимость учтены; найденный файл не равен LIVE_VERIFIED.

## APA-P70.A03.S01

**Связать помещения, несущую схему, оси, уровни и конструктивные ограничения** — INTEGRATION / DONE_PUBLISHED / P1

- Parent: APA-P70 → APA-P70.A03
- Topic: PRODUCT_DEVELOPMENT
- Work key: semantic-spatial-structural-plan
- Depends on: APA-P70.A02.S03
- Related, check before duplicating: none
- Acceptance: Проверяемый граф помещений/нагрузочных путей/осей с привязкой к CSE и этажам; без условных стен
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)
- Existing V2 runs: [APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md) (receipt verified)
- Expected output: Проверяемый граф помещений/нагрузочных путей/осей с привязкой к CSE и этажам; без условных стен

## APA-P70.A03.S02

**Собрать модель средствами уже существующих BIM-исполнителей** — BUILD / DONE_PUBLISHED / P0

- Parent: APA-P70 → APA-P70.A03
- Topic: PRODUCT_DEVELOPMENT
- Work key: reuse-native-whole-building-builder
- Depends on: APA-P70.A03.S01
- Related, check before duplicating: none
- Acceptance: Создание полноценной BIM-геометрии из схемы через имеющиеся writer/graph; связные стены не дробятся без необходимости; тестовый PLN только после разрешения
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-PR16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md), [ART-APA-LIVE-SCRATCH-PARTIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md), [ART-APA-PLN-WRITE-AUTH-20261011](../../../../../docs/research/apa-results/control/IMPLEMENTATION_ROADMAP.md%23%D1%80%D0%B0%D0%B7%D1%80%D0%B5%D1%88%D0%B5%D0%BD%D0%B8%D0%B5-%D0%B8-%D0%B4%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D1%8C%D1%81%D1%82%D0%B2%D0%B0)
- Existing V2 runs: [APA-RUN-20261011-165558Z-p70-a03-s02-native-graph-partial](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-165558Z-p70-a03-s02-native-graph-partial/REPORT.md) (receipt verified), [APA-RUN-20261011-195000Z-isolated-authored-core](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-195000Z-isolated-authored-core/REPORT.md) (receipt verified)
- Expected output: Создание полноценной BIM-геометрии из схемы через имеющиеся writer/graph; связные стены не дробятся без необходимости; тестовый PLN только после разрешения

## APA-P70.A03.S03

**Доказать редактируемость, GUID/host/story/material и инкрементальное обновление** — VALIDATION / DONE_PUBLISHED / P0

- Parent: APA-P70 → APA-P70.A03
- Topic: PRODUCT_DEVELOPMENT
- Work key: incremental-model-integrity-gates
- Depends on: APA-P70.A03.S02
- Related, check before duplicating: none
- Acceptance: Тесты обновления проекта без лишних элементов/потери GUID, readback этажей, материалов, хостов и откат изменений
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-APA-LIVE-SCRATCH-PARTIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md)
- Existing V2 runs: [APA-RUN-20261011-195800Z-incremental-native-edit](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-195800Z-incremental-native-edit/REPORT.md) (receipt verified)
- Expected output: Тесты обновления проекта без лишних элементов/потери GUID, readback этажей, материалов, хостов и откат изменений

## APA-P70.A03.S04

**Дополнить авторскую модель до связного небольшого здания существующими writer-циклами** — BUILD / DONE_PUBLISHED / P0

- Parent: APA-P70 → APA-P70.A03
- Topic: PRODUCT_DEVELOPMENT
- Work key: authored-building-native-component-completeness
- Depends on: APA-P70.A03.S02
- Related, check before duplicating: none
- Acceptance: Стены, перекрытия, колонны и hosted двери/окна из утверждённой схемы проходят typed GUID/host/story/material/geometry readback; требуемые неподдерживаемые элементы имеют конкретный blocker; один BIM Graph и SceneWriter.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)
- Existing V2 runs: [APA-RUN-20261011-200100Z-native-completeness](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200100Z-native-completeness/REPORT.md) (receipt verified)
- Expected output: Стены, перекрытия, колонны и hosted двери/окна из утверждённой схемы проходят typed GUID/host/story/material/geometry readback; требуемые неподдерживаемые элементы имеют конкретный blocker; один BIM Graph и SceneWriter.

## APA-P70.A04.S01

**Вывести из модели обязательные семейства узлов и их условия применимости** — INTEGRATION / DONE_PUBLISHED / P4

- Parent: APA-P70 → APA-P70.A04
- Topic: PRODUCT_DEVELOPMENT
- Work key: required-junction-condition-coverage
- Depends on: APA-P70.A03.S01, APA-P70.A02.S04
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Матрица всех применимых примыканий/отверстий/армопоясов/связей/крепежа с точным source/detail ID и открытыми пробелами
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-P70-A11-S03-NATIVE95-V32-20261012](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-110611Z-connected-native-continuation-v32/REPORT.md)
- Existing V2 runs: [APA-RUN-20261012-122511Z-construction-junctions-s01](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-122511Z-construction-junctions-s01/REPORT.md) (receipt verified), [APA-RUN-20261012-123259Z-construction-junctions-s01-openings](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-123259Z-construction-junctions-s01-openings/REPORT.md) (receipt verified)
- Expected output: Accepted-model construction junction/source coverage:47interfaces/34actual planar BREP contacts, actual0.4x0.6m Generic Opening host holes; seven model families incl absent cladding;73context/1142source Details;95GUID/body signatures retained;414Windows/LinuxPASS. Reinforcement/fastener/source-grade/full-assembly/engineering gaps explicit. Next ready bounded sub-junction:source PF001/PF002 batten/counterbatten contact.

## APA-P70.A04.S02

**Привязать выбранные узлы и композиции к нативным BIM элементам** — BUILD / DONE_PUBLISHED / P4

- Parent: APA-P70 → APA-P70.A04
- Topic: PRODUCT_DEVELOPMENT
- Work key: native-details-to-cse-binding
- Depends on: APA-P70.A04.S01, APA-P70.A03.S02
- Related, check before duplicating: none
- Acceptance: Редактируемые системы и узлы с параметрами, классификацией, происхождением и invalidation при изменении
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md)
- Existing V2 runs: [APA-RUN-20261012-130748Z-construction-junction-native-support-s02](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-130748Z-construction-junction-native-support-s02/REPORT.md) (receipt verified)
- Expected output: Editable source-bound ARMO PF001/PF002 batten/counterbatten support sub-junction: native50x50mm structural-timber Morph, existing Archicad2.0Beam classification,5.9801000489m model span, actual75cm2contact/no new collisions, pinned source/body/material/story invalidation.95accepted GUID/body signatures preserved,96GUID/38context saved/reopened.426Windows/LinuxPASS. Full assembly/fixings/grade/capacity and other families not inferred.

## APA-P70.A04.S03

**Проверить узлы окон, облицовки, перекрытий и кровельных примыканий** — VALIDATION / DONE_PUBLISHED / P4

- Parent: APA-P70 → APA-P70.A04
- Topic: PRODUCT_DEVELOPMENT
- Work key: junction-evidence-acceptance
- Depends on: APA-P70.A04.S02
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Для каждого узла классификация PASS_GEOMETRY/PASS_DOCUMENTED/PASS_ENGINEERING/NOT_VERIFIED; ложные approvals запрещены
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12)
- Existing V2 runs: [APA-RUN-20261012-132353Z-construction-junction-qualification-s03](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-132353Z-construction-junction-qualification-s03/REPORT.md) (receipt verified)
- Expected output: All49actual candidate native interface pairs independently graded:34PASS_GEOMETRY,1PASS_DOCUMENTED bounded source support,14NOT_VERIFIED,0PASS_ENGINEERING. New50x50mm timber/Beam-classified Morph contact75cm2/material/story/placement validated after save/reopen.95accepted GUID/body signatures preserved,96current GUID/38context. Current IFC45elements/38bounds matches/new IfcBeam material/11port links/12quantitymatches0mismatch.432Windows/LinuxPASS. Complete families, cladding, fixings/grades/structural capacity and visible3D remain NOT_VERIFIED. Qualification complete; whole-family construction acceptance not inferred.

## APA-P70.A05.S01

**Получить проверяемую расчётную схему и исходные нагрузки** — INTEGRATION / READY / P4

- Parent: APA-P70 → APA-P70.A05
- Topic: PRODUCT_DEVELOPMENT
- Work key: load-bearing-design-and-load-cases
- Depends on: APA-P70.A03.S01, APA-P70.A02.S02, APA-P70.A04.S03
- Related, check before duplicating: none
- Acceptance: Нагрузки, расчётная схема, несущие стены/пролёты/фундаменты/стропила, комбинации и неподтверждённые допущения отдельно
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
- Existing V2 runs: none
- Expected output: Нагрузки, расчётная схема, несущие стены/пролёты/фундаменты/стропила, комбинации и неподтверждённые допущения отдельно

## APA-P70.A05.S02

**Использовать SAM/SAF/IFC и доступный проверенный расчётный движок** — BUILD / READY / P4

- Parent: APA-P70 → APA-P70.A05
- Topic: PRODUCT_DEVELOPMENT
- Work key: structural-engine-adapter-handoff
- Depends on: APA-P70.A05.S01, APA-P70.A03.S02
- Related, check before duplicating: none
- Acceptance: Экспорт и сверка идентичности элементов, материалов, уровней; расчёт только в доступном проверенном инструменте, отсутствие доступа явно BLOCKED
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Экспорт и сверка идентичности элементов, материалов, уровней; расчёт только в доступном проверенном инструменте, отсутствие доступа явно BLOCKED

## APA-P70.A05.S03

**Применить результаты инженерного расчёта и повторно проверить узлы** — VALIDATION / READY / P4

- Parent: APA-P70 → APA-P70.A05
- Topic: PRODUCT_DEVELOPMENT
- Work key: engineering-feedback-to-bim
- Depends on: APA-P70.A05.S02, APA-P70.A04.S02
- Related, check before duplicating: none
- Acceptance: Контролируемое внесение инженерных изменений в BIM; сверка с расчётом и запись необходимости согласования специалистом
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Контролируемое внесение инженерных изменений в BIM; сверка с расчётом и запись необходимости согласования специалистом

## APA-P70.A06.S01

**Сформировать инженерные требования и трассы на базе штатного MEP** — INTEGRATION / READY / P5

- Parent: APA-P70 → APA-P70.A06
- Topic: PRODUCT_DEVELOPMENT
- Work key: native-mep-semantic-network
- Depends on: APA-P70.A03.S02, APA-P70.A02.S02, APA-P70.A05.S03
- Related, check before duplicating: none
- Acceptance: Проверенные системы труб/воздуховодов с сетью и портами, применимые нормы и явные незакрытые расчёты
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md)
- Existing V2 runs: none
- Expected output: Проверенные системы труб/воздуховодов с сетью и портами, применимые нормы и явные незакрытые расчёты

## APA-P70.A06.S02

**Проверить инженерные сети, проходки, коллизии и узлы пересечений** — VALIDATION / READY / P5

- Parent: APA-P70 → APA-P70.A06
- Topic: PRODUCT_DEVELOPMENT
- Work key: mep-junction-collision-acceptance
- Depends on: APA-P70.A06.S01, APA-P70.A04.S02
- Related, check before duplicating: none
- Acceptance: Readback связности и коллизий, согласованные проходки/узлы без ложных PASS и без потери идентичности
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Readback связности и коллизий, согласованные проходки/узлы без ложных PASS и без потери идентичности

## APA-P70.A07.S01

**Получить согласованные планы, разрезы, фасады, спецификации и узлы** — BUILD / READY / P7

- Parent: APA-P70 → APA-P70.A07
- Topic: PRODUCT_DEVELOPMENT
- Work key: native-project-documentation-views
- Depends on: APA-P70.A03.S03, APA-P70.A04.S02, APA-P70.A10.S01
- Related, check before duplicating: none
- Acceptance: Чертежи и ведомости из одной BIM-модели, соответствие срезов/количеств/версий, без ручных дублирующих источников
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml)
- Existing V2 runs: none
- Expected output: Чертежи и ведомости из одной BIM-модели, соответствие срезов/количеств/версий, без ручных дублирующих источников

## APA-P70.A07.S02

**Выполнить поэлементную и общепроектную проверку нормативов** — VALIDATION / READY / P7

- Parent: APA-P70 → APA-P70.A07
- Topic: PRODUCT_DEVELOPMENT
- Work key: revisioned-compliance-and-coverage-report
- Depends on: APA-P70.A07.S01, APA-P70.A05.S03, APA-P70.A06.S02
- Related, check before duplicating: none
- Acceptance: Матрица применимых требований: PASS/FAIL/NOT_VERIFIED/NEEDS_SPECIALIST с источниками и журналом пересчётов
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Матрица применимых требований: PASS/FAIL/NOT_VERIFIED/NEEDS_SPECIALIST с источниками и журналом пересчётов

## APA-P70.A07.S03

**Собрать итоговый пакет BIM/IFC/PDF и доказательства проверки** — BUILD / READY / P7

- Parent: APA-P70 → APA-P70.A07
- Topic: PRODUCT_DEVELOPMENT
- Work key: verified-final-project-release
- Depends on: APA-P70.A07.S02
- Related, check before duplicating: none
- Acceptance: Ревизионно согласованный комплект проекта с provenance и инженерными ограничениями; выпуск только после всех gates
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Ревизионно согласованный комплект проекта с provenance и инженерными ограничениями; выпуск только после всех gates

## APA-P70.A08.S01

**Проверить полный цикл создания проекта на эталонном ИЖС** — VALIDATION / READY / P8

- Parent: APA-P70 → APA-P70.A08
- Topic: PRODUCT_DEVELOPMENT
- Work key: full-cycle-new-project-e2e
- Depends on: APA-P70.A07.S03
- Related, check before duplicating: none
- Acceptance: По одному brief сформирован редактируемый расчётно обоснованный проект; сохраняется, повторно открывается и читается; отдельное live-разрешение
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-PR16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16)
- Existing V2 runs: none
- Expected output: По одному brief сформирован редактируемый расчётно обоснованный проект; сохраняется, повторно открывается и читается; отдельное live-разрешение

## APA-P70.A08.S02

**Проверить доработку единственного открытого существующего PLN** — VALIDATION / READY / P8

- Parent: APA-P70 → APA-P70.A08
- Topic: PRODUCT_DEVELOPMENT
- Work key: full-cycle-adapt-existing-e2e
- Depends on: APA-P70.A08.S01
- Related, check before duplicating: none
- Acceptance: ADAPT_EXISTING: проект дорабатывается без переключения/изменения чужого PLN; изменение только с разрешением, воспроизводимый readback
- Owner/lease: unclaimed
- Requires owner approval: True
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
- Existing V2 runs: none
- Expected output: ADAPT_EXISTING: проект дорабатывается без переключения/изменения чужого PLN; изменение только с разрешением, воспроизводимый readback

## APA-P70.A08.S03

**Доказать расширяемость на другом типе здания и системах** — VALIDATION / READY / P8

- Parent: APA-P70 → APA-P70.A08
- Topic: PRODUCT_DEVELOPMENT
- Work key: building-type-extension-contract
- Depends on: APA-P70.A08.S02
- Related, check before duplicating: none
- Acceptance: Новый тип здания или конструктивная система подключается без нового параллельного генератора и без регрессии старого проекта
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
- Existing V2 runs: none
- Expected output: Новый тип здания или конструктивная система подключается без нового параллельного генератора и без регрессии старого проекта

## APA-P70.A08.S04

**Принять ядро: задание → связное редактируемое здание → правка → readback** — VALIDATION / DONE_PUBLISHED / P0

- Parent: APA-P70 → APA-P70.A08
- Topic: PRODUCT_DEVELOPMENT
- Work key: editable-native-core-e2e-acceptance
- Depends on: APA-P70.A03.S03, APA-P70.A03.S04
- Related, check before duplicating: none
- Acceptance: Один brief создаёт связное небольшое здание; все требуемые типы поддержаны, GUID/этажи/материалы/host/геометрия подтверждены; согласованная правка сохраняет GUID и не дублирует модель; сохранение и повторное чтение подтверждены. Четыре элемента и offline CI не достаточны. Инженерная/нормативная приёмка отдельно.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)
- Existing V2 runs: [APA-RUN-20261011-200500Z-editable-core-acceptance](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md) (receipt verified)
- Expected output: Один brief создаёт связное небольшое здание; все требуемые типы поддержаны, GUID/этажи/материалы/host/геометрия подтверждены; согласованная правка сохраняет GUID и не дублирует модель; сохранение и повторное чтение подтверждены. Четыре элемента и offline CI не достаточны. Инженерная/нормативная приёмка отдельно.

## APA-P70.A08.S05

**Адаптировать готовое ядро под установленный Archicad 30** — INTEGRATION / READY / P8

- Parent: APA-P70 → APA-P70.A08
- Topic: PRODUCT_DEVELOPMENT
- Work key: archicad30-existing-core-adaptation
- Depends on: APA-P70.A08.S03
- Related, check before duplicating: none
- Acceptance: После установки AC30 подтверждены API/библиотеки/проектный сценарий тем же ядром; нет отдельного генератора. Отсутствующая установка — конкретный BLOCKED, не ложный PASS.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
- Existing V2 runs: none
- Expected output: После установки AC30 подтверждены API/библиотеки/проектный сценарий тем же ядром; нет отдельного генератора. Отсутствующая установка — конкретный BLOCKED, не ложный PASS.

## APA-P70.A09.S01

**Подключить Native Model Dump, графовую связность и реальные 3D-проверки** — INTEGRATION / DONE_PUBLISHED / P2

- Parent: APA-P70 → APA-P70.A09
- Topic: PRODUCT_DEVELOPMENT
- Work key: integrated-native-3d-geometry-precision
- Depends on: APA-P70.A08.S04
- Related, check before duplicating: none
- Acceptance: Native dump/NetworkX/Shapely используются через существующий readback; стыки, XYZ, story и host проверены на подтверждённых ошибках; 2D пересечение не считается 3D коллизией; ядро сохраняет работоспособность.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-SDK-SEO](../../../../../docs/research/apa-results/runs/2026-10-10/apa-discovery-20261010-102440-slinktrim-9f2b7.md)
- Existing V2 runs: [APA-RUN-20261011-202800Z-native-geometry-integration](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md) (receipt verified)
- Expected output: Native dump/NetworkX/Shapely используются через существующий readback; стыки, XYZ, story и host проверены на подтверждённых ошибках; 2D пересечение не считается 3D коллизией; ядро сохраняет работоспособность.

## APA-P70.A10.S01

**Оптимизировать конкретный стабильный сценарий с измерением результата** — INTEGRATION / READY / P6

- Parent: APA-P70 → APA-P70.A10
- Topic: PRODUCT_DEVELOPMENT
- Work key: stable-native-pipeline-measured-optimization
- Depends on: APA-P70.A06.S02
- Related, check before duplicating: none
- Acceptance: Есть воспроизводимый baseline и измеримое улучшение времени/числа native calls/ресурсов без потери точности; OR-Tools/CP-SAT внедряется лишь при явных ограничениях и критерии качества.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md)
- Existing V2 runs: none
- Expected output: Есть воспроизводимый baseline и измеримое улучшение времени/числа native calls/ресурсов без потери точности; OR-Tools/CP-SAT внедряется лишь при явных ограничениях и критерии качества.

## APA-P70.A11.S01

**Подключить готовые компоненты совместимым пакетом** — INTEGRATION / DONE_PUBLISHED / P1

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: compatible-component-batch-v31
- Depends on: APA-P70.A02.S04
- Related, check before duplicating: none
- Acceptance: Ready donor functions execute through shared XYZ/GUID/story/material/host context. Functional geometry/Details/MEP/IFC adapters integrated where implementation exists; research-only and missing provider functions explicitly identified. Independent optional modules disabled safely; no second writer or placeholder/catalog-only PASS.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: [APA-RUN-20261012-010000Z-compatible-integration-v31](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-010000Z-compatible-integration-v31/REPORT.md) (receipt verified)
- Expected output: Ready donor functions execute through shared XYZ/GUID/story/material/host context. Functional geometry/Details/MEP/IFC adapters integrated where implementation exists; research-only and missing provider functions explicitly identified. Independent optional modules disabled safely; no second writer or placeholder/catalog-only PASS.

## APA-P70.A11.S02

**Проверить объединённую систему в тестовом PLN** — VALIDATION / DONE_PUBLISHED / P1

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: connected-system-native-test-v31
- Depends on: APA-P70.A11.S01
- Related, check before duplicating: none
- Acceptance: Reproducible combined native scenario uses retained graph/journal/writer/readback; source elements preserved, save/reopen verified. Source/offline/live/engineering statuses separate. Unsupported mandatory module never silently omitted.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: [APA-RUN-20261012-011500Z-connected-system-v31](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-011500Z-connected-system-v31/REPORT.md) (receipt verified)
- Expected output: Reproducible combined native scenario uses retained graph/journal/writer/readback; source elements preserved, save/reopen verified. Source/offline/live/engineering statuses separate. Unsupported mandatory module never silently omitted.

## APA-P70.A11.S03

**Исправить пробелы после системного теста** — INTEGRATION / PARTIAL / P1

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: system-gap-driven-development-v31
- Depends on: APA-P70.A11.S02
- Related, check before duplicating: APA-P70.A11.S06, APA-P70.A11.S07, APA-P70.A11.S08, APA-P70.A11.S09, APA-P70.A11.S10, APA-P70.A04.S01, APA-P70.A04.S03
- Acceptance: Observed gaps reconciled against donors/archives and fixed with real behavior and regression proof; no duplicated subsystem without reason. UNIVERSAL_NATIVE_FIRST_20261014: Universal APA Archicad29 Windows11 development resumes. TRC project is excluded from current trials and further analysis/writes require a separate task. Existing authorized native test PLN only; priority actual external candidate load, true Grid create/read/edit/reuse and exact Stair native readback, then Roof contour/slope and connected BIM operations. Windows-only CI. Functional completeness precedes scale; 2D counts are not BIM scalability evidence.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: [APA-RUN-20261012-012500Z-gap-windows-sqlite-v31](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-012500Z-gap-windows-sqlite-v31/REPORT.md) (receipt verified), [APA-RUN-20261012-075300Z-functional-gaps-v31](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-075300Z-functional-gaps-v31/REPORT.md) (receipt verified), [APA-RUN-20261012-095401Z-functional-expansion-v32](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-095401Z-functional-expansion-v32/REPORT.md) (receipt verified), [APA-RUN-20261012-110611Z-connected-native-continuation-v32](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-110611Z-connected-native-continuation-v32/REPORT.md) (receipt verified), [APA-RUN-20261012-144857Z-native-beam-mep-reference200-followon](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-144857Z-native-beam-mep-reference200-followon/REPORT.md) (receipt verified), [APA-RUN-20261012-175944Z-wall-roof-actual-underside-native109](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-175944Z-wall-roof-actual-underside-native109/REPORT.md) (receipt verified), [APA-RUN-20261012-185427Z-four-real-wall-roof-native109](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-185427Z-four-real-wall-roof-native109/REPORT.md) (receipt verified), [APA-RUN-20261012-235115Z-bim-documentation](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-235115Z-bim-documentation/REPORT.md) (receipt verified), [APA-RUN-20261013-013642Z-knowledge-core-mcp](../../../../../docs/research/apa-results/runs/2026-10-13/APA-RUN-20261013-013642Z-knowledge-core-mcp/REPORT.md) (receipt verified), [APA-RUN-20261013-082134Z-native-documentation-followon](../../../../../docs/research/apa-results/runs/2026-10-13/APA-RUN-20261013-082134Z-native-documentation-followon/REPORT.md) (receipt verified), [APA-RUN-20261013-121018Z-model-first-building](../../../../../docs/research/apa-results/runs/2026-10-13/APA-RUN-20261013-121018Z-model-first-building/REPORT.md) (receipt verified), [APA-RUN-20261013-165220Z-native-spatial](../../../../../docs/research/apa-results/runs/2026-10-13/APA-RUN-20261013-165220Z-native-spatial/REPORT.md) (receipt verified), [APA-RUN-20261013-184337Z-grid-stair-exact](../../../../../docs/research/apa-results/runs/2026-10-13/APA-RUN-20261013-184337Z-grid-stair-exact/REPORT.md) (receipt verified), [APA-RUN-20261013-200350Z-grid-stair-live-checkpoint](../../../../../docs/research/apa-results/runs/2026-10-13/APA-RUN-20261013-200350Z-grid-stair-live-checkpoint/REPORT.md) (receipt verified), [APA-RUN-20261013-234433Z-true-grid-live-stair-runtime](../../../../../docs/research/apa-results/runs/2026-10-13/APA-RUN-20261013-234433Z-true-grid-live-stair-runtime/REPORT.md) (receipt verified), [APA-RUN-20261014-074612Z-universal-native-floor-contours](../../../../../docs/research/apa-results/runs/2026-10-14/APA-RUN-20261014-074612Z-universal-native-floor-contours/REPORT.md) (receipt verified)
- Expected output: Observed gaps reconciled against donors/archives and fixed with real behavior and regression proof; no duplicated subsystem without reason.; Historical PR55 baseline: Published PR55 head3191e7ce5071e6de7401f6e520fbd8f3ef2a1ea2 stacked on PR54;31new tests,371/371Windows/LinuxPASS.; Historical PR55 baseline: Details73context/source/host/material/fact exchange, reciprocal two-section MEP, Generic Opening/SEO, specialized metadata and IFC host/port observations work together.; Historical PR55 baseline: Saved/reopened isolated PLN:27primary/59totalGUID, all original48GUID/geometry preserved; SHA256da37fa0fe9b1b255f1618a881a79eb9d4ae8b66993a99cb75fdba30cddc69bb4. Engineering/visibleUI NOT_VERIFIED.; Historical PR56 baseline: Current published draft PR56 head3a743a4f96a98acdcbb837946603f0681d9a1f54:403/403Windows host and Windows/Linux CI PASS; all11GitHub code blobs and all15publication blobs exactly match committed/generated bytes.; Historical PR56 baseline: LIVE_PASS working routed graph:7routes/9segments/12physical members/11reciprocal edges, one three-port-connected tee and two elbows; exact architectural collisions empty. Native default terminal is separately read back but open/outside routed scope.; Historical PR56 baseline: LIVE_PASS independent Details c4 timber part:source25x150mm section, actual10mroof span/slope/story/material, model-bound placement and empty exact collision readback; full8-dimension manufacturer assembly and native roof-child relationship not claimed.; Historical PR56 baseline: Save/reopen95GUID and37context records; all95resultant geometry signatures unchanged, original48/baseline59preserved. PLN SHA256dea93fe0fd520747bf4fee5f12d86372f57d972a7021b65029419d2d127892c8.; Historical PR56 baseline: Actual IFC37/37world bounds and all11native/IFCowner-pair multiplicities agree;44elements/19materials/39classifications/26ports. Twelve verified quantity comparisons match,0verified mismatch. Engineering/full receiver semantics remain NOT_VERIFIED.; Historical PR57 qualification: Current continuation: A04.S01-S03 qualification/source-bound support published. S10 ready Create reference selector found read-only; actual transition/terminal connection unverified. S06-S09 retain existing source/Shell/analytical/receiver gates. S04 waits real A11.S03 completion.; Historical draft PR57 headb1abd584585feb0f286621337986c8a5d3077507:432/432Windows host and Windows/LinuxCI PASS;96GUID/38context saved/reopened, all95accepted GUID/body signatures preserved. Native source c4/c5support contact75cm2 and timber/Beam classification;49interface grades with no family/engineering promotion; IFC38/38bounds/45elements/20material assignments/11port links.; Historical draft PR59 head744e0bd184a11f1de4a1cf16382d21aec6f8cfca on exact PR57 headb1abd584585feb0f286621337986c8a5d3077507:455/455Windows host and Windows/LinuxCI PASS,23new checks. All13code and11evidence/report GitHub blobs exactly match; publisher receipt DONE_PUBLISHED.; LIVE_PASS actual new route-local crossSectionReferenceId200 gives circular diameter0.2m and automatically connects the original terminal with reciprocal physical ports. Unique current preference row/identity/journal verified; no global preferences/APX changes. Full8route graph has2components; main circular/rectangular bridge remains S10 BLOCKED.; LIVE_PASS real native Beam25x150mm and Beam50x50mm with actual75cm2Beam/Beam contact, source dimensions, Wood material/story/profile and SDK-owned BeamSegments. Native vertical end cut gives73.1108100945cm2contact to retained Morph batten, explicitly distinguished from nominal75cm2. Original Morph support is retained. Single confirmed profile edit and independent modulo2pi reconciliation; zero mutation replays.; LIVE_PASS bounded new Wall/Roof Trim perimeter abutment3.236340608m2 with no new volume collision; not underside bearing. Four original upper Wall/Roof gaps unchanged. Reverse Wall trim metadata returns installed provider target-row error. SEO relation accepted but no incremental body change/underside goal; engineering and full family remain NOT_VERIFIED.; Historical PR59: LIVE_PASS saved/reopened107GUID/43shared context; all96PR57GUID/geometry/material/story preserved. Independent final readback and baseline collision pairs agree. PLN SHA25647366e08ecdc7cd5340480c7e0bd455e8ab0aaea64b1321085d9fdbad1a2591c.; Actual IFC50elements/43of43world bounds,24material assignments,12port relations,6opening hosts and18native/IFCquantity matches with0mismatch. True nativeBeam/IfcBeam distinct from retained Morph/IfcBeam and Morph/IfcBuildingElementProxy. Structural contact/Trim/SEO relationship semantics and full receiver compatibility NOT_VERIFIED.; Permanent MORPH LAST RESORT published in canonical operating instruction/plan and feature AGENTS; runtime creation/geometry edit requires documented checked native tool rejection and preserved mandatory BIM properties/relationships. Source c4/c5 must use real Beam. A04.S01-S03 DONE_PUBLISHED retained; S03 remainsPARTIAL and S04 waits its acceptance.; Historical PR59 next work: qualify a supported sized circular/rectangular transition and main bridge preserving accepted96GUID, and independently qualify native Wall/Roof underside bearing from verified geometry/source. S06-S09 external source, Shell/edit, analytical and receiver dependencies remain explicit; no new roadmap or writer.; Historical draft PR63 head7966db58ca8830b43938a03cc064bcc3e952a21e, exact PR59 parent744e0bd184a11f1de4a1cf16382d21aec6f8cfca.469/469Windows host and Windows/LinuxCI38287308901 PASS;14new focused checks. All6code blobs and12native/source/report blobs match GitHub exactly; publisher receipt DONE_PUBLISHED.; LIVE_PASS new true native Wall/Roof lower-face contact2.33623338255613m2 versus measured-source expected2.336233382576165m2. Actual lower principal BREP plane and contact face contours/holes verified; Wall body changed, all Wall vertices below underside. Materials/story/native types correct; native pair and architecture collision checks empty.; Working existing SceneWriter recipe:2native creates and1SubtractionUpwardsSEO; no Morph/new executor/prior accepted experiment replay. Shared actual planar face reader and actual sloped wall-cap overlap measure all4original upper Wall/Roof gaps. Original4gaps and accepted perimeter specimen preserved.; Requested skipPolygonHoles=true but native relation reads false. Flag metadata NOT_VERIFIED_REQUEST_READBACK_DIFFERENCE; actual underside geometry/SEOrelation independently proven. Initial strict flag-check failure retained in journal and reconciled read-only, zero native replay. GetFlags source ignores SDK return code; cause/application is not inferred.; LIVE_PASS saved/reopened109GUID/45shared records; all107accepted GUID/body/material/story signatures preserved, including prior96. Independent final geometry/network/collision readback PASS. PLN SHA2560d87954de1a0b75f0510c4bbd1a7424db2eb09fa928d5e0fb746c58d9a18f14d. User authorized renamed isolated copy; exact identity/saved hash and107baseline verified before writing; full paths/raw files stay local.; Actual IFC52elements/45of45world bounds/26material assignments/12port relations/6opening hosts/20quantitymatches/0mismatch. New true native Wall/IfcWall and Roof/IfcRoof BREP/material quantities agree. Native contact/SEOexport semantics, full receiver and engineering remain NOT_VERIFIED.; S10BLOCKED remains only sized circular/rectangular transition/main bridge: closed CreateMEPElements default-placement enum lacks sized ports; exposed route Place supplies empty per-segment section maps despite SDK support. SDK TransitionDefault is non-geometric settings, not a sized standalone factory. Existing8routes/two components/Ø200terminal pair unchanged; no ConnectLogically on retained routes, APX or global preference change.; Exact continuation: qualify the tested native underside recipe for required actual building interfaces, explicitly binding any intended target geometry change and edge overlap; retain GUIDs and do not invent overhang/fastening/load dimensions. S10 needs an exposed qualified route-local mixed-section and GUID-preserving physical connection contract; installed APX changes require separate authorization. Existing S06-S09 dependencies and S04 acceptance gate remain. A11.S03PARTIAL; A04.S01-S03DONE_PUBLISHED retained.; Current draft PR64 headb056cb76929a62047c82fd66961b72eb4d9078a8 on exact PR63 parent7966db58ca8830b43938a03cc064bcc3e952a21e.495/495Windows host and Windows/LinuxCI38292933894 PASS;26new checks. All6code blobs and12native/source/report blobs match GitHub; publisher receipt DONE_PUBLISHED.; LIVE_READ_ONLY_PASS current109GUID/body/material/story signatures, saved-file SHA and existing SQLite scene journal unchanged; known diagnostic Morph collision retained, no new collisions. Zero Create/Modify/Save/Open/IFC export; accepted PR63 specimen was not repeated.; Working four-target CLI joins actual Native Model Dump lower-face contours/holes, native typed details/materials/story, existing73Details/CSE source candidates and one shared Roof dependency. Four measurements VERIFIED; direct complete-cap repair NOT_APPLICABLE for all4 current boundary walls. Actual cap coverage east48.192771percent/north59.063104percent/south39.436896percent/west50percent.; Four correction plans bind exact source hashes and actual uncovered-cap polygons. First qualify a native SinglePlane Roof contour/edge design; then remeasure coverage before Wall-height+SubtractionUpwardsSEO. Existing inspected ModifyRoofs implementation rejects SinglePlane roofs despite schema polygon fields; native UI/SDK single-plane memo path needs qualification. No invented overhang/fixing/bearing/load dimensions.; Same SceneWriter now supports narrowly qualified exact ModifyWalls height. Two-operation application has OFFLINE_PASS synthetic native/SQLite callback checks: exact reviewed plan and separately approved copy, complete baseline protection, actual cap/underside/contact/material/story/placement/SEO/collision checks, stop on unknown result. No new LIVE write acceptance. All four original target edits require separate copy and operation authorization.; Read-only retained SEO relation queried from target/operator sides: both skipPolygonHolesfalse vs recorded requesttrue. Metadata/cause/applied flag remain NOT_VERIFIED. SDK bit mapping agrees; source getter ignores SDK error code. Hole-free specimen geometry cannot establish hole-skip behavior. APX untouched.; Exact next native step: qualify source-bound SinglePlane contour editing and approved roof contour in a separate authorized saved copy, then rerun the existing four-target assessment; only APPLICABLE_NOT_EXECUTED complete-cap plans may enter the same writer. S10 remainsBLOCKED with existing source/port/GUID-safe main-bridge reason, no repeated MEP transition investigation. Existing independent eligible task continues after publication. S03PARTIAL; A04.S01-S03DONE_PUBLISHED retained.; PR67 source-verified installed Archicad29 DevKit polygon example explicitly accepts plane roofs and uses GetMemo/ChangeMemo with polygon/edge/side-material/roof-edge masks. Sample may clear edge customizations; preservation/synchronization must be qualified. Exposed installed callable edit and binary/source correspondence NOT_VERIFIED; inspected ModifyRoofs rejects SinglePlane. No installed APX change.; Working non-executable SinglePlane candidate in existing native adapter binds actual source body/details, native GUID/material/story, memo/principal contours and exact sourced design proposal. Current native memo/reference contour matches upper actual face; lower footprint has actual29.887626mmXY offset. Original four junctions and their geometry/plans remain unchanged. Source holes/topology changes reject without a qualified memo contract.; Exact native next step: approve actual roof design/contour and a separate saved copy, qualify an available exposed SDK/UI memo operation preserving all edge data/holes, then use the existing SceneWriter once with independent actual lower-contact/collision/GUID/material/story and Save/Open readback. Candidate/source contract is not LIVE write acceptance. S03PARTIAL/S10BLOCKED retained.; Published draft PR70 head f5aa4754a0ace251e8541001f17f6fa8eddfe8e5 based on exact PR68 head29aa06a6e9bbef0d991bea922e1ad4101ab29bdd.14newtests;587/587Windows host and Windows/Linux CI38323722458PASS. Six code blobs and architecture evidence/report/receipt independently matched GitHub.; Architectural documentation adapter uses the existing SceneWriter/SQLite ledger, Native Model Dump, BIM facts and existing IFC planar BREP quantity adapter. No second executor/drawing engine/controller. Normative database/executor/policies and GitHub search/token-optimization work excluded and untouched.; LIVE: native floor0 saved associative plan, one new native Section and one native InteriorElevation exterior projection;4explicit saved ViewMap entries. Section readback16selected owners; limited projection4selected owners (Column/Door/Wall/Window). Reused true Elevation view is empty: NOT_VERIFIED as full facade. CreateElevations and vertical2D primitive readback contracts absent; rendered/visible drawing acceptance not claimed.; Six CSV native-fact specifications share one immutable modelVersion for19primary elements:9Wall,2Slab,2Column,4Window,1Door,1Roof. Wall/Slab quantities use actual resultant bodies; Column parent body absent and Door quantities unsupported remain explicit. Native interactive schedule row/configuration contract absent; CSV is not native schedule acceptance. Some Native Model Dump display labels damaged; identities/numeric stories retained, damaged labels not promoted.; One new separate native Wall changed height1.0->1.2m and actual joined volume0.085->0.102m3. Native floor cutfills15->16; adjoining Column drawing facts changed while its native3D signature stayed unchanged. Explicit public refresh regenerated linked native databases and owner readback after change and after Open. No background watcher; full vertical drawn-coordinate synchronization NOT_VERIFIED. Original ambiguous Modify ledger event preserved and independently reconciled without repeat.; Save/Open PASS with independent final native readback: original109GUID/geometry/material/story signatures unchanged; full inventory121 includes newWall+CutPlane+InteriorElevation+9native Object markers/subordinates.112explicit retained persistence identities plus separate ViewMap/database checks. Authorized isolated testPLN savedSHA256c7350d717e223fd5ec8e82dbaa44197e4483a54b31c54c3913e317a0893054c9. No new testWall volume collision. No Morph/APX/global preference change; raw identities/PLN/paths remain local.; A11.S03 remains PARTIAL and A11.S10 remains BLOCKED. This is preparatory architectural functionality for A07.S01; dependencies and status unchanged, not closed. Normative/engineering acceptance NOT_EXECUTED, PDF/nativePublisher output NOT_EXECUTED. Next available documentation work: qualify true exterior Elevation placement, vertical primitive readback and native schedule rows through the same executor, then actual publisher-file proof. No normative/search re-research.; Published draft PR71 head88169d358e4c329f8959f557c944300adcec2df9 on exact PR70 f5aa4754a0ace251e8541001f17f6fa8eddfe8e5.19newtests;606/606APA and102/102upstream Windows host/Windows+Linux CI38332614305 PASS including actual separate MCP stdio client.29code blobs and evidence/report/receipt independently read back; publisher receipt DONE_PUBLISHED.; StageI DONE: existing PR69 component tools/apa_knowledge_graph transferred19files unchanged from merge64cec581b257b209a097556ae19d498e53631ba1, eight runtime source hashes pinned. APA core read-only feature-flag entry points directly call original gateway/graph/sections/multidoc/delta/bootstrap/machine/mcp modules. Default flag off; no second search engine/task controller/publisher/normative executor.; Current GitHub source capture at revision128: project/status/lease and S-ID/ART-ID, shared document references, scheduling dependencies, possible changed-artifact impact, next eligible suggestions without claim, source-bound TDK design_only trace and pinned small PR70 source fragment. Each live request checks current canonical commit/plan bytes, graph integrity and returned source bytes. LOCAL_CHECKOUT explicitly local-only, cache never task authority; source texts untrusted data.; Actual canonical plan127->128 CAS reservation is detected as STALE_INDEX_REMOTE_PLAN on an independently retained historical source copy; safe source refresh/original bootstrap rebuild restores verified response. Corrupt source/forged index/denied source class/unavailable remote reject without authority fallback. Caller SOURCE_VERIFIED labels do not grant verified field propagation; only operator-reviewed exact lineage digest allowed. No guessed semantic edges or engineering/normative promotion.; StageII localMCP DONE: official Python SDK2.3.0 actual client launches separate stdio server and calls only apa_retrieve for task/artifact and denied source class. No model-supplied paths, BIM writes or task management. Target ChatGPT registration/call NOT_VERIFIED; current official Secure MCP Tunnel/ChatGPT operator steps documented, account/workspace association unavailable here. No server registration, tunnel, external deployment or paid model calls.; StageIII measured five real core queries and ordinary GitHub plan GET separately: payload bytes/chars, latency, GET counts and o200k_base tokenizer proxy. Captured raw plan286718bytes/77867proxy tokens; compact query payloads approximately386-662proxy tokens. Exact requests use2freshness GETs, section case5, ordinary plan GET1; no universal token/latency/call saving claim. Exact oracle91tasks/173artifacts/40shared-reference pairs has0failures; broad semantic missed/false dependencies and actual billed GPT tokens NOT_MEASURED. Prior research benchmarks retained.; PR70 documentation/BIMGraph/SceneWriter and normative modules unchanged; full587prior tests retained within606. Zero Archicad calls, PLN/APX/main changes in this package; prior saved native121inventory is historical evidence, not newly checked live. Normative parallel system untouched. A11.S03 remainsPARTIAL/A11.S10BLOCKED; A07 status/dependencies unchanged. P50.A01.S04 not admitted: compatible core scope already usesA11.S03; broader80question semantic proposal remainsNEEDS_EVIDENCE for independent audit.; Next available knowledge step: operator-supported ChatGPT tunnel/endpoint registration and actual apa_retrieve call with fresh provenance. On any canonical revision change, fetch the operator-owned source checkout and rebuild the same cache or returnSTALE_INDEX; no automated CAS claim. Independent native documentation work still needs trueElevation/vertical primitive/native schedule-row contracts. No repeated normative research or new roadmap.; Published draft PR73 head93557ed0cd59c471b0f903a03708ed88c8feb31b on exact PR71 head88169d358e4c329f8959f557c944300adcec2df9.17newtests;623/623APA host and Windows/Linux CI38367671224PASS;102/102upstream graph tests and core/MCP integration in each environment. Six code blobs, native evidence/report/receipt independently read back. Full committed diff privacy scan PASS.; Real native exterior Elevation copied from an accepted template via retained SceneWriter/SQLite, without CreateElevations contract or InteriorElevation/Morph substitution. Initial finite segment captured half the building; user screenshot identified scope failure. Only newly created Elevation movedprojectY-5m. Rebuild/update/readback and rendered native PDF now show full west face, both stories/windows and complete roof. Native roof horizontal span8.029912m vs actual BREP projection8.029888m within0.0001m. Visible owners9->12 are not used alone as full-facade proof.; New associative native Section dimension reports0.20000006m actual Slab thickness with5native witness coordinates and verified SectionElement->Slab ownership. Native Drawing fill contours32plan/34section; inverse Drawing-transform vertical levels agree with dimension witnesses within0.000001m. Drawing2D/paperXY/UV are not projectXYZ. Facade fill contours, full line/text and per-contour model ownership remain unexposed/NOT_VERIFIED.; Three new saved views frame plan/Section/Elevation at1:100; one native A2 Layout/master with3printed native Drawings. Preliminary oversized new Drawing parked offsheet and retained. GUID domains distinguished. Provider source-link GUID differs from requested ViewMapGUID: metadata identity NOT_VERIFIED. Controlled newplan view scale100->125->100 produces native Drawing0.01->0.008->0.01, while clipping frame remains fixed; behavior independently proved.; Existing native Layout Publisher selected new sheet and generated oneA2PDFpage. File hash/pages/titles/scale/render verified afterSave/Open. Publisher2views produced65pages despite2selected items and is not accepted as a subset. New empty local output directories; native empty-success reply is insufficient without file proof. No global Publisher preferences/APX changes. Local native PDF and processed public PNG retained; raw paths/PLN/full dumps excluded.; Save/Open and independent final readback: original121GUID/BREP/material/story signatures unchanged, including original109; all126current main identities persist. Added Elevation+4native Objects. Native dimension/Layout/Drawings/ViewMap/database IDs separately verified. Physical primary modelVersion unchanged; no new physical BIM construction or testWall change. Historical PR70 edit-synchronization proof retained, not claimed as a fresh BIM-edit test.; Layout ShowAllIn3D error-2130313109 uses the same writer for a view-only floor0 activation, exact identity/saved-byte checks and subsequent complete native-signature proof. Historical UNKNOWN_OUTCOME events kept and independently reconciled, no blind Create/Modify retry. AfterOpen Drawing fill caches initially absent; known-success update onlynewDrawings restored32/34contours.; 13native Schedule definitions discovered; native rowread/configure contracts unsupported. Existing six-type CSV specification adapter retained without duplication. Main APA orchestrator actually queried existing read-only Knowledge Graph with GitHub-current revision129 beforeclaim130. KG/search implementation and normative-system code/branches/policies unchanged.; A11.S03 remainsPARTIAL; A07.S01 not closed and dependencies preserved; S10BLOCKED unchanged. No normative/engineering drawing acceptance. Next: supported native schedule row/configuration contract and complete vertical primitive/owner mapping; require actual rendered projection extent for all future facade placement acceptance.; User changed priority to MODEL_FIRST2026-10-13. Cancelled multi-sheet follow-on performed fresh126GUID/journal/identity read-only preflight and main APA Knowledge Graph query132, zero new native writes/artifacts. PR73 retained. New audited A11.S03 acceptance package creates/edits/verifies a complete separate native two-story building through existing generator/SceneWriter. Historical DONE_PUBLISHED criteria retained; no full-building DONE claim.; Model-first scope audit preserves historical DONE_PUBLISHED and cancelled documentation checkpoint. Draft PR74 head5a3a9201a715a5528c93bed4a5318e2acb32eea7 exact parentPR73 93557ed0cd59c471b0f903a03708ed88c8feb31b;10code blobs matchGitHub.15newtests;638/638APA Windows host/Windows/LinuxCI38394734173PASS;102upstream tests and actual core/MCP smoke each. Canonical native evidence/report/receipt and complete committed privacy scan verified.; Existing authored intent/BIMGraph/CSE/material pack/SceneWriter now creates one native21-element two-story test model:10Walls,2Slabs,6Windows,2Doors,1SinglePlaneRoof. NoMorph/newgenerator/secondexecutor. Actual storybindings0/3m; outerWall-face Slab footprint,0.2mSlab and lowerWall2.8m; upper editable uncutWall4m; testRoof slope0.05rad/thickness0.2m. Dimensions/materials/structural roles are explicit TEST inputs, not engineering design.; Actual native lowerRoof face/memo offset measured and corrected through an owned native translation. Five upperWalls receive SubtractionUpwardsSEO with actual sloped sharedface areas and native zero-volume collision proof. One connected component21using physicalBREPcontact/nativehost edges. Native Category_StructuralFunction actual editable enum resolved:8exteriorWalls bearing,2partitions nonbearing. Native readback afterSave/Open PASS; no structural-capacity inference.; SourceRoof level6.0->6.2m editsoneownedRoof withoutCreate; existingSEO makes all5upper resultantWall caps rise0.2m while memo.height4m remains. HostedWindow width1.2->1.4m preservesGUID/host and changes actualhostWallBREP. Existing snapshot/modelVersion delta6then2changednativefacts,0added/removedGUIDs. Exact sourceDiff scopes use sameSceneWriter/journal with retained126signature gates before each native write.; Two distinct clear-zone21-element scenarios verified. Public orchestrator createdall21successfully then failedread-onlyGetSolidElementLinks allowance. Fixedrouter and independently reconciledcomplete existingGUIDset with publicfinish_created_model, neverrepeatedCreate. Partial/unexpectedSEO sets remainmanualreconciliation, complete links and source areas persisted. Final completionreuse0Creates/0SEO/0propertywrites and168signaturesunchanged.; Final model168mainGUIDs saved/reopened with independent all168body/material/story signatures. Original126includes accepted121/109 preserved, editedprototype147 preserved. Primarysecondbuilding21oneconnectedcomponent and nointernal/new-to-retained nativevolume collisions. Additional firstprototype21vsoriginal126 nativecollision query zero. Historical diagnosticMorph/roof collision retained. NativeUI inspection notperformed; availablebody/regeneratedview/filter scope explicit.; Nativeaxes blocked:installedCreateObjects lacksSDKGridElement variationcontract; genericStructuralGridObject notacceptednativeGridtool. Globalstoryediting requires separatelyauthorizedstory-isolatedproject toprotectoriginalgeometry. SinglePlaneRoof contour/slope edits unqualified. NewhostedDoor/Windowvoidsverified; noGenericOpening/Staircreated; sourceStairrequirement remainsNOT_VERIFIED. RequestedSEOskipPolygonHolestrue readsfalse; holes rejected andflagNOT_VERIFIED. BodylessExternal semanticsNOT_VERIFIED. These are model-first acceptance gaps, not changes to historicalDONE criteria.; Existing plans/Sections/Elevations/PDF/CSV and PR73 code preserved; cancelledmultisheet expansion notcontinued. Normative/search/KnowledgeGraphimplementation/APX/main/master unchanged. Actual mainorchestrator read-onlyKnowledgeGraphquery atGitHubcurrentplan133. A11.S03PARTIAL/A07dependencies/S10BLOCKED preserved. Next:supportednativeaxescontract and separatelyauthorizedstory-isolatedcreate/editcycle, then broaderqualifiedhost/Roofedits and sourceStair.; Native spatial continuation published in draft PR75 head 8ee3fcd89efa5220dc4d1ceb4fb92a26e0d8c07f on exact PR74 base 5a3a9201a715a5528c93bed4a5318e2acb32eea7. 30 new tests; 668/668 APA Windows host and Windows/Linux CI 38416422147 PASS, 102 upstream tests and actual core/MCP smoke each. All 17 code blobs and processed canonical evidence/report/receipt match GitHub. Initial Linux synthetic target-path test corrected; no native replay.; Fresh separately authorized story-isolated project initially contains 20 native template marker/Elevation references and zero available physical bodies. Same-template shared GUIDs were initially misclassified as copied model; interpretation corrected by native body/library readback. All 20 references preserved. Previous 168 accepted model signatures and saved bytes independently unchanged.; Native SetStories inserts actual datum story ID4 while preserving floor IDs1/2/3. Existing generator creates 21 native elements in isolated project. Real global height change 3.0 -> 3.3m produces native levels 0/3.3/6.3/9.3m: two occupied floors plus two datum stories. Upper Walls/Slab/Roof move through global stories, not Z-only MoveElements. Five lower Walls change 2.8 -> 3.1m under 0.2mSlab. Four upper Window sills left at0.7m are restored to authored1.0m by exact ModifyWindows, preservingGUID/host. ZeroCreate/MoveElements during height edit; five actual sloped Roof contacts and nativeSEO remain.; One true native concrete Stair from installed source Favorite connects floors0/3.3m. Source width1m/20risers/preferred going0.35m and derived test riser0.165m are explicit test data. Actual native20Risers/20Treads/1Structure plus60auxiliary Objects. One nativeSlab hole derives actual1x6.4mBREP footprint. Slab outer ring/GUID/material/floor/thickness preserved by semantic native-ring comparison. Real upperSlab contact0.3342017047m2, zero upperSlab nativevolume collision; intentional lower foot0.1membed recorded separately from engineering capacity.; Native Stair solver changes requested going0.35 -> 0.32m. Official precise property readback gives going0.32/riser0.165/width1/line length6.4; rounded localized strings are not numeric acceptance. Source-going NOT_VERIFIED, installed contract lacks going-lock and nativeStair baseline/parameter Modify. Favorite export-7003 wrote mainXML scalar data but completeFavorite/GDL bundle remainsNOT_VERIFIED. Ten auxiliary Object owner GUIDs outside availabledump remainNOT_VERIFIED.; Final new saved revision Save/Open both return nativePASS under120sload timeout. All143identities/signatures persist:20template+21building+102Stair-related IDs (1root/41parts/60auxiliaryObjects). Twenty-two primary elements form one actual physical component by existing BREP/host/NetworkX logic; no other architectural volume collisions. Original168saved/live unchanged. ExistingStairpacket replay fails on baseline before anywrite. NoMorph/secondexecutor/nativepreferences change.; TrueGrid runtime BLOCKED: installedCreateObjects has no Grid tool variation contract. Source-only GetNativeGridDefaultsV1 uses SDK29API_ObjectID+APIVarId_GridElement actual defaults and parameter names, compiles C++20, registers through existing overlay. NoAPXinstalled/noaxescreated/fullAPXlinking notclaimed; unrelated documentation extended-pen compile gap left untouched. Minimum runtime: nativeGrid variation/defaultparameterread/create/readback/stableGUIDedit. Semantic BIMGraphaxes retained.; Historical UNKNOWN ledger rows preserved. Local Wall router refusal proved zero native dispatch before distinct reconciled scoped corrections. First41Open30s timeout independently reconciled without blind retry. One successful nativeSlab-hole write had literal-contour callback failure; actual rotated/closed/quantized contour, BREP and contacts independently proved without ModifySlabs repetition. Final143Save/Open has native repliesPASS. Private UTF8 story-label recovery recorded explicitly.; Canonical single task A11.S03 staysPARTIAL; historicalDONE/A07dependencies/S10BLOCKED preserved. Existing documentation/normative/KG/search/main/master/APX unchanged. Mainorchestrator read-only KnowledgeGraph used GitHub-current134 before CASclaim135; publication rechecks owncurrentclaim. Next: qualify trueGrid runtime and strictStairgoing edit using existingSDK overlay; installing changedAPX requires separate permission. Preserve original168and accepted143 and never replay creation.; Grid/exactStair package in draft PR76 head bc8f8575ed65e308e10c5ac5f573b7d8ad9466a6 on exactPR75 8ee3fcd89efa5220dc4d1ceb4fb92a26e0d8c07f. 21newtests;689/689APA Windows host and Windows/LinuxCI 38448023873 PASS,102upstream tests/core-MCPsmoke each. All15code blobs and canonical processed report/receipt verified. BUILD/OFFLINE/SOURCE proof is explicitly notLIVE or newSOURCE_DIMENSION_PASS.; Full WindowsReleaseSDK29/C++20 APX compiles/links with /WX. NativeGrid4contracts: trueAPI_ObjectID+APIVarId_GridElement defaults/read/create/edit, genericvariation rejection, actualsourceparameter names/types/descriptions, expectedposition editguard and retainedGUID. Existing semantic axes bind to verifiedactualnative library role mapping; missing mapping and renderedspan remainNOT_VERIFIED pendinglive. Mainorchestrator delegates to existingSceneWriter; completedSQLite creates reuseGUID, UNKNOWN neverretries. Coordinate edits return updatedsemanticaxis/nativebinding; no secondexecutor or genericObject/Morph substitute.; Actual FavoriteXML hash ae2ac9b234889b75835062356cd293ea9881d7a839e68d68dca5106de5a3296f has active2R+G0.60..0.65m,going0.25..0.35m,riser0.15..0.20m. Rise3.3/20 givesR0.165; requestedG0.35 ->0.68 conflicts0.65. NativeG0.32 reaches0.65 and matchesPR75independentprecise readback. Source-compatible testcases3.0/20/G0.35 and3.3/22/G0.35;23risers violatesminR. These are Favoriteconstraints, notSP/GOSTacceptance or nativecreatedsamples. Requestedbaseline6.65/nativewalkingline6.4 remainseparatefacts; completebaseline-solvingcausality pendingdetachedSDKprobe.; NativeStair4contracts: exacttype/count/locks/rules/baseline/walkingline read; detachedSDKsolving withoutmodel/defaultwrites; lockedsource creation through existingproviderFavorite handling; oneownedroot edit with expectedheight/going/count. SourceXMLhash/active-rules gate denies incompatible case beforeCreate. SDKsolver changedsource dimensions/baseline deniescreation; exactnativeNumeric/rule readback remains mandatory. Accepted0.32Stair untouched; hierarchicaledit onlynewtestsample becausechildGUIDchanges possible. MainFavorite export stayspartial, nofullGDLbundleacceptance.; Read-only94file runtime-source snapshot preserves originaldirty Tapir checkout. Candidate source registry includes all263old documentednames and predicts274names:8newGrid/Stair and3prior document endpoints registered by repairedoverlay. Source registry is not runtimeacceptance. ExistingLine extendedpenSDK29compilecast fixed usingeffectiveindex; originalTextshort unchanged. NoSheet/layout,normative,KG,search ormain/master edits. InstalledAPXhash dc99af071d3dbcff9626653ccc37001613cb3fa4a8eff50c6000c1cc70e8d7c7 unchanged; accepted143/168savedfilebytesmatch. Zero native writes thispackage, no newSave/Open/livePASS.; READY candidateAPX SHA256 8ad672092aa93e4bf1b4d469cbf7840cb60acd538820183bb68d5d6786ea221d; package APA_Grid_Stair_SDK29_Candidate_20261013.zip SHA256 07715253d6a3a73ec6b61a408a0200c70b5c2048f49a8fa1cce33546525dee94. Binaries,fullprivatepaths,PLN andrawtechnicaldumps notcommitted. Separate deployment permission remainsDEP-APA-GRID-STAIR-APX-LOAD. Preparedisolatedcopy basenameAPA_Grid_Stair_Exact_Test_01.pln: freshidentity/port/hash/journal, installedschema and actualGridlibraryroles, detachedStaircases beforeonecompatible exactnewStair; nativeaxiscreate/edit/reuse, independentreadbackandSave/Open,retain143/168andacceptedStair. BuildcannotstandinforLive.; A11.S03 remainsPARTIAL and claimreleased afterpublished checkpoint. All91S-ID/history/A07dependencies/S10BLOCKED preserved. Mainorchestrator used read-onlyKGcurrent137 beforeCAS138. Next exactgate: userpermissiontocandidateAPXloadandisolatednativeprobe. NativeGridrenderedspan and0.35Stairsource-dimensioncriteria stillNOT_VERIFIED; ENGINEERING_NOT_VERIFIED. Roofcontour/slope development follows actualGrid/Staircriteria.; PR77 c1b4e1a565bcd903273933d8917608df156ac600 preserves exactPR76 parent bc8f8575ed65e308e10c5ac5f573b7d8ad9466a6. Eight new exactStair SQLite completion/drift tests;697/697APA host and Windows/LinuxCI 38459091689 PASS,102upstream graph tests/core-MCPsmoke each. Four committed code blobs and canonical report/receipt independently verified. Native Grid/Stair acceptance remains NOT_VERIFIED; no new samples created.; Existing authorized APA_Stories_Grid_Stair_Test_01.pln is the sole current target. Previous proposed new APA_Grid_Stair_Exact_Test_01.pln superseded by direct user instruction; no newPLN/building created. All143accepted GUID/geometry/material/story signatures and native story structure unchanged after two UI module-switch Save/Open cycles. Separate original168saved bytes match. Saved143filehash changed after Save and is recorded separately from unchanged signatures; local current-state hash updated with recovery provenance, historical snapshots/journal preserved.; User explicitly authorized temporary test-instance Tapir switching without installedfile overwrite. Candidate exactPR76APX SHA2568ad672092aa93e4bf1b4d469cbf7840cb60acd538820183bb68d5d6786ea221d verified. Manager displayed original installedpath for bothTapir entries after externalcandidate selection; automatic approval review rejected applying ambiguous configuration as potentially loading wrongmodule. Candidate notloaded; originalmodule restored and actualprocessmodules/schema read back. InstalledAPX bytes unchanged, otherinstances not reconfigured; verifiedlocalbackup retained. This is a pathidentity blocker, not missing general user authorization.; Freshactualschema retains263oldcommands; all8newGrid/Stair endpoints absent. NativeGrid defaults/actualrole mapping/renderedspan and detached3.3m/22R/0.15m/0.35m Stairsolver/newsource dimension remainNOT_VERIFIED. No Create/Modify/newnativeStair or acceptedStair edit. UIdeploymentSave/Open was separatelyrecorded and not mislabeled asSceneWriteroperation; existing modelledger unchangedPASS52/UNKNOWN3, no blindretry.; ExactStair completedPASS now reuses sameSceneWriterSQLite rootGUID with0Create, after sourceXML/rules/hash, targetbinding, currentsavedhash, retainedgeometry, exactnativefield/rule checks. Unknown/unverifiedhistory or changedsource cannotreplay; explicitownededit/reconciliation required. WorkingOFFLINE skeleton extends existingmainorchestrator, no secondexecutor. LiveREPEATABILITY and GridLIVE/StairSOURCE_DIMENSION remainNOT_VERIFIED, ENGINEERING_NOT_VERIFIED.; Publishedcheckpoint APA-RUN-20261013-200350Z-grid-stair-live-checkpoint with correctedgapregister/roadmap and exactGitHubreadback. A11.S03PARTIAL; A07deps, S10BLOCKED,91S-ID/history preserved. Nextgate: unambiguously load external exactcandidate in sameapprovedinstance, independentlyverify actualmodulepath/hash andfresh8commands, qualifyGRELdefaults and detachedStairsolve before newone-samplewrites, nativegeometry/renderedspan/edit/reuse andSceneWriterSave/Open. Userassistance may be necessary for ambiguousmanager selection; no installedAPXoverwrite or otherinstancechanges withoutspecificpermission. Roofcontour/slope follows actualGrid/Staircriteria.; Direct user priority override REAL_PROJECT_FIRST_20261014 recorded while APX restoration was completed; existing TRC has 1033 native 2D elements on three actual stories and zero available resultant 3D bodies. Two authored upper-floor contours with atrium holes selected for a bounded native Slab plan; no production write approval inferred from generic continue. Native execution awaits explicit scoped authorization; A11.S03 remains incomplete.; Direct user correction UNIVERSAL_NATIVE_FIRST_20261014 supersedes the previous practical TRC target. TRC read-only checkpoint is preserved separately; zero native Create/Modify/Save/Open there, proposed floorplates cancelled before authorization. Installed original APX SHA verified restored and legacy registration restored. User confirmed all Archicad closed; previously authorized external test-instance switching resumes without installed APX replacement. Historical completed tasks remain unchanged.; PR79 60a78e0cd55fc4951c1de3c8d060adf4f9538134 exact PR77 parent c1b4e1a565bcd903273933d8917608df156ac600. True native GREL Grid1created, independently read and edited same GUID; zeroCreate reuse before and after SceneWriter Save/Open. All143 original GUID/geometry/material/story signatures unchanged, saved144. GridCRUD/persistence LIVE_PASS; rendered complete wire-span NOT_VERIFIED, not inferred from marker BREP. No building recreated/newPLN/Morph/acceptedStair edit.; Native Grid parameter script uses degrees input while SDK memo uses radians; Object.angle and AC_Angle are distinct.90degrees readback1.570796327radians. Earlier wrong-unit edit remains UNKNOWN_OUTCOME, reconciled by actual read then separate corrective intent. UI-observed owned-axis placement drift corrected after143preservation proof; causeNOT_VERIFIED. JournalPASS59/UNKNOWN4 preserved; no blind repeats/deletions. Existing BIMGraph/SceneWriter and source bindings retained.; Candidate actual moduleSHA8ad672092aa93e4bf1b4d469cbf7840cb60acd538820183bb68d5d6786ea221d and fresh274schema/263oldcommands/new8 verified. Explicitly authorized temporary installed replacement unblocked loading. OriginalAPX SHA dc99af071d3dbcff9626653ccc37001613cb3fa4a8eff50c6000c1cc70e8d7c7 and originalsingle registryvalue restored byte-exact. Post-restoration test-project opening/readback is PENDING_USER_OPEN. New commands are not claimed permanently installed.; Detached Stair3.3m/22risers/0.15m/0.35m source-compatible probe reset connection and Archicad process disappeared. Exactly1Evaluate,0CreateExact/ModifyStair; saved144 bytes unchanged. FailurecauseNOT_VERIFIED. Native baseline local vs request world; qualified frame absent. NewexactStair writes require pinned detached PASS bound to source/target/savedmodel/retainedgeometry/schema; missing/failed/stale proof and knownterminatingcandidate denied. CompletedverifiedSQLite reuse avoids solver/Create. SOURCE_DIMENSION and ENGINEERING_NOT_VERIFIED.; 707/707host and Windows-onlyCI 38485644027 PASS,10newtests,102upstream/coreMCP PASS. HistoricalLinux results preserved. Mainorchestrator KG read current145 before completion146; implementation unchanged. Report/evidence14files/receipt APA-RUN-20261013-234433Z-true-grid-live-stair-runtime GitHubbyte-readback verified. A11.S03PARTIAL, A07 dependencies/S10BLOCKED and other90tasks preserved. TRC excluded; normative/search/documentation implementation untouched. Next: correctedSDK detached memo/base-plane candidate, build then separateauthorization and detachedqualification beforewrite; Roofcontour/slope independent native contracts follow.; Resume same-owner native runtime/source-contour work after resource interruption. No competing claim overwritten; temporary review-limit denial executed no test action. Original APX and saved144 preserved; supplemental post-restoration144native readback completed with0modelwrites. Newcontour/stair candidate writes still require specific separate approval.; PR80 cb73cd578c7cd7577f80397920d9e81b8d09c6e1 begins at exactPR79 60a78e0cd55fc4951c1de3c8d060adf4f9538134 and preserves stacked ancestry. Existing compiler now accepts authored nonrectangular floor contours/trueholes by story and emits native Slab graphs; targeted contour/hole delta emits1ModifySlabs,0Creates, preserves GUID. SameSceneWriter/SQLite; no newgenerator/controller/renderer.; ARCHICAD_LIVE_PASS:1L-shaped nativeSlab10x8m/2x2mvoid/0.2m created, then outer11x8m/void3x2m edited sameGUID. Actual native memo and closed BREP top/hole contours prove60to62m2, exact current acceptedSlab material.3modelcalls=1CreateSlabs+2ModifySlabs,0extraCreate in delta; native collisionsnone. Testparameters only, engineeringNOT_VERIFIED. Save/Open and separate145readbackPASS; all144previous signatures includingoriginal143 unchanged, separate168/Trc untouched. Current savedSHA256 bfbae730dc65a8cd68dad707685406649f6a3e5ea79f4d63140241043b02f689.; OriginalAPX module/path/SHA dc99af071d3dbcff9626653ccc37001613cb3fa4a8eff50c6000c1cc70e8d7c7 and263freshcommands verified; prior pendingpostrestore144readback completed. Actual Archicad29build5101. NewSDK candidate f6f0861ffb76aced7de89922bdfa5f271d9aa371795c3849cbfe6e585003187f source/build identity 0b929f11a7e892b5cab062a9a6dc7bdc77363cec3a59109245f95e18de770eef compiledWindowsRelease and embedded revision cb73cd578c7cd7577f80397920d9e81b8d09c6e1 checked; notinstalled. Staleincrementalbinary detected/rejected and cleanrebuilt; builder refuses mismatched outputreceipt. SharedTapirversion alone cannotqualifySDKdispatch.; Stair preparation remainsBLOCKED: stockcreate setter removesbaseline edge/vertexdata, leavesoldwalkingmemo beforeSolveStair. RootfaultcauseNOT_VERIFIED. Detacheddiagnostic candidate nowreads source/frame/buffers withoutsetter orsolver; exactwrite requires qualifieddetachedPASS andcompletebuffers. Oldterminatingrequest neverrepeated. Local/world baselineframe exposedsource/buildonly. DifferentAPXdeployment requires separateauthorization.; Livepreflight fixedforbodyless hiddenRiser/Tread sentinelbounds through slotcompleteNativeDump/actualStairowner/specializedmembership; parentgeometry stillchecked, no2Dsemanticguess. Nativecreate1.002s/edit1.446s/Save3.251s/Open11.458s includingreadback; sourcecompile0.489s separatePythonmeasurement. No largemodel/scalability/optimizationclaim.; 718/718WindowsAPA host/CI 38527855349 PASS,11newregressions,102upstream/coreMCP. Mainorchestrator unchangedKG fresh148 beforecompletion149. Code13blobs, canonicalreport/evidence14files/receipt APA-RUN-20261014-074612Z-universal-native-floor-contours GitHubbyte-readbackverified. A11.S03PARTIAL; other90tasks, historicalDONE, A07deps andS10BLOCKED preserved.; Directuserapproval: allnativeoperations in existingtestPLN areauthorized, with retained145protection/identity/journal/readback; no newPLN required. APXreplacement remains separatepermission. Nextqualify newruntimeidentity/safe read-onlyStairdiagnostic under separatelyauthorizedtemporarycandidate; SinglePlaneRoof contour/slope is nextindependent SDK/nativecontract. Normative/search/documentation/Trc/main untouched.; Runtime continuation afterPR80: directuser authorized f6f0861ffb76aced7de89922bdfa5f271d9aa371795c3849cbfe6e585003187f temporaryAPX, safe identity/Stair read-only diagnosis and agentfileopen/close. Retained145 independently rechecked before UIclose; test saved/closed, current SHA256 f25438ef700ef590a4f85634c14bc95384df866b039783b31e77479648cfe8c0 and backupverified. Windows RunAs cancelled before replacementhelper executed; installedoriginal dc99af071d3dbcff9626653ccc37001613cb3fa4a8eff50c6000c1cc70e8d7c7 unchanged, registry unchanged,0modelgeometrywrites. Candidate LIVE NOT_VERIFIED; exactStair remainsBLOCKED. Windowsconfirmationretry pendinguser; no repeatedwrite and no repeated terminating solver. Supplemental readback afterUI Save requiresreopening. Published Slab LIVE/718Windows result remainsvalid in its original scope.

## APA-P70.A11.S04

**Измерить и ускорить объединённый контур** — INTEGRATION / READY / P1

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: combined-system-measured-optimization-v31
- Depends on: APA-P70.A11.S03
- Related, check before duplicating: none
- Acceptance: Same scenario before/after timings/API counts with native semantics retained; optional optimizer verified within deterministic bounds.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: none
- Expected output: Same scenario before/after timings/API counts with native semantics retained; optional optimizer verified within deterministic bounds.

## APA-P70.A11.S05

**Собрать установщик стабилизированного APA** — INTEGRATION / READY / P1

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: integrated-apa-installer-ac29-v31
- Depends on: APA-P70.A11.S04, APA-P70.A08.S02
- Related, check before duplicating: none
- Acceptance: Version-aware installer/diagnostics/uninstall tested on actual supported AC29 builds; installation/APX changes require separate authorization. AC30 separate.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: none
- Expected output: Version-aware installer/diagnostics/uninstall tested on actual supported AC29 builds; installation/APX changes require separate authorization. AC30 separate.

## APA-P70.A11.S06

**Получить подтверждённые размеры и источник сборки производителя** — INTEGRATION / BLOCKED / P2

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: manufacturer-dimensions-source-v31
- Depends on: APA-P70.A11.S02
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Qualified source/page/fact dimensions and product-to-native-material mapping; exact assembly waits for source compile gates.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: none
- Expected output: Qualified source/page/fact dimensions and product-to-native-material mapping; exact assembly waits for source compile gates.; REAL_NATIVE_C4_C5_BEAM_SUPPORT_PASS; full manufacturer assembly still requires eight dimensions/source commit/grade/fixings/rafter bearing.

## APA-P70.A11.S07

**Подтвердить доступный нативный контракт Shell и редактирования Opening** — INTEGRATION / BLOCKED / P2

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: shell-opening-edit-provider-v31
- Depends on: APA-P70.A11.S02
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Use an existing ready native path with GUID/story/material/body readback. Any installed APX change requires separate user authorization.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: none
- Expected output: Use an existing ready native path with GUID/story/material/body readback. Any installed APX change requires separate user authorization.; Native Wall/Roof Trim perimeter contact verified. Reverse Trim metadata provider error and ineffective underside SEO goal remain explicit; Shell/Opening-edit contract blocker unchanged.; Native Wall/Roof actual underside contact and SEOrelation are now LIVE_PASS in a separate specimen. Flag readback difference remains explicit; missing Shell/Opening-edit runtime contracts still BLOCKED.

## APA-P70.A11.S08

**Подключить фактический SAM/SAF обмен и входы расчётного движка** — INTEGRATION / BLOCKED / P2

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: sam-saf-qualified-exchange-v31
- Depends on: APA-P70.A11.S02
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Actual SAM/SAF artifact/provider and receiver mapping; approved inputs and available solver/results with provenance. No architectural-body-to-SAM inference.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: none
- Expected output: Actual SAM/SAF artifact/provider and receiver mapping; approved inputs and available solver/results with provenance. No architectural-body-to-SAM inference.; Native Beam structural identity and IFC quantities do not establish SAM/SAF or loads/norms/solver results; existing analytical gate retained.

## APA-P70.A11.S09

**Подтвердить семантический обмен с MCP/Twinmotion** — INTEGRATION / BLOCKED / P2

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: mcp-twinmotion-semantic-receiver-v31
- Depends on: APA-P70.A11.S02
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Use an existing actual receiver implementation and independently validate supported semantics, distinguished from IFC geometry coordination.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: none
- Expected output: Use an existing actual receiver implementation and independently validate supported semantics, distinguished from IFC geometry coordination.; Actual IFC43mappings/50elements/18quantity matches/0mismatch/24material assignments/12port relations/6opening hosts verified. Structural contact/Trim/SEO export semantics and receiver compatibility remain unverified.; Actual IFC45mappings/52elements/26materials/20quantity matches/0mismatch; native new Wall/Roof bodies/materials agree. SEO/contact relationship export semantics and actual receiver compatibility remain unverified.

## APA-P70.A11.S10

**Подтвердить нативный круглый порт терминала, предпочтения диаметра и переход MEP** — INTEGRATION / BLOCKED / P2

- Parent: APA-P70 → APA-P70.A11
- Topic: PRODUCT_DEVELOPMENT
- Work key: mep-terminal-diameter-transition-provider-v32
- Depends on: APA-P70.A11.S02
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Actual terminal port and route sections agree through a verified native transition and reciprocal physical connections; preserve original baseline and persist readback.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-P70-A11-S03-PR56-20261012](https://github.com/dvikt33-ux/safe-bim-layer/pull/56), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-P70-A11-S10-REFERENCE200-20261012](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-132353Z-construction-junction-qualification-s03/mep-preferences.json)
- Existing V2 runs: none
- Expected output: Reuse a ready exposed provider path; connect actual terminal port to routed network with native diameter/transition readback, original baseline preservation and save/reopen. No installed APX change without separate authorization.; LIVE_PASS unique live reference200/diameter0.2m row binding and one new circular route; original terminal now connected automatically with reciprocal actual0.2mports and saved/reopened independently. No preference/APX modification or Create/Connect replay.; The connected terminal/circular pair has one reciprocal edge and one open downstream port; full8route network still has2components. Existing rectangular network preserved. Native mixed-section transition and baseline-preserving main bridge not verified.; Read-only existing source/SDK/schema/native-port scope reconfirmed; minimally expose and qualify the existing route-local per-segment SDK maps on a new specimen before claiming a native transition. Retained-GUID-safe main connectivity is a separate contract/acceptance. No transition write was attempted.
