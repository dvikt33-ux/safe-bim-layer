# APA №2 22Z — проверки 24–27
SOURCE. Вопрос → pinned source/строка → вывод → следующий.

24. Связь задач с IFC? IfcOpenShell 0.8.5 `util/sequence.py` L332–349: `get_task_outputs` по IfcRelAssignsToProduct; `get_task_inputs` по OperatesOn. REUSE, хранить input/output отдельно. Далее: cycles.
25. Готовый scheduler безопасен? `api/sequence/cascade_schedule.py` L27,118–142: `cascade_schedule(file,task)` меняет даты; цикл → RecursionError. DEFER запись; read-only graph QA. Далее: геометрия.
26. Mapped transform? `util/placement.py` L127–187: `get_mappeditem_transformation` 4×4, nonuniform Scale2/Scale3, зеркальность; TODO 2d. REUSE для 3D, 2D fail-closed. Далее: B3.
27. APA уже строит world bounds? PR170 `scripts/apa_ifc_geometry_b3.py` L68–115: `use-world-coords` true кроме GLB, `convert-back-units=false`, `METER,1.0`, full selected STEP ID check. REUSE; не второй geometry engine. Далее: Publisher.

Источники: https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/placement.py
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py
https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-geometry-b3-20261018/scripts/apa_ifc_geometry_b3.py
