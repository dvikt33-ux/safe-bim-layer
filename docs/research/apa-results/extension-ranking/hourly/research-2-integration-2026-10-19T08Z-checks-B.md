# APA №2 08Z — проверки 11–20

SOURCE inspections, не runtime. Контракты из AC29 b3000, Tapir tag 1.5.9 и pinned IFC 0.8.5.

11. **Hotlink provenance** — [первоисточник](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/docs/evidence/apa-ac29-hotlink-batch-20261018/live02/persistence-provenance.json). saved SHA bca84b15… ≠ later scratch 6c14ea78…; originalBatchScratchAccepted=false. **REUSE_WITH_LIMIT**. Далее: exact snapshot SHA.

12. **IFC PDF document** — [первоисточник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/element.py#L1460-L1510). get_referenced_elements(IfcDocumentReference); relation может отсутствовать. **ADAPTER**. Далее: page/revision/IFC GlobalId.

13. **IFC 4D recursion** — [первоисточник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py#L272-L305). parent fallback повторно вызывает get_task_work_schedule(task), риск рекурсии. **BLOCK**. Далее: visited/NO_SCHEDULE.

14. **IFC 5D divide-zero** — [первоисточник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L49-L84). quantity None≠0; ZeroDivisionError подавляется. **BLOCK**. Далее: INVALID_FORMULA.

15. **B3 world/local** — [первоисточник](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-geometry-b3-20261018/scripts/apa_ifc_geometry_b3.py#L65-L117). GLB local, OBJ/bounds world; sample 5000. **REUSE**. Далее: coordinateFrame/PARTIAL_SAMPLE.

16. **AC29 runtime** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). GetProductInfo()→(version,build,language), IsAlive(). **REUSE**. Далее: локальный read-only preflight.

17. **Add-on capability** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). IsAddOnCommandAvailable(AddOnCommandId)→bool; не ABI proof. **REUSE**. Далее: проверить локальную схему.

18. **Publisher sets** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). GetPublisherSetNames()→List[str]. **REUSE**. Далее: named set whitelist.

19. **Publisher tree** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). GetNavigatorItemTree(NavigatorTreeId(type,name?)). **REUSE**. Далее: явное имя набора.

20. **Tapir Publisher path** — [первоисточник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L36-L75). publisherSetName required; outputPath optional→stored path. **BLOCK**. Далее: явный безопасный outputPath.
