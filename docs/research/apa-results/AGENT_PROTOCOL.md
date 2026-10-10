# APA — обязательный протокол для каждого чата, исследователя и агента

Это не системная инструкция ChatGPT и не гарантия, что другой чат автоматически её увидит. Это **контракт проекта**, который исполнитель должен прочитать через GitHub в начале каждого прохода.

## Приоритетный режим исполнения — инструкция владельца от 2026-10-10

- **Обычный чат ChatGPT + GitHub connector** — стандартный исполнитель исследований, проверок и публикации APA. Исследование может идти несколькими обычными чатами/разрешёнными запланированными запусками; каждый сохраняет доказательства в один canonical hub.
- **Не запускать Deep Research**, не назначать его движком для 24/7 и не тратить его попытки без отдельного явного запроса. Если отчёт прежней сессии недоступен, не запускать новую вместо восстановления.
- До сообщения «готово» — GitHub write, commit SHA, readback и регистрация. Ссылки на Slack, пустые индексы, планы и сообщения виджета не заменяют сохранённый результат.
- 24/7 — требование к процессу, **не** характеристика обычного чата. Не заявлять, что он запущен, пока не подтверждены расписание, исполнитель и два реальных цикла с SHA/readback. Не использовать платные API/Work/Codex для обхода ограничения.
- Любое «применить исследование» сначала означает сверить первоисточник, версии, код и безопасные gates. Не изменять PLN/APX/main и проверенные ветки без отдельного разрешения.

## Автоматическая публикация через inbox (DEPLOYED)

Обычный ChatGPT может создать полный [PUBLISH_REQUEST_V1](protocol/PUBLISH_REQUEST_V1.schema.json) JSON в [inbox](inbox/) на canonical branch, включая Markdown-отчёт и source/evidence статус. Push запускает [GitHub Actions publisher](../../.github/workflows/apa-research-publisher.yml). Исполнитель обязан дождаться успешного run и [receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json); до этого не сообщать DONE_PUBLISHED. [Проверенный synthetic E2E run 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668), [idempotent rerun 38046020069](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046020069). Это publisher, **не** самостоятельный исследователь и не 24/7 scheduler. При GitHub Actions failure — GITHUB_PUBLISH_BLOCKED; не терять исходный inbox/report, не запускать повторное исследование.

## Новый контракт V2 и восстановление

Перед работой прочитать [сохранённый аудит APA Research OS](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md), [RUN_EVENT_V2](protocol/RUN_EVENT_V2.schema.json), [PUBLISHER_CONTRACT](protocol/PUBLISHER_CONTRACT.md) и [EVIDENCE_POLICY](protocol/EVIDENCE_POLICY.md). **Выполнение схемы — проект, а не включённый publisher.**

1. Использовать существующий canonical hub; не создавать новую ветку для очередного research run.
2. Если есть подтверждённый immutable report, но отсутствует запись в реестре, **достроить индекс**, не запускать повторное исследование.
3. Сверять run_id/evidence fingerprint до публикации дубликата; источник из другого чата/Deep Research помечать USER_SUPPLIED/REPORTED, не SOURCE_VERIFIED.
4. В конце выдавать receipt: branch, path, commit, readback, content hash (только если реально вычислен), evidence status, следующий S-ID. При сбое GITHUB_PUBLISH_BLOCKED.
5. Обычный чат + GitHub connector — основной исполнитель; Deep Research не запускать без прямого разрешения владельца. 24/7 без реального runner не обещать.

## Старт без ручной сортировки владельцем

1. Открыть [README](README.md), [MASTER_PLAN](MASTER_PLAN.md), [CURRENT_STATUS](CURRENT_STATUS.md), [RESEARCH_QUEUE](RESEARCH_QUEUE.md), [ARTIFACT_REGISTER](ARTIFACT_REGISTER.md), [BRANCH_REGISTRY](BRANCH_REGISTRY.md).
2. Определить один ID вида APA-PXX.AYY.SZZ. Если не существует — сначала зарегистрировать в MASTER_PLAN и RESEARCH_QUEUE.
3. В начале ответа и файла показать **ПЛАН → ДЕЙСТВИЕ → ТЕКУЩИЙ ПОДШАГ** с названиями и ID. Указать конкретный критерий завершения.
4. Перед исследованием прочитать уже сохранённые доказательства. Дубли и гипотезы не превращать в SOURCE_VERIFIED.
5. Сохранить отчёт по [RESEARCH_TEMPLATE](RESEARCH_TEMPLATE.md) в docs/research/apa-results/runs/YYYY-MM-DD/<track>-<utc>-<short-id>.md **на ветке research/apa-verified-results-hub-20261010**. Не создавать новую research-ветку.
6. Получить commit SHA и прочитать записанный файл через GitHub API. Только тогда говорить SAVED_TO_GITHUB.
7. Обновить ARTIFACT_REGISTER, RESEARCH_QUEUE и CURRENT_STATUS. Ссылка в чате — только на конкретный опубликованный файл и коммит.
8. Если инструмент записи отсутствует: **GITHUB_PUBLISH_BLOCKED**, полный готовый Markdown, конкретная причина; не говорить, что задача завершена или опубликована.
9. Если Deep Research отдаёт результат только в виджете: это **не GitHub commit**; требуется отдельный подтверждённый шаг публикации. Не перекладывать скрытый ручной поиск по чатам на владельца.

## Ограничения

- Никогда не изменять main/master, PLN, установленные APX, рабочие проверенные ветки или исполняемый код без отдельного разрешения.
- Никаких платных API/моделей/Work/Codex и скрытых расходов.
- Для AC29 указывать версию SDK/APX/исходников и источник; read-only по умолчанию.
- Не помещать в GitHub токены, приватные дампы, персональные данные, проприетарные файлы библиотек.
- PR и Slack — контекст, не подмена первичного доказательства; SOURCE_VERIFIED ≠ LIVE_PASS.

## Финиш одного прохода

Ответить кратко: P/A/S-ID, 1–3 проверенных вывода, прямой URL GitHub, commit SHA, что осталось NOT_VERIFIED и следующий S-ID. **Не просить пользователя распределять файлы по чатам.**
