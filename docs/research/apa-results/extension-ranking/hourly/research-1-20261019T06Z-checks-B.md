# APA №1 06Z — P11–P20, transforms/geolocation SOURCE

Pinned: IfcOpenShell ifcopenshell-python-0.8.5, LGPL-3.0+.
P11 placement.py:127 get_cartesiantransformationoperator3d negates axis2 for mirror. №2: preserve determinant sign.
P12 placement.py:127 3DnonUniform uses Scale2/Scale3. №2: report XYZ scales; no uniform-clone inference.
P13 placement.py:172 get_mappeditem_transformation has TODO 2d, only 3D branch. №2: mark 2D mapped target NOT_SUPPORTED.
P14 placement.py:188 get_storey_elevation: ObjectPlacement then Elevation then 0. №2: missing is not measured zero.
P15 geolocation.py:147 auto_xyz2enh uses Helmert/WCS; without MapConversion returns input XYZ. №2: no georef PASS without source.
P16 geolocation.py:180 auto_enh2xyz inverse; missing map returns unchanged coordinates. №2: CRS UNKNOWN.
P17 geolocation.py:214 Helmert IFC2X3 ePSet_MapConversion vs IFC4 IfcCoordinateOperation. №2: schema-specific evidence.
P18 geolocation.py:606 get_grid_north missing map→0. №2: unknown north not true zero.
P19 geolocation.py:628 get_true_north missing/error→0. №2: require explicit TrueNorth for solar analysis.
P20 representation.py:58 get_context filters ContextType/ContextIdentifier/TargetView. №2: isolate Model/Body from plan 2D.

Source URLs: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util.
All checks static. Windows wheel metadata Py3.11/3.12 confirmed, local AC29/Tapir runtime not tested. SOURCE only, OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED no new evidence.