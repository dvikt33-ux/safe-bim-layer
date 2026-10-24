# APA AC29 — №2 инженер интеграции — 2026-10-19 14Z

**Статус SOURCE ONLY; MODEL_MODE_NOT_VERIFIABLE.** 30 фактических статических проверок ниже (НЕ runtime-тесты), два независимых контрааудита A/B. Цель: способы подключения к существующему Router/Bridge, BIM Graph, SceneWriter; без второго writer, установки, кода, PLN/APX, main, PR merge и LIVE.

## 0. Прочитано первым / исходное состояние
- [Очередь №3](../NEXT_RESEARCH_PRIORITIES.md) SHA `2cb49edc410632c65503d8f17e93c58bc2d971d1` (последняя редакция 18.10 20Z); [матрица 61](../priority_matrix_20261018.json) SHA `9cb5e6f2a59f80762cc77073eeb10404829af75a`; [каталог 61](../candidates.json) SHA `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`. Задачи №2: [A](audit-2026-10-18-20-tasks-2A.md), [B](audit-2026-10-18-20-tasks-2B.md). Их приоритеты T2-20-01..08 сохраняются, новая версия Tapir не отменяет их.
- №1: последний найденный файл [09Z checks](research-1-20261019T09Z-checks.md); последний полный [07Z](research-1-20261019T07Z.md). Более свежий основной отчёт №1 в целевой hourly директории **не обнаружен**; не жду публикации. №3 позднее 20Z также не обнаружен. Предыдущий №2 [13Z](research-2-integration-2026-10-19T13Z.md).
- Канон [PROJECT_PLAN.json revision 182](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json), blob `c2ab2f9d606db1412c4031076103c267fc463f83`, прочитан без изменения. Политика: план — единственный диспетчер, не создавать вторую очередь.
- Существующие [APA V2](https://github.com/dvikt33-ux/safe-bim-layer/blob/5c0dc009e729db9834301b4a369512490a205ef7/scripts/apa_high_density_readonly_v2.py) и [C1](https://github.com/dvikt33-ux/safe-bim-layer/blob/7589c5dcee1fb71edae64e1d3bc9b1de14693e8e/scripts/apa_dxf_geometry_c1.py) прочитаны: opt-in Router, IFC-порты, ezdxf 1.4.5, recursive_decompose; ни один не заменять. PR164/171/173 SceneWriter/Hotlink не повторять. Старую фразу очереди «PR173 batch не LIVE» нельзя считать актуальным доказательством отсутствия LIVE: см. поздние saved/reopened receipts, но независимый ACCEPTED отсутствует.
- Новый факт относительно 13Z: **в Tapir 1.7.2 одновременно две несовместимые семьи Graphic Override**, и **SaveProject(projectPath) может перезаписать PLN**, а также выявлен sentinel ассоциативной отметки и false-PASS DeleteElements.

## 1. Независимые первоисточники, строго tag 1.7.2
- **R** https://api.github.com/repos/ENZYME-APD/tapir-archicad-automation/releases/tags/1.7.2
- **A** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/AddOnMain.cpp
- **G** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicOverrideCommands.cpp
- **H** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicalOverrideCommands.cpp
- **C** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/ElementCreationCommands.cpp
- **E** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/ElementCommands.cpp
- **P** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/ProjectCommands.cpp
- **D** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/3DProjectionCommands.cpp
- **X** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GridElementCommands.cpp
- **M** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/MEPCommands.cpp
- **S** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/RFIX/Images/CommonSchemaDefinitions.json
- **T** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/LICENSE
- **K** https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/LICENSE
- **Q** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
- **V** https://github.com/dvikt33-ux/safe-bim-layer/blob/5c0dc009e729db9834301b4a369512490a205ef7/scripts/apa_high_density_readonly_v2.py
- **Z** https://github.com/dvikt33-ux/safe-bim-layer/blob/7589c5dcee1fb71edae64e1d3bc9b1de14693e8e/scripts/apa_dxf_geometry_c1.py

## 2. 30 проверок: вопрос → pinned source/lines → контракт → блокер → вердикт/следующая проверка
01. **Релиз и AC29-бинарник?** Источник **R assets**; контракт: 1.7.2 опубликован 2026-10-19 11:49:43Z; TapirAddOn_AC29_Win.apx, 5 914 112 байт, SHA256 4714fcbfadb47307b0b3cecf578fe18ff326f3c06ee0b8e7db5a31a979a01bf7. Блокер: Нет SHA локальной 1.5.10. Вердикт/следующий шаг: **SOURCE; далее сравнить локальную подпись/хеш, без установки**.
02. **Разделение лицензий?** Источник **T / K**; контракт: Tapir MIT, Graphisoft SDK29 отдельное Graphisoft Software License Agreement; Archicad лицензионный продукт. Блокер: Нельзя приписать всей цепочке MIT. Вердикт/следующий шаг: **SOURCE; далее проверить права использования установленного AC29**.
03. **Две параллельные семьи Graphic Override?** Источник **A:926-958,1210-1222**; контракт: В одном теге зарегистрированы GetGraphicOverrideRules (plural, пакет) и GetGraphicalOverrideRules (plural, другая форма), а также разные Create-команды. Блокер: Два контракта одной сущности, риск дубля и неверного маршрута. Вердикт/следующий шаг: **ADAPTER; далее выбрать единственный канонический read-path**.
04. **Богатый readback правил?** Источник **G:319-365**; контракт: GetGraphicOverrideRules -> graphicOverrideRules[]: graphicOverrideRuleId GUID, name, criterionXML, style, ruleGroupName. Блокер: Требует 1.7.2, локальная 1.5.10 неизвестна. Вердикт/следующий шаг: **ADAPTER; далее сравнить style+GUID с Navigator/ViewMap**.
05. **Ограниченный альтернативный readback?** Источник **H:218-283**; контракт: GetGraphicalOverrideRules -> rules[]: ruleId, name, ruleGroupName, criterionXML; style отсутствует. Блокер: Не годится для полной QA визуального стиля. Вердикт/следующий шаг: **REJECT как единственный источник; далее использовать G**.
06. **Пакетный контракт создания правил?** Источник **G:378-443**; контракт: CreateGraphicOverrideRules принимает graphicOverrideRules[]; обязательны name,ruleGroupName; возвращает graphicOverrideRuleIds[] по порядку. Блокер: Нельзя трактовать общий HTTP success как успешные все элементы. Вердикт/следующий шаг: **DEFER writes; далее OFFLINE 2 success + 1 error**.
07. **XML критериев может молча пропасть?** Источник **G:393-405, H:78-91**; контракт: Документация в схеме: XML, написанный с нуля, Archicad отбрасывает без ошибки; правило тогда применяется ко всем элементам. Блокер: КРИТИЧНО: ложная цветовая классификация и массовое изменение вида. Вердикт/следующий шаг: **REJECT произвольный XML; далее read-existing/modify/readback**.
08. **Готовая структурированная альтернатива XML?** Источник **G:220-249**; контракт: criterion (structured GraphicOverrideCriterion) конвертируется в XML; одновременно criterionXML и criterion запрещены. Блокер: Проверять сериализацию и фактическую выборку элементов. Вердикт/следующий шаг: **ADAPTER prefer structured; далее 2 positive/negative fixtures**.
09. **Проверка GUID атрибутов стиля?** Источник **G:61-78**; контракт: GetAttributeFromField проверяет GUID, тип и индекс атрибута, ошибку APIERR_BADPARS при несовпадении. Блокер: GUID материала нельзя подменять индексом слоя. Вердикт/следующий шаг: **REUSE; далее fixture wrong attribute type**.
10. **Взаимоисключающие параметры фона?** Источник **G:140-177**; контракт: fillBackgroundPen и fillBackgroundColor вместе -> APIERR_BADPARS. Блокер: Нельзя слить два независимых формата настроек. Вердикт/следующий шаг: **ADAPTER schema gate; далее negative fixture**.
11. **Взаимоисключающие параметры поверхности?** Источник **G:174-195**; контракт: surface и surfaceColor вместе -> APIERR_BADPARS; без appliesTo стиль охватывает cut/uncut surfaces. Блокер: Риск неожиданного переопределения всех поверхностей. Вердикт/следующий шаг: **ADAPTER explicit appliesTo; далее readback**.
12. **Ошибки поэлементные?** Источник **G:444-491**; контракт: CreateGraphicOverrideRules внутри undoable loop продолжает после ошибки и возвращает item error либо GUID. Блокер: Частичный результат нельзя помечать PASS. Вердикт/следующий шаг: **FAIL_CLOSED; далее сверить count и все GUID**.
13. **Упрощённый Create меняет существующее правило?** Источник **H:135-207**; контракт: CreateGraphicalOverrideRule находит rule по имени во всём проекте и вызывает ChangeOverrideRule, даже если другая группа. Блокер: Риск перезаписи чужого правила. Вердикт/следующий шаг: **REJECT автоматическое использование; далее preflight names+GUID**.
14. **Неявная группа Tapir?** Источник **H:137-145**; контракт: При отсутствии ruleGroupName выбирается группа 'Tapir'. Блокер: Нарушение контролируемой схемы именования APA. Вердикт/следующий шаг: **ADAPTER explicit group; далее allowlist**.
15. **Пакетная комбинация по GUID?** Источник **G:790-880**; контракт: CreateGraphicOverrideCombinations: name + ordered graphicOverrideRuleIds[]; ответ graphicOverrideCombinationIds[] с ошибками. Блокер: Правильный контракт сохраняет приоритет правил. Вердикт/следующий шаг: **ADAPTER после read-only; далее order readback**.
16. **Упрощённая комбинация по именам перезаписывает?** Источник **H:300-366**; контракт: CreateGraphicalOverrideCombination: name + ruleNames[]; если имя уже есть, ChangeOverrideCombination заменяет список. Блокер: Риск незаметной смены документационных видов. Вердикт/следующий шаг: **REJECT по умолчанию; далее preflight GUID/name**.
17. **Ограничение текущего окна AC30?** Источник **A:1137-1148**; контракт: Get/SetActiveGraphicalOverrideCombination прямо помечены Available from Archicad 30. Блокер: SDK30 не является подтверждением AC29. Вердикт/следующий шаг: **REJECT AC29; далее GetViewSettings/read-only**.
18. **Готовая штатная альтернатива для сохранённых видов?** Источник **Q / A:1128-1135**; контракт: Официальный AC29 Navigator/View API и Tapir GetViewSettings читают сохранённые настройки, но не равны active window override. Блокер: Нельзя приписать текущему окну состояние сохранённого вида. Вердикт/следующий шаг: **REUSE existing Router; далее сравнить view GUID и override combination**.
19. **Нативные оси доступны только в новом релизе?** Источник **A:555-568 / X:175-225**; контракт: GetGridElements возвращает elementId, floorIndex,layerIndex,pos,angle,length,libraryPartName. Блокер: Не доказано наличие в локальной 1.5.10. Вердикт/следующий шаг: **DEFER; далее capability gate и сравнение с native inventory**.
20. **Создание осей может быть частичным?** Источник **X:496-545**; контракт: CreateGridElements -> elements[] и warnings[]; нулевая длина <1e-6 отбрасывается. Блокер: Считать PASS только count=expected и warnings=[]. Вердикт/следующий шаг: **ADAPTER после допуска; далее 2x2 fixture**.
21. **Параметры GDL осей не универсальны?** Источник **X:225-250,540-566**; контракт: GDL array parameter не поддержан; AC_Length fallback к A; lengthMode меняет семантику. Блокер: Не создавать свой GDL-движок. Вердикт/следующий шаг: **DEFER; далее defaults + param names**.
22. **Curtain Wall — реальные полилинии, не произвольные контуры?** Источник **C:2813-2885,3174-3203**; контракт: curtainWallsData[]; coordinates минимум 2; каждый последовательный отрезок — сегмент, одинаковые соседние точки запрещены. Блокер: Открытый профиль, не полигон произвольного здания. Вердикт/следующий шаг: **ADAPTER; далее 2-segment synthetic input**.
23. **Curtain Wall зависит от favorites/defaults?** Источник **C:2813-2885,3203-3255**; контракт: Непереданные classes/pattern/surfaces наследуются из favorite или Tool defaults; zCoordinate абсолютная отметка, floorIndex может выводиться. Блокер: Нельзя считать результат детерминированным без snapshot defaults. Вердикт/следующий шаг: **DEFER writes; далее frozen favorite + readback**.
24. **Level Dimension — готовая ассоциативность?** Источник **C:4550-4640,4640-4675**; контракт: levelDimensionsData[]: position, parentElementId GUID, level; родитель задаёт высоту и этаж. Блокер: Нужен parent GUID и проверка попадания точки на геометрию. Вердикт/следующий шаг: **ADAPTER; далее point-in-parent offline**.
25. **Level Dimension — опасный sentinel?** Источник **C:4562-4578**; контракт: При маркере вне родительского контура Archicad может создать объект, но GetDetailsOfElements.level=-110000000. Блокер: Создание GUID != корректная высотная отметка. Вердикт/следующий шаг: **FAIL_CLOSED; далее readback finite+domain**.
26. **Разные единицы Level Dimension?** Источник **C:4580-4638**; контракт: level в метрах; textHeight/markerSize в миллиметрах бумаги; angle в радианах; dimForm 0..19. Блокер: Ошибки ×1000 и некорректный символ отметки. Вердикт/следующий шаг: **ADAPTER unit gate; далее roundtrip mm/m/rad**.
27. **SaveProject теперь может перезаписать другой PLN?** Источник **P:1363-1420**; контракт: projectPath (опционально) действует как Save As и перезаписывает существующий файл; активный проект переключается на него. Блокер: КРИТИЧНО: запрет вызывать на исходном PLN; существующий GuardedSaveTransport не заменять. Вердикт/следующий шаг: **REJECT direct save; далее только review разрешённого scratch workflow**.
28. **Безопасный plain save использует Floor Plan?** Источник **P:1397-1453**; контракт: Если projectPath не задан, команда временно активирует Floor Plan и делает plain Save; сохраняет отказ read-only. Блокер: Операция меняет окно, а не просто пишет байты. Вердикт/следующий шаг: **DEFER; далее source-vs-opened project readback**.
29. **DeleteElements возвращает успех для отсутствующего GUID?** Источник **E:4738-4798**; контракт: После delete API отсутствующий GUID трактуется как success, даже если элемента не было до операции. Блокер: Ложный PASS при недостоверном списке исходных GUID. Вердикт/следующий шаг: **REJECT без pre-inventory; далее before/after GUID diff**.
30. **MEP read-only и версия AC29/AC30?** Источник **A:1438-1462 / M:1390-1444**; контракт: GetMEPPreferenceTables расширен referenceSet/angleSet/fittingTables, transition доступен AC29; GetMEPSystemGroups AC29; ElectricalPanels AC30. Блокер: Не переносить электрические команды на AC29; нет подтверждения лицензии MEP Designer. Вердикт/следующий шаг: **ADAPTER read-only; далее schema/permissions/port provenance**.
## 3. Матрица подключения (10 конкретных решений; баллы — экспертная польза, НЕ ускорение)
| Инструмент → путь (≤3 внешних звена) | Контракт/версия, reuse APA | Выбор / польза / трудность / риск | Критерий ГОТОВО |
|---|---|---|---|
| Tapir Graphic Override **read** → Router→Tapir→BIM Graph | G:319-365; 1.7.2 AC27+; GUID/name/XML/style/group; MIT+Graphisoft license | **ADAPTER 99**, АДАПТАЦИЯ, средний (локальная 1.5.10 неизвестна) | capability true; полные GUID/style; 0 missing; no model write |
| Graphic Override **structured criteria** → Router→Tapir→existing View QA | G:220-249,378-491; structured criterion, item errors; AC27+ | **DEFER 98**, АДАПТАЦИЯ, высокий (XML fail-open) | OFFLINE criterion fixtures; затем согласованный LIVE scratch, выборка не all-elements, GUID/style readback |
| View Map / saved override → Router→официальный JSON AC29→Navigator | Q, A:1128-1135; existing official API; SDK Graphisoft license | **REUSE 96**, БЫСТРО, низкий для чтения | GUID вида, settings, override ID, совпадение до/после, без вызова AC30-only active window |
| Нативные оси Grid → Router→Tapir→BIM Graph | X:175-250,496-570; 1.7.2 AC26+, elements/warnings, GDL defaults | **DEFER 95**, АДАПТАЦИЯ, высокий (binary version) | 2×2 input/output GUID, warnings=0, length/floor/layer readback, saved scratch только по разрешению |
| Curtain Wall → Router→Tapir→existing SceneWriter gate | C:2813-2885,3174-3255; 1.7.2, favorite+polyline+pattern | **DEFER 93**, АДАПТАЦИЯ, высокий (defaults drift) | frozen favorite, segments/panels/frames GUID, world coords, save/reopen scratch; не дублировать SDK writer |
| Level Dimensions → Router→Tapir→BIM Graph | C:4550-4755; 1.7.2, parent GUID, mm/m/rad, sentinel -110000000 | **DEFER 96**, АДАПТАЦИЯ, высокий (silent invalid height) | parent hit, level finite valid, origin, dimensions, parent GUID readback; no sentinel |
| Native QTO → Router→Tapir→existing IFC QA | A:383, PR860; 1.7.2; elements,minOpeningSize, per-item quantities/errors | **ADAPTER 94**, АДАПТАЦИЯ, средний | 1 wall+slab, m²/m³, threshold pinned, no native/IFC GUID conflation |
| MEP preference/system groups **read** → Router→Tapir→V2 BIM Graph | A:1438-1462, M:1390-1444; AC29 fittings and groups; AC30 electrical excluded | **ADAPTER 91**, АДАПТАЦИЯ, средний | domain/refSet/angleSet/owner, schema and permissions; IFC ports independently crosschecked |
| 3D projection **read** → Router→Tapir→View QA | D:10-100; 1.7.1+ in 1.7.2, 12-value axono matrix or perspective fields | **ADAPTER 89**, АДАПТАЦИЯ, средний | projection type, 12 numeric matrix values, no Set3DProjectionSettings; compare saved view |
| Delete/Save safety guard → existing Router/GuardedSaveTransport, **no direct new writer** | E:4738-4798 and P:1363-1453; 1.7.2, missing GUID success, Save As overwrite | **REUSE safety 100**, БЫСТРО (analysis), критический при нарушении | read-only pre/post GUID snapshot; deny projectPath to original, no deletion unless explicit approval; no false PASS |

**Альтернативы и выбор.** Для Graphic Override: (A) богатый пакетный GetGraphicOverrideRules (GUID+XML+style+group) против (B) GetGraphicalOverrideRules (без style). Выбор A для чтения, B отклонён как единственный источник; для записи — структурированный criterion и пакетные per-item errors, не single upsert-by-name. Для сохранения: (A) существующий GuardedSaveTransport + preflight/receipt против (B) прямой Tapir SaveProject(projectPath) с overwrite. Выбор A; B отклонён. Для нативных осей: (A) Tapir 1.7.2 с готовым CreateGridElements против (B) новый SDK29 APX. Выбор A как минимальный будущий путь, но до проверки бинарника DEFER; B не разрабатывать. Все пути ≤1 новый внешний инструмент, не требуется Rhino/Grasshopper.

## 4. Монтажный контракт и безопасные ворота (план, НЕ выполненные действия)
1. **SOURCE:** pinned tag 1.7.2, release asset SHA256, MIT/SDK license, JSON schema, runtime version delta, список опасных writes; текущий статус этого отчёта.
2. **OFFLINE:** в будущей изолированной ветке с разрешения координатора — контрактные fixtures для 10 команд, ошибки/пустые результаты, units/GUID/criteria, сравнение с уже существующим APA; никакого Archicad runtime.
3. **BUILD:** только если выбран SDK путь — компиляция SDK **29**, а не SDK30; для готового Tapir бинарника BUILD=VENDOR_RELEASE_VERIFIED, не локальный BUILD. Проверить release provenance/signature и hash.
4. **INSTALLED:** лишь после отдельного разрешения — локальный backup установленного APX 1.5.10, SHA и перечень доступных команд, AC29 build 5101, контроль регистраций; сценарий отката до старого APX; сейчас NOT_RUN.
5. **LIVE:** только scratch PLN, явное разрешение; read-only раньше writes, единственный Router/Bridge и журнал; per-item errors, GUID+coordinate+style readback, no publisher, no production writes.
6. **ACCEPTED:** независимый аудит, сохранённая копия и повторное открытие, проверка GUID/вида/отметки/стиля, квитанция и утверждение №3; не подменять ACCEPTED успешным JSON.

**Windows 11 / AC29 5101 / 8 GB VRAM / 48 GB RAM:** metadata, Grid/Override/LevelDim не требуют собственного GPU; 3D mesh/QTO могут потребовать RAM/время, измерений нет. Локальная 1.5.10 не идентифицирована по SHA и не объявляется совместимой с 1.7.2. Обновление APX не выполнять. Никаких заявлений 100×.

## 5. Контрааудит А — независимая проверка версии/API/лицензий
- Сверено по **tag 1.7.2**, не по main: A регистрирует одновременно обе семьи, G/H имеют разные input/output schemas; особенно опасен H upsert-by-name и G/H XML fail-open. Это SOURCE, не доказательство успешной регистрации на AC29 5101.
- R показывает отдельный AC29 Win APX и SHA256; T MIT; K — Graphisoft proprietary SDK. Ни одна локальная подпись/установка не проверялась. AC30-only active window и electrical исключены из AC29.
- Внутренние контракты: H ruleId отличается от G graphicOverrideRuleId; G batch item errors; C LevelDimension.level sentinel; P SaveProject projectPath overwrite; E delete missing-GUID success. Автоматический generic adapter **запрещён**, пока поля не нормализованы.
- Контрвердикт: **SOURCE_PASS_WITH_CRITICAL_GATES**. NOT_INSTALLED, NOT_LIVE, NOT_ACCEPTED.

## 6. Контрааудит Б — независимая проверка графа монтажа, дублирования, пользы и безопасности
- Никакого нового движка: Router→официальный AC29 JSON для видов, Router→существующий Tapir для будущих команд, Router→существующие V2/C1 для IFC/DXF; BIM Graph/SceneWriter остаются владельцами GUID/журналов.
- Две семьи Override нельзя одновременно экспонировать как одинаковую команду: разные ID keys, семантика upsert/create и покрытие style; выбирать один канонический маршрут. Учитывать view-specific комбинации: глобальное правило не равно цвету каждого вида.
- Предотвратить четыре ложных PASS: invalid criterion XML→all elements; LevelDim вне host→-110000000; DeleteElements missing GUID→success; SaveProject success без независимого saved/reopened receipt. При любой неоднозначности `NOT_VERIFIED`.
- Ни одна новая функция не нужна для повторения уже доказанных PR164/171/173; не запускать Clone/Hotlink/Publisher. PR165 MEP port owners и C1 MINSERT остаются задачами №3 выше новых оформительских работ.
- Контрвердикт: **ADAPTER_AFTER_GATES**, приоритет безопасности выше красоты листов.

## 7. Адресные вопросы исследователю №1
1. Найти официальный AC29 read-only API/SDK29 sample для полного списка комбинаций Graphic Override и фактической связи с saved ViewMap, не AC30 active window.
2. Найти доказанный AC29 способ валидации criterion XML **без применения к модели**, либо готовый schema validator; если нет — NOT_FOUND.
3. Найти vendor tests/CI Tapir 1.7.2 на AC29 5101 для GraphicOverride, LevelDimensions и CurtainWalls; отделить source от runtime.
4. Проверить source/лицензию конкретной локальной сборки Tapir 1.5.10 только через имеющиеся read-only receipts (не угадывать бинарник).
5. Проверить официальные AC29 способы получить LevelDimension host intersection и отрицательные результаты без создания элемента.
6. Найти официальную возможность определить write-safe readonly project state перед Save As; при отсутствии NOT_FOUND и сохранить GuardedSaveTransport.

## 8. Координатору №3 на утверждение (НЕ менять очередь №3)
1. **100** — охранный контракт SaveProject/DeleteElements, исключить overwrite/false PASS.
2. **99** — read-only инвентаризация Graphic Override с GUID+style+XML+group, выбор одной семьи.
3. **98** — структурированные критерии Graphic Override: negative XML/all-elements fixtures (OFFLINE only).
4. **96** — LevelDimension sentinel/units/host GUID gate (OFFLINE).
5. **95** — GridElements 1.7.2 schema/warnings, без установки.
6. **94** — Native QTO threshold/materials с existing BIM Graph (OFFLINE).
7. **93** — CurtainWall favorites/pattern determinism (OFFLINE).
8. **91** — MEP preference/system groups AC29 read-only, без AC30 электрических API.

**Все 30 проходов — SOURCE inspection, два контрааудита — аналитические.** SOURCE=PASS for cited tag, OFFLINE=NOT_RUN, BUILD=NOT_RUN, INSTALLED=NOT_VERIFIED, LIVE=NOT_RUN, ACCEPTED=NO. Изменение NEXT_RESEARCH_PRIORITIES.md, PROJECT_PLAN.json, рабочего кода и PLN/APX запрещено и не выполнялось.
