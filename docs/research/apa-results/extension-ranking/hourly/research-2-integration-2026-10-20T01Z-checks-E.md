# APA №2 — SOURCE проверки 21–25

21. [IfcOpenShell0.8.5 system](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L118-L125): get_port_element возвращает первого owner. **UNKNOWN** orphan/multiple; next cardinality fixture.
22. [IfcOpenShell0.8.5 element](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/element.py#L1478-L1515): get_referenced_elements поддерживает IFC2X3/IFC4, возвращает set. **REUSE** read-only; next stable GlobalId sidecar.
23. [IfcOpenShell0.8.5 add_reference](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/document/add_reference.py#L62-L72): file.create_entity, ItemReference/Identification по схеме. **DEFER** mutation.
24. [APA PR154 PDFVectors](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_readonly.py#L136-L155): PDF points/Bézier, не BIM host/metres. **REUSE SOURCE**; next calibration.
25. [APA PR160 AP2](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ap2-massops-preflight-20261018/scripts/apa_ap2_massops_preflight.py#L145-L190): wallHostGUID=null, story/size/rotation unverified. **DENY CREATE**; next host/offset/favorite.
