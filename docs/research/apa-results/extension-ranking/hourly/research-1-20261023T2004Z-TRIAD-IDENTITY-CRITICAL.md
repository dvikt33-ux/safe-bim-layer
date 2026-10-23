# APA №1 — 23.10.2026 20:04 UTC — контроль идентичности, библиотек и нативных атрибутов

## Влияние на BUILD-01 (issue #192) — P0

**НОВОЕ, SOURCE_ONLY:** (1) у Tapir Grasshopper есть режим `ReplaceExisting`, который заменяет ранее созданные элементы через **Create + Delete**, а не Modify с сохранением Archicad GUID; при замене стены могут удаляться размещённые в ней окна/двери; (2) upstream описал повреждение GDL-параметров массивов на старой ветке Tapir и исправление только в 1.7.2; (3) старый `CreateWalls` мог перезаписывать структуру/привязку, полученную из Favorite; исправление вошло позднее; (4) в pinned каталоге Tapir 1.5.10 уже есть read-only `GetConnectedElements` для Wall→Window/Door и `GetIFCIdsOfElements` — для них **не нужен новый writer**. Это непосредственно влияет на сохранность hostWall, GUID, GDL-библиотек, материалов и этажей. Ни один из найденных механизмов не доказывает автоматическую трёхстороннюю синхронизацию.

**Границы:** `SOURCE=30` предметных проверок ниже, `OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0` **для нового BUILD-01**. Исторические 21-элементные LIVE PR74 не обнуляются, но не доказывают эту новую тройную связку. G0 `BLOCKED_RUNTIME` (не прочитаны локальные APX SHA, команда inventory, Rhino8/GH плагины, целевой scratch PLN); G1 `SOURCE_ONLY`; G2 `SOURCE_ONLY`; G3 `NOT_AUTHORIZED`; G4/G5 `NOT_RUN`. `FULL_THREE_WAY_SYNC=NOT_FOUND_IN_CHECKED_SOURCES`.

### Первоисточники и версия

- [TREL] Tapir upstream MIT, [1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.5.9), [1.7.0](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.0), [1.7.1](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.1), [1.7.2 от 19.10.2026](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2); лицензия [MIT](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE).
- [P615] [GH metadata/ReplaceExisting](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/615); [P493] [GetRelationsOfElements](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/493); [P864] [ConnectedElements Window/Door dropdown](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/864).
- [P767] [CreateWalls Favorite preservation](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/767); [P558] [GDL array write safety](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/558); [P866] [Detail outputs for GH](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/866).
- [P802] [IFC GlobalId stories](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/802); [P878] [libraryPartName + curved beams + SaveProject path](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/878); [P889] [native Grid GH components](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/889).
- [G29] [Graphisoft Grasshopper–Archicad AC29 руководство](https://help.graphisoft.com/AC/29/INT/GC.pdf), официальный продукт; совместимость/бесплатность дополнения — отдельно от платных лицензий AC29/Rhino8.
- [PIN] [immutable snapshot схемы Tapir 1.5.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json), blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`. **Схема не доказывает локальный бинарник.**
- [BUILD] [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74), [поручение TRIAD 11Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md), [№2 18Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T18Z-triad-report.md), [№3 20.10 07Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07.md), [NEXT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md). NEXT blob `6f074693360231c5cb42ada815984a6b0dd504c0`, №3 blob `40742adbf7ec945b31d125aac6912d95e5f07920`. PROJECT_PLAN rev182 исторический, только чтение; не изменялся.

## 30 отдельных SOURCE-проверок (НЕ 30 независимых источников)

| ID | Проверка, факт и ограничение | Источник |
|---|---|---|
| S01 | BUILD-01 требует новый двухэтажный native building и G0–G5, а не повтор PR74. | BUILD |
| S02 | PR74 уже содержит исторический 21-элементный двухэтажный native prototype с сохранением и GUID-правками, но не трёхстороннюю приёмку. | BUILD |
| S03 | №2 18Z: Wall zCoordinate относительно home story, Slab level абсолютный; единый global Z удваивает высоту стены второго этажа. | BUILD |
| S04 | №2 18Z: ModifySlabs polygonOutline без повторной передачи holes способен удалить отверстия. | BUILD |
| S05 | PIN содержит `GetConnectedElements` version 1.1.4: owner Wall→hosted Window/Door; запрос read-only. | PIN |
| S06 | PR864 1.7.2 меняет GH dropdown для Window/Door, **не добавляет** ранее отсутствующую команду Add-On. | P864 + PIN |
| S07 | PIN содержит `GetRelationsOfElements` version 1.5.7: wall/beam connections, zone boundaries, opening adjacent zones; не универсальный hostWall resolver. | P493 + PIN |
| S08 | `GetRelationsOfElements` для Door/Window даёт fromRoom/toRoom, а не обещанный универсальный GUID стены-хозяина. | P493 |
| S09 | PIN содержит `GetIFCIdsOfElements` version 1.5.1, доступный для cross-file IFC readback. IFC GlobalId не равен Archicad GUID. | PIN |
| S10 | PIN содержит `GetElementsByIFCIds`: обратный поиск по IFC идентификатору; нужна проверка отсутствующих/изменившихся IFC IDs. | PIN |
| S11 | В релизе Tapir 1.5.9 заявлено внедрение метаданных для GH-created элементов (#615). | TREL |
| S12 | PR615: `EmbedMetadata` default true, `ReplaceExisting` default false; фактическую версию GH plugin на ноутбуке не знаем. | P615 |
| S13 | PR615: свойства `Tapir GH/Source Definition`, `Last Updated`, `Component Guid` содержат путь GH-файла, локальное время, GUID **GH-компонента**. | P615 |
| S14 | GH Component Guid не равен Archicad Element GUID и не обеспечивает identity preservation. | P615 |
| S15 | `ReplaceExisting=false` повторный Solve может создать дубликаты; `true` сначала ищет старые, создаёт новые, затем удаляет старые. | P615 |
| S16 | Даже при успешной замене через Create→Delete Archicad GUID меняется; нет доказательства переноса SEO/hostWall/ссылок. | P615 + BUILD |
| S17 | Автор PR615 предупреждает: удаление прежней стены удаляет её hosted openings; Teamwork может не разрешить Delete. | P615 |
| S18 | PR615: поиск замен сканирует все элементы/свойства; метки unclassified elements могут не записаться, ошибки metadata — warnings. | P615 |
| S19 | PR615 изначально заявлял отсутствие DevKit/build/live; выпуск в 1.5.9 ≠ приёмка на AC29 build5101. | P615 + TREL |
| S20 | PR866 1.7.2: Wall/Beam/Column/Slab Details теперь отдают structure/material/profile/floor/offset входы Create/Modify. | P866 |
| S21 | PR866: `null` у неприменимых composite/profile/segment полей ломает прямое массовое подключение смешанных типов. | P866 |
| S22 | PR866: закрытые `Settings` типы официальной GH–AC Connection не совместимы напрямую с Tapir. | P866 + G29 |
| S23 | PR767: в старой ветке CreateWalls при Favorite мог принудительно задавать Basic/Center/no top-link/zero offset и перекрывать атрибуты. | P767 |
| S24 | Исправление PR767 в 1.7.0 делает поля опциональными, но explicit height сбрасывает top link; default tool state становится важен. | P767 + TREL |
| S25 | PR558: старый SetGDLParametersOfElements для целого массива мог вернуть success при повреждении читаемости параметров GDL; описан также hang. | P558 |
| S26 | PR558 в 1.7.2 переводит array items на API ChangeAParameter и отказывает при несовпадении размеров; зависание скрипта полностью не исключено. | P558 + TREL |
| S27 | PR878 1.7.2: `CreateWindows/Doors.libraryPartName` позволяет выбирать библиотечную деталь по имени; upstream live указан на AC30 Windows/JPN, AC29 BUILD-01 не доказан. | P878 |
| S28 | PR802 1.7.1: `GetStories.ifcId` на AC28+ — IFC GlobalId этажа; в PIN такого поля не заявлено, оно не заменяет floorIndex/floorId. | P802 + PIN |
| S29 | PR889 1.7.2: GH native Grid components появились; upstream AC30 Windows live, AC29 Windows не подтверждён; PR74 Grid axis остаётся PARTIAL. | P889 + BUILD |
| S30 | G29: `Deconstruct` существующих элементов + ручная `Send Changes` и только SinglePlane Roof; это не симметричная автоматическая синхронизация любых edits Rhino↔GH↔AC. | G29 |

## Семь карточек: конкретная операция → контракт → ограничение → поручение №2

### C2004-01 P0 — Wall→hosted Door/Window inventory БЕЗ обновления Tapir
- **Операция:** получить GUID окон/дверей каждой стены до/после изменения; проверить hostWall, количество и типы.
- **Источник/версия/лицензия:** PIN `GetConnectedElements` v1.1.4, Tapir MIT; GH dropdown улучшен в 1.7.2 P864.
- **Направление:** AC29 read-only → JSON/GH; **не** синхронизация и **не** writer.
- **Контракт:** owner `elements` (Wall GUIDs), `connectedElementType=Window` или `Door`; ответ с дочерними GUID. В G0 фактическую регистрацию проверять read-only.
- **Ограничение:** не подменять `GetRelationsOfElements`, не предполагать связь без readback; отсутствие child после Delete/Create = FAIL.
- **№2:** G2 составить таблицу wallGUID→windowGUIDs/doorGUIDs до/после, сравнить с PR74 GUID bindings, без LIVE.

### C2004-02 P0 — IFC ID readback как дополнительный ключ, не замена GUID
- **Операция:** проверка устойчивости идентичности при IFC обмене и Save/Open.
- **Источник:** PIN `GetIFCIdsOfElements` v1.5.1 и `GetElementsByIFCIds`; Tapir MIT. PR802 1.7.1 расширяет IFC id на Story (не pinned).
- **Направление:** AC→read/lookup, не Rhino↔AC automatic update.
- **Ограничение:** IFC GlobalId, Archicad GUID, Rhino Object ID и GH Component Guid — четыре разных идентификатора; никакого автоматического reconciliation.
- **№2:** read-only ID matrix с четырьмя столбцами и источником каждой пары, при несовпадении `CONFLICT_STOP`.

### C2004-03 P0 REJECT_AS_SYNC — GH `ReplaceExisting` не является Modify
- **Операция:** обновить GH-created стены, не потеряв окна/двери.
- **Источник/версия:** P615, релиз Tapir GH 1.5.9, MIT; installed GH plugin unknown.
- **Направление:** GH→Tapir Create + Delete старых, не AC→GH→Rhino roundtrip.
- **Ограничение:** `ReplaceExisting=true` меняет Archicad GUID и может удалить hosted openings/SEO; `false` дублирует при повторном Solve. Метаданные — лишь trace, не транзакция.
- **№2:** **запретить** прямой GH `Create*`/`ReplaceExisting` на APA-owned элементах; GH использовать для вычислений/JSON staging, единственный writer SceneWriter.

### C2004-04 P0 HOLD_VERSION — Favorite не гарантирует composite/structure на старом CreateWalls
- **Операция:** создавать стены с проверенными Favorites и сохранять Composite/ReferenceLine/TopLink.
- **Источник:** P767, релиз 1.7.0, MIT; локальный 1.5.10 не квалифицирован.
- **Направление:** GH/APA→Tapir→AC; нет reverse-sync.
- **Ограничение:** старый код мог перезаписать атрибуты; позднее исправление не установлено; даже после исправления explicit height отключает top-link.
- **№2:** не полагаться на имя Favorite; в G2 сравнить исходный Favorite и readback `structureType,compositeId,referenceLineLocation,relativeTopStory,offset`, при несовпадении BLOCKED.

### C2004-05 P0 HOLD_VERSION — безопасные GDL массивы окон/дверей
- **Операция:** менять библиотечные параметры без повреждения окна/двери.
- **Источник:** P558, Tapir 1.7.2, MIT; локальный 1.5.10 не обновлялся.
- **Направление:** AC native GDL parameter WRITE; не трёхсторонний sync.
- **Ограничение:** старый whole-array write мог оставить нечитаемые параметры, новый reject size mismatch и не гарантирует отсутствие hang в самом GDL script.
- **№2:** запретить whole-array `SetGDLParametersOfElements` в G3 без квалифицированной версии; только read-only `GetGDLParametersOfElements`, копия PLN, при необходимости отдельное разрешение на upgrade.

### C2004-06 P1 HOLD_VERSION — GH Detail→Modify без копирования закрытых Settings
- **Операция:** читать существующие Wall/Beam/Column/Slab параметры и готовить изменение геометрии/материалов.
- **Источник:** P866, Tapir 1.7.2 MIT; Graphisoft G29 для собственного Deconstruct.
- **Направление:** AC→GH read, GH→Tapir Modify только после разрешения; нет общего GUID ownership.
- **Ограничение:** null в смешанных structure types; Graphisoft Settings нельзя напрямую вставить в Tapir; direct GH Modify конкурирует с SceneWriter.
- **№2:** SOURCE-only матрица `WallDetails/SlabDetails`→typed fields существующего PR74, с проверкой null и home story; GH native write выключен.

### C2004-07 P1 HOLD_VERSION — библиотечные детали по имени / нативные Grid axes
- **Операция:** Window/Door без Favorite (`libraryPartName`), либо native Grid как отдельный необязательный тип.
- **Источник:** P878/P889, релиз 1.7.2 MIT, upstream Windows AC30; local AC29 1.5.10 unknown.
- **Направление:** GH/JSON→AC native create; не reverse-sync.
- **Ограничение:** локализованные имена GDL, библиотечные зависимости, child GUID; Grid требует собственную квалификацию и не должен блокировать первый BUILD-01.
- **№2:** подготовить отдельный optional scenario после G0 и разрешения на версию, без автоматической установки или записи.

## Контрааудит A — первоисточник, версии, лицензия

1. Источники P615/P767/P558/P866/P878/P889 — **upstream PR**, релизный список фиксирует включение в 1.5.9/1.7.0/1.7.2, но тексты PR содержат первоначальные предупреждения об отсутствии сборки/Archicad seat; где upstream live упомянут, он не является Windows AC29 build5101 LIVE APA. Не выдавать исходный PR за локальный тест.
2. PIN — immutable schema, не APX. Фактические `GetAddOnVersion`, command inventory, checksum установленного .apx, GH plugin version, Rhino8 build и точный PLN отсутствуют. `INSTALLED=0` **по новым подтверждениям**, не утверждение что пользователь ничего не установил.
3. Tapir репозиторий MIT; Rhino 8 и Archicad 29 лицензируются отдельно. Бесплатность Tapir/GH дополнений не означает бесплатность Rhino/Archicad. Ни платные API, ни установки не применялись.
4. Отчёт №2 18Z и аудит №3 20.10 07Z реально прочитаны; более свежий №3 в известных путях не подтверждён. NEXT и pivot прочитаны, PROJECT_PLAN rev182 не редактировался. Матрица 61 упомянута аудитором с blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`, **сам файл напрямую не открыт из-за неустановленного пути**, поэтому нельзя объявлять его повторно проверенным.

## Контрааудит B — инженерная применимость и недублирование

1. **Проверка ownership:** для APA-owned элементов единственный writer `DynamicCommands→BIM Graph→SceneWriter→SQLite` из issue192/PR74. GH `ReplaceExisting`, Graphisoft GH native create и сторонний Archicad MCP create — альтернативные writers, а не дополнительные фазы одной атомарной транзакции.
2. **GUID vs metadata:** GH component GUID связывает создание с источником, но при Delete/Create не сохраняет Archicad GUID; IFC GlobalId — отдельная сущность; Rhino Object ID — ещё одна. Нет готового универсального cross-app GUID registry, который автоматически устраняет конфликты.
3. **Host/holes:** замена Wall способна уничтожить hosted windows/doors, ModifySlabs без holes — отверстия. Проверять GUID детей и count/geometry holes до/после, иначе FAIL даже при визуально совпавшей модели.
4. **Материалы/библиотеки:** Favorite мог быть перезаписан, GDL array мог повреждаться. Native type, material/composite, profile, story, library link, properties и GDL parameters нужно независимо читать; визуальное совпадение Mesh не является BIM acceptance.
5. **Синхронизация:** Graphisoft GH Live Connection поддерживает направленную генерацию и ручной Send Changes, Tapir GH позволяет команды и metadata; ни одно не доказывает автоматическое изменение из любой из трёх программ с защитой от циклов/конфликтов/сохранением GUID.
6. **Приёмка:** сначала G0 только READ, затем G1/G2 schema/DAG/plan hash, G3 только отдельная новая scratch PLN по явному допуску, G4 Save/Close/Reopen + независимые GUID/host/material/geometry readbacks, G5 второе здание. При UNKNOWN запрет повторного CREATE, read-only reconciliation.

## Адресные поручения №2 / №3

**№2:** P0-1 документировать G0 read-only command inventory и host Wall→Window/Door через уже существующий `GetConnectedElements`; P0-2 построить ID map (AC GUID, IFC GlobalId, Rhino Object ID, GH component GUID) без записи; P0-3 закрыть риски Favorite и GDL arrays версионной таблицей, без обновления; P0-4 запретить GH ReplaceExisting и конкурирующие writers для APA-owned элементов; P0-5 добавить в будущую G4 приёмку независимый контроль hosted children, Slab holes, Composite/Story/GDL и Save/Open. Отчёт с путями и критериями, без LIVE.

**№3:** независимо проверить, что новая metadata не ошибочно классифицирована как GUID-preserving synchronization; что исправления 1.7.2 не приписаны установленной 1.5.10; что PR74 historical LIVE не объявлен новым BUILD-01; и что G0–G5 остаются честными.

**Итог:** найденные механизмы помогают обнаруживать и предупреждать потери, но **не дают готовой автоматической трёхсторонней синхронизации**. Не создавать writer/router/sync; не изменять main, код, PLN/APX, установки, лицензии, NEXT или PROJECT_PLAN; не запускать LIVE/Work/Codex/Arena/merge. `MODEL_MODE_NOT_VERIFIABLE`.
