# APA №1 | 2026-10-24 10:56Z | BUILD-01: Speckle AC29/Rhino8/GH, Rhino Worksession, Linked Blocks и контроль 3DM

## 0. Реальное влияние на трёхстороннюю сборку BUILD-01 (#192)

**Результат P0:** официальный Speckle подтверждает готовые коннекторы для Archicad 29, Rhino 8 и Grasshopper, но при Rhino/GH→Archicad получает **GDL-объекты**, а при Archicad→Rhino/GH передаёт **meshes** с материалами/метаданными. Это готовый обмен для координации и независимой QA, **не** нативное обновление Wall/Slab/Roof/Window/Doors и не GUID-preserving roundtrip. Матрица 61 уже содержит SPECKLE29; новое здесь — проверенный точный контракт и аргументированное отклонение его как native writer BUILD-01, а не «обнаружение неизвестного плагина».

**Результат P0-2:** Rhino 8 имеет два готовых, разных механизма внешних ссылок: Worksession (неизменяемая в текущем файле reference geometry с явным Update) и Linked / Embedded-and-Linked Block (обновляемая геометрия повторяемых элементов, с разным поведением при потере источника). Они дают ограниченное AC/Rhino reference-side обновление при наличии подходящего внешнего файла, **не** AC native BIM-sync и не гарантируют автоматическое обновление по окончании каждой операции.

**Результат P0-3:** штатные Audit3dmFile и IncrementalSave пригодны для контроля целостности и версионирования Rhino-стороны. Важный отрицательный контракт: Save Geometry Only исключает слои, материалы, свойства, заметки и единицы; для BUILD-01 неприемлем как backup. IncrementalSave по умолчанию «small» исключает render/analysis meshes.

**Статусы этого прохода:** SOURCE=28 адресных документарных/репозиторных сверок ниже; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. Full native three-way roundtrip=NOT_PROVEN. Не выполнялись установка, LIVE, Work/Codex/Arena, платные API, код, main, PLN/APX, merge. MODEL_MODE_NOT_VERIFIABLE.

**Среда:** Windows 11; Archicad 29 build 5101; Tapir 1.5.10; Rhino 8 (точный SR неизвестен); Grasshopper; официальный Graphisoft Live Connection AC29 build 3000 для Rhino 7/8 (локально INSTALLED не доказано). PR #74 исторически дал ограниченный 21-element two-story prototype с Save/Open; новый BUILD-01 не собран. Никаких новых заявлений об испытаниях.

## 1. Шесть карточек — точный контракт, направление, ограничение и поручение №2

### F1056-01 — Speckle Archicad 29 + Rhino 8 + Grasshopper: готовый обмен, но не native writer

- **Операция BUILD-01:** передать сохранённую native модель AC29 в Rhino/GH для визуального и атрибутивного контроля по этажам; проверить возможность обратной передачи изменения Rhino/GH.
- **Первоисточники:** Speckle [Archicad integration](https://speckle.systems/integrations/archicad/), [Rhino integration](https://speckle.systems/integrations/rhino/), [Grasshopper integration](https://speckle.systems/integrations/grasshopper/). Это официальные страницы производителя, актуальные на дату чтения 24.10.2026, а не immutable release конкретного Archicad бинарника.
- **Версии/лицензия:** Speckle официально заявляет Archicad **27/28/29**, Rhino **7/8**, Grasshopper plugin. На [официальном тарифе](https://speckle.systems/pricing/) имеется бесплатный Explore; Rhino/Archicad требуют собственных лицензий. Для именно бинарника AC29 exact connector build и license manifest **NOT_VERIFIED**; не считать source-code лицензией каждого распространяемого бинарника.
- **Точный контракт/направление:** AC→Rhino: **meshes+materials**, hierarchy by story then element type, AC properties→Rhino UserText. AC→GH: meshes+materials и properties для анализа. Rhino→AC: **GDL objects+materials**. GH→AC: **GDL objects+materials**. Speckle publish/load и versioning ≠ событие native AC change/merge.
- **Ограничение:** GDL-объект не является нативной Roof/Wall/Slab/hosted Window/Doors; AC GUID, SEO, hostWall, floorId, exact BIM type не гарантированы. Receive в тот же BUILD-01 PLN был бы вторым writer и нарушил бы строгий whole-inventory SceneWriter. Публичные маркетинговые слова «sync» не доказывают обратную native-семантику.
- **№2 I1056-01:** SOURCE-only включить Speckle как **необязательный read-only/sidecar QA кандидат**, запретить Receive в BUILD-01 PLN; проверить exact AC29 connector binary/version/licence и вариант полностью локальной проверки без передачи проектных данных в облако. Не устанавливать и не отправлять файлы.

### F1056-02 — Speckle Free + active/legacy source boundary

- **Операция:** хранить независимые контрольные публикации модели для визуального diff, не подменяя SQLite ledger/PLN.
- **Источники:** [Speckle Pricing 2026](https://speckle.systems/pricing/), [active V3 connectors](https://github.com/specklesystems/speckle-sharp-connectors), [legacy archived](https://github.com/specklesystems/speckle-sharp), [separate Archicad source](https://github.com/specklesystems/speckle-archicad).
- **Версия/лицензия:** актуальный сайт: Free Explore — 1 проект, до 10 пользователей, 30 дней истории версий; активный V3 repo Apache-2.0 unless otherwise indicated, содержит Rhino 7–8; старый speckle-sharp архивирован 12.05.2026; исходники Archicad находятся отдельно. **Нельзя переносить версию релиза Rhino V3 на бинарник Archicad 29** без manifest.
- **Контракт/направление:** published snapshots→Speckle versions→viewer/QA; это внешняя копия, не источник истины для APA native element identity.
- **Ограничения:** внешняя облачная передача, условия тарифа, срок хранения, безопасность проекта; self-hosted и полный бесплатный workflow без отдельной проверки NOT_VERIFIED. Внешний version history не равен атомарному rollback PLN+3DM+GH.
- **№2 I1056-02:** сравнить Speckle sidecar с уже доступными Model Compare/IFC QA по необходимости и приватности. Не предлагать регистрацию/загрузку без отдельного допуска.

### F1056-03 — Rhino 8 Worksession: read-only external reference и ручное обновление

- **Операция:** в Rhino смотреть независимую эталонную геометрию из другого файла, не позволяя случайно менять её во время редактирования своей .3dm модели.
- **Официальный источник:** [McNeel Rhino 8 Worksession](https://docs.mcneel.com/rhino/8/help/en-us/commands/worksession.htm), [commands overview](https://docs.mcneel.com/rhino/8/help/en-us/seealso/sak_blocksgroups.htm).
- **Версия/лицензия:** штатный Rhino 8, отдельного плагина нет; требуется лицензия Rhino 8.
- **Контракт/направление:** Attach внешнего Rhino/importable файла→**reference-only** в активной .3dm; Update перечитывает attachment. Attached geometry нельзя Move/Scale в активном документе, но можно использовать как вход для Copy/Extrude. В Worksession только один .3dm активен для редактирования; другие доступны для просмотра. .rws хранит список ссылок отдельно.
- **Ограничение:** Attach/Update — не гарантированное автоматическое обновление по завершении AC-операции; не AC native element readback. При копировании reference объектов возникают новые объекты и новая идентичность. Имена материалов/текстур могут конфликтовать. Нельзя принимать .rws за единую модель.
- **№2 I1056-03:** оформить SOURCE-only вариант «эталонная AC→3DM геометрия как reference в Rhino» с явным Update и сверкой координат, этажей и материалов; не экспортировать PLN и не создавать .rws без разрешения. Если нет готового безопасного AC→3DM snapshot, отметить NOT_FOUND.

### F1056-04 — Rhino 8 Linked Blocks: безопасный fallback и риск пересоздания

- **Операция:** использовать повторяющиеся геометрические элементы (например, корпус/обрамление окон) как linked reference и обновлять их при изменении исходной .3dm.
- **Официальный источник:** [McNeel Rhino 8 Block](https://docs.mcneel.com/rhino/8/help/en-us/commands/block.htm), [Block Definitions to Update](https://docs.mcneel.com/rhino/8/help/en-us/information/blockdefinitionstoupdate.htm), [Rhino 8 GH Blocks](https://www.rhino3d.com/en/features/grasshopper/blocks/).
- **Версия/лицензия:** встроено в Rhino 8 / Grasshopper 1; отдельной подписки нет, лицензия Rhino требуется.
- **Контракт/направление:** external .3dm→linked block definition→instances; Embedded не обновляется при изменении внешнего файла; Embedded-and-Linked сохраняет геометрию локально и ссылку, при недоступном файле остаётся встроенная геометрия; Linked-only при недоступном источнике становится отсутствующим. На открытии обнаруженных изменённых linked blocks есть Update Now/Update Later.
- **Ограничение:** Rhino Block Definition/Instance ID ≠ Archicad GUID/LibraryPart Main ID; nested blocks и имена/материалы требуют проверки; Linked-only создаёт missing geometry; никакой native BIM Roof/Window.
- **№2 I1056-04:** только SOURCE-сравнение Embedded-and-Linked против Linked-only для sidecar references. Не использовать BlockReplace/CreateUniqueBlock как способ сохранить AC GUID. Сопоставить с уже изученным AC Hotlink, не смешивать два механизма.

### F1056-05 — Rhino 8 Audit3dmFile + IncrementalSave: контроль целостности/backup

- **Операция:** независимая диагностика сохранённой .3dm после будущей санкционированной операции и получение версии до/после без перезаписи активной модели.
- **Официальный источник:** [McNeel Audit3dmFile](https://docs.mcneel.com/rhino/8/help/en-us/commands/audit3dmfile.htm), [McNeel Save/IncrementalSave](https://docs.mcneel.com/rhino/8/help/en-us/commands/save.htm).
- **Версия/лицензия:** Rhino 8 штатно, без отдельного плагина; требуется лицензия Rhino.
- **Контракт/направление:** Audit3dmFile проверяет **не открытый** .3dm на ошибки базы/содержимое; IncrementalSave создаёт последовательно пронумерованную отдельную .3dm и не меняет текущую активную модель. Default IncrementalSave saves small (без render/analysis meshes). Save Geometry Only **не сохраняет** layers/materials/properties/notes/units.
- **Ограничение:** целостность .3dm не доказывает соответствие AC BIM GUID, hosted openings и SEO; IncrementalSave и Audit3dmFile — файловые операции, выполнять только после разрешения, сейчас SOURCE_ONLY. Автосохранение Rhino не атомарно с PLN и .gh.
- **№2 I1056-05:** добавить в будущий G4 **проект проверки** 3DM backup hash, Audit3dmFile и сравнение атрибутов/единиц; явно запретить Geometry Only как backup для BIM метаданных; не запускать сейчас.

### F1056-06 — Graphisoft Live Connection Boolean Toggle: write side-effects уже при готовых входах

- **Операция:** не допустить непреднамеренного GH Design→AC native CREATE во время настройки параметров и маршрутизации.
- **Официальный источник:** [Graphisoft Community, Grasshopper-ARCHICAD Live connection: Boolean Toggle for Synchronization](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564), [Graphisoft AC29 GC.pdf, last updated 22.01.2026](https://help.graphisoft.com/AC/29/INT/GC.pdf).
- **Версия/лицензия:** рекомендация Graphisoft историческая (не доказательство поведения каждой AC29 build5101); Live Connection AC29 build3000 бесплатный add-on к лицензированным Archicad/Rhino.
- **Контракт/направление:** GH Design/Document components могут начать синхронизацию, когда входов достаточно; Graphisoft рекомендует выключить активные AC nodes при подключении, включать только после готовности входов и выключать при регулировке sliders. GH→AC native writer. AC→GH Deconstruct reference — отдельное направление.
- **Ограничение:** Boolean Toggle/Sync=False не атомарная транзакция, не блокировка всего PLN, не гарантия сохранения прежних GUID и не решение inventory drift. Для BUILD-01 нельзя использовать как разрешение GH-native writes.
- **№2 I1056-06:** до любого G0/G1 составить SOURCE-only GH side-effect inventory (каждый Design/Document node, Sync state, Bake/Cache). BUILD-01 GH только read-only Deconstruct/Reference, пока строгий SceneWriter inventory не согласован.

## 2. Журнал 28 отдельных проверок (каждая — проверяемый тезис, а не 28 LIVE-тестов)

| ID | Проверенный предмет | Источник | Вывод |
|---|---|---|---|
| C01 | Имя research-ветки существует | GitHub branch search, 24.10.2026 | PASS SOURCE |
| C02 | TRIAD-PIVOT не допускает новый writer | [directive](research-1-20261023T11Z-TRIAD-PIVOT.md) | PASS SOURCE |
| C03 | NEXT_RESEARCH_PRIORITIES задаёт G0–G5 | [priorities](../NEXT_RESEARCH_PRIORITIES.md) | PASS SOURCE |
| C04 | BUILD-01 требует native two-story + Save/Open | [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) | PASS SOURCE |
| C05 | PR74 — исторический 21-element native прототип | [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) | PASS SOURCE |
| C06 | №2 10Z whole-inventory drift при GH-native writes | [№2 report](research-2-integration-2026-10-24T10Z-report.md) | PASS SOURCE |
| C07 | №2 10Z два контрааудита reject 3-way | [№2 audits](research-2-integration-2026-10-24T10Z-audits.md) | PASS SOURCE |
| C08 | №3 последнее найденное 20.10 18Z G0 BLOCKED | [№3](audit-2026-10-20-18-A.md) | PASS SOURCE |
| C09 | Матрица содержит 61 item и SPECKLE29 | [matrix](../priority_matrix_20261018.json) | PASS SOURCE |
| C10 | Speckle официально поддерживает Archicad 29 | [Speckle AC](https://speckle.systems/integrations/archicad/) | PASS SOURCE |
| C11 | Speckle AC→Rhino = meshes + materials | [Speckle AC](https://speckle.systems/integrations/archicad/) | PASS SOURCE |
| C12 | AC→Rhino организуется по story и element type | [Speckle AC](https://speckle.systems/integrations/archicad/) | PASS SOURCE |
| C13 | AC properties→Rhino UserText | [Speckle AC](https://speckle.systems/integrations/archicad/) | PASS SOURCE |
| C14 | AC→GH = meshes + materials + properties | [Speckle AC](https://speckle.systems/integrations/archicad/) | PASS SOURCE |
| C15 | Speckle Rhino 7/8 поддерживаются | [Speckle Rhino](https://speckle.systems/integrations/rhino/) | PASS SOURCE |
| C16 | Rhino→AC = GDL objects + materials | [Speckle Rhino](https://speckle.systems/integrations/rhino/) | PASS SOURCE |
| C17 | GH→AC = GDL objects + materials | [Speckle GH](https://speckle.systems/integrations/grasshopper/) | PASS SOURCE |
| C18 | Free Explore 1 project/10 users/30-day history | [Speckle pricing](https://speckle.systems/pricing/) | PASS SOURCE |
| C19 | Active V3 Rhino connector, Apache-2.0 repo | [Speckle V3](https://github.com/specklesystems/speckle-sharp-connectors) | PASS SOURCE |
| C20 | Legacy speckle-sharp archived 12.05.2026 | [Speckle legacy](https://github.com/specklesystems/speckle-sharp) | PASS SOURCE |
| C21 | Rhino Worksession reference attachments нельзя редактировать | [Rhino 8 Worksession](https://docs.mcneel.com/rhino/8/help/en-us/commands/worksession.htm) | PASS SOURCE |
| C22 | Worksession Update перечитывает attachments | [Rhino 8 Worksession](https://docs.mcneel.com/rhino/8/help/en-us/commands/worksession.htm) | PASS SOURCE |
| C23 | Worksession materials могут конфликтовать по имени | [Rhino 8 Worksession](https://docs.mcneel.com/rhino/8/help/en-us/commands/worksession.htm) | PASS SOURCE |
| C24 | Linked vs Embedded-and-Linked missing-source behavior различается | [Rhino 8 Block](https://docs.mcneel.com/rhino/8/help/en-us/commands/block.htm) | PASS SOURCE |
| C25 | Block Definitions Update Now/Later при изменении внешнего файла | [Rhino 8 Block Update](https://docs.mcneel.com/rhino/8/help/en-us/information/blockdefinitionstoupdate.htm) | PASS SOURCE |
| C26 | Audit3dmFile проверяет не открытый 3DM | [Rhino 8 Audit](https://docs.mcneel.com/rhino/8/help/en-us/commands/audit3dmfile.htm) | PASS SOURCE |
| C27 | IncrementalSave default small, отдельная версия | [Rhino 8 Save](https://docs.mcneel.com/rhino/8/help/en-us/commands/save.htm) | PASS SOURCE |
| C28 | Save Geometry Only удаляет BIM-подобные атрибуты/units | [Rhino 8 Save](https://docs.mcneel.com/rhino/8/help/en-us/commands/save.htm) | PASS SOURCE |

**Метод:** 28 разных проверяемых утверждений по конкретным страницам и файлам; один документ может поддерживать несколько разных контрактов. Это не 28 отдельных программных тестов, не 28 независимых источников и не 28 найденных новых расширений. В этом проходе реально новых для предыдущего hourly №1 SOURCE-карточек шесть; Speckle как продукт был в матрице раньше.

## 3. Контрааудит A — «Speckle автоматически сохраняет native BIM при круговом обмене»

Гипотеза: наличие готовых Archicad29/Rhino8/GH коннекторов и слов «stay in sync» означает AC Roof/Wall/Window GUID-safe roundtrip.

**Опровержение по контракту производителя:** AC→Rhino/GH передаёт meshes; Rhino/GH→AC загружает GDL objects, а не native Wall/Roof/hosted Window. Материалы не равны Building Material GUID. Не доказаны hostWall, SEO, floor bindings, ownership и удаление. Receive добавляет второй writer к SceneWriter, конфликтуя с проверкой полного GUID inventory в №2 10Z. **Результат: REJECT_NATIVE_WRITER, SPECKLE_QA_SIDECAR_CANDIDATE_SOURCE_ONLY.**

## 4. Контрааудит B — «Rhino reference + incremental backup дают автоматическую трёхстороннюю транзакцию»

Гипотеза: Worksession Update/Linked Block Update + IncrementalSave + Audit3dmFile гарантируют, что изменение в любом приложении появится в остальных с тем же ID и при сбое откатится.

**Опровержение:** Worksession attachments read-only, Update явный; linked blocks обновляют Rhino definitions, не AC native types. Embedded/Linked могут потерять внешний файл, имена материалов конфликтуют. IncrementalSave только 3DM, а не PLN/.gh/SQLite; Audit3dmFile проверяет базу, не соответствие BIM. Save Geometry Only удаляет нужные атрибуты. **Результат: REJECT_ATOMIC_ROUNDTRIP; RHINO_REFERENCE_AND_FILE_QA_CANDIDATE_SOURCE_ONLY.**

## 5. Адресный план №2 и граница инженерной готовности

1. **G0 (read-only, после допуска к Windows):** actual AC build/PLN/port/APX SHA/Tapir commands/stories; Rhino exact SR/active .3dm/units; .gh hash; GH add-on build; side-effect inventory. Ни одна из этих локальных проверок не проводилась.
2. **G1/G2:** только существующий PR74 typed DAG→SceneWriter, no GH Design native writer. Использовать Speckle, Worksession, Linked Blocks только как опциональные внешние **read-only references**; не включать в обязательный G1.
3. **G3/G4:** исключительно после отдельного разрешения; one writer SceneWriter; native GUID/BREP/type/story/host/material readback + guarded Save/Close/Reopen; отдельно проверять .3dm integrity, но не приравнивать к AC acceptance.
4. **G5:** второе отличное исходное здание; 3-way bidirectional остаётся NOT_PROVEN, пока не появится готовый безопасный identity-aware маршрут. Не менять инвариант inventory ради «красивого» демо.

**Запреты соблюдены:** никаких новых writer/router/sync, изменений main/кода/PLN/APX, установки, LIVE, Work/Codex/Arena, платных API, merge. PROJECT_PLAN rev182 только read-only в ранее сохранённом управленческом контексте; прямой повторный fetch этого исторического документа в текущем проходе не выполнялся, поэтому «перепроверен rev182» не заявляется.

MODEL_MODE_NOT_VERIFIABLE.
