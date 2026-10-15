# APA-P00.A02.S03 — техническая дедупликация 71 архивного source: Roof, Composite, Project Context против текущего APA

**Task:** `APA-P00.A02.S03` / `legacy-evidence-dedup`.  
**Run:** `APA-RUN-20261011-190658Z-roof-comp-context-map`. **Claim:** `APA-RUN-20261011T185929Z-roof-comp-context`.  
**Source phase:** `SOURCE`, no live Archicad/API calls. **Task result:** `PARTIAL` (exact three-topic integration map; remaining semantic corpus audit open).  
**Дата:** 2026-10-11; repo `dvikt33-ux/safe-bim-layer`; canonical branch `research/apa-verified-results-hub-20261010`.

## 1. Зачем этот проход отличается от уже опубликованного

71 исторический `research/archicad29-tapir159/` исходный Markdown/JSON уже были **физически архивированы побайтово** под `docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/` с 71/71 одинаковыми Git SHA и размерами, см. [предыдущий byte-exact V2 report](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-092155Z-source71-byte-archive/REPORT.md) и [manifest](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/ARCHIVE_MANIFEST_20261011.json). Также проведена первичная проверка 13 архивных документов. Поэтому перенос не повторяется, 71 файлов не копируем заново, исходную ветку не модифицируем.

Цель **этого** прохода — проверка конкретных контрактных пробелов и сохранение неизбыточного `source → current code → S-ID → next acceptance gate` с pinned SHA. Исторический baseline — **Tapir 1.5.9**; сравнительная retained схема — **Tapir 1.5.10**, но это не readback загруженного APX.

**Машинный результат:** [ARCHIVE_ROOF_COMPOSITE_CONTEXT_GAPS_20261011.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/ARCHIVE_ROOF_COMPOSITE_CONTEXT_GAPS_20261011.json); 3 объекта `topics`, 12 исходников с точными Git blob SHA, сохранён в GitHub и повторно прочитан.

## 2. Технический разбор и решения

### A. Односоставная двускатная крыша (один Roof GUID)

Архивное [исследование 20 проходов](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/03_archicad_api_contracts/SINGLE_ELEMENT_GABLE_ROOF_RESEARCH_PASSES_01_20.md) и [финальный addendum](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/09_final_audit/GABLE_ROOF_FINAL_AUDIT_ADDENDUM.md) предлагают `API_PolyRoofID` с `API_PivotPolyEdgeData`, позволяющим различать `Gable` и `Sloped` у конкретного ребра. Это исследование по Graphisoft C++ API и старому Tapir 1.5.9, **не рабочий нынешний patch**.

Проверен реальный retained [JSON export Tapir 1.5.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-authored-spatial-clearance-20261011/schemas/tapir-live-1.5.10/tapir-scene-live.json), blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`:

- `CreateRoofs`, schema command version **1.4.0**, допускает `polygonCoordinates`, `pivotLine`, `angle`, `levels`, `structureType`, `compositeId` и другие базовые поля; **нет** `pivotEdgeSettings`, `pivotPolyEdges` или typed edge-type input;
- `common_schemas.RoofDetails` уже содержит `roofClass`, `levels`, `pivotPolygonOutline`, `compositeId`, но **нет** per-edge segment-type readback — для Gable proof этого недостаточно;
- текущий [highlevel builder](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-highlevel-whole-model-20261011/scripts/archicad_building_shell.py) явно ограничивает `WRITES` до `CreateWalls/CreateSlabs/CreateDoors/CreateWindows`. **Roof не включён**.

**Решение о дедупликации:** не писать второй универсальный Roof-исполнитель и не объявлять две отдельные Single-plane Roof стандартной заменой одним Multi-plane Gable. Использовать имеющийся writer/graph и предложить узкое typed per-edge расширение со встречным native readback. Source-контрактный пробел **VERIFIED** в *сохранённой схеме*, **загруженный APX и LIVE Gable NOT_VERIFIED**.

**Привязка:** `APA-P10.A01.S03` (Roof API/C++), `APA-P10.A02.S01` (Tapir 1.5.10 version/ABI), `APA-P70.A03.S02` (reuse native writer, только после отдельного согласования). **Следующий измеримый шаг:** source+schema сравнение loaded Tapir 1.5.10 и offline payload/memo+edge readback tests; перед любым реальным CreateRoof отдельное явное разрешение, exactly one GUID и independently verified roof face/edge evidence.

### B. Composite — готовые attribute-команды, но нет доказанного end-to-end write

Архивное [исследование 18 проходов](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/03_archicad_api_contracts/COMPOSITE_STRUCTURES_RESEARCH_PASSES_01_18.md) и [Addendum Roof/Composite](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/09_final_audit/ROOF_PARAPET_COMPOSITE_FINAL_AUDIT_ADDENDUM.md) рекомендуют использовать `GetBuildingMaterials → CreateComposites/GetComposites → native Wall/Roof(compositeId)`, с предразрешением GUID материалов, lineType, ordinal skins, толщин и fingerprints. Исследование правильно отмечает глобальное влияние изменения атрибута Composite на другие элементы проекта.

Сохранённый 1.5.10 contract содержит:
- `CreateComposites` version **1.0.2**, `GetComposites` **1.5.4**, `GetBuildingMaterials` **1.5.4**, и `CreateRoofs` с `compositeId`. Это **существующие команды**, а не предложение написать новый Tapir addon;
- `CreateComposites` требует `name/skins/separators`, но **не требует `useWith` по schema.required**, несмотря на необходимость набора применяемых классов. Следовательно проектный валидатор должен **сам требовать** `useWith` и N+1 separator, точный GUID BuildingMaterial/LineType, fail-closed unresolved dependency, `overwriteExisting=false`, readback всего атрибута по ID;
- нынешняя [стратегия семейств Composite](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-highlevel-whole-model-20261011/docs/archicad-template/COMPOSITE_FAMILY_STRATEGY_v0.1.md) и [YAML blueprint](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-highlevel-whole-model-20261011/docs/archicad-template/composite-family-registry-v0.1.yaml) уже задают source-driven семьи и запрещают универсальную толщину по рекламному названию;
- действующий [highlevel builder](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-highlevel-whole-model-20261011/scripts/archicad_building_shell.py) маркирует Walls как Basic до сертификации CSE; [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-authored-spatial-clearance-20261011/scripts/archicad_scene_run.py) разрешает **один exact BuildingMaterial для Basic slab**, и этот read-only material preflight не является Composite authoring gate.

**Решение о дедупликации:** сохранить исторический spec про жёсткую привязку GUID и fingerprint, но **не** создавать ещё один attribute manager; реализовать тонкий resolver/receipt на уже существующем JSON-контракте после отдельного task gate. `CREATE/OVERWRITE` не запускать; **NO LIVE PROOF** доступности и точности установки Composite в конкретном PLN.

**Привязка:** `APA-P10.A02.S01`, `APA-P70.A04.S02`, `APA-P70.A03.S02`. **Ближайший тест:** чисто read-only GET BuildingMaterials/Composites в точном открытом disposable PLN с GUID/useWith/skins/separators/total thickness, повторный project identity stamp. Затем отдельный offline plan guard без writes; лишь после approval — один controlled Composite attribute write (влияние на проект отдельно проверено).

### C. Project Context Bridge — не создавать второй watcher

Архивный [проектный мост после 160 проходов](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/09_final_audit/FINAL_PROJECT_CONTEXT_BRIDGE_AUDIT_AFTER_160.md) описывает атомарный по-проектный snapshot, cheap `project/element modiStamp`, индекс GUID, event queue и cloud mirror. Он содержит осмысленные требования к coherence/staleness, но не доказывает реализацию такого native моста.

Современный [archicad_change_watch.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-authored-spatial-clearance-20261011/scripts/archicad_change_watch.py) **уже существует** и делает read-only polling `GetProjectInfo`, `GetStories`, `GetAllElements`, `GetDetailsOfElements`, `Get3DBoundingBoxes` с SHA отпечатками; при смене проекта останавливается. [archicad_watch_context.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-authored-spatial-clearance-20261011/scripts/archicad_watch_context.py) превращает локальные файлы watcher в компактный контекст. [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fapa-authored-spatial-clearance-20261011/scripts/archicad_scene_run.py) проверяет exact project path/name, native story index/floorId/level, `GetAddOnVersion`, 3D conflict envelope, frozen sourcePlanHash, журнал mutation до write и exact GUID readback. Повторно писать этот контур не нужно.

**Конкретный оставшийся пробел:** в сохранённом 1.5.10 JSON export **нет** `GetSafeBIMProjectStamp` / `GetSafeBIMElementStateIndex`; watcher переснимает факты polling, а не подтверждённый native cheap `modiStamp` с атомарной версионированной границей. Из проверенных исходников не следует существование приватного coherent project-state mirror для обычного ChatGPT. **PARTIALLY IMPLEMENTED** в текущем источнике; **MULTI-INSTANCE/FULL EPOCH/PRIVATE MIRROR NOT_VERIFIED**.

**Решение о дедупликации:** сохранить old source как требования к coherence, reuse нынешний watcher+SceneWriter; не делать второго постоянно работающего watcher или автопереключателя PLN. **Привязка:** `APA-P70.A03.S03`, `APA-P70.A01.S02`, `APA-P10.A02.S01`. **Следующий тест:** offline adversarial stale-context scenarios (смена даже одного атрибута/story внутри неизменившегося пути, project-switch, неточный GUID hash, partial snapshot), отдельный live read-only native APX capability probe; без физического write.

## 3. Что именно принято и что запрещено объявлять

| Проверяемый объект | Состояние | Доказательство |
| --- | --- | --- |
| Архив 71 файлов | **BYTE_EXACT_VERIFIED** ранее, исходные Git SHA сохранены | [Archive manifest](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/ARCHIVE_MANIFEST_20261011.json) |
| Проанализированы конкретные Roof/Composite/Context контракты | **SOURCE_READ_VERIFIED** (12 pinned sources, exact current schema code) | [Matrix](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/ARCHIVE_ROOF_COMPOSITE_CONTEXT_GAPS_20261011.json) |
| Отсутствует ввод per-edge Gable в retained Tapir 1.5.10 JSON | **SOURCE_CONTRACT_GAP_CONFIRMED** | CreateRoofs/RoofDetails props отсутствуют |
| Get/CreateComposites как API surface | **SOURCE_SCHEMA_PRESENT**, current native runtime unverified | `CreateComposites/GetComposites` exported schemas |
| Existing watcher and SceneWriter | **SOURCE_CODE_PRESENT**, current operation not executed | current checked Python source |
| Пользовательский Archicad 29 LIVE Roof/Composite/stamp | **NOT_VERIFIED** | Neither native endpoint nor binary tested in this run |
| Полная семантическая дедупликация 71 источника | **PARTIAL** | 13 previously reviewed and 5 key additional archives; many historic claims remain unvalidated |

## 4. Задачи и дальнейший принцип

**Не создаю новый work_key без нужды.** Все три темы покрываются уже зарегистрированными S-ID. Этот проход сохраняет явные `source → reused code → gap → validation` связи; конечная публикационная квитанция V2 не переводит `APA-P00.A02.S03` в DONE, пока архивные заявления и оставшиеся уникальные результаты не сопоставлены полностью.

**Приоритет на следующий проход:** только read-only / offline проверка roof input+readback по реальному 1.5.10 addon source (не широкая реализация), затем отдельный typed Composite resolver, затем независимый тест project-context epoch на неизменившемся пути. Выбор зависит от действующего контроллера и уже имеющихся PR; нужно сначала прочитать актуальные задачи, не начинать конкурентную работу.

## 5. Безопасность и источники

12 pinned Git blob SHA доступны в матрице. Удаления веток, merge/force-push, автоматическое изменение проекта, открытие другого файла и локальный runtime отсутствуют. Никакой Deep Research, платный агент или имитация LIVE PASS. Исторические данные Tapir 1.5.9 не считаются текущей нативной аттестацией Tapir 1.5.10.
