# APA №1 | 2026-10-24 06:01Z | AC→GH auto-sync, GH ownership, GDL identity

## 0. Реальное влияние на BUILD-01 #192 и статусы

**Новая P0-дельта:** официальный **Graphisoft Grasshopper–Archicad 29 Live Connection** содержит **Sync Changes to GH**. При включённой кнопке изменения *подключённых* элементов Archicad автоматически и непрерывно обновляют Grasshopper. Следовательно, ранее сформулированное ограничение «AC→GH всегда требует ручного Send Changes» неверно для AC29 при включённом режиме. Но это **не** автоматическое обновление Rhino Object ID, не общий commit/rollback, не сохранение GUID при пересоздании, не предотвращение циклов. Отдельно **Lock/Unlock GH Elements** возвращает GH-контролируемые параметры к GH-значениям при relock, сохраняя отдельные AC-only параметры (пример: CW Panel Building Material). Это P0-конфликт с APA SceneWriter.

**Новая P0-дельта библиотеки:** GH **Object Settings → Create New Library Part** действительно создаёт обновляемую GDL-часть в Embedded Library. Но удаление GH Object Settings или переключение на Use existing Library Part удаляет созданную часть, а её размещённые экземпляры становятся Missing Objects. **GDL Main ID** (тип) и **GLOB_INTGUID** (экземпляр) — разные идентичности. Это не безопасная замена native Roof/Window/Door.

**SOURCE_ONLY: 26 документарных/репозиторных сверок, 8 карточек, 2 контрааудита. OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых.** G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. **AC↔Rhino↔GH full native BIM sync = NOT_PROVEN. MODEL_MODE_NOT_VERIFIABLE.**

Конфигурация: AC29 build5101, Win11, Tapir1.5.10, Rhino8/GH1. Не менять main, код, PLN/APX, установленное ПО; не выполнять LIVE, merge, Work/Codex/Arena, платные API. PROJECT_PLAN rev182 только чтение.

## 1. Восемь карточек (операция → версия/лицензия/контракт/направление → ограничения → №2)

### F0601-01 — AC29 Sync Changes to GH, условное автоматическое AC→GH
**Операция:** изменить стену/Single-Plane Roof в AC и получить обновлённый GH reference input.
**Первоисточник:** Graphisoft AC29 GC.pdf, раздел Grasshopper Palette, https://help.graphisoft.com/AC/29/INT/GC.pdf ; официальный add-on AC29 **build 3000**, Windows, Rhino7/8, 01.10.2025: https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ .
**Лицензия:** официальный скачиваемый add-on для коммерческих Archicad и Rhino; GH включён в Rhino8. Установка NOT_VERIFIED.
**Контракт/направление:** Sync Changes to GH ON → continuous automatic update connected Archicad elements **AC→GH**; OFF → нет автоматического обновления. Это не AC→Rhino write и не triad transaction.
**Ограничение:** задержки, возможный GH downstream feedback, GUID/host/material/type/Story не проверены.
**№2 I0601-01:** SOURCE-схема ON/OFF, connected scope, ownership, readback и STOP при цикле. Ничего не включать.

### F0601-02 — Lock/Unlock GH Elements и параметрический приоритет
**Операция:** локальная правка GH-generated Curtain Wall panel/material.
**Первоисточник:** AC29 GC.pdf, Grasshopper Palette; add-on build3000.
**Лицензия:** штатный UI официального add-on, коммерческие AC/Rhino.
**Контракт/направление:** Unlock → AC правит GH-generated элемент; relock → GH-controlled values восстанавливаются из GH. Исключение: параметры, не управляемые GH (пример CW Panel Building Material), сохраняют AC-значение. **GH authority→AC**, не двусторонний merge.
**Ограничение:** локальный GUID/SEO после relock NOT_VERIFIED; конфликт SceneWriter.
**№2 I0601-02:** parameter ownership matrix: GH-controlled / AC-only / APA-owned / UNKNOWN; конфликт → STOP.

### F0601-03 — Select in GH, штатная трассировка GH provenance
**Операция:** по выделенному в Archicad GH-generated элементу найти управляющий компонент.
**Первоисточник:** AC29 GC.pdf, Grasshopper Palette; build3000.
**Лицензия:** штатная функция add-on.
**Контракт/направление:** **AC selected GH-owned element → GH generating component**; только для элементов, действительно созданных GH.
**Ограничение:** не GUID crosswalk для APA-owned; не доказывает сохранение ID после copy/recreate.
**№2 I0601-03:** read-only G0 provenance checklist; не считать Select in GH проверкой GUID.

### F0601-04 — Create New Library Part: обновление + каскадное удаление
**Операция:** GH-defined декоративный Object из Rhino geometry в AC Embedded Library.
**Первоисточник:** AC29 GC.pdf, раздел Create New Library Part, стр.45; build3000.
**Лицензия:** штатный add-on.
**Контракт/направление:** **GH Geometry→Object Settings→AC Embedded Library**; изменение GH Geometry обновляет Library Part. Удаление GH Object Settings **или** переключение Use existing Library Part удаляет generated part; размещённые экземпляры становятся **Missing Objects**.
**Ограничение:** GDL Object не native Roof/Wall/Window; нет доказанного GUID-preserving update.
**№2 I0601-04:** запретить для APA-owned roof/window/door; подготовить read-only inventory Embedded Library/placed instances/missing objects.

### F0601-05 — Property Settings GH: полноценный отдельный writer метаданных
**Операция:** присвоить Classification/Property GH-generated элементу.
**Первоисточник:** AC29 GC.pdf, раздел The Property Settings Component, стр.46; build3000.
**Лицензия:** штатный add-on.
**Контракт/направление:** выбрать Classifications → доступные Properties → GH может overwrite Archicad Property values. **GH→AC native metadata write**.
**Ограничение:** второй writer для APA-owned элементов, риск race с SceneWriter; не read-only.
**№2 I0601-05:** сравнить контракт GH Property Settings и существующий SceneWriter/ApplyFavorites; не выполнять GH property write к APA-owned.

### F0601-06 — GDL Main ID и instance GUID: разная идентичность
**Операция:** сохранить корректность библиотечных окон/дверей при будущих обновлениях.
**Первоисточник:** AC29 GDL Reference Guide, Compatibility issues / Migrating Elements, https://help.graphisoft.com/AC/29/INT/GDL.pdf ; GDL Center General Libpart Parameters, https://gdl.graphisoft.com/reference-guide/general-object-parameters/ .
**Лицензия:** штатный GDL коммерческого AC29.
**Контракт/направление:** GDL **Main ID** определяет совместимость Library Part и правила миграции; **GLOB_INTGUID** — внутренний GUID экземпляра, не задаётся пользователем. **Type identity ≠ instance GUID ≠ Rhino Object ID**.
**Ограничение:** переименование не мигрирует несовместимые параметры; замена Main ID может потребовать migration scripts.
**№2 I0601-06:** колонки AC GUID / GDL Main ID / Library Part / GH source / Rhino ID; не делать миграцию.

### F0601-07 — Rhino8 native Object Attributes/UserText без стороннего плагина
**Операция:** read-only отбор Rhino геометрии кровли/фасада по layer, material, UserText.
**Первоисточник:** McNeel Rhino8 Object Attributes https://www.rhino3d.com/en/docs/guides/grasshopper/object-attributes/ ; Rhino8 Features https://www.rhino3d.com/en/features/ .
**Лицензия:** Rhino8 коммерческий, GH1 включён, доп. плагин не нужен.
**Контракт/направление:** Rhino document attributes/UserText→GH native Query/DataType components; GH также может писать Rhino-side attributes.
**Ограничение:** Rhino material не Archicad Building Material; UserText не гарантирует AC GUID; side effects могут пересчитать GH.
**№2 I0601-07:** read-only SOURCE схема APA_Type/Story/Owner/SourceObjectId, reject UNKNOWN, без bake/записи.

### F0601-08 — GH Data Dam: граница потока, не atomic commit
**Операция:** закончить подготовку сложной геометрии перед потенциальным GH→AC действием.
**Первоисточник:** стандартный GH1 Data Dam в component index https://grasshopperdocs.com/completeIndex.html ; McNeel developer Daniel Piker, 07.05.2020 https://discourse.mcneel.com/t/geometry-record-and-automatic-slider/101637 ; Rhino8 GH included https://www.rhino3d.com/en/features/ .
**Лицензия:** GH1 в Rhino8, без дополнительной платы.
**Контракт/направление:** GH upstream→Data Dam→downstream; ручной release задержанных данных.
**Ограничение:** не блокирует обходные GH ветви и AC edits; не GUID gate, не rollback, не двухфазная транзакция.
**№2 I0601-08:** SOURCE-only схема Dam + GH Synchronize=False + AC Sync Changes to GH OFF при подготовке; не выполнять LIVE.

## 2. Реестр 26 предметных SOURCE-сверок

Число означает проверенные документарные утверждения/репозиторные состояния, НЕ 26 запусков программ. [R] GitHub research branch; [G29] AC29 GC.pdf; [GS] Graphisoft download; [GDL] AC29 GDL/GDL Center; [MC] McNeel Rhino8 docs; [DAM] GH index/McNeel forum.

| № | Предмет | Результат/источник |
|---|---|---|
| 01 | Имя research branch существует | PASS [R] search_branches |
| 02 | TRIAD-PIVOT файл прочитан | PASS [R] |
| 03 | NEXT_RESEARCH_PRIORITIES.md находится в extension-ranking, не корне | PASS [R] |
| 04 | Матрица count/items/unique ID = 61/61/61 | PASS [R] priority_matrix_20261018.json |
| 05 | BUILD-01 issue192 содержит G0–G5, no repeated CREATE | PASS [R] |
| 06 | PR74 открыт, historical model не новый BUILD-01 | PASS [R] |
| 07 | №2 2026-10-24T05Z: G0 BLOCKED, IFC dual QA | PASS [R] |
| 08 | Последний обнаруженный №3 на ветке audit-2026-10-20-18-A | PASS/STALE [R] |
| 09 | Add-on AC29 build3000, Win/Rhino7/8, 01.10.2025 | PASS [GS] |
| 10 | В AC29 кнопка называется Sync Changes to GH | PASS [G29] |
| 11 | Включённая кнопка continuous AC→GH update | PASS [G29] |
| 12 | Выключенная кнопка прекращает auto AC→GH update | PASS [G29] |
| 13 | AC29 содержит Lock/Unlock GH Elements | PASS [G29] |
| 14 | Relock возвращает GH-controlled параметры | PASS [G29] |
| 15 | AC-only CW Panel Building Material может сохраняться | PASS [G29] |
| 16 | Select in GH указывает generating component | PASS [G29] |
| 17 | Create New Library Part пишет в Embedded Library | PASS [G29] |
| 18 | Изменение GH Geometry обновляет Library Part | PASS [G29] |
| 19 | Удаление GH Object Settings удаляет generated Library Part | PASS [G29] |
| 20 | Switch to Use existing удаляет generated part; instances missing | PASS [G29] |
| 21 | Property Settings выбирает Classification и доступные Properties | PASS [G29] |
| 22 | Property Settings может overwrite Archicad Properties | PASS [G29] |
| 23 | Rhino8 содержит GH1, native Object Attributes/UserText | PASS [MC] |
| 24 | GH Data Dam задерживает downstream данные, не atomic commit | PASS/BOUNDARY [DAM] |
| 25 | GDL Main ID отвечает за Library Part compatibility/migration | PASS [GDL] |
| 26 | GLOB_INTGUID — внутренний instance GUID, не задаётся пользователем | PASS [GDL] |

## 3. Два документарных контрааудита (не независимый аудит №3)

**A. «Автоматическое AC→GH обновление = полноценная трёхсторонняя синхронизация». ОПРОВЕРГНУТО.** AC29 Sync Changes to GH охватывает connected AC elements→GH. GH→AC зависит от Synchronize и ownership; Rhino attrs имеют другой ID; GH Property Settings конкурирует с SceneWriter. Нет подтверждённого общего commit/rollback, GUID/host/material/type/story preservation, conflict resolution и loop suppression. Полный цикл Rhino→GH→AC→GH→Rhino **NOT_PROVEN**.

**B. «GH Library Part update сохраняет native BIM type/GUID, значит безопасен для кровли/проёмов». ОПРОВЕРГНУТО.** GC29 описывает каскадное удаление generated Library Part при удалении/переключении Object Settings, с Missing Objects. GDL Main ID ≠ native instance GUID. Object/GDL ≠ native Roof/Window/Door, связи host/SEO не доказаны. **NOT_ACCEPTED**.

## 4. Поручения №2 и ограничения

**P0-1:** исправить интеграционную схему: AC29 **Sync Changes to GH ON** может автоматически обновлять GH, но это только направленный reference update; описать OFF/ON, конфликтные ветви, контроль завершения.
**P0-2:** parameter ownership matrix GH-controlled / AC-only / APA-owned / UNKNOWN для Lock/Unlock, GH Property Settings, CW Panel material. SceneWriter — единственный writer APA-owned.
**P0-3:** read-only provenance G0: AC GUID/native Tool/story/host/material → Select in GH → GH definition → Rhino Object ID/UserText → GDL Main ID/library presence. UNKNOWN или Missing Object → STOP.
**P1:** GH Data Dam/Boolean Synchronize как пауза потока, не transaction. Никаких новых writers/routers, установок, LIVE, изменений исходников или PLN.

## 5. Ссылки и публикационный контроль

Graphisoft AC29 GH guide: https://help.graphisoft.com/AC/29/INT/GC.pdf
Graphisoft build download: https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/
Graphisoft GDL: https://help.graphisoft.com/AC/29/INT/GDL.pdf
GDL Center: https://gdl.graphisoft.com/reference-guide/general-object-parameters/
McNeel Rhino8: https://www.rhino3d.com/en/docs/guides/grasshopper/object-attributes/
Rhino8 features: https://www.rhino3d.com/en/features/
GH Data Dam: https://grasshopperdocs.com/completeIndex.html
McNeel forum: https://discourse.mcneel.com/t/geometry-record-and-automatic-slider/101637
BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
PR74: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
Priority: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md

Только research branch: create_file с branch → fetch_file по branch и commit → точное сравнение → commit SHA. При ошибке WRITE_BLOCKED. Не менять main/код/PLN/APX/PROJECT_PLAN.
