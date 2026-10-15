# APA-P00.A02.S03 — аудит трёх отклонённых Slack-сообщений и дедупликация ссылок

**Этап:** APA-P00 — восстановление и централизация результатов.  
**Действие:** APA-P00.A02 — консолидация GitHub-доказательств.  
**Подзадача:** APA-P00.A02.S03 — evidence map + семантическая дедупликация.  
**Run:** APA-RUN-20261010-234200Z-slack-legacy-three-audit  
**Claim:** APA-RUN-20261010-2342Z-slack-legacy-three-audit-01; owner chatgpt-gpt6-manual-20261011-audit; registry revision at start 36.  
**Дата:** 2026-10-11 (время пользователя); GitHub canonical branch `research/apa-verified-results-hub-20261010`.  
**Фаза доказательств:** SOURCE; **статус самой подзадачи:** PARTIAL (полный разбор 72 веток не завершён).  
**Режим:** Slack read-only, GitHub REST readback, без запуска Archicad и без SQLite/Slack mutations.

## Зачем проводился разбор

Реальный локальный Slack→SQLite координатор восстановил 20 исторических событий и при повторном запуске распознал 21 дубль без новых вставок; независимое HTTP API чтение после перезапуска показало 21 событие, cursor 21, 16 состояний, smoke seq1 сохранён. [Канонический отчёт](../apa-sync-live-sqlite-history-recovery-20261011.md) и [Draft PR #33](https://github.com/dvikt33-ux/safe-bim-layer/pull/33).

Но три устаревших сообщения Slack не соответствуют строгому контракту `APA_EVENT_V1`. Не изменять парсер для чтения произвольного текста и не выдавать такие сообщения за автоматически аттестованные события.

## Карта трёх сообщений (Slack #apa-research, channel C0C886E1PGR)

Исходные номера `Message TS` ниже получены из **подключённого Slack reader**; это отображаемая через connector версия. Независимая пользовательская диагностика raw Slack API установила только суммарные формы (2 без fenced блока, 1 с одним открывающим fence), но не подтвердила индивидуальные сырые байты по каждому TS. Текст сообщений и автора в этот отчёт не копировали.

| Slack message TS | Semantic ID / фактическая проблема | Источник доказательств и S-ID | Решение по восстановлению / дедупликации |
| --- | --- | --- | --- |
| `1791666555.695829` | `apa-live-smoke-20261011-001`, `APA-SYNC-SMOKE-01`; один открывающий fence, нет закрывающего | [живой отчёт SQLite](../apa-sync-live-sqlite-history-recovery-20261011.md); задача S03 только для фиксации происхождения | **TEST_MALFORMED / SEMANTICALLY_REPLACED_BY** `apa-live-smoke-20261011-002` (seq1). Это *не* протокольное поле supersedes и не потерянное исследование. Оригинал не переписывать, не импортировать. |
| `1791629363.289809` | Свободный текст `APA_EVENT_V1 \| APA-P00.A03.S03`, без JSON/fences и event_id; дайджест publisher | [workflow](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/.github/workflows/apa-research-publisher.yml), [deployment receipt](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/deployments/APA_PUBLISHER_DEPLOYMENT_20261010.json), [V2 publication receipt](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json), [Actions 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668), [38046020069](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046020069) | **SUMMARY_DUPLICATE / SUPERSEDED_BY_CANONICAL_ARTIFACTS**, не новый research run. GitHub workflow и deployment receipt прочитаны, V2 receipt `DONE_PUBLISHED` с `readback_verified=true` подтверждён, оба Actions publish jobs SUCCESS. Только SYNTHETIC publisher E2E, не автономный исследователь 24/7. |
| `1791624243.296309` | `apa-audit-20261010-reconcile-branch-research-v1`, `APA-AUDIT-RECONCILE-01`; JSON в одинарных backticks без code fence, `phase=AUDIT` вне allowlist (`SOURCE/OFFLINE/SYNTHETIC/BUILD/LIVE`) | [PR #16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [PR #20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [PR #21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21), [Actions 37995245127](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/37995245127), [branch inventory](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md) | **HISTORICAL_REPORTED / NOT_IMPORTABLE_AS_PROTOCOL**. В GitHub проверены открытые draft PR #16/#20/#21 (не merged); Actions coordinator-unit 18/18 OFFLINE tests SUCCESS. Утверждение того сообщения `Socket Mode NOT_DEPLOYED` **SUPERSEDED** реальным LIVE запуском 2026-10-11. Прочие архивные утверждения не повышать до VERIFIED без проверки указанной исходной ревизии. |

## Source verification и границы доказательств

1. Publisher: workflow привязан к canonical GitHub push/inbox и выполняет offline tests, source/manifest/index/receipt GitHub readback. Проверены реальный `APA_PUBLISHER_DEPLOYMENT_V1`, synthetic `APA_PUBLISH_RECEIPT_V1`, Github Actions run IDs 38045964668 и 38046020069, оба success. Никакой 24/7 research runner или Archicad LIVE из этого не следует.
2. Аудиторский Slack JSON: GitHub API PR метаданные сейчас: #16 head `bcac2e8...`, #20 head `9b75c2f...`, #21 head `1a6c5e6...`, все open/draft/unmerged; тождество текущим HEAD не доказывает, что каждое утверждение старой сводки корректно. CI run 37995245127 имеет 18/18 PASS именно OFFLINE. Исторический `NOT_DEPLOYED` теперь неверен для координатора, но не для Archicad.
3. Утверждение `ни одного из 6 названий summary нет в трёх деревьях` — только **REPORTED**. В сообщении не перечислены все шесть имён, полные tree listings/проверка всех 72 веток в этом проходе не проводились. Нельзя заключать, что отчёты отсутствуют во всём GitHub или что Deep Research отчёт восстановлен.
4. Сам факт `accepted=20` в SQLite удостоверяет успешный импорт форматированных claims, а не техническую истинность SOURCE/OFFLINE/BIM findings. Три rejected события не должны автоматически становиться `PASS` при ослаблении схемы.

## Evidence map / superseded_by (строго семантически)

| Исходная сущность | canonical / superseded_by | Verified scope |
| --- | --- | --- |
| malformed smoke 001 | `apa-live-smoke-20261011-002` (seq=1) | User-local post-restart API receipt PASS; **semantic replacement only** |
| publisher narrative digest | immutable [deployment record](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/deployments/APA_PUBLISHER_DEPLOYMENT_20261010.json) + [publisher receipt](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json) | GitHub files readback, Actions jobs success; **duplicate summary** |
| historical audit about PR #16/#20/#21 | PR head metadata + canonical [branch inventory](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/FULL_BRANCH_INVENTORY.md), partial | No entire-summary supersession. Only now-obsolete `NOT_DEPLOYED` coordinator claim superseded by [live report](../apa-sync-live-sqlite-history-recovery-20261011.md). 72-branch content audit **OPEN**. |

## Acceptance и дальнейшие действия

**Сделано в этом проходе:** все 3 rejected сообщения классифицированы, найдены source GitHub links, выделены semantic duplicate/replacement vs historical unverified claims, старые события не повреждены. Результат является измеримым вкладом в `APA-P00.A02.S03`.

**Не сделано:** полная дедупликация 72 веток/22 исторических PR, локальные SHA, независимый аудит шести якобы отсутствующих файлов, автоматический импорт трёх невалидных сообщений. Поэтому **S03 не DONE_PUBLISHED**, даже если квитанция этого отчёта `DONE_PUBLISHED`.

**Следующая eligible работа в рамках существующих S-ID:** `APA-P00.A02.S03` — доказательная карта уникальных артефактов и branch ancestry для нужных исторических tree snapshots; параллельный независимый контроль receipt/commit/readback в `APA-P00.A02.S04`. Новая задача не предлагается — аналогичная работа уже зарегистрирована. Аудит трёх сообщений сам по себе не расширяет исполняемый `PROJECT_PLAN.json`.

## Безопасность

No main/master changes, PLN/APX writes, GitHub merge, Slack message edit or SQLite mutation. Original messages preserved, private Slack user/author fields and tokens intentionally omitted.
