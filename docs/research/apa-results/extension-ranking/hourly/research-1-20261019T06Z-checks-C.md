# APA №1 06Z — P21–P30, IFC geometry/units/MEP SOURCE

Pinned IfcOpenShell ifcopenshell-python-0.8.5, src/ifcopenshell-python/ifcopenshell/util/.
P21 representation.py:134 get_representation returns FIRST matching context; №2: preserve representation ID.
P22 representation.py:304 resolve_representation unwraps mapped source WITHOUT instance matrix; №2: no world-geometry claim.
P23 representation.py:325 resolve_items returns item+matrix; 2D target unsupported (P13); №2: matrix validity gate.
P24 unit.py:682 calculate_unit_scale project→SI, missing UnitsInContext→1; №2: UNKNOWN_UNITS not meter PASS.
P25 unit.py:459 get_property_unit explicit property unit or project default; №2: distinguish QTO unit inheritance.
P26 system.py:91 get_ports IFC4 IsNestedBy vs IFC2X3 HasPorts; №2: schema/flow completeness, not native MEP acceptance.
P27 system.py:111 get_connected_port returns first peer; №2: cardinality/reciprocity without second graph.
P28 shape.py:71 get_volume triangle signed sum; non-manifold unpredictable; №2: manifold gate before QTO.
P29 shape.py:305 get_faces_representation_item_ids maps face→IFC item ID, not Archicad GUID; №2: provenance chain.
P30 shape.py:319 get_shape_vertices returns world vertices after shape matrix; №2: avoid double placement.

Source: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util. LGPL-3.0+, Windows Python3.11/3.12 wheel. Existing APA IFC engine; no new writer. SOURCE only; no OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED.