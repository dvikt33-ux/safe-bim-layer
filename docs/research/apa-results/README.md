# APA — единый GitHub-журнал исследований

Дата создания: 2026-10-10. Цель: **сохранять проверяемые результаты исследования Archicad Project Accelerator (APA) для Archicad 29 в GitHub**. Slack #apa-research используется для оперативной передачи событий, но не заменяет сохраняемую техническую документацию.

## Режим работы, установленный владельцем (2026-10-10)

**Исследования APA выполняются в обычных чатах ChatGPT с подключённым GitHub; Deep Research не является исследовательским движком по умолчанию и не запускается без отдельного прямого указания владельца.** Результат каждого существенного прохода должен быть сохранён в этом hub через GitHub commit + API readback **до** объявления о завершении. Исчезнувший ответ/отчёт нельзя заменять новой сессией Deep Research без согласия; найденные в GitHub/Slack фрагменты маркируются по происхождению, а не выдаются за полный утраченный отчёт.

Запрос на круглосуточный режим означает последовательные обычные исследовательские проходы и публикации. **Он не доказывает наличие работающего 24/7 runner**: расписание, права GitHub и фактические циклы должны быть проверены отдельно. Пока это не подтверждено, статус NOT_RUNNING.

## ⚙️ Единый управляющий APA Project Controller (2026-10-10)

**Единственный источник новых поручений и актуальных статусов:** [PROJECT_PLAN.json](control/PROJECT_PLAN.json). **Старт любому чату:** [HANDOFF](control/generated/HANDOFF.md) → [CONTROL_BOARD](control/generated/CONTROL_BOARD.md) → [TASK_CARDS](control/generated/TASK_CARDS.md). [THEMES](control/generated/THEMES.md) связывает 15 тематических направлений, [RELATIONSHIPS](control/generated/RELATIONSHIPS.md) — зависимости и связанные работы. [Инструкция управляющего](control/README.md).

[GitHub Actions 38046747207](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046747207) **SUCCESS**: 6 publisher + 12 controller offline tests, проверки claim/inbox, автоматическое построение 6 views и GitHub REST readback. План содержит **50 S-ID и 15 тематических направлений**; **актуальные** статусы, число артефактов и назначений брать только из [STATE.json](control/generated/STATE.json), не из ручных текстов. Publisher и контроллер работают по push, **автономный ChatGPT 24/7 NOT_RUNNING**. Старые flat отчёты пока не полностью сопоставлены; статусы в старых ручных документах не заменяют PROJECT_PLAN.

**Первый реальный проход через управляющего:** [APA-P50.A01.S01 — карта пяти legacy reports и одного V2](runs/2026-10-10/APA-RUN-20261010-110048Z-legacy-traceability/REPORT.md), [receipt DONE_PUBLISHED](receipts/APA-RUN-20261010-110048Z-legacy-traceability.json), [Actions success 38046902061](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046902061). Задача осталась PARTIAL из-за ещё не исследованных архивных веток. Claim освобождён, evidence привязаны к PROJECT_PLAN, board пересобран [Actions 38046959908](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046959908).

## ОТКРЫВАТЬ СНАЧАЛА: единый центр управления

**Постоянная ссылка из GitHub Issues:** [Issue #23 — APA Research Control Center](https://github.com/dvikt33-ux/safe-bim-layer/issues/23). Она доступна без переключения на исследовательскую ветку; актуальные данные находятся в этой папке.



**Это единственная каноническая папка для публикации новых исследований APA.** Старые ветки — архив/источники, не места для новых отчётов. Новые research-ветки под каждый запуск не создавать.

1. **[CURRENT_STATUS — что делается прямо сейчас](CURRENT_STATUS.md)**: ПЛАН → ДЕЙСТВИЕ → ТЕКУЩИЙ ПОДШАГ, выполнено/не выполнено, следующий шаг.
2. **[MASTER_PLAN — полный иерархический план](MASTER_PLAN.md)**: стабильные P/A/S-ID и критерии завершения.
3. **[RESEARCH_QUEUE — очередь](RESEARCH_QUEUE.md)**: приоритет, исполнитель, вход, выход, блокировки.
4. **[ARTIFACT_REGISTER — что реально опубликовано](ARTIFACT_REGISTER.md)**: прямые ссылки и уровни проверки, включая старые ветки.
5. **[BRANCH_REGISTRY — где какие ветки](BRANCH_REGISTRY.md)**: canonical/archive/code, запрет хаотичного ветвления.
6. **[AGENT_PROTOCOL — инструкция любому чату/агенту](AGENT_PROTOCOL.md)**: read → research → commit → readback → index.
7. **[RESEARCH_TEMPLATE — шаблон каждого прохода](RESEARCH_TEMPLATE.md)**: обязательная лестница ПЛАН → ДЕЙСТВИЕ → ПОДШАГ.
8. **[AUTOMATION_AND_GATES — 24/7 архитектура и ограничения](AUTOMATION_AND_GATES.md)**: **NOT_RUNNING**, пока нет подтверждённого runner.
9. **[PUBLISHING_PROTOCOL — контракт публикации](PUBLISHING_PROTOCOL.md)**: commit SHA и readback обязательны.

## APA Research OS — сохранённый аудит и внедрение

- [Переданный владельцем аудит Research OS — содержательно полная публикационная версия](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md) — **USER_SUPPLIED_REPORT**, не самостоятельная техническая верификация.
- [72 ветки и PR: полный снимок названий/SHA, forensic stage 1/2](inventories/FULL_BRANCH_INVENTORY.md) и [JSON](inventories/BRANCH_HEADS_20261010.json). Ветки не удалены; ancestry/unique artifacts ещё не проверены.
- [RUN_EVENT_V2.schema.json](protocol/RUN_EVENT_V2.schema.json) — машинная схема; [PUBLISHER_CONTRACT](protocol/PUBLISHER_CONTRACT.md) — идемпотентность, commit/readback и crash recovery; [EVIDENCE_POLICY](protocol/EVIDENCE_POLICY.md) — статусы доказательств.
- [Receipt readback исходного аудита](receipts/APA-RUN-20261010-102800Z-research-os-audit-readback.json) — зафиксирован commit/blob SHA, **не** автоматический publisher.

**Решение:** Split-Plane APA Research OS. **Автоматический push-triggered publisher DEPLOYED**: [GitHub Actions success 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668), [synthetic receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json), [generated V2 index](generated/INDEX.md), [operator README](../../../tools/apa_publisher/README.md). Research plane — обычный ChatGPT; **24/7 research runner NOT_RUNNING**, legacy indexes manual. Не запускать Deep Research без отдельного разрешения.

## Накопленные исследовательские материалы

- [Реестр 12 находок APA от 10.10.2026](2026-10-10-research-register.md)
- [Текущие технические блокировки](CURRENT_BLOCKERS.md)
- [APA-DOC-PIPELINE-01: Publisher/Layout](runs/2026-10-10/apa-technical-20261010-094254-publisher-layout-01.md)
- [Архивные исследования и ссылки на другие ветки](ARTIFACT_REGISTER.md)

**Правило одного результата:** каждый проход обязан завершиться ссылкой на файл и commit SHA, проверенными повторным чтением через GitHub API. Если публикация не состоялась, писать GITHUB_PUBLISH_BLOCKED, а не DONE. Никакая существующая сессия Deep Research сама по себе не доказывает автоматический GitHub push.

## Правила достоверности

1. `SOURCE_VERIFIED` означает, что прочитан первоисточник, но это не означает успешный вызов в Archicad.
2. `OFFLINE_PASS`, `BUILD_PASS` и `LIVE_PASS` относятся исключительно к заявленному испытанию и конкретной версии/среде; **не переносить статус на другие стадии**.
3. `REPORTED` — факт или результат присутствует в PR/журнале как сообщение другой сессии, но не был независимо воспроизведён при составлении этого реестра.
4. `NOT_VERIFIED`, `BLOCKED`, `CONFLICT` — явные состояния без домысливания.
5. Для любого важного технического вывода требуются **точная ссылка на прочитанный фрагмент документации или исходного кода и применимость к AC29**. Заголовок и поисковый сниппет недостаточны.
6. Если файл/публикация не подтверждены API GitHub, результат считается **неопубликованным**.
7. Не добавлять токены, приватные журналы, PLN, APX и необезличенные локальные пользовательские данные.

## Ветвление и публикация

Исследовательская ветка: `research/apa-verified-results-hub-20261010`. Не меняет рабочие APX/PLN/исходники и не вносит правки в `main` до отдельного ревью.

Ежедневные новые результаты должны сохраняться как отдельные Markdown-файлы, например `docs/research/apa-results/runs/2026-10-10/apa-technical-YYYYMMDD-HHMM.md`, с уникальным именем. Дубли не создавать; новый отчёт должен ссылаться на прежний вывод и добавлять только существенную новую информацию.

## Связанные PR и журнал

- [PR #20 — GDL diagnostic](https://github.com/dvikt33-ux/safe-bim-layer/pull/20)
- [PR #21 — Slack coordinator](https://github.com/dvikt33-ux/safe-bim-layer/pull/21)
- [PR #16 — accelerator integration](https://github.com/dvikt33-ux/safe-bim-layer/pull/16)
- [PR #17 — SomeStuff SyncGuids](https://github.com/dvikt33-ux/safe-bim-layer/pull/17)
- [Slack #apa-research](https://app.slack.com/client/T0C847UM0A2/C0C886E1PGR)

Этот журнал намеренно не заявляет, что Deep Research, фоновые задачи или Opera имеют право на запись в GitHub: доступ к действию проверяется в каждом конкретном запуске.
