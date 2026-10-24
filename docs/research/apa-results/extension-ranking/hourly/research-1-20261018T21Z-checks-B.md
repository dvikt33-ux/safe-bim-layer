# APA №1 21Z — доказательства B: проверки 11–20
Все исходники IfcOpenShell строго из тега `ifcopenshell-python-0.8.5` (commit 16723d11cab9bc8a13b4e025a00d39445ccc462e), не из документации 0.9.0post1. Только SOURCE.

11. **Mirror:** `util/placement.py` L138–155: Axis2 инвертируется, если dot с построенной Axis2 отрицателен; зеркальность предусмотрена. Не тестировали на реальном IFC. №2: determinant<0 fixture.
12. **Nonuniform:** тот же файл L155–170: IfcCartesianTransformationOperator3DnonUniform читает Scale2/Scale3; остальные используют общую Scale. №2: fixture 1×2×3, units.
13. **2D TODO:** `get_mappeditem_transformation` L172–184 содержит TODO 2d и ветку только IfcCartesianTransformationOperator3D. Не заявлять 2D поддержку. №2: fail-closed 2D.
14. **Nested mappings:** `util/representation.py` L325–339: `resolve_items` рекурсивно раскрывает MappingSource.MappedRepresentation, возвращает item+matrix. Матричный порядок нужен в fixture.
15. **World vertices:** `util/shape.py` L319–335: `get_shape_vertices` применяет get_shape_matrix к local vertices. PR170 уже выдаёт world bounds, второй provider не нужен.
16. **4D tasks:** `util/sequence.py` L293–304: get_work_schedule_tasks рекурсивно возвращает root+nested tasks. Не календарный solver и не APA scheduler.
17. **5D missing/zero:** `util/cost.py` L49–60: IfcCostItem без CostQuantities → None, quantity=0 → 0.0. Нельзя подменять None нулём. №2: missing/zero/unit QA.
18. **IFC provenance:** `api/document/assign_document.py` L27–103: products:list + document:IfcDocumentReference; создаёт/дополняет IfcRelAssociatesDocument, фильтрует повторные связи. Это изменение IFC-копии, не PLN. №2: 2 GlobalId + sheet/revision/SHA.
19. **PDF page labels:** PyMuPDF Document.get_page_labels и Page.get_label (API v1.18.6/7+). Page label может повторяться; не равен номеру листа в штампе и revision. №2: сначала reuse PR154/pdfplumber.
20. **PDF license:** официальный PyMuPDF AGPLv3 либо commercial, не MIT. Нельзя считать новую зависимость беспроблемной для закрытого APA. №2: доказать лицензионную допустимость или отказаться.

Исходники pinned:
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/placement.py#L138-L184
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/representation.py#L325-L339
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/shape.py#L319-L335
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py#L293-L304
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L49-L60
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/document/assign_document.py#L27-L103
https://pymupdf.readthedocs.io/en/latest/document.html
https://pymupdf.readthedocs.io/en/latest/page.html
https://pymupdf.io/licensing

SOURCE=PINNED_VERIFIED, OFFLINE/BUILD/INSTALLED/LIVE=NOT_RUN, ACCEPTED=NO.
