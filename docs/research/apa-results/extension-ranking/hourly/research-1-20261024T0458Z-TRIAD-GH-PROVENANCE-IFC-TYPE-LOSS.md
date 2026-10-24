# APA №1 | 2026-10-24 04:58Z | GH provenance, Teamwork conflicts, IFC native-type collision
**P0 BUILD-01 #192: Archicad 29 build5101 (Win11, local Tapir 1.5.10) + Rhino8 + Grasshopper.**
**SOURCE_ONLY; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых.**
G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.

## 0. Реальное влияние на трёхстороннюю сборку BUILD-01
**Новая P0-дельта 1:** Graphisoft исторически документировал встроенную классификацию **Grasshopper Connection** и два поля **Grasshopper Source Definition** / **Last Updated by Grasshopper** для идентификации GH-generated элементов. Это готовый read-only кандидат для provenance/ownership, а не native GUID или полноценный cross-app commit. Доказательство: Graphisoft Teamwork article (21.07.2017, edited 12.11.2021), руководство AC27; наличие именно в локальном AC29 build5101 пока **NOT_VERIFIED**.

**Новая P0-дельта 2:** Graphisoft документировал Teamwork-конфликты: при чужом reservation GH regeneration может создавать дубликаты, при отсутствии нужного reservation изменения и удаления могут не происходить; GH delete/recreate меняет GUID и рвёт SEO. **Это правила Teamwork**, не подтверждённые для обычного одиночного PLN. Результат: простой GH refresh нельзя принимать за identity-safe sync.

**Новая P0-дельта 3:** официальный **Archicad 29** IFC Type Mapping `by Element Type` экспортирует **Roof и Shell одинаково как IfcSlab с PredefinedType=ROOF**. IFC IfcSlab.ROOF не доказывает native Roof. Это прямой false-positive для проверки сложной кровли BUILD-01: только native AC Tool + GUID + topology + host/SEO readback после Save/Reopen.

**Архитектурное решение:** единственный APA-owned writer остаётся существующий PR74 → BIM Graph → SceneWriter/SQLite → Tapir 1.5.10. Rhino/GH — подготовка геометрии и чтение; GH-owned native writes нельзя смешивать с APA-owned GUID без отдельного разрешения и ownership gate. Полная автоматическая AC↔GH↔Rhino синхронизация, единый commit/rollback, предотвращение циклов/конфликтов = **NOT_PROVEN**.

## 1. Шесть карточек новых готовых возможностей / ограничений

### F0458-01 — встроенная GH provenance классификация
- **Операция:** перед редактированием стены, кровли или фасада различить GH-owned и APA-owned элементы.
- **Официальный источник/версия:** Graphisoft Community (2017, update 2021) https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680 ; AC27 user guide https://help.graphisoft.com/AC/27/INT/GC.pdf ; актуальный AC29 guide https://help.graphisoft.com/AC/29/INT/GC.pdf (локальная проверка полей отсутствует).
- **Пакет/лицензия:** официальный GH–AC29 Live Connection **build3000**, Windows, Rhino7/8, last modified 01.10.2025: https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ ; отдельный API не нужен; Archicad и Rhino коммерческие; локальная установка пакета не проверена.
- **Контракт/направление:** GH-generated → AC native element, автоматически назначаются Grasshopper Connection classification, Grasshopper Source Definition (имя .gh) и Last Updated by Grasshopper (timestamp) **по историческим документам**. Не AC→Rhino native GUID sync.
- **Ограничение:** filename/timestamp не уникальный ключ и не immutable GUID; наличие и семантика в AC29 build5101 NOT_VERIFIED; нельзя дописывать APA-owned свойства через GH writer.
- **№2 I0458-01:** read-only native inventory `AC GUID / native Tool / GH classification / source filename / last updated / GH document / owner`; UNKNOWN или конфликт владельцев → STOP.

### F0458-02 — Teamwork reservation и сохранение SEO
- **Операция:** изменение GH-generated элемента в Teamwork без дубликатов и потери зависимых SEO.
- **Источник/версия:** Graphisoft Community 2017/2021 https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680 .
- **Лицензия:** встроенное поведение исторической GH Connection в Teamwork/BIMcloud; условия лицензирования Teamwork не проверены, не бесплатный межпрограммный lock.
- **Контракт/направление:** GH→AC Teamwork. Reserved by another user → возможен duplicate; free/not reserved by operator → modification/deletion могут не пройти; GH delete/recreate → новый GUID и потеря SEO. Изменённые attributes по ID могут требовать restart GH connection.
- **Ограничение:** не переносить выводы на single-user PLN и AC29 без испытания. Не разрешать LIVE.
- **№2 I0458-02:** условный gate только при обнаруженном Teamwork: reservation state, duplicate count, native GUID/SEO readback, no CREATE retry on UNKNOWN.

### F0458-03 — AC29 IFC Roof/Shell type collision
- **Операция:** доказать, что сложная кровля осталась native Roof, а не Shell/Morph/GDL.
- **Источник/версия:** официальный Archicad29 Built-in IFC Type Mapping https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-51.htm (2026).
- **Лицензия:** встроено в коммерческий Archicad29.
- **Контракт:** при `by Element Type` Roof→IfcSlab.ROOF; Shell→IfcSlab.ROOF; Slab→IfcSlab.FLOOR; Skylight и Window→IfcWindow; Opening→IfcOpeningElement. `by Classification` может давать другое отображение.
- **Направление:** AC→IFC QA/export; это не IFC→native edit и не доказательство GUID.
- **№2 I0458-03:** матрица `native Tool + GUID → IFC type/predefinedType/GlobalId + translator preset`; native Roof обязательный acceptance gate.

### F0458-04 — AC29 IFC Door-Window / Composite / Material экспорт
- **Операция:** дополнительная проверка GDL окон/дверей, состава стены, материалов после санкционированной сборки.
- **Источник/версия:** официальный AC29 Data Conversion for IFC Export https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm (2026).
- **Лицензия:** штатный экспорт коммерческого AC29.
- **Контракт:** опции Classifications, Element Properties, Building Material Properties and Classifications, Element Parameters (включая Library Parts), Component Parameters (Composite Skins/Complex Profiles), Door-Window Parameters (Lining/Panel), Base Quantities. В IFC2x3 Building Material data привязаны к элементам, в IFC4/4.3 к IFC Materials. Element Parameters увеличивают размер IFC.
- **Направление:** AC→IFC read-only QA, не триадная синхронизация. Отключённый preset скрывает поля, не удаляя native данные.
- **№2 I0458-04:** зафиксировать read-only signature IFC Translator, сравнивать native GUID/tool/material/GDL/host с экспортными IFC полями, не менять Translator.

### F0458-05 — Space Boundaries ≠ Space Containment
- **Операция:** проверить связь Zone→ограждающие стены/окна/двери и наличие объектов в помещениях.
- **Источник/версия:** официальный AC29 Data Conversion https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm (2026).
- **Лицензия:** встроено в AC29.
- **Контракт:** IFC Space Boundaries экспортирует IfcRelSpaceBoundary и учитывает границы, прорезанные openings. IFC Space Containment относится только к Object/Lamp/Morph/Slab: для Object/Lamp/Morph нужны тот же Home Story и bbox-center внутри Zone 2D; для Slab — reference line между top/bottom и полигон в Zone. Это не native hostWall relation.
- **Направление:** AC→IFC QA, не автоматическое изменение.
- **№2 I0458-05:** отдельно проверять IfcRelSpaceBoundary / spatial containment / IfcRelVoidsElement / IfcRelFillsElement / native host Wall GUID; отсутствие containment у Wall/Window не считать потерей.

### F0458-06 — IFC spatial GUID не уникализирует независимые здания
- **Операция:** избежать ложного сопоставления этажей двух scratch BUILD-01 моделей.
- **Источник/версия:** официальный AC29 IFC Data Types https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-48.htm (2026).
- **Лицензия:** встроено в AC29.
- **Контракт:** IFC Project/Site/Building/Story GlobalIds выводятся из Project Info ID; одинаковые Building ID + Story Number в разных проектах могут дать одинаковые Story GlobalId. IFC GlobalId, Archicad Unique ID и native GUID различны.
- **Направление:** AC→IFC spatial identity, не cross-app GUID synchronization.
- **№2 I0458-06:** сравнивать `PLN path/hash + Building ID + Story number/index/elevation + native GUID`, не считать совпадение IFC Storey GUID идентичностью разных файлов; Project Info не изменять.

## 2. Реестр 27 реально выполненных SOURCE-сверок (не 27 независимых источников)
| № | Контракт | Доказательство/статус |
|---:|---|---|
| 01 | Точная исследовательская ветка существует | GitHub search_branches PASS |
| 02 | Issue #192 задаёт G0–G5 и single writer | https://github.com/dvikt33-ux/safe-bim-layer/issues/192 PASS |
| 03 | Triad pivot 23.10 11Z прочитан | research-1-20261023T11Z-TRIAD-PIVOT.md PASS |
| 04 | NEXT_RESEARCH_PRIORITIES.md расположен в extension-ranking, не в root | GitHub fetch_file PASS |
| 05 | Матрица count=61 | priority_matrix_20261018.json parsed PASS |
| 06 | Матрица items.length=61 | тот же JSON parsed PASS |
| 07 | GRASSHOPPER имеет priority=40 / decision=ИССЛЕДОВАТЬ_ТОЧКУ_ПОДКЛЮЧЕНИЯ | тот же JSON PASS |
| 08 | PR74 уже содержит 21-элементный исторический prototype, не новый BUILD-01 | https://github.com/dvikt33-ux/safe-bim-layer/pull/74 PASS |
| 09 | №1 03:56Z уже исследовал Model Compare и IFC property-only | research-1-20261024T0356Z-TRIAD-MODEL-COMPARE-IFC-SEMANTICS.md PASS |
| 10 | №2 04Z установил 3DM Hotlink = GDL reference, не native Roof | research-2-integration-2026-10-24T04Z-report.md PASS |
| 11 | №3 20.10 18Z доступен, но устарел | audit-2026-10-20-18-A.md PASS/STALE |
| 12 | GH-AC29 build3000 Windows Rhino7/8 от 01.10.2025 | https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ PASS |
| 13 | Teamwork чужое reservation → возможны дубликаты GH | Graphisoft Teamwork article PASS/HISTORICAL |
| 14 | Teamwork отсутствие нужного reservation → изменения не проходят | Graphisoft Teamwork article PASS/HISTORICAL |
| 15 | Teamwork ненужные GH элементы могут не удалиться | Graphisoft Teamwork article PASS/HISTORICAL |
| 16 | GH delete/recreate → SEO lost, GUID changed | Graphisoft Teamwork article PASS/HISTORICAL |
| 17 | GH attribute by ID may require restart connection | Graphisoft Teamwork article PASS/HISTORICAL |
| 18 | GH Source Definition + Last Update metadata documented historically | Graphisoft Teamwork + AC27 guide PASS/HISTORICAL |
| 19 | AC29 GH Deconstruct Roof only Single-Plane | https://help.graphisoft.com/AC/29/INT/GC.pdf PASS/SOURCE |
| 20 | AC29 Roof and Shell both export IfcSlab.ROOF by Element Type | AC29 IFC Type Mapping PASS |
| 21 | AC29 Window and Skylight both IfcWindow | AC29 IFC Type Mapping PASS |
| 22 | AC29 Door-Window Lining/Panel export option | AC29 Data Conversion PASS |
| 23 | AC29 Composite/Profile Component Parameters export option | AC29 Data Conversion PASS |
| 24 | AC29 IFC2x3 vs IFC4/4.3 Building Material data placement differs | AC29 Data Conversion PASS |
| 25 | AC29 IFC Space Containment restricted to Object/Lamp/Morph/Slab | AC29 Data Conversion PASS |
| 26 | AC29 IFC Space Boundaries exports IfcRelSpaceBoundary | AC29 Data Conversion PASS |
| 27 | AC29 IFC Story GlobalId derived from Building ID, can match across files | AC29 IFC Data Types PASS |

27 SOURCE checks = 11 repo/context + 16 document/official contract checks. Six cards, two counteraudits. No OFFLINE, BUILD, INSTALLED, LIVE or ACCEPTED in this run. Historical GH/Teamwork evidence is not an AC29 runtime acceptance.

## 3. Контрааудит A — «GH provenance даёт безопасную двусторонность?»
**ОПРОВЕРГНУТО.** Source filename/timestamp ≠ immutable GUID/owner lease/transaction ID. GH-generated Teamwork элементы могут дублироваться, не обновляться или терять SEO при recreate. На локальном AC29 GH provenance даже не проверен. Для APA-owned элементов GH writer запрещён. Вердикт: `GH_PROVENANCE_SOURCE_HISTORICAL`, `FULL_TRIAD_SYNC_NOT_PROVEN`.

## 4. Контрааудит B — «IFC IfcSlab.ROOF + материалы/Zone доказывают native Roof?»
**ОПРОВЕРГНУТО.** Roof и Shell сворачиваются в IfcSlab.ROOF при штатном type mapping; выключенные export options скрывают GDL/material/lining, Space Containment не равно hostWall; IFC Story GlobalId может совпадать между разными файлами. Нужен native GUID/Tool/host/roof topology/SEO/BREP + Save/Close/Reopen. Вердикт: `IFC_NATIVE_TYPE_COLLISION_CONFIRMED`, `NATIVE_ROOF_PRESERVATION_NOT_PROVEN`.

## 5. Передача №2, приоритет и ограничения
**I0458-01** GH provenance read-only inventory; **I0458-02** conditional Teamwork reservation/duplicate/SEO gate; **I0458-03** native Roof vs Shell gate; **I0458-04** IFC Translator signature/door-window/composite/material QA; **I0458-05** Zone boundary vs containment vs host; **I0458-06** namespace spatial IFC GlobalId by project/building/story.

Следующий инженерный шаг — **G0 только чтение**: активный AC29 build/port/PLN, Tapir APX/schema/command registration, Rhino8 SR, GH-AC29 package, .gh/.3dm paths и owner inventory. G1/G2 после G0, G3 только по отдельному разрешению. `PROJECT_PLAN` rev182 — только чтение. Никакого нового writer/синхронизатора, main, кода, PLN/APX, установки, LIVE, Work/Codex/Arena, платного API, merge. Публикация только в research branch; commit/fetch в отдельном подтверждении.
