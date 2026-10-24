# APA №1 02Z · SOURCE 22–24

IfcOpenShell/Ifc5D tag ifcopenshell-python-0.8.5; LGPL-3.0-or-later. Windows wheel/APA runtime NOT_VERIFIED.

**22. Зависит ли цена от региональной локали?** [locale.setlocale](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifc5d/ifc5d/csv2ifc.py#L152), blob `c33d6e847e9b`. Свидетельство: locale.LC_ALL системная; locale.atof далее. Вывод: готовая функция/ограничение. Контрааудит: RU/EN offline NOT_RUN. Далее: CostSchedule.

**23. Есть ли сущность сметы и таблицы расценок?** [add_cost_schedule](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/cost/add_cost_schedule.py#L26), blob `cc88336cb49d`. Свидетельство: IfcCostSchedule с predefined_type. Вывод: готовая функция/ограничение. Контрааудит: Не источник официальных расценок. Далее: Иерархия.

**24. Есть ли вложенные позиции сметы?** [add_cost_item](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/cost/add_cost_item.py#L27), blob `1bdae9e9a1d6`. Свидетельство: cost_schedule XOR parent cost_item. Вывод: готовая функция/ограничение. Контрааудит: Нельзя задавать оба. Далее: Space QTO.

