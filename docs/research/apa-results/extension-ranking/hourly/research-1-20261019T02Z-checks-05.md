# APA №1 02Z · SOURCE 13–15

IfcOpenShell/Ifc5D tag ifcopenshell-python-0.8.5; LGPL-3.0-or-later. Windows wheel/APA runtime NOT_VERIFIED.

**13. Как закрепить источник класса в IFC?** [add_classification](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/classification/add_classification.py#L27), blob `50cff831944c`. Свидетельство: Создаёт IfcClassification. Вывод: готовая функция/ограничение. Контрааудит: Это IFC запись, не PLN. Далее: Назначение ссылки.

**14. Можно ли назначить класс нескольким IFC объектам?** [add_reference](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/classification/add_reference.py#L28), blob `10177821b4bb`. Свидетельство: products:list, reference/identification/classification. Вывод: готовая функция/ограничение. Контрааудит: Не нативный batch AC29. Далее: Наследование.

**15. Можно ли учитывать классы, унаследованные от типа?** [get_references](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/classification.py#L24), blob `df36eb97a486`. Свидетельство: should_inherit=True, type+occurrence. Вывод: готовая функция/ограничение. Контрааудит: Без наследования ложный MISSING. Далее: Версии IFC.

