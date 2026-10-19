# APA AC29 — исследователь №2 — 19.10.2026 05:00 UTC

**Итог:** 27 содержательных SOURCE-проходов (P01–P27), два независимых контрааудита А/Б; 9 путей подключения к существующему APA. Не выполнялись OFFLINE, BUILD, INSTALLED, LIVE, ACCEPTED для новых кандидатов. MODEL_MODE_NOT_VERIFIABLE.

## Исходная база, прочитанная ПЕРВОЙ
- `NEXT_RESEARCH_PRIORITIES.md` blob `2cb49edc410632c65503d8f17e93c58bc2d971d1`; последняя подтверждённая очередь №3 **18.10 20Z**, более новой публикации №3 в hourly не найдено.
- `priority_matrix_20261018.json` blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`, **61 кандидат**; `candidates.json` из того же каталога прочитан; новых карточек №1 **19.10 05Z** семь (C1–C7), включая уточнение IFC4D.
- `PROJECT_PLAN.json` branch `research/apa-verified-results-hub-20261010`, path `docs/research/apa-results/control/PROJECT_PLAN.json`, blob `c2ab2f9d606db1412c4031076103c267fc463f83`, revision **182**, только чтение.
- PR165/167/169/173/175, snapshot Tapir `schemas/tapir-live-1.5.10/tapir-scene-live.json` blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`; snapshot **не является новым runtime probe**. Последний отчёт №2 04Z прочитан.

## Главное новое инженерное решение
В snapshot Tapir 1.5.10 **нет** `GetPropertyDefinitionAvailability`, `GetClassificationItemAvailability`, `GetCompositeAttributes`, `GetPublisherSetNames`. Все четыре функции **есть в официальном Graphisoft API 29.3000**. Поэтому оптимальная цепочка **APA Router → уже имеющийся Graphisoft JSON transport → официальный AC29 метод → typed read-only JSON → BIM Graph/QA**, а не сборка нового APX или выдуманный Tapir command. Отсутствие относится к конкретному source-snapshot, не доказывает невозможность других сборок. Источники: https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html, https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json, https://pypi.org/project/archicad/29.3000/.

Отдельно PR165 `_ifc_ports` считает `IfcRelConnectsPorts`, но не строит owner/peer/flow. Готовый `ifcopenshell.util.system` 0.8.5 предоставляет `get_port_element`, `get_connected_port`, `get_ports`. Цепочка **APA → существующий V2 read-only provider → pinned IfcOpenShell util.system → BIM Graph**, без нового IFC-движка. Источники: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L170-L191 и https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/system/index.html.

## Матрица девяти конкретных решений
| Решение | Готовый инструмент / версия | Контракт | Повторно используем APA | Лицензия/риск | Вердикт | Польза* | Сложность | ГОТОВО |
|---|---|---|---|---|---|---:|---|---|
| Property↔Classification | Graphisoft Python 29.3000 → штатный JSON | GetPropertyDefinitionAvailability / GetClassificationItemAvailability | APA Router/official JSON | Apache-2.0; runtime AC29 не проверен | ADAPTER | 96 | БЫСТРО | двусторонняя матрица, errors≠empty |
| Typed Property SI/status | Graphisoft 29.3000 + Tapir snapshot | elements,properties,onlySupportedTypes; normal/notAvailable/notEvaluated | existing property reads/Router | Apache-2.0+Tapir MIT; crash/cardinality | REUSE+ADAPTER | 98 | БЫСТРО | 4 статуса, SI, GUID cardinality |
| Composite skins | Graphisoft 29.3000 | GetCompositeAttributes, CompositeSkin(materialId,thickness,isCore,isFinish) | official JSON/Router | Apache-2.0; nominal≠BREP | REUSE | 94 | БЫСТРО | skin order, thickness, errors |
| Attribute GUID drift | Graphisoft 29.3000 / Tapir snapshot | GetAttributesByType, GetAttributesIndices | APA inventory/Router | Apache-2.0+MIT; index unstable | ADAPTER | 93 | БЫСТРО | 2 types, stable GUID, index diagnostic |
| Classification provenance | Graphisoft 29.3000 + V2 PR165 | ClassificationSystem(source,version,date); IFC relation count | official JSON + V2 IFC read | Apache-2.0+LGPL; SP currency not proven | ADAPTER | 89 | БЫСТРО | metadata↔2 IFC GUID, no normative claim |
| IFC 4D task links | IfcOpenShell 0.8.5 util.sequence | get_tasks_for_product → 2 lists | V1 vendor env/Router/JSON | LGPL-3.0-or-later; mutation prohibited | ADAPTER | 87 | АДАПТАЦИЯ | 3 tasks, roles, no file writes |
| Publisher artifact gate | Graphisoft 29.3000 + Tapir snapshot | GetPublisherSetNames; PublishPublisherSet required publisherSetName | Router/Bridge existing document scope | Apache-2.0+MIT; no artifact receipt | ADAPTER | 94 | АДАПТАЦИЯ | unique path + PDF signature + SHA readback |
| MEP port owner/peer | IfcOpenShell 0.8.5 util.system | get_port_element/get_connected_port/get_ports | PR165 V2/Router/BIM Graph | LGPL-3.0-or-later; export may omit native link | REUSE+ADAPTER | 96 | БЫСТРО | 3 fixtures, owner/peer/flow statuses |
| Hotlink provenance | PR173 + PR175, existing native Router | 69→119 GUID, 2 roots, one batch call, saved/reopen SHA | BIM Graph/SceneWriter/native verifier | Existing APA; race & incomplete independent acceptance | REUSE | 95 | БЫСТРО | roots/owned/BREP/source SHA; no replay |

*Польза 0–100 — экспертная оценка, НЕ ускорение и НЕ benchmark. Все новые решения SOURCE, а не ACCEPTED.

## Архитектурные альтернативы (проверены)
1. **Property availability:** Tapir snapshot direct — NOT_FOUND; официальный Graphisoft 29.3000 — готовый контракт. Выбран официальный API, 0 новых внешних звеньев. Не смешивать PropertyId с ClassificationItemId.
2. **IFC4D:** `util.sequence.get_tasks_for_product` — read-only; `api.sequence.recalculate_schedule/cascade_schedule/create_baseline` — изменяют IFC. Выбран только util.sequence; для остальных DEFER.
3. **Publisher:** `GetPublisherSetNames` — безопасный preflight, но только имена; `PublishPublisherSet` — документная операция с внешним выводом. Выбран read-only preflight + отдельный будущий SHA/readback gate; сейчас никакого вызова publish.
4. **MEP:** сырые счётчики PR165 не подтверждают владельцев и flow; готовые функции util.system позволяют добавить owner/peer без второго графового ядра. Выбран reuse V2 + узкий adapter.
5. **Hotlink:** новая реализация writer отвергнута: PR173 уже доказал batch LIVE на scratch; PR175 исследует позднюю файловую запись. Выбран read-only аудит существующих receipt/SceneWriter/BREP, без повтора команды.

## Монтаж и защита
- Graphisoft `archicad==29.3000`: официальный wheel `py3-none-any`, Apache Software License, опубликован 01.10.2025; не смешивать с 30.3000. JSON transport работает через HTTP; на AC29 build5101 живую доступность новых методов в этом цикле не проверяли. https://pypi.org/project/archicad/29.3000/.
- Tapir: upstream MIT (https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE); локальный snapshot помечен 1.5.10, APX SHA в PR169, но актуальная регистрация в запущенном Archicad НЕ ПРОВЕРЕНА. Установка запрещена.
- IfcOpenShell 0.8.5: upstream LGPL-3.0-or-later; уже существующий V1 vendor runtime/PR165 synthetic INSTALLED 12/12, не доказательство нового LIVE или совместимости каждого 4D fixture. https://github.com/IfcOpenShell/IfcOpenShell.
- Windows 11, 8 GB VRAM/48 GB RAM: девять путей не требуют GPU; пиковая RAM больших IFC не измерена, существующий V2 ограничивает вход 4 GiB и отчёт 200 MiB. Никаких гарантий производительности.
- Сохранять идентичность GUID + источник (PLN/IFC) + тип/единицы/status; пустой список, `notAvailable`, `notEvaluated`, `Error`, `NOT_VERIFIED` — разные состояния. Исходные файлы не изменять. Для потенциального вывода только новый путь, SHA до/после, атомарный receipt, rollback удалением лишь нового sidecar/выходного артефакта.

## Границы приёмки
**SOURCE:** версии, upstream signatures, лицензии и локальные контракты документированы (этот цикл). **OFFLINE:** будущие synthetic/negative fixtures и точные JSON cardinality/units. **BUILD:** проверка сборки только если понадобится SDK29, иначе `NOT_APPLICABLE`. **INSTALLED:** подтверждение существующей локальной версии, hash/probe, без автоматической регистрации. **LIVE:** исключительно отдельно разрешённая read-only проверка на копии/экспорте; никаких операций в этом цикле. **ACCEPTED:** независимый readback SHA, полный coverage, явная санкция координатора; пока **NO**.

## Передача №1
Найти: (1) реальный AC29 build5101 пример bidirectional property/classification; (2) source пример Typed Property status handling с unsupported type; (3) composite skin material error fixture; (4) stable GUID/index drift fixture; (5) 0.8.5 IFC4D assigned/reference fixture; (6) MEP orphan/peer/flow fixture; (7) официальный пример Publisher artifact SHA readback, а при отсутствии — NOT_FOUND.

## Координатору №3 на утверждение следующего этапа
Приоритеты: **Typed Property fail-closed (98)**, **Property↔Classification (96)**, **MEP port owner/peer (96)**, **Hotlink provenance readback (95)**, **Composite skins (94)**, **Publisher artifact gate (94)**, **Attribute GUID drift (93)**. Это исследовательская передача, не разрешение установки.

## Доказательства
- [P01–P09](research-2-integration-2026-10-19T05Z-checks-A.md) · [P10–P18](research-2-integration-2026-10-19T05Z-checks-B.md) · [P19–P27](research-2-integration-2026-10-19T05Z-checks-C.md)
- [Контрааудит А](research-2-integration-2026-10-19T05Z-audit-A.md) · [Контрааудит Б](research-2-integration-2026-10-19T05Z-audit-B.md)

Никаких изменений main/PLN/APX/рабочего кода/PROJECT_PLAN rev182/NEXT_RESEARCH_PRIORITIES. Ускорение не заявлено. Браузер GPT и GitHub использованы; Opera не использовалась.
