# APA R1 16Z — приложение B: IFC QA и BCF, первичные контракты
Проходы 15–24. GitHub IfcOpenShell tag **v0.9.0** и документация **0.9.0post1** не идентичны. Tagged pyproject `version=0.0.0` не равен установленной версии. IfcTester/IfcDiff/IfcClash/BCF: Python>=3.11, LGPL-3.0-or-later. Локальный Windows runtime NOT_VERIFIED.

**SPF:** `python -m ifcopenshell.simple_spf model.ifc` обнаруживает синтаксические ошибки и дубли STEP #id, поддерживает JSON. **Schema:** `ifcopenshell.validate.validate(path,json_logger,express_rules=True)` проверяет типы/обратные атрибуты, но документация прямо ограничивает полноту global WHERE и SPF. Нужны обе проверки.

**IDS:** IfcTester `ids.Ids`, `Specification`, `Entity(name='IFCWALL')`, `Property(baseName='IsExternal',propertySet='Pset_WallCommon',cardinality='required')`. Отчёты Json/Sqlite/Html/Bcf. buildingSMART IDS 1.0 — требования к IFC данным, не автоматический СП/ГОСТ.

**IfcDiff:** tag v0.9.0 `relationships=['attributes','geometry']` по умолчанию; optional type/property/container/aggregate/classification. Added/deleted/changed by GlobalId. Эквивалентное тело extrusion↔mesh может считаться изменённым.

**IfcClash:** `ClashSet` требует `name,a,mode`, mode intersection/collision/clearance; intersection требует `tolerance/check_all`, collision `allow_touching`, clearance `clearance`. Результат содержит `a_global_id,b_global_id,distance`. Упрощённый пример docs без mode не рабочий контракт.

**BCF:** `bcf.bcfxml.load(Path)` различает v2/v3; обе реализации имеют load/save. Но `IfcTester reporter.Bcf.to_file` tag v0.9.0 импортирует **bcf.v2** и может создавать два viewpoint на один failing IfcElement (placement + element). Issue #7152: совместимость BCF2.1 имён viewpoint/snapshot; tagged topic.py пишет `guid+'.bcfv'`. Риск, не LIVE отказ.

**CRS:** `auto_xyz2enh` / `auto_enh2xyz` работают с MapConversion; при его отсутствии результат может оставаться без преобразования. Три независимые точки/единицы/CRS обязательны.

Первоисточники:
https://docs.ifcopenshell.org/ifcopenshell-python/validation.html
https://docs.ifcopenshell.org/autoapi/ifcopenshell/validate/index.html
https://docs.ifcopenshell.org/ifctester.html
https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifctester/ifctester/reporter.py
https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifcdiff/ifcdiff.py
https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifcclash/ifcclash/ifcclash.py
https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/bcf/bcf/bcfxml.py
https://github.com/IfcOpenShell/IfcOpenShell/issues/7152
https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/geolocation/index.html
