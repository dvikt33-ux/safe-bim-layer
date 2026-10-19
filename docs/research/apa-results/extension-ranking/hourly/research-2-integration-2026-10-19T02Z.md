# APA AC29 — исследователь №2, 19.10.2026 02:00 UTC

**Исследование:** 30 SOURCE-проверок исходников, два собственных контрааудита. Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED не проводились. MODEL_MODE_NOT_VERIFIABLE. Ускорение не измерялось.

**Контекст:** `NEXT_RESEARCH_PRIORITIES.md` SHA `2cb49edc`, матрица `9cb5e6f2` (61 кандидат), свежий №1 02Z (7 карточек), последний найденный №3 20Z 18.10. Канонический `PROJECT_PLAN.json` revision 182 SHA `c2ab2f9d` прочитан без изменений. PR165/167/168/170/171/173/154/159/160/162 сопоставлены.

**Открытие 1:** официальный Python API **AC29** уже предоставляет `GetAttributesByType`, `GetAttributesIndices`, `GetBuildingMaterialAttributes`, `GetAttributeFolderStructure`. Инвентаризация атрибутов не требует нового APX. `GetClassificationsOfElements` — только элементы; классификации и свойства именно атрибутов доступны в SDK29 C++, но готовый JSON binding в проверенных путях **NOT_FOUND**. [AC29 Python](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html) · [SDK29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html).

**Открытие 2:** готовый `bsdd.Client` присутствует в `IfcOpenShell` 0.8.5 (`src/bsdd/bsdd.py`, LGPL-3+). `get_dictionary` имеет строковый default `"False"`, фактически truthy; при стандартном вызове передаётся `IncludeTestDictionaries=true`. Нужна минимальная проверка параметров и ответов поверх готового клиента, не новый движок. [Код](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/bsdd/bsdd.py#L688).

**Открытие 3:** `util.sequence.get_tasks_for_product(product,schedule)` разыменовывает `get_task_work_schedule(task).id()` без None guard. `util.cost.calculate_applied_value` подавляет деление на ноль. Для 4D/5D — fail-closed QA, не нормативный расчёт. [4D](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py#L364) · [5D](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L63).

## Решения на рассмотрение №3

| Готовое средство → APA reuse | Польза | Вердикт / сложность |
|---|---:|---|
| AC29 Python Attribute inventory → existing Router | 96 | REUSE / БЫСТРО |
| AC29 Python + Tapir Publisher preflight | 95 | REUSE / БЫСТРО |
| IfcOpenShell classification inheritance → PR165 | 94 | ADAPTER / АДАПТАЦИЯ |
| bsdd.Client → APA IFC classifications | 91 | ADAPTER / АДАПТАЦИЯ |
| IfcOpenShell util.cost → PR167 B2 | 88 | ADAPTER / АДАПТАЦИЯ |
| IfcOpenShell util.sequence → PR167 B2 | 85 | ADAPTER / АДАПТАЦИЯ |
| SDK29 attribute classifications | 84 | DEFER / ДОЛГО; JSON binding NOT_FOUND |
| SDK29 attribute property values | 82 | DEFER / ДОЛГО; JSON binding NOT_FOUND |

**Графы:** APA→официальный JSON/Python→JSON; APA→B2 IFC sidecar→pinned IfcOpenShell util→JSON; APA→read-only sidecar→bsdd.Client→публичный bSDD REST→cached JSON. Максимум три внешних звена, без нового SceneWriter. Выбор готовых инструментов вместо новых APX/MCP/IFC-движков.

**Ворота:** SOURCE подтверждён. OFFLINE нужны IFC2X3/IFC4 negative fixtures, bSDD mock, Publisher empty/duplicates. BUILD Windows Python3.11/3.12 exact lock; INSTALLED runtime SHA; LIVE отдельное разрешение и scratch PLN; ACCEPTED независимый readback. AC29 build5101, локальный Tapir1.5.10, 8GB VRAM/48GB RAM не испытывались.

**Полные контракты:** [01–15](research-2-integration-2026-10-19T02Z-checks-A.md) · [16–30](research-2-integration-2026-10-19T02Z-checks-B.md) · [аудит А](research-2-integration-2026-10-19T02Z-audit-A.md) · [аудит Б](research-2-integration-2026-10-19T02Z-audit-B.md). Вопросы №1 и условия ГОТОВО — в аудите Б. Очередь №3, main, PLN/APX, код и план182 не менялись.
