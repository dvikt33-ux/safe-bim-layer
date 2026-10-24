# APA №2 | 2026-10-24 08Z | BUILD-01: roof-plane authority, ridge rejoin, G0 provenance
**Статус: SOURCE_ONLY / WRITE-PROTECTED.** Исследование для issue #192. Никакого нового writer/router/synchronizer, установки, LIVE, изменений main/PLN/APX/исходного кода/merge. Ожидаемые Windows11, AC29 build5101, Tapir1.5.10, Rhino8 SR UNKNOWN; фактический INSTALLED не проверен. MODEL_MODE_NOT_VERIFIABLE.

## Новые P0-выводы

**I08-01 | GH Roof не берёт pitch из Favorite.** Официальный Graphisoft AC29 GC.pdf, стр.28: planar Curve/Surface polygon для GH Roof задаёт **контур, пространственную плоскость, уклон и высоту** native Single-plane Roof. Roof Settings/Favorite Offset from Home Story и Roof Pitch **не определяют** эту геометрию. PR74 authored nativeComponents CreateRoofs — **другой** контракт: Basic Single-Plane, typed buildingMaterialId, pivotLine, floorIndex и ограничение polygon до outline+0.35m (pinned code, lines 293–311). Поэтому сравнение названия Favorite или угла в настройках недостаточно для признания эквивалентности GH→AC и PR74→AC. Требуется сравнение геометрической плоскости (origin/normal), уклона, абсолютной Z, pivot line, контура, native GUID/tool, floorIndex, материала и BREP. Если поле неизвестно — FAIL_CLOSED, а не «эквивалентно». Никакой конвертации автоматически не доказано.

**I08-02 | Изменение pitch может нарушить конёк даже при успешной синхронизации.** Официальная Graphisoft Support статья от 15.10.2025 прямо описывает Single-plane Roof junction, не обновившийся в разрезе после изменения уклона; рекомендует adjust/rejoin двух скатов. Для BUILD-01 нужно после каждой операции изменения pitch проверить пересечение двух BREP по линии конька, отсутствие щели/перекрытия, секущий разрез и roof-wall Trim/SEO. У PR74 nativeRoofJunctions есть ограниченный отдельный путь completion через существующий archicad_authored_extension, но это **не** доказательство универсальной автоматической команды rejoin двух Single-plane Roof. Готовый unattended rejoin на обоих writers — NOT_FOUND.

**I08-03 | G0 catalog provenance строже «schema файл существует».** PR74 catalog_with_provenance требует _metadata.origin=live TapirCommand.GenerateDocumentation, provider_version=RUN.EXPECTED_TAPIR, SHA256 двух source JS и **точное равенство** восстановленного каталога. Отдельный JSON с похожими командами или сохранённый static snapshot не достаточен. EvidenceAPI и native_transport не гарантируют текущую установленную регистрацию. Требуется read-only runtime manifest на фактическом PLN/порту/APX, а не SOURCE-документ. Без этого G0=BLOCKED_RUNTIME, G1 не объявлять OFFLINE_PASS.

**I08-04 | Разграничение полномочий.** Для APA-owned native GUID — только PR74→BIM Graph→SceneWriter/SQLite→Tapir. Для GH-owned — Graphisoft GH Design компоненты (после отдельного допуска); для Rhino-owned — GH Content Cache Push (после отдельного допуска). GH Roof может создавать native Roof, но это **другой writer**, без receipts SceneWriter. Переход изменения AC→GH через Deconstruct/Sync Changes не означает запись в .3dm. Путь с единым 3-way commit/rollback/GUID crosswalk = NOT_FOUND.

## Готовые инструменты и лицензии

- Graphisoft AC29 Grasshopper–Archicad Live Connection **build 3000**, Windows 16.8 MB, Rhino7/8, опубликован 01.10.2025; скачивание расширения отдельно от коммерческих лицензий AC29/Rhino8. **Не подменять AC30 build3000**. Доказательство: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/.
- Grasshopper в Rhino8, Rhino Query Model Objects и Content Cache — штатные средства Rhino, но установленный Rhino SR UNKNOWN. McNeel Rhino Query Synchronise=False — frozen temporary reference; Content Cache Action=False не останавливает Pull при видимом Result. Источники https://discourse.mcneel.com/t/model-object-component-update-problem/168818/5, https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1.
- APA PR74, authored compiler, SceneWriter/Tapir — существующие инструменты; версия pinned code 5a3a9201, **не установленный runtime**. https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py, https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py, https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py.
- IFC/IfcOpenShell и GH геометрические расчёты — только независимый QA; не writer native BIM и не юридическая экспертиза.

## G0 → G5 воспроизводимая последовательность (в этом проходе НЕ выполнялась)

**G0 READ ONLY.** Проверить AC29 product/build, Tapir GetAddOnVersion, точный порт, GetProjectInfo (path/name/untitled/teamwork), story index/floorId/Z, SHA/APX, native command registration/schema, material GUID, library part GUID/skippedCount; отдельно Rhino8 SR/active .3dm path+units+hash, GH active .gh+hash/definition, Graphisoft Connection Palette port+target document. Порт GH≠автоматически Tapir 19723. Неизвестный PLN/несохранённый оригинал/unknown owner => STOP.

**G1 OFFLINE/PREFLIGHT.** Использовать ровно authored schemaVersion=apa-authored-project/1, units=meters, brief.targetProjectPath=RUN.EXPECTED_PATH; заранее approved scratch binding (saved copy SHA+authorization_ref). Важное ограничение: authored mode=offline не принимается; требуется mode=preflight с callable read-only transport. Получить typed DAG, dependency order, sourcePlanHash, collisions и no-change GUID inventory. Rhino→GH→authored JSON **универсального готового автоматического конвертера нет**; только структурированный intent, удовлетворяющий контракту.

**G2.** Сверить конкретные CreateWalls/Slabs/Columns/Roofs/Windows/Doors, hostWall, story, material GUID, GDL parts, roof plane/pivot, SEO, actual schema. Beam в authored allowlist отсутствует, GH Beam отдельно GH-owned. Не обходить guard.

**G3.** Только после отдельного разрешения конкретного scratch PLN/port/planHash: единственный SceneWriter dispatch с SQLite intent-before-write; при UNKNOWN/timeout STOP и read-only reconcile, никакого повторного CREATE.

**G4.** GuardedSave → фактическое закрытие → повторное открытие → независимый GUID/native tool/story/host/material/BREP/roof ridge/SEO audit, сравнение с до-записью и IFC (BREP отдельно от параметров). При несовпадении BLOCKED, не ACCEPTED.

**G5.** Повторить с другим структурированным зданием на другой изолированной PLN, не дублируя 21-element historical prototype. Без G5 только bounded demonstration.

## 10 операций BUILD-01: выбор → изменение → окончание → передача → QA → Save/Open/откат

| # | Операция / владелец / готовые компоненты | Направление и окончание | QA/критерий ГОТОВО | Доказательность |
|---|---|---|---|---|
| 1 | Этажи / AC native Stories + PR74 storyBindings | AC read-only → authored floor index; Rhino/GH z reference | index/floorId/elevation, units, PLN path, reopen; откат snapshot | SOURCE; INSTALLED unknown |
| 2 | Стены / Rhino curves+GH Query → authored CreateWalls | После завершения GH расчёта передавать только проверенный authored intent в APA; нет generic auto adapter | native Wall GUID/tool, host, thickness, material, 3D bbox/BREP; reopen; snapshot | SOURCE; auto GH→JSON NOT_FOUND |
| 3 | Перекрытия / PR74 CreateSlabs | authored rectangular footprint/story, absolute level, SceneWriter | GUID, slab top Z, thickness, actual building material, holes; reopen | SOURCE; arbitrary holes NOT_FOUND |
| 4 | Колонны / PR74 nativeComponents CreateColumns | GH points как источник координат; только authored typed intent → APA | story, XYZ, segments GUID, profile, BREP, reopen | SOURCE |
| 5 | Балки / GH Beam Settings→native AC Beam | GH-owned writer отдельно, не APA-owned; после разрешённого GH sync | GUID count при 3D curve segmentation, material/profile, reopen | GH SOURCE; APA-owned NOT_FOUND |
| 6 | Простая кровля / GH Roof planar polygon **или** APA CreateRoofs | GH-owned: плоскость полигона задаёт pitch/Z; APA-owned: pivotLine/Basic/material/story | origin/normal/pitch/Z, native GUID/tool, ridge, BREP, material, reopen | SOURCE; equivalence NOT_PROVEN |
| 7 | Сложная кровля / AC native Multi-plane Tool | AC UI единый native Multi-plane; GH Deconstruct Roof только single-plane; PR74 native multi-plane absent | один native Roof GUID, multiple planes/SEO, reopen; автоматический route NOT_FOUND | SOURCE; automatic NOT_FOUND |
| 8 | Двери/окна / PR74 CreateDoors/CreateWindows | APA-owned: typed hostWall native GUID, library part, floor, размеры | native Window/Door GUID, host relation, actual cut BREP, library resolved, reopen | SOURCE; library INSTALLED unknown |
| 9 | Библиотеки/материалы / AC GetLibraries/GetAvailableLibraryParts/GetBuildingMaterials | Read-only preflight; не создавать GH library part для APA-owned | part GUID, skippedCount, availability, buildingMaterial GUID, missing objects=0 | SOURCE; no runtime |
| 10 | QA, нормативы, удаление/конфликты / native readback+IFC+GH | После завершения одной операции — read-only diff; при 2 writers/unknown owner STOP | GUID add/remove, floor, material, normals, ridge, collision, clearances, accessibility; Save/Close/Reopen, rollback saved files | SOURCE; full 3-way NOT_FOUND |

**Правило синхронизации:** автоматическая GH→AC запись не является автоматическим AC→Rhino update; AC→GH reference не равен изменению Rhino .3dm; Rhino Content Cache Push не создаёт native Wall/Roof. Удаление или recreate требует отдельной проверки GUID/cardinality/host/SEO и отсутствия непреднамеренного удаления. Никакого «last write wins» или глобального Undo; rollback только заранее сохранёнными версиями и повторной инвентаризацией. Нормативные вычисления (площадь, высоты, эвакуация, доступность) — контрольные гипотезы до подтверждения применимых СП и параметров, не экспертное заключение.

## Статусы и приоритеты

SOURCE=33 документарных утверждения в companion checks (не 33 разных сайта). OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. Нативная BUILD-01 не создана. Следующий P0 — read-only G0 manifest + roof-plane comparison contract для будущего preflight, не GH write.

**Контрааудиты:** companion audits. **База:** issue #192, NEXT, TRIAD-PIVOT, 61 matrix, №1 08:02Z, №3 20.10 18Z, pinned PR74. Исторический PROJECT_PLAN rev182 не изменён.