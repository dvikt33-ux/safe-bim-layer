# APA Project Controller — единый центр управления

**Реальный статус:** GitHub Actions [38046610758](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046610758) SUCCESS; 6 publisher + 10 controller offline tests, generated views и GitHub REST readback. Это управляющий реестр/диспетчер, **не** автономный ChatGPT-агент 24/7.

## Один источник поручений

[PROJECT_PLAN.json](PROJECT_PLAN.json) — единственный авторитетный машиночитаемый план. Его статусы и зависимости важнее устаревших ручных MASTER_PLAN, CURRENT_STATUS и RESEARCH_QUEUE.

Автоматически создаются [CONTROL_BOARD](generated/CONTROL_BOARD.md), [TASK_CARDS](generated/TASK_CARDS.md), [RELATIONSHIPS](generated/RELATIONSHIPS.md), [HANDOFF](generated/HANDOFF.md), [STATE.json](generated/STATE.json).

Каждый чат читает HANDOFF → CONTROL_BOARD → TASK_CARDS, выбирает один S-ID из плана, изучает существующие входы и related задачи. Новая тема сначала сопоставляется с планом; при отсутствии подходящего S-ID добавляется новая задача с уникальным work_key, depends_on, inputs и acceptance. Нельзя начинать незарегистрированную работу.

## Параллельные направления

Из одного плана формируются очереди RESEARCH, BUILD, INTEGRATION, CONSOLIDATION, VALIDATION и CONTROL. Задачи READY/PARTIAL выдаются только если зависимости DONE_PUBLISHED. Занятые, завершённые и блокированные не выдаются.

## Claim → работа → публикация → завершение

1. Прочитать текущий blob SHA PROJECT_PLAN.json через GitHub.
2. Изменить только свою задачу: status=CLAIMED, owner=уникальный executor, lease_until=UTC timestamp, claim_ref=ссылка на работу.
3. Записать через GitHub update_file с ожидаемым blob SHA. При конфликте — перечитать план, не перезаписывать чужой claim.
4. Выполнить только scope задачи, не повторяя связанные исследования.
5. Опубликовать PUBLISH_REQUEST_V1 в inbox с matching substep_id и executor=owner. Контроллер блокирует новые запросы без claim или с неизвестным S-ID.
6. Дождаться успешного workflow, GitHub readback и DONE_PUBLISHED receipt. Проверить acceptance; затем отметить DONE_PUBLISHED, освободить claim, сохранить ссылки. Для BUILD — code commit + CI PASS + readback и evidence.

Истёкшая аренда подсвечивается, но не присваивается другому исполнителю автоматически.

## Изменение структуры и пределы

Структура расширяется по P → A → S; существующие ID не переиспользуются. PROJECT_PLAN.json изменяется в canonical research branch; workflow проверяет DAG, уникальность work_key, claims, inbox и строит views.

Immutable V2 runs и receipts связываются автоматически. Исторические flat-отчёты и 72 ветки пока **не полностью сопоставлены**; задача APA-P50.A01.S01 открыта. Семантическая дедупликация не объявляется завершённой.

**Безопасность:** main/master, PLN, APX и протестированные ветки не меняются; merge, платные инструменты и Deep Research без отдельного разрешения не запускаются. Автономный 24/7 исследователь NOT_RUNNING.
