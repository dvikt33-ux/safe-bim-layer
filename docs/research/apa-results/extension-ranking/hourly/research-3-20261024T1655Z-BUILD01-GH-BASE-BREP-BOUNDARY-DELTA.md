# APA R3 — BUILD-01 #192: GH-BASE, точная геометрия и граница native BIM (дополнение цикла 16Z)
**Дата:** 2026-10-24, 16:55 UTC (19:55 МСК). **Роль:** R3, Rhino 8 + Grasshopper + RhinoCommon. **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Режим:** SOURCE + ограниченная OFFLINE-арифметика; не Rhino/Archicad execution. **MODEL_MODE_NOT_VERIFIABLE**.

## 0. Диспетчеризация: актуальное поручение A5 и неповторение
Прочитан непосредственно в указанной ветке `audit-a5-20261024T16Z-BUILD01-G0-G1-GATE-DECISION.md` (Git blob `78bb38b2326025c5e3c72eed89567a6a2ae34a11`). Поручение **R3 P1/80**: не расширять каталог плагинов; передать I4 один GH-BASE P0 контракт (единицы, outline/rooms/bearingLines/stories/roof/openings), NEG-Z/NEG-HOST/NEG-UNIT и пять независимых QA. Предыдущий R3 `research-3-20261024T1602Z-BUILD01-GH-BASE-P0-CHECKLIST.md` прочитан в ветке (blob `9d04949b908b7d786172efbe290dcf2b2b7d606b`); данный документ — **только инженерное дополнение**, не новый writer и не повтор прежней спецификации. Issue #192: https://github.com/dvikt33-ux/safe-bim-layer/issues/192 .

## 1. Решение по расширениям и лицензиям — без установки
| Компонент | SOURCE / совместимость / лицензия | Реальная функция в BUILD-01 | Решение |
|---|---|---|---|
| Grasshopper, штатный Rhino 8 | штатная параметрика Rhino 8; требует действующей лицензии Rhino, локальная SR/лицензия неизвестна | Number Sliders, Construct Point, Rectangle/Polyline, Area, Line, Move, проверки входных чисел | **P0 USE**, без нового плагина |
| RhinoCommon Rhino.Geometry | официальный API McNeel для BREP/curve и `RhinoDoc.ModelUnitSystem/ModelAbsoluteTolerance`; локальная версия не проверена | геометрическая валидация до ручного JSON; не создаёт Archicad Wall | **P0 QA**, если Rhino доступен |
| Graphisoft Grasshopper–Archicad 29 Live Connection | официальный **build 3000**, Windows, Rhino 7/8, опубликован 2025-10-01; не Start Edition; локальная установка неизвестна | чтение/сопоставление элементов после отдельного допуска; Design Create/Modify **не использовать** параллельно SceneWriter | **OPTIONAL READ**, не G1 blocker |
| IfcOpenShell + IfcTester | upstream LGPL-3.0-or-later для Python/ifctester, версии локально неизвестны | независимый IFC geometry/semantic + IDS audit после G4, не Archicad native writer | **OPTIONAL G4/G5** |
| GDL/GSM/LCF, Morph, Rhino Bake, внешние GH-to-BIM writers | отдельный объект/геометрия или альтернативный writer, native Wall/Slab/Roof/host не гарантируются | не заменяют PR74 native BIM | **EXCLUDE P0** |
| Karamba, Ladybug/Honeybee, новые плагины конструкций/норм | лицензии/локальные версии и применимость не доказаны для конкретного G0/G1 blocker | не нужны для typed P0; численный/энергетический расчёт не равен СП PASS | **DEFER**, не искать без нового STOP |

Первоисточники: Graphisoft https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; McNeel RhinoCommon https://developer.rhino3d.com/api/rhinocommon ; ModelUnitSystem https://developer.rhino3d.com/api/rhinocommon/rhino.rhinodoc/modelunitsystem ; ModelAbsoluteTolerance https://developer.rhino3d.com/api/rhinocommon/rhino.rhinodoc/modelabsolutetolerance ; IfcOpenShell https://github.com/IfcOpenShell/IfcOpenShell ; IfcTester https://docs.ifcopenshell.org/ifctester.html .

## 2. Единственный GH-BASE P0 граф — числовые параметры, не автоматическая запись
```text
RhinoDoc units/tolerances (READ) ───────────────┐
W,D,originXY,Z0,Z1,H0,H1,wall_t,roof_angle_deg ─┼→ UNIT_GUARD / LEVEL_GUARD
                                                ↓
Construct Point → Rectangle / Closed Polyline → Area / boundary check
  ├─ Rectangle per room → containment / overlap check → layout.rooms[]
  ├─ X/Y axes → axis reference check → layout.axes[]
  ├─ Bearing lines → thickness/length/axis guard → layout.bearingLines[]
  ├─ Story levels / storyHeights → actual GetStories binding REQUIRED
  ├─ Roof pivot + plane polygon + angle → SinglePlane roof fields only
  └─ Openings positions/sizes → Wall host step IDs (NOT native GUID)
                                                ↓
READ-ONLY Panels + MANUAL mapping to existing apa-authored-project/1 JSON
                                                ↓
Existing PR74 compiler / BIM Graph / one SceneWriter+SQLite (no new adapter)
```
**Владение:** GH выдаёт проектные числа и предварительную геометрию; `projectId/stepId/plan_hash` формирует существующий APA; native GUID выдаёт Archicad только после CREATE. Ни GH DataTree path, ни Rhino ObjectId не являются native GUID. `ownerWallId.guid.$createdGuid` — зависимость от созданного Wall step, не буквальный GUID до G3.

## 3. Контракт I4: точные поля существующего PR74, без добавления схемы
| GH output | Поле authored `apa-authored-project/1` | Guard/STOP |
|---|---|---|
| unit conversion | root `units="meters"` | `RhinoDoc.ModelUnitSystem` фактически READ; при mm все координаты/длины ×0.001 **один раз**; при m ×1.0; неизвестные units → STOP |
| footprint | `layout.outline.{xMin,xMax,yMin,yMax}` | xMin<xMax; yMin<yMax; exact scratch origin G0; без bbox-подмены сложного плана |
| rooms | `brief.rooms[].{id,name,storyId,minAreaM2}`; `layout.rooms[].{roomId,storyId,rectangle}` | прямоугольная комната, inside outline, отсутствие overlap; сложная NURBS-комната → UNSUPPORTED, не прямоугольный bbox |
| stories | `brief.stories[].{id,label,level}`; `storyHeights[storyId]` | первый label «1 этаж», level 0; 2.4–4.5 м; `abs(Z0+H0-Z1)≤1e-5`; G0 подтверждает **существующие** native stories |
| adapted stories | `brief.stories[].existingNativeIndex/existingFloorId/existingNativeLabel` | только `brief.mode="ADAPT_EXISTING"`, actual `GetStories`; индексы 0/1 не выдумывать |
| axes/bearing | `layout.axes[].{id,direction,coordinate}`; `layout.bearingLines[].{id,storyId,axisId,fromCoordinate,toCoordinate,wallThicknessMeters,cseCandidateId}` | оси X/Y; стены 0.15–0.60 м, длина ≥1 м; связи и границы проверяются до компиляции |
| load path | `layout.loadPaths[].{upperMemberId,lowerMemberId}` | обе ссылки существуют; геометрия не доказывает несущую способность |
| roof | `nativeComponents[].command="CreateRoofs"`, `params.roofsData[].{floorIndex,level,thickness,structureType,buildingMaterialId,angle,pivotLine,polygonCoordinates}` | только Basic SinglePlane; floorIndex/material из G0; angle в единицах **реального локального schema**, не считать градусы радианами |
| windows/doors | `nativeComponents[].command="CreateWindows"/"CreateDoors"`, `params.windowsData[]/doorsData[].{ownerWallId,centerOffset,sillHeight,width,height}` | host Wall step до child; library/Favorites G0; не присваивать GUID вручную |
| slabs | генерируются authored compiler из `layout` | `CreateSlabs` material на CREATE не доказан; holes отсутствуют в подтверждённом authored P0 |

**Существенная граница:** GH может иметь BREP с произвольными вырезами, но PR74 P0 принимает ограниченный набор параметрических native команд. **Успешный GH BREP ≠ созданный Roof/Slab/Opening**. Оставлять геометрию, не представимую в контракте, в STOP/DEFER, не создавать GDL/Morph ради формального успеха.

## 4. Геометрический QA: что можно проверить официальным RhinoCommon и что это НЕ доказывает
| Проверка | Официальная операция | Критерий до handoff |
|---|---|---|
| Система единиц и допуски | `RhinoDoc.ModelUnitSystem`, `ModelAbsoluteTolerance` | записать реальные units/tolerance и коэффициент перевода; значение допусков не придумывать |
| Топология/геометрия BREP | `Brep.IsValidWithLog`; при глубокой диагностике `IsValidTopology` → `IsValidGeometry` → `IsValidTolerancesAndFlags` | результат true и log; invalid → STOP; последовательность диагностических методов важна |
| Сборка твёрдого объёма | `Brep.CreateSolid(breps,tolerance)` | не-null, ожидаемое число тел; отсутствие результата → STOP; одиночная плоскость кровли **не обязана** быть solid |
| Пересечение | `Brep.CreateBooleanIntersection(..., tolerance)` | не-null и ожидаемая геометрия; проверять результат, а не только факт вызова |
| Вырез/отверстие | `Brep.CreateBooleanDifference(..., tolerance)` | не-null и проверенная геометрия, но native Slab hole **не доказан** |
| IFC geometry | `ifcopenshell.geom.create_shape(settings, element)` | только на фактическом IFC, отдельно от Rhino BREP и native Archicad; возможен RuntimeError |

Источники McNeel: https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/createbooleandifference ; https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/createsolid ; https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/isvalidtopology ; https://developer.rhino3d.com/api/RhinoCommon/html/M_Rhino_Runtime_CommonObject_IsValidWithLog.htm ; IfcOpenShell geometry https://docs.ifcopenshell.org/autoapi/ifcopenshell/geom/main/index.html . **Все эти методы здесь изучены как SOURCE, не исполнялись в Rhino.**

## 5. NEG тесты (только ожидаемые STOP; все NOT_RUN)
| ID | Преднамеренно неверный вход | Ожидаемый STOP | Evidence после фактического исполнения |
|---|---|---|---|
| NEG-Z | Z0=0, H0=3.2, Z1=3.1 м | `STORY_HEIGHT_INCONSISTENT_WITH_LEVELS` на уровне PR74, либо предварительный отказ; фактический текст ошибки не придумывать | GH inputs + JSON + PR74 preflight receipt |
| NEG-HOST | `ownerWallId.guid.$createdGuid="wall-absent"` | `HOST_STEP_UNRESOLVED` (имя локального guard, **не** утверждение о строке исключения PR74) | typed DAG host reference, preflight error, modelWriteAttempts=0 |
| NEG-UNIT | 12000 mm ошибочно записано как 12000 m | `UNIT_MISMATCH` в ручной проверке коэффициента и approved scratch envelope; **PR74 не гарантирует** обнаружение | Rhino units, raw/scaled dimension, outline, receipt |
| NEG-HOLE | outline 12×8 м, внутренний hole 2×2 м, но authored slab без отверстия | `UNREPRESENTABLE_SLAB_HOLE` — не отправлять bbox/slab без отверстия | GH boundary count/area vs authored slab contour; NOT_RUN |
| NEG-BREP-ROOF | curved NURBS roof вместо Basic SinglePlane | `UNREPRESENTABLE_NATIVE_ROOF` — не заменять Morph/GDL/planar bbox | Rhino geometry classification vs CreateRoofs schema; NOT_RUN |

Имена `HOST_STEP_UNRESOLVED`, `UNIT_MISMATCH`, `UNREPRESENTABLE_*` здесь **предлагаемые метки R3 precheck**, а не подтверждённые исключения существующего компилятора. Не добавлять writer/router ради них.

### OFFLINE_NUMERIC_ONLY — независимая арифметика, не Rhino/GH
Для гипотетического двускатного сечения 12×8 м, угол ската 30°: половина пролёта 4 м, подъём `4*tan(30°)=2.3094010768 м`; площадь двух плоскостей без свесов `12*8/cos(30°)=110.8512516844 м²`; `30°=0.5235987756 рад`. Эти числа пригодны как контроль калькулятора, **не** доказывают, что PR74 создаёт двускатную PolyRoof. Перекрытие 12×8 м с отверстием 2×2 м: `96−4=92 м²`; передача в PR74 P0 контура без hole создаст геометрически другую модель (96 м²), даже если схема принята. **Геометрический запрет** — не заменять 92 на 96 без согласования.

## 6. Пять независимых вердиктов — до фактических запусков UNKNOWN
| Verdict | Требуемое свидетельство для PASS | Сейчас |
|---|---|---|
| GH_GEOMETRY | реальный Rhino8 SR, `.gh` hash, units/tolerances, валидность контуров/BREP, площадь/пересечения | UNKNOWN_GH_NOT_RUN |
| AC_NATIVE | native GUID/type/story/host/material + BREP readback после отдельного G3/G4 и Save/Open | UNKNOWN_NATIVE_NOT_RUN |
| IFC_STRUCTURE | реальный IFC, IfcBuildingStorey/IfcWall/IfcSlab/IfcRoof/IfcWindow/IfcDoor, containment/voids/fills + геометрия | UNKNOWN_IFC_NOT_EXPORTED |
| IDS_INFORMATION | версионированный IDS + IfcTester отчёт, без подмены IFC geometry | UNKNOWN_IDS_NOT_RUN |
| NORMATIVE_REVIEW | точная редакция СП, пункт, область применимости, измерение, порог, ответственное решение | RULE_UNSPECIFIED |

## 7. Передача I4 / G0–G5 / критерий ГОТОВО
**R3 → I4:** передан P0 граф, существующие authored поля, два дополнительных отрицательных геометрических сценария, обязательные единицы/допуски, геометрический STOP при невоспроизводимых отверстиях и криволинейных кровлях. **I4 НЕ должен ждать новых плагинов.** Как только получен реальный G0 manifest (AC29 build 5101, scratch PLN SHA, native stories, Tapir APX/schema, materials/library, Rhino units), I4 вручную собирает один новый authored JSON и выполняет только разрешённый G1 read-only preflight. G2 local schema до native; G3 требует отдельного разрешения; G4 Save/Open и G5 вторая модель не запускались.

| Класс | Состояние на момент отчёта |
|---|---|
| SOURCE | A5 16Z и предыдущий R3 прочитаны; официальные Graphisoft/McNeel/IfcOpenShell API проверены |
| OFFLINE | только арифметика подъёма/площади; **PR74/GH не запускались** |
| BUILD | 0 новых зданий |
| INSTALLED | NOT_VERIFIED: нет доступа к ноутбуку/активным AC29/Rhino/Tapir |
| LIVE | 0 новых операций; не запускались |
| ACCEPTED | 0 |
| NOT_FOUND | только в ограниченном проверенном authored P0: holes/PolyRoof/автоматический GH→PR74 adapter; глобальное отсутствие НЕ утверждается |
| G0/G1 | BLOCKED_RUNTIME_NOT_OBSERVED / NOT_RUN |
| G2/G3/G4/G5 | SOURCE_PARTIAL / NOT_AUTHORIZED / NOT_RUN / NOT_RUN |

**Запреты соблюдены:** не изменять `main`, код, PLN/APX, не устанавливать ПО, не выполнять LIVE, merge, платные API, Work/Codex/Arena. Отчёт — единственная запланированная запись, в `docs/research/.../hourly/` исследовательской ветки. **MODEL_MODE_NOT_VERIFIABLE.**
