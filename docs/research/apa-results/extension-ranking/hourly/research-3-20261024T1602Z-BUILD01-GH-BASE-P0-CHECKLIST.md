# APA R3 — BUILD-01: GH-BASE → PR74, минимальный P0-контракт и независимый QA

**Срез:** 24.10.2026, цикл 16Z (19:02 МСК). **Роль:** R3 — Rhino 8 / Grasshopper / RhinoCommon / геометрия / независимый IFC-аудит. **Цель:** [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Режим:** SOURCE; ни GH, ни Archicad на ноутбуке не запускались. **MODEL_MODE_NOT_VERIFIABLE.**

## 1. Принятое поручение A5 и ограничение объёма

Прочитан фактический A5 [15:43Z](audit-a5-20261024T1543Z-BUILD01-G0G1-STRICT-COUNTERAUDIT.md), Git blob `af0ab17e54b556001a47572a5d858e8c9eda76a8`. Задачи **R3-16A** — одна таблица «параметр GH → точное поле authored JSON → единицы → precheck → evidence» для двух этажей, Wall/Slab/SinglePlane Roof/Window/Door; **R3-16B** — ровно пять независимых QA-вердиктов и три критических негативных сценария (wrong Z, missing host, mm↔m). Не расширять GH-OPT, не искать новые плагины вместо закрытия G0/G1, не создавать writer/router.

Прочитан предыдущий [R3 15Z](research-3-20261024T15Z-BUILD01-A5-STRICT-GH-CONTRACT-QA.md), Git blob `ac9a9b8d80def329a29915755603801fa5c98465`. Проверены immutable PR74 `5a3a9201a715a5528c93bed4a5318e2acb32eea7`: `scripts/archicad_project_accelerator.py` blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`; `scripts/archicad_semantic_brief.py` blob `e431016f796bb8052487478dde3b2ed2752e7c00`; `scripts/archicad_semantic_spatial.py` blob `5cfcfa1ee016703b1d2bf672a2af288901c0229d`; `scripts/archicad_authored_native_plan.py` blob `f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7d`; `examples/accelerator/model-first-building.json` blob `e192fbb31bc872d751c41aa7132f0a4981755051`. Это SOURCE по Git, не установленная локальная версия APA.

## 2. Минимальный GH-граф, без записи и без нового формата

**GH-BASE (спецификация, НЕ созданный .gh):** `Number Sliders (W,D,Z0,Z1,H0,H1,t_wall,t_slab,roof_angle,openings)` → `Construct Point` → `Polyline Closed` / `Rectangle` → `Area` / `Line` / `Length` → `Move (Z1-Z0)` → `Panel` со значениями и идентификаторами элементов. Отдельные проверки плоскостности, самопересечения, габарита, комнат, линий опирания и отверстий выполняются **до** ручного заполнения существующего `apa-authored-project/1`. GH DataTree path не является идентификатором Archicad GUID. Никакого `Bake`, `GH Design Create`, Tapir GH Push, экспорта Morph/GDL в рабочий PLN.

**Правило единиц:** `RhinoDoc.ModelUnitSystem`, `ModelAbsoluteTolerance` и `ModelAngleTolerance` сначала фактически прочитать из Rhino 8; PR74 требует `units="meters"`. Если Rhino в миллиметрах, преобразовать числовые координаты ×0.001 **ровно один раз** и записать коэффициент в evidence. Порог согласования этажей 1e-5 м — guard PR74, а не нормативный строительный допуск.

### Контракт R3-16A: только существующие поля

| GH-параметр / источник | Точное поле существующего JSON PR74 | Единицы | Precheck / STOP | Evidence для I4 |
|---|---|---|---|---|
| schema, project | `schemaVersion="apa-authored-project/1"`, `projectId`, `brief.projectId`, `units="meters"` | ID / м | IDs совпадают; посторонние root-ключи запрещены | intent JSON + schema verdict |
| разрешённый PLN | `brief.targetProjectPath` | абсолютный Windows .pln | строго равен `RUN.EXPECTED_PATH`; BDD запрещён | G0 project identity |
| режим / участок | `brief.mode`, `brief.site.siteId/region` | ID / строка | только режим из allowlist BRIEF; site обязателен | исходный пример PR74 + schema |
| уровни `L0,L1` | `brief.stories[].id/label/level` | м (абсолютный Z) | первый `label="1 этаж"`, `level=0`; строго возрастают | GetStories readback / G0 |
| native этажи | `brief.stories[].existingNativeIndex/existingFloorId/existingNativeLabel` | index / floorId / строка | эти pin-поля допустимы **только** при `brief.mode="ADAPT_EXISTING"`, полный комплект, реальные GetStories; нельзя подставлять 0/1 из GH | G0 story bindings |
| `H0,H1` | `storyHeights[storyId]` | м | 2.4≤H≤4.5; `abs(Z0+H0-Z1)≤1e-5` | проверка высот |
| `W,D,originXY` | `layout.outline.{xMin,xMax,yMin,yMax}` | м | xMin<xMax,yMin<yMax; только утверждённая свободная зона scratch | XY bounds + approval |
| комнаты GH | `brief.rooms[].{id,name,storyId,minAreaM2}` и `layout.rooms[].{roomId,storyId,rectangle}` | м² / м | один rectangle на комнату, containment, minArea, без overlap на одном этаже; не заменять NURBS комнату bbox | spatial schema + area |
| оси | `layout.axes[].{id,direction,coordinate}` | м | 1–100, `direction` X/Y, уникальные ID | axes schema |
| несущие стены | `layout.bearingLines[].{id,storyId,axisId,fromCoordinate,toCoordinate,wallThicknessMeters,cseCandidateId}` | м | толщина 0.15–0.60, длина ≥1, совпадение с границей комнаты, без дубликатов | spatial schema / wall DAG |
| конструктивные связи | `layout.loadPaths[].{upperMemberId,lowerMemberId}` | ID | ссылки на существующие bearingLines; не выводить несущую способность из BREP | loadPaths schema |
| материал / slab | `cseCandidate`, опционально `wallBasicMaterialName`; slabs создаёт authored compiler | ID / м | материал и GUID только из активного PLN; slab holes не входят в проверенный authored маршрут | CSE + material G0; будущий Slab readback |
| кровля GH (простая) | `nativeComponents[]`: `command="CreateRoofs"`, `params.roofsData[0].{floorIndex,level,thickness,structureType,buildingMaterialId,angle,pivotLine,polygonCoordinates}` | index, м, рад по примеру | один ряд, floorIndex из G0; `structureType="Basic"`; pivotLine+material обязательны; typed verifier SinglePlane; произвольный NURBS/PolyRoof не подставлять | command schema + future native roof readback |
| окно | `nativeComponents[]`: `command="CreateWindows"`, `params.windowsData[0].{ownerWallId,centerOffset,sillHeight,width,height}` | ссылка / м | `ownerWallId.guid.$createdGuid` ссылается на существующий Wall step, не GH ID; библиотека/host фактически проверены | graph host dependency |
| дверь | `nativeComponents[]`: `command="CreateDoors"`, `params.doorsData[0].{ownerWallId,centerOffset,sillHeight,width,height}` | ссылка / м | тот же host guard; фактический GUID только после native CREATE | graph host dependency |

**Точные ограничения SOURCE:** `compile_authored_intent` (PR74, строки 265–319) имеет строгий root allowlist и `nativeComponents` allowlist `CreateColumns/CreateDoors/CreateWindows/CreateWalls/CreateRoofs`. `CreateSlabs` рождается внутри authored compiler, а `CreateBeams` в его дополнительных nativeComponents отсутствует. Схема `layout` содержит **ровно** `schemaVersion,outline,rooms,axes,bearingLines,loadPaths`. Пример PR74 содержит hosted openings и roof с `pivotLine`; примерные native индексы, координаты и GUID материалов **не** являются значениями для нового PLN.

**Непосредственно полезный результат для I4:** заполнить **один** existing authored JSON из проверенных GH-чисел вручную после G0; никаких GH→PR74 конвертеров, второго SceneWriter или синхронизатора. `GH→typed PR74 auto adapter = NOT_FOUND_IN_CHECKED_PR_HEADS`, не абсолютное отсутствие в экосистеме.

## 3. Три отрицательных сценария R3-16B — спецификация STOP, не исполненные тесты

| ID | Вход | Ожидаемый STOP и доказательство | Чего это не доказывает |
|---|---|---|---|
| `NEG-Z` | `Z0=0,H0=3.2,Z1=3.1` | `STORY_HEIGHT_INCONSISTENT_WITH_LEVELS` по authored native plan; сверить GH input, JSON `storyHeights`, GetStories; до G1 отказ | не является проверкой фактического GH или AC |
| `NEG-HOST` | `CreateWindows.ownerWallId.guid.$createdGuid="wall-absent"` | precheck: target step отсутствует / неверный тип; STOP до CREATE; при реальном G1 требовать DAG/schema rejection, не выдумывать конкретный текст исключения | не доказывает host API runtime и фактическую библиотеку |
| `NEG-UNIT` | Rhino `12000 mm` перенесено в `12000 m` | `UNIT_MISMATCH` (локальный precheck label), сравнить Rhino units, коэффициент, `layout.outline`, реальный scratch envelope; STOP | не утверждать, что PR74 гарантированно ловит все ошибки масштаба |

**Граница проверок:** `RhinoCommon Brep.IsValidWithLog` и `Intersection.BrepBrep` применимы для независимого геометрического QA. Для `BrepBrep` `true` означает успешное вычисление; факт пересечения определяют возвращённые массивы curves/points. Одиночный кровельный BREP не обязан быть `IsSolid`. Это SOURCE API, не выполненный Rhino8 test.

## 4. Пять независимых QA-verdict — ни один не заменяет остальные

| Verdict | Что реально нужно для PASS | При отсутствии |
|---|---|---|
| `GH_GEOMETRY` | реальный Rhino8 SR + лицензия + `.gh` SHA256; units/tolerances; замкнутые/плоские ориентированные контуры; BREP validity, площади, пересечения, кровельные линии | `UNKNOWN_GH_NOT_RUN` |
| `AC_NATIVE` | только после отдельного G3/G4 допуска: реальные Archicad GUID, type=Wall/Slab/Roof/Window/Door, floorIndex/story/host/material, BREP/bbox, Save/Close/Reopen и независимый readback | `UNKNOWN_NATIVE_NOT_RUN` |
| `IFC_STRUCTURE` | отдельный IFC export и проверка IfcOpenShell: IfcBuildingStorey, IfcWall/Slab/Roof/Window/Door, GlobalId, containment, IfcRelVoidsElement/IfcRelFillsElement, геометрия | `UNKNOWN_IFC_NOT_EXPORTED` |
| `IDS_INFORMATION` | versioned IDS + IfcTester PASS/FAIL по требованиям свойств; отдельно от IFC geometry | `UNKNOWN_IDS_NOT_RUN` |
| `NORMATIVE_REVIEW` | конкретный СП, редакция, пункт, применимость, метод измерения, порог, допуск, ответственное подтверждение | `RULE_UNSPECIFIED` |

Нельзя повышать `GH_GEOMETRY` до `AC_NATIVE`; IFC GlobalId не равен автоматически Archicad GUID; IDS не подтверждает геометрическую корректность или соблюдение СП. Cross-app atomic rollback `NOT_FOUND` в проверенном маршруте: при UNKNOWN только STOP + read-only reconciliation в scratch; без автоматического DELETE/CREATE.

## 5. Контрааудиты, версии и лицензии

**CA-R3-16A — первоисточники/совместимость.** Официальная страница Graphisoft (проверена 24.10.2026) перечисляет **Grasshopper–Archicad 29 Live Connection build 3000**, Windows, Rhino 7/8, опубликован 01.10.2025; на странице также имеется 30 build 3000 от 07.10.2026, **не подменять AC29 новой версией**. Graphisoft отдельно указывает: GDL Converter создаёт GSM/LCF **Object**, не нативные Wall/Slab/Roof. Штатный Grasshopper/RhinoCommon входит в лицензируемый Rhino; GC29 — дополнение, а не отдельная лицензия Archicad/Rhino. IfcOpenShell/IfcTester — LGPL-3.0-or-later по upstream, полезен для независимого IFC/IDS QA, **не** native Archicad writer. RhinoCommon `Intersection.BrepBrep` возвращает bool успешности операции и массивы пересечений. Локальные версии Rhino8 SR, GC29, Tapir 1.5.10, лицензии, `.gh` и `APX` **не проверены**.

**CA-R3-16B — инженерная воспроизводимость/отсутствие дублирования.** `GH→manual typed JSON→PR74→BIM Graph→SceneWriter/SQLite→Tapir→AC29` — единственный разрешённый write path после отдельного допуска; GC29 `Element Input/Deconstruct` только read-only. У GH нет полномочия выдавать AC GUID. Slab holes, двухскатная PolyRoof и arbitrary NURBS/BREP не входят в P0 G1. Без G0 нельзя выбрать этаж, origin, material или доказать схему Tapir; без фактического G1 нельзя писать `OFFLINE_PASS`. Отдельные GH Design Create/Modify, GDL/Morph и Rhino Bake как замена BIM — **REFUSED**.

**Проверенные официальные источники:**
- Graphisoft: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ (AC29 build 3000, Rhino 8, GSM/LCF Object).
- McNeel RhinoCommon: https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.intersect.intersection/brepbrep (семантика bool/arrays).
- IfcOpenShell upstream: https://github.com/IfcOpenShell/IfcOpenShell (лицензии подпроектов, IFC/IDS).
- IfcTester: https://docs.ifcopenshell.org/ifctester.html (IDS validation).
- Immutable PR74: https://github.com/dvikt33-ux/safe-bim-layer/tree/5a3a9201a715a5528c93bed4a5318e2acb32eea7 .

## 6. Передача I4 и критерий ГОТОВО

**I4-P0-16A:** при фактическом G0 `RUNTIME_READY` взять один новый authored JSON по существующему example, подставить подтверждённые PLN/story/material/library/origin, выполнить **один** разрешённый read-only G1 `--preflight`. **ГОТОВО:** immutable JSON/plan hash, полный typed DAG, no native writes, before=after inventory, SHA receipts. Если G0 отсутствует — `BLOCKED_RUNTIME`, а не новая серия исследований.

**I4-P0-16B:** прикрепить к G1 evidence три негативных precheck verdict (`NEG-Z`, `NEG-HOST`, `NEG-UNIT`) только как спецификацию, пока не исполнены. **ГОТОВО:** входные поля, ожидаемый STOP, и где будет фактическая квитанция; не выдавать ожидаемый результат за тест.

**I4-P1-16C:** сохранить пять QA verdict в будущей G4 evidence matrix, все текущие `UNKNOWN`; IFC/IDS/нормативы не блокируют G1. **ГОТОВО:** никакого ложного native/IFC/СП PASS.

## 7. Фактическое состояние и открытые блокеры

| Класс | Факт |
|---|---|
| `SOURCE` | A5 15:43Z, предыдущий R3, immutable PR74 и официальные Graphisoft/RhinoCommon/IfcOpenShell/IfcTester прочитаны; контракт GH-BASE сужен до P0 |
| `OFFLINE` | **0 новых исполнений** PR74/GH; данный отчёт — SOURCE, не offline test |
| `BUILD` | 0 |
| `INSTALLED` | `NOT_VERIFIED` (нет локального manifest) |
| `LIVE` | 0 новых |
| `ACCEPTED` | 0 |
| `NOT_FOUND` | GH→typed adapter только в scoped проверенных PR; slab holes/PolyRoof в проверенном authored compiler; не утверждать глобальное отсутствие |
| `G0` | `BLOCKED_RUNTIME` |
| `G1` | `NOT_RUN` |
| `G2` | `SOURCE_PARTIAL` |
| `G3` | `NOT_AUTHORIZED` |
| `G4/G5` | `NOT_RUN` |

**Не выполнялось:** установка ПО, LIVE, запись PLN/APX, изменение `main`, исходников, `NEXT_RESEARCH_PRIORITIES.md`, merge, Work/Codex/Arena, платные API. **MODEL_MODE_NOT_VERIFIABLE.**
