# APA Research OS — Split-Plane publisher и crash recovery

**ПЛАН:** APA-P00 → **ДЕЙСТВИЕ:** APA-P00.A03 → **ПОДШАГ:** APA-P00.A03.S03.  
**Статус:** PUBLISHER_DEPLOYED / SYNTHETIC_E2E_PASS; 24H_RESEARCH_RUNNER_NOT_RUNNING. [GitHub Actions run 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) success; [idempotent rerun 38046020069](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046020069) success.  
**Основание:** [переданный аудит APA Research OS](../runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md). **Обычные чаты ChatGPT с GitHub — основной исследователь и текущий publisher. Deep Research без отдельного запроса не запускать.**

## Реализованный publisher (2026-10-10)

[Workflow](../../../.github/workflows/apa-research-publisher.yml) слушает push в canonical research branch с изменениями в inbox/*.json, коде или workflow. [PUBLISH_REQUEST_V1](PUBLISH_REQUEST_V1.schema.json) содержит report_markdown, source/evidence и safety flags. [Python publisher](../../../tools/apa_publisher/publisher.py) валидирует запрос, создаёт immutable V2 run, строит [generated V2 index](../generated/INDEX.md), коммитит, сверяет SHA-256 и Git blob через REST API, коммитит [receipt](../receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json) и проверяет его через REST. Реальный [SYNTHETIC run 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) SUCCESS. Это **не** подтверждение Archicad LIVE или 24/7 research.

**Legacy индекс** пока остаётся ручным, а generated index строится только из V2 manifests. Это не полное исполнение целевого index builder. На следующий gate остаются legacy migration, watchdog/heartbeat, устойчивые retry и два отдельных SOURCE runs.

## Инварианты

1. **GitHub — единственная долговременная память APA.** ChatGPT, Slack, Deep Research и PR #21 coordinator — исполнители/транспорт, не source of truth.
2. **EVIDENCE_READY ≠ DONE_PUBLISHED.** До коммита, API readback и индексации статус не повышать.
3. Immutable run сохраняется **до** mutable index. Если индекс не обновился, run остаётся доступным.
4. Никогда не изменять main/master, PLN, установленный APX, протестированные кодовые ветки; только canonical research branch для отчётов/метаданных. Никакого force push, удаления, auto-merge или платных моделей.
5. **Capability probe на каждый запуск:** реальный write + readback. Отсутствие write в одной сессии не означает глобального запрета; при отказе — GITHUB_PUBLISH_BLOCKED.
6. RUN_EVENT_V2 — структурированный формат, а не готовый publisher. Наличие схемы **не** означает включение 24/7.

## Три контура

**Research plane:** обычный ChatGPT читает MASTER_PLAN, CURRENT_STATUS, RESEARCH_QUEUE и ARTIFACT_REGISTER; выбирает один APA-PXX.AYY.SZZ; собирает evidence и готовит отчёт. Исследование не закрывается до публикации.

**Publish plane:** валидирует [RUN_EVENT_V2.schema.json](RUN_EVENT_V2.schema.json), файлы и evidence; вычисляет idempotency; сохраняет immutable run; commit/readback; записывает receipt; перестраивает индексы; readback; возвращает проверенный receipt. Может быть вызван вручную из обычного чата сейчас; автоматический runner пока отсутствует.

**Control plane:** Issue #23 + CURRENT_STATUS + MASTER_PLAN + очередь + реестр. Проекции могут быть восстановлены из immutable runs/receipts; **существующие Markdown остаются редактируемыми вручную до отдельного gate, когда генератор протестирован**.

## V2 layout и commit boundary

Новые V2 runs публиковать в:

    docs/research/apa-results/runs/YYYY-MM-DD/APA-RUN-YYYYMMDD-HHMMSSZ-slug/
      REPORT.md
      manifest.json           # RUN_EVENT_V2 (immutable)
      evidence.json           # индекс доказательств, без секретов

После первого коммита и readback — отдельный receipt в:

    docs/research/apa-results/receipts/APA-RUN-...json

Receipt должен содержать: run_id, report_path, report_commit_sha, report_blob_sha, report_sha256 (если вычислен), readback_verified, index_commit_sha (может быть null), indexed, status, checked_at, executor, failures. **Нельзя встраивать SHA самого коммита в файлы того же коммита:** это циклическая зависимость. Receipt пишется после первого коммита; его собственный SHA хранится во внешнем указателе или в ответе.

Существующие flat Markdown в runs/YYYY-MM-DD/ **не переписывать и не удалять**; index builder обязан поддерживать legacy файлы и V2. Дедупликация — по evidence fingerprint и run_id, а не по похожему имени файла.

## Детерминированный алгоритм публикации

1. Проверить, что P/A/S-ID существуют в MASTER_PLAN, а phase и evidence status не завышены.
2. Валидировать RUN_EVENT_V2 по JSON Schema 2020-12. Отвергать path traversal, внешние абсолютные пути, secrets и неразрешённые файлы.
3. Рассчитать idempotency_key = SHA-256 от canonical JSON tuple: substep_id + sorted source revisions + sorted evidence fingerprints + executor_run_id. Уникальный executor_run_id не заменяет проверку evidence: для дедупликации выводов использовать отдельно evidence fingerprint без executor ID.
4. Найти существующий run по run_id/idempotency; при совпадении содержимого вернуть существующий receipt, при конфликте зафиксировать CONFLICT и не перезаписывать immutable run.
5. Создать REPORT.md + manifest.json + evidence.json в новом V2 run directory **одним git tree/commit**, если это поддерживает write tool. Если инструмент умеет только последовательные create_file, статус остаётся PUBLISHING, пока все файлы не проверены; не считать частичную запись атомарной.
6. Зафиксировать commit SHA и выполнить GitHub readback каждого файла. Сравнить bytes/content hash и Git blob SHA; SHA-256 вычислять над UTF-8 bytes с одинаковой нормализацией переводов строк.
7. Только после readback сохранить отдельный receipt с COMMITTED/READBACK_VERIFIED.
8. Пересобрать производные индексы из immutable records/receipts. Сохранить отдельным коммитом, выполнить readback и проверить непротиворечивость CURRENT_STATUS/QUEUE/REGISTER.
9. Зафиксировать INDEXED/DONE_PUBLISHED в новом receipt/event, **не редактируя исходный immutable run**.
10. Отправить Slack APA_EVENT только после GitHub readback; invalid events должны диагностироваться явно, не silently dropped.

## Сбой и восстановление

| Сбой | Источник истины | Действие |
| --- | --- | --- |
| Исследование завершилось, но нет commit | EVIDENCE_READY, не опубликовано | GITHUB_PUBLISH_BLOCKED; сохранить доступный полный Markdown; не обещать восстановление UI |
| Частичная запись файлов до общего commit | PUBLISHING | проверить каждый path/SHA; дополнить недостающее, не плодить новый run |
| Commit есть, readback не прошёл | COMMITTED | повторить readback, сравнить хеши, PUBLISH_READBACK_FAILED при расхождении |
| Readback есть, index не обновился | READBACK_VERIFIED | сканировать unindexed receipts, перестроить проекции без повторного исследования |
| Индекс обновился, receipt не подтвердил | INDEX_PENDING | сравнить commit SHA и фактическое содержимое, завершить только после readback |
| Существуют два run с одинаковым evidence fingerprint | CONFLICT / DUPLICATE | связать supersedes, сохранить оба immutable, не удалять |
| Runner остановился | RUNNER_OFFLINE | heartbeat + явное сообщение, без ложного DONE |

## Реальный gate внедрения

- **Gate 0 (DONE):** документы, схема, снимок веток, публикация вручную через обычный ChatGPT + GitHub readback.
- **Gate 1 (PARTIAL_PASS):** [push-triggered workflow](../../../.github/workflows/apa-research-publisher.yml), [stdlib publisher](../../../tools/apa_publisher/publisher.py), [6 offline tests](../../../tools/apa_publisher/tests/test_publisher.py), автоматические immutable runs + generated V2 index + GitHub REST readback + receipt; SYNTHETIC E2E PASS [38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668). Реальные outage/retry, legacy index migration и security hardening ещё NOT_VERIFIED.
- **Gate 2 (PARTIAL):** один полный SYNTHETIC E2E цикл + успешный идемпотентный повтор; два независимых SOURCE research cycles пока NOT_VERIFIED.
- **Gate 3:** разрешённый unattended runner, реальный GitHub write без зависания на approval, heartbeat и watchdog; только после 24 часов наблюдения — 24H_VERIFIED.

**Нельзя утверждать:** что JSON Schema — это работающий сервис; что Scheduled Tasks имеют unattended write; что PR #21 уже развёрнут; что старые ветки полностью классифицированы; что пропавший ответ восстановлен, если опубликована только другая работа.
