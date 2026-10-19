# APA №2 02Z — контрааудит Б: монтажный граф, недублирование, польза и безопасность

**Повторная собственная инженерная ревизия**, отдельно от проверки исходников. Не внешняя приёмка. Условие: ни один путь не создаёт второго Router, SceneWriter, IFC parser, scheduler, сметный или нормативный движок.

| Кандидат | Монтажная цепь и независимые границы | Риск, выбор и критерий ГОТОВО |
|---|---|---|
| A Attribute inventory 96 | APA existing Graphisoft connection → AC29 Python GetAttributesByType/GetBuildingMaterialAttributes → JSON в BIM Graph | REUSE, БЫСТРО; GUID/index/errors на всех атрибутах, no writes |
| D Publisher preflight 95 | APA → AC29 Python GetPublisherSetNames/GetNavigatorItemTree → Tapir GetNavigatorItemTree для сравнения | REUSE, БЫСТРО; set name однозначен, allowlist GUID непуст, пропуски fail-closed, Publish не запускать |
| E IFC classification 94 | APA PR165 V2 sidecar → pinned util.classification.get_references → JSON QA | ADAPTER, АДАПТАЦИЯ; inherited/own/override per system, IFC2X3/4, GlobalId; no second graph |
| G bSDD 91 | APA read-only sidecar → bsdd.Client → публичный bSDD REST → JSON cache | ADAPTER, АДАПТАЦИЯ; explicit include_test=False, dictionary URI/version/license/status, 429 fail-closed; никаких private APIs |
| F IFC 5D 88 | APA PR167 B2 private IFC → util.cost getters → JSON | ADAPTER, АДАПТАЦИЯ; missing≠zero, IfcSpace, UnitBasis/currency/rate, DIVIDE/0; не выдавать за ГЭСН/ФЕР |
| H IFC 4D 85 | APA PR167 B2 → util.sequence task/input/output getters → JSON | ADAPTER, АДАПТАЦИЯ; 3 tasks, orphan/unscheduled, predecessor and GUID, None guard; не новый scheduler |
| B/C attribute classification/property | APA → SDK29 C++ read-only methods → **JSON binding NOT_FOUND** | DEFER, ДОЛГО; минимально недостающий SDK29 read-only endpoint, требуются разрешение, ABI и license |

**Альтернативы:** (1) Attribute inventory: официальный AC29 JSON vs новый SDK APX — выбирать официальный; C++ только для отсутствующих property/classification. (2) bSDD: готовый bsdd.Client + минимальные guards/cache vs новый OpenAPI client/MCP server — выбрать готовый, один внешний пакет. (3) IFC 4D/5D: pinned IfcOpenShell util через existing B2 vs отдельный расчётный/планировочный сервис — выбрать existing B2, read-only. Каждая цепь имеет максимум 3 внешних звена.

**Монтажный gate:** SOURCE сейчас. OFFLINE: отдельные IFC2X3/4 positive/negative fixtures, 5D zero/missing/Space/divide, 4D unscheduled, bSDD HTTP 429/5xx и stale license, Publisher empty/duplicate; input SHA и GUID. BUILD: Windows11 Python3.11/3.12 exact lock, без изменения main. INSTALLED: actual hash/version и opt-in existing Router. LIVE: только с отдельным разрешением, scratch PLN, GUID/BREP before/after, zero writes. ACCEPTED: независимый readback, negative tests, rollback. RTX4060 8GB/48GB RAM не измерялись; не планировать GPU/LLM. Сетевой bSDD доступ по умолчанию выключен до утверждения.

**Вопросы №1:** 1) Найти готовый AC29 SDK29 attribute property/classification read-only sample с совместимым ABI. 2) Есть ли штатный GUID resolver для Publisher Set при одинаковых именах? 3) Найти проверенный bsdd.Client retry/cache wrapper без private endpoints. 4) Найти IFC2X3/IFC4 fixture с type→occurrence override. 5) Найти IFC4D orphan/unscheduled и 5D zero/Space fixture.

**Передача №3 на утверждение:** A96, D95, E94, G91, F88, H85. B84/C82 отложить. Первый этап после разрешения — OFFLINE fixtures и сравнение с существующими APA reports, не установка. Нет новых LIVE/ACCEPTED. `NEXT_RESEARCH_PRIORITIES.md` меняет только №3. MODEL_MODE_NOT_VERIFIABLE.

**Аудит Б: PASS_SOURCE / INTEGRATION_NOT_RUN.** Инженерная ценность — меньше дублирования и лучше fail-closed QA, но экономия времени и скорость не измерялись.
