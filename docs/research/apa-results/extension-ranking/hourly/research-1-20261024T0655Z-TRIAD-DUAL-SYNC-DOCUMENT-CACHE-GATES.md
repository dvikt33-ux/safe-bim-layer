# APA №1 | 2026-10-24 06:55Z | Два разных Synchronise, привязка GH-документа, Rhino cache write-gates

## 0. Реальное влияние на трёхстороннюю BUILD-01 #192 и статусы

**P0-дельта 1 — нельзя объединять два одноимённых переключателя.** В Rhino 8 **Query Model Objects → Synchronise=False** (McNeel, исправление Rhino 8.1, 16.11.2023) выдаёт *замороженную копию* объектов до собственного expire/Query. В официальном Graphisoft **GH Design/Document → Synchronize=False** (AC29 GC.pdf, стр.17; подтверждено отчётом №2 06Z) возвращает **Null**, не typed snapshot. Это принципиально разные контракты в одном Grasshopper: Rhino frozen input можно использовать для read-only сравнения, а выход GH→Archicad генератора при False — нельзя использовать как сохранённую модель.

**P0-дельта 2 — соединение имеет явную идентичность не только PLN, но и GH definition/порта.** AC29 GC.pdf, стр.7: Graphisoft Connection Palette имеет **Port Number** и **Connect Document to Archicad**, выбирающий конкретный открытый GH документ. Эти настройки **не** тождественны константе Tapir/APA PORT=19723. До G0 нельзя считать, что изменение выполнено в нужной GH definition и направлено в нужный Archicad.

**P0-дельта 3 — Rhino-side Content Cache имеет собственный write-gate.** McNeel описывает ручной **Push Content** и опциональный Boolean **P** для непрерывной записи в Rhino. Это реальный готовый механизм GH→Rhino, но **не** Rhino→AC native BIM и не atomic commit; включённый P рядом с Rhino Query может дать обратную петлю. Отдельный writer не создаём.

**SOURCE: 30 отдельных документарных/репозиторных утверждений ниже; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых.** G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. **Full AC↔GH↔Rhino native BIM sync, GUID-preserving 3-way commit/rollback = NOT_PROVEN.** Это не 30 запусков Archicad/Rhino. MODEL_MODE_NOT_VERIFIABLE.

Сборка: Windows 11, Archicad 29 build 5101, локальный Tapir 1.5.10, Rhino 8/Grasshopper, официальный Graphisoft Live Connection AC29 **build 3000** (Windows, Rhino 7/8, 01.10.2025; статус установки неизвестен). Дополнительной подписки на сам add-on в официальном каталоге не указано; коммерческие Archicad/Rhino требуют лицензий. Rhino 8 Grasshopper и Content Cache штатные; отдельного платного плагина для перечисленных компонентов не требуется. Не устанавливать ПО и не выполнять LIVE.

## 1. Шесть SOURCE-карточек: операция → источник/версия/лицензия → контракт/направление → предел → поручение №2

### F0655-01 — Привязка порта и активного GH-документа в Graphisoft Live Connection
- **Операция BUILD-01:** выбрать именно GH definition для текущего учебного здания и целевой экземпляр Archicad до редактирования стены/кровли.
- **Первоисточник:** официальный Graphisoft AC29 Grasshopper-Archicad Live Connection User Guide, *Getting Started*, стр.7, https://help.graphisoft.com/AC/29/INT/GC.pdf ; официальный каталог версий https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/ (AC29 build 3000, Windows, Rhino 7/8, 01.10.2025).
- **Версия/лицензия:** AC29 add-on build3000, коммерческие AC29/Rhino8, GH встроен в Rhino; установленность add-on и порт не проверены.
- **Контракт/направление:** Connection Palette → **Port Number** выбирает порт общения GH↔AC; **Connect Document to Archicad** выбирает один GH-документ из открытых. Это *выбор адресата*, а не семантический маршрутизатор операций.
- **Ограничение:** GH port нельзя молча приравнять к APA Tapir JSON PORT=19723; одного статуса Connected недостаточно для PLN/GH identity, GUID, материалов и этажей. Не доказана параллельная запись из нескольких GH definitions.
- **№2 I0655-01:** SOURCE-only G0-манифест: Archicad projectPath/build/port + Graphisoft GH port/connected GH path + Rhino active 3dm path + GH document hash + APA Tapir port; UNKNOWN/несовпадение → STOP. Ничего не подключать.

### F0655-02 — Rhino Query Synchronise=False: read-only frozen reference
- **Операция:** после редактирования Rhino-объекта кровли получить контролируемую *замороженную* исходную выборку для сравнения с текущей геометрией/атрибутами.
- **Первоисточник:** ответ разработчика McNeel Kike Garcia 16.11.2023 о исправлении в **Rhino 8.1**: https://discourse.mcneel.com/t/model-object-component-update-problem/168818/5 ; подтверждение Query XXX non-synchronised option 07.08.2024: https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/10 .
- **Версия/лицензия:** Rhino 8.1 и позднее — документированное поведение на момент ответа; Rhino8 коммерческий, GH штатный. Фактический SR на ноутбуке NOT_VERIFIED.
- **Контракт/направление:** Rhino document → GH **Query**; Synchronise ON реагирует на изменения объектов и связанных данных, OFF выдаёт frozen copy до собственного expire/Query. **Read**, не Rhino/AC write.
- **Ограничение:** snapshot живёт в состоянии GH, не durable файл и не транзакция; downstream может получить новую выборку после manual Query/expire; нет crosswalk AC GUID.
- **№2 I0655-02:** описать SOURCE read-only пару live Query / frozen Query, явно указать, что это **не** Graphisoft Design Synchronize=False и не архив .3dm/.gh.

### F0655-03 — Rhino Content Cache: ручной Push vs непрерывный P
- **Операция:** закончить GH-вычисление фасадной/кровельной Rhino-геометрии и только затем обновить Rhino-owned объект.
- **Первоисточник:** McNeel Rhino8 feature https://www.rhino3d.com/features/grasshopper/content-cache/ ; практический контракт инженера McNeel Michael Vollrath 07.08.2024 https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/4 .
- **Версия/лицензия:** штатный Content Cache Rhino8, без отдельной лицензии плагина; точный SR текущей установки неизвестен.
- **Контракт/направление:** GH → **Rhino .3dm**. Чёрная кнопка **Push Content** — ручная отправка; раскрытый вход **P** + Boolean Toggle — непрерывный Push. Официальная функция обновляет объекты в кэше без обязательного ручного удаления.
- **Ограничение:** **P=True** — автоматическая Rhino-side запись и возможная петля при обратном Query; нет AC native GUID, hostWall, roof tool или общего commit. Не включать в текущем SOURCE-only проходе.
- **№2 I0655-03:** нарисовать read-only карту всех write branches (GH→Rhino Content Cache P/Push; GH→AC Graphisoft Synchronize; APA→AC SceneWriter) и STOP при более одном активном writer на один owner. Не тестировать запись.

### F0655-04 — Model Object direct reference против Brep→Guid→ModelObject
- **Операция:** поменять в Rhino UserText/Layer/Material у геометрии и гарантированно заметить *кандидат* изменения BIM-метаданных в GH.
- **Первоисточник:** разработчик McNeel Kike Garcia, 09.10.2024: https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/19 .
- **Версия/лицензия:** Rhino8 GH Model Object, коммерческий Rhino8, без стороннего расширения; конкретный SR локально не установлен.
- **Контракт/направление:** Rhino object → GH. **Brep** ссылается на геометрию и не обязан пересчитываться при изменении UserText/атрибутов; **direct ModelObject reference** включает атрибуты и UserText и инициирует пересчёт при их изменении. Промежуточная цепь **Brep→Guid→ModelObject** не доказана эквивалентной прямой ссылке; GUID→Geometry в описании предполагает активный документ.
- **Ограничение:** ложные пересчёты от Layer, пропущенные события на промежуточных преобразованиях; локальное исправление в более поздних SR NOT_VERIFIED; Rhino Object ID ≠ AC GUID.
- **№2 I0655-04:** SOURCE-only provenance table: direct ModelObject vs Brep vs Brep-Guid-ModelObject, изменение geometry/UserText/Layer; для обязательного BIM-метадата route — reject Brep-only. Без C# events и нового watcher.

### F0655-05 — Query Model Objects: широкая инвалидация и риск обратной петли
- **Операция:** выбор 3D-объектов Rhino для GH расчёта параметров окон/кровли по слою и метаданным.
- **Первоисточник:** McNeel Discourse, обсуждение 07.08–09.10.2024, https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/7 и /16; разработчик подтвердил реакцию ModelObject на Layer в /19.
- **Версия/лицензия:** Rhino8 native Query Model Objects, без отдельного плагина.
- **Контракт/направление:** Rhino document changes → GH Query → downstream recompute; фильтр объектов **не** гарантирует изоляцию события обновления только выбранных GUID.
- **Ограничение:** участник форума описал инвалидацию на изменения любого объекта документа — это **сообщение о поведении**, а не измеренный universal benchmark; при Content Cache P=True возможны повторные пересчёты. Производительность и конкретный SR не проверены.
- **№2 I0655-05:** задокументировать риск global invalidation, использовать read-only gate и frozen Query, не включать таймеры/автопуш; критерий приёмки в будущем — отсутствие повторного writer-dispatch после одного изменения.

### F0655-06 — Data Dam + frozen/live Query: готовый локальный detector, не арбитр трёх программ
- **Операция:** сравнить Rhino-метаданные/геометрию до и после одной завершённой операции, прежде чем считать её кандидатом на перенос в AC.
- **Первоисточник:** рекомендация разработчика McNeel 07.08.2024 https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/13 ; frozen Query Rhino8.1 https://discourse.mcneel.com/t/model-object-component-update-problem/168818/5 .
- **Версия/лицензия:** Rhino8 GH штатные Query/Data Dam/сравнение, без нового writer/платного API.
- **Контракт/направление:** Rhino→GH read: live Query сравнивается с задержанным/замороженным baseline. Это локальный **change candidate**, а не подтверждённый commit/rollback.
- **Ограничение:** не сохраняет автоматически GUID Archicad, BIM Tool/Story/host/material; baseline может устареть, Data Dam не закрывает обходные GH ветви.
- **№2 I0655-06:** описать минимальную схему сравнения и границы baseline; при различиях — только отчёт и независимый native readback через существующий APA, без GH Property Settings и GH→AC writer.

## 2. Реестр 30 документарных/репозиторных SOURCE-сверок (не 30 LIVE)

Ключи: [R] GitHub research branch, [P74] immutable PR74 head, [GS] Graphisoft официальный AC29 guide/download, [MC] McNeel официальная документация/ответы разработчиков. Отчёты №2/№3 проверены как опубликованные исследовательские артефакты, **не** как локальный runtime.

| № | Предмет фактической сверки | Результат/основание |
|---|---|---|
| 01 | Имя research branch найдено | PASS [R] search_branches |
| 02 | TRIAD-PIVOT 2026-10-23T11Z прочитан | PASS [R] |
| 03 | NEXT_RESEARCH_PRIORITIES.md найден по правильному пути extension-ranking | PASS [R] |
| 04 | Matrix declared count=61 | PASS [R] JSON |
| 05 | Matrix actual items=61 | PASS [R] JSON |
| 06 | Matrix unique IDs=61 | PASS [R] JSON |
| 07 | Matrix formula mismatches=0 | PASS [R] JSON, пересчёт 61 элементов |
| 08 | BUILD-01 issue #192 открыт | PASS [R] |
| 09 | BUILD-01 G0..G5 требуют native readback/Save-Reopen, нет разрешения G3 | PASS [R] |
| 10 | PR #74 открыт, не merged | PASS [R] |
| 11 | PR74 pinned head 5a3a9201a715a5528c93bed4a5318e2acb32eea7 | PASS [P74] |
| 12 | PR74 authored allowlist CreateColumns/Doors/Windows/Walls/Roofs | PASS [P74] code |
| 13 | PR74 allowlist не содержит CreateBeams | PASS [P74] code |
| 14 | PR74 Roof требует Basic/pivotLine/material, margin .35m | PASS [P74] code |
| 15 | PR74 bind_authorized_saved_copy проверяет path, name, SHA256, authorization_ref | PASS [P74] code |
| 16 | PR74 CreateSlabs.level использует абсолютный Z | PASS [P74] code |
| 17 | №1 предыдущий 0601Z отчёт прочитан, новизна сверена | PASS [R] |
| 18 | №2 06Z report прочитан: GH Synchronize False→Null, MultiPlane NOT_FOUND | PASS [R] |
| 19 | №2 06Z audits прочитан: два SOURCE контрааудита | PASS [R] |
| 20 | №3 20.10 18Z A прочитан; аудит устарел | PASS/STALE [R] |
| 21 | №3 20.10 18Z B прочитан; аудит устарел | PASS/STALE [R] |
| 22 | Официальный AC29 add-on build3000 Win Rhino7/8, 01.10.2025 | PASS [GS] |
| 23 | AC29 GH palette предоставляет отдельный Port Number | PASS [GS] GC.pdf indexed excerpt стр.7 |
| 24 | AC29 GH palette выбирает конкретный открытый GH документ | PASS [GS] GC.pdf indexed excerpt стр.7 |
| 25 | Rhino 8.1 Query Synchronise OFF выдаёт frozen copy | PASS [MC] Kike Garcia 16.11.2023 |
| 26 | Rhino 8.1 Query при синхронизации реагирует на object/reference changes | PASS [MC] Kike Garcia 16.11.2023 |
| 27 | Rhino8 Content Cache имеет ручной Push Content | PASS [MC] Michael Vollrath 07.08.2024 |
| 28 | Rhino8 Content Cache P + Boolean — continuous Push | PASS [MC] Michael Vollrath 07.08.2024 |
| 29 | ModelObject direct attr/UserText vs Brep geometry-only | PASS [MC] Kike Garcia 09.10.2024 |
| 30 | Brep-Guid-ModelObject intermediate/active-document assumption не равно direct reference | PASS/BOUNDARY [MC] Kike Garcia 09.10.2024 |

**Источник GH Design Synchronize=False→Null — AC29 GC.pdf стр.17, ранее сверено №2; в текущем проходе большой PDF не скачан целиком, утверждение перепроверено по опубликованному №2, не выдаётся за новый независимый PDF readback.** Официальный AC29 GC.pdf доступен как индексированный поисковый фрагмент; локальная бинарная PDF-верификация не выполнялась. Исторические форумы McNeel датированы 2023–2024, не являются LIVE-верификацией текущего Rhino8 SR.

## 3. Два контрааудита №1 (не независимый аудит №3)

**A. «Оба Synchronise=False одинаково замораживают данные» — ОПРОВЕРГНУТО.** Rhino Query OFF возвращает frozen model content (McNeel, Rhino8.1). Graphisoft GH Design/Document OFF возвращает Null (AC29 GC стр.17, №2). Поэтому нельзя передавать output GH-generating компонента в authored PR74 как snapshot. Необходима явная upstream geometry/metadata baseline. Никакой из переключателей не создаёт межпрограммную атомарную транзакцию.

**B. «Rhino Content Cache P=True + AC Sync Changes to GH ON + GH Synchronize=True = надёжная трёхсторонняя синхронизация» — ОПРОВЕРГНУТО.** Это три независимых механизма обновления с разными владельцами/ID и возможными циклами; нет общего арбитра конфликта, двухфазного commit, сохранения native Roof/Window/Door GUID и hostWall. PR74 SceneWriter остаётся единственным разрешённым writer APA-owned. На SOURCE-уровне можно только описать изоляцию ветвей; не запускать.

## 4. Адресное поручение №2 и критерий «ГОТОВО»

1. **I0655-01**: один read-only G0 manifest с отдельными GH port/definition, Rhino .3dm, Archicad PLN/build/port, Tapir registration. ГОТОВО: для каждого поля указаны источник и UNKNOWN/STOP, без фиктивного INSTALLED.
2. **I0655-02/04/06**: один read-only Grasshopper flow: Rhino direct ModelObject/Query → frozen baseline (без GH generating output) → сравнение geometry+UserText+Layer+Rhino ID → candidate report. ГОТОВО: нет GH→AC/GH→Rhino write branches и не заявлена сохранность AC GUID.
3. **I0655-03/05**: таблица ownership и write-gates: Content Cache P/Push, Graphisoft GH Synchronize, AC Sync Changes to GH, SceneWriter; STOP при loop/unknown owner/unknown GH document. ГОТОВО: никакой новый writer/router/synchronizer.
4. **BUILD-01**: пока только SOURCE; multi-plane native roundtrip, arbitrary BREP→native, shared GUID crosswalk и atomic 3-way rollback остаются NOT_FOUND/NOT_PROVEN. №3 должен независимо проверить после будущего разрешённого LIVE, не подменять аудитом №1.

## 5. Пин первоисточников и ограничений

- Graphisoft AC29 guide (стр.7,17): https://help.graphisoft.com/AC/29/INT/GC.pdf
- Graphisoft AC29 Live Connection build3000: https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/
- McNeel Rhino8 Content Cache: https://www.rhino3d.com/features/grasshopper/content-cache/
- McNeel Query 8.1 frozen behaviour: https://discourse.mcneel.com/t/model-object-component-update-problem/168818/5
- McNeel Content Cache P/ModelObject/direct refs: https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/4 ; /13 ; /19
- BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- PR74: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
- Research directive: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
- Priority matrix: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json

Только исследовательская ветка; PROJECT_PLAN rev182 только чтение; main, код, PLN/APX, установки, LIVE, Work/Codex/Arena, платные API и merge не выполнялись. Публикационный критерий: explicit branch create_file → fetch_file(branch) + fetch_file(commit) → точное сравнение содержимого и blob SHA; при сбое WRITE_BLOCKED. MODEL_MODE_NOT_VERIFIABLE.
