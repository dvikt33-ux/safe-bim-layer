# APA — тематическая карта исследований, разработки и интеграции

Generated from the sole project plan. Each task belongs to exactly one topic.
Related tasks and evidence are preserved; do not repeat a topic review blindly.

| Topic | Research/build tasks | Done | Ready | Existing inputs |
| --- | ---: | ---: | ---: | --- |
| ARCHITECTURE — Варианты архитектуры | 4 | 0 | 0 | ART-REGISTER |
| AUTOMATION — Автономизация и 24h gate | 4 | 0 | 0 | ART-OS-AUDIT, ART-PUBLISHER |
| CONTROLLER — Единый управляющий и межчатовый контекст | 8 | 6 | 2 | ART-CONTROLLER, ART-PLAN, ART-PUB-WORKFLOW, ART-PUBLISHER, ART-PROPOSAL-PROTOCOL |
| GDL_TN — GDL и ТЕХНОНИКОЛЬ | 1 | 0 | 1 | ART-PR20 |
| HUB_GOVERNANCE — Канонический hub и реестр | 8 | 4 | 3 | ART-BRANCH-JSON, ART-BRANCHES, ART-PLAN, ART-PUB-RECEIPT, ART-QUEUE, ART-REGISTER, ART-STATUS |
| IFC_MCP — IFC/openBIM и MCP | 1 | 0 | 1 | ART-REGISTER |
| KNOWLEDGE_GRAPH — Сведение исследований и доказательств | 3 | 0 | 1 | ART-BRANCHES, ART-REGISTER, ART-TRACE-RECEIPT, ART-TRACE-REPORT |
| MEP — MEP native и Tapir | 1 | 0 | 0 | ART-REGISTER |
| MVP — MVP и внедрение | 2 | 0 | 0 | ART-PLAN |
| PUBLISHER — Публикация, квитанции и capability | 4 | 0 | 2 | ART-OS-AUDIT, ART-PUB-RECEIPT, ART-PUBLISHER |
| SDK_NATIVE — Archicad 29 native SDK | 3 | 0 | 3 | ART-REGISTER, ART-SDK-GET3D, ART-SDK-SEO |
| SYNTHESIS — Синтез research → implementation | 2 | 0 | 0 | ART-PLAN, ART-REGISTER |
| TAPIR_PYTHON — Tapir и Python/JSON | 1 | 0 | 1 | ART-REGISTER |
| TESTS — Read-only и разрешённые live-тесты | 6 | 0 | 0 | ART-PLAN, ART-PR20, ART-REGISTER |
| TOOL_INTEGRATION — Каталог и интеграция инструментов | 3 | 0 | 1 | ART-PLAN, ART-REGISTER |

## Tasks by topic

### ARCHITECTURE — Варианты архитектуры

- APA-P10.A03.S01 [INTEGRATION/READY]: Сравнить native C++, Tapir/Python, IFC и hybrid; work_key=architecture-option-matrix; related=APA-P50.A02.S02
- APA-P10.A03.S02 [INTEGRATION/READY]: Сравнить performance, обратимость, тестируемость, стоимость; work_key=architecture-constraints-cost; related=none
- APA-P30.A01.S01 [INTEGRATION/READY]: Decision matrix для нативной BIM-геометрии; work_key=native-bim-shortest-path; related=none
- APA-P30.A01.S02 [INTEGRATION/READY]: Блокировки и альтернативные маршруты; work_key=architecture-blockers-fallbacks; related=none

### AUTOMATION — Автономизация и 24h gate

- APA-P40.A01.S01 [CONTROL/BLOCKED]: Настроить запуск через ChatGPT Scheduled Tasks и разрешённый GitHub доступ; work_key=always-on-executor-auth; related=none
- APA-P40.A01.S02 [BUILD/BLOCKED]: Проверить Scheduled → IN_PROGRESS → результат → DONE_PUBLISHED/PARTIAL; work_key=unattended-research-cycle; related=none
- APA-P40.A01.S03 [BUILD/BLOCKED]: Watchdog пропусков Scheduled Task, зависших IN_PROGRESS и журнал ошибок; work_key=watchdog-and-error-journal; related=none
- APA-P40.A01.S04 [VALIDATION/BLOCKED]: Проверить 24 часа реальных запусков ChatGPT Scheduled Tasks без повторов; work_key=24h-continuity-proof; related=none

### CONTROLLER — Единый управляющий и межчатовый контекст

- APA-P60.A01.S01 [CONTROL/DONE_PUBLISHED]: Зафиксировать единый машинный костяк проекта и ID; work_key=canonical-project-dag; related=none
- APA-P60.A01.S02 [BUILD/DONE_PUBLISHED]: Валидатор DAG, статусов, duplicate work и gates; work_key=controller-dag-validator; related=none
- APA-P60.A01.S03 [BUILD/DONE_PUBLISHED]: Генератор единого control board, next work, context pack; work_key=controller-generated-views; related=none
- APA-P60.A01.S04 [VALIDATION/DONE_PUBLISHED]: End-to-end controller workflow и readback; work_key=controller-github-e2e; related=none
- APA-P60.A02.S01 [CONTROL/DONE_PUBLISHED]: Handoff protocol: каждый чат читает control plan, берёт S-ID; work_key=cross-chat-handoff; related=none
- APA-P60.A02.S02 [INTEGRATION/DONE_PUBLISHED]: Связать publisher inbox с controller plan, запретить orphan runs; work_key=publisher-plan-claim-gate; related=APA-P00.A03.S03
- APA-P60.A02.S03 [VALIDATION/PARTIAL]: Протестировать CAS-claim, lease, duplicate prevention; work_key=claim-concurrency-test; related=APA-P60.A02.S04
- APA-P60.A02.S04 [VALIDATION/PARTIAL]: Ввести сбор предложений задач исследователями и принятие аудитором в PROJECT_PLAN; work_key=research-proposals-audit-approval; related=APA-P60.A02.S03

### GDL_TN — GDL и ТЕХНОНИКОЛЬ

- APA-P10.A02.S02 [RESEARCH/READY]: GDL/TN, Unicode, target identity и 92 ошибок; work_key=gdl-tn-identity-and-92-errors; related=APA-P50.A02.S01

### HUB_GOVERNANCE — Канонический hub и реестр

- APA-P00.A01.S01 [CONTROL/DONE_PUBLISHED]: Найти и прочитать исходный hub; work_key=hub-discovery; related=none
- APA-P00.A01.S02 [CONTROL/DONE_PUBLISHED]: Найти архивные исследования и индекс; work_key=archive-research-inventory; related=none
- APA-P00.A01.S03 [CONSOLIDATION/PARTIAL]: Инвентаризировать 72 ветки и PR, проверить уникальные результаты и ancestry; work_key=branch-ancestry-forensics; related=APA-P50.A01.S01
- APA-P00.A01.S04 [VALIDATION/BLOCKED]: Сопоставить локальные и удалённые SHA без догадок; work_key=local-git-sha-parity; related=none
- APA-P00.A02.S01 [CONTROL/DONE_PUBLISHED]: Установить единственную каноническую исследовательскую ветку; work_key=canonical-branch-policy; related=none
- APA-P00.A02.S02 [CONTROL/DONE_PUBLISHED]: Создать hub, план, реестр, очередь, протоколы; work_key=hub-operating-documents; related=none
- APA-P00.A02.S03 [CONSOLIDATION/READY]: Связать старые находки с S-ID и удалить логические дубли без удаления оригиналов; work_key=legacy-evidence-dedup; related=APA-P50.A01.S02
- APA-P00.A02.S04 [VALIDATION/PARTIAL]: Контролировать receipt/commit/readback всех завершённых отчётов; work_key=publication-completeness-audit; related=none

### IFC_MCP — IFC/openBIM и MCP

- APA-P10.A02.S03 [RESEARCH/READY]: MCP/IFC/openBIM и альтернативы; work_key=ifc-mcp-openbim; related=APA-P50.A02.S01

### KNOWLEDGE_GRAPH — Сведение исследований и доказательств

- APA-P50.A01.S01 [CONSOLIDATION/PARTIAL]: Карта связей: исследования ↔ S-ID ↔ артефакты ↔ PR; work_key=cross-research-traceability; related=APA-P00.A01.S03
- APA-P50.A01.S02 [CONSOLIDATION/READY]: Дедупликация по work_key/source revision/claim; work_key=claim-and-evidence-dedup; related=APA-P00.A02.S03
- APA-P50.A01.S03 [INTEGRATION/READY]: Сводить несколько исследований одной темы в решение; work_key=theme-research-synthesis; related=none

### MEP — MEP native и Tapir

- APA-P10.A02.S04 [RESEARCH/IN_PROGRESS]: Native MEP/Tapir MEP команды, трассы, порты; work_key=native-and-tapir-mep; related=APA-P50.A02.S01

### MVP — MVP и внедрение

- APA-P30.A02.S01 [BUILD/READY]: MVP: этажи → атрибуты → геометрия → библиотека → MEP; work_key=mvp-implementation-milestones; related=APA-P50.A03.S01
- APA-P30.A02.S02 [VALIDATION/READY]: Acceptance gates и rollback по этапам MVP; work_key=mvp-acceptance-rollback; related=none

### PUBLISHER — Публикация, квитанции и capability

- APA-P00.A03.S01 [VALIDATION/PARTIAL]: Проверить write/readback для всех классов исполнителей; work_key=executor-capability-matrix; related=none
- APA-P00.A03.S02 [CONTROL/BLOCKED]: Выбрать разрешённый периодический research runner без платных API; work_key=unattended-runner-selection; related=none
- APA-P00.A03.S03 [BUILD/PARTIAL]: Publisher, дедупликация, retry, heartbeat и ошибки; work_key=publisher-and-recovery; related=APA-P60.A02.S02
- APA-P00.A03.S04 [VALIDATION/PARTIAL]: Два независимых SOURCE цикла с GitHub readback; work_key=two-independent-source-publishes; related=none

### SDK_NATIVE — Archicad 29 native SDK

- APA-P10.A01.S01 [RESEARCH/PARTIAL]: AC29 SDK headers и native create/change/get сигнатуры; work_key=sdk-native-signatures; related=none
- APA-P10.A01.S02 [RESEARCH/PARTIAL]: Этажи, building materials, surfaces, composites, profiles, связи; work_key=sdk-attributes-stories; related=none
- APA-P10.A01.S03 [RESEARCH/PARTIAL]: Morph/Roof/Shell/Openings/SEO/3D dump; work_key=sdk-geometry-modeldump; related=none

### SYNTHESIS — Синтез research → implementation

- APA-P50.A03.S01 [INTEGRATION/READY]: Синтез тем: источник → решение → MVP → тесты; work_key=research-to-mvp-synthesis; related=APA-P30.A02.S01
- APA-P50.A03.S02 [VALIDATION/READY]: Проверка готовности интеграции и отсутствия повторов; work_key=integration-go-no-go; related=none

### TAPIR_PYTHON — Tapir и Python/JSON

- APA-P10.A02.S01 [RESEARCH/PARTIAL]: Tapir публичные версии и Python/JSON vs локальная 1.5.10; work_key=tapir-python-compatibility; related=APA-P50.A02.S01

### TESTS — Read-only и разрешённые live-тесты

- APA-P20.A01.S01 [VALIDATION/READY]: Read-only provenance AC29 SDK/APX/source SHA; work_key=ac29-sdk-apx-provenance; related=none
- APA-P20.A01.S02 [VALIDATION/READY]: Read-only доступность команд, GDL, MEP, model dump; work_key=read-only-command-capabilities; related=none
- APA-P20.A01.S03 [VALIDATION/READY]: Сохранить PASS/FAIL с raw evidence; work_key=raw-test-evidence-register; related=none
- APA-P20.A02.S01 [CONTROL/READY]: План изолированных тестов, rollback, критерии; work_key=isolated-live-test-plan; related=none
- APA-P20.A02.S02 [CONTROL/BLOCKED]: Получить отдельное разрешение на изменение BIM/APX; work_key=owner-live-write-permission; related=none
- APA-P20.A02.S03 [VALIDATION/BLOCKED]: Протоколировать разрешённые live тесты; work_key=isolated-live-test-results; related=none

### TOOL_INTEGRATION — Каталог и интеграция инструментов

- APA-P50.A02.S01 [RESEARCH/READY]: Единый каталог AC29 SDK/Tapir/Python/GDL/IFC/MEP инструментов; work_key=tool-capability-catalog; related=APA-P10.A02.S01, APA-P10.A02.S02, APA-P10.A02.S03, APA-P10.A02.S04
- APA-P50.A02.S02 [INTEGRATION/READY]: Выявить дубли функций между инструментами и выбрать adapter boundaries; work_key=tool-adapter-overlap-map; related=APA-P10.A03.S01
- APA-P50.A02.S03 [BUILD/READY]: Спланировать безопасное объединение инструментов; work_key=tool-consolidation-roadmap; related=none
