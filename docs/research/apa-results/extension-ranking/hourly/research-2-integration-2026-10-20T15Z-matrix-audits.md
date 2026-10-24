# APA №2 — 20.10.2026 15Z — матрица BUILD-01 и два контрааудита

Только исследование SOURCE. Оценки — экспертная ценность для BUILD-01 (0–100), не измеренное ускорение. Windows 11, AC29 build5101; локальный Tapir обозначен 1.5.10, SHA/ABI/команды установленного APX НЕ проверены. Нет новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED.

| G | Готовая цепочка (не более 3 внешних звеньев) | Источник/контракт | APA reuse | Вердикт / польза / сложность / риск | ГОТОВО |
|---|---|---|---|---|---|
| G0 | APA → existing Bridge READ → live schema export; отдельно Windows SHA256 APX | PR150 capture_read_task; Tapir GetProjectInfo/GetStories/GetAddOnVersion; PowerShell 5.1 Get-FileHash | Existing Router, EvidenceAPI | REUSE+минимальный manifest / 100 / БЫСТРО / высокий до readback | Immutable code/APX SHA, порт, PLN, этажи, список команд и схем |
| G1 | intent → PR74 compiler → BIM Graph DAG | PR74 compile_authored_intent, apa-authored-project/1, units=meters, sourcePlanHash | PR34/48/74 | REUSE / 100 / БЫСТРО / средний | Новое двухэтажное задание, полный DAG/topological order, реальный read-only preflight |
| G2 | GetStories → resolve_stories → native floorIndex | PR74 authored_native L24–53, level/height 2.4–4.5m | PR48/74 | REUSE / 99 / БЫСТРО / средний | index/floorId/name/level совпали с активной scratch PLN |
| G2 | CreateSlabs → details → ModifySlabs → details | pinned CreateSlabs v1.0.3 без material, ModifySlabs v1.4.0; PR74 SceneWriter L856–914 | SceneWriter+SQLite | REUSE / 100 / АДАПТАЦИЯ / высокий до LIVE | оба этажа: GUID, Basic, thickness, material GUID и BREP после readback |
| G2 | typed CreateBeams → existing NativeAdapter → BIM Graph | PR149 CreateBeams только Basic axis-aligned, floorIndex=0, 1 элемент | PR74+PR149 | ADAPTER/DEFER / 94 / АДАПТАЦИЯ / высокий | beam optional; этаж1 квалифицирован отдельно; без второго writer |
| G2 | Walls GUID → hosted Doors/Windows → readback | PR131 ownerWallId, centerOffset, sillHeight, settingsHash, host-fit | PR74/131 | REUSE / 99 / БЫСТРО / средний | GUID хозяина, этаж, размеры, BREP отверстия, отсутствие перекрытий |
| G2 | DynamicCommands.execute_batch → existing SceneWriter | PR126 1–200, 6 CREATE типов, pre/post verification | PR126/SceneWriter | DEFER / 92 / АДАПТАЦИЯ / высокий | G1 single маршрут PASS; 1 native batch receipt и full independent verifier |
| G2 | verified group members → PR162 selector → native group commands | PR162 2–128 members, ≤32 placements, sourceRef, dependency proof | PR162/Graph | DEFER / 84 / ДОЛГО / высокий | отдельный installed provider + group GUID/readback, не дублировать Clone |
| G4 | GuardedSave → byte snapshot → Close/Open → native readback | PR175 snapshot SHA + cooperative lock; ModelDumpV1 не в 262 Tapir | PR74/175 + existing BIM Graph | ADAPTER / 100 / АДАПТАЦИЯ / высокий | отдельная квитанция BUILD-01: GUID/BREP/material/host после GUI reopen |

**Лицензии и среда.** Tapir tag1.5.9 — MIT; Graphisoft SDK29.3000 — Graphisoft Software License Agreement, не MIT. PowerShell Get-FileHash встроен в Windows; дополнительные пакеты не нужны для хеша. Для локального 1.5.10 ни SHA APX, ни точная установленная команда не проверены. GPU 8GB и RAM 48GB не влияют на эти JSON/CLI контракты; объём BREP и расход памяти надо измерять, не прогнозировать. Отмена: до G3 ничего не меняется; при G3 отдельная scratch, SQLite intent-before-write, UNKNOWN→STOP/read-only reconcile, snapshot; никакого автоматического повтора CREATE.

## Контрааудит А — исходники, версии, лицензии

1. PR74 schema содержит 262 команды; provider 1.5.10 ≠ локальный binary SHA. CreateSlabs v1.0.3 без buildingMaterialId, ModifySlabs v1.4.0 с ним. PR149 material-only verifier требует floorIndex=0 и отсутствие dependents; PR74 Create→Modify использует иной scoped contract и может работать для второго этажа, но это не подтверждено локально.
2. PR149 Beam verifier: один Basic axis-aligned Beam floor0, не готовый универсальный floor1. PR126 batch не совместим автоматически с single verifier. PR162 group commands отсутствуют в Tapir snapshot, нужен отдельный installed provider.
3. Tapir tag1.5.9 LICENSE MIT; DevKit29 LICENSE Graphisoft EULA. SDK30 и upstream PR785 не являются доказательством SDK29 build5101/локального 1.5.10. **Вердикт А: SOURCE_ONLY.**

## Контрааудит Б — монтажный граф, дублирование и безопасность

1. Единственный контур: intent → PR74 → BIM Graph → DynamicCommands → SceneWriter/SQLite. PR126 — оптимизация только после базовой квалификации, PR162 — группы только при доказанном провайдере. Второй writer/Router/Clone запрещён.
2. PR131 требует существующий native host GUID, библиотечный settingsHash, этаж и полную геометрию. Для новых стен порядок: create walls → readback GUID → hosted openings. Ошибки не маскировать.
3. PR175 lock cooperative и не защищает от сторонних GUI writers. Get3DBoundingBoxes ≠ BREP; GetModelDumpV1 требует отдельной фактической регистрации. **Вердикт Б: G0 BLOCKED, G1/G2 SOURCE, G3–G5 NOT_RUN.**

## Координатору №3 — на утверждение

1. G0 exact installed manifest; 2. G1 новый intent/preflight без записи; 3. G2 slab второго этажа через существующий PR74; 4. G2 hosted openings через PR131; 5. G4 отдельная BUILD-01 reopen-квитанция; 6. Beam как optional, batch/group после базового PASS.

**Вопросы №1:** найден ли релизованный AC29 APX с новым CreateSlabs материалом; есть ли штатный read-only способ доказать ModelDumpV1 provider и BREP; существуют ли готовые source-qualified Beam floor1 и GUI reopen receipt без Hotlink-специфики.

**Публикационная приёмка:** этот файл SOURCE, не BUILD-01 ACCEPTED; основной индекс публиковать только после всех приложений и точного readback.
