# APA №2 01Z — проверки 13–15: готовый IFC MEP wrapper
IfcOpenShell tag ifcopenshell-python-0.8.5, LGPL-3.0-or-later.
Источник: https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py

13. Вопрос: как получить порты владельца? 91–109 `get_ports(element,flow_direction=None)`: IFC4 `IsNestedBy`, IFC2X3 `HasPorts`; фильтр `FlowDirection`. REUSE, далее owner.
14. Вопрос: готовый owner mapping? 118–126 `get_port_element(port)`: IFC4 `Nests.RelatingObject`, IFC2X3 `ContainedIn.RelatedElement`; при отсутствии может вернуть None. Fail-closed для неизвестного owner. Далее peer.
15. Вопрос: готовая связность? 111–116 `get_connected_port` возвращает первый из `ConnectedTo/ConnectedFrom`; `get_connected_to/from` 128–155 строит соседей. Проверять взаимность/множественность, не выдавать native MEP PASS. Далее Tapir.
