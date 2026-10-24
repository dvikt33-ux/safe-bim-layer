# APA №2 — 11Z — проверки 21–30

Все проверки SOURCE (не runtime). [Основной отчёт](research-2-integration-2026-10-19T11Z.md).

21. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/shape.py#L319-L353) — get_shape_vertices/get_element_vertices применяют матрицу; ADAPTER не умножать дважды; next translated mesh.
22. [SOURCE](https://github.com/dvikt33-ux/safe-bim-layer/pull/170/files) — B3 world-coords=true для OBJ/bounds, false GLB; REUSE; next mirror.
23. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcdiff/ifcdiff.py#L77-L93) — IfcDiff relationships default ['geometry'], shallow=True; ADAPTER explicit; next property-only.
24. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcdiff/ifcdiff.py#L99-L118) — IfcFeatureElement исключён из default inventory; ADAPTER opening graph; next new opening.
25. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcdiff/ifcdiff.py#L149-L172) — shallow continue пропускает geometry после атрибутов; ADAPTER shallow=False; next combined.
26. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcdiff/ifcdiff.py#L231-L253) — disable-opening-subtractions=True; ADAPTER отдельные IfcRelVoidsElement; next opening change.
27. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcdiff/ifcdiff.py#L293-L340) — container сравнивается entity objects, не явно GlobalId; ADAPTER GUID normalization; риск пока SOURCE.
28. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifccsv/ifccsv.py#L75-L145) — include_global_id мутирует attributes list, None→'-'; REUSE export-only; next null/zero.
29. [SOURCE](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/bcf/bcf/v2/bcfxml.py#L53-L61) — BCF v2 BcfXml default version_id=2.1; REUSE PR167 B2; next ZIP readback.
30. [SOURCE](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html) — GetPublisherSetNames List[str], IsAddOnCommandAvailable bool; REUSE names, DEFER publishing.

[IfcDiff entity equality](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/entity_instance.py#L444-L463) и [IfcCSV Import](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifccsv/ifccsv.py#L399-L514) требуют отдельного OFFLINE negative gate. Никаких установок или изменений IFC/PLN.
