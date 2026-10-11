# APA — что делается сейчас

**Дата контрольного среза:** 2026-10-10. **Каноническая ветка:** [research/apa-verified-results-hub-20261010](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results).

## Текущая лестница

**ПЛАН:** [APA-P00 — Восстановление и централизация](MASTER_PLAN.md#apa-p00--восстановление-и-централизация-накопленных-материалов)

↳ **ДЕЙСТВИЕ:** APA-P00.A01 — Инвентаризация фактически опубликованного

↳ ↳ **ТЕКУЩИЙ ПОДШАГ:** **APA-P00.A01.S03 — Продолжить forensic inventory 72 веток (ancestry/unique artifacts/PR mapping)**

- Обычный чат с GitHub connector: **PASS** — несколько Markdown записаны и прочитаны обратно.
- Deep Research → GitHub: **NOT_VERIFIED / НЕ НАСТРОЕНО** — вывод в отдельном виджете не является GitHub commit.
- Постоянный планировщик / runner: **NOT_RUNNING**.
- Следующий подшаг после S01: APA-P00.A03.S02 — выбрать разрешённый always-on исполнитель без платных API и без изменений main.

## Режим, подтверждённый владельцем

**Исследования — в обычных чатах ChatGPT с GitHub connector и публикацией в canonical hub; Deep Research без отдельного запроса НЕ ЗАПУСКАТЬ.** Это выбранный способ исполнения, а не утверждение, что 24/7 runner работает. Проверка расписания и двух последовательных публикаций остаётся открытой; статус 24/7 **NOT_RUNNING**.

**Частичная техническая дельта APA-P10.A01.S01:** [AC29 Get3DInfo/contacts/Opening](runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md) сохранена, commit [d65c5bd](https://github.com/dvikt33-ux/safe-bim-layer/commit/d65c5bd327d077d7873ff720cda6dac3bf8a22cb), readback подтверждён. В официальной документации встречаются оба имени `ACAPI_Element_Get3DInfo` и `ACAPI_ModelAccess_Get3DInfo`; нельзя переименовывать код без SDK header/compile gate. Полный прежний Deep Research отчёт **не восстановлен**.

## Автоматический publisher — DEPLOYED / SYNTHETIC_E2E_PASS (2026-10-10)

**Проверено:** [GitHub Actions run 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) — success; 6 offline tests, автоматический report+manifest+evidence, [generated index](generated/INDEX.md), GitHub REST SHA-256/blob readback, [automatic DONE_PUBLISHED receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json). Повторный запуск [38046020069](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046020069) завершился success без нового коммита (idempotent no-op). [Workflow](../../../.github/workflows/apa-research-publisher.yml), [publisher source](../../../tools/apa_publisher/publisher.py), [операторская инструкция](../../../tools/apa_publisher/README.md), [PUBLISH_REQUEST_V1](protocol/PUBLISH_REQUEST_V1.schema.json).

**Граница:** это автоматический **push-triggered GitHub publisher**, а не автономный исследователь ChatGPT; 24/7 research scheduler/heartbeat **NOT_RUNNING**. Тест SYNTHETIC, не Archicad LIVE/BUILD. Legacy manual индексы пока обновляются отдельно.

## APA Research OS — результат публикации переданного аудита

**Опубликовано и прочитано обратно:** [содержательно полная версия аудита](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md), commit [9b07679](https://github.com/dvikt33-ux/safe-bim-layer/commit/9b076792124d99d67dcc0f01554b4834fc3ed8cb); [readback receipt](receipts/APA-RUN-20261010-102800Z-research-os-audit-readback.json). Это **другой** документ, не прежний пропавший полный AC29 Deep Research отчёт.

**APA-P00.A01.S03 частично выполнен:** [снимок всех 72 веток с SHA и PR](inventories/FULL_BRANCH_INVENTORY.md) + [JSON](inventories/BRANCH_HEADS_20261010.json) опубликованы; ancestry, уникальные артефакты, superseded_by и локальные SHA остаются NOT_VERIFIED. Ни одна ветка не удалена.

**APA-P00.A03.S03 — PUBLISHER_DEPLOYED / SYNTHETIC_E2E_PASS:** [RUN_EVENT_V2.schema.json](protocol/RUN_EVENT_V2.schema.json), [publisher source](../../../tools/apa_publisher/publisher.py), [workflow](../../../.github/workflows/apa-research-publisher.yml), [generated V2 index](generated/INDEX.md), [receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json). GitHub Actions [38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) success; 6 offline tests + report/index/receipt API readback. **Publisher работает на push inbox, но scheduler/heartbeat/24h runner NOT_RUNNING.** Ручные legacy индексы ещё не переведены на generated projections.

**Исполнитель:** обычный ChatGPT + GitHub write/readback подтверждён в этой сессии. Deep Research не запускался и без отдельного разрешения запускаться не должен. Права Scheduled Tasks на unattended GitHub write — NOT_VERIFIED.

## Что завершено и где доказательства

- **APA-P00.A01.S01:** прочитаны 5 существовавших файлов research hub; [реестр](ARTIFACT_REGISTER.md).
- **APA-P00.A01.S02:** обнаружены и прочитаны 3 архивных документа/индекса; [реестр](ARTIFACT_REGISTER.md).
- **APA-P00.A02.S01:** зафиксирована каноническая ветка, новые research-ветки не создавать.
- **APA-P00.A02.S02:** опубликованы операционные документы [MASTER_PLAN](MASTER_PLAN.md), [BRANCH_REGISTRY](BRANCH_REGISTRY.md), [RESEARCH_TEMPLATE](RESEARCH_TEMPLATE.md), [AGENT_PROTOCOL](AGENT_PROTOCOL.md), [AUTOMATION_AND_GATES](AUTOMATION_AND_GATES.md), [RESEARCH_QUEUE](RESEARCH_QUEUE.md) и этот статус. Проверка readback — отдельные подтверждения GitHub API.

## Следующие действия без потери контекста

1. **APA-P00.A01.S03:** полная инвентаризация старых веток/коммитов, сопоставление дублей и пустых/отсутствующих документов.
2. **APA-P00.A02.S03:** связать старые находки с задачами P10/P20, пометить verified/reported/unknown.
3. **APA-P10.A01.S01:** первичный аудит SDK Archicad 29 с точными сигнатурами и ссылками.
4. **APA-P00.A03.S02:** решить, какой реально работающий исполнитель может запускаться 24/7 и публиковать.

## Нельзя считать выполненным

- Прежний полный технический AC29 Deep Research отчёт и шесть обещанных файлов: **НЕ ОПУБЛИКОВАНЫ**. Отдельный предоставленный владельцем аудит APA Research OS **ОПУБЛИКОВАН**.
- Непрерывное исследование и автоматическая публикация: **НЕ ЗАПУЩЕНЫ**.
- Автоматическая синхронизация всех чатов: **НЕ ПОДТВЕРЖДЕНА**.
- Изменения main/PLN/APX и merge: **НЕ ПРОВОДИЛИСЬ**.

**Правило:** если исполнитель не может прочитать и записать этот файл в GitHub, он обязан явно сообщить GITHUB_PUBLISH_BLOCKED и дать готовый Markdown, а не просить владельца искать результаты по чатам.


## Проверенное восстановление трёх неопубликованных отчётов (2026-10-10)

**APA-P00 / APA-P00.A02 / APA-P00.A02.S03 — частичный результат:** в канонической ветке сохранены и прочитаны обратно три `RECOVERED_FROM_CHAT` Markdown-файла (Tapir docs; Native Hotlink/MEP Transition; IfcMCP/IfcPatch). Зафиксированы три отдельных commit SHA и readback, [реестр](ARTIFACT_REGISTER.md#восстановленные-из-чата-результаты-2026-10-10) обновлён, commit [69c327f](https://github.com/dvikt33-ux/safe-bim-layer/commit/69c327f0f2897bc85ce4a3dce44605e1abe21757), readback PASS. [Slack APA_EVENT_V1](https://w1791579305-0gy426514.slack.com/archives/C0C886E1PGR/p1791639564779389) отправлен. **Ограничение:** это восстановление ранее изложенных выводов (`REPORTED_FROM_PRIOR_CHAT`), а не новый независимый source audit или LIVE PASS. Полный системный P00.A02.S03 пока PARTIAL: дедупликация всех исторических веток и источников не закончена. `main`, PLN, APX не изменялись.


## APA Slack Sync — восстановленная история, локальный HTTP-readback PASS (2026-10-11)

**Новый подтверждённый результат:** в checkout `feature/apa-sync-slack-envelope-evidence-recovery-20261011`, [PR #33](https://github.com/dvikt33-ux/safe-bim-layer/pull/33) (44/44 offline tests PASS), пользователь запустил координирующий Socket Mode и получил в 02:24 **20 accepted, 1 duplicate, 0 conflicts, 3 malformed rejects** из 28 сообщений Slack. Дополнительно отдельный PowerShell через локальный API проверил **21 событие, cursor=21, сохранность исходного seq1, 16 task-phase states, 0 effective conflicts**. [Полный отчёт](runs/2026-10-11/apa-sync-live-sqlite-history-recovery-20261011.md), [ARTIFACT_REGISTER](ARTIFACT_REGISTER.md#apa-p00a02s03--s04--slack-historical-sqlite-recovery-and-http-readback-2026-10-11).

**Границы:** транспорт+исторический импорт+API readback = LIVE_PASS. Но ни 4 `OFFLINE PASS`, ни 13 `SOURCE INFO` не означают Archicad BUILD/LIVE PASS; `APA-SYNC-LIVE-01` по-прежнему `LIVE BLOCKED`. **Повторный чистый рестарт 02:33 подтвердил LIVE_PASS идемпотентности: 0 accepted, 21 duplicates, 0 conflicts, 3 malformed rejects.** **Независимый HTTP-readback после повторного рестарта LIVE_PASS:** 21 событие, курсор 21, 16 состояний, исходное событие seq=1 сохранилось. Три malformed сообщения — отдельный аудит с источниками. Автоматическая синхронизация всех чатов и исследовательский runner 24/7 не доказаны. Контроллер `PROJECT_PLAN.json` не менялся: существующие задачи `APA-P00.A02.S03` и `APA-P00.A02.S04` продолжают требовать provenance/publishing audit, и никто не объявляет их DONE по Slack-логу.

## APA-P00.A02.S03 — source-backed audit of three malformed Slack records (2026-10-11)

**РЕЕСТР ЗАДАЧ:** `PROJECT_PLAN.json` revision **37**, task `APA-P00.A02.S03` now **PARTIAL**, execution claim `APA-RUN-20261010-2342Z-slack-legacy-three-audit-01` released (owner/lease/claim_ref cleared). Verified V2 evidence artifact: `ART-APA-SLACK-THREE-RECON-20261011`. This is a partial result within the existing task, NOT full 72-branch dedup completion.

**ПУБЛИКАЦИЯ:** immutable [V2 source reconciliation report](runs/2026-10-10/APA-RUN-20261010-234200Z-slack-legacy-three-audit/REPORT.md) and [publication receipt](receipts/APA-RUN-20261010-234200Z-slack-legacy-three-audit.json) **DONE_PUBLISHED / readback_verified=true / indexed=true**; [artifact register](ARTIFACT_REGISTER.md#apa-p00a02s03--три-отклонённых-slack-сообщения-source-reconciliation-2026-10-11) updated. This receipt attests to report persistence, **not** task completion or native Archicad behavior.

**АУДИТ:** three rejected Slack items structurally categorized and cross-referenced: (1) malformed smoke `...-001` semantically replaced by seq1 `...-002`; (2) unfenced publisher announcement duplicates validated workflow/deployment/V2 receipt rather than an unpublished research artifact; (3) unfenced historical auditor JSON uses unsupported `phase=AUDIT`, cites draft PR #16/#20/#21 and prior coordinator 18/18 offline test, but its `NOT_DEPLOYED` claim was superseded by the current LIVE Socket Mode proof. This third message does **not** prove that the six unnamed summary files are globally absent; full source tree / 72-branch reconciliation remains OPEN.

**NEXT:** continue existing `APA-P00.A02.S03` to produce a complete unique-artifact and `superseded_by` map for the remaining branch inventory; independent publication controls remain `APA-P00.A02.S04`. No new duplicate S-ID admitted, main/master/PLN/APX untouched. Slack parser and existing SQLite unchanged.

## APA-P00.A02.S03 — 72 ветки, HEAD alias map и 13 сравнений ancestry (2026-10-11)

**Пройден дополнительный SOURCE проход в обычном GPT-6 чате.** Пользовательский реестр `PROJECT_PLAN.json` содержит partial-результат `APA-P00.A02.S03`: назначение `IN_PROGRESS` было зафиксировано GitHub CAS до исследования, результаты отправлены через publisher и после readback контроллер обновлён до **PARTIAL** с очищенными owner/claim/lease. Отдельная квитанция V2 этого отчёта **DONE_PUBLISHED** (`readback_verified=true`, `indexed=true`); это не статус полного завершения task.

**Факт:** [72-branch / 13-pair machine matrix](inventories/BRANCH_DEDUP_MATRIX_20261011.json) сохранена (commit `df6c8c98`, readback PASS). На snapshot 72 ветки / 69 разных HEAD SHA / 2 exact alias groups (в сумме 5 имён), и при 13 прямых GitHub compare — 3 identical / 8 ahead / 2 diverged. [V2 report](runs/2026-10-10/APA-RUN-20261010-235301Z-branch-evidence-dedup/REPORT.md) + [receipt](receipts/APA-RUN-20261010-235301Z-branch-evidence-dedup.json) сохранены и проверены; [ARTIFACT_REGISTER](ARTIFACT_REGISTER.md) содержит `ART-APA-BRANCH-DEDUP-20261011`.

**Не уничтожать неповторяющиеся результаты:** `work/stage5-hosted-window` — потомок Stage4 Performance (19 путей отличаются) и его W08-W10 LIVE проверки остаются PENDING; GDL/TN native-probe дополняет checkpoint патчем read-only resolver, а установленный APX и 92 ошибки не закрыты; два независимых семейства `detail-machine-v2.3` и `detail-machine-db-v2.3-20261006` разошлись по истории и содержат разные исходные коллекции KAIMAN и ROCKFACADE. Исторические benchmark и detail coverage не запускались заново и остаются `REPORTED`.

**Следующий измеримый шаг:** в рамках существующего `APA-P00.A02.S03` совместно с `APA-P00.A01.S03` просканировать **уникальные git blob paths** оставшихся HEAD деревьев, отнести оригинальные артефакты к S-ID, отделить повторяемые (identical blob SHA) от схожих по названию, но разных по содержанию. 72×72 попарный перебор без необходимости не выполнять. Заявление об отсутствии шести исторических summary файлов без списка точных имён и exhaustive tree search по-прежнему `NOT_VERIFIED`. `main`, PLN, APX и установленные компоненты Archicad не менялись.

## APA-P00.A02.S03 — Git blobs, 83 branches / 80 heads (2026-10-11)

**Измеримое новое состояние:** все **83 текущих Git branch references** (снимок `CURRENT_BRANCH_HEADS_20261011.json`) сведены к **80 уникальным HEAD**. Все 80 Git trees прочитаны через REST `recursive=1`, `truncated=false`, **0 failures**. Сохранён 9-батчевый byte-level файл-реестр в [blob-scan-20261011](inventories/blob-scan-20261011/CURRENT_BLOB_AGGREGATE_20261011.json): **14 920** file occurrences → **1 578** blob SHA, **1 594** paths, **1 748** path+SHA pairs; **422** SHA встречаются только в одном HEAD, **44** одинаковых blob SHA имеют разные пути, **91** путь представлен разными содержимыми.

**Публикация SOURCE:** [immutable V2 REPORT](runs/2026-10-11/APA-RUN-20261011-001922Z-eighty-head-blob-inventory/REPORT.md), [receipt](receipts/APA-RUN-20261011-001922Z-eighty-head-blob-inventory.json) `DONE_PUBLISHED`, `readback_verified=true`, `indexed=true`. Отчёт сверён с inbox byte-content и занесён в [ARTIFACT_REGISTER](ARTIFACT_REGISTER.md) под `ART-APA-BLOB-CENSUS-83-20261011`. В реестре имеются absolute links, исправляющие неверные relative машинные ссылки внутри immutable report без переписывания receipt-verified bytes.

**71 исходный документ:** ветка `research/archicad29-tapir159-expansion` содержит 71 MD/JSON blob SHA, эксклюзивных среди 80 HEAD; все 71 **не совпали byte-for-byte** с одним pinned canonical SHA. [71-link source index](inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json) с SHA/permalink — PASS; **сами 71 файла не скопированы** в canonical, попытка atomic write была заблокирована и не изменяла ref. Статус `SOURCE_LINKS_VERIFIED_NOT_COPIED`. [TASK_PROPOSAL_V1](control/proposals/APA-CAND-20261011-source-archive-71.md) создан для независимого аудита: либо новое S-ID, либо включение в существующую S03, не назначать новый substep без review.

**Крупные содержательные находки:** в старом source корпусе изучены архитектуры deterministic recipe compiler/Project Profile, project stamp/context snapshot, local transport, Safe BIM guarded writer, backlog пробных native API. Это **исторический research под Tapir 1.5.9**, не заново принятый CURRENT Tapir 1.5.10 и не Archicad LIVE PASS. У текущей `feature/apa-highlevel-whole-model-20261011` есть 10 distinct exclusive source SHA и заявленные в branch документации offline/synthetic gate; LIVE test house не объявлять завершённым на основании этого исследования.

**Task controller:** `APA-P00.A02.S03` = **PARTIAL**, claim завершён, артефакты `ART-APA-BLOB-CENSUS-83-20261011` и `ART-APA-SOURCE-71-INDEX-20261011` добавлены к evidence через CAS/readback, `PROJECT_PLAN.json` revision 44. Это не task DONE. **Следующий measured pass:** семантическая review 422 SHA по 80 HEAD, приоритет 71 архивных text sources + 10 новых highlevel files; независимый review на перенос source bytes. `main`, PLN, APX, SQLite без изменений.

## APA-P00.A02.S03 — 71 исходных файлов сохранены byte-exact (2026-10-11)

**Статус источника скорректирован:** запись выше со статусом `SOURCE_LINKS_VERIFIED_NOT_COPIED` описывала **предыдущий** неудавшийся перенос. После отдельного CAS-claim и независимой source-tree проверки перенос **состоялся**, а именно:

- Исходный pinned commit: `c651035ddc77869fbc5a04bf23170b4f1188a9ab`, архивный [commit `477ba54a`](https://github.com/dvikt33-ux/safe-bim-layer/commit/477ba54a0620ce7c0efc1b835f1d0ad2f1a03ba5), `force=false`; ровно **71 оригинальный Markdown/JSON Git blob**, суммарно 487455 байт, помещены в [канонический source-архив](source-archives/archicad29-tapir159-expansion-c651035d/ARCHIVE_GUIDE_20261011.md) одним commit. Источники не переписаны.
- Прямой Git REST `recursive=1` readback по архивному commit: `sha&size` совпали **71/71**, zero mismatches, `truncated=false`. [Манифест](source-archives/archicad29-tapir159-expansion-c651035d/ARCHIVE_MANIFEST_20261011.json) связывает `source_path→archived_path→blob_sha→S-ID`.
- [Immutable V2 report](runs/2026-10-11/APA-RUN-20261011-092155Z-source71-byte-archive/REPORT.md) + [receipt](receipts/APA-RUN-20261011-092155Z-source71-byte-archive.json): **DONE_PUBLISHED / indexed=true / readback_verified=true**, прямой readback `REPORT.md` совпал с `inbox` содержимым. В [реестре](ARTIFACT_REGISTER.md) зарегистрирован `ART-APA-SOURCE-71-BYTE-EXACT-20261011`.
- [TASK_REVIEW_V1](control/reviews/APA-CAND-20261011-source-archive-71.md): proposal `APA-CAND-20261011-source-archive-71` получил `DUPLICATE`, поскольку отдельная `S05` повторила бы сохранение оригиналов в существующей `APA-P00.A02.S03`; новый S-ID **не вставлялся**. Контроллер: `PROJECT_PLAN.json` revision **48**, `APA-P00.A02.S03=PARTIAL`, `owner/claim_ref/lease_until=null`, evidence включает новый архивный artifact ID. Проверка JSON/readback PASS.
- Содержательная выборка 13 исходных документов: native single-element Gable Roof, Composite Attributes, GDL, Project Profile, context-state/transport; сопоставление с текущим `scripts/archicad_building_shell.py` выявило ограничение `CreateWalls/Slabs/Doors/Windows`. Это **source-gap**, а не работающий Roof или подтверждённое current Tapir. Технические выводы остальных 58 файлов остаются только архивированными, не independently reviewed.
- Важная граница: исторический исследовательский Tapir **1.5.9** не подменяет актуальный Tapir **1.5.10** и installed APX; никакой Archicad LIVE-бинарной или PLN-проверки не проводилось. Исходная ветка, `main`, модель, локальный daemon, SQLite, APX не изменялись.
- **Оставшаяся работа S03:** semantic `superseded_by` карта архивных решений к современным артефактам/контрактам, затем независимый аудит SDK и live acceptance по существующим S-ID. Не открывать снова задачу на physical source archival.
- **CI caveat:** [workflow 38128175054](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38128175054) SUCCESS после восстановления V2; более поздний [38128227619](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38128227619) FAIL по тесту контроллера `development.done (expected 0, got 1)`; это самостоятельная проверка состояния тестов, не ошибка source byte preservation. Последующая CI по ревизии плана требует отдельной оценки, не заявляется автоматически зелёной.



## CI reconciliation after 71-file archival controller update (2026-10-11)

**Последующая независимая проверка закрыла прежний CI warning.** [GitHub Actions #38128367467](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38128367467) на точном коммите контроллера `6f14dccaa0ffb947ac54b590f529ebbf26960f8e` завершился **SUCCESS**. Отдельно по job logs: `Project Controller DAG, claim and dispatch tests` SUCCESS, `Validate canonical project plan and reject orphan/unclaimed inbox` SUCCESS, `Prepare immutable run files and generated projections` SUCCESS, `Commit report and index projection` SUCCESS, `Verify controller projections via GitHub REST` SUCCESS. На этом прогоне подтверждено независимое `READBACK_VERIFIED` для `APA-RUN-20261011-092155Z-source71-byte-archive` receipt и `APA_CONTROLLER_READBACK_VERIFIED` для generated board/state. **Предыдущий fail #38128227619 является историческим и не текущей блокировкой этого controller commit.** Это не означает доступность Archicad LIVE.

## APA-P70.A03.S02 — Archicad test-building 25/25 live scene PASS (2026-10-11)

**Новое подтверждение владельцем:** отдельный локальный одноразовый PLN `C:\\LocalAI\\APA_Test_House_01.pln`, Archicad 29 / Tapir 1.5.10, native port 19726. После строгого read-only preflight (13 существующих/12 недостающих, zero writes) выполнено отдельное разрешённое создание: `COMPLETE_UNSAVED`, `reusedCount=13`, `newCreatedCount=12`, `allGuidsReadback=true`, `failedStep=null`. В итоге **25/25 BIM элементов тестового двухэтажного shell** прошли проверки текущей сессии; 20 исходных элементов дают ожидаемый итог 45. Повторное создание GUID при восстановлении после прежних тайм-аутов не проводилось. [Детальный отчёт](runs/2026-10-11/apa-p70-a03-s02-pr35-basic-slab-implementation-partial-20261011.md), [реестр артефакта](ARTIFACT_REGISTER.md#apa-p70a03s02--live-2525-building-shell-acceptance-unsaved-2026-10-11).

**Граница:** `REPORTED_LIVE_TYPED_READBACK_PASS_UNSAVED`, а НЕ `SAVE_REOPEN_PASS`. Сохранённая копия, независимый reopen, 45 GUID и визуально-конструктивная корректность пока `NOT_VERIFIED`. Контроллер `PROJECT_PLAN.json` task `APA-P70.A03.S02` не переводился в DONE: он шире этого теста и связан с upstream семантикой. Следующий безопасный gate — **Save As в новый тестовый путь → reopen копии → read-only пересчёт 45 GUID и повторный typed scan 25 плановых элементов**, без повторного запуска любого ранее зарезервированного suffix и без изменений main/APX.
