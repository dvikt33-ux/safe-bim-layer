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

**Связать проектные требования с версиями нормативов и проверяемыми правилами** — BUILD / READY / P3

- Parent: APA-P70 → APA-P70.A02
- Topic: PRODUCT_DEVELOPMENT
- Work key: normative-applicability-pack
- Depends on: APA-P70.A02.S01, APA-P70.A08.S04
- Related, check before duplicating: none
- Acceptance: Rule pack с юрисдикцией/редакцией СП/ГОСТ, применимостью, требованиями, источниками и явными NOT_VERIFIED
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Rule pack с юрисдикцией/редакцией СП/ГОСТ, применимостью, требованиями, источниками и явными NOT_VERIFIED

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

**Вывести из модели обязательные семейства узлов и их условия применимости** — INTEGRATION / IN_PROGRESS / P4

- Parent: APA-P70 → APA-P70.A04
- Topic: PRODUCT_DEVELOPMENT
- Work key: required-junction-condition-coverage
- Depends on: APA-P70.A03.S01, APA-P70.A02.S04
- Related, check before duplicating: APA-P70.A11.S03
- Acceptance: Матрица всех применимых примыканий/отверстий/армопоясов/связей/крепежа с точным source/detail ID и открытыми пробелами
- Owner/lease: work-construction-junctions-20261012 / 2026-10-12T16:08:54Z
- Requires owner approval: False
- Source inputs: [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-P70-A11-S03-NATIVE95-V32-20261012](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-110611Z-connected-native-continuation-v32/REPORT.md)
- Existing V2 runs: [APA-RUN-20261012-122511Z-construction-junctions-s01](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-122511Z-construction-junctions-s01/REPORT.md) (receipt verified), [APA-RUN-20261012-123259Z-construction-junctions-s01-openings](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-123259Z-construction-junctions-s01-openings/REPORT.md) (receipt verified)
- Expected output: Матрица всех применимых примыканий/отверстий/армопоясов/связей/крепежа с точным source/detail ID и открытыми пробелами

## APA-P70.A04.S02

**Привязать выбранные узлы и композиции к нативным BIM элементам** — BUILD / READY / P4

- Parent: APA-P70 → APA-P70.A04
- Topic: PRODUCT_DEVELOPMENT
- Work key: native-details-to-cse-binding
- Depends on: APA-P70.A04.S01, APA-P70.A03.S02
- Related, check before duplicating: none
- Acceptance: Редактируемые системы и узлы с параметрами, классификацией, происхождением и invalidation при изменении
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md)
- Existing V2 runs: none
- Expected output: Редактируемые системы и узлы с параметрами, классификацией, происхождением и invalidation при изменении

## APA-P70.A04.S03

**Проверить узлы окон, облицовки, перекрытий и кровельных примыканий** — VALIDATION / READY / P4

- Parent: APA-P70 → APA-P70.A04
- Topic: PRODUCT_DEVELOPMENT
- Work key: junction-evidence-acceptance
- Depends on: APA-P70.A04.S02
- Related, check before duplicating: none
- Acceptance: Для каждого узла классификация PASS_GEOMETRY/PASS_DOCUMENTED/PASS_ENGINEERING/NOT_VERIFIED; ложные approvals запрещены
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12)
- Existing V2 runs: none
- Expected output: Для каждого узла классификация PASS_GEOMETRY/PASS_DOCUMENTED/PASS_ENGINEERING/NOT_VERIFIED; ложные approvals запрещены

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
- Related, check before duplicating: APA-P70.A11.S06, APA-P70.A11.S07, APA-P70.A11.S08, APA-P70.A11.S09, APA-P70.A11.S10, APA-P70.A04.S01
- Acceptance: Observed gaps reconciled against donors/archives and fixed with real behavior and regression proof; no duplicated subsystem without reason.
- Owner/lease: unclaimed
- Requires owner approval: False
- Source inputs: [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-P70-A08-S04-EDITABLE-NATIVE-CORE-ACCEPTED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-200500Z-editable-core-acceptance/REPORT.md), [ART-P70-A02-S01-SEMANTIC-GETSTORIES-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-161511Z-p70-semantic-brief-getstories/REPORT.md), [ART-P70-A03-S01-AUTHORED-SPATIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-164748Z-p70-a03-s01-spatial-loadpaths/REPORT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-P70-A02-S04-NATIVE-MATERIAL-LIBRARY-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-211000Z-native-material-library-integration/REPORT.md), [ART-P70-A03-S02-PR47-SPATIAL-CLEARANCE-275-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-spatial-clearance-20-owner-boxes-pr47-275-offline-20261011.md), [ART-P70-A03-S02-PR46-SCENEWRITER-READONLY-PREFLIGHT-271-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr46-original-scene-writer-preflight-contract-271-pass-20261011.md), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-ATTR-STORY-SLAB-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md), [ART-SDK-GET3D](../../../../../docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md), [ART-P70-A09-S01-NATIVE-GEOMETRY-INTEGRATED-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-202800Z-native-geometry-integration/REPORT.md), [ART-SDK-OPENING-SHELL-20261010-8E41](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md), [ART-PR20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md), [ART-APA-SOURCE-71-INDEX-20261011](https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json)
- Existing V2 runs: [APA-RUN-20261012-012500Z-gap-windows-sqlite-v31](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-012500Z-gap-windows-sqlite-v31/REPORT.md) (receipt verified), [APA-RUN-20261012-075300Z-functional-gaps-v31](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-075300Z-functional-gaps-v31/REPORT.md) (receipt verified), [APA-RUN-20261012-095401Z-functional-expansion-v32](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-095401Z-functional-expansion-v32/REPORT.md) (receipt verified), [APA-RUN-20261012-110611Z-connected-native-continuation-v32](../../../../../docs/research/apa-results/runs/2026-10-12/APA-RUN-20261012-110611Z-connected-native-continuation-v32/REPORT.md) (receipt verified)
- Expected output: Observed gaps reconciled against donors/archives and fixed with real behavior and regression proof; no duplicated subsystem without reason.; Historical PR55 baseline: Published PR55 head3191e7ce5071e6de7401f6e520fbd8f3ef2a1ea2 stacked on PR54;31new tests,371/371Windows/LinuxPASS.; Historical PR55 baseline: Details73context/source/host/material/fact exchange, reciprocal two-section MEP, Generic Opening/SEO, specialized metadata and IFC host/port observations work together.; Historical PR55 baseline: Saved/reopened isolated PLN:27primary/59totalGUID, all original48GUID/geometry preserved; SHA256da37fa0fe9b1b255f1618a881a79eb9d4ae8b66993a99cb75fdba30cddc69bb4. Engineering/visibleUI NOT_VERIFIED.; Current published draft PR56 head3a743a4f96a98acdcbb837946603f0681d9a1f54:403/403Windows host and Windows/Linux CI PASS; all11GitHub code blobs and all15publication blobs exactly match committed/generated bytes.; LIVE_PASS working routed graph:7routes/9segments/12physical members/11reciprocal edges, one three-port-connected tee and two elbows; exact architectural collisions empty. Native default terminal is separately read back but open/outside routed scope.; LIVE_PASS independent Details c4 timber part:source25x150mm section, actual10mroof span/slope/story/material, model-bound placement and empty exact collision readback; full8-dimension manufacturer assembly and native roof-child relationship not claimed.; Save/reopen95GUID and37context records; all95resultant geometry signatures unchanged, original48/baseline59preserved. PLN SHA256dea93fe0fd520747bf4fee5f12d86372f57d972a7021b65029419d2d127892c8.; Actual IFC37/37world bounds and all11native/IFCowner-pair multiplicities agree;44elements/19materials/39classifications/26ports. Twelve verified quantity comparisons match,0verified mismatch. Engineering/full receiver semantics remain NOT_VERIFIED.; Next independent step:existing A04.S01 applicability/source coverage using the shared model/matrix; S10 separately qualifies actual terminal diameter/transition via an existing ready provider. S06-S09 retain external gates. S04 waits actual S03 completion.

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
- Expected output: Qualified source/page/fact dimensions and product-to-native-material mapping; exact assembly waits for source compile gates.

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
- Expected output: Use an existing ready native path with GUID/story/material/body readback. Any installed APX change requires separate user authorization.

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
- Expected output: Actual SAM/SAF artifact/provider and receiver mapping; approved inputs and available solver/results with provenance. No architectural-body-to-SAM inference.

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
- Expected output: Use an existing actual receiver implementation and independently validate supported semantics, distinguished from IFC geometry coordination.

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
- Source inputs: [ART-P70-A11-S03-PR56-20261012](https://github.com/dvikt33-ux/safe-bim-layer/pull/56), [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-TAPIR-COMPAT-20261010-6F29](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md)
- Existing V2 runs: none
- Expected output: Reuse a ready exposed provider path; connect actual terminal port to routed network with native diameter/transition readback, original baseline preservation and save/reopen. No installed APX change without separate authorization.
