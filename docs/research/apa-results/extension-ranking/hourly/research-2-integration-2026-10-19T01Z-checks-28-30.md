# APA №2 01Z — проверки 28–30: 4D/5D/SAM
S1 https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py
S2 https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py
S3 https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html

28. Вопрос: готовое 4D чтение? S1:299–347 `get_work_schedule_tasks` рекурсивно выдаёт `IfcTask`, `get_task_inputs/outputs` связывает IFC Product; отсутствующий `Controls/OperatesOn` может ломать итерацию. ADAPTER read-only, no scheduler. Далее 5D.
29. Вопрос: надёжный 5D итог? S2:49–61 None quantity ≠ zero; 271–294 false-like `AppliedValue` → None; 75–80 ZeroDivisionError подавляется. FAIL-CLOSED, unit/currency guard, no cost writer. Далее SAM.
30. Вопрос: нативная нагрузка? S3:678–681 `ACAPI_Analytical_GetAnalyticalLoadCombinations/GetAnalyticalLoadCombination`; SDK29 `API_AnalyticalLoadCombination.loadFactors` массив. Готового Tapir JSON bridge/solver/СП mapping NOT_FOUND. DEFER.
