# APA-P00.A02.S03 — физическое сохранение 71 исторического source-файла + экспертиза повторного использования

**Run:** `APA-RUN-20261011-092155Z-source71-byte-archive`; **claim:** `APA-RUN-20261011T091256Z-archival-content-audit`; **основа:** существующая `APA-P00.A02.S03` (`legacy-evidence-dedup`).  
**Фаза:** SOURCE; результат данного прохода **SOURCE_VERIFIED / PARTIAL**.  
**Каноническая ветка:** `research/apa-verified-results-hub-20261010`; запись исключительно GitHub, без Archicad, PLN, APX, SQLite, main/master и без Deep Research.  
**Период:** 2026-10-11 (локальная дата пользователя).

## 1. Сохранение source-байтов завершено и независимо проверено

Source tree `c651035ddc77869fbc5a04bf23170b4f1188a9ab`, `research/archicad29-tapir159/`: 71 исходный Git blob (`.md/.json`), суммарно **487455 байт**. Перед записью исходные `path/sha/size` сопоставлены с pinned [source index](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json); расхождений = **0**. Архивный каталог ранее отсутствовал.

**Коммит архивирования:** [`477ba54a`](https://github.com/dvikt33-ux/safe-bim-layer/commit/477ba54a0620ce7c0efc1b835f1d0ad2f1a03ba5), parent `a22d4f45f747850d06f457a163b528fb48e4c29f`; дерево `4958d8016d995248f5f7fe627ec98ae20794608e`. Git `create_tree(base_tree,71 entries)` ссылался **непосредственно на исходные существующие blob SHA**, `create_commit` создал одну новую ревизию, `update_ref(expected_sha=parent,force=false)` обновил **только** canonical research branch.

После записи независимое чтение Git дерева по commit SHA подтвердило **71/71 одинаковых `SHA` и размеров**, `truncated=false`, исходный commit в качестве parent, незатронутые source paths. Не менялись содержимое, перевод строк, пробелы или исходные Git объекты. Файлы находятся в [архивной директории](https://github.com/dvikt33-ux/safe-bim-layer/tree/477ba54a0620ce7c0efc1b835f1d0ad2f1a03ba5/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/).

Проверяемый список source/target идентификаторов: [`ARCHIVE_MANIFEST_20261011.json`](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/ARCHIVE_MANIFEST_20261011.json). Дополнительный [навигатор](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/ARCHIVE_GUIDE_20261011.md) сохранён под отдельным именем: штатный `README.md` оказался оригинальным архивным документом, попытка создать файл с тем же именем была отклонена HTTP 422 и оригинал оставлен нетронутым. Навигация опубликована как `ARCHIVE_GUIDE_20261011.md`.

**Статус переноса:** `LEGACY_SOURCE_ARCHIVED_BYTE_EXACT`. Это доказывает идентичность *файлов*, но не актуальную техническую достоверность содержащихся в них утверждений.

## 2. Что обнаружено при технической проверке (выборка 13 исходных документов)

| Область | Source | Вывод для нынешнего APA | Verification |
| --- | --- | --- | --- |
| Детерминированный компилятор | [Final Audit V2, pass 90](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/09_final_audit/FINAL_RESEARCH_AUDIT_V2_AFTER_PASS_90.md) | Системный принцип profile/recipe/graph/writer и короткого on-demand AI соответствует действующей цепочке Project Accelerator → BIM Graph → SceneWriter. **Новый второй исполнитель не нужен.** | Historical research + нынешняя исходная реализация |
| Существующий параметрический builder | [`archicad_building_shell.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-highlevel-whole-model-20261011/scripts/archicad_building_shell.py) | Реальный исходник ограничивает native writes `CreateWalls, CreateSlabs, CreateDoors, CreateWindows` и строит graph/plan. Roof/Gable/Composites там **не реализованы**; успешные синтетические тесты не означают LIVE строение. | CURRENT CODE READBACK |
| Одна двускатная кровля как native объект | [single-element Gable Roof research](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/03_archicad_api_contracts/SINGLE_ELEMENT_GABLE_ROOF_RESEARCH_PASSES_01_20.md), [исправляющий addendum](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/09_final_audit/GABLE_ROOF_FINAL_AUDIT_ADDENDUM.md) | Исследуется один `API_PolyRoofID` с per-edge data вместо двух single-plane Roof. Это **отдельная потенциальная capability**: актуальная команда Tapir 1.5.10, мемо и live readback НЕ проверены. Не заменять одно решение двумя крышами без проекта/требований. | SOURCE CANDIDATE / LIVE NOT_VERIFIED |
| Composite/слойность | [Composite passes 01–18](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/03_archicad_api_contracts/COMPOSITE_STRUCTURES_RESEARCH_PASSES_01_18.md) | Старый Tapir 1.5.9 предполагает использование `CreateComposites` и `GetComposites` с проверенными слоями/fingerprint вместо самодельного псевдо-материала. Текущую 1.5.10 и project building materials требуется проверить. | SOURCE CANDIDATE |
| GDL library factory | [factory passes](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/05_expansion_candidates/PARAMETRIC_GDL_LIBRARY_FACTORY.md) | HSF/XML→GSM pipeline + Library Part name/GUID preflight; пользоваться текущим GDL/TN blocker1 анализом, не считать 92 ошибок закрытыми. | HISTORICAL PROPOSAL |
| Fresh project-state bridge | [audit after pass 160](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/09_final_audit/FINAL_PROJECT_CONTEXT_BRIDGE_AUDIT_AFTER_160.md) | Project ID/stamp, model GUID index, atomic context snapshot, stale-plan rejection; сравнить со свежей current context bridge и существующим dump, не начинать второй постоянный watcher. | HISTORICAL ARCHITECTURE |
| Cloud/local transport | [audit after pass 200](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/09_final_audit/FINAL_TRANSPORT_SYNC_OUT_OF_BOX_AUDIT_AFTER_200.md) | Предлагает локальную очередь + GitHub boundary для обычного ChatGPT. Нынешний LIVE Slack→SQLite **доказал только transport/dedup событий**, не самоисполняемый research agent или произвольный доступ ChatGPT к PLN. | HISTORICAL ARCHITECTURE |
| Разработка и тесты | [Development Acceleration Audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/06_integration_audits/DEVELOPMENT_ACCELERATION_AUDIT.md) | Авто-синхронизация схем, golden fixtures, разделение offline/live и уже действующие controller/publisher receipt полезнее ещё одного оркестратора. | SOURCE POLICY |
| Project Profile | [Project Profile schema v0.1](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/00_master/project_profile_v0_1.schema.json) | Профиль — историческая draft JSON-схема, не current executable input contract. Имеет смысл как справочник для `APA-P70.A01.S01`, но только после semantic gap map. | HISTORICAL DRAFT |

Выборка содержит **13 прочитанных конкретных файлов из 71** плюс актуальный код APA; остальные 58 сохранены байт-в-байт и индексированы, но их *содержательное* заключение этим проходом не сертифицировано. Для всех 71 применимо только доказательство файла/побайтового архива.

## 3. Решение по обнаруженному предложению новой подзадачи

В [`TASK_REVIEW_V1`](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/control/reviews/APA-CAND-20261011-source-archive-71.md) кандидат `APA-CAND-20261011-source-archive-71` рассмотрен с `decision=DUPLICATE` относительно **существующей S03**, потому что измеримый отдельный результат «71 оригинальный source blob → 71 target-path с тем же SHA» уже выполнен внутри S03 и подтверждён. **Новую S05 не регистрировать.** Это не отвержение исходных исследований, а устранение дублирующей исполняемой задачи.

- Принят для дальнейшей работы действующий `APA-P00.A02.S03`: семантическая дедупликация и `superseded_by`.
- Связанный `APA-P50.A01.S01`: traceability исследование↔S-ID↔product capability.
- `APA-P70.A01.S02`: product evidence-to-capability map, с обязательными предшествующими задачами.
- `APA-P10.A01.S03` и `APA-P10.A02.S01`: актуальность geometry/API/Tapir 1.5.10; никаких новых параллельных S-ID для gable-команд.

## 4. Точные ограничения и следующая проверка

1. Архив содержит исходные MD/JSON файлы из Tapir 1.5.9 era, не 1.5.10. Совместимость и native capabilities не повышать без текущего source/schema, installed binary identity и отдельного live readback.
2. Source archive и нынешний Project Accelerator могут содержать *семантически* одинаковые идеи под разными SHA; архивирование не доказывает уникальность 71 технического решения.
3. В текущем `archicad_building_shell.py` проверены разрешённые классы native writes, а не факт исполнения в Archicad. Не утверждать Roof/Composites/MEP, нет в текущем bundle.
4. В GitHub не копировались исходные исторические бинарные библиотеки или неизвестные приватные сведения: только существующие 71 text Git blob из публично доступной source ветки.
5. **Next eligible measured result:** `APA-P00.A02.S03` — content-level comparison источников Roof/Composite/Context с current capability matrix и тестовой evidence, подготовить `superseded_by` и точный блокирующий readback. Не делать 71 мелкую команду запуска Archicad.
6. Независимый контроллерный валидатор/CI не запускался этим report; GitHub byte SHA readback и publisher publication receipt — разные gates.

**Итог прохода:** `SOURCE_VERIFIED` для переноса байтов и совпадения SHA; `REPORTED/HISTORICAL` для инженерного содержимого; task остаётся `PARTIAL` с доказательством, не `DONE_PUBLISHED`. `main`, source commit/branch, Archicad, PLN, APX, installed software и Slack SQLite не изменялись.
