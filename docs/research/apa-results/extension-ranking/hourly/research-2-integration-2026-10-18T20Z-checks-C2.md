# APA №2 20Z — проверки 26–30: ссылки, матрицы, wheel

26. PDF лист связывается с IFC? [D] L68–104 `assign_document(products,document)` → IfcRelAssociatesDocument; дубликаты исключаются. Нужен sheet/revision/SHA manifest; далее URI.
27. External library — готовый коннектор? [L] L60–91 `assign_reference(products,reference)` → IfcRelAssociatesLibrary. Только URI, не сетевое подключение; далее transform.
28. MappedItem transform? [M] L118–128 `get_mappeditem_transformation` возвращает 4×4: MappingTarget @ MappingOrigin. Проверить единицы/зеркальность; далее PR170.
29. APA уже отдаёт матрицу? [B3] `IFCGeometryBounds` → `IFC_WORLD_SI_METRES` bbox, не mapped matrix. Только delta adapter; далее binary.
30. Windows wheel 0.8.5? [PY] Python 3.11 SHA256 `a994cb398aa822b0153ace11fc19deea108706d3a10339de9ac9dc13da21076d`, 3.12 `7927921dbfd18024f44780880c37e48460bbca7476da3b0c2607e044b31521d5`. PyPI PASS, локально NOT_VERIFIED; далее import/hash.

[D]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/document/assign_document.py
[L]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/api/library/assign_reference.py
[M]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/util/placement.py
[B3]: https://github.com/dvikt33-ux/safe-bim-layer/blob/35a8b7b2fd78e63a6e13254d4c4fde26171793c8/scripts/apa_ifc_geometry_b3.py
[PY]: https://pypi.org/project/ifcopenshell/0.8.5/
