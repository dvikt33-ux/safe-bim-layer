# APA — сборка существующего ускорителя (вместо повторной разработки)

**Статус:** исполнимый план интеграции / ни одна live-запись не объявляется проверенной.  
**Единственный управляющий реестр:** [PROJECT_PLAN.json](PROJECT_PLAN.json), S-ID из APA-P70.  
**Цель:** дорабатывать один общий Fast Project Compiler для Archicad 29, а не вводить отдельный генератор ИЖС, новый SceneWriter, новый контроллер или искусственные циклы. См. [Full Cycle Goal](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md) и [Checkpoint 37 §5](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md).

> **Рабочие этапы выпуска и приёмочные ворота:** [APA_ACCELERATOR_DELIVERY_ROADMAP_20261011.md](APA_ACCELERATOR_DELIVERY_ROADMAP_20261011.md). Это конкретизация данного интеграционного плана для доставки MVP и полного цикла; `PROJECT_PLAN.json` остаётся единственным управляющим реестром, а дорожная карта ждёт независимого аудита.

## 1. Реально существующие блоки, подключать их, а не переписывать

| Роль | Использовать существующий источник | Состояние / граница |
|---|---|---|
| Единственная точка входа | [archicad_project_accelerator.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/scripts/archicad_project_accelerator.py), PR #16, [PR #34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34) | Компиляция и синтетическое выполнение; PR #34: 106/106 offline CI. Не считать live |
| Проверка возможностей и источников | [archicad_accelerator_integration.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/scripts/archicad_accelerator_integration.py), [capability-registry.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/schemas/accelerator/capability-registry.json) | Реестр провайдеров и проверка покрытия; статусы провайдеров различаются |
| Единственный BIM-граф | [archicad_bim_graph.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/scripts/archicad_bim_graph.py) | Проверяет команды, host GUID, зависимости, порядок и коллизии проёмов offline |
| Единственная защищённая запись | [archicad_scene_run.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/scripts/archicad_scene_run.py) | Проверка PLN, журнал SQLite, no-retry, readback; PR #34 расширяет схему; live новой схемы НЕ доказан |
| Уже написанные нативные писатели | [archicad_executor.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/working-archicad-mvp/scripts/archicad_executor.py), `scripts/archicad_write_cycles/`; [series178_typical_floor.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/scripts/archicad_series178_typical_floor.py) | Есть стены, slab modify/material и проектные сборщики; не предполагать универсальность Series178 |
| Этажи, атрибуты и шаблон | [archicad_template_builder.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/scripts/archicad_template_builder.py) + штатные AC29 Favorites / Composites / Profiles / GDL | Подключить к тому же плану BIM-графа, не писать вторую базу материалов |
| Конструктивные системы и узлы | [details/v2.12](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [PLP contract](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [CSE checkpoint](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md) | 1215 записей узлов — не 1215 одобренных решений; требуется применимость/источники и узловые пробелы |
| Инженерия / выпуск | Штатные MEP/SAM/SAF, AC29 views, schedules, IFC; [full-cycle checkpoint](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md) | Штатные механизмы и исследованные маршруты; не выдавать за завершённую интеграцию |

**Правило выбора:** прежде чем создавать новый модуль, указать исходный existing entrypoint, доказать конкретный недостающий контракт и показать, почему его нельзя закрыть адаптером существующего кода. Работа «написать заново, потому что проще» не допускается.

## 2. Последовательность соединений (не отдельные циклы и не новая очередь)

Существующие S-ID **остаются** единственной очередью. Каждое соединение фиксируется в той же задаче со ссылкой на commit, CI, readback и версию PLN, если live был разрешён.

| Приоритет | Существующие S-ID | Недостающее соединение | Операционный критерий |
|---|---|---|---|
| **Сейчас** | P70.A01.S01 / P70.A01.S03 | Карта повторного использования; один публичный вход → capability selection → BIM Graph → SceneWriter; сопоставление проверенных исторических веток | Нет нового диспетчера / графа / писателя; раскрыта реальная граница PR #16 и #34 |
| **Следом** | P70.A02.S01 / P70.A02.S03 | Реальное разрешение этажей, атрибутов, Favorites/Composites, отбор малого CSE/PLP; нормативный минимум как входные ограничения | Нет фиктивного «0 этажа»; выбранные реальные материалы и слои с источниками, неизвестное помечено NOT_VERIFIED |
| **Сквозная модель** | P70.A03.S01 / P70.A03.S02 / P70.A03.S03 | Семантика помещений и несущих линий → нативная BIM-модель; повторное использование старых writer/roof/stair/slab циклов; readback и сохранение редактируемости | Геометрия не раздроблена; родительские стены, связи проёмов, этажи, GUID/материалы проверены; не только 25 абстрактных элементов |
| **Реальные детали** | P70.A04.S01–S03 | Привязка применимых узлов CSE/v2.12, окна, облицовка, опирания, фундамент, стропила и примыкания к native BIM | Узел не «APPROVED», пока нет условий применимости, источника и соответствующих проверок |
| **Инженерный контур** | P70.A05 / A06 | Расчётная схема, инженерный solver по наличию, передача/возврат, штатные MEP; изменённые связи пересчитываются | Реальные расчёты и provenance; если solver/лицензия недоступны — BLOCKED, не подмена самодельным FEM |
| **Выпуск** | P70.A07 / A08 | Native views, спецификации, IFC/PDF, проверка и reopen отдельного тестового PLN | Единство модели и документации, видны открытые нормативные и инженерные ограничения |

**Нет искусственного требования закрыть всю нормативную базу до первой сквозной модели**. Но нельзя создавать статус «строительно пригодно» без подтверждённых применимых требований и расчётов. Уточнённые зависимости находятся в `PROJECT_PLAN.json`.

## 3. Почему 25 операций PR #34 недостаточно

Доказанный только synthetic пример: 12 Walls, 2 Slabs, 5 Doors, 6 Windows = 25 native create operations. Отсутствуют крыша, стропила, фундамент, лестница, зоны, конструктивные материалы и слои, армопояса/перемычки, опирания, узлы и расчёт. **25 операций — проверка проводки, не эталон реального здания.** Не увеличивать счётчик элементов ради числа: непрерывная стена должна оставаться одним редактируемым Wall, состав — native Composite/Favorite/Profile; деталь параметрическая или native node в требуемой области.

## 4. Конкретное ближайшее исполнение

1. Выполнить `P70.A01.S01` как инвентаризацию **реально исполняемого** кода, API/команд и подтверждённых входных файлов; опираться на source SHA, PR #16/#34, Native MVP, серии и CSE.
2. Подключить `archicad_executor.py` / `archicad_template_builder.py` через маленькие адаптеры к **одному** existing dispatcher + SceneWriter, без переноса всех алгоритмов в новый гигантский скрипт.
3. Подтвердить одной сквозной проверкой: input → resolved stories/attributes/CSE → BIM DAG → safe executor → GUID/material/host/story readback → сохранение доказательств в GitHub. Synthetic и LIVE не смешивать.
4. Следующая функциональная поставка — уже существующие roof, slab material, stair и детали; делать только то, что действительно не покрыто current code.
5. Сохранять в реестр недостающие контракты, а не дублирующие планы. Никакого отдельного «генератора дома».

## 5. Разрешение на тесты

Пользователь выразил в чате разрешение на испытание 2026-10-11. Оно **не означает разрешение менять произвольный PLN**: нужен отдельный идентифицированный disposable PLN, свежая проверка identity/версии/этажей, явный запуск локальным исполнителем, no auto retries и сохранённые журналы. Protected `APA_Pavilion_MVP_SUCCESS.pln`, ранее tested PLN и main/master остаются без изменений без отдельного точного разрешения. GitHub-коннектор не имеет доступа к локальному Archicad, поэтому live не заявлять без исполнения на Windows.

## 6. Приёмка

- **SOURCE/CI:** source SHA, команда теста, GitHub CI, список реально вызываемых adapters.
- **LIVE:** точный PLN, согласованный `GetStories`, GUID-материал-слои, hash geometry, типы, host, native readback, saved/reopened evidence.
- **ENGINEERING:** нормы/применимость CSE, конструктивные расчёты, нерешённые блокировки.
- **DONE:** только после acceptance каждого S-ID; все P/A DONE лишь при завершении всех обязательных подзадач.

Нет отчёта без GitHub commit/readback. Не запускать 12-элементный pavilion regression повторно как отдельную задачу без реальной регрессии.
