# APA №2 22Z — проверки 06–10
SOURCE. Вопрос → pinned код → контракт → вывод → следующий.

06. Owner порта? IfcOpenShell 0.8.5 `util/system.py` L118–125: `get_port_element` через `Nests.RelatingObject` или IFC2X3 `ContainedIn.RelatedElement`. REUSE, IFC GlobalId ≠ native GUID. Далее: документ.
07. Документ IFC? `api/document/add_information.py` L26,59–83: `add_information(file,parent)`; IFC2X3 `DocumentId`, IFC4 `Identification`. REUSE на копии. Далее: лист.
08. Лист? `api/document/add_reference.py` L22,65–71: `add_reference(file,information)`; IFC2X3 `ItemReference`, IFC4 `Identification`. ADAPTER page/revision/SHA. Далее: привязка.
09. Привязка к GUID? `api/document/assign_document.py` L27–30,74–76: `assign_document(file,products,document)`; пустой products → None. Reject empty. Далее: повторы.
10. Повторы? `assign_document.py` L77–103: ищет существующую `IfcRelAssociatesDocument` и объединяет RelatedObjects, отдельный IFC2X3/IFC4 путь. REUSE, readback по двум GUID. Далее: PDF SHA.

Источники: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/document
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py
