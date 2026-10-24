# APA R3 — два GH-графа и независимый QA-контракт BUILD-01
**Цикл:** 2026-10-24 14Z (17:00 МСК). **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Роль:** R3 (Rhino 8 / Grasshopper 1 / RhinoCommon / геометрия / IFC / нормы). **Цель:** issue #192, G0→G1→G2. **Тип работы:** SOURCE, без запуска Grasshopper и без записи в Archicad.

## 0. Управляющее поручение и итог
Прочитан A5 13Z (`audit-a5-2026-10-24T13Z-BUILD01-TRIAD-DISPATCH.md`, blob `71e752a11e8324086d9ac2d9cec98de01bed8204`): **R3-14A** — два минимальных GH-графа с точными units/tolerance/orientation/story, входами/выходами, отказными случаями; **R3-14B** — независимый QA BREP/IFC/IDS/СП. Также прочитаны issue #192, каноническая очередь и immutable исходники PR74. Новые A5-поручения 14Z ещё не наступили: **PENDING**, не подменять их предположениями.

**Результат R3:** подготовлены две проектные схемы GH-BASE и GH-OPT и матрица QA, привязанные к **фактическим полям** существующего PR74. Это **спецификации для сборки GH-определений**, а не созданные или исполненные `.gh`-файлы. Готовый GH DataTree→`apa-authored-project/1` сериализатор в изученных исходниках **NOT_FOUND**; нельзя выдавать визуальный граф за автоматический writer. Единственный разрешённый native writer — существующий APA SceneWriter. Встроенные компоненты GH не требуют новых плагинов; сам Rhino 8 лицензируется отдельно. Graphisoft GC29 build3000 совместим с Rhino 8 по официальному каталогу, но его компоненты Create являются **вторым writer** при параллельной записи с APA и в этих графах **отключены/не подключаются**.

## 1. GH-BASE: два этажа, стены, перекрытия, простая кровля, окно и дверь (P0)
**Назначение:** вычислить геометрию, проверить входные инварианты, подготовить *источники данных* для существующего authored-intent PR74; **никакого Bake, Push, Archicad Create или записи файлов**.

### 1.1 Входные параметры (учебный пример, НЕ согласованная архитектура)
| Ключ | Пример | Единицы / смысл | Обязательный guard |
|---|---|---|---|
| `W`, `D` | 12.0, 8.0 | метры, габарит прямоугольника | конечные >0; конкретные размеры согласовать |
| `Z0`, `Z1` | 0.0, 3.2 | метры, **абсолютные** отметки этажей | `Z1>Z0`; сопоставить с реальным GetStories |
| `H0`, `H1` | 3.2, 3.2 | метры, высоты этажей | PR74: 2.4≤H≤4.5; `Z0+H0=Z1` с исходным guard 1e-5 м |
| `T_slab`, `T_wall` | 0.20, 0.20 | метры, толщина | положительные, материал/структура в AC обязательны |
| `roof_eave_Z`, `roof_angle` | 6.4, 0.05 | абсолютный Z, угол **в радианах в контракте примера PR74** | проверить знак/единицы в локальной Tapir schema; не брать уклон только из Favorite |
| `origin_XY` | `UNRESOLVED` | абсолютные координаты scratch PLN | **не подставлять** 0,0 или исторические координаты без утверждённого свободного участка |
| `story_native_index` | `UNRESOLVED` | реальный index из GetStories, не GH path | G0 required; индекс 0/1 в примере — не runtime факт |
| `material_guid`, `library_parts` | `UNRESOLVED` | реальные GUID атрибутов / доступные библиотеки | GetFavorites/attributes/libraries; иначе STOP |
| `units`, `abs_tol`, `angle_tol` | `meters`, `UNRESOLVED`, `UNRESOLVED` | Rhino model units + tolerances | взять из G0, **не навязывать произвольное epsilon** |

**Примечание:** числа здесь только тестовый вход для **проектной схемы**, не готовое разрешение на сборку. Rhino tolerance задаётся в единицах Rhino; изменение units может масштабировать модель. PR74 `storyHeights` и `brief.stories[].level` проверяются в метрах, а `CreateSlabs.level` в существующем authored compiler — **абсолютный Z**. Параметры `zCoordinate` у других типов нельзя приравнивать к этому полю без проверки команды.

### 1.2 Узлы и связи (штатный Grasshopper 1)
`Number Slider / Panel (W,D,Z0,Z1,H,T)` → `Construct Point` для четырёх углов `(X,Y,Z0)` → `Polyline` (замкнуть) → `Area` (ожидаемая площадь `W×D`) и `Boundary Surfaces` (preview перекрытия) → `Move` по `Unit Z × (Z1−Z0)` для второго уровня → четыре `Line`/осевых отрезка на каждом этаже → `Length` (проверка ненулевых стен). Для простой кровли: `Construct Point` + `Polyline` планового контура и отдельно `Line` pivot, `roof_eave_Z`, `roof_angle` → численная проверка знака/уклона и контура. `Panel` фиксирует табличные параметры для существующего authored JSON; `Data Tree` можно использовать для группировки, но `{story;type;ordinal}` — **не** native GUID и не стабильный ключ при перестройке ветвей.

**Семантические ключи** (фиксированные строки, не пути дерева): `L0`, `L1`; `wall-south-L0`, `wall-south-L1`; `slab-L0`, `slab-L1`; `roof-simple-L1`; `door-entry-L0`, `window-east-L0`. Геометрические точки в локальной системе преобразуются в абсолютные координаты **только после** G0 origin/bindings. Все контуры должны иметь заданный обход, непересекающиеся рёбра, конечные координаты; GH-превью не доказывает AC native BIM.

### 1.3 Фактический контракт PR74 (не придуманная новая схема)
В `scripts/archicad_project_accelerator.py` (immutable `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, строки 262–276) вход `compile_authored_intent` требует **строго**:
`schemaVersion="apa-authored-project/1"`, `projectId`, `units="meters"`, `brief`, `cseCandidate`, `layout`, `storyHeights`; дополнительные поля только из текущего allowlist (например, `nativeComponents`, `wallBasicMaterialName`). **Нельзя добавить `source_key`, `roof_facets`, `slab_holes` на верхний уровень и считать, что компилятор их примет.**

`scripts/archicad_authored_native_plan.py` строки 105–111 реально формирует `CreateSlabs` из `level`, `floorIndex`, `thickness`, `referencePlaneLocation="Top"`, `polygonCoordinates`; **внутренних контуров здесь нет**. Стены создаются через `BUILD.wall(p1,p2,native,wall_height,thickness)` на строках 112–119. `storyHeights` ограничены 2.4–4.5 м; межэтажная отметка сверяется с высотой (строки 33–43).

В `scripts/archicad_project_accelerator.py` строки 294–303 `nativeComponents` допускает `CreateColumns/Doors/Windows/Walls/Roofs` и требует для Roof **pivotLine + Basic + buildingMaterialId**; Roof без pivotLine будет отвергнут, даже если upstream Tapir умеет Multi-plane. В `examples/accelerator/model-first-building.json` строки 235–330 hosted двери/окна связываются через `ownerWallId.guid.$createdGuid`, `centerOffset`, `sillHeight`, `width`, `height`; это **образец существующей схемы**, а не доказательство библиотечного part на ноутбуке.

**Выход GH-BASE для I4:** таблицы `story_levels`, `bearing_lines`, `slab_outer_polygons`, `roof_single_outline_pivot_angle`, `hosted_openings`, `attribute_requirements`, `geometry_checks` (как спецификация, не новая JSON API). **Реальный вход PR74:** только утверждённый `apa-authored-project/1` с существующими `brief/layout/storyHeights/nativeComponents`. Автоматическая сериализация таблиц GH в этот объект **NOT_FOUND**; I4 обязан обозначить этот разрыв, а не дописать новый router.

### 1.4 Отрицательные сценарии GH-BASE (не исполнены)
- **N1:** `H0=2.3` м → ожидаемый отказ PR74 `UNSUPPORTED_AUTHORED_STORY_HEIGHT` (исходный guard 2.4≤H≤4.5); GH должен пометить `BLOCKED_HEIGHT` ещё до компиляции.
- **N2:** `Z0=0, H0=3.2, Z1=3.1` → `STORY_HEIGHT_INCONSISTENT_WITH_LEVELS`; не компенсировать «подгонкой» GH Z.
- **N3:** `host_source_key=wall-missing-L0` для окна → отсутствует `$createdGuid`-цель; ожидается отказ связности/host binding, **точный текст ошибки не утверждается** без G1.
- **N4:** `material_guid=UNRESOLVED` или `origin_XY=UNRESOLVED` → G0 STOP, не выпускать нативное задание и не подставлять дефолт.

**Критерий ГОТОВО GH-BASE (будущий):** реальный `.gh` с версиями/хешем, два этажа с проверенными геометрическими инвариантами, подтверждённый PR74 input и фактический G1 offline compiler receipt. **Сейчас: SOURCE_SPEC_ONLY.**

## 2. GH-OPT: Slab с отверстием + двухскатная кровля как 2 плоскости (P1, не блокирует G1)
**Цель:** исследовать геометрические ограничения без включения второго writer в рабочий PLN.

### 2.1 Входные данные и узлы
**Перекрытие:** outer XY-loop `(0,0)→(12,0)→(12,8)→(0,8)`, inner XY-loop `(4,2)→(6,2)→(6,4)→(4,4)` при общем Z. Замкнуть оба `Polyline`, проверить `Curve Closed`, плоскость, вложенность, самопересечения, обход (outer CCW / inner CW относительно +Z), `Boundary Surfaces` с **обоими** контурами в согласованной ветви. Проверить, что результат — одна обрезанная planar surface **с внутренним loop**, а не две отдельные поверхности. Ожидаемая площадь `96−4=92 м²`; `Area` сравнивать с ожидаемой только в согласованных единицах и допусках. В официальном GC29 компонент Slab может принимать горизонтальную Surface с отверстиями, но **не использовать GC29 Slab Create** одновременно с APA SceneWriter. Поле `polygonCoordinates` в проверенном authored compiler содержит только наружный контур, поэтому `GH→PR74 slab_holes` = **NOT_FOUND**.

**Кровля:** план 12×8 м, `eave_Z=6.4`, `ridge_Z=8.0`, линия конька `y=4`, `x=0..12`. Фасет F1: `(0,0,6.4),(12,0,6.4),(12,4,8.0),(0,4,8.0)`; F2: `(0,4,8.0),(12,4,8.0),(12,8,6.4),(0,8,6.4)`. На каждом фасете `Construct Point→Polyline→Boundary Surfaces`, проверка `planar`, нормали, замыкания, совпадения общего ребра, площади и `atan((8.0−6.4)/4)=21.8014°`. Внешние границы/уклоны согласовать с проектом; пример **не** нативная сборка. Официальный GC29 Roof создаёт Single-plane Roof из планарного полигона (включая наклон), но это отдельный writer. Для APA PR74 требуется **другой** typed контракт `polygonCoordinates XY + pivotLine + level + angle + Basic + material`; простая передача 3D GH Brep вместо этого не предусмотрена. Две отдельные native Roof ≠ один Multi-plane Roof. `GH→PR74 multi-roof-from-Brep` = **NOT_FOUND**.

**Контракт GH-OPT для I4:** `slab_outer_loop`, `slab_inner_loops`, `roof_facet_id`, `facet_polygon_xyz`, `facet_plane`, `facet_normal`, `facet_shared_edge_ids`, `ridge/eave_z`, `roof_pitch_rad`, `geometry_status`. Это **read-only QA output** и не объявляется принимаемым PR74 payload.

### 2.2 Отрицательные сценарии GH-OPT (не исполнены)
- **N5:** внутренний контур пересекает outer или касается его → `HOLE_INVALID`; не считать площадь 92 м² и не передавать на запись.
- **N6:** один угол фасета смещён по Z так, что четыре точки не компланарны → `NON_PLANAR_FACET`; не преобразовывать молча в mesh/морф.
- **N7:** F1/F2 имеют разрыв конька больше согласованного `abs_tol` → `RIDGE_GAP`; не считать две поверхности замкнутым BREP solid.
- **N8:** Rhino mm, а authored intent `units="meters"` без явного масштаба → `UNIT_MISMATCH`; 12 000 мм ≠ 12 000 м.

**Критерий ГОТОВО GH-OPT (будущий):** сохранённый `.gh`, фактические outputs и негативные кейсы, подтверждённая ориентация и топология; отдельно — доказанный existing native contract. Сейчас **SOURCE_SPEC_ONLY / PR74_HOLES_AND_POLYROOF_NOT_FOUND**.

## 3. QA-контракт: геометрия, native BIM, IFC, IDS, СП — независимые уровни
| Уровень / инструмент | Инварианты | Допустимый статус и ограничения |
|---|---|---|
| GH/RhinoCommon до записи | units/tolerance, finite XYZ, closed curves, planar loops, non-self-intersect, outer/inner nesting, winding, roof normals/shared edges, length/area, bbox, solid topology **только для объёмных Brep** | GEOMETRY_PRECHECK; `Brep.IsSolid` не требовать от одиночной planar surface; не BIM |
| Existing APA BIM Graph / PR74 offline | `apa-authored-project/1`, реальные `storyBindings`, `sourcePlanHash`, DAG/toposort, `$createdGuid` host dependencies, schema/attribute/footprint guards | OFFLINE_PASS только после **фактического** G1 запуска; SOURCE ≠ OFFLINE |
| Tapir + AC native readback | фактический Wall/Slab/Roof/Window/Door GUID и type, этаж/homeStory, host, материал/композит, толщина, параметры, дочерние элементы, normalized BREP/geometry signature | Только после разрешённого G3 и G4 Save/Close/Reopen; `GetDetailsOfElements`/инвентаризация по установленной схеме; `GUID` не заменять GH path |
| IfcOpenShell (после отдельного экспорта) | IfcWall/IfcSlab/IfcRoof/IfcDoor/IfcWindow, IfcBuildingStorey, spatial containment, IfcRelVoidsElement/IfcRelFillsElement, материалы, IFC GlobalId, bbox/объём при доступной геометрии | IFC_CHECK; возможны потери экспорта, `IFC GlobalId` не равен автоматически AC internal GUID |
| IfcTester / IDS | проверка **информационных** требований: классификация, атрибуты, свойства, материалы, отношения/количества согласно применимому IDS | IDS_INFO_CHECK; **не** геометрический и не полный нормативный сертификат |
| Нормативы СП и инженерная экспертиза | применимый документ/редакция/пункт, проверяемый параметр, единицы, порог, допуск, доказательство и ответственный; ширины/высоты/уклоны можно вычислить из геометрии при наличии правила | `RULE_UNSPECIFIED`, если нет подтверждённого пункта/порога; **не** писать `COMPLIANT` без экспертизы |

**Сравнение геометрии:** до и после разрешённого native Save/Open фиксировать одинаковую систему координат, единицы и допуски; сравнивать состав элементов, координаты, площади, bbox, геометрические сигнатуры и топологию с учётом допустимой сегментации. Не сравнивать точное совпадение control points Rhino NURBS с AC mesh/BREP без проверенного преобразования. Не считать IFC-геометрию первичным native readback.

## 4. Контрааудиты R3
**CA-R3-14A / инженерная семантика:** GC29 Slab с отверстиями и GC29 Roof — действительно native Archicad *при работе собственного GC writer*, но параллельный APA SceneWriter не имеет доказанного transaction/ownership с GC. GH-BASE не включает GC Create; GH-OPT остаётся исследованием. PR74 `nativeComponents` не содержит произвольных `slab_holes`/3D `roof_facets`. Отсутствие bridge подтверждено для **проверенного immutable PR74**, но не доказывает отсутствия во всех внешних ветках: статус **NOT_FOUND_IN_CHECKED_PR74**, дальнейший поиск — R2.

**CA-R3-14B / метрология и нормативы:** GH tree branch path не является persistent BIM identity; `IsSolid=true` для замкнутого Brep не гарантирует корректность native Wall/Slab; `Boundary Surfaces` может выдать неверную структуру при неправильном grouping loops; Roof F1/F2 — две открытые поверхности, поэтому нельзя требовать `IsSolid` для них. В IFC IDS не заменяет проверку BREP, противопожарных/доступностных норм и инженерное заключение. Все отрицательные кейсы — **спецификации**, не реальные PASS.

## 5. Реестр 16 фактически прочитанных SOURCE-оснований
S01 — A5 13Z, blob `71e752a11e8324086d9ac2d9cec98de01bed8204` — поручение R3-14A/B, gates.
S02 — issue #192: https://github.com/dvikt33-ux/safe-bim-layer/issues/192 — критерии G0–G5, один writer.
S03 — NEXT_RESEARCH_PRIORITIES.md, blob `6f074693360231c5cb42ada815984a6b0dd504c0` — приоритет BUILD-01.
S04 — PR74 `scripts/archicad_project_accelerator.py`, blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`, строки 262–303 — authored contract/guards.
S05 — PR74 `scripts/archicad_authored_native_plan.py`, blob `f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7d`, строки 33–43 и 105–119 — stories/Slab/Wall.
S06 — PR74 `scripts/archicad_connected_components.py`, blob `c5a99f59a90369ff622807574677cf11ca0a2225`, строки 184–196 — Roof native verifier SinglePlane.
S07 — PR74 `examples/accelerator/model-first-building.json`, blob `e192fbb31bc872d751c41aa7132f0a4981755051`, строки 235–330 — hosted opening example.
S08 — Graphisoft official LC29 build3000 Rhino8: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ .
S09 — Graphisoft GC29 Slab/ Roof components, geometry limits: https://help.graphisoft.com/AC/29/INT/GC.pdf .
S10 — McNeel Rhino8 units/tolerance: https://docs.mcneel.com/rhino/8/help/en-us/documentproperties/units.htm .
S11 — McNeel Grasshopper DataTree/GH_Path: https://developer.rhino3d.com/en/guides/rhinopython/grasshopper-datatrees-and-python/ .
S12 — McNeel RhinoCommon geometry structures: https://developer.rhino3d.com/en/guides/grasshopper/csharp-essentials/3-rhinocommon-geometry/ .
S13 — IfcOpenShell IfcTester docs: https://docs.ifcopenshell.org/ifctester.html .
S14 — Graphisoft native Slab holes: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-128.htm .
S15 — Graphisoft native Roof holes: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-83.htm .
S16 — Graphisoft crop to roof is not associative: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-88.htm .
**Примечание:** S01–S16 = 16 конкретных прочитанных материалов/файлов; не заявляется 20–30 новых независимых проверок или тестов. Официальная документация и исходный код — SOURCE, а не INSTALLED.

## 6. Передача I4 и статусы
**I4-P0-01:** использовать **строгий** PR74 `apa-authored-project/1` для базового двухэтажного G1; принять от R3 только геометрическую спецификацию, не выдумывать GH→PR74 adapter. **ГОТОВО:** один approved fixture/input и реальная offline команда/receipt; если нет — `GH_BRIDGE_NOT_FOUND`.
**I4-P0-02:** в G0 получить `Rhino8 SR, units, abs_tol, angle_tol, GH .gh hash, AC stories/origin, Tapir APX/schema, material/library bindings`. **ГОТОВО:** read-only manifest; без него блокировать сериализацию.
**I4-P1-03:** Slab holes и MultiPlane Roof оставить optional; существующий PR74 принимает один наружный slab polygon и SinglePlane roof с pivotLine. **ГОТОВО:** подтверждённая матрица supported/NOT_FOUND и запрет второго writer.
**I4-P1-04:** QA-таблицу встроить в G4 с отдельными вердиктами `GH_GEOMETRY`, `AC_NATIVE`, `IFC_STRUCTURE`, `IDS_INFORMATION`, `NORMATIVE_REVIEW`; отсутствие любой необходимой ступени = не ACCEPTED.
**I4-P1-05:** проверить отрицательные кейсы N1–N8 **только в разрешённом будущем OFFLINE**; пока не писать PASS.

**Статусы текущего запуска:** SOURCE = 16 прочитанных оснований + 2 GH-спецификации + QA-контракт + 2 внутренних контрааудита. OFFLINE = 0 новых выполненных; BUILD = 0; INSTALLED = NOT_VERIFIED; LIVE = 0; ACCEPTED = 0. `G0=BLOCKED_RUNTIME`; `G1=NOT_RUN`; `G2=SOURCE_PARTIAL`; `G3=NOT_AUTHORIZED`; `G4/G5=NOT_RUN`. **NOT_FOUND:** готовый GH→PR74 typed bridge в проверенном immutable PR74; Slab holes через текущий authored compiler; native MultiPlane Roof через текущий SinglePlane verifier; трёхсторонний атомарный sync/rollback; автоматическая полная проверка СП. **MODEL_MODE_NOT_VERIFIABLE.**

**Запреты соблюдены:** main, код, PLN/APX, установки, LIVE, Work/Codex/Arena, платные API, merge не изменялись/не выполнялись. Каноническая очередь и PROJECT_PLAN rev182 только читались.
