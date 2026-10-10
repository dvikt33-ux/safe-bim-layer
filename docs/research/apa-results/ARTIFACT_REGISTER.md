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
| RUN-SDK-GET3D-20261010 | [AC29 3D/Opening API: два Get3DInfo и нативные связи](runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md) | canonical hub | GITHUB_READBACK_VERIFIED; [commit d65c5bd](https://github.com/dvikt33-ux/safe-bim-layer/commit/d65c5bd327d077d7873ff720cda6dac3bf8a22cb) | SOURCE_VERIFIED official docs; SDK header/BUILD/LIVE NOT_VERIFIED; **не** полный Deep Research |
| OPS-001 | [MASTER_PLAN](MASTER_PLAN.md) | canonical hub | GITHUB_READBACK_VERIFIED | План, не исследовательское доказательство |
| OPS-002 | [BRANCH_REGISTRY](BRANCH_REGISTRY.md) | canonical hub | GITHUB_READBACK_VERIFIED | Частичная карта веток |
| OPS-003 | [RESEARCH_TEMPLATE](RESEARCH_TEMPLATE.md) | canonical hub | GITHUB_READBACK_VERIFIED | Шаблон |
| OPS-004 | [CURRENT_STATUS](CURRENT_STATUS.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Операционный статус |
| OPS-005 | [AGENT_PROTOCOL](AGENT_PROTOCOL.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Инструкция всем исполнителям |
| OPS-006 | [AUTOMATION_AND_GATES](AUTOMATION_AND_GATES.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Проект автоматики, не действующий сервис |
| OPS-007 | [RESEARCH_QUEUE](RESEARCH_QUEUE.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Очередь задач |

## APA Research OS — материалы из переданного аудита

| ID | Материал | Публикация | Достоверность |
| --- | --- | --- | --- |
| OS-AUDIT-001 | [Сохранённый аудит APA Research OS](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md) | GITHUB_READBACK_VERIFIED, [commit 9b07679](https://github.com/dvikt33-ux/safe-bim-layer/commit/9b076792124d99d67dcc0f01554b4834fc3ed8cb) | USER_SUPPLIED_REPORT, нормализованная версия; исторические claims REPORTED |
| OS-INV-001 | [72 branch heads + PR map JSON](inventories/BRANCH_HEADS_20261010.json) | GITHUB_READBACK_VERIFIED, [commit 7dc6544](https://github.com/dvikt33-ux/safe-bim-layer/commit/7dc65444282d6bf6f14013fd8621328ee08b18a9) | GitHub API branch/head/PR SOURCE_VERIFIED; ancestry/artifacts NOT_VERIFIED |
| OS-INV-002 | [FULL_BRANCH_INVENTORY stage 1/2](inventories/FULL_BRANCH_INVENTORY.md) | GITHUB_READBACK_VERIFIED, [commit 895846f](https://github.com/dvikt33-ux/safe-bim-layer/commit/895846f096aea4440a7e292f8cc89adab79c78d9) | Все 72 имена/SHA, не полная forensic classification |
| OS-SCHEMA-001 | [RUN_EVENT_V2 JSON Schema](protocol/RUN_EVENT_V2.schema.json) | GITHUB_READBACK_VERIFIED, [commit 2ff4dcf](https://github.com/dvikt33-ux/safe-bim-layer/commit/2ff4dcfde139c5f9b52df31ba07b59de9ca6dcd6) | Схема, не работающий publisher |
| OS-CONTRACT-001 | [Publisher / crash recovery](protocol/PUBLISHER_CONTRACT.md) | GITHUB_READBACK_VERIFIED, [commit b736f23](https://github.com/dvikt33-ux/safe-bim-layer/commit/b736f23cf8573febfd6722e42e9db4b63c986f22) | Дизайн и gates; runtime NOT_DEPLOYED |
| OS-POLICY-001 | [Evidence policy](protocol/EVIDENCE_POLICY.md) | GITHUB_READBACK_VERIFIED, [commit d6e60fb](https://github.com/dvikt33-ux/safe-bim-layer/commit/d6e60fb1044489fc88eb8015455464ae04f7f7cb) | Политика, не live-test |
| OS-RECEIPT-001 | [Readback receipt исходного аудита](receipts/APA-RUN-20261010-102800Z-research-os-audit-readback.json) | GITHUB_READBACK_VERIFIED, [commit b64a491](https://github.com/dvikt33-ux/safe-bim-layer/commit/b64a4913249af780abac4b330b3958b5d1f93841) | GitHub blob SHA подтверждён; SHA256 NOT_COMPUTED; index pending |

| OS-PUB-001 | [GitHub Actions automatic publisher workflow](../../../.github/workflows/apa-research-publisher.yml) | DEPLOYED on canonical research branch, [commit 901dd97](https://github.com/dvikt33-ux/safe-bim-layer/commit/901dd973293f3200749b5f37fd5bbfa7f7da4f21) | [Push-triggered E2E run success](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668); no 24/7 research scheduler |
| OS-PUB-002 | [Publisher Python implementation](../../../tools/apa_publisher/publisher.py) + [6 offline tests](../../../tools/apa_publisher/tests/test_publisher.py) | GitHub readback verified; [tests in workflow success](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) | Immutable run, generated index, REST readback, receipt; no Archicad live |
| OS-PUB-003 | [Synthetic automatic REPORT](runs/2026-10-10/APA-RUN-20261010-104437Z-publisher-integration-smoke/REPORT.md), [receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json), [generated STATE](generated/STATE.json) | DONE_PUBLISHED / GITHUB_REST_READBACK_VERIFIED; [workflow 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) | SYNTHETIC only, claims REPORTED; idempotent no-op [workflow 38046020069](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046020069) |


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


## Восстановленные из чата результаты (2026-10-10)

Эти файлы были восстановлены из видимых отчётов ChatGPT после прежних `GITHUB_PUBLISH_BLOCKED`. **Статус содержания: `RECOVERED_FROM_CHAT / REPORTED`, не независимо перепроверенный SOURCE_VERIFIED**. Для каждого файла отдельно подтверждены GitHub `create_file` commit SHA и `fetch_file` readback.

| ID | Восстановленный отчёт | Commit SHA | GitHub readback | Содержание |
|---|---|---|---|---|
| RECOVER-TAPIR-7C3F | [Tapir: разрезы, размеры, автотекст](runs/2026-10-10/apa-recovery-20261010-132600-tapir-docs-7c3f.md) | [3b5197a](https://github.com/dvikt33-ux/safe-bim-layer/commit/3b5197adb2031b81853fd324d1a7fc93d80bbd46) | PASS, blob `efa84fd335ed1073cd3c8be5353e06d3f62990fe` | Предыдущий исходный аудит Tapir 1.5.9; installed 1.5.10 NOT_VERIFIED |
| RECOVER-HOTLINK-277E19 | [Native Hotlink и MEP Transition](runs/2026-10-10/apa-recovery-20261010-132700-hotlink-mep-277e19.md) | [5e03f46](https://github.com/dvikt33-ux/safe-bim-layer/commit/5e03f4693016977b40dd7cf197bf643cb97ef030) | PASS, blob `e6d3eebacaef09c238009e3eb86823e344d7faa6` | AC29 SDK 29.3100 claims; LIVE NOT_VERIFIED |
| RECOVER-IFCMCP-3F759 | [IfcMCP и IfcPatch MergeProjects](runs/2026-10-10/apa-recovery-20261010-132800-ifcmcp-merge-3f759.md) | [7c42418](https://github.com/dvikt33-ux/safe-bim-layer/commit/7c42418a7f64d827e45aa44b2993a67c0adb66cf) | PASS, blob `1a9cb5f5271d5ce41adc16ff61f728763bd464f7` | IfcOpenShell v0.9.0 claims; OFFLINE/BUILD/LIVE NOT_VERIFIED |

**Что осталось:** не считать восстановление файла независимой технической проверкой или завершением подшага PROJECT_PLAN. Для повышения уровня доказательств назначить отдельный source re-audit по указанным pin/version/line links, затем офлайн/изолированные испытания. Обнаруженные повторы с APA-01…APA-12 и архивом должны быть дедуплицированы по исходникам.


## Полные исходники аудитов из вложений — 2026-10-10

В отличие от нормализованных/сокращённых документов, эти две записи — **полные текстовые снимки приложенных владельцем аудитов**. GitHub readback сравнил каждый текст с исходником посимвольно. **Это проверка факта публикации, а не верификация технических выводов.** Ссылки вида `turn…` и `filecite` в оригиналах являются внутренними маркерами исходного исследовательского ответа и не гарантируют независимую открываемость из GitHub.

| ID | Полный исходник | Источник / объём | Commit и readback | Содержание |
| --- | --- | --- | --- | --- |
| IMPORT-FULL-001 | [APA Research OS — оригинал, 735 строк](runs/2026-10-10/apa-source-snapshot-research-os-full-20261010.md) | Вложение владельца `Вставленный текст.txt`, 2026-10-10; 26 160 символов | [fc8d3e7](https://github.com/dvikt33-ux/safe-bim-layer/commit/fc8d3e7a1c18090dad7f66035f8528f4081ce531); EXACT_GITHUB_READBACK_PASS; blob `6eb98cd428836c8fd73fbd2971e50ca9b24cba94` | USER_SUPPLIED_FULL_SOURCE / технические claims REPORTED; [краткая нормализованная версия](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md) существовала ранее, это не новое независимое исследование |
| IMPORT-FULL-002 | [APA Scheduled Task без Work/Codex — оригинал, 715 строк](runs/2026-10-10/apa-source-snapshot-scheduled-task-work-limits-full-20261010.md) | Вложение владельца `Вставленный текст.txt`, 2026-10-10; 31 539 символов | [c3d6945](https://github.com/dvikt33-ux/safe-bim-layer/commit/c3d6945c7972818bb380ccae0ae057488caa1ff8); EXACT_GITHUB_READBACK_PASS; blob `9b96f1f1023ca03d4c1bd7100e8a110f64987a2f` | USER_SUPPLIED_FULL_SOURCE / технические claims REPORTED; практический вывод о write-access обычной Scheduled Task требует отдельного теста именно scheduled execution |

**Что эти записи НЕ закрывают:** все исследования из других чатов, не представленные вложениями или GitHub; полный forensic-аудит уникальных артефактов 72 веток; восстановление утраченных ответов, которых нет ни в источниках, ни в GitHub. Эти пробелы не считать DONE. Исторические отчёты не перезаписывались, `main` не менялся.
