# APA — реестр реально опубликованных материалов

**Срез:** 2026-10-10. Этот реестр различает **файл найден и прочитан** от **его технический вывод независимо проверен**. Не делать вид, что все прошлые исследования доступны или проверены.

## Текущий центр

| ID | Материал | Где лежит | Состояние публикации | Проверка содержания |
| --- | --- | --- | --- | --- |
| HUB-001 | [README](README.md) | canonical hub | GITHUB_READBACK_VERIFIED | Прочитан; служебная навигация |
| HUB-002 | [Реестр APA-01…APA-12](2026-10-10-research-register.md) | canonical hub | GITHUB_READBACK_VERIFIED | Много REPORTED и SOURCE_CANDIDATE; независимые LIVE не подтверждены |
| HUB-003 | [CURRENT_BLOCKERS](CURRENT_BLOCKERS.md) | canonical hub | GITHUB_READBACK_VERIFIED | Сводка; не самостоятельное LIVE-доказательство |
| HUB-004 | [PUBLISHING_PROTOCOL](PUBLISHING_PROTOCOL.md) | canonical hub | GITHUB_READBACK_VERIFIED | Правила публикации |
| HUB-005 | [APA-DOC-PIPELINE-01: Publisher/Layout](runs/2026-10-10/apa-technical-20261010-094254-publisher-layout-01.md) | canonical hub | GITHUB_READBACK_VERIFIED | SOURCE claim, installed APX LIVE NOT_VERIFIED |
| OPS-001 | [MASTER_PLAN](MASTER_PLAN.md) | canonical hub | GITHUB_READBACK_VERIFIED | План, не исследовательское доказательство |
| OPS-002 | [BRANCH_REGISTRY](BRANCH_REGISTRY.md) | canonical hub | GITHUB_READBACK_VERIFIED | Частичная карта веток |
| OPS-003 | [RESEARCH_TEMPLATE](RESEARCH_TEMPLATE.md) | canonical hub | GITHUB_READBACK_VERIFIED | Шаблон |
| OPS-004 | [CURRENT_STATUS](CURRENT_STATUS.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Операционный статус |
| OPS-005 | [AGENT_PROTOCOL](AGENT_PROTOCOL.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Инструкция всем исполнителям |
| OPS-006 | [AUTOMATION_AND_GATES](AUTOMATION_AND_GATES.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Проект автоматики, не действующий сервис |
| OPS-007 | [RESEARCH_QUEUE](RESEARCH_QUEUE.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Очередь задач |

## Найденные в архивных ветках

| ID | Материал | URL | Состояние |
| --- | --- | --- | --- |
| ARC-001 | Archicad full capability audit — index | [INDEX_20260928](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/archicad-full-capability-audit-20260928/research/INDEX_20260928.md) | GITHUB_READBACK_VERIFIED; ссылки на ledger/architecture/tests; эти дочерние документы ещё не проверены |
| ARC-002 | GDL Blocker 1 forensic | [APA_TN-GDL-CREATE-01_BLOCKER1_AUDIT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-tn-gdl-create-01-blocker1-audit-20261009/docs/research/APA_TN-GDL-CREATE-01_BLOCKER1_AUDIT_2026-10-09.md) | GITHUB_READBACK_VERIFIED; технические утверждения не воспроизведены в этом проходе |
| ARC-003 | Tapir 1.5.10 upstream contract | [tapir-1510-upstream-contract-audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-20261009-api-mep-batching-audit/docs/tapir-1510-upstream-contract-audit-20261009.md) | GITHUB_READBACK_VERIFIED; runtime 1.5.10 ≠ автоматически исходники 1.5.9 |
| ARC-004 | Ветка с GDL checkpoint | [research/apa-tn-gdl-create-01-checkpoint-20261009](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-tn-gdl-create-01-checkpoint-20261009) | BRANCH_FOUND; конкретные дельты не прочитаны |
| ARC-005 | Ветка с GDL native probe | [research/apa-tn-gdl-create-01-native-probe-20261009](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-tn-gdl-create-01-native-probe-20261009) | BRANCH_FOUND; дельты не прочитаны |
| ARC-006 | Архив MEP bridges | [research/apa-20261009-resource-mep-bridges-audit-v1](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-20261009-resource-mep-bridges-audit-v1) | BRANCH_FOUND; дельты не прочитаны |
| ARC-007 | Старый независимый индекс | [RESEARCH_INDEX](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-archicad29-independent-audit-20261010/RESEARCH_INDEX.md) | GITHUB_READBACK_VERIFIED; POINTER_ONLY, не полный отчёт |

## Известные пробелы и правила добавления

- Полный итог прежнего Deep Research: **NOT_FOUND_IN_CHECKED_GITHUB_ARTIFACTS**, не заявлять о восстановлении.
- Непушенные локальные файлы: **NOT_VERIFIED / LOCAL_ACCESS_REQUIRED**.
- Наличие файла в GitHub: это только GITHUB_READBACK_VERIFIED. Истинность конкретного API claim требует отдельного SOURCE_VERIFIED/BUILD_PASS/LIVE_PASS.
- Для каждого нового отчёта добавлять: ID, S-ID, прямую ссылку, commit SHA, readback, метод проверки, статус, дату, источник; не дублировать старые документы.
- Если файл существует в архиве, сначала дать ссылку и delta, не создавать копию в другой ветке.
