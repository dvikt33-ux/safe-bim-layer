# APA №1 — TRIAD: граница Deconstruct, сложная кровля, Rhino ID и управление пересчётом
**Период:** 2026-10-24 01Z (04:00 МСК). **MODEL_MODE_NOT_VERIFIABLE.** Только SOURCE и чтение GitHub; никаких установок, LIVE, кода, изменений main/PLN/APX, Work/Codex/Arena, платных API и merge.

## 0. Реальное влияние на BUILD-01 #192 и доказательные статусы
**Новый P0-результат:** официальный **AC29 Grasshopper–Archicad Live Connection** прямо ограничивает **Deconstruct Roof только Single-Plane Roof**; при изменении Archicad-элемента для передачи его новых настроек в Grasshopper требуется **Send Changes**. Это **направленное чтение**, а не автоматическая двусторонняя запись. Штатное **Split into Single-Plane Roofs** в Archicad 29 не устраняет требование сохранить исходную нативную идентичность Multi-Plane Roof: операция изменяет состав элементов и требует отдельного согласования. Дополнительно официальный McNeel Content Cache имеет существенную развилку: при сохранённом Rhino ID Push/даже Bake заменяет объект, но при потере ID обычный Bake создаёт новые объекты; False у Action **не прекращает Pull**, пока виден Result. Это важно для устранения циклов и дубликатов при Rhino→GH→APA. Ни одно из решений не является общим трёхсторонним транзакционным синхронизатором.

**Статусы именно этого прохода:** SOURCE=28 отдельных проверенных утверждений/позиций (НЕ 28 независимых документов); OFFLINE=0 новых; BUILD=0 новых; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых. BUILD-01: G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. FULL_AUTOMATIC_NATIVE_GUID_PRESERVING_THREE_WAY_SYNC=NOT_PROVEN. Исторический 21-элементный PR74 не выдаётся за новое здание.

**Официальная версия:** Grasshopper–Archicad **29** Live Connection **build 3000**, Windows, поддержка **Rhino 7/8**, официальный список Graphisoft от **01.10.2025**; бесплатный add-on при отдельно лицензированных AC29/Rhino8. Это **не** AC29 executable build 5101 и не доказательство установки на компьютере. Rhino 8 Grasshopper — штатные компоненты в коммерчески лицензируемом Rhino8.

## 1. Шесть карточек новых контрактов и рисков

### C01 — AC29 Deconstruct существующего элемента: AC→GH READ, не writer
- **Операция:** изменить уже размещённую стену/перекрытие в Archicad и извлечь reference geometry + Settings в GH для следующего этапа BUILD-01.
- **Первоисточник/версия:** Graphisoft **AC29 GC User Guide**, раздел «Archicad Deconstruct Components», стр. 40: https://help.graphisoft.com/AC/29/INT/GC.pdf ; Windows add-on 29 build3000 https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ .
- **Контракт/направление:** вручную выбрать «Set one Element / Set Multiple Elements in Archicad» на GH Parameter; Deconstruct извлекает геометрию/Settings, далее Extract Settings. После ручного изменения в AC нажать **Send Changes** на палитре AC, чтобы обновить GH. Deconstruct **не имеет** входа Synchronize.
- **Ограничения:** GH получение параметров не равно GH изменению исходного Archicad GUID; автоматическая доставка после каждой операции без клика не доказана. GH Definition и объект должны быть однозначно идентифицированы. INSTALLED/LIVE не проверены.
- **№2:** I01-01 — описать SOURCE-only последовательность «AC edit → Send Changes → Deconstruct → GH frozen read → APA preflight», со снимком GUID/type/story/material до и после, без GH→AC записи.

### C02 — Deconstruct Roof: AC29 Multi-Plane НЕ поддерживается
- **Операция:** сложная кровля BUILD-01: изменить нативную Multi-Plane Roof в AC29 и прочитать её параметры в GH без потери типа и GUID.
- **Первоисточник:** тот же официальный **AC29** GC.pdf, «Deconstruct Roof»: **only Single-Plane Roofs; Multi-Plane Geometry not handled**. Версия build3000, Rhino7/8, Windows; отдельные лицензии AC29/Rhino8.
- **Направление:** AC SinglePlane Roof → GH Deconstruct READ; AC MultiPlane Roof → GH Deconstruct **UNSUPPORTED**. Обратное GH→существующая MultiPlane Roof не доказано.
- **Ограничения:** нельзя объявлять весь «AC→GH roof» двусторонним; конверсия MultiPlane→несколько SinglePlane изменяет BIM-состав и требует проверки GUID/Opening/Skylight/SEO.
- **№2:** I01-02 — в матрице BUILD-01 выделить SinglePlane read path и отдельный MultiPlane BLOCKED path; поискать **только готовые** штатные read-only альтернативы (Tapir geometry/IFC/3DM) с пометкой «геометрия ≠ нативные roof settings», не создавать writer.

### C03 — штатный Split MultiPlane Roof не сохраняет автоматически требуемую идентичность
- **Операция:** попытка обойти C02 через «Split into Single-Plane Roofs».
- **Первоисточники:** AC29 help https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-62.htm ; Graphisoft AC28 «Openings in Roofs» https://help.graphisoft.com/AC/28/INT/_AC28_Help/005_NewFeatures/005_NewFeatures-4.htm .
- **Контракт:** штатная команда AC29 преобразует одну MultiPlane в **несколько** SinglePlane; AC28 отдельно предупреждает, что Openings при split **recreated** in logical positions.
- **Направление:** AC→AC restructuring, **не** sync; не эквивалент исходному одному native Roof GUID.
- **Ограничения:** применимость AC28 формулировки об Opening к AC29 требует проверки; утверждать конкретные GUID после split без LIVE нельзя. Запрещено выполнять преобразование в рамках исследования.
- **№2:** I01-03 — пометить Split как **DESTRUCTIVE_TO_IDENTITY_RISK**, не рекомендовать для уже связанной кровли; добавить в G4 список проверки Roof GUID, child Openings, Skylights, SEO, materials, stories.

### C04 — Rhino8 Model Object и Brep: разные триггеры обновления
- **Операция:** изменение Rhino UserText/слоя/материала без изменения BREP → автоматический пересчёт GH.
- **Первоисточники:** ответ разработчика McNeel Kike Garcia от **09.10.2024** https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/19 ; официальный API Rhino8 GH **8.37.26258.02000 (15.09.2026)** https://developer.rhino3d.com/api/grasshopper/html/Properties_T_Grasshopper_Rhinoceros_Model_ModelObject.htm .
- **Контракт:** обычный **Brep parameter** отслеживает геометрию, не все атрибуты; **ModelObject** содержит Layer/Name/Id/UserText и реагирует на изменение атрибутов, в т.ч. изменение Layer. Rhino→GH READ/recompute, не Archicad write.
- **Ограничения:** лишние пересчёты при изменении слоя и риск обратной связи с Content Cache; точная SR локального Rhino8 не подтверждена. «Отслеживает UserText» не значит «сохраняет Archicad GUID».
- **№2:** I01-04 — для передачи BIM-полей в GH выбрать **Model Object** вместо Brep-only, разделить geometryHash/attributesHash, использовать штатный Data Dam/выключенную синхронизацию на время правки; пока только документарная схема.

### C05 — Content Cache: ID решает replace vs duplicate, False не выключает Pull
- **Операция:** обновить Rhino объект без дублирования и без циклического Rhino→GH→Rhino recompute.
- **Первоисточник:** официальный форум McNeel, руководство Scott Davidson **17.05.2024**, изначально **Rhino 8.8 RC**: https://discourse.mcneel.com/t/content-cache-updated-guide/181883 ; стабильная страница Rhino8 https://www.rhino3d.com/features/grasshopper/content-cache/ .
- **Контракт:** Push с отслеживаемым Rhino ID заменяет ранее созданный объект; Bake без ID может дублировать; **Push или Bake с существующим ModelObject ID заменяет**, а удаление ID (передача одной Geometry) делает Bake новым объектом. Action=False блокирует действие, **но Result продолжает Pull, пока виден**. Content Details показывает ID, CacheName, Cached/Referenced; Purge может затронуть также неиспользуемые Layers/Block Definitions/Materials.
- **Направление:** GH↔Rhino objects только; ни native AC BIM GUID, ни cross-app rollback не обеспечиваются.
- **Ограничения:** руководство первоначально о RC 8.8, локальная Rhino8 SR не квалифицирована; Content Cache не должен становиться вторым writer для APA-owned элементов; Purge не использовать в исследовании.
- **№2:** I01-05 — без LIVE описать GH cache gate: before/after Rhino ID + CacheName + content hash; False и скрытый Result для freeze, no Purge, no Bake stripped-ID; проверить документарно доступность в локальной Rhino8 SR до рекомендаций к установке.

### C06 — UserText: где хранить BIM cross-reference и почему не путать с GUID
- **Операция:** сохранять в Rhino 3DM происхождение Archicad элемента и атрибуты для read-only сопоставления после правки.
- **Первоисточник:** McNeel developer guide «Custom information on objects», редакция **05.12.2018** https://developer.rhino3d.com/en/guides/rhinopython/python-user-text/ ; Rhino8 API ModelObject 8.37.26258.02000 выше.
- **Контракт:** UserText string/string key/value на уровне документа, геометрии или атрибутов объекта; изменение данных **на геометрии** добавляет копию геометрии в Undo stack, на атрибутах экономнее. Rhino metadata READ/WRITE внутри Rhino, **не нативный AC GUID**.
- **Ограничения:** ключ вроде `ac_guid` — пользовательская строка, не доказательство GUID preservation; для переноса в AC через PR74 нужен существующий поддержанный контракт, не новый writer.
- **№2:** I01-06 — составить минимальный **read-only** crosswalk Rhino ObjectId / UserText / AC native GUID / IFC GlobalId / owner / story / sourceHash, запретить считать равными; в G4 сверять отдельно.

## 2. 28 фактически выполненных SOURCE-сверок (не тесты программ)
Каждая строка — конкретный проверенный факт по источнику. Разные строки одного документа НЕ считаются независимыми источниками.

01. GitHub search_branches: целевая `research/apa-extension-ranking-hub-20261018` существует.
02. GitHub TRIAD-PIVOT 2026-10-23 11Z: P0 = AC29+Rhino8+GH, G3 запрещён.
03. GitHub `NEXT_RESEARCH_PRIORITIES.md` в `docs/research/apa-results/extension-ranking/`: BUILD-01 #192 важнее числа SOURCE-отчётов.
04. GitHub issue #192: G0→G5, один новый целый native building; старый прототип не повторять.
05. GitHub PR #74: существует authored model-first route; нет разрешения повторить CREATE.
06. GitHub immutable PR74 `docs/APA_MODEL_FIRST_BUILDING.md`: 10 Wall, 2 Slab, 6 Window, 2 Door, 1 SinglePlane Roof.
07. Тот же PR74: SinglePlane Roof slope/contour edit **not qualified**, MultiPlane не заявлен.
08. GitHub №2 2026-10-24 00Z report: существующий SceneWriter/SQLite единственный APA writer.
09. GitHub №2 00Z matrix: MultiPlane roof authored **NOT_WIRED**, G0 BLOCKED_RUNTIME.
10. GitHub №3 `audit-2026-10-20-18-A.md`: G0 receipt отсутствует, Source ≠ Runtime.
11. GitHub `priority_matrix_20261018.json`: `count=61`, `items.length=61`, blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`.
12. GitHub №1 2026-10-24 00Z: Rhino MCP/Content Cache/Hotlink/Speckle уже описаны; не объявлять их заново.
13. Graphisoft download 2025-10-01: GH–AC29 Windows build3000 поддерживает Rhino7 и Rhino8.
14. AC29 GC.pdf: Deconstruct читает reference geometry и Settings существующих AC элементов.
15. AC29 GC.pdf: GH Parameter может ссылаться на вручную размещённый AC элемент через Set one/multiple.
16. AC29 GC.pdf: после изменения AC требуется команда Send Changes для обновления GH.
17. AC29 GC.pdf: Extract Settings выводит параметры выбранного элемента.
18. AC29 GC.pdf: у Deconstruct отсутствует вход Synchronize.
19. AC29 GC.pdf: Deconstruct Roof поддерживает только SinglePlane, MultiPlane не поддерживает.
20. AC29 help: штатный Split into Single-Plane Roofs доступен как преобразование MultiPlane.
21. AC28 help: при Split roof Openings могут быть recreated в логической позиции (не переносить на AC29 без оговорки).
22. Graphisoft Community 12–17.03.2024: описан случай потери roof GUID/SEO/окон после GH recompute при перемещении колонн в AC; пользовательский кейс, НЕ подтверждённый AC29 тест.
23. McNeel API GH 8.37.26258.02000: ModelObject содержит Id/Layer/UserText.
24. McNeel developer forum 09.10.2024: Brep-only не обновляется при произвольном изменении атрибутов, ModelObject — обновляется.
25. McNeel Content Cache guide 2024 (8.8 RC): ModelObject с ID Push/Bake заменяет, Geometry без ID Bake дублирует.
26. Там же: Action=False не останавливает Result Pull; Purge может удалять неиспользуемые definitions.
27. Там же: Content Details показывает ID, Cached, Referenced и CacheName; Result Pull имеет overhead.
28. McNeel UserText guide 2018: данные на геометрии вызывают копию в Undo, атрибутное хранение эффективнее.

**SOURCE URLs (проверены в ходе прохода):**
- https://help.graphisoft.com/AC/29/INT/GC.pdf
- https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-62.htm
- https://help.graphisoft.com/AC/28/INT/_AC28_Help/005_NewFeatures/005_NewFeatures-4.htm
- https://community.graphisoft.com/t5/Parametric-design/Updating-existing-Roof-Components-instead-of-creating-new-ones/td-p/592049
- https://developer.rhino3d.com/api/grasshopper/html/Properties_T_Grasshopper_Rhinoceros_Model_ModelObject.htm
- https://discourse.mcneel.com/t/detect-user-text-changes-to-trigger-content-cache/189163/19
- https://discourse.mcneel.com/t/content-cache-updated-guide/181883
- https://developer.rhino3d.com/en/guides/rhinopython/python-user-text/
- https://www.rhino3d.com/features/grasshopper/content-cache/
- https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- https://github.com/dvikt33-ux/safe-bim-layer/pull/74

## 3. Два контрааудита

### A / Направление обмена, авторство и ложная «двусторонность»
**Проверка:** C01 Deconstruct/Send Changes = AC→GH READ (с ручным действием); GH Design Sync = GH→AC запись только GH-owned элементов; C04 ModelObject = Rhino→GH event/read; C05 Cache = GH↔Rhino objects. Ни один из них не доказывает одновременную AC↔Rhino↔GH синхронизацию, exactly-once, межпрограммную транзакцию, авто-выбор инструмента, GUID preservation или конфликт-merge. Два writer одного GUID запрещены. **AUDIT A: PASS как разграничение контрактов; TRIAD ACCEPTANCE: FAIL/NOT_PROVEN.**

### B / Идентичность кровли, hosted objects и события пересчёта
**Проверка:** MultiPlane Roof как один native элемент ≠ несколько SinglePlane после Split; AC28 Opening recreation ≠ сохранение GUID; Rhino ModelObject ID ≠ AC GUID; UserText `ac_guid` ≠ native GUID; Content Cache False ≠ полностью остановленный Pull; Purge ≠ безопасный read-only; GH roof GUID-loss forum report ≠ проверка AC29. Без native GUID/type/story/host/SEO/Opening/Skylight readback + Save/Close/Reopen нельзя повышать статус. **AUDIT B: PASS как выявление рисков; MODEL SAFETY: NOT_ACCEPTED.**

## 4. Адресное поручение исследователю №2
**I01-01..I01-06** переданы текстом в карточках. Приоритет: (1) AC29 Deconstruct + Send Changes как только READ, (2) MultiPlane roof gap без Split, (3) Rhino ModelObject+Content Cache с сохранённым ID и остановкой лишнего Pull, (4) crosswalk независимых идентификаторов, (5) G0 actual runtime receipt, (6) GH JSON→PR74 preflight только после отдельного допуска на чтение локального окружения. **ГОТОВО** = документарная матрица «операция → owner → направление → gate → readback» без добавления writer, без LIVE.

## 5. Ограничения и границы результата
AC29 GC.pdf — официальный индексируемый текст, полный PDF в ходе прохода не выгружался из-за ограничений размера; извлечённые точные положения проверены через поиск официального документа, не весь PDF. McNeel Content Cache подробное руководство исходно для 8.8 RC, локальная SR неизвестна. История Roof GUID loss — свидетельство пользователя 2024, не приёмка AC29. Свежего №3 после 20.10 не обнаружено/не доказано. Исторический PROJECT_PLAN rev182 не извлекался, только чтение сохранено. Установленные AC29 build5101, Tapir1.5.10, Rhino8 и GH не подключались. Никаких новых SOURCE фактов не повышать до INSTALLED/LIVE/ACCEPTED. При проблеме публикации — WRITE_BLOCKED.

**MODEL_MODE_NOT_VERIFIABLE.**
