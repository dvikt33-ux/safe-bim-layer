# APA — единая очередь исследований и разбор входящих материалов

**Источник приоритета:** [MASTER_PLAN](MASTER_PLAN.md). **Главный активный подшаг:** [CURRENT_STATUS](CURRENT_STATUS.md). Новая задача без P/A/S-ID не принимается в исполнение.

| Очередь | Подшаг | Приоритет | Входной материал | Состояние / выход |
| --- | --- | --- | --- | --- |
| Q-001 | APA-P00.A03.S01 | P0 | GitHub connector, Deep Research, scheduler | PARTIAL: ordinary ChatGPT GitHub write/readback PASS; Deep Research not used, unattended scheduled write NOT_VERIFIED |
| Q-002 | APA-P00.A01.S03 | P0 | [72 branches and 22 PR map](inventories/FULL_BRANCH_INVENTORY.md) | IN_PROGRESS: APA Research OS audit published; branch snapshot and SHA verified, ancestry/unique artifacts NOT_VERIFIED |
| Q-003 | APA-P00.A02.S03 | P0 | [ARTIFACT_REGISTER](ARTIFACT_REGISTER.md), 12 findings | QUEUED; дедуплицированная evidence map |
| Q-004 | APA-P10.A01.S01 | P1 | SDK AC29 29.3100, primary headers/docs | IN_PROGRESS; [SEO/Trim/Morph source audit](runs/2026-10-10/apa-discovery-20261010-102440-slinktrim-9f2b7.md) SOURCE_VERIFIED; SDK header/build/live NOT_VERIFIED; [Get3DInfo/contacts source audit](runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md) SOURCE_VERIFIED (docs), SDK header/build/live NOT_VERIFIED |
| Q-005 | APA-P10.A02.S01 | P1 | Tapir public tags, local 1.5.10 provenance | QUEUED; compatibility matrix |
| Q-006 | APA-P10.A02.S02 | P1 | PR #20, GDL audit, catalog errors | QUEUED; blocker-specific proof |
| Q-007 | APA-P10.A02.S04 | P1 | MEP API and Tapir commands | QUEUED; command/route/port matrix |
| Q-008 | APA-P10.A03.S01 | P2 | Findings from P10 | QUEUED; architecture alternatives |
| Q-009 | APA-P30.A02.S01 | P2 | verified technical matrix | QUEUED; MVP milestones |
| Q-010 | APA-P40.A01.S01 | P0-OPS | [AUTOMATION_AND_GATES](AUTOMATION_AND_GATES.md) | BLOCKED_EXTERNAL; runtime choice + permissions |

| Q-011 | APA-P00.A03.S03 | P0-OPS | [Workflow](../../.github/workflows/apa-research-publisher.yml), [publisher](../../tools/apa_publisher/publisher.py), [receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json) | PUBLISHER_DEPLOYED: synthetic E2E success 38045964668; idempotent rerun 38046020069; research scheduler/heartbeat NOT_RUNNING |

## Правила диспетчеризации

- Новая тема: найти подходящий S-ID или дополнить MASTER_PLAN; дать Q-ID; затем начать исследование.
- Одна запись очереди не равна одному чату. Любой чат может выполнить Q-ID, но обязан сохранить результат в одном canonical hub.
- Смена исполнителя: читать CURRENT_STATUS + последний опубликованный run; не пересказывать всё заново и не плодить ветки.
- Повторный отчёт без новой проверяемой информации не публиковать; обновлять старый только с provenance и без потери истории.
- Если source недоступен, записать NOT_VERIFIED — DOCUMENT_NOT_READ, не закрывать задачу.
- Если публикация сорвалась, задача остаётся IN_PROGRESS / GITHUB_PUBLISH_BLOCKED до подтверждённого readback.
