# APA / Archicad 29 — ARCHITEChTURES и легально переиспользуемый код архитектурных планировщиков

**Дата исследования:** 2026-10-15 · **Тип:** SOURCE_AUDIT + CANDIDATE_RESEARCH · **Статус:** NOT_INSTALLED / NOT_TESTED_IN_APA · **Публикация:** только выделенная исследовательская ветка / draft PR #78. Этот документ не изменяет программу ускорителя и исходные PLN.

## 1. Что действительно есть у ARCHITEChTURES

Первоисточники:
- https://architechtures.com/en/ — параметрическое проектирование, площади, DXF/IFC/XLSX; основная типология: жилые многоквартирные объекты, некоторые коммерческие помещения, парковки.
- https://architechtures.com/en/pricing — Pro **$49/мес. при годовой оплате**, 7-дневная пробная версия, выгрузки DXF/IFC/XLSX; Business **$294/мес. при годовой оплате**. Цены на момент исследования.
- https://architechtures.com/en/blog/posts/t2-overview-of-the-platform — раздельные «design criteria», «target areas», минимальные внутренние размеры; геометрически обязательное ограничение при конфликте **выше** пожелания по целевой площади.
- https://architechtures.com/en/blog/posts/parking-lot-design — зафиксированные вертикальные ядра, перенос structural grid на подземные этажи, автоматическая расстановка парковок, но пандусы доступа и межуровневые рампы задаёт пользователь.
- https://architechtures.com/en/blog/posts/t1-what-is-architechtures — поставщик явно выделяет residential multifamily типологию; ТРЦ с атриумами и проверками российских СП не доказан.

**Результат лицензионной проверки:** проект — платный закрытый сервис; публичного GitHub репозитория с его движком планировки не установлено, публичного бесплатного API для интеграции в APA не найдено. Это **не доказательство полного отсутствия API/закрытых соглашений**. Использовать UX/математический подход как функциональный образец можно, **копировать исходники/скрейпить приватные endpoint'ы/обходить тарифы нельзя**. Для 0 ₽ постоянной работы — `DO_NOT_CONSIDER`.

### Идеи, применимые к нашему ТРЦ

1. **Program constraints:** магазин / галерея / атриум / лифт / лестница / санузел / инженерная зона + ориентировочные/минимальные площади, ширина и допустимые связи.
2. **Hard-before-soft constraints:** ограничения безопасности и норм проектной геометрии отделены от «желательно площадь N» и имеют приоритет в решателе; версия СП/правила отдельно как `NOT_VERIFIED` до экспертизы.
3. **Global structure synchronization:** сетка осей, несущие конструкции и коммуникационные ядра инвариантны между этажами и парковкой. Не подменять оси обычными линиями.
4. **Parking optimization:** вход — габариты участка/подвала + сетка колонн, въезды, пандусы, пожарные проезды, эвакуация; выход — несколько упорядоченных вариантов с числами машиномест и нарушениями.
5. **Variation + scoring:** каждое решение связано с исходными ограничениями, метриками и выбором варианта; не менять элементы без разрешения.
6. **One BIM truth:** этажи/планы/разрезы/3D/IFC и отчёты получают один источник геометрии и при изменении сверяются, а не генерируются независимыми AI-картинками.

## 2. Реальные открытые кодовые базы

| Приоритет изучения | Проект / pinned commit | Проверенная лицензия | Конкретные исходники и функции | Что можно перенести без нового BIM Writer | Ограничения |
|---|---|---|---|---|---|
| **P0** | [ParkSolver](https://github.com/ucalyptus/ParkSolver/tree/73c5dd0bca64636e8e0a36af920a59556b610faa) | [MIT](https://github.com/ucalyptus/ParkSolver/blob/73c5dd0bca64636e8e0a36af920a59556b610faa/LICENSE) | `parksolver/solver/{optimizer,stripe}.py`, `scoring/scorer.py`: перебор вариантов угла и конфигураций; Shapely clip, препятствия, scoring, парковочные места, проезды; Python/GeoJSON | **Парковка ТРЦ** на предварительном геометрическом контуре; выходная геометрия через **существующий APA geometry → SceneWriter**, не доверять встроенному IFC text-export | **v0.1.0, очень молодой проект (2 commits при проверке)**; эвакуация/пожарные нормы РФ/проезды/устойчивость решений в подвалах НЕ подтверждены |
| **P0** | [archit-app](https://github.com/archit-app/archit-app/tree/e2913370845bfe2523c57862a2ef19badbd84056) | [MIT](https://github.com/archit-app/archit-app/blob/e2913370845bfe2523c57862a2ef19badbd84056/LICENSE) | `archit_app/analysis/validate.py`: orphan/duplicate walls, overlap rooms, orphan openings, empty/no-door rooms; `analysis/topology.py`: wall/door adjacency graphs; stable Finding codes | **Независимый offline валидатор** по mapping имеющихся элементов APA; не добавлять второе геометрическое ядро | **v0.7.0 alpha**; схемы классов и метры/adjoining tolerance нужно сопоставить с APA и GUID/Story. Доказанных российских норм нет |
| **P1** | [ifc2plan](https://github.com/datarefinerylab/ifc2plan/tree/613f7661947420df76cbe44d05719e6008354551) | [MIT](https://github.com/datarefinerylab/ifc2plan/blob/613f7661947420df76cbe44d05719e6008354551/LICENSE) | `src/ifc2plan/extract_floor_plans.py`, engine `IfcOpenShell/Trimesh/Shapely`: проекция этажей, PNG, WKT/CSV; `--storey`, `--section-offset` | **Вторичная сверка видов из IFC**, подтверждение структуры помещений/планов после PLN→IFC на копии | Разрез IFC-геометрии не заменяет нативный Archicad разрез, IFC lossiness, незавершённые импорты IFC |
| **P1** | [HarnessBIM](https://github.com/ReverseZoom2151/harnessbim/tree/3035021938cbf01128a619146f01eb2c9081d7e5) | [Apache-2.0](https://github.com/ReverseZoom2151/harnessbim/blob/3035021938cbf01128a619146f01eb2c9081d7e5/LICENSE) | `src/harnessbim/verify/egress.py`, `backends/base.py`: обход графов, оценки эвакуации, typed `Effect` классификация read/additive/destructive/irreversible; отчёты `CheckReport` | Перенести только **принципы bounded checker + failed-to-verify** и при необходимости egress-анализ в существующий read-only QA слой; не устанавливать гигантский второй BIM-агент | **v0.0.1, self-described early-stage**, local LLM generative authoring not proven at frontier quality. **IBC-inspired default egress assumptions — НЕ нормы РФ!** Привязать только к проверенным rule-packs |
| **P1** | [COMPAS IFC](https://github.com/compas-dev/compas_ifc/tree/0daa70547a272302db3d970066b366b569eab106) | [MIT](https://github.com/compas-dev/compas_ifc/blob/0daa70547a272302db3d970066b366b569eab106/LICENSE) | `src/compas_ifc/bim.py`: spatial tree + interaction graph + IFC entity factory; 2.1.0 release metadata, MIT | Оценить как готовую **структурированную IFC view-модель** для анализа зависимостей и relationships вместо повторения IFC-only adapter | Дублирует существующий IfcOpenShell-контур; дополнительная зависимость COMPAS; сначала проверить uncovered gaps |
| **P1** | [TopologicPy](https://github.com/wassimj/topologicpy/tree/aef15b4a503014ed63eb487f91d01ad89c95671b) | [LGPLv3](https://github.com/wassimj/topologicpy/blob/aef15b4a503014ed63eb487f91d01ad89c95671b/LICENSE) | топологические пространства, adjacency/graph и non-manifold spatial analysis | Потенциально сложные атриумы/галереи/инженерная связность | Лицензия и зависимости требуют проверки при распространении установщика; не заменять существующие Shapely/NetworkX/CP-SAT |
| **RESEARCH_ONLY** | [SPOX](https://github.com/benjaminwfriedman/spox/tree/4bb4e14d1d2ad920ba41c6964aa6432e62bc9e6d) | **НЕ НАЙДЕН LICENSE** в проверенном корне | `pyproject.toml` заявляет OR-Tools 9.8–9.11, `README` показывает area bounds, adjacency, exterior access, min dimension и score | Изучать **формулировку** CP-SAT требований и собственноручно писать независимые решения; код не переносить без лицензии/письменного разрешения | Не лицензирован открыто на проверенном рефе; решатель рассчитан на прямоугольные помещения/участки; нет proof интеграции |
| **RESEARCH_ONLY** | [ifc-floorplan](https://github.com/Show2Instruct/ifc-floorplan/tree/ee3fbaccad7b64fccf5d2b54f9549f9680cb740c) | **НЕ НАЙДЕН LICENSE** в проверенном корне | `fp/{band_projection,connectivity}.py` треугольники/сечения, граф дверей и вертикальные связи | Идеи независимой топологии и сравнения 3D→2D; **без копирования кода** | Лицензия не установлена, собственные данные и метрики автора не были воспроизведены |
| **P2** | [ArchiGen](https://github.com/Dropio12/archigen/tree/076d3c039ae8da068828b5bd5508f60e8a0f0d06) | [MIT](https://github.com/Dropio12/archigen/blob/076d3c039ae8da068828b5bd5508f60e8a0f0d06/LICENSE) | `backend/app/main.py` routes `generate/edit/ingest/export/compliance/projects`; multi-service design with LLM/diffusion/Celery/Redis/Neo4j | Можно подсмотреть **JSON-протокол итерационного редактирования**, но почти все нужные функции уже есть в APA | Docker/Node/CUDA/весов > текущего быстрого «подключить готовое»; проверки основаны на Canada/Quebec, не СП |
| **P2** | [GSDiff](https://github.com/SizheHu/GSDiff/tree/a02af021b80eba984228f92f7cf5b6f296cf3725) | [GPL-3.0](https://github.com/SizheHu/GSDiff/blob/a02af021b80eba984228f92f7cf5b6f296cf3725/LICENSE) | графово-диффузионная генерация векторных жилых планов | Исследовательский отдельный inference; может давать эскизную геометрию, **не BIM и не нормативную гарантию** | GPL-3.0 copyleft; dataset RPLAN/LIFULL и веса/скрипты имеют дополнительные условия; 8 GB VRAM / ТРЦ / временные затраты требуют проверки; не встраивать в несвободный установщик без юридической оценки |

**Проверки источников:** GitHub connector прочитал `LICENSE`/ `pyproject.toml`/ `README`/ указанные Python-модули для основных кандидатов; исходники не запускались и не копировались в APA. `Show2Instruct` и `SPOX`: ошибка 404 у `LICENSE`, **это не доказательство отсутствия вообще каких-либо прав**, но до прояснения нет согласия на copying/redistribution. **Описание README и заявленные upstream тесты ≠ наши результаты**.

## 3. Что добавить, а что уже есть (антидублирование)

| Возможность | Уже существующий APA | Реальный incremental gap (не доказанная пустота всего проекта) | Источник |
|---|---|---|---|
| Генерация редактируемого BIM через Archicad | SafeBIM/SceneWriter, Tapir, SDK, GUID/read-back | Другой writer **НЕ НУЖЕН** | Ни один новый |
| CP-SAT и архитектурные ограничения | В проекте применён CP-SAT; были тесты маршрутов и model planning | Полноценная библиотека **room program / hard+soft priorities / multi-floor** требует проверки фактического покрытия, а не переписывания | ARCHITEChTURES UX, SPOX идея (без кода) |
| Парковка по контуру и препятствиям | Готовый полноценный parking optimizer в известных исходниках APA **не подтверждён** | **Первый приоритет на пробную адаптацию**: ParkSolver stripe-angle sweep, вернуть контуры машиномест и проездов в общий геометрический контракт | ParkSolver MIT |
| Проверка планировки | У APA есть модельные проверки и native GUID/readback | Проверить добавочную ценность **проверки топологии помещений и дверей** (не считать это нормативной проверкой) | archit-app MIT |
| Выпуск планов из IFC | IFC контур есть; native Archicad floorplan writer/reader — отдельная система | Независимая диагностика расхождений model/IFC/2D без AI-художественной генерации | ifc2plan MIT |
| Эвакуация и инженерные связи | Graph/MEP/модельные направления запланированы, часть работает | Измерить дополнительный охват read-only checker, **только проверенные российские rule IDs** | HarnessBIM Apache-2.0 |
| BIM entity/relationship graph | IFC и граф знаний существуют | COMPAS IFC только если будет новая необходимая функция, и не усложнит релиз | COMPAS IFC MIT |

## 4. Предложенная быстрая интеграция (без второго ядра)

**A. Геометрический adapt-layer: ParkSolver**

`APA read-only site/parking envelope + columns + fixed cores + ramp reservations + exit/fire-lane masks → Polygon/masks → ParkSolver.solve() (isolated process) → candidate stalls/aisles with score, polygon, allowed revisions → APA geometry validation and normative flags → SceneWriter only after user approval.`

**B. Validator-layer: archit-app**

`APA snapshot read-only → convert to external Room/Wall/Opening/Level DTO → archit_app.analysis.validate() + topology building → stable Findings with source GUID/level → compare against existing APA checks → publish newly detected unique issues.`

**C. Cross-view verification: ifc2plan**

`APA native saved test PLN → existing IFC export → ifc2plan per-storey geometry + PNG/WKT → compare to authoritative APA floor outlines and GUID-derived element inventory → PASS/PARTIAL/NOT_VERIFIED. PNG is a diagnostic projection, never a technical Archicad drawing.`

**D. Egress-checker: HarnessBIM selective, later**

`Existing APA graph / IFC snapshot → selected checker function → route distances, assumptions, error report → compare to verified project-specific SP rule-pack. Never use IBC heuristic defaults to approve Russian egress.`

No automatic install or code merge in current work; this is a **proposed integration sequence**.

## 5. Minimal acceptance experiments (do not burn project time on hundreds of synthetic tests)

**Test once per chosen function**, same target Windows AC29.3001+ and the same disposable project / snapshot; first source-level callable, then real native check only where necessary:
- ParkSolver: 3 deliberately different parking footprints (rectangular, L-shaped, column/ramp obstruction), compare all stalls against obstacles; count capacity, parking aisle connectivity, zero illegal overlaps and unchanged GUIDs of original source.
- archit-app: 4 labelled geometry pathologies (orphan opening, overlapping rooms, duplicate walls, disconnected area) plus one known clean plan. Count newly found true errors, false flags, latency and memory. Native PLN read-only.
- ifc2plan: 2 floors + 1 curved or split-wall edge case with matched IFC; coordinates/areas vs authoritative APA geometry; record if IFC export fidelity prevents conclusion.
- HarnessBIM egress: only after verified Russian project rule-pack, reject undefined/inapplicable rule data and explicitly emit `NOT_VERIFIED`.

**STOP CONDITIONS:** unresolved licenses, changed source hashes, unvalidated geometry, unsupported AC build, mismatch target PLN, unbounded writers, missing mandatory rule; do not automatically fix original elements.

## 6. Decision at this stage

- **Use first (P0 research/POC):** ParkSolver MIT (parking), archit-app MIT (plan QA).
- **Next (P1):** ifc2plan MIT (cross-view), then narrow HarnessBIM checker/COMPAS IFC if new value is measured.
- **Study logic, not code:** ARCHITEChTURES (proprietary), SPOX + ifc-floorplan (no verified license).
- **Not default runtime:** GSDiff GPL and heavy ArchiGen stack; postpone PDF→BIM until after core APA, consistent with existing roadmap.

Status of all proposed integrations **NOT_TESTED**. No artifact in this report establishes native Archicad 29 build/pass. Source research is published for independent audit only, without changing `PROJECT_PLAN.json` or shipping a new installer.
