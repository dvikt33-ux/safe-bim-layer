# APA-P00.A02.S03 — полный аудит blob SHA всех 83 текущих веток APA

**Дата:** 2026-10-11. **RUN_ID:** `APA-RUN-20261011-001922Z-eighty-head-blob-inventory`. **Task claim:** `APA-RUN-20261011T000452Z-branch-blobs-69`.  
**Scope:** SOURCE / GitHub REST, без Archicad, APX, PLN, SQLite или изменений main.  
**Статус исследований:** Git/tree/byte SHA — VERIFIED; содержание старых инженерных аудитов — REPORTED, LIVE NOT_VERIFIED.  
**Статус задачи:** PARTIAL после этого опубликованного этапа, до семантической дедупликации файлов.

## 1. Выполнено — охват всех текущих Git HEAD

Первоначальный [снимок 72 веток](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/BRANCH_HEADS_20261010.json) имел 69 HEAD SHA, но не описывал 11 новых веток. Теперь через GitHub `/branches?per_page=100&page=1` получена [актуальная на момент обхода перепись 83 веток](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BRANCH_HEADS_20261011.json), меньше лимита 100. Сравнение: +11 имён, удалённых 0, изменённая историческая SHA у канонической ветки 1; итого **80 разных HEAD**.

По GitHub REST `/git/trees/<commit-sha>?recursive=1` собраны **80 из 80** полных Git-деревьев, `truncated=false` в каждом случае. Для 68 неизменившихся HEAD использованы семь сохранённых исходных batch files; новые 11 веток и обновлённая canonical HEAD прочитаны и сохранены в `CURRENT_DELTA_BATCH_01.json` и `CURRENT_DELTA_BATCH_02.json`. Всего девять raw batch records в GitHub.

[Машинный полный summary 80 HEAD](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BLOB_AGGREGATE_20261011.json), [422 single-head SHA](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BLOB_EXCLUSIVE_20261011.json), [44 blob/path / 91 multi-version path](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BLOB_COLLISIONS_20261011.json) — readback PASS.

| Сравнимый показатель | Измерено по 83 веткам |
| --- | ---: |
| Вхождений файлов across HEAD | **14 920** |
| Различных git blob SHA | **1 578** |
| Различных путей файлов | **1 594** |
| Различных пар path+SHA | **1 748** |
| Git blob SHA только в одном из 80 HEAD | **422** |
| Git blob SHA, встречающихся во множестве HEAD | **1 156** |
| Один и тот же Git SHA по разным путям | **44** |
| Один путь с разными SHA | **91** |

**Семантика:** Git SHA однозначно свидетельствует о равенстве Git-сохранённых байтов. Однако `422` не означает 422 новых самостоятельных решения, а `44` не даёт права удалять повторяющиеся файлы: разные пути могут быть архивными доказательствами. SHA Git LFS pointer (если есть) — не сам внешний бинарный payload. Этот снимок описывает ветки на момент API-обхода, а не все будущие ветки.

## 2. Обнаружен крупный исходный архив, требующий сохранения

В `research/archicad29-tapir159-expansion` при точном SHA-сопоставлении находятся **71 текстовый MD/JSON source blob**, все под `research/archicad29-tapir159/`. Их нет как точных SHA ни в другом HEAD исторического снимка, ни в одном из 80 текущих HEAD. [Источниковый индекс 71 файла с pinned Git links и byte SHA](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json) теперь опубликован в канонической исследовательской ветке и повторно прочитан.

В отдельном [byte-exact сравнении с конкретной ревизией canonical branch](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CANONICAL_BLOB_COVERAGE_20261011.json) `6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27`: среди исторически exclusive 278 blob SHA обнаружено 7 пересечений с канонической, а среди 71 source SHA этого архива — **0**. Это не отрицает возможные пересказы или новый код с другим SHA; только точное совпадение исходных байтов.

**Явный незакрытый риск:** попытка перенести *сами 71 исходных файла* в канонический namespace одним Git commit была заблокирована write-инструментом. После отказа проверены HEAD и отсутствие нового `ARCHIVE_MANIFEST`: копирование **не произошло**. Source index и исходные ветки сохраняют проверяемые пути/SHA, но статус именно `SOURCE_LINKS_VERIFIED_NOT_COPIED`. Публикация исследовательского отчёта не равнозначна физической миграции всех 71 source-файлов.

### Content review — что действительно полезно

Прочитаны следующие исходные документы (исторический research, а не новое внедрение):

1. [Final Audit after pass 90](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Farchicad29-tapir159-expansion/research/archicad29-tapir159/09_final_audit/FINAL_RESEARCH_AUDIT_V2_AFTER_PASS_90.md) — deterministic recipe compiler и reuse существующих native BIM capabilities; LLM по запросу и отдельно от writer. Уже есть собственный highlevel compiler, поэтому не создавать параллельный новый writer.
2. [Project Context Bridge after pass 160](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Farchicad29-tapir159-expansion/research/archicad29-tapir159/09_final_audit/FINAL_PROJECT_CONTEXT_BRIDGE_AUDIT_AFTER_160.md) — свежий context snapshot с project identity/stamp, этажами, выделением GUID и защитой от stale state; требуется проверка точных API и identity/capture gates.
3. [Transport/Sync audit after pass 200](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Farchicad29-tapir159-expansion/research/archicad29-tapir159/09_final_audit/FINAL_TRANSPORT_SYNC_OUT_OF_BOX_AUDIT_AFTER_200.md) — локальный guarded service, SQLite/journal и GitHub connector только для пересечения cloud boundary; не считать это уже работающим 24/7 agent.
4. [Integration backlog](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Farchicad29-tapir159-expansion/research/archicad29-tapir159/06_integration_audits/INTEGRATION_BACKLOG.md) — grouped Project Profile, Favorites, Hotlink, GDL, roof/mesh QA and documentation re-use; первоначально привязан к Tapir **1.5.9**, нынешнюю **1.5.10** и installed APX нужно проверять отдельно.
5. [Controlled Probe backlog](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Farchicad29-tapir159-expansion/research/archicad29-tapir159/07_live_probe_backlog/NEXT_CONTROLLED_PROBES.md) — Roof, Mesh, Morph, SEO, Trim, Hotlink/GDL как кандидаты контролируемых испытаний, но его публикация не разрешает записи в PLN.

**Вывод:** полезные оригинальные исследования существуют, а не «потеряны», однако исходные SHA в canonical до этого не были представлены. До любого внедрения обязательны аудит применимости, сопоставление с уже существующим MVP и повторный контроль installed/source версиями.

## 3. Актуальный продуктовый контур — не перепутать с историческим архивом

Новая [ветка feature/apa-highlevel-whole-model-20261011](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/apa-highlevel-whole-model-20261011) содержит **10 SHA эксклюзивно в одном HEAD**, среди них highlevel building-shell intent и исполнитель, tests, read-only partial-scene diagnostic. Исходный [APA_HIGHLEVEL_EXECUTION.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-highlevel-whole-model-20261011/docs/APA_HIGHLEVEL_EXECUTION.md) сообщает 106/106 offline + synthetic CI PASS, но **Archicad LIVE создание не подтверждено в этом проходе**. Это источник отчёта, а не независимый воспроизведённый тест.

[Read-only recovery diagnostic](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-highlevel-whole-model-20261011/scripts/diagnose_apa_partial_scene.py) требует совпадения journal scene/hash, оценивает partial Slab и **запрещает слепой повтор Create**. Нельзя переиспользовать `-Execute` без свежих read-only evidence и явного owner acceptance в рабочем PLN. Результаты высокоуровневой сборки относятся к существующей `APA-P70.A03.S02`, не являются отдельной конкурирующей реализацией.

## 4. Дедупликация и границы принятия

- **EXACT_HEAD_ALIAS:** три имени поверх существующих HEAD в 83-branch snapshot, хранить происхождение.
- **EXACT_CONTENT_EQUALITY:** 44 SHA, встречающихся в разных путях. Архивная копия может быть отдельным доказательством; не удалять.
- **DIFFERENT_VERSION_SAME_PATH:** 91 файл-путь с разными SHA, не разрешено автоматически выбирать «новейшее».
- **EXCLUSIVE_BY_HEAD:** 422 SHA требуют content-level source mapping, не 422 внедрённых инструмента.
- **SOURCE_ARCHIVE_NO_COPY:** 71 pinned original MD/JSON; отдельная задача на корректный перенос исходных байтов остаётся OPEN.
- **NO_LIVE_CERTIFICATION:** старые source/CI/README и запись Git SHA не заменяют тест на установленной версии Archicad/Tapir и точном проекте.

## 5. Привязка к единому реестру и следующий критерий

**Текущий измеримый результат:** baseline 83 refs, полный обход 80 HEAD, два machine inventories путей/версий, 71 source-index links и обзор ядра архитектурных аудитов сохранены в GitHub. Сам этот research run можно пометить `DONE_PUBLISHED` после receipt/readback; **подзадача APA-P00.A02.S03 остаётся PARTIAL**, поскольку не проведена содержательная классификация всех 1594 путей и все 71 source-файл не скопированы.

**Следующий блок:** в рамках `APA-P00.A02.S03` и `APA-P50.A01.S01` приоритетно выполнить batch-review 422 single-head SHA: сначала 71 text sources/10 highlevel sources, затем уникальные test contracts и library releases. Для `APA-P70.A01.S02` обновить capability→evidence mapping, `APA-P70.A03.S02/.S03` — связь context snapshot/SceneWriter с существующим MVP, `APA-P10.A02.S01` — сверка исторических Tapir 1.5.9 contract proposals с текущей 1.5.10. Отдельное source-copy решение предложить аудитору без создания дублирующей задачи: обязательны сохранение byte SHA, SHA readback и no-main policy.

**Не выполнялось:** изменения main/master, PLN/APX, Archicad, Socket Mode SQLite, source code; нет новой LIVE геометрии или нормативных сертификатов. Никакого Deep Research/платного исследовательского окружения не использовалось.
