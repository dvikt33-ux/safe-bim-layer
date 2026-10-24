# APA №1 / TRIAD — document-bound MCP, GH write gates и проверка границ двусторонности
**Дата:** 2026-10-24 00Z (03:00 МСК). **MODEL_MODE_NOT_VERIFIABLE.**
**Режим:** только документарное исследование (SOURCE), GitHub READ и публикация одного нового отчёта в исследовательскую ветку. Никаких LIVE, установок, правок main/кода/PLN/APX, Work/Codex/Arena, платных API и merge.

## 0. Реальное влияние на трёхсторонний BUILD-01 / issue #192
**Главный новый результат:** обнаружены **две независимые бесплатные MIT MCP-альтернативы** (ArchBench Rhino MCP и ArchBench Archicad MCP, обе 0.1.0-alpha.3), которые адресуют **идентификацию целевого Rhino-документа** и **явный выбор порта Archicad**, но не являются новым нативным writer и **не реализуют автоматическую Rhino↔GH↔Archicad синхронизацию**. Особенно полезна заявленная привязка Rhino-bridge к конкретному документу вместо автоматического выбора другого окна. **Оба проекта честно маркированы авторами как alpha без нативной приёмки**; не предлагать устанавливать до отдельного разрешения. Дополнительно выявлены документированные Graphisoft механизмы GH provenance, контроля записи Boolean Toggle, а также расхождения этажности и устаревших атрибутов, требующие проверки на AC29.

**Статусы данного прохода:** SOURCE=28 предметных документарных сверок (НЕ 28 независимых источников); OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых. BUILD-01 G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. **FULL_AUTOMATIC_THREE_WAY_NATIVE_GUID_PRESERVING_SYNC=NOT_FOUND/NOT_PROVEN.** Старый PR #74/21-элементный Save/Open не считается новым BUILD-01.

**Уже известное, не выдавать за новое:** McNeel Rhino MCP Platform 0.3.0, Tapir 1.7.2, Content Cache, Query Model Objects как таковой, Speckle, Hotlink update, GH Embedded Library deletion, условный AC→GH Sync Changes to GH, jSwan и QA связей №2 23Z. Никакого второго writer; единственный разрешённый для APA-owned BIM: DynamicCommands → BIM Graph → SceneWriter → SQLite. Rhino/GH — подготовка/чтение, пока не доказано иное.

**Прочитанная база:** BUILD-01 #192; TRIAD-PIVOT 11Z; NEXT_RESEARCH_PRIORITIES.md (полный файл в docs/research/apa-results/extension-ranking/); №1 22:58Z; №2 22Z и **№2 23Z**; №3 audit-2026-10-20-18-A (последний непосредственно доступный, более свежий №3 не доказан); PR74 `docs/APA_MODEL_FIRST_BUILDING.md` на immutable commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`; матрица `priority_matrix_20261018.json` реально count=61/items=61, blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`; закреплённый Tapir 1.5.10 schema blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7` (это SOURCE, не установленный APX). Исторический PROJECT_PLAN rev182 **не извлечён**, ничего не менялось; не подменять его текущей rev197.

## 1. Карточки новых находок: операция → первоисточник/версия/лицензия → контракт/направление → ограничение → №2

### C01 / P0 — Rhino MCP by ArchBench: привязка к конкретному Rhino-документу
- **Операция BUILD-01:** при нескольких Rhino окнах/документах безопасно прочитать контекст **точного** 3DM перед передачей геометрии в GH, не перепутав целевой проект.
- **Первоисточники:** авторские README https://github.com/3d-mcp/rhino-mcp/blob/main/README.md ; лицензия https://github.com/3d-mcp/rhino-mcp/blob/main/LICENSING.md ; проверка https://github.com/3d-mcp/rhino-mcp/blob/main/docs/VALIDATION.md ; безопасность https://github.com/3d-mcp/rhino-mcp/blob/main/SECURITY.md ; release https://github.com/3d-mcp/rhino-mcp/blob/main/RELEASE_NOTES.md .
- **Версия/лицензия:** v0.1.0-alpha.3, обзор автора от 13.09.2026, MIT для Node/adapter/transport; Rhino лицензируется отдельно. Цель Rhino 8 + Python 3, Node.js 22+. **Ничего не установлено**.
- **Контракт/направление:** после запуска `start_mcp.py` в Rhino ScriptEditor с выбором read-only bridge привязывается к **тому документу, в котором запущен**; `rhino_get_status` и `rhino_get_context` читают статус/выделение. MCP client → Rhino READ; никакой нативной записи в Archicad и GH sync. Включение произвольного `rhino_execute_code` требует одновременно выбора на стороне Rhino, `ARCHBENCH_MCP_ALLOW_SCRIPTS=1` и `confirm:true`; для APA ЗАПРЕЩЕНО.
- **Границы:** автор явно пишет **native application qualification pending**; 16 локальных тестов на fixtures/stubs, НЕ AC29+Rhino8 LIVE. Скрипты не sandboxed, отмена/timeout не доказывают отсутствие изменений, Undo не откатывает filesystem/network; нельзя делать auto-retry.
- **Поручение №2 / I00-01:** SOURCE-only сравнить target binding McNeel Rhino MCP Platform vs ArchBench; составить `RhinoDocumentPath/Name/ObjectGUID/units/bridgeSession` и fail-closed правило. Никакой установки или скриптов.

### C02 / P0 — Archicad MCP by ArchBench: явный порт и отказ от автопереключения
- **Операция:** G0 выбрать точный экземпляр AC29 на портах 19723–19727 и не выполнить команду на чужом PLN.
- **Первоисточники:** https://github.com/3d-mcp/archicad-mcp/blob/main/README.md ; https://github.com/3d-mcp/archicad-mcp/blob/main/LICENSING.md ; https://github.com/3d-mcp/archicad-mcp/blob/main/docs/VALIDATION.md ; https://github.com/3d-mcp/archicad-mcp/blob/main/SECURITY.md .
- **Версия/лицензия:** v0.1.0-alpha.3, 13.09.2026, MIT для публичного Node server; Archicad отдельно лицензируется; Node.js 22+, Archicad 26+ built-in JSON API, **дополнительный APX не требуется**.
- **Контракт/направление:** `ARCHICAD_MCP_PORT` явно выбирает порт 19723–19743, 127.0.0.1, нет сканирования/автовыбора другого проекта/редиректов/автоповторов. `archicad_get_status`/`archicad_get_selection` дают базовое READ. `archicad_call_command({command,parameters,confirm:true})` включается только при `ARCHBENCH_MCP_ALLOW_SCRIPTS=1` — для APA **НЕ включать**. Это MCP→AC read/опциональный native JSON command, НЕ AC↔Rhino native sync.
- **Границы:** автор подтвердил только **7 fixture/Node тестов**, native AC29 Win11 qualification pending. Даже верный порт **не доказывает правильный PLN**; обязателен GetProjectInfo/expected path. Нет транзакционного rollback, HTTP timeout не доказывает отсутствие side effects. Существующий Tapir/SceneWriter не заменять и не дублировать.
- **№2 / I00-02:** SOURCE-only таблица «порт → project identity → GetProjectInfo → allowed read → forbidden arbitrary write», сопоставить с текущим G0 и уже используемым MCP. Оценить, даёт ли новый alpha что-либо сверх существующего read-only контура; если нет — **НЕ_ВНЕДРЯТЬ**.

### C03 / P0 — Graphisoft: штатные provenance-поля GH и устаревание атрибутов
- **Операция:** определить владельца GH-generated элемента и обнаруживать изменение материалов/composites/layers в Archicad до повторной синхронизации.
- **Официальный первоисточник:** Graphisoft Community, Teamwork note 21.07.2017, edited 12.11.2021: https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680 ; AC29 Live Connection user guide: https://help.graphisoft.com/AC/29/INT/GC.pdf .
- **Версия/лицензия:** описанный механизм **исторический**, применимость именно к AC29 GH Connection build3000 **НЕ_ПОДТВЕРЖДЕНА**. GH–AC29 Windows build3000, совместим Rhino7/8, официальный Graphisoft download от 01.10.2025: https://www.graphisoft.com/fr-ch/downloads/add-ons/rhino-grasshopper/ . Add-on бесплатный при отдельно лицензированных AC29/Rhino8.
- **Контракт/направление:** в историческом Graphisoft Teamwork описаны `Grasshopper Source Definition` (имя .gh) и `Last update from Grasshopper` (время), а атрибуты GH связываются по ID; изменения имён/слоёв/composites/building materials требуют **остановки и перезапуска connection**, чтобы обновить информацию в GH. Направление AC→GH attribute refresh после reconnect, НЕ транзакционный синхронизатор. Эти метки — диагностический provenance, **не GUID**, не гарантия сохранения.
- **Границы:** статья о Teamwork 2017/2021, не сертификация AC29 build5101. При конфликте reservation возможны дубликаты или оставшиеся элементы; GH deletion/recreate теряет SEO. Уже известный общий риск Teamwork не объявляется новым.
- **№2 / I00-03:** SOURCE-only указать в G4 provenance поля как `OPTIONAL_IF_PRESENT`, а изменения атрибутов как `RECONNECT_REQUIRED_CANDIDATE`; перед любой LIVE проверкой сравнить реальные GUID, material ID, composite, story, library part и last update; никаких новых классификаций создавать.

### C04 / P0 — Graphisoft GH write gate и Home Story не равен PR74 floorIndex
- **Операция:** подготовить geometry/units/этажи в Rhino/GH, затем **однократно** открыть допустимый write gate; исключить промежуточные записи при движении слайдеров и неверный этаж.
- **Официальный первоисточник:** Graphisoft Community tips 15.09.2016, edited 29.11.2021: https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564 ; официальный AC29 Walls: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-6.htm ; официальный GH29 build3000: https://www.graphisoft.com/fr-ch/downloads/add-ons/rhino-grasshopper/ .
- **Контракт/направление:** Graphisoft рекомендует Boolean Toggle к входу `Synchronize`: OFF до готовности всех входов, OFF при изменении slider, ON лишь при окончательной геометрии. В исторической GH-схеме Home Story определяется положением reference line/anchor (Morph — нижней точкой); `Story Plane` даёт плоскости этажей AC. В PR74 authored DAG native floorIndex задаётся явно; **совпадение Z ≠ доказанное совпадение floorId/index**. Направление GH→AC native creation/update только для GH-owned элементов; APA-owned всегда SceneWriter.
- **Границы:** Boolean Toggle — **ручной/логический gate**, НЕ commit acknowledgement, не предотвращает другие writers и не гарантирует rollback. Исторические советы о Home Story нужно проверить на GH29 build3000. Неправильные mm↔m порождают дегенеративные стены; смещённые списки точек дают нулевую высоту последней колонны. Не использовать GH direct write на APA-owned GUID.
- **№2 / I00-04:** SOURCE-only описать `GH_Sync=FALSE → freeze geometry → check units/story/host → compile PR74 preflight → native SceneWriter after separate approval`; в G1 сравнить Story Plane/Z и явный floorIndex, фиксировать mismatch как BLOCKED.

### C05 / P1 — Rhino8 Query Model Objects может порождать повторный solve при обратной записи
- **Операция:** Rhino → GH read геометрии для BUILD-01 без самовозбуждающегося цикла при Rhino/GH изменениях.
- **Первоисточники:** McNeel developer forum, 26.01.2023: https://discourse.mcneel.com/t/rhino-8-feature-build-blocks-better-using-grasshopper/149081 ; компонент `Data Dam` в GH: https://grasshopperdocs.com/completeIndex.html ; Graphisoft Boolean Toggle: https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564 .
- **Контракт/направление:** Rhino `Query Model Objects`/Geometry Pipeline → GH READ; встроенный `Data Dam` задерживает downstream данные, ручной release может изолировать пересчёт; GH `Synchronize=FALSE` предотвращает прямой GH→AC update. На McNeel forum пользователь документировал многократный цикл `Query Model Objects` → Data Dam → Python command при изменениях Rhino. **Это не доказанный универсальный баг Rhino8** и не доказанная автоматическая блокировка.
- **Версия/лицензия:** штатные компоненты Rhino 8/GH в лицензии Rhino, дополнительных платных плагинов не требуется; конкретная Rhino 8 SR неизвестна.
- **Границы:** Data Dam и Boolean Toggle не дают cross-app exactly-once и не отслеживают APA SQLite receipts. GH solution completion ≠ сохранённый PLN.
- **№2 / I00-05:** SOURCE-only построить схему предотвращения feedback `Rhino read → GH compute (dam) → JSON handoff → PR74 → native readback`; запретить ветку `AC write → Rhino bake → GH auto-resolve → AC write` до отдельной приёмки.

### C06 / P2 — Новый slopifc 0.0.1-beta.5: условный IFC read в GH, пока исключить
- **Операция:** независимая IFC QA в Grasshopper (тип/свойства/количества/mesh), а НЕ native Archicad editing.
- **Источник:** опубликованная карточка пакета с версией и ограничениями https://rhinopackages.github.io/package/slopifc ; ссылка автора https://github.com/aectooling/slopifc в момент проверки **404**, поэтому точный авторский исходный код/лицензия не подтверждены.
- **Контракт:** IFC file → GH read, filter by type/material, inspect properties/quantities, mesh preview и optional planar NURBS conversion. Rhino >=8.21, .NET8, Windows; beta.5 15.10.2026. Направление только IFC→GH для инспекции, не GUID-preserving triad sync.
- **Лицензия:** в Yak listing **Not declared**; бесплатность/исходники/возможность стабильной эксплуатации **NOT_VERIFIED**. Нет причин заменять уже существующие IfcOpenShell/IfcTester.
- **№2 / I00-06:** **НЕ_УСТАНАВЛИВАТЬ**, лишь записать как CONDITIONAL_CANDIDATE, закрыть без действий при отсутствии лицензии, документации и преимуществ над IfcOpenShell.

### C07 / P2 — Archi Automate: действительно один cross-host MCP, но коммерческий и не подходит
- **Операция:** потенциальный единый MCP для Archicad 27–29, Rhino8, Grasshopper с именованными инструментами и policy gates.
- **Авторский первоисточник:** https://github.com/gotoarchi/archi-automate/blob/main/README.md ; заявленная версия 27.28 (состояние README на 24.10.2026), продукт **commercial**, только 14-day trial; исходников продукта в публичном репозитории **нет**.
- **Контракт/направление:** заявлен cross-host discovery + отдельные `archicad_*`, `rhino_*`, `grasshopper_*`; GH graph read/edit; Archicad native add-on. Это **маркетингово-документированный multi-host orchestration**, не опубликованная приемка сохранения GUID/SEO/host/material после AC↔GH↔Rhino циклов.
- **Лицензия/ограничение:** коммерческий продукт, несовместим с требованием только бесплатных решений; дополнительные установки/лицензия запрещены. Не смешивать с независимыми бесплатными MIT ArchBench MCP C01/C02.
- **№2 / I00-07:** пометить `EXCLUDED_PAID_NO_NATIVE_TRIAD_PROOF`, не предлагать как бесплатное решение.

## 2. Реестр 28 проверенных документарных утверждений (SOURCE, не LIVE)
Каждая строка сверена с указанным первоисточником/прочитанным репозиторием. Источники: B=BUILD-01 #192; P=PR74 immutable doc; R2=№2 23Z; M=матрица61; G=официальная Graphisoft страница build3000; GT=Graphisoft Teamwork 2017/2021; GP=Graphisoft tips 2016/2021; RM=ArchBench Rhino README; RV=Rhino VALIDATION; RS=Rhino SECURITY; RL=Rhino LICENSING; AM=ArchBench Archicad README; AV=Archicad VALIDATION; AS=Archicad SECURITY; AL=Archicad LICENSING; F=McNeel forum; S=slopifc package; C=Archi Automate README.
| № | Конкретное документарное утверждение | Источник |
|---:|---|---|
| 01 | BUILD-01 #192 требует нового двухэтажного native building и шести gate G0–G5 | B |
| 02 | Для APA-owned предусмотрен один DynamicCommands→BIM Graph→SceneWriter→SQLite | B |
| 03 | PR74 документирует 21-элементный исторический прототип, не новый BUILD-01 | P |
| 04 | PR74 native plan имеет явные story bindings/hosted Wall GUID | P |
| 05 | №2 23Z: .gh с Rhino references требует сохранения исходного .3dm | R2 |
| 06 | №2 23Z: GetModelDumpV1 отсутствует в pinned Tapir, provider должен проверяться | R2 |
| 07 | Матрица extension ranking действительно содержит 61 item | M |
| 08 | GH–AC29 build3000 официально совместим с Rhino7/8 Windows | G |
| 09 | Graphisoft Teamwork note исторически описывает Source Definition | GT |
| 10 | Та же note описывает Last update from Grasshopper | GT |
| 11 | Атрибуты GH связаны по ID, обновление после изменений требует restart connection | GT |
| 12 | Teamwork GH deletion/recreate может терять SEO | GT |
| 13 | Graphisoft рекомендует Synchronize=OFF при изменении slider | GP |
| 14 | Graphisoft рекомендует включать Synchronize только после подготовки входов | GP |
| 15 | Исторический GH Home Story определяется положением anchor/reference | GP |
| 16 | GH Story Plane позволяет получить этажные плоскости Archicad | GP |
| 17 | Graphisoft предупреждает о mm↔m degenerate walls и zero-height columns | GP |
| 18 | Rhino MCP ArchBench v0.1.0-alpha.3 нацелен на Rhino8/Python3/Node22+ | RM,RV |
| 19 | Rhino bridge привязан к документу запуска, по умолчанию status/context READ | RM |
| 20 | Rhino arbitrary code требует host opt-in+env flag+confirm:true | RM,RS |
| 21 | Rhino MCP MIT; 16 fixture tests не являются native qualification | RL,RV |
| 22 | Rhino MCP timeout/cancel не доказывает отсутствие native side effects | RS |
| 23 | Archicad MCP v0.1.0-alpha.3, built-in JSON API, без нового APX | AM,AV |
| 24 | Archicad MCP явный порт 19723–19743, без сканирования и авто retry | AM,AS |
| 25 | Archicad MCP базовый status/selection READ, arbitrary API gated | AM,AS |
| 26 | Archicad MCP MIT; 7 fixture tests не являются native qualification | AL,AV |
| 27 | McNeel forum документирует возможный повторный solve с Query Model Objects/Data Dam | F |
| 28 | slopifc beta требует Rhino8.21+, лицензия не объявлена; Archi Automate коммерческий | S,C |

## 3. Контрааудит A — направление и семантика
1. Два независимых MCP (C01/C02) дают **два READ endpoint**, а не общий event bus, source-of-truth, atomic commit, stable Archicad GUID или conflict resolution. Нельзя объявлять их трёхсторонним sync.
2. Graphisoft Boolean Toggle и Data Dam **управляют потоком**, но не фиксируют SQLite intent/receipt; GH solution и Rhino document save не равны Archicad Save/Close/Reopen. Даже AC→GH Sync Changes to GH (ранее проверено №2) переносит связанные параметры, а не полную native identity.
3. GH Source Definition/Last update — исторические диагностические поля, не immutable source hash и не доказательство AC29 build5101. Для APA-owned authoritative GUID/host/material/floor остаётся Archicad readback.
4. Изменение Home Story по Z у GH-owned и явный floorIndex PR74 потенциально дают разные этажи; без сравнения GUID/story index нельзя говорить об эквивалентной геометрии. IFC/mesh/GDL Objects не равны нативным Wall/Slab/Roof.
**Вердикт:** P0 full triad native sync NOT_FOUND, G0–G5 не повышать.

## 4. Контрааудит B — безопасность, бесплатность, реальная готовность
1. Оба ArchBench MCP — alpha с авторскими fixtures (16 и 7), **без AC29 build5101/Rhino8 live qualification**. Две бесплатные MIT альтернативы не оправдывают установку, пока уже существующий SceneWriter/Graphisoft bridge не принят.
2. `confirm:true` — только поле запроса, не доказательство human approval. Optional script/raw API может модифицировать файлы; не включать. Timeout/cancel не rollback, повтор CREATE запрещён.
3. Archi Automate — коммерческий продукт, несмотря на публичный README и trial; **исключён**. slopifc beta — неизвестная лицензия и недоступный source URL, **исключён из G0**.
4. Ни один новый источник не подтверждает GUID-preserving AC↔Rhino↔GH, auto tool selection, обработку конфликтов, циклов, потерь библиотек, native multi-plane roof и безопасное rollback всех трёх программ.
5. PROJECT_PLAN rev182 не извлечён; свежий №3 позже 20.10 не подтверждён; отсутствует G0 runtime/installed APX; никаких новых OFFLINE/LIVE/ACCEPTED.
**Вердикт:** SOURCE_ONLY, запрет на INSTALL/LIVE/WRITE вне этого отчёта соблюдён.

## 5. Сводное поручение исследователю №2 (без исполнения)
**I00-01/I00-02:** подготовить сравнительную read-only таблицу `Rhino doc binding / Archicad explicit port / PLN identity / native GUID / expected SHA / units / floorIndex` для существующих McNeel/Tapir/Cline и двух ArchBench alpha; предпочтение уже подключённым готовым инструментам, не установкам.
**I00-03/I00-04:** GH29 provenance и write gate: какие свойства действительно присутствуют на AC29, как обновляются атрибуты, какие этажи назначаются при изменении anchor Z; только SOURCE-процедура, никаких элементов не создавать.
**I00-05:** зафиксировать anti-feedback границу `Rhino READ → GH compute → frozen JSON → PR74 preflight → single SceneWriter`, без новых обработчиков, без автоматического обратного bake и без direct GH write для APA-owned.
**I00-06/I00-07:** slopifc и коммерческий Archi Automate пометить EXCLUDED до подтверждения бесплатности/нужности и отдельного разрешения.
**ГОТОВО для №2:** одно документированное сравнение контрактов, target-binding и UNKNOWN полей; не выдавать подготовку за G0 PASS.

## 6. Ссылки на внутреннюю базу и доказательность
- BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- PR74: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
- PR74 immutable doc: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/docs/APA_MODEL_FIRST_BUILDING.md
- TRIAD-PIVOT: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
- NEXT: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
- №2 23Z: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T23Z-triad-report.md
- Матрица61: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
- №3: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md
- Указанные в карточках официальные страницы производителей/авторов — первоисточники. 28 проверок — документарные утверждения, НЕ 28 самостоятельных сайтов и НЕ runtime tests.
- **Контроль GitHub-публикации:** только branch `research/apa-extension-ranking-hub-20261018`, create_file с branch, fetch_file по branch и immutable commit, exact equality, commit SHA. Результат публикуется отдельно после фактического чтения; при ошибке WRITE_BLOCKED.
