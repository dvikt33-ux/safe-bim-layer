# APA — IMPLEMENTATION ROADMAP: CORE FIRST → EXPANSION

Пользовательский порядок исполнения от 2026-10-11. Единственный реестр задач и статусов — [PROJECT_PLAN.json](PROJECT_PLAN.json). Эта карта является его человекочитаемой проекцией; новая независимая очередь не создаётся. Полная рабочая инструкция — [WORK_OPERATING_INSTRUCTION.md](WORK_OPERATING_INSTRUCTION.md).

## Ближайший работающий результат

Ядро APA-P70.A03.S02/S03/S04 → A08.S04 принято и опубликовано: PR #48 head `976c19cecebe3f6bb4352365d9a59051d5b2b61b`, native 17 основных элементов + 2 принадлежащих колоннам сегмента + 20 исходных GUID. Подтверждены создание, материалы/этажи/host, инкрементальная правка окна с возвратом, сохранение и повторное открытие. PR остаётся draft без merge.

Геометрия A09.S01 также DONE_PUBLISHED: PR #50 head `ec401314c185df4845ccb6ae7b15e57234a46cad`, CI 296 тестов PASS; native dump/XYZ/material/host, 34 контакта реальных BREP-граней, 40 пересечений XY без объёмной коллизии. Расчётная/нормативная пригодность и качество узлов остаются NOT_VERIFIED. Следующая область — A02.S04, реальные BM/Composite/Profile/Surface/GDL. Статусы и evidence читаются из единого реестра.

Сохранён единственный Project Accelerator → Semantic Brief/Spatial/PLP → Authored Native Plan → BIM Graph → SceneWriter → Tapir → typed readback. Действующие исходники и выполненные задачи не переписывать.

## Последовательные этапы

| Этап | Задачи в существующем реестре | Критерий ГОТОВО |
| --- | --- | --- |
| 1. Ядро | A02.S01/S03 и A03.S01 уже DONE; A03.S02 → A03.S03 и A03.S04 → A08.S04 | Связное небольшое редактируемое здание из задания, материалы/этажи/host/GUID/геометрия readback; реальная инкрементальная правка без дублей; сохранение и повторное чтение. Четыре элемента недостаточны |
| 2. Геометрия | A09.S01 после A08.S04 | Native dump, связность, стыки, XYZ, host и фактические 3D ошибки интегрированы в общий цикл |
| 3. Материалы и библиотеки | A02.S04 после A09.S01 | Реальные BM/Composite/Profile/Surface и выбранные GDL/CSE/PLP применяются и проверяются в AC29 |
| 4. Конструктив и расчёты | A04.S01–S03 → A05.S01–S03 | Узлы и расчётные результаты связаны с BIM с проверенными входами, нормами и уровнем подтверждения |
| 5. MEP | A06.S01 → S02 | Native команды, оборудование, маршруты, проходки и междисциплинарная координация подтверждены |
| 6. Ускорение | A10.S01 | Конкретный baseline, ограничения и измеримое улучшение без регрессии точности |
| 7. Выпуск | A07.S01–S03 → A08.S01/S02 | Чертежи, ведомости, нормативная проверка и IFC/экспорт соответствуют модели; полнота проекта отдельно от ядра |
| Адаптация AC30 | A08.S03 → A08.S05 | После установки AC30 адаптация того же ядра, отдельная проверка совместимости |

Префикс всех A/S в таблице: APA-P70. DONE/IN_PROGRESS, старые ID, work_key, evidence и чужие leases сохраняются. Добавленные подзадачи покрывают отдельные отсутствовавшие результаты: полнота типов здания, приёмка ядра до выпуска, геометрия, применение реальных библиотек, измеримая оптимизация и AC30. Нормативный минимум остаётся входным ограничением; полное исследование нормативов не блокирует первый рабочий BIM.

## Карта повторного использования

Полные поля каталога находятся в `PROJECT_PLAN.json.component_catalog`: источник → целевой модуль → S-ID → зависимости → приёмка, уровни подтверждения и ограничения. Начальный каталог не объявлен полной проверкой исторических веток. Завершение инвентаризации остаётся в существующих A01.S02 / P50.A02.S01, но не вытесняет ядро.

| Компонент | Существующий источник | Модуль | Внедрение | Зависимости | Приёмка |
| --- | --- | --- | --- | --- | --- |
| Project Accelerator | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_project_accelerator.py | entrypoint | APA-P70.A03.S02 | APA-P70.A03.S01 | Compile brief through existing entry; no second executor |
| Semantic Brief | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_semantic_brief.py | semantic input | APA-P70.A03.S02 | APA-P70.A03.S01 | Real stories and hard constraints retained |
| Semantic Spatial | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_semantic_spatial.py | authored geometry | APA-P70.A03.S02 | APA-P70.A03.S01 | Authored room/axis/bearing/load-path identity retained |
| Project Library Pack / CSE | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_project_library_pack.py | construction resolver | APA-P70.A02.S04 | APA-P70.A09.S01 | Verified selection and real attribute readback |
| Authored Native Plan | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_authored_native_plan.py | authoring adapter | APA-P70.A03.S02 | APA-P70.A03.S01 | Original graph/writer receives approved authored plan |
| BIM Graph | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_bim_graph.py | dependency DAG | APA-P70.A03.S04 | APA-P70.A03.S02 | Hosted openings use verified wall GUIDs and ordering |
| SceneWriter / SQLite | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_scene_run.py | native transaction journal | APA-P70.A03.S02 | APA-P70.A03.S01 | Exact target, pinned hash, intent before every write, no blind replay |
| Native MVP / write cycles | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_executor.py | native donor adapters | APA-P70.A03.S04 | APA-P70.A03.S02 | Supported columns/doors/windows reused with typed readback |
| Template Builder | https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/scripts/archicad_template_builder.py | project attributes | APA-P70.A02.S04 | APA-P70.A09.S01 | BM/Composite/Profile/Surface identities resolved independently |
| Tapir / Python JSON | docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-163950Z-tapir-compat-6f29/REPORT.md | transport | APA-P70.A03.S02 | APA-P70.A03.S01 | Installed version/command schema and typed readback verified |
| Native Model Dump / AC29 geometry | docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md | geometry | APA-P70.A09.S01 | APA-P70.A08.S04 | Real XYZ/3D bodies and failure cases verified |
| NetworkX / Shapely | docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md | geometry | APA-P70.A09.S01 | APA-P70.A08.S04 | Graph/2D predicates used within declared scope; 3D proven separately |
| Roof / Shell / Morph / Openings / SEO | docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-143940Z-opening-shell-geom/REPORT.md | geometry | APA-P70.A09.S01 | APA-P70.A08.S04 | Native capabilities adapted individually; required unsupported scope blocks |
| GDL / ТЕХНОНИКОЛЬ / manufacturer catalogs | https://github.com/dvikt33-ux/safe-bim-layer/pull/20 | library | APA-P70.A02.S04 | APA-P70.A09.S01 | Unicode, stable library identity, rights and target-version runtime verified |
| Details v2.12 / constructive nodes | https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12 | constructive | APA-P70.A04.S01 | APA-P70.A03.S01, APA-P70.A02.S04 | Applicability/source and BIM attachment verified; found detail not automatically approved |
| SAM / SAF / structural handoff | https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md | engineering | APA-P70.A05.S01 | APA-P70.A03.S01, APA-P70.A02.S02, APA-P70.A04.S03 | Verified inputs, solver, loads, norms and BIM provenance; connectivity not carrying capacity |
| Native MEP Designer | docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md | MEP | APA-P70.A06.S01 | APA-P70.A03.S02, APA-P70.A02.S02, APA-P70.A05.S03 | Commands/routes/ports and model coordination proven; UI presence not integration |
| OR-Tools / CP-SAT / batching / caches | https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md | optimization | APA-P70.A10.S01 | APA-P70.A06.S02 | Specific optimization objective/constraints plus measured benefit |
| СП / ГОСТ normative sources | https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md | release | APA-P70.A07.S02 | APA-P70.A07.S01, APA-P70.A05.S03, APA-P70.A06.S02 | Applicable norm/version/source linked to verified check |
| IFC / openBIM / MCP / Twinmotion | https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md | export | APA-P70.A07.S03 | APA-P70.A07.S02 | Required export/sync checked against native model; unsupported scope explicit |
| Archived branches / alternate implementations / source71 | https://github.com/dvikt33-ux/safe-bim-layer/blob/6a8abe2ac4e5a3e664c94bc9e71f9e15da943e27/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json | candidate donors | APA-P70.A01.S02 | APA-P70.A01.S01, APA-P50.A01.S01 | Keep source provenance; compare measurable advantage before replace/merge |

## Разрешение и доказательства

Прямая инструкция пользователя в текущем чате: «запись в pln разрешаю любую, продолжай». Это разрешает текущую разработку и native-запись; повторное согласование того же воздействия не требуется. Конкретный сценарий привязан к `C:\LocalAI\APA_Isolated_Writer_Test_01.pln`. Смена чужого активного проекта не нужна; APX/main/protected branches этим сообщением не разрешены.

Историческая пользовательская read-only база: порт 19724, 20 элементов, область X 40–50 / Y 40–48 / Z −0,3…6,3 м, LIVE_SPATIAL_CLEARANCE_PASS, native writes 0. Последняя строка clearance приведена пользователем в инструкции; канонический отчёт PR47 ещё содержит NOT_VERIFIED. Перед native-записью заново проверить identity/version/stories/materials/inventory/bounds; отсутствие актуального результата не подменять историческим PASS.

Каждый native call использует существующий SQLite intent-before-write, уникальный operation ID и no-retry при UNKNOWN_OUTCOME. Прочитать GUID, тип, геометрию, отметки, конструкцию/материал и host. Не ослаблять проверку для Composite вместо Basic. Однозначный readback, затем следующая область.

SOURCE_VERIFIED ≠ OFFLINE_PASS ≠ LIVE_PASS ≠ DONE_PUBLISHED. Никаких новых Deep Research, платных model rounds, расписаний или обещаний фоновой работы. Существующие scheduled задачи не перенастраиваются.

## Публикация

План/инструкция публикуются в канонической research-ветке после штатной проверки DAG; повторное чтение трёх файлов и соответствие исходной инструкции обязательны. Только после этого A02.S05 получает DONE_PUBLISHED и резервируется ближайшая допустимая core-задача.
