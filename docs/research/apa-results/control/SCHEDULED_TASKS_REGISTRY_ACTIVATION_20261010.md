# APA — подключение существующих Scheduled Tasks к реестру GitHub

**Дата:** 2026-10-10. **S-ID:** APA-P00.A03.S01 (частичная проверка доступности исполнителей). **Режим:** только обычные ChatGPT Scheduled Tasks + GitHub connector; не запускался Work/Codex/OpenAI API.

## Источник истины

- [PROJECT_PLAN.json](PROJECT_PLAN.json) — список задач, зависимости, owner, lease, claim_ref, evidence, статусы.
- [HANDOFF](generated/HANDOFF.md), [CONTROL_BOARD](generated/CONTROL_BOARD.md), [TASK_CARDS](generated/TASK_CARDS.md) — производные, не заменяют PROJECT_PLAN.
- [ChatGPT Scheduled инструкция](CHATGPT_SCHEDULED_TASK.md) — переход состояния READY/PARTIAL → IN_PROGRESS → DONE_PUBLISHED/PARTIAL/BLOCKED.

## Привязаны три реально включённых расписания

| Специализация | ChatGPT Scheduled Task ID | Интервал |
|---|---|---|
| Поиск решений | `6ac83b171cf08191b74e06caaa8ae1c7` | ежечасно в :20 Europe/Moscow |
| Технический анализ | `6ac9752aae8081919d9feeada08ad91e` | ежечасно в :40 Europe/Moscow |
| Независимый аудит | `6ac7664c66f88191a51d8c0a414b0eac` | ежечасно в :00 Europe/Moscow |

Промпты всех трёх обновлены: сначала проверка PROJECT_PLAN → выбор ровно одного eligible S-ID → CAS-claim IN_PROGRESS → GitHub readback → выполнение acceptance → полная публикация → CAS-статус DONE_PUBLISHED/PARTIAL/BLOCKED с evidence и очисткой lease → readback → предложение следующего eligible S-ID. Новые работы сначала вносятся в PROJECT_PLAN; задачи нельзя брать из памяти бесед или занимать параллельно.

**Состояние scheduler в GitHub:** `CONFIGURED_UNVERIFIED`. Это значит, что задачи существуют и инструкции обновлены, но именно scheduled запуск ещё **НЕ доказал** end-to-end GitHub claim/publication/status. 24/7 непрерывная работа НЕ подтверждена.

## Подтверждённые действия этой сессии

1. Из актуального PROJECT_PLAN выбрана уже существующая eligible VALIDATION задача `APA-P00.A03.S01`, status до изменения `PARTIAL`.
2. В начале работы GitHub CAS-запись статуса `IN_PROGRESS`, owner/claim_ref/lease и readback: [commit e165500](https://github.com/dvikt33-ux/safe-bim-layer/commit/e16550042ea7a22f82b4d44d1def4b69dfb34b3f).
3. Записи инструкций трёх Scheduled Tasks подтверждены ответами средства планирования.
4. В PROJECT_PLAN.json зафиксированы все три task ID, периодичность и `CONFIGURED_UNVERIFIED`; GitHub CAS + readback [commit d5fae48](https://github.com/dvikt33-ux/safe-bim-layer/commit/d5fae489368294bd2a592cf6e441c2dc133d6ca9).

## Непроверенное / частичное

- Нет проверенного цикла, в котором Scheduled Task записала `IN_PROGRESS` сама, затем сохранила проверенный отчёт и обновила задачу до `DONE_PUBLISHED` или `PARTIAL`.
- Работоспособность GitHub write в обычном чате подтверждена; в Scheduled отдельная проверка обязательна.
- E2E интеграции с publisher/receipt через Scheduled и тест одновременных CAS-claims ещё NOT_VERIFIED.

**Поэтому задача APA-P00.A03.S01 должна вернуться в PARTIAL, а не DONE_PUBLISHED.**

## Следующий измеримый шаг

Следующий запланированный запуск из трёх должен взять один допущенный `READY/PARTIAL` S-ID строго из актуального PROJECT_PLAN, записать `IN_PROGRESS` до исследования и прочитать его обратно. После выполнения — сохранить отчёт/receipt, законно завершить/частично завершить тот же S-ID и проверить контрольную запись в GitHub. После такого фактического proof можно переводить scheduler state в `RUNNING_VERIFIED` (но не объявлять непрерывные 24/7 запуски).

**Безопасность:** Только canonical research branch. Main/master, PLN, APX, рабочий исходный код не изменялись.
