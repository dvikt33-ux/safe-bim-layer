# APA-P70.A02.S03 — первый проектный Library Pack, без дублирования источников и BIM-исполнителя

**2026-10-11** · **Phase: OFFLINE** · **Источник:** [draft PR #41](https://github.com/dvikt33-ux/safe-bim-layer/pull/41) · **GitHub CI:** [#38155701345](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38155701345) **SUCCESS, 231/231 offline tests**. Контроллер `PROJECT_PLAN.json` source rev62, task `APA-P70.A02.S03` claimed with owner/lease/CAS and readback before implementation. Текущий отчёт — строгий **минимальный project-scope candidate pack**, НЕ полная пригодная к строительству библиотека.

## Итог

Использован уже реализованный интерфейс `archicad_project_accelerator.py` и его `archicad_semantic_brief` из [PR #40](https://github.com/dvikt33-ux/safe-bim-layer/pull/40). В отдельном [PR #41](https://github.com/dvikt33-ux/safe-bim-layer/pull/41) добавлен только тонкий `archicad_project_library_pack.py::compile_pack`, вызываемый через существующий `compile_project_library_pack`. Он **не** создаёт собственные source registry, материал-резолвер, BIM DAG, SceneWriter, разрешения или native writer. Использует **существующий** `archicad_scene_run.resolve_basic_slab_material` для одного явного Building Material name→GUID в единственном открытом PLN. Native API только `GetProjectInfo`, `GetStories`, `GetAttributesByType`, все прочие вызовы запрещены.

**Выбранный первый узкий CSE-кандидат**: `rc-basic-slab-v1`, семья `reinforced-concrete-slab-provisional`, роль `floor-slab`, Basic Slab **200 мм** и material name `Железобетон - Конструкционный`. При точном текущем тестовом PLN ожидается **не глобальный ID**, а локальный проверяемый Guid `63db2ce9-903d-45c0-b93c-b3c604c77394` из пользовательского live typed readback. Это только доказательство **геометрии и атрибута в конкретном PLN** (2 slabs на двух этажах, 25/25 элементов и 45/45 GUID после смены .bpn→.pln); это **не** подтверждение прочности, применимости строительной системы к реальному проекту, прав на внешнюю библиотеку или типовых узлов. Для других PLN несовпадение GUID → STOP, не silent selection.

**Реально опубликован Project Library candidate:** `examples/accelerator/project-library-rc-slab.candidate.json` в PR #41; это editable source-safe JSON с id системы, реальным material name, expected project GUID, толщиной в метрах, per-story scope, source URI и Git blob hash, лицензией `LINK_ONLY_RIGHTS_UNVERIFIED`, статусом `PROJECT_NATIVE_READBACK`, явными *missing* интерфейсами. Авторизация внешних библиотечных загрузок **не дана**.

### Source identity and rights

| Объект | Точная публикация и source SHA (Git blob, НЕ SHA256) | Применимость / лицензионный вывод |
|---|---|---|
| Existing ProjectLibraryPack contract v0.1 | [project-library-pack-contract-v0.1.yaml](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), blob `3fc09f03c3ac6305fc73a92c6889ff9f6c7d8bd8` | RESEARCH_DRAFT — используется **ссылка** и список обязательных прав/статусов, без автозагрузки исходных документов |
| Existing Details release v2.12 | [details/releases/v2.12/manifest.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12/manifest.json), blob `797752bd4eb5b82a0056e2bc475dd4005fff4abb` | 1 215 detail units / 1 835 parameter facts — это индекс знаний, не 1 215 утверждённых строительных узлов. Ни один узел не объявлен APPROVED автоматически; не делается импорт PLA/LCF/GDL |
| Применимость выбранного Basic Slab | [проверенный пользовательский native отчёт](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/apa-p70-a03-s02-pr35-basic-slab-implementation-partial-20261011.md), Git blob `e4bf711bdc3322f594699b59ea34107cde0bcfdf` на дату отчёта | Evidence: USER_REPORTED_LIVE_TYPED_READBACK_PASS and .pln path switch. Ссылка указывает на source-safe отчет, а не на право повторно копировать сторонний контент или инженерное утверждение |

Output Project Pack включает `catalogReferences`, `sourceLinksAndGitBlobHashes`, `sourceRegistryRevision`, `native` (BM name/optional exact live GUID), `selectedCseCandidates`, `requiredJunctionConditions`, `missingCriticalConditionIds`, `licenseAndStoragePermission`, `normativePackDigest=null`, `importedLibraryObjects=[]`. Не объявляются выдуманные Favorites, Composites, Profiles, LCF и GDL; свойства `engineeringApproved=false`, `detailApproved=false`. В runtime переносимое user-provided source URI/hash считается **декларацией**, а не независимо загруженным SHA256/подтверждением источника; данный пример сверён отдельно GitHub fetch_file/readback.

**Три реально открытых interface conditions:**
1. `slab-wall-bearing` — опирание стены на плиту (недостаточно проектных нагрузок и detail applicability).
2. `floor-waterproofing` — инженерно/архитектурно подтверждённая гидроизоляция и применимый узел.
3. `slab-opening-penetration` — проходки, огнезащита, короба и условия сопряжений (пока нет индивидуального проектного source).
Все три имеют `UNVERIFIED` и `selectedDetailIds=[]`: **никакого construction/engineering normative PASS**.

### Элементы и границы AC29

- Подтверждён **один** AC29-compatible native attribute class: `BuildingMaterial` (exact name+GUID), в контексте ранее проверенного Basic Slab в approved scratch PLN. Другая модель требует **свежий** project identity + native material lookup и совпадение/отказ; не рассылается GUID между проектами.
- Favorites / Composites / Profiles / custom GDL Objects: **NOT_SELECTED / NOT_VERIFIED**; не считаются существующими в активном Archicad по одному только каталогу. Расширение после source/license/native capability audit.
- Native floors resolved `GetStories` по S01; `GENERATE_FROM_ZERO` остаётся только корректным source-level input, не триггером для открытия/создания PLN.
- Requirement ambiguity, license status, unknown junctions сохраняются в результатах, а не подменяются «стандартным» решением.

## Offline CI и тесты

[CI #38155701345](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38155701345) — `231 tests, OK` — провёл 219 ранее существовавших и 12 новых тестов. Покрытие: оба режима и формирование pack без native; exact active PLN identity и GetStories; использование прежнего RUN material resolver; 0 native writes; поиск ровно одного BM / блокировка отсутствия и дублей; false expected material GUID; запрещение самосертификации прав и detail approval; wrong PLN; unresolved story; duplicate conditions, invalid SI thickness/source SHA; незавершённые нормативные требования. **Архикад локально не запускался в этом цикле**. CI — синтетическая проверка логики, а не live установленных библиотек.

Первоначально тесты упали из-за ошибочного переиспользования поля mock `names` для этажей и материалов (тестовый fixture). Исправлено в отдельной ветке PR #41, финальная CI SUCCESS. Никакая native запись, PLN/APX/main/master/tested code branch не изменена этим S-ID.

### Ограничения и следующее действие

**Source/offline acceptance достигнут для одной проектно-локальной CSE-подсистемы**: источники+Git blob SHA+права, минимальный геометрический материал, scope этажа, явные интерфейсы/отсутствующие узлы и read-only точная атрибутика. Это **НЕ** полный каталог ограждений, не «готов к стройке», не аккредитация нормативных значений.

**Следующий S-ID по текущему DAG:** `APA-P70.A03.S01` — semantic rooms / support axes / story and CSE condition inputs → existing BIM graph (still no write), игнорируя недоказанные инженерные/нормативные PASS. В нём использовать текущий минимальный pack как *provisional geometry envelope*, а нерешённые сопряжения как hard blockers до конструктивного acceptance. В параллельном потоке `APA-P70.A02.S02` — нормативные источники с применимостью, по мере необходимости; не блокировать создание первой геометрии избыточной нормативной археологией. Потребуется расширить system set только когда spatial designer реально запросит дополнительную семью.

**Следующий PR:** не второй writer/граф; адаптировать semantic rooms/axes к существующему `archicad_bim_graph` и parameterized `building-shell` с duplicate guard, и только после положительного offline + отдельного разрешения native test.
