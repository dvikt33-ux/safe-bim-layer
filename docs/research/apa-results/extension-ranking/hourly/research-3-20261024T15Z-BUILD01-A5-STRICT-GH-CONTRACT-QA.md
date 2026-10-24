# APA R3 — BUILD-01: строгий GH→PR74 контракт, геометрия и независимый QA
Дата: 24.10.2026, 15Z (18:00 МСК). Роль R3. Статус: SOURCE + OFFLINE_NUMERIC_ONLY; MODEL_MODE_NOT_VERIFIABLE. Никаких LIVE, установок, изменений кода/PLN/APX.

## 1. Поручение A5 и исходные доказательства
Прочитан свежий аудит A5 14:39Z: audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md, blob 2b9079c78c226f4c01cb05b6957e993c6f4e0d12. Задачи R3-15A: каждое поле GH-BASE сопоставить с реальным apa-authored-project/1, выявить минимум 3 отрицательных случая; R3-15B: пять независимых QA-verdict. Прочитаны issue #192, предыдущий R3 14Z (blob 6d28049eecf832fcde60e3da92356acf1753cac1), R1 14:58Z (blob 5c036f238ae65afd3a0f338eb98d0884aaad7805), R2 14Z (blob 6c5e5d3f83cef786f79e7e5ed97eb8a9bac665cc) и NEXT_RESEARCH_PRIORITIES.md. Исходный PR74 проверен по immutable commit 5a3a9201a715a5528c93bed4a5318e2acb32eea7, не по текущей исследовательской ветке.

**Новое инженерное обнаружение:** PR74 не принимает произвольную GH/NURBS геометрию как authored layout. Пространственная модель жёстко требует прямоугольные комнаты, оси X/Y и линии несущих стен на границах комнат. GH-BASE 14Z был спецификацией, а не schema-compatible .gh. Не строить второй writer/router.

## 2. Полевая таблица GH-BASE → существующий PR74
| Данные GH | Реальный путь в authored JSON | Ограничение / STOP |
|---|---|---|
| Идентификатор | root.projectId = brief.projectId | schemaVersion='apa-authored-project/1'; units='meters'; без неизвестных top-level полей |
| PLN | brief.targetProjectPath | абсолютный Windows .pln; равен RUN.EXPECTED_PATH; только одобренный scratch, не BDD |
| Этажи Z0/Z1 | brief.stories[].level | первый строго label='1 этаж', level=0; далее возрастают; existingNativeIndex/floorId сверяются с GetStories |
| Высоты H0/H1 | storyHeights[storyId] | 2.4–4.5 м; для смежных этажей abs(level+height-nextLevel) ≤ 1e-5 м |
| Габарит W/D, XY origin | layout.outline | только xMin,xMax,yMin,yMax; прямоугольный контур; координаты согласованы, не угаданы |
| Комнаты | brief.rooms[] + layout.rooms[] | на каждую brief room ровно один layout rectangle; одинаковый storyId, площадь ≥ minAreaM2; без пересечений комнат на этаже |
| Оси | layout.axes[] | 1–100 уникальных осей X/Y; координата внутри outline; произвольные кривые не поддержаны |
| Стены | layout.bearingLines[] | id,storyId,axisId,fromCoordinate,toCoordinate,wallThicknessMeters,cseCandidateId; длина ≥1 м, толщина **0.15–0.60 м**, совпадение с границей комнаты |
| Вертикальные связи | layout.loadPaths[] | пары исходных member IDs, а не вывод по касанию BREP; прочность не подтверждена |
| Slab CSE | cseCandidate + wallBasicMaterialName | точные provenance/source/native BuildingMaterial expectedProjectGuid/storyIds; материал только из активного PLN |
| Кровля | nativeComponents[].CreateRoofs | XY polygon, level, pivotLine, Basic, buildingMaterialId, floorIndex; PR74 verifier SinglePlane; фасеты NURBS не являются допустимым payload |
| Окна/двери | nativeComponents[].CreateWindows/Doors | ownerWallId.guid.$createdGuid существующей созданной стены; centerOffset,width,height,sillHeight; проверить библиотеку |
| Остальные нативные элементы | nativeComponents[] | allowlist только CreateColumns/Doors/Windows/Walls/Roofs; CreateBeams и произвольные slab holes здесь не разрешены |

Корень требует schemaVersion, projectId, units, brief, cseCandidate, layout, storyHeights. Дополнительные ключи только wallBasicMaterialName, nativeComponents, nativeGeometryAudit, junctionPolicy, nativeRoofJunctions, structuralFunctions. Поля source_key, GH_Path, slab_holes, roof_facets нельзя вставлять в root. **Ручной перенос параметров** в existing authored JSON остаётся единственным подтверждённым GH→PR74 способом для G1; автоматический конвертер NOT_FOUND_IN_CHECKED_PR74.

Новые ограничения непосредственно из SOURCE: scripts/archicad_semantic_brief.py:39–145, blob e431016f796bb8052487478dde3b2ed2752e7c00 — первый этаж '1 этаж' на 0.0; scripts/archicad_semantic_spatial.py:47–176, blob 5cfcfa1ee016703b1d2bf672a2af288901c0229d — rectangles, axes, 0.15 м minimum bearingLine, collinear overlap; scripts/archicad_project_accelerator.py:262–340, blob 8e0ce2fbb5441009925f0d9199e180e8670a5eea — strict authored contract; scripts/archicad_authored_native_plan.py:33–43,105–119, blob f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7d — story heights, Slab/Wall generation; example model-first-building.json blob e192fbb31bc872d751c41aa7132f0a4981755051 — hosted openings.

## 3. Воспроизводимая схема GH-BASE (SOURCE_SPEC, не исполненный .gh)
Inputs: W,D,Z0=0,Z1,H0,H1, originXY, room rectangles, wall thickness, roof pitch, openings. Grasshopper штатный: Construct Point ×4 → Polyline Closed → Area → XY outline; четыре Line → Length → axis/bearingLine tables; Move(Unit Z × Z1) → этаж 2; Rectangle/Area/Region Intersection → комнаты; Construct Point + Line → pivotLine; Panel → проверенные числа. В GH фиксировать stable source IDs для стен/комнат, но не выдавать GH_Path/Rhino ObjectId за AC GUID. RhinoCommon Curve.IsClosed/IsPlanar, CurveSelf, Brep.IsValidWithLog, AreaMassProperties, bbox и Intersection.BrepBrep только для read-only QA. У метода BrepBrep bool=true означает успешное вычисление, а не наличие пересечения: проверять массивы intersectionCurves/Points. Brep.IsSolid применим к замкнутому объёму, не к одиночной поверхности кровли.

Units: RhinoDoc.ModelUnitSystem и ModelAbsoluteTolerance записать при G0; authored units строго meters. При Rhino mm → m умножить на 0.001 один раз. Для PR74 story level tolerance 1e-5 м — это программный guard, не универсальный нормативный допуск. Контур перекрытия CCW относительно +Z, отверстие CW, проверить planarity, nesting, self-intersections и площадь. GH preview/BREP не доказывает native Wall/Slab/Roof, а передача через Morph/GDL теряет нужную типизацию. Официальный Graphisoft GH Design Create не подключать одновременно с единственным APA SceneWriter.

## 4. Ошибки до G1 — ожидаемые, НЕ тестовые PASS
N01 FIRST_STORY: label='0 этаж' или Z0≠0 → FIRST_ARCHITECTURAL_STORY_MUST_BE_1_AT_ZERO.
N02 THIN_BEARING: wallThicknessMeters=0.10 в bearingLines → INVALID_AUTHORED_WALL_ENVELOPE; 100-мм перегородка только через отдельно проверенный nativeComponents.CreateWalls.
N03 NON_RECT_ROOM: произвольный пятиугольник/NURBS вместо layout.rooms[].rectangle → ROOM_LOCATION_SCHEMA.
N04 WRONG_Z: Z0=0,H0=3.2,Z1=3.1 → STORY_HEIGHT_INCONSISTENT_WITH_LEVELS.
N05 HOST_MISSING: окно с отсутствующим source wall → unresolved $createdGuid, STOP без CREATE.
N06 UNIT_DRIFT: 12000 mm интерпретировано как 12000 m → UNIT_MISMATCH.
N07 DUPLICATE_WALL: два совпадающих collinear bearingLine на одном этаже → DUPLICATE_COLLINEAR_BEARING_WALL.
N08 ROOM_TOO_SMALL: room area ниже minAreaM2 → ROOM_MINIMUM_AREA_VIOLATION.
Точные ошибки для host/unit являются локальными precheck labels, а не утверждением текста ошибки PR74.

## 5. Численный независимый OFFLINE контроль (Python без Rhino/Grasshopper)
Проверено вычислением shoelace/atan: внешний контур 12×8 = 96 м² (CCW), внутренний 2×2 = -4 м² (CW), площадь после отверстия = 92 м²; Z0=0+H0=3.2 совпадает с Z1=3.2; rise 1.6 / halfspan 4 → угол 21.801409486°; H0=2.3 отклоняется по guard 2.4–4.5; Z1=3.1 не совпадает; 0.10 м вне диапазона bearingLines. **Это OFFLINE_NUMERIC_ONLY, не G1, не RhinoCommon BREP и не GH .gh execution.** Slab inner loop и PolyRoof остаются P1/NOT_FOUND_IN_CHECKED_PR74.

## 6. Пять независимых вердиктов I4
| Verdict | Минимальные доказательства | Не подтверждает |
|---|---|---|
| GH_GEOMETRY | Rhino8 SR, .gh SHA256, units/abs+angle tolerances, source IDs, closed/planar/oriented loops, Area, Brep validity, intersections | не native BIM |
| AC_NATIVE | после разрешённых G3/G4: реальные GUID/type/story/host/material/library, BREP/bbox, Save/Close/Reopen independent readback | не IFC/СП |
| IFC_STRUCTURE | отдельный IFC export: schema, GlobalId uniqueness, IfcBuildingStorey/Wall/Slab/Roof/Door/Window, containment, RelVoids/RelFills, geometry; IfcOpenShell/IfcDiff | не равенство IFC GlobalId и AC GUID |
| IDS_INFORMATION | versioned IDS + IfcTester spec-level PASS/FAIL | не геометрия |
| NORMATIVE_REVIEW | СП/редакция/пункт/применимость/порог/единицы/допуск/измерение/проверяющий; неизвестно → RULE_UNSPECIFIED | не автоматическое COMPLIANT |

Независимый IFC audit не заменяет native readback, а геометрия NURBS не гарантирует совпадения control points после конвертации. Два ската — открытые поверхности, не требовать IsSolid=true. Межпрограммного атомарного rollback не найдено; STOP+read-only reconciliation на UNKNOWN, только scratch PLN.

## 7. Готовые средства и лицензии
| Средство | SOURCE-совместимость/лицензия | Решение |
|---|---|---|
| Grasshopper + RhinoCommon | входят в лицензируемый Rhino 8, локальный SR не проверен | **P0**, дополнительных GH плагинов для GH-BASE не требуется |
| Graphisoft Grasshopper–Archicad 29 LC | официальный build 3000 для Rhino 7/8, Windows, 01.10.2025; бесплатное дополнение, лицензии основных приложений отдельно | read-only reference/deconstruct; GH Design Create = второй writer, запрещён |
| Ladybug/Honeybee | открытые исходники; современные Honeybee energy/radiance AGPL-3.0; зависимые пакеты и Rhino8 runtime отдельно не проверены | P1 климат, не BIM writer, не G1 |
| Karamba3D | официальная поддержка Rhino8, бесплатный Demo с ограничениями, Pro платный | P1 структурные гипотезы, не обязательный G1 и не конструктивная экспертиза |
| IfcOpenShell/IfcTester | LGPL-3.0-or-later по upstream, IDS/IFC read/QA | независимый P1/G4 аудит, не Archicad writer |
| Morph/GDL из свободного BREP | не native Wall/Slab/Roof contract | не принимать как BUILD-01 native BIM |

Первоисточники: Graphisoft https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; Rhino https://www.rhino3d.com/en/download/ ; McNeel https://docs.mcneel.com/rhino/8/help/en-us/documentproperties/units.htm ; RhinoCommon https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.intersect.intersection/brepbrep ; IfcOpenShell https://github.com/IfcOpenShell/IfcOpenShell ; IfcTester https://docs.ifcopenshell.org/ifctester.html ; Honeybee https://github.com/ladybug-tools/honeybee-grasshopper-energy ; Karamba https://karamba3d.com/get-started/ . Локальные версии/лицензии/пакеты не проверены. Не переносить лицензию одного подпроекта Ladybug на все остальные.

## 8. Передача I4 и два контрааудита
I4-P0-15A: существующий authored fixture с правильными brief/layout/rooms/axes/bearingLines, не произвольный Brep. **ГОТОВО:** G1 schema-check на реальных PLN/story/material bindings после G0; иначе BLOCKED_LOCAL_BINDINGS.
I4-P0-15B: пять независимых QA slots с UNKNOWN/STOP. **ГОТОВО:** evidence matrix для будущего G4, без ложного ACCEPTED.
I4-P0-15C: G0 manifest Rhino units/SR/tolerances/.gh hash, AC stories/PLN, Tapir APX/schema, library/material. **ГОТОВО:** фактический read-only manifest или BLOCKED.
I4-P1-15D: holes, PolyRoof, arbitrary NURBS — OPTIONAL, не блокируют G1. **ГОТОВО:** честный NOT_FOUND_IN_CHECKED_PR74.
I4-P0-15E: после G0 — реальный G1 read-only preflight; G3 только по отдельному разрешению. **ГОТОВО:** receipt nativeWriteCalls=0, plan hash, DAG и SHA.

CA-R3-15A: 0.15 м bearingLine и первый этаж на нуле — **ограничения PR74, не универсальные нормы**; bbox нельзя выдавать за утверждённую сложную комнату. CA-R3-15B: RhinoCommon не отдельный бесплатный Rhino, Karamba Demo не полноценный бесплатный FEA, IFC/IDS не native readback, GH Create — конкурирующий writer.

**Итог:** SOURCE = свежий A5 + PR74 + официальные материалы; OFFLINE = только арифметика, не G1; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0; ACCEPTED=0; NOT_FOUND_IN_CHECKED_PR74 = GH→typed adapter, slab holes, native arbitrary NURBS roof, atomic sync/rollback. G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. Не менялись main, исходники, PLN/APX, NEXT_RESEARCH_PRIORITIES.md. MODEL_MODE_NOT_VERIFIABLE.
