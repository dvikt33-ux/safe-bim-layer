# APA №1 — проверки 11–20, SOURCE-only
11. AC29 IDS Import help L25–31: даже ошибочный IDS импортируется частично; вывод — нужен preflight, UI success не compliance. №2: rejected facets.
12. IfcTester tag ifcopenshell-python-0.8.5 ids.py L56–78: open(validate=True) и from_string(validate=True). XML schema check, не IFC model. №2: invalid XML.
13. ids.py L167–180: Ids.validate(ifc_file,should_filter_version=False), check_ifc_version. Model compliance, не XML check. №2: missing property.
14. facet.py L391–407: Classification(value,system,uri,cardinality,instructions). Классификации required/prohibited; российский справочник отдельно. №2: fixed system/value.
15. facet.py L634–650: Property(propertySet,baseName,value,dataType,uri,cardinality). Проверка Pset/типа, не всех СП/ГОСТ. №2: negative type.
16. facet.py L922–933: Material(value,uri,cardinality). Материал как IFC данные, не прочность. №2: negative material.
17. reporter.py L244–260,455–463: Json.report/to_string/to_file. Машинный отчёт, не LIVE. №2: JSON→JUnit.
18. reporter.py L470–483: Html(Json), entity_limit=100. HTML может ограничивать показ, не объём проверки. №2: JSON primary.
19. reporter.py L550–560: Ods(Json), ifctester/pyproject.toml L15–18 LGPL3+, xmlschema/odfpy/pystache. Pinned version=0.0.0, wheel не проверен. №2: Windows deps.
20. ifcclash.py L58–72: intersection/collision/clearance, tolerance/allow_touching/clearance. Готовый QA, пороги СП не заданы. №2: 3 IFC fixtures.
Source: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifctester/
Все 10 — проверки исходных контрактов, не исполнения. OFFLINE/BUILD/INSTALLED/LIVE NOT_RUN.
