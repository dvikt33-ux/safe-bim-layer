# APA №2 20Z — проверки 11–20 (4D SOURCE)

Вопрос → pin/поле → контрааудит → следующий вопрос. GitHub pin b139fe1c, НЕ доказанный exact source wheel 0.8.5.

11. Готовый work schedule? [W] L29–36 `add_work_schedule(file,name,predefined_type,start_time,work_plan)`. Да; далее календарь.
12. IFC2X3/4 одинаковы? [W] L91–105: IFC4 `assign_declaration`, IFC2X3 нет. Различать; далее WBS.
13. Корневой/дочерний task? [T] L27–35 `work_schedule` или `parent_task`. Взаимоисключение; далее ID.
14. Сохраняется Identification? [T] L142–151 дочерний IFC4 получает parent.ID + порядковый номер. Может переписать заданный ID; далее readback.
15. Время создаётся заполненным? [AT] L21–67 `add_task_time(task,is_recurring=False)` создаёт blank. Нужен внешний календарь; далее edit.
16. Как задаётся длительность? [ET] L29–60 `edit_task_time(...,attributes)`, `ScheduleStart`, `ScheduleDuration=P2D`. Проверить дату; далее output.
17. Построенная стена — вход? [O] L24–32 `assign_product(relating_product,related_object)` создаёт `IfcRelAssignsToProduct`. Нет, OUTPUT; далее input.
18. Демонтаж — выход? [I] L24–31 `assign_process(relating_process,related_object)` создаёт `IfcRelAssignsToProcess`. Нет, INPUT; далее циклы.
19. Граф с циклом? [CP] L92 `RecursionError`, networkx; циклы не принимать; далее float.
20. Готовая критическая траектория? [CP] L207/330 forward/backward pass, L498 free float. Есть, но не оптимизатор; далее QTO.

[W]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/sequence/add_work_schedule.py
[T]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/sequence/add_task.py
[AT]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/sequence/add_task_time.py
[ET]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/sequence/edit_task_time.py
[O]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/sequence/assign_product.py
[I]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/sequence/assign_process.py
[CP]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/sequence/recalculate_schedule.py
