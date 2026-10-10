# APA — расширение реестра задач через исследования и независимый аудит

**Принятое правило (2026-10-10):** *исследователь выполняет текущий S-ID и параллельно ищет, какие следующие блоки P/A/S дадут измеримый выигрыш; аудитор проверяет предложения и только после проверки добавляет одобренные задания в `PROJECT_PLAN.json`*. Аудитор может сформулировать новые задания непосредственно по результатам собственной проверки. **ChatGPT Scheduled Tasks не требуется создавать заново:** три существующих расписания читают единый план при каждом срабатывании.

## Источники и роли

- **Single source of truth:** [`PROJECT_PLAN.json`](PROJECT_PLAN.json). Только `READY/PARTIAL`, со всеми `depends_on = DONE_PUBLISHED`, без чужого claim доступны для автоматического выбора.
- **Discovery + technical:** выполнять выбранный, уже зарегистрированный S-ID; в конце отчёта добавлять *candidate tasks* с доказательствами и указанием ожидаемой пользы. Создавать **отдельные документы предложений** в `control/proposals/<proposal_id>.md` без изменения списка исполняемых задач. Не переводить кандидат в READY самостоятельно, если для этого не было независимого аудита.
- **Audit:** прочитать свежие `control/proposals/`, выбрать предложения, проверить доказательства/дубли/зависимости и записать решение в `control/reviews/<proposal_id>.md`. С проверенной и одобренной кандидатурой атомарно расширить `PROJECT_PLAN.json`; иначе указать в review `NEEDS_EVIDENCE`, `DUPLICATE`, `DEFERRED` или `REJECTED`. Может выдвигать **собственные предложения** на основании выявленных аудитором пробелов и при достаточной проверке сразу принимать их в план; в review отметить `origin=audit` и какие первоисточники проверены.
- **Owner** может самостоятельно утверждать или менять приоритеты, но это не заменяет фиксацию GitHub с readback.

## Условия предложения нового «куска работы»

Каждый завершённый исследовательский проход должен оценить, стоит ли предложить новые задачи в рамках текущего P/A или создать новый блок. **Не придумывать задачи ради количества.**

1. Что остаётся не закрытым для MVP и *почему* существующие S-ID не покрывают работу? Проверить `work_key`, `related`, результаты и активные `IN_PROGRESS`.
2. Разложить полезный блок на **одно проверяемое действие** (A) и **минимальные исполнимые подшаги** (S), с отдельным acceptance для каждого. При большом новом направлении требуется новый план P, action A и S-ID; в уже существующем направлении достаточно нового S-ID в существующем Action.
3. Указать сравнительный приоритет P0/P1/P2, зависимости `depends_on`, риски, границы (read-only или требует разрешения), потенциальное влияние на время разработки (без выдуманных цифр) и минимальный тест.
4. Предложение не считается задачей и **не появляется в очереди**, пока аудит не зарегистрировал его в `PROJECT_PLAN.json`.

### Шаблон `TASK_PROPOSAL_V1` в `control/proposals/<unique_id>.md`

```yaml
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-<date>-<unique-id>
origin: discovery | technical | audit
proposer_run_id: <executor_run_id>
source_substep_id: <existing S-ID>
proposed_parent_plan: APA-Pxx       # existing or new
proposed_action: APA-Pxx.Ayy        # existing or new
suggested_substep_id: APA-Pxx.Ayy.Szz # provisional; auditor rechecks uniqueness
work_key: <unique-semantic-key>
title: <measurable short task>
kind: RESEARCH | VALIDATION | BUILD | INTEGRATION | CONSOLIDATION | CONTROL
priority: 0 | 1 | 2
depends_on: [<S-ID>]
related: [<S-ID>]
inputs: [<ART-ID>]
outputs: [<expected artifacts>]
acceptance: <objective observable criteria>
requires_approval: false
expected_mvp_benefit: <specific qualitative saving; no invented speed>
evidence_urls: [<commit/doc/source URLs>]
risks: <limitations, SOURCE/OFFLINE/LIVE gaps>
```

Структурированный YAML-текст здесь — формат предложения для чтения человеком и аудитором; он **не является новым автоматически исполняемым контроллером**. К предложениям прилагается Markdown-пояснение, разбивка блока P/A/S, альтернативы, полезность и цена интеграции. Если предложений несколько — каждый получает собственный proposal_id и связанную группу `related`.

### Шаблон `TASK_REVIEW_V1` в `control/reviews/<proposal_id>.md`

```yaml
schema: TASK_REVIEW_V1
proposal_id: <same>
auditor_run_id: <executor_run_id>
source_substep_id: <audit S-ID>
origin: discovery | technical | audit
decision: APPROVED | NEEDS_EVIDENCE | DUPLICATE | DEFERRED | REJECTED
verified_sources: [<exact source URLs>]
overlap_checked_against: [<existing S-IDs/work_keys>]
final_task_ids: [<registered S-IDs, only for APPROVED>]
plan_commit_sha: <GitHub commit; only when real>
readback_verified: true | false
reason: <testable argument>
```

**Нельзя писать `APPROVED` при отсутствии подтверждённого CAS-коммита и readback `PROJECT_PLAN.json`.** При конфликте записи review имеет `DEFERRED` / `STATUS_WRITE_FAILED`, даже если техническая гипотеза хороша.

## Контракт аудиторского принятия в текущую очередь

1. Прочитать *свежий* `PROJECT_PLAN.json` и его blob SHA, `HANDOFF.md`, TASK_CARDS, доступные предложения и исходные исследования. Сравнить work_key/title/related для недопущения semantic duplicate; проверить, что все `depends_on` существуют и граф без циклов. Проверить `requires_approval`.
2. Уточнить, создаётся ли новый P/A или лишь S. Подтвердить уникальные ID; добавить новые записи в `plans[<P>].actions`, `tasks[<S>]` и `topics[<topic>].task_ids` (и новый `topics` при новом направлении), согласовать `inputs`/выходы. Для нового S использовать текущую контроллерную схему полей, статус `READY` (или `BLOCKED` только при документированной недоступности), `owner=null`, `lease_until=null`, `claim_ref=null`, `evidence=[]`, `blocked_reason=null` для READY.
3. Создавать `READY` можно и при неполных зависимостях — **dispatch сам не выдаёт его до DONE_PUBLISHED предпосылок**. При отсутствии проверяемых источников оставить предложением `NEEDS_EVIDENCE`, не вставлять спорную задачу в очередь.
**ВНИМАНИЕ — точная схема контроллера:** массивы `tasks[*].inputs` и `tasks[*].evidence` содержат **только идентификаторы, присутствующие в `PROJECT_PLAN.json.artifacts`**, например `ART-PROPOSAL-PROTOCOL`. Нельзя помещать в них URL, commit SHA или S-ID. Для нового доказательства сперва добавить запись `artifacts[ART-...]={id,uri,kind,verification}` с существующим GitHub-документом; прямые URL и commit SHA хранить в Markdown-отчёте/review или атрибуте `uri`. `tasks[*].related` должны быть **симметричны**: если A related B, B тоже related A. Нарушение любого правила валит все тесты controller и блокирует publisher. После каждого изменения необходимо увидеть SUCCESS шага `Project Controller DAG, claim and dispatch tests`, прежде чем считать реестр валидным.

4. Одним GitHub `update_file` по blob SHA изменить план (`revision += 1`); при `409 Conflict` перечитать текущий план, сверить, что другой исполнитель не зарегистрировал предложение, и только тогда повторить. Не перетирать чужие `IN_PROGRESS`/evidence/lease.
5. GitHub readback должен подтвердить **те же ID, work_key, depends_on, acceptance и revision**, а контрольный workflow — отсутствие схемных ошибок, дубликатов и циклов. Если валидатор не выполнился, статус принятия остаётся `VALIDATION_PENDING` в пояснении; не заявлять полностью проверенный admission.
6. Записать `TASK_REVIEW_V1` с URL коммита/источников; после этого не предлагать её как новую, а следующий ChatGPT Scheduled запуск подхватит зарегистрированный и допустимый S-ID.
7. Отчёт аудитора обязан содержать: **принятые S-ID, отклонённые предложения, ссылки, одну следующую eligible задачу**. Если найден новый пробел при аудите — создать собственный proposal и либо принять по тем же правилам, либо оставить `NEEDS_EVIDENCE`.

## Нельзя

- Не менять исполняемую очередь только на основании идеи исследователя или Slack сообщения.
- Не назначать `IN_PROGRESS` новой задаче до отдельного её claim.
- Не отменять старые задачи и не менять зависимости задним числом без объяснения/подтверждения.
- Не объявлять `DONE_PUBLISHED` по факту регистрации новой задачи: это только admission, а не её выполнение.
- Не изменять `main`, PLN, APX, протестированные рабочие ветки, устанавливать ПО или запускать платные средства.

## Статус на момент принятия протокола

Протокол и промпты Scheduled Tasks — **настроены**. Полный реальный end-to-end цикл `TASK_PROPOSAL_V1 -> независимый TASK_REVIEW_V1 -> валидированный PROJECT_PLAN.json -> следующий Scheduled claim` пока **NOT_VERIFIED**. Его тест включён в задачу `APA-P60.A02.S04` и не должен считаться DONE до подтверждения GitHub readback и валидатора.
