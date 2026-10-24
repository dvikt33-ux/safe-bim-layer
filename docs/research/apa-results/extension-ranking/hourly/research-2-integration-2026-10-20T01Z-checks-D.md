# APA №2 — SOURCE проверки 16–20

16. [ezdxf1.4.5 insert.py L668–702](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py#L668-L702): multi_insert дедуплицирует zero-spacing через done=set. Вердикт ADAPTER declared/unique; next 2×3 fixture.
17. [ezdxf1.4.5 xclip.py L25–45](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xclip.py#L25-L45): inverted boundaries upstream признаёт неоднозначными. Вердикт UNSUPPORTED до независимого oracle.
18. [IfcOpenShell0.8.5 util/system.py L91–103](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L91-L103): IFC4 get_ports использует IsNestedBy. Вердикт REUSE IFC V2; next IFC4 fixture.
19. [IfcOpenShell0.8.5 util/system.py L103–109](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L103-L109): IFC2X3 HasPorts. Вердикт REUSE; next IFC2X3 fixture.
20. [IfcOpenShell0.8.5 util/system.py L111–116](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L111-L116): get_connected_port возвращает только первый peer. Вердикт ADAPTER read-only все IfcRelConnectsPorts; next cardinality.
