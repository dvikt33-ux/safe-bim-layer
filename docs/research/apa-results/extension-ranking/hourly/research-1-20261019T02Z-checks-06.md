# APA №1 02Z · SOURCE 16–18

IfcOpenShell/Ifc5D tag ifcopenshell-python-0.8.5; LGPL-3.0-or-later. Windows wheel/APA runtime NOT_VERIFIED.

**16. Одинаково ли поле кода в IFC2X3/IFC4?** [ItemReference](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/classification/add_reference.py#L214), blob `10177821b4bb`. Свидетельство: IFC2X3 ItemReference, иначе Identification. Вывод: готовая функция/ограничение. Контрааудит: Нужен schema gate. Далее: Источник системы.

**17. Как разрешить родительскую систему класса?** [get_classification](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/classification.py#L61), blob `df36eb97a486`. Свидетельство: ReferencedSource до IfcClassification. Вывод: готовая функция/ограничение. Контрааудит: Может вернуть None. Далее: Ifc5D.

**18. Есть ли готовая CSV→IFC смета?** [CSV to IFC](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifc5d/README.md#L10), blob `ba37664a88f0`. Свидетельство: README Ifc5D заявляет CSV→IFC. Вывод: готовая функция/ограничение. Контрааудит: Не нормативная база цен. Далее: ODS.

