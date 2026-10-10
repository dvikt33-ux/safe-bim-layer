# APA — единственный Project Controller / Control Board

**Source of truth:** [PROJECT_PLAN.json](../../../../../docs/research/apa-results/control/PROJECT_PLAN.json).
This file is generated. Never dispatch from chat memory or edit this board.
**Execution trigger:** ChatGPT Scheduled Tasks (user-configured, not a controller cron).
**Scheduler state:** CONFIGURED_UNVERIFIED; **Publisher:** DEPLOYED; **verified 24/7:** NOT_RUNNING.

## Task status

| Status | Count |
| --- | ---: |
| BLOCKED | 8 |
| CLAIMED | 0 |
| DONE_PUBLISHED | 10 |
| IN_PROGRESS | 0 |
| PARTIAL | 11 |
| READY | 22 |
| SUPERSEDED | 0 |
| DISPATCHABLE_NOW | 16 |
| HELD_BY_DEPENDENCIES | 17 |
| EXPIRED_LEASES | 0 |

## Claimed tasks

| Task | Owner | Lease until | Work key |
| --- | --- | --- | --- |
| — | — | — | — |

## CONTROL — 0 ready

| Priority | Task | Acceptance |
| --- | --- | --- |
| — | — | — |

## CONSOLIDATION — 3 ready

| Priority | Task | Acceptance |
| --- | --- | --- |
| P0 | APA-P00.A01.S03 — Инвентаризировать 72 ветки и PR, проверить уникальные результаты и ancestry | Список уникальных артефактов, SHA, дубликатов и неизвестного |
| P0 | APA-P00.A02.S03 — Связать старые находки с S-ID и удалить логические дубли без удаления оригиналов | Evidence map и superseded_by для дублей |
| P0 | APA-P50.A01.S01 — Карта связей: исследования ↔ S-ID ↔ артефакты ↔ PR | Traceability matrix, orphan report list |

## RESEARCH — 8 ready

| Priority | Task | Acceptance |
| --- | --- | --- |
| P1 | APA-P10.A01.S01 — AC29 SDK headers и native create/change/get сигнатуры | Версии SDK, первоисточники, проверенные сигнатуры |
| P1 | APA-P10.A01.S02 — Этажи, building materials, surfaces, composites, profiles, связи | Матрица native elements/attributes и readback |
| P1 | APA-P10.A01.S03 — Morph/Roof/Shell/Openings/SEO/3D dump | Матрица покрытия и побочных эффектов |
| P1 | APA-P10.A02.S01 — Tapir публичные версии и Python/JSON vs локальная 1.5.10 | Compatibility matrix с source SHA |
| P1 | APA-P10.A02.S02 — GDL/TN, Unicode, target identity и 92 ошибок | Разбор blockers без ложного LIVE |
| P1 | APA-P10.A02.S04 — Native MEP/Tapir MEP команды, трассы, порты | MEP command/route/port matrix |
| P1 | APA-P50.A02.S01 — Единый каталог AC29 SDK/Tapir/Python/GDL/IFC/MEP инструментов | Capability matrix, версии, пересечения |
| P2 | APA-P10.A02.S03 — MCP/IFC/openBIM и альтернативы | Матрица альтернатив с границами |

## BUILD — 1 ready

| Priority | Task | Acceptance |
| --- | --- | --- |
| P0 | APA-P00.A03.S03 — Publisher, дедупликация, retry, heartbeat и ошибки | Publisher E2E + оставшиеся recovery/heartbeat gates |

## INTEGRATION — 0 ready

| Priority | Task | Acceptance |
| --- | --- | --- |
| — | — | — |

## VALIDATION — 4 ready

| Priority | Task | Acceptance |
| --- | --- | --- |
| P0 | APA-P00.A03.S01 — Проверить write/readback для всех классов исполнителей | Capability matrix по каждому исполнителю |
| P1 | APA-P00.A02.S04 — Контролировать receipt/commit/readback всех завершённых отчётов | Нет ложных DONE без квитанции |
| P1 | APA-P60.A02.S03 — Протестировать CAS-claim, lease, duplicate prevention | Offline tests PASS; concurrent two-writer CAS and lease-expiry recovery NOT_VERIFIED |
| P1 | APA-P60.A02.S04 — Ввести сбор предложений задач исследователями и принятие аудитором в PROJECT_PLAN | Процесс discovery proposal -> independent audit decision -> TASK registry admission задокументирован; CAS claim/readback и уникальность work_key/dependency DAG соблюдены; Scheduled instructions согласованы. End-to-end независимая публикация proposal, аудит, регистрация и валидатор контроллера подтверждены фактами. Не объявлять DONE по одним инструкциям. |

## Waiting for dependencies

| Task | Missing completed prerequisites |
| --- | --- |
| APA-P00.A03.S04 | APA-P00.A03.S03 |
| APA-P10.A03.S01 | APA-P10.A01.S01, APA-P10.A02.S01, APA-P10.A02.S03 |
| APA-P10.A03.S02 | APA-P10.A03.S01 |
| APA-P20.A01.S01 | APA-P10.A01.S01 |
| APA-P20.A01.S02 | APA-P20.A01.S01 |
| APA-P20.A01.S03 | APA-P20.A01.S02 |
| APA-P20.A02.S01 | APA-P20.A01.S03 |
| APA-P30.A01.S01 | APA-P10.A03.S02, APA-P20.A01.S03 |
| APA-P30.A01.S02 | APA-P30.A01.S01 |
| APA-P30.A02.S01 | APA-P30.A01.S01 |
| APA-P30.A02.S02 | APA-P30.A02.S01 |
| APA-P50.A01.S02 | APA-P50.A01.S01 |
| APA-P50.A01.S03 | APA-P50.A01.S01 |
| APA-P50.A02.S02 | APA-P50.A02.S01 |
| APA-P50.A02.S03 | APA-P50.A02.S02, APA-P30.A01.S01 |
| APA-P50.A03.S01 | APA-P50.A01.S03, APA-P50.A02.S02 |
| APA-P50.A03.S02 | APA-P50.A03.S01 |

## Warnings

- Unmapped V2 manifests: 0
- Expired leases: none
- Legacy flat reports remain in ARTIFACT_REGISTER; do not silently infer their task links.
- DONE_PUBLISHED needs accepted evidence, not only a receipt.
