# Проверки 16–18 — IfcFM и IDS

16. **Сохраняются ли типы CSV?** IfcFM `__init__.py:168–213`: None→N/A, empty→-, bool→YES/NO, list→строка. Вердикт CSV не lossless typed storage; нужен исходный IFC/GUID. Далее COBie.

17. **Единицы и GUID?** `cobie24.py:310–348`: LinearUnits, AreaUnits, VolumeUnits, CurrencyUnit, ExternalFacilityIdentifier=GlobalId. Вердикт readback units/GUID; далее IDS.

18. **Строгий XML API?** IfcTester `ids.py:56–86`: `open(filepath,validate=False)`; при true `get_schema().validate(filepath)`, затем decode. Вердикт explicit XSD preflight; далее CLI.

Источники: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcfm/ifcfm/
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifctester/ifctester/ids.py
