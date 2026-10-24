# APA R2 — BUILD-01: конечный поиск GH→PR74 и матрица конфликтов
**Срез:** 24.10.2026, 15:04 UTC (18:04 МСК). **Роль:** R2, мосты/синхронизация. **Задача:** [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка публикации:** `research/apa-extension-ranking-hub-20261018`. **Уровень:** SOURCE_ONLY; MODEL_MODE_NOT_VERIFIABLE.

## 1. Свежие поручения и входы
Прочитан A5 14:39Z [audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md](audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md), Git blob `2b9079c78c226f4c01cb05b6957e993c6f4e0d12`. Прямые поручения R2-15A: **закрыть ограниченный поиск** готового GH→PR74 adapter по названным веткам и файлам; R2-15B: **конфликты** create/update/delete/UNKNOWN/partial Slab/host drift/feedback loop, owner GUID, readback, STOP. Также прочитаны R1 14:58Z [G0 inventory](research-1-20261024T1458Z-BUILD01-G0-READONLY-INVENTORY.md), blob `5c036f238ae65afd3a0f338eb98d0884aaad7805`; R3 14Z [GH graphs QA](research-3-2026-10-24T14Z-GH-GRAPHS-QA-CONTRACT.md), blob `6d28049eecf832fcde60e3da92356acf1753cac1`; I4 14:15Z [runtime gate](integrator-4-2026-10-24T1415Z-BUILD01-RUNTIME-GATE-CORRECTION.md), blob `634c993599aab6a5ff059a4701ec8a841fa79992`; предшествующий R2 14Z, blob `6c5e5d3f83cef786f79e7e5ed97eb8a9bac665cc`. Это проверка документов на GitHub, **не** установленной конфигурации ноутбука.

## 2. R2-15A — закрытый, воспроизводимый scope поиска
Через GitHub connector получены **фактические** метаданные пяти PR, полные списки changed filenames и содержимое **12 указанных ниже Python-файлов** на immutable head commits. В каждом из 12 файлов проведён текстовый просмотр вхождений `grasshopper|rhino|datatree|gh_bridge|gh_to_|gh.io|ghjson` с отдельным поиском `sourcePlanHash|scene_id|ATTEMPTED|ModifySlabs|GetStories|--preflight`. Первой группы терминов в этих 12 файлах **не найдено**. Это ограниченный SOURCE-поиск, а не доказательство отсутствия bridge в остальных файлах репозитория.

| PR | Immutable head commit | Фактически прочитанные Python-файлы | Итог в этом scope |
|---|---|---|---|
| [#74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) | `5a3a9201a715a5528c93bed4a5318e2acb32eea7` | `scripts/archicad_project_accelerator.py`, `archicad_authored_native_plan.py`, `archicad_scene_run.py`, `archicad_authored_extension.py`, `archicad_accelerator_integration.py` | Есть typed authored intent, BIM Graph/SceneWriter; GH parser НЕ найден |
| [#126](https://github.com/dvikt33-ux/safe-bim-layer/pull/126) | `f12aeba017ecd34a13989998f0b7700f6a0107d2` | `scripts/archicad_dynamic_commands.py` | Batch/dynamic workflow, GH converter НЕ найден |
| [#131](https://github.com/dvikt33-ux/safe-bim-layer/pull/131) | `75ae71dc60176225bb71928fb805e5adcc688b2e` | `scripts/archicad_strategy_discovery.py`, `archicad_project_accelerator.py` | Discovery/preview, GH converter НЕ найден |
| [#149](https://github.com/dvikt33-ux/safe-bim-layer/pull/149) | `4c119428e9b1c24bd00774c91a6f33cbf26f0369` | `scripts/apa_ac29_dynamic_native_verifiers.py`, `install_apa_ac29_autonomous_job_bridge.py` | Existing verifier/bridge для заданий APA, **не GH DataTree adapter** |
| [#162](https://github.com/dvikt33-ux/safe-bim-layer/pull/162) | `f7c37b84b76c040c417ccd58a5543326e50f673a` | `scripts/apa_ac29_group_strategy.py`, `archicad_project_accelerator.py` | Group-first routing, GH converter НЕ найден |

**Вердикт:** `GH_TO_PR74_ADAPTER_NOT_FOUND_IN_12_INSPECTED_FILES_5_PR_HEADS`. Не утверждать `NOT_FOUND` во всех ветках или installed. **Исследовательскую ветку нельзя принимать за объединённую сборку этих PR.** Повторный поиск без нового указания конкретного файла/коммита не повышает BUILD-01; закрыть R2-15A в данном scope и передать I4 временный путь через **ручной typed authored JSON**, а не новый writer/router. Исходный PR74 `scripts/archicad_project_accelerator.py` содержит `--preflight`; для `apa-authored-project/1` необходим read-only доступ к Archicad, полностью автономный offline G1 запрещён. Реальный G1 **не выполнялся**.

## 3. Первоисточники, версии, лицензии
1. [Graphisoft официальный дистрибутив](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/): **Grasshopper–Archicad 29 Live Connection build 3000**, Windows, Rhino 7/8, дата **01.10.2025**; Start Edition не поддерживается. Это SOURCE, **не** INSTALLED; поддержка конкретного локального Archicad 29 build 5101 проверкой запуска не доказана. GC30 2026 **не заменяет** GC29.
2. [Tapir upstream](https://github.com/ENZYME-APD/tapir-archicad-automation): Archicad Add-On с командами и отдельный GH plugin; лицензия репозитория MIT, но не эквивалент лицензии конкретного бинарного Yak. Заявленный локальный Add-On **1.5.10** требует GetAddOnVersion + APX SHA + registered schema.
3. [Rhino Packages: tapir](https://rhinopackages.github.io/package/tapir): GH package **1.7.2**, обновление **19.10.2026**, опубликован `tapir-1.7.2-rh7_21-any.yak`, «No Rhino 8+ build», лицензия «Not declared». [McNeel Yak distribution](https://developer.rhino3d.com/en/guides/yak/the-anatomy-of-a-package/) объясняет `rh7_21` как Rhino 7.21+, а `rh8` как отдельную цель. Вывод `RHINO8_DISTRIBUTION_NOT_FOUND_IN_CHECKED_CATALOG`, **не** «плагин заведомо не работает в Rhino 8».
4. [McNeel Rhino.Inside](https://www.rhino3d.com/features/rhino-inside/): технология встраивания Rhino в Windows hosts, но готовый поддерживаемый host/add-on **Archicad 29** и путь в один существующий SceneWriter здесь **не подтверждены**. Не включать в G0.
5. Rhino 8, Archicad 29, лицензии самих программ, версии/хеши локальных APX/GHA/PLN и соединение не инспектировались: `INSTALLED=NOT_VERIFIED`. Бесплатность дополнения не означает бесплатность Rhino/Archicad.

## 4. Восемь обоснованных маршрутов для I4 (один writer)
| № | Направление и готовое средство | Native BIM / идентичность | Режим BUILD-01 |
|---|---|---|---|
| M1 | Rhino/GH параметрические размеры → **ручная верификация и перенос** в `apa-authored-project/1` JSON → PR74 compiler | Нативность появляется только после SceneWriter/Tapir; GH preview не BIM | **P0 SOURCE, без автоматического bridge** |
| M2 | AC `GetStories/GetProjectInfo/GetAttributesByType` → PR74 G0/G1 | Story `index/floorId/level`, material ID принадлежат активному PLN | **P0 read-only** |
| M3 | AC → Graphisoft GC29 **Element Input/Deconstruct/Story Plane** → GH reference/QA | AC GUID — источник истины; GH reference не AC writer | **P0 после INSTALLED, read-only** |
| M4 | Typed PR74 → BIM Graph/DynamicCommands → **единственный SceneWriter + SQLite → Tapir** | AC GUID появляется после CREATE и читается обратно; host Wall → Window/Door | **P0, G3 только с допуском** |
| M5 | GH Design → GC29 native Create/Modify | Может создавать настоящие native BIM, но является **вторым writer** | **НЕ подключать** параллельно SceneWriter |
| M6 | Tapir GH 1.7.2 → Tapir Add-On | Возможен отдельный путь записи; Rhino8 Yak и владение GUID не подтверждены | **НЕ обязательный**, не подключать к G3 |
| M7 | Rhino `.3dm` / GDL/GSM / Morph import в AC | Не доказывает native Wall/Slab/Roof/Window/Door и hosted GUID | Только reference/visual, **не BUILD-01** |
| M8 | AC native GUID/BREP readback + IFC/IfcOpenShell/IDS независимый QA | IFC GlobalId ≠ AC GUID; IFC/IDS не заменяет native BREP и СП экспертизу | **P0 G4 QA**, без обратной IFC-записи |

**Не выбран:** Rhino.Inside для AC29 (готовый host NOT_FOUND в проверенных первоисточниках), Content Cache Push/Bake/Purge как механизм native AC (нет контракта одного SceneWriter), произвольная двунаправленная синхронизация. Никакого нового writer/router/synchronizer.

## 5. R2-15B — таблица владения и STOP при конфликтах
**Разные пространства ID:** Rhino `ObjectId`, GH document/component/path, APA `stepId/sourcePlanHash/scene_id`, Archicad native `GUID`, IFC `GlobalId`. Не копировать их друг в друга как одинаковые. `GUID` и `ownerWallId` читать из AC receipts; `storyIndex` связывать с реальным `GetStories`, не с порядком в GH. Изменение/удаление host Wall требует проверки всех hosted children.

| Событие | Владелец / readback | Обязательная реакция |
|---|---|---|
| CREATE native | SceneWriter журналирует `ATTEMPTED` до API; GUID принадлежит AC | Получить GUID/type/story/material/bbox; нет receipt → `UNKNOWN_STOP`, без повторного CREATE |
| UPDATE параметров | Только разрешённый SceneWriter/существующий Modify; AC GUID | До/после snapshot и readback; при drift остановить, не подменять GUID |
| DELETE native / потеря GH-ссылки | AC GUID + SQLite ledger; GH Null/Sync=False не является delete receipt | `DELETE_UNAUTHORIZED_STOP`, ручная сверка; не удалять по пустому GH output |
| TIMEOUT/UNKNOWN | `scene_id/plan_hash` уникальны; SQLite != транзакция PLN | `STOP` → SQLite+GetAllElements/GetDetailsOfElements, без нового scene_id для обхода |
| PARTIAL SLAB | `CreateSlabs → readback → ModifySlabs(material)`, две native mutations | При UNKNOWN на Modify сохранить уже созданный GUID; проверить материал; **не** повторять CreateSlabs |
| HOST DRIFT | AC Wall GUID + hosted Window/Door ownerWallId + story | `HOST_DRIFT_STOP`; без автоматического перепривязывания/пересоздания |
| FEEDBACK LOOP | AC→GH Element Input/Deconstruct → GH Design Create/Modify | `SECOND_WRITER_STOP`; физически разорвать GH Design write branch |
| SAVE/OPEN DRIFT | AC persisted PLN, а не Rhino .gh и не SQLite | GuardedSave/Close/Reopen только после разрешения; GUID/type/story/host/material/BREP diff; расхождение → `G4_FAIL` |
| ROLLBACK | Ни GH Undo, ни SQLite не откатывают атомарно AC+Rhino | Только заранее разрешённая scratch snapshot и отдельно утверждённое восстановление; `ATOMIC_ROLLBACK_NOT_FOUND` |

## 6. Конкретный контракт I4, G0–G5 и доказательства
- **G0 READ:** `API.GetProductInfo`/build, `GetProjectInfo`/path+port+SHA, `GetStories`/index+floorId+level, `GetAddOnVersion`/1.5.10+APX SHA+command schema, attributes/Favorites/library parts, Rhino8 version+units+tolerance+license, GC29 installed, immutable PR74 checkout. R1 указывает, что `GetFavoritesByType` не входит в PR74 `EvidenceAPI.READS`: отдельное существующее read-only чтение или `BLOCKED`, **не** новый router.
- **G1 PREFLIGHT:** одно новое authored JSON, `--preflight` с запущенным Archicad только для чтения, `--output` на **ещё не существующий** каталог, DAG/plan hash/schema/story/host/material/collision; `nativeWriteCalls=0` + inventory before=after. **Не маркировать OFFLINE_PASS без реального запуска.**
- **G2 SCHEMA:** локальная registered Tapir 1.5.10 schema vs frozen PR74 и upstream; `Window/Door libraryPartName` drift, Slab Basic material two-step, Roof SinglePlane, Column/Beam opt-in, host Wall GUID. Несовпадение → `BLOCKED_LOCAL_SCHEMA`.
- **G3 WRITE:** только отдельный явный допуск на конкретные scratch PLN/port/plan hash; единственный SceneWriter; GUID receipts и native BREP. Сейчас `NOT_AUTHORIZED`.
- **G4 PERSIST:** GuardedSave, реальное Close/Open, независимый native inventory, diff GUID/type/story/host/material/BREP; IFC/IDS отдельные слои QA.
- **G5 GENERALITY:** второе независимое authored задание и новая scratch PLN, полный цикл; без него `BOUNDED_DEMO`.
- **QA verdicts:** `GH_GEOMETRY`, `AC_NATIVE`, `IFC_STRUCTURE`, `IDS_INFORMATION`, `NORMATIVE_REVIEW` раздельно; GDL/Morph не принимать за native Wall/Slab.

## 7. Передача I4/A5 — закрыть blocker, не повторять исследования
**I4/P0:** принять `GH_TO_PR74_ADAPTER_NOT_FOUND_IN_12_INSPECTED_FILES_5_PR_HEADS` как закрытый **ограниченный** поиск. Не строить новый bridge; G1 использовать authored JSON из существующего PR74. Подтвердить фактическую G0 среду; затем один G1 `--preflight` без записи. При отсутствии доступа отметить `BLOCKED_RUNTIME`, а не SOURCE-прогресс.
**I4/P0:** в runbook запретить одновременный GH Design writer; внедрить уже имеющиеся guard `scene_id/plan_hash`, readback при UNKNOWN и отдельный Slab material receipt; никаких новых компонентов.
**A5/P0:** закрыть R2-15A/15B как `SOURCE_SCOPED_DONE`, не как BUILD. Следующий аудит проверяет наличие G0 manifest/G1 preflight receipt, а не количество новых GitHub-исследований.

## 8. Статусы и ограничения
**SOURCE:** фактически прочитаны A5/R1/R3/I4/R2/issue; 5 PR metadata + 5 PR changed-filenames lists; 12 конкретных Python-файлов; официальные страницы Graphisoft, McNeel и каталог Tapir. Число независимых «проверок» не объявляется. **OFFLINE:** новых запусков 0. **BUILD:** 0. **INSTALLED:** NOT_VERIFIED. **LIVE:** 0 новых. **ACCEPTED:** 0. **NOT_FOUND (строго scoped):** GH→PR74 adapter в 12 прочитанных файлах пяти head commits, подтверждённый Rhino8 Yak Tapir GH distribution в проверенном каталоге, готовый Rhino.Inside AC29 host в просмотренных официальных материалах, атомарный cross-app rollback. **G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN.**

**Безопасность:** main, исходники, PLN/APX, локальная установка, LIVE, merge, платные API, Work/Codex/Arena не затрагивались. Изменение — только этот новый русский отчёт в разрешённой исследовательской ветке. `MODEL_MODE_NOT_VERIFIABLE`.
