# APA — обязательная публикация результатов в GitHub

## Split-Plane / V2 protocol

[RUN_EVENT_V2 JSON Schema](protocol/RUN_EVENT_V2.schema.json), [PUBLISH_REQUEST_V1](protocol/PUBLISH_REQUEST_V1.schema.json), [publisher contract](protocol/PUBLISHER_CONTRACT.md), [evidence policy](protocol/EVIDENCE_POLICY.md). **Push-triggered publisher DEPLOYED**: [workflow](../../../.github/workflows/apa-research-publisher.yml), [source](../../../tools/apa_publisher/publisher.py), [synthetic E2E success](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668), [automatic receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json). Legacy flat reports остаются; 24/7 research scheduler не развёрнут.

Порядок: immutable report/manifest/evidence → GitHub commit → readback/hash → отдельный receipt → восстановимые проекции/индексы → index commit/readback → DONE_PUBLISHED. Если индексация падает, восстанавливать из immutable run, не повторять исследование. До готовности index builder текущие Markdown обновляются вручную и проверяются. Не вставлять commit SHA в файл того же коммита (самоссылка). Не считать SOURCE_VERIFIED равным LIVE_PASS.

## Режим исполнения по прямому указанию владельца

Исследования выполняются в **обычных чатах ChatGPT с GitHub connector**; Deep Research **не запускать по умолчанию** и не использовать как замену обычным чатам или автоматическому GitHub push. Каждое исследование: первоисточник → проверка → Markdown в canonical hub → commit SHA → readback → реестр/очередь/статус. Запрос на 24/7 не означает, что runner уже работает; проверять фактическое расписание и публикации. Если ранее показанный Deep Research отчёт исчез, не приписывать его содержимое другим артефактам и не запускать повторно без разрешения.

## Принцип

**GitHub = долговременный журнал доказательств и обсуждаемых решений; Slack = быстрые уведомления.** Статус `SAVED_TO_GITHUB` присваивается только после успешного ответа GitHub write API с commit SHA и последующего readback файла/ветки. Нельзя обещать автоматическую запись, если в конкретном сеансе нет write-инструментов.

## Действия в каждом исследовательском проходе

1. Прочитать актуальные GitHub PR, [реестр](2026-10-10-research-register.md) и свежие сообщения Slack `#apa-research`.
2. Исследовать только новые вопросы или новые факты по старым вопросам; читать фактическое содержание первоисточника и необходимые фрагменты кода, не только названия/сниппеты.
3. Записать найденное в новый Markdown-файл с **уникальным** путём `docs/research/apa-results/runs/YYYY-MM-DD/<track>-<utc-date>-<HHMMSS>-<short-id>.md` в ветке `research/apa-verified-results-hub-20261010`. Для каждого факта: ID, время UTC, проблема, точные ссылки, доказательство, phase, status, ограничения, следующий тест, не менять main.
4. Если нет новых результатов, можно опубликовать короткий checkpoint **только при существенном изменении статуса**, иначе не создавать шум.
5. После подтверждения GitHub commit SHA при необходимости отправить в Slack сообщение `APA_EVENT_V1` с `evidence_urls`, включая URL нового файла/коммита. **Не публиковать как проверенный результат без доказательства чтения документа.**
6. Если GitHub write недоступен, сохранить полный Markdown в видимом ответе, указать `GITHUB_PUBLISH_BLOCKED`, причину и шаг для переноса. Не утверждать, что результат опубликован.
7. Если Slack write недоступен, GitHub-документ остаётся первичным; указать `SLACK_PUBLISH_BLOCKED`, не считать это причиной потерять результаты.

## Обязательная иерархия работы (дополнение от 2026-10-10)

Единственный master plan — [MASTER_PLAN.md](MASTER_PLAN.md); текущий подшаг — [CURRENT_STATUS.md](CURRENT_STATUS.md); входящие задачи — [RESEARCH_QUEUE.md](RESEARCH_QUEUE.md). Перед любым новым исследованием исполнитель обязан открыть эти три файла и [ARTIFACT_REGISTER.md](ARTIFACT_REGISTER.md).

**Каждый запуск и каждый файл начинаются лестницей:**
- **ПЛАН** — APA-PXX, название.
  - **ДЕЙСТВИЕ** — APA-PXX.AYY, название.
    - **ТЕКУЩИЙ ПОДШАГ** — APA-PXX.AYY.SZZ, название, критерий завершения.

Запрещено создавать новую исследовательскую ветку для каждого отчёта: новые материалы направляются только в research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/. Старые ветки сохраняются как архив; см. [BRANCH_REGISTRY.md](BRANCH_REGISTRY.md).

**Транзакция публикации:** 1) файл отчёта; 2) commit SHA; 3) readback и сравнение содержимого; 4) обновление ARTIFACT_REGISTER; 5) обновление RESEARCH_QUEUE и CURRENT_STATUS; 6) краткая ссылка на файл/коммит в ответе. Если любой шаг не завершён, явно фиксировать частичный статус и не заявлять DONE_PUBLISHED.

**Режим 24/7:** см. [AUTOMATION_AND_GATES.md](AUTOMATION_AND_GATES.md). Пока реальный runner не подключён и не прошёл 24-часовую проверку, статус **NOT_RUNNING**. Обычный чат и Deep Research не равны постоянно работающему процессу. Система не должна скрывать этот факт или требовать от владельца вручную собирать непушенные файлы по чатам.

## Минимальный шаблон нового исследования

```md
# APA — <тема>
- UTC timestamp:
- Task/event ID:
- AC version/API version:
- Phase: SOURCE | SYNTHETIC | OFFLINE | BUILD | LIVE
- Status: INFO | PASS | BLOCKED | NOT_VERIFIED | CONFLICT
- Source commit / URL:
- Что именно было прочитано:
- Проверенные факты:
- Непроверенные допущения:
- Сравнение архитектур A/B:
- Последствия для MVP:
- Read-only test / PASS/FAIL:
- Независимый аудит:
- Slack event permalink (только если подтверждена публикация):
```

## Ограничения

- Только штатный ChatGPT Plus без Work, Codex, платного OpenAI API и локальной LLM.
- Никаких изменений PLN, установленных APX, production-веток и основного кода.
- Писать исключительно исследовательские Markdown-документы в выделенную ветку. Не выполнять merge без отдельной авторизации.
- Не включать приватные модельные данные, пароли, токены, персональные сведения и сырые большие дампы.
- Создание файлов через GitHub connector не гарантируется для запланированных задач — если нет доступного инструмента, вывод должен явно сообщать об ограничении и отдавать готовый текст для публикации.
