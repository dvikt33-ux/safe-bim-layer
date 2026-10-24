# APA A5 | Независимый аудит и диспетчер | 2026-10-24 13Z (16:40 МСК)

**Цель:** BUILD-01, issue #192. Archicad 29 build 5101 + Rhino 8 + Grasshopper, только готовые официальные/бесплатные мосты и существующий APA. **Вердикт: RESEARCH_EVIDENCE_VERIFIED / BUILD01_BLOCKED_G0 / THREE_WAY_SYNC_NOT_FOUND.** Никаких новых OFFLINE, BUILD, INSTALLED, LIVE, ACCEPTED. **MODEL_MODE_NOT_VERIFIABLE.**

## 1. Входные отчёты: проверка фактического наличия, содержимого и Git blob SHA-1

Ветка: research/apa-extension-ranking-hub-20261018. Все четыре файла текущего 13Z найдены по точным путям, получены через GitHub fetch_file, независимый Git blob SHA-1 вычислен по полному UTF-8 содержимому и совпал с GitHub. Это проверка архивной целостности, НЕ инженерная приёмка.

| Роль | Путь относительно docs/research/apa-results/extension-ranking/hourly/ | Git blob SHA-1 | Итог |
|---|---|---|---|
| R1 | research-1-20261024T13Z-BUILD01-NATIVE-ROOF-FAVORITES.md | 4be23c3371c572b09d87c80ab882eca699e2bfee | PRESENT / SHA_MATCH |
| R2 | research-2-triad-2026-10-24T13Z-report.md | e379a5341e41dec5d9d7f7c58d517f1c1acfbbb4 | PRESENT / SHA_MATCH |
| R3 | research-3-rhino-gh-2026-10-24T13Z.md | 6a51de7906bbdc6a454547604dbc75f9f077de06 | PRESENT / SHA_MATCH |
| I4 | integrator-4-2026-10-24T13Z-BUILD01-TRIAD-G0-G5.md | 343bd8a5586b80b12ad3a0c45cb0931ac6a0e419 | PRESENT / SHA_MATCH |

Дополнительно прочитаны issue #192, поручение research-1-20261023T11Z-TRIAD-PIVOT.md (blob 896fa3af0953468ca58fca710f32cb926504f582), действующая очередь docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md (blob 6f074693360231c5cb42ada815984a6b0dd504c0). Попытка прочитать одноимённый файл из корня дала 404: **канонический путь находится в docs/research/apa-results/extension-ranking/**. Исторический PROJECT_PLAN rev182 не изменялся и не использовался для новых фактических утверждений.

## 2. Контрааудит CA-A5-01 — первоисточники, версии, лицензии, доказательная граница

1. **Официальный Graphisoft:** каталог Rhino–Grasshopper–Archicad Toolset показывает Grasshopper–Archicad **29** Live Connection, **build 3000**, Windows 16.8 MB, дата 01.10.2025, Rhino 7/8. Указана несовместимость с Archicad Start Edition. Источник: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ . Это совместимость выпуска, **не подтверждение INSTALLED** на ноутбуке и не бесплатная лицензия на Archicad/Rhino.
2. **Официальный AC29 GC User Guide, стр. 41:** Deconstruct Brep для Beam, Column, Slab, Wall, Mesh, Zone, Shell, Single-Plane Roof; выход — список поверхностей. **Multi-Plane Roof, Window, Door не включены в этот список**; из отсутствия в перечне нельзя выводить полную невозможность иных способов чтения. Источник: https://help.graphisoft.com/AC/29/INT/GC.pdf .
3. **Официальный McNeel:** Rhino.Inside — open-source технология внедрения Rhino в 64-битные Windows-хосты, а не готовый Archicad 29 host; документированы примеры Revit/AutoCAD. Проверенного AC29-host в этих первоисточниках нет. Статус готового Rhino.Inside→AC29 writer: **NOT_FOUND**, не добавлять в список обязательных установок. Источник: https://www.rhino3d.com/features/rhino-inside/ .
4. **Лицензия Rhino:** Rhino 8 требует действующей лицензии; 90-дневная Evaluation ограничена после окончания, в частности перестают работать сохранение и плагины. «Бесплатный мост» не означает «бесплатная тройка приложений». Источник: https://www.rhino3d.com/en/download/ .
5. **Tapir upstream, immutable tag 1.5.9:** fetch_file файла archicad-addon/Sources/ExtendedElementCommands.cpp, blob bd5cd197e9ad2c0db9e40c1baff877bbdcbfae30. В CreateRoofsCommand::Execute проверено: при отсутствии pivotLine выбирается API_PolyRoofID, при наличии pivotLine — API_PlaneRoofID; angle допустим только для single-plane, levels/eavesOverhang — для multi-plane. ModifyRoofs ограничен API_PolyRoofID. Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp . **Локальная заявленная версия Tapir 1.5.10 не идентифицирована по бинарному SHA/schema, не приравнивать её к tag 1.5.9.**
6. **APA PR74, immutable commit 5a3a9201a715a5528c93bed4a5318e2acb32eea7:** повторно прочитаны реальные исходники: archicad_project_accelerator.py blob 8e0ce2fbb5441009925f0d9199e180e8670a5eea; archicad_connected_components.py blob c5a99f59a90369ff622807574677cf11ca0a2225; archicad_scene_run.py blob ca91c1cfc41cee763c62d1f3a70337d74fbafd53; archicad_authored_native_plan.py blob f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7. Проверены не только пересказы исследователей, но и конкретные guards и allowlists.
7. **Неподтверждённые утверждения:** локальные AC29 build5101/Tapir APX/GC29/Rhino8 SR, действующие лицензии, установленные GH-плагины, конкретный PLN/порт, PR74 checkout, полный GH→PR74 parser и автоматическая трёхсторонняя транзакция **НЕ проверены**. R1/R2/R3/I4 не предоставили LIVE receipts для BUILD-01. Количество SOURCE-карточек исследователей не заменяет G1/G3/G4.

**Решение CA-A5-01:** PASS по доступности и согласованности перечисленных первоисточников; **BLOCKED** по локальным версиям/лицензиям/бинарному provenance. Отсутствие доказательств не трактовать как доказательство отсутствия возможностей.

## 3. Контрааудит CA-A5-02 — инженерная воспроизводимость, native BIM, циклы и дублирование

Проверка PR74 на уровне исходников выявила:
- scripts/archicad_project_accelerator.py строки 294–304: authored CreateRoofs **требует pivotLine**, Basic и buildingMaterialId. Поэтому upstream Tapir API_PolyRoofID пока **не проходит действующий authored contract**.
- scripts/archicad_connected_components.py строки 184–196: Roof verifier требует **roofClass=SinglePlane** и Basic. Следовательно даже успешная внешняя PolyRoof CREATE не означает прохождение APA native verifier.
- scripts/archicad_scene_run.py строки 94–98: ALLOWED_WRITES = CreateWalls/CreateSlabs/CreateColumns/CreateWindows/CreateDoors/CreateObjects; EXTENDED_WRITES включает CreateRoofs и CreateBeams **через opt-in adapters**, но **не ModifyRoofs**. Не обходить существующий SceneWriter.
- scripts/archicad_connected_components.py: проверяются Beam/BeamSegment, parent/host, materials и geometry signatures; новые GUID/изменения геометрии вне ledger способны вызвать inventory drift. Нельзя обещать безопасную параллельную запись GH и APA только за счёт декларации «разные владельцы».
- scripts/archicad_authored_native_plan.py: CreateSlabs.level передаётся в абсолютных координатах проекта; story/floor bindings и readback обязательны. GH отверстия в Slab не равны автоматически доказанным holes в PR74.
- PR74 и связанные PR126/131/149/162 представлены разными ветками/коммитами согласно I4; **единый установленный checkout и объединённые зависимости не подтверждены**. Не объявлять набор открытых PR одной готовой сборкой.

**Цикл/удаление/rollback:** AC→GH Deconstruct может использоваться как read-only наблюдение, но при подключении GH Design Create/Modify возникает потенциальный feedback loop/второй writer. Rhino Bake/Push и .3dm Hotlink не создают native Wall/Slab/Roof с доказанной GUID-идентичностью. Synchronize=False не является доказанным удалением или откатом. IFC GlobalId ≠ автоматически internal AC GUID. Deconstruct BREP surfaces ≠ доказанный closed manifold. В случае UNKNOWN: STOP → snapshot receipts/SQLite → read-only inventory/reconcile → никакого повторного CREATE. Restore только на отдельной разрешённой scratch копии.

**Решение CA-A5-02:** концепция **один SceneWriter + GH/Rhino для вычислений + AC→GH readback** инженерно обоснована как безопасное ограничение. Но end-to-end GH DataTree/BREP → typed PR74 → native AC → GH/Rhino roundtrip **NOT_FOUND** как готовый воспроизводимый автоматический маршрут. **Трёхсторонний BIM roundtrip и атомарный rollback NOT_FOUND.**

## 4. BUILD-01: строгая матрица G0–G5

| Gate | Критерий ГОТОВО | Факт текущего цикла |
|---|---|---|
| G0 | Реальные AC29 build/port/PLN SHA; Tapir APX version/SHA/registered schema; Rhino8 SR/license/units/tolerance; GC29 build; GH .gh hash; Favorites/attributes/libraries; immutable локальный APA checkout | **BLOCKED_RUNTIME**: нет чтения пользовательского ноутбука, APX, PLN, активного GH и локального checkout |
| G1 | Одно новое структурированное здание >=2 этажа, Wall/Slab/Roof/Window/Door, typed DAG, topological order, host GUID bindings, collision/schema/plan hash, **фактический offline compiler run** | **NOT_RUN**, описание и исторический fixture не засчитывать |
| G2 | Сверка локальных Tapir command schemas с typed PR74/SceneWriter; story/host/material/roof/slab/beam constraints; однозначный writer и rollback guard | **SOURCE_PARTIAL**, PolyRoof/Slab holes/GH bridge/installed registry не закрыты |
| G3 | Только после отдельного разрешения: новая scratch PLN, один writer, native GUID receipts, BIM type/story/host/material/BREP, no duplicate GUID | **NOT_AUTHORIZED / NOT_RUN** |
| G4 | GuardedSave → Close → Open → независимый native GUID/BREP/material/host inventory; receipts с SHA | **NOT_RUN** |
| G5 | Второе отличающееся исходное задание, новый scratch, повтор G1–G4 | **NOT_RUN** |

**Статусы:** SOURCE — 4/4 текущих исследовательских/интеграционных отчёта архивно подтверждены; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. Это показатели **данного BUILD-01**, не отрицание исторических локальных тестов APA. Модель BUILD-01 **НЕ ГОТОВА**.

## 5. Маршруты и минимальный scope для первого BUILD-01

| Операция | Наиболее узкий доказанный SOURCE-маршрут | Статус |
|---|---|---|
| Этажи | AC GetStories → explicit PR74 story bindings → readback | SOURCE, G0 pending |
| Стены | typed CreateWalls → SceneWriter/Tapir → Wall GUID/type/height/material/BREP | SOURCE, G1 not run |
| Перекрытия | typed CreateSlabs с absolute level → SceneWriter → Slab readback | SOURCE; GH holes NOT_FOUND |
| Колонны | CreateColumns → SceneWriter → Column story/axis/material/BREP | SOURCE, local schema pending |
| Балки | connected opt-in CreateBeams → тот же SceneWriter → Beam/BeamSegment | SOURCE, unified authored route pending |
| Простая кровля | PR74 CreateRoofs с pivotLine, Basic, material → Roof verifier | SOURCE, G3 not run |
| Многоскатная кровля | Tapir upstream CreateRoofs без pivotLine | **SOURCE_FOUND / PR74_ROUTE_NOT_FOUND** |
| Окна/двери | hosted CreateWindows/CreateDoors → ownerWallId/$createdGuid → library/void readback | SOURCE, local libraries pending |
| Параметрика | Rhino/GH geometry/constraints → frozen authored intent | **автоматический GH→PR74 bridge NOT_FOUND** |
| QA | AC native readback + GH Deconstruct supported types; IFC/IDS отдельно | SOURCE; IFC/IDS != BREP/нормативная экспертиза |

**Приоритет исполнения:** базовое 2-этажное здание на уже существующем ограниченном PR74 SinglePlane-маршруте, без обязательного PolyRoof/Slab holes, пока их typed contract не квалифицирован. Нельзя расширять scope так, чтобы новый blocker бесконечно задерживал G1.

## 6. Диспетчерские задания на следующий час

### R1 — нативные BIM-инструменты, P0/96
**Задача R1-14A:** составить компактную immutable матрицу **CreateWalls/CreateSlabs/CreateColumns/CreateRoofs(single)/CreateWindows/CreateDoors**: точные обязательные поля PR74 vs upstream Tapir vs local schema snapshot; отметить несовпадения, defaults/Favorites, material и story/host. **ГОТОВО:** 6 строк с прямыми file/line/blob refs, два отрицательных кейса (zero-length wall; отсутствующая library part), минимальный безопасный 2-этажный BUILD-01 scope. Ни установки, ни LIVE.
**Задача R1-14B, P1/84:** отдельно подтвердить upstream MultiPlane CreateRoofs vs ModifyRoofs и наличие любого **уже существующего** opt-in PolyRoof adapter в иных открытых ветках. **ГОТОВО:** найден точный path/commit/guard или NOT_FOUND; без разработки нового writer и без обязательности для первого G1.

### R2 — мосты, GUID и конфликты, P0/100
**Задача R2-14A:** проверить, существует ли в доступных ветках/файлах APA **уже готовый GH→PR74 typed bridge** с точной схемой (DataTree → authored intent → plan hash). **ГОТОВО:** путь, commit, воспроизводимый беззаписный вызов и образец schema либо **NOT_FOUND**, без обещаний на основе GH JSON/BREP.
**Задача R2-14B, P0/95:** таблица owner/identity для AC GUID, Rhino ObjectId, GH persistent reference, IFC GlobalId и SQLite intent id; операции create/update/delete/conflict/UNKNOWN/rollback. **ГОТОВО:** для каждого перехода указаны реально существующая команда/readback, три отказных сценария (external GH CREATE, lost GH link, duplicate CREATE) и STOP-критерий. Не заявлять трехстороннюю sync без native receipt.

### R3 — параметрика, геометрия и нормативы, P0/92
**Задача R3-14A:** подготовить **без установки и без выполнения** два минимальных воспроизводимых GH-графа: (1) 2-story Wall/Slab/SinglePlane Roof/Window/Door parameter source, (2) PolyRoof/Slab holes как отдельные optional experiments. Для каждого указать точные units/tolerance/curve orientation/plane normals/story Z, требуемые поля PR74 и источник каждого компонента. **ГОТОВО:** таблица graph input/output с 2-3 отрицательными кейсами, где невозможно без нового bridge; никаких фиктивных .gh или PASS.
**Задача R3-14B, P1/85:** независимый QA-контракт BREP/IFC/IDS/СП: какие проверки выполняет GH, какие Tapir/AC, какие IfcOpenShell/IfcTester, какие только инженер. **ГОТОВО:** список проверяемых инвариантов и явно NOT_FOUND для отсутствующих нормативных автоматизаций; не считать IDS проверкой геометрии.

### I4 — единая исполнимая схема, P0/100
**Задача I4-14A:** **прекратить расширение архитектуры** и оформить единственный G0→G1→G2 **read-only/offline runbook** с командами, входными файлами, exact repo ref/commit, sourcePlanHash и отказными условиями. Указать, какой PR74 checkout реально нужен и почему исследовательская ветка его не заменяет. **ГОТОВО:** один минимальный approved fixture/spec на >=2 этажа без прежних BDD путей, точная offline CLI команда без execute, полный список ожидаемых файлов/полей/логов, границы прав доступа. Это проект runbook, НЕ выполненный G1.
**Задача I4-14B, P0/98:** сверить блокеры B01 локальный APX/версии, B02 local PR74 checkout, B03 GH→PR74 adapter, B04 story/material/library defaults, B05 single-writer conflicts, B06 Save/Open evidence, B07 PolyRoof optional. **ГОТОВО:** для каждого ID owner, существующий механизм, один следующий безопасный шаг и доказательство закрытия; отсутствие runtime не скрывать. Не предлагать merge или новый router.

## 7. Решения аудитора и передача

1. **G0 — STOP/BLOCKED_RUNTIME** до фактической read-only инвентаризации Windows и локального APX/PLN. Это внешний барьер, а не недостаток очередной теоретической статьи.
2. **G1 — следующий реальный производственный milestone.** После подтверждения подходящего локального checkout/путей допускается отдельный офлайн-прогон существующего PR74, без LIVE и без изменения пользовательских PLN. В текущем цикле запуск не выполнялся.
3. **G2 — SOURCE_PARTIAL:** не расширять обязательную модель до многоскатных кровель, сложных holes и автоматического Rhino↔AC roundtrip. Доказать базовый native SinglePlane first.
4. **G3/G4/G5 — без отдельного разрешения запрещены.** Ни один из текущих отчётов не является разрешением на запись.
5. **NEXT_RESEARCH_PRIORITIES.md не изменён:** канонический файл найден и прочитан; поручение TRIAD-PIVOT прямо запрещает перезаписывать исходную очередь до административного согласования. Текущие задания переданы в отдельном append-only hourly отчёте, исключая риск конфликта.
6. Следующий A5 проверяет закрытие конкретных B01–B07, а не рост числа SOURCE-карточек. При отсутствии G0/G1 прогресса фиксирует STALLED_EXTERNAL_DEPENDENCY.

**Итог:** REPORTS 4/4 VERIFIED; 2 counteraudits performed; BUILD-01 NOT_ACCEPTED; THREE_WAY_NATIVE_SYNC NOT_FOUND; MODEL_MODE_NOT_VERIFIABLE.