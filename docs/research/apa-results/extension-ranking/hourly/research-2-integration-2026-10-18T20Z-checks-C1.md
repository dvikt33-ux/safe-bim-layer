# APA №2 20Z — проверки 21–25: 5D SOURCE

21. Cost schedule готов? [CS] `add_cost_schedule(name,predefined_type)` → IfcCostSchedule. Да, IFC копия; далее item.
22. Иерархия? [CI] `add_cost_item(cost_schedule|cost_item)`. Root/child; далее quantity.
23. QTO связь? [CQ] L140 `control.assign_control`; L146 `ast.parse(formula)`. Да, но formula нужно ограничить; далее missing.
24. Отсутствующий QTO? [CQ] L151–166 missing/zero печатает WARNING; дальше FormulaEvaluator. Требовать fail-closed; далее rate.
25. Стоимость? [CV] `edit_cost_value_formula(cost_value,formula)`; [UC] `get_total_quantity` L49. Нет источника тарифов ГЭСН/ФЕР; далее документ.

[CS]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/cost/add_cost_schedule.py
[CI]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/cost/add_cost_item.py
[CQ]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/cost/assign_cost_item_quantity.py
[CV]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/cost/edit_cost_value_formula.py
[UC]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/util/cost.py
