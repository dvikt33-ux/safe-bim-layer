# APA Project Controller — единый центр управления

**Реальный статус:** GitHub Actions [38046610758](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046610758) SUCCESS; 6 publisher + 10 controller offline tests, generated views и GitHub REST readback. Это управляющий реестр/диспетчер, **не** автономный ChatGPT-агент 24/7.

## Один источник поручений

[PROJECT_PLAN.json](PROJECT_PLAN.json) — единственный авторитетный машиночитаемый план. Его статусы и зависимости важнее устаревших ручных MASTER_PLAN, CURRENT_STATUS и RESEARCH_QUEUE.

Автоматически создаются [CONTROL_BOARD](generated/CONTROL_BOARD.md), [TASK_CARDS](generated/TASK_CARDS.md), [RELATIONSHIPS](generated/RELATIONSHIPS.md), [HANDOFF](generated/HANDOFF.md), [STATE.json](generated/STATE.json).

Каждый чат читает HANDOFF → CONTROL_BOARD → TASK_CARDS, выбирает один S-ID из плана, изучает существующие входы и related задачи. Новая тема сначала сопоставляется с планом; при отсутствии подходящего S-ID добавляется новая задача с уникальным work_key, depends_on, inputs и acceptance. Нельзя начинать незарегистрированную работу.

## Параллельные направления

Из одного плана формируются очереди RESEARCH, BUILD, INTEGRATION, CONSOLIDATION, VALIDATION и CONTROL. Задачи READY/PARTIAL выдаются только если зависимости DONE_PUBLISHED. Занятые, завершённые и блокированные не выдаются.

## ChatGPT Scheduled → IN_PROGRESS → результат → DONE/PARTIAL

**Инициатор — только пользовательская задача в ChatGPT Scheduled**, не GitHub controller. [Готовая инструкция для Scheduled Task](CHATGPT_SCHEDULED_TASK.md) содержит полный текст запуска, проверку GitHub и безопасный сценарий. Пока в `PROJECT_PLAN.json.scheduler` указано `NOT_CONFIGURED`: расписание в аккаунте ChatGPT ещё не создано.

1. ChatGPT Scheduled запускает исполнителя. Он читает актуальный PROJECT_PLAN.json и выбирает один READY/PARTIAL S-ID, у которого завершены зависимости.
2. **Сразу до любой работы** записывает через GitHub CAS `status=IN_PROGRESS`, `owner`, `lease_until`, `claim_ref=executor_run_id`; затем повторно читает GitHub. Если запись не удалась — работу не начинает.
3. Исполняет только выбранный S-ID, не повторяет занятые и завершённые задачи.
4. Публикует PUBLISH_REQUEST_V1 с matching `substep_id`, `executor`, `executor_run_id`. Publisher отвергает запрос, если статус не IN_PROGRESS, ID исполнителя не совпадает, аренда истекла или зависимости не завершены.
5. После успешной публикации, GitHub readback и acceptance переводит S-ID в DONE_PUBLISHED с evidence. Если результат частичный — PARTIAL с evidence, если ошибка — BLOCKED с blocked_reason. Во всех случаях освобождает owner/lease/claim_ref, проверяет запись GitHub.
6. Следующий Scheduled запуск или другой чат читает уже новый статус; `DONE_PUBLISHED` не выдаётся повторно.

Истёкшая аренда подсвечивается, но не присваивается другому исполнителю автоматически. **Receipt DONE_PUBLISHED относится к публикации отчёта, не обязательно к завершению S-ID.** При недоступности GitHub write исполнитель останавливается, а не выполняет незарегистрированную работу.

## Изменение структуры и пределы

Структура расширяется по P → A → S; существующие ID не переиспользуются. PROJECT_PLAN.json изменяется в canonical research branch; workflow проверяет DAG, уникальность work_key, claims, inbox и строит views.

Immutable V2 runs и receipts связываются автоматически. Исторические flat-отчёты и 72 ветки пока **не полностью сопоставлены**; задача APA-P50.A01.S01 открыта. Семантическая дедупликация не объявляется завершённой.

**Безопасность:** main/master, PLN, APX и протестированные ветки не меняются; merge, платные инструменты и Deep Research без отдельного разрешения не запускаются. ChatGPT Scheduled Task NOT_CONFIGURED; автономное выполнение и 24/7 NOT_VERIFIED.
