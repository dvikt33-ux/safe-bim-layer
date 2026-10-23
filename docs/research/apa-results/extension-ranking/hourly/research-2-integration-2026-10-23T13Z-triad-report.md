# APA №2 — 23.10.2026 13Z — инженерный отчёт BUILD-01 (Archicad29/Rhino8/GH)

## Конкретный вклад в BUILD-01 — G2: исправлен маршрут проверки GDL identity (приоритет 99/100)
Прямое чтение `scripts/archicad_authored_extension.py` (immutable commit `f7c37b84b76c040c417ccd58a5543326e50f673a`) показало **существующий** `verify_model` readback для `nativeLibraryExpectations[sid]`: сравниваются `GetDetailsOfElements.details.libPart.name` и `libPart.ownUnID.guid`. Это уже готовая проверка идентичности библиотечной части; второй writer или новый GDL checker НЕ нужен.

**Точный оставшийся блокер:** текущий `examples/accelerator/model-first-building.json` не задаёт `nativeLibraryExpectations` (и не задаёт libraryPartName/favoriteName в показанных CreateDoors/Windows), поэтому эта ветка readback не активируется для sample. Исторический GDL PASS нельзя переносить на BUILD-01. Без WRITE можно получить доступные библиотечные части через pinned `GetAvailableLibraryParts(filterByTypeId)`, избранное через `GetFavoritesByType(elementType)`, затем подготовить утверждённые `name` и `ownUnID.guid` expectations. **Автоматическая привязка этого словаря к PR74 fixture: NOT_FOUND / CONDITIONAL_WIRING**, проверить через existing compiler и preflight, не создавать новый engine.

## Второй конкретный результат — конфликт GH/AC правок (приоритет 100/100)
Официальный AC29 Grasshopper Live Connection использует ID-based association для **GH-generated** Archicad элементов; это не обещание сохранения произвольных GUID, созданных SceneWriter. GH Design/Document создают реальные первоначально LOCKED элементы. После unlock пользователь может менять их в Archicad, но значения параметров, управляемых GH, имеют приоритет при следующем вычислении. Незаданные GH параметры наследуют текущие AC Tool Defaults при генерации. Это два самостоятельных риска: `silent overwrite` и `nondeterministic BIM defaults`.

**Проверяемое правило для BUILD-01:** все APA-owned native элементы пишет только SceneWriter/SQLite; GH Design `Synchronize=FALSE` на том же scope. GH можно использовать как reference/geometry calculator, AC→GH Deconstruct/Extract Settings/Send Changes (где поддерживается), но GH-created objects — другой ownership scope. Rhino/GH solver toggle не является native commit, а GH ID не является общим transaction ID. FULL_AUTO_THREE_WAY_SAME_GUID=NOT_FOUND.

## Третий результат — найден готовый альтернативный интерфейс Tapir GH, но не квалифицирован
Upstream ENZYME-APD `tapir-archicad-automation` — MIT; Rhino Package Manager содержит GH package `tapir`. Однако разработчик называет GH plugin `work in progress`, а coverage checklist — статической проверкой кода, не runtime test. Для BUILD-01 этот plugin не является доказанным способом подать произвольный GH output в PR74 typed DAG; его native writes также обходили бы SceneWriter. Статус `SOURCE_CANDIDATE_NOT_INSTALLED`, не рекомендован к установке до G0/G1. Источники: https://github.com/ENZYME-APD/tapir-archicad-automation ; https://enzyme-apd.github.io/tapir-archicad-automation/gh-coverage/

## Готовая последовательность без разработки нового исполнителя
**G0 READ:** Archicad29 build5101 / фактический Tapir1.5.10 APX SHA + loaded commands/schema / port+scratch PLN / stories/elevations / material GUID / GDL ownUnID / Rhino8 license / GH AC29 build3000 binary. Provider release != installed contract. G0 пока BLOCKED_RUNTIME.

**G1 SOURCE→OFFLINE:** использовать существующий PR74 authored intent `apa-authored-project/1` + `compile_candidate` и BIM Graph; подготовить НОВОЕ двухэтажное задание, а не повторять fixture. CLI preflight указан в `docs/APA_MODEL_FIRST_BUILDING.md`; настоящий OFFLINE_PASS возможен только после запуска вне данного исследовательского прохода. G1 NOT_RUN.

**G2 READ schema:** Tapir pinned CreateWalls/Slabs/Columns/Beams/Roofs/Doors/Windows; ownerWallId через `$createdGuid`; floors `nativeStoryBindings`; materials через `GetAttributesByType`. `CreateSlabs` НЕ имеет `structureType/buildingMaterialId`, отдельный `ModifySlabs` с явным разрешением и readback. Beam NativeAdapter есть, `run_project` подключает только roof. SinglePlane Roof Basic + explicit pivotLine/angle/material; complex MultiPlane↔GH same GUID native roundtrip NOT_FOUND. GDL readback exists conditional, sample binding missing. G2 SOURCE_ONLY.

**G3 ONLY WITH EXPLICIT OWNER AUTH:** exact scratch PLN+SHA/port+plan hash; original SceneWriter+SQLite intent-before-write; phased native writes, each GUID readback; UNKNOWN→STOP/READ reconciliation, no blind retry. GH Synchronize FALSE for APA-owned. G3 NOT_AUTHORIZED.

**G4:** GuardedSave, GUI Close/Open, independent GUID/type/story/host/GDL/material/SEO/BREP; pinned catalog does NOT contain GetModelDumpV1, installed native BREP contract unverified. G4 NOT_RUN.

**G5:** second structurally different intent on another scratch PLN; until then `BOUNDED_DEMO`, not universal BUILD-01. G5 NOT_RUN.

## Девять приоритетных сценариев
T01 G0 stories/attributes (100); T02 Walls (100); T03 Slabs (100); T04 Columns+Beams (98); T05 SinglePlane Roof (99); T06 MultiPlane/NURBS Roof (97, NOT_FOUND native roundtrip); T07 hosted Door/Window+GDL (99); T08 AC↔GH reference/parameter edits (97, full three-way NOT_FOUND); T09 conflict, Save/Open, second model (100). Детальные команды, направления, критерии ГОТОВО в `triad-matrix.md`.

## Версии и лицензии (SOURCE, не INSTALLED)
- Graphisoft GH–Archicad **29** Live Connection **build3000**, Windows 16.8MB, Rhino7/8, 2025-10-01. На той же странице AC30 build3000 от 2026-10-07; не перепутать. Бесплатное официальное дополнение, но AC/Rhino требуют собственных лицензий. https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- Rhino8 Grasshopper встроен; `-Grasshopper Solver Disable/Enable`, `-GrasshopperPlayer` для .gh/.ghx. Trial 90 дней, после него saving/plugins stop. https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm ; https://www.rhino3d.com/download/
- Tapir upstream MIT, GH plugin WIP; установленный бинарный контракт 1.5.10 не подтверждён. https://github.com/ENZYME-APD/tapir-archicad-automation
- Graphisoft built-in Rhino .3dm import/export с AC25; это не гарантирует нативные Wall/Roof/Slab и не заменяет GH/APA. https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/

## Доказательность и ограничения
**SOURCE:** 30 отдельных проверенных утверждений (не 30 файлов/тестов); 9 сценариев; 2 контрааудита этого исследователя. **OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0** новых результатов BUILD-01. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. 06Z PARTIAL_NOT_ACCEPTED (оригинальный основной отчёт отсутствует). Нормативные проверки остаются предварительными и не заменяют официальную экспертизу. AC29 PDF 22.8MB прочитан только через официальный поисковый индекс, полный page audit NOT_DONE. №1 TRIAD-PIVOT 11Z и №3 NEXT queue 20.10 прочитаны; свежий самостоятельный №3 23.10 не найден по проверенным путям. Исторический PROJECT_PLAN rev182 не редактировался, путь в данном проходе не установлен.

**Изменения:** только исследовательские markdown/manifest в branch `research/apa-extension-ranking-hub-20261018`. Никаких main/NEXT/кода/PLN/APX/установки/LIVE/merge/платных API. MODEL_MODE_NOT_VERIFIABLE.
