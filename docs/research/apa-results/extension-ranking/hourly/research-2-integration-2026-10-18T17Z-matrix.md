# APA AC29 №2 / 17Z — матрица 10 путей подключения

Оценки 0–100 — экспертная инженерная полезность, НЕ замер ускорения. SOURCE only. В каждой цепочке не более трёх внешних звеньев, оригинальные APA Router/BIM Graph/SceneWriter остаются единственными исполнителями.

| Решение и цепочка | Балл | Версия/лицензия | APA reuse / выбор | Сложность, риск, ГОТОВО |
|---|---:|---|---|---|
| PR165 IFC 8 readers: APA Router → V1 isolated Python → IfcOpenShell → JSON | 92 | PR165 draft; pin 0.8.5 LGPL-3+ | existing IFC reader/BIM Graph; ADAPTER | БЫСТРО; export≠PLN, GUID/relations/schema fixtures, receipt |
| PR165 DXF 4 readers: Router → V1 Python → ezdxf → JSON | 86 | ezdxf 1.4.5 MIT | existing PDF/DXF provider; ADAPTER | БЫСТРО; MINSERT/OCS/units; 4 fixtures, raw-only |
| IfcDiff: existing APA V1 CLI → IfcDiff → diff.json | 91 | pin 0.8.5 LGPL-3+ | existing external JSON runner; REUSE | БЫСТРО; geometry/attributes absent with -r; 2 passes + GUID |
| Publisher: existing Bridge → local Tapir → AC29 Publisher → files | 91 | Tapir 1.5.9 MIT, local 1.5.10 unknown | original Router; ADAPTER | АДАПТАЦИЯ; empty selection fail-open; exact GUID whitelist + output SHA |
| IfcPatch: exported IFC copy → IfcPatch -o → patched IFC | 79 | upstream commit b139 LGPL-3+ | existing IFC QA; ADAPTER | АДАПТАЦИЯ; -o required; immutable input, host/ports/GUID postcheck |
| Hotlink: existing Bridge → Tapir nodes/instances → AC29 .mod/.pln | 82 | Tapir 1.5.9 MIT, runtime unknown | original SceneWriter scopes; ADAPTER | АДАПТАЦИЯ; source hash, node/instance/child GUID, rollback |
| BCF: existing IfcTester IDS → BCF2 ZIP → viewer | 75 | upstream b139 LGPL-3+, package license review | existing IDSValidate; ADAPTER | АДАПТАЦИЯ; issue #7152, ZIP viewpoint filenames and selected GlobalId |
| STEP-to-JSON: isolated Node API → id/name/contains JSON → APA evidence | 73 | 4.0.0 MIT, npm dependencies | existing file evidence; ADAPTER | АДАПТАЦИЯ; no transforms, unsafe CLI output; safe wrapper + assembly fixture |
| STEPhen: isolated Python CLI → CadQuery STEP → BOM/positions CSV → APA evidence | 66 | 0.0.1 Apache-2.0, CadQuery | existing evidence; DEFER | ДОЛГО; Windows wheels, .step only, units; known transform fixture |
| PR162 group strategy: BIM Graph → DynamicCommands → SceneWriter → CloneNativeGroupV1 | 95 | APA draft; Graphisoft proprietary, Tapir runtime unknown | REUSE native writer | АДАПТАЦИЯ; PR159 scratch LIVE only; scoped end-to-end readback |

**Сравнение альтернатив.** IFC QA: существующий V1/PR165 против нового IFC reader → выбрать V1/PR165, не создавать движок. STEP: STEP-to-JSON быстро извлекает только дерево, STEPhen даёт координаты/вращения, но требует CadQuery; STEPcode BSD-3 с CMake ещё дороже — defer. Publisher: Tapir preflight предпочтительнее нового SDK29 Add-On; если локальной команды нет, NOT_FOUND готовый безопасный bridge. BCF: локальный ZIP предпочтительнее сервера BCF API. Group: PR162 SceneWriter предпочтительнее прямого CloneNativeGroupV1.

**Координатору №3 на утверждение:** PR165 IFC QA 92, IfcDiff 91, Publisher 91, PR165 DXF QA 86, Hotlink 82, BCF 75, STEP-to-JSON 73. STEPhen 66 — после проверки CadQuery Windows/units. MEP/SAF DEFER/BLOCKED.

**Вопросы исследователю №1:** (1) локальный каталог Tapir 1.5.10 Publish/GetHotlinks? (2) STEP с placements без CadQuery? (3) BCF #7152 исправлен в каком теге? (4) native GUID→IFC GlobalId полная host/port карта? (5) PDF физические opening anchors? (6) SDK29 Multiply API count? (7) SAF 6DOF/LCS/load готовый адаптер?

**Готово для следующей стадии** означает OFFLINE fixtures + independent readback, не просто наличие SOURCE. Никаких установок или изменений модели в этом цикле.
