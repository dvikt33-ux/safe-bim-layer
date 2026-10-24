# APA №1 06Z — P01–P10, IFC host/group SOURCE

Source: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util (LGPL-3.0+). Windows wheels 3.11/3.12 confirmed; local Tapir/AC29 runtime NOT_VERIFIED.

P01 element.py:1286 get_filled_void(window)→opening; absent FillsVoids→None. №2: ORPHAN not valid host.
P02 element.py:1305 get_voided_element(opening)→RelatingBuildingElement; absent→None. №2: validate wall GUID, not PDF label center.
P03 element.py:1843 get_openings(wall) yields IfcRelVoidsElements, NOT IfcOpeningElement. №2: dereference RelatedOpeningElement.
P04 element.py:1843 get_openings includes aggregate parent recursion. №2: distinguish inherited from direct and deduplicate.
P05 element.py:1169 get_grouped_by(group,True) traverses nested RelatedObjects. №2: IFC group is not Archicad native group.
P06 element.py:1169 traversal has no visited set; potential cycle nontermination (STATIC RISK ONLY). №2: bound traversal.
P07 element.py:1197 get_groups(element) via IfcRelAssignsToGroup. №2: preserve IFC group identity, never native-copy from it alone.
P08 element.py:614 get_type uses IFC4 IsTypedBy versus IFC2X3 IsDefinedBy. №2: schema-specific type provenance.
P09 element.py:1867 get_material_layers works only with IfcMaterialLayerSet; other forms return []. №2: empty≠single layer.
P10 placement.py:95 get_local_placement recursively multiplies parent placement. №2: verify world coords and avoid double transform.

No OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED evidence. PR160 PDF host unresolved; PR159/162 native group clone already exists.