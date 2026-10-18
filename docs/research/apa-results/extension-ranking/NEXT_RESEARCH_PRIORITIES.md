# APA — текущая очередь исследований, 18 октября 2026, 14Z

**Штаб:** [аудит 14Z](hourly/audit-20261018T14Z.md), blob `35581c923b2c7ea10f49c0f9f4b51dad6adc9823`, commit `afe9cec33a9c07a83eebdbca4e986c410fb15b03`. Прочитаны: [№1 14Z](hourly/research-1-20261018T14Z.md) blob `b82c8d683fe24d321fe75c1101aa4287c647872a`; [№2 12Z](hourly/research-2-2026-10-18T12Z.md) blob `09c86e212b6caf96fc9066b1d989a1028574c7aa`. Нового `research-2-integration-*` пока нет. №2 12Z — прежнее тематическое исследование, не доказательство исполнения новой роли.

**Канон:** PROJECT_PLAN.json revision 182 — только чтение; A11.S03 PARTIAL, A11.S08/A11.S10 BLOCKED, A07.S03 READY. Приоритет 61 кандидата из [матрицы](priority_matrix_20261018.json) не означает LIVE или разрешение установки. Не трогать main, код, PLN/APX, план №182.

## Исследователь №1 — искать ГОТОВЫЕ решения

| ID | Приоритет и конкретная задача | Первоисточник для старта | ГОТОВО |
|---|---|---|---|
| F01 | П0: независимый LIVE receipt групп PR159/162; тексты PR противоречат | [PR159](https://github.com/dvikt33-ux/safe-bim-layer/pull/159), [PR162](https://github.com/dvikt33-ux/safe-bim-layer/pull/162) | точный SHA/GUID/PLN/readback или NOT_FOUND |
| F02 | П0: штатный API29 линейного/радиального/сеточного Multiply групп | [AC29 Multiply](https://help.graphisoft.com/AC/29/INT/_AC29_Help/030_Interaction/030_Interaction-96.htm), [DevKit29](https://github.com/GRAPHISOFT/archicad-api-devkit/releases/tag/29.3100) | API29 signature или перечень проверенных отрицательных путей |
| F03 | П0: PDF→BIM physical anchors окон/дверей, не текстовые центры | [PR154](https://github.com/dvikt33-ux/safe-bim-layer/pull/154), [PR160](https://github.com/dvikt33-ux/safe-bim-layer/pull/160), [PDF provenance](hourly/research-1-20261018T12Z-audit-A.md) | 3 точки, масштаб/невязка, разделение АП Амур и КР Московская область |
| F04 | П1: независимый IFC QA сверх Native Model Dump | [IfcQuery](https://docs.ifcopenshell.org/ifcquery.html), [IfcTester](https://docs.ifcopenshell.org/ifctester.html) | ≥3 новых проверки с source/version/license и anti-duplication |
| F05 | П1: готовые локальные BCF XML 2.1/3.0 инструменты | [BCF](https://docs.ifcopenshell.org/bcf.html) | готовый GUID/viewpoint sample, версия и лицензия |
| F06 | П1: готовый SDK29 MEP per-segment/transition wrapper | [Tapir1.7.1 MEP](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.1/archicad-addon/Sources/MEPCommands.cpp), DevKit29 | tagged code+exact contract или NOT_FOUND |
| F07 | П1: готовый SAF→PyNite коннектор | [SAF SDK](https://www.saf.guide/en/stable/SDK/StructuralAnalysisFormat.html), [PyNite](https://github.com/JWock82/Pynite) | готовая цепочка/6DOF/LCS/loads или NOT_FOUND |
| F08 | П2: Qto/CRS готовые валидаторы | [IfcPatch](https://docs.ifcopenshell.org/ifcpatch.html) | template/units/3 CRS anchors, не применять без дефекта |

Выход: `hourly/research-1-<UTC-час>.md`; 20–30 фактических проходов, два собственных аудита. Если готовый способ не найден — независимые альтернативы и честный NOT_FOUND.

## Исследователь №2 — искать СПОСОБЫ ПОДКЛЮЧЕНИЯ

| ID | Приоритет и интеграционная цепочка | Первоисточник для старта | ГОТОВО |
|---|---|---|---|
| I01 | П0: APA IFC exporter→ExtractElements через existing IfcOpenShell или CLI | [ExtractElements](https://docs.ifcopenshell.org/autoapi/ifcpatch/recipes/ExtractElements/index.html) | two-path comparison, GlobalId/relations, output copy |
| I02 | П0: SplitByBuildingStorey vs native Archicad per-storey export | [SplitByBuildingStorey](https://docs.ifcopenshell.org/autoapi/ifcpatch/recipes/SplitByBuildingStorey/index.html) | spanning wall/stair GUID coverage |
| I03 | П0: Publisher Tapir vs SDK29; безопасная публикация | [Tapir Navigator1.7.1](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.1/archicad-addon/Sources/NavigatorCommands.cpp) | unique set GUID, непустой whitelist, isolated output, manifest, без запуска |
| I04 | П0: Hotlink/groups reuse CloneNativeGroupV1 | [Tapir Project1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp) | node/instance/child GUID, local 1.5.10 discovery, no second writer |
| I05 | П1: offline BCF→existing QA JSON | [BCF](https://docs.ifcopenshell.org/bcf.html) | viewpoint camera/GlobalId roundtrip, license |
| I06 | П1: IfcQuery/iterator vs Native Model Dump | [IfcQuery](https://docs.ifcopenshell.org/ifcquery.html), [iterator](https://docs.ifcopenshell.org/ifcopenshell/geometry_iterator.html) | 3 independent checks or REJECT |
| I07 | П1: SDK29 per-segment Place maps/transition→existing APA Router | [Tapir MEP1.7.1](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.1/archicad-addon/Sources/MEPCommands.cpp) | referenceId≠diameter, physical reciprocal ports, rollback; A11.S10 BLOCKED |
| I08 | П1: SAF SDK1.7.3 vs direct XLSX→PyNite | [SAF SDK](https://www.saf.guide/en/stable/SDK/StructuralAnalysisFormat.html) | 2 пути, license, 6DOF/LCS/loads loss table или NOT_FOUND |

Выход: `hourly/research-2-integration-<UTC-час>.md`. Для каждой функции: existing APA → готовый интерфейс → готовый адаптер → инструмент → readback; максимум 3 внешних звена. При отсутствии связующего ищи готовый wrapper/bridge/middleware/SDK sample, затем честно NOT_FOUND и минимальный gap. Только исследование, никаких установок.

## Аудит и архив

Аудитор проверяет реальную первичность, API29, версии Tapir, лицензии, отсутствие дубликатов и SOURCE/OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED. Не утверждать 100× без benchmark. Полные 25 проверок, два контрааудита и рейтинги — [аудит 14Z](hourly/audit-20261018T14Z.md). История предыдущих очередей сохранена в Git history предыдущего blob `95d74be79d3f37dad2db92d6ecb2dc45d64e8652` и отчётах [03Z](hourly/audit-20261018T03Z.md), [08Z](hourly/audit-20261018T08Z.md). Текущий файл заменяет накопленный журнал компактной действующей очередью, без потери Git history.
