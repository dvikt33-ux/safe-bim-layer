# APA R2 — GH→PR74, идентичность и конкурирующие писатели
Дата: 2026-10-24 14Z / 17:00 МСК. Цель: BUILD-01, issue #192. Срез SOURCE_ONLY. MODEL_MODE_NOT_VERIFIABLE.

## 0. Входные документы и граница
Фактически прочитаны: issue #192; A5 13Z (blob 71e752a11e8324086d9ac2d9cec98de01bed8204); R1 13:55Z (blob 8b4e8ffa65b096b8c27b852692ef66f8c84cf771); R3 13Z (blob 6a51de7906bbdc6a454547604dbc75f9f077de06); I4 13Z (blob 343bd8a5586b80b12ad3a0c45cb0931ac6a0e419); NEXT_RESEARCH_PRIORITIES.md (blob 6f074693360231c5cb42ada815984a6b0dd504c0). В начале этого 14Z цикла отчёты R1/R3/I4/A5 14Z ещё не были доступны как проверенные входы; не объявлять их MISSING за весь час. PR74 прочитан из immutable commit 5a3a9201a715a5528c93bed4a5318e2acb32eea7, не из исследовательской ветки. Исторический PROJECT_PLAN rev182 не менялся.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/issues/192

## 1. Новое существенное обнаружение: Tapir GH Package Manager не подтверждён для Rhino 8
Официальный README Tapir рекомендует пакет Grasshopper с именем tapir, но прямо характеризует GH plugin как work in progress: https://github.com/ENZYME-APD/tapir-archicad-automation .
Публичный индекс пакетов Rhino (срез 24.10.2026) показывает tapir GH v1.7.2, обновлён 19.10.2026, distribution tapir-1.7.2-rh7_21-any.yak, метку «No Rhino 8+ build», Works with Rhino 7; лицензия отдельного Yak-пакета в каталоге «Not declared»: https://rhinopackages.github.io/package/tapir .
Документация McNeel определяет rh7_21 как distribution для Rhino 7.21+, rh8 как отдельную платформенную метку; Package Manager показывает совместимые distributions: https://developer.rhino3d.com/en/guides/yak/the-anatomy-of-a-package/ .
Следствие: **не включать Tapir GH package в обязательную конфигурацию Rhino 8** до подтверждения совместимой сборки или установленного запуска. Это не доказательство абсолютной несовместимости бинарника, но точного SOURCE-подтверждения Rhino8 package НЕТ. Не путать версию GH package 1.7.2 с заявленным локальным Archicad Tapir Add-On 1.5.10. Ни один из этих пакетов не требуется для read-only GH→AC через официальный Graphisoft Connector.

## 2. Позитивное подтверждение официального моста
Graphisoft 29 Live Connection build 3000 (Windows 16.8 MB, выпуск 01.10.2025) официально поддерживает Rhino 7/8; Start Edition исключён: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ .
Graphisoft AC29 руководство: https://help.graphisoft.com/AC/29/INT/GC.pdf . Параметр Synchronize=False останавливает передачу из Design/Document-компонента, но возвращаемый Null НЕ является доказанным удалением ранее созданного AC элемента. Историческое обсуждение Graphisoft о необходимости отдельно удалить элементы: https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/m-p/292443/highlight/true .
Graphisoft описывает автоматическую генерацию **настоящих BIM-элементов** через GH Design, но именно это создаёт второго native writer при включённом APA SceneWriter. Для BUILD-01 разрешён только AC→GH Element Input/Deconstruct/Story Plane как reference/readback, без соединения с GH Design output. Старое руководство Graphisoft по производительности отмечает, что активные GH-узлы создают реальный BIM и могут перегружать Archicad; кривые могут давать множество стен; неправильные единицы и последний zero-height column порождают вырожденные элементы: https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564 . Это исторические рекомендации, не локальная приёмка AC29.

## 3. Результат проверки существующего PR74: готовый GH→typed authored intent НЕ обнаружен в проверенном scope
Непосредственно прочитаны 5 файлов PR74 на commit 5a3a9201a715a5528c93bed4a5318e2acb32eea7:
- scripts/archicad_project_accelerator.py, blob 8e0ce2fbb5441009925f0d9199e180e8670a5eea: compile_authored_intent, строки 262–340, принимает authored schemaVersion apa-authored-project/1; нет подтверждённого прямого GH DataTree/BREP парсера.
- scripts/archicad_authored_native_plan.py, blob f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7d: authored layout/stories→typed DAG, но не GH plugin.
- scripts/archicad_bim_graph.py, blob 87fc7476c9079a189c8b8e31ae3c6beaf6712dd3: compile_graph принимает JSON operations, считает sourcePlanHash; не знает Rhino ObjectId.
- scripts/archicad_scene_run.py, blob ca91c1cfc41cee763c62d1f3a70337d74fbafd53: single SceneWriter + SQLite ledger, не GH converter.
- examples/accelerator/model-first-building.json, blob e192fbb31bc872d751c41aa7132f0a4981755051: пример authored intent, не исполняемый GH definition.
GitHub code search по словам Grasshopper, gh_bridge, DataTree, apa-authored-project/1, SceneWriter, rhino в default branch репозитория вернул 0 результатов. ВАЖНО: это не exhaustive search всех веток; PR74 читается по отдельному immutable commit, а исследовательская ветка не является объединённым рабочим деревом.
**Вердикт R2-14A:** EXISTING_GH_TO_PR74_BRIDGE_NOT_FOUND_IN_INSPECTED_SCOPE. Никакого воспроизводимого беззаписного вызова такого bridge и sample output представить нельзя. Нельзя выдумывать JSON-конвертер, вводить новый router/writer или выдавать ручное копирование параметров за автоматизацию. Для G1 уже существует JSON authored intent → PR74 compiler; Rhino/GH на этом шаге факультативны, пока bridge не квалифицирован.

## 4. Новое точное уточнение по SceneWriter: один writer ≠ одна нативная операция
scripts/archicad_scene_run.py:94–97: ALLOWED_WRITES = CreateWalls/Slabs/Columns/Windows/Doors/Objects; opt-in EXTENDED_WRITES = CreateRoofs/Beams/Morphs/MEP, **без ModifyRoofs**.
:295–314: hosted Window/Door ownerWallId обязан быть ссылкой $createdGuid на проверенную Wall; Rhino ObjectId и GH reference здесь не принимаются.
:514–525: только явно подключённые adapters расширяют разрешённый набор.
:776–787: SQLite STARTED reserve, scene_id/plan_hash unique, повтор ambiguous CREATE запрещён.
:801–855: binding check до/после записи, durable ATTEMPTED до вызова API, затем GUID receipt.
:856–893: **CreateSlabs → readback → ModifySlabs(Basic/material)** — две отдельные native mutations под одним SceneWriter, обе требуют receipts. Если CREATE успешен, а MODIFY неизвестен/отказал, нельзя повторять CREATE. Это отдельный риск частично созданного Slab, не «атомарная транзакция».
:894–915: последующая native проверка, host/floor/material. Принцип: SQLite ledger = доказательство последовательности попыток, не AC undo и не гарантированный rollback.

## 5. Матрица идентичности и владельцев
| Идентификатор | Источник истины | Вход в PR74 | Сохранение при обновлении | Критерий/ограничение |
|---|---|---|---|---|
| AC internal GUID | Archicad GetDetailsOfElements/GetAllElements | Native receipt после CREATE; для hosted только $createdGuid | Изменение native элемента может сохранить GUID; замена/удаление нет гарантии | Сравнить GUID+type+host+story+material до/после reopen |
| Rhino ObjectId | Rhino 8 document object | Не принимается как AC GUID | Content Cache Pull/Push может отслеживать Rhino ID | Rhino ID НЕ доказывает native AC identity |
| GH component/persistent reference | GH definition/document | Нет подтверждённого штатного typed bridge | Зависит от .gh и соединения; нет доказанного AC GUID mapping | Зафиксировать .gh SHA, source_key; без write |
| IFC GlobalId | IFC entity после экспорта | Нет прямого доказанного соответствия AC internal GUID | Может зависеть от экспорта и настроек | Проверять IFC mapping отдельно, не сравнивать строки GUID как равные |
| APA operation id / sourcePlanHash | BIM Graph + SQLite SceneWriter | id, command, params, dependencies, hash | Не является native element GUID | Журнал+native readback; unknown → STOP |
| Tapir API elementId | Archicad JSON API | GUID native element после CREATE | Требует фактического GetDetailsOfElements | Только из AC receipt, не из Rhino |

## 6. Десять маршрутов для I4, с окончанием и критериями ГОТОВО
| № | Операция: программа → готовый инструмент → передача | Проверка после завершения и Save/Open | Статус |
|---|---|---|---|
| 1 | AC Story Settings/GetStories → typed story binding PR74; GH Story Plane только reference | floorId/index/elevation, Z абсолютный vs относительный | SOURCE; INSTALLED не проверен |
| 2 | Rhino оси/контуры → GH проверки единиц и ненулевой длины → authored PR74 CreateWalls → SceneWriter/Tapir | Wall GUID, thickness, height, floor, material, BREP | SOURCE; GH auto bridge NOT_FOUND |
| 3 | GH planar footprint → PR74 CreateSlabs → SceneWriter Create + ModifySlabs при material binding | Slab GUID, level, Basic/material, hole loops отдельно, reopen | SOURCE; partial mutation risk; holes readback NOT_FOUND |
| 4 | GH points/section → PR74 CreateColumns → SceneWriter | Column GUID/height/width/depth/story/child segments/BREP | SOURCE; локальная schema не проверена |
| 5 | GH straight axis → существующий connected CreateBeams opt-in SceneWriter | Beam/BeamSegment GUID/host/material/closed BREP | SOURCE; unified G1 route NOT_VERIFIED |
| 6 | GH single plane → PR74 CreateRoofs с pivotLine/Basic/material → SceneWriter opt-in | native SinglePlane Roof GUID, pitch, material, BREP | SOURCE; новый LIVE NOT_RUN |
| 7 | GH multi-plane geometry → upstream Tapir CreateRoofs без pivotLine или ModifyRoofs | нужен native PolyRoof GUID, ridges/valleys, materials, reopen | SOURCE_TOOL_FOUND; PR74 ROUTE_NOT_FOUND; прямой writer запрещён |
| 8 | GH opening host intent → PR74 CreateWindows/Doors с $createdGuid Wall → SceneWriter | Window/Door GUID, ownerWallId, width/height/sill, libpart/marker | SOURCE; frozen schema vs upstream drift |
| 9 | Rhino Content Cache Pull/Query Model Objects → GH read-only geometry; AC→GH Deconstruct | Rhino ObjectId отдельно от AC GUID; не Bake/Push/Purge | SOURCE; это не трёхсторонняя sync |
| 10 | AC native readback + GH geometric QA + отдельный IFC/IDS/IfcOpenShell | GUID/type/story/host/material/BREP и IFC GlobalId раздельно, no duplicate | SOURCE; автоматическая нормативная экспертиза NOT_FOUND |

Общий будущий маршрут каждой операции: read-only G0 → frozen authored input/plan hash G1 → schema+ownership G2 → **только после разрешения** SceneWriter native G3 → native readback → GuardedSave/Close/Reopen G4 → independent diff → G5 второе новое здание. Ни один маршрут не получил новых LIVE receipts в этом цикле.

## 7. Конфликты, удаление, циклы, rollback — отказные сценарии
C1 External GH CREATE: GH Design Synchronize=True и SceneWriter одновременно создают Wall. Два writer, два набора AC GUID, SQLite не знает внешний элемент. **STOP; запретить GH Design writes**, сравнить native inventory с ledger; никакой автоматической «синхронизации».
C2 Lost GH link: Synchronize=False/закрытие .gh даёт Null/разрыв обновления, но ранее созданный AC элемент может оставаться. **Не удалять по пустому GH output; STOP и read-only AC GUID inventory**.
C3 Duplicate CREATE after timeout: SceneWriter записал ATTEMPTED, ответ API потерян; повтор того же плана запрещён guard по scene_id/plan_hash. **STOP → SQLite+native readback+ручная сверка**, а не новый scene_id.
C4 Partial slab: native CreateSlabs создал GUID, последующий ModifySlabs(material) завершился UNKNOWN. **STOP, не повторять CreateSlabs**, сохранить журнал, отдельно прочитать Slab GUID/material и согласовать исправление.
C5 External delete/edit: ручное изменение или удаление native Wall нарушает host у Window/Door. **STOP на inventory/host drift**; автоматическое восстановление/пересоздание без нового разрешения запрещено.
C6 AC→GH→AC feedback: выход Element Input/Deconstruct подключён к Design Create/Modify; возникает петля/перезапись. **Разорвать write branch**, не считать выключение Synchronize откатом.
Rollback: SQLite не транзакция PLN, Rhino Undo не отменяет Archicad, GH solution не откатывает PLN. Гарантированный cross-app atomic rollback **NOT_FOUND**. Единственный предлагаемый путь — санкционированная scratch snapshot + restore после независимой сверки, не выполнять сейчас.

## 8. Два контрааудита
CA-R2-01 источники/версии/лицензии: Graphisoft AC29 build3000/Rhino8 подтверждено; Tapir GH Yak 1.7.2 имеет только rh7_21 distribution по публичному каталогу, его лицензия там не объявлена; upstream Tapir repo MIT не заменяет проверку лицензии конкретного пакета; local Tapir APX 1.5.10, Rhino8 SR, GH .gh, лицензии приложений и установленные плагины НЕ проверены. Вывод: GRAPHISOFT_SOURCE_PASS / TAPIR_GH_RH8_COMPATIBILITY_NOT_VERIFIED / G0_BLOCKED.
CA-R2-02 воспроизводимость: пять файлов PR74 содержат typed JSON→BIM Graph→SceneWriter, но не готовый GH DataTree→typed parser; исследовательская ветка не содержит единого checkout; 2-step slab create/modify и external GH writer нарушают атомарность. Вывод: BASE_G1_JSON_ROUTE_SOURCE_FOUND / GH_TO_PR74_AUTO_NOT_FOUND / 3WAY_SYNC_NOT_FOUND / LIVE_NOT_AUTHORIZED.

## 9. 24 конкретные SOURCE-проверки (не 24 независимых сайта и не LIVE-тесты)
S01 issue #192 прочитан; S02 A5 13Z fetch+SHA; S03 R1 13:55Z fetch+SHA; S04 R3 13Z fetch+SHA; S05 I4 13Z fetch+SHA; S06 NEXT_RESEARCH_PRIORITIES canonical path+SHA; S07 Graphisoft download AC29 build3000/Rhino8; S08 Graphisoft Start Edition exclusion; S09 Tapir upstream README GH WIP; S10 Tapir Yak v1.7.2 rh7_21; S11 Yak «No Rhino 8+ build»; S12 Yak license «Not declared»; S13 McNeel distribution rh7_21/rh8 semantics; S14 McNeel Package Manager compatible distribution filtering; S15 Graphisoft Synchronize=False→Null (AC29 guide); S16 Graphisoft community older non-deletion behavior; S17 Graphisoft GH Design real BIM/performance caution; S18 PR74 project_accelerator authored schema/compiler; S19 PR74 authored_native_plan source; S20 PR74 bim_graph sourcePlanHash; S21 PR74 SceneWriter allowlists and hosted binding; S22 PR74 SQLite reserve/no automatic retry; S23 PR74 slab CREATE→MODIFY; S24 PR74 example authored intent. Каждая S — отдельно проверенное утверждение или конкретный файл, не утверждение о 24 уникальных URL.

## 10. Передача I4/A5 — только закрывающие действия
I4 P0/100: зафиксировать, что Tapir GH Yak не имеет подтверждённого Rhino8 distribution; исключить его из обязательного G0; официальный Graphisoft AC29 build3000 — единственный подтверждённый для Rhino8 готовый bridge.
I4 P0/100: G1 запускать по существующему JSON authored intent PR74, не ждать автоматического GH bridge; GH source вносить как ручной подтверждённый typed input, не называть это автоматической трёхсторонней сборкой.
I4 P0/98: включить в runbook отказный C4 (CreateSlabs→ModifySlabs), отдельный material readback, durable ledger; no retry.
A5 P0/98: закрыть R2-14A как scoped NOT_FOUND, не делать из отсутствия GH parser в 5 файлах вывод о всех ветках; G1 OFFLINE не повышать без фактического compiler receipt.
R2 next P1/87: если потребуется расширенный поиск, read-only проверить конкретные новые ветки по GH parser path/commit и upstream Tapir GH Rhino8 build; при отсутствии — NOT_FOUND, не разрабатывать.

## 11. Статусы и запреты
SOURCE: 24 предметных проверки; OFFLINE: 0 новых; BUILD: 0; INSTALLED: NOT_VERIFIED; LIVE: 0 новых; ACCEPTED: 0. G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4=NOT_RUN; G5=NOT_RUN. Готовая полноценная трёхсторонняя native BIM синхронизация, GH→PR74 auto bridge, atomic rollback, гарантированное сохранение AC GUID через Rhino/IFC: NOT_FOUND.
Не менялись main, исходный код, PLN/APX, установленные программы, merge, платные API, Work/Codex/Arena. Создан только исследовательский markdown в разрешённой ветке.
MODEL_MODE_NOT_VERIFIABLE.
