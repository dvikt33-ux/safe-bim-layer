# APA №2 22Z — проверки 19–23
SOURCE. Вопрос → первоисточник/строка → решение → следующий.

19. Готовый JSON видимой DXF? ezdxf v1.4.5 `addons/drawing/json.py` L172–209,218–229: `CustomJSONBackend.get_json_data()` отдаёт type/properties/geometry, properties только color/stroke-width/layer, без source handle. REUSE для QA; C1 отдельно для provenance. Далее: 5D.
20. Готовая cost-связь? IfcOpenShell 0.8.5 `util/cost.py` L190–203: `get_cost_items_for_product` читает `IfcRelAssignsToControl`. REUSE, без записи. Далее: quantity.
21. Missing vs zero? `util/cost.py` L49–57: `get_total_quantity` возвращает None при отсутствии, 0 при нулевой сумме. REUSE, запрет подмены None на 0. Далее: applied.
22. Applied value? `util/cost.py` L37–45: `get_primitive_applied_value(None)` возвращает 0.0. ADAPTER для явного absent marker до расчёта; далее: 4D.
23. Чтение задач? IfcOpenShell 0.8.5 `util/sequence.py` L299–303: `get_work_schedule_tasks(work_schedule)` yield root+nested. REUSE, не собственный scheduler. Далее: связи.

Источники: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/addons/drawing/json.py
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py
