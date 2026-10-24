# APA №1 — проверки 21–30, SOURCE-only
21. ifcclash.py L37–41,93–107: ClashSource file/mode/selector, группы a/b. Готовый фильтр дисциплин, selector syntax ещё не проверен. №2: fixture.
22. ifcclash.py L219–243: export_bcfxml импортирует bcf.v2.bcfxml.BcfXml. Это BCF v2, не BCF3 AC29. №2: version roundtrip.
23. ifcclash.py L45–55,249–258: a_global_id/b_global_id/p1/p2/distance и export_json. JSON QA, единицы и GUID не проверены. №2: schema.
24. ifcfm/__init__.py L64–95: Parser(preset=basic), pinned cobie24.py. Новый кандидат IfcFM, не COBie3. №2: handover profile.
25. ifcfm/__init__.py L100–128: duplicate_keys.append и замена значения по ключу. Не lossless без gate. №2: duplicate_keys==0.
26. ifcfm/__init__.py L130–143 federate пропускает повторный ключ; L228–305 CSV/ODS/XLSX. Конфликты скрываются. №2: conflict report.
27. src/bcf/pyproject.toml L9–24: bcf-client Python>=3.8, GPLv3 classifier; общий README IfcOpenShell говорит LGPL. Лицензия не разрешена. №2: sdist/LICENSE.
28. bcf/v3/bcfxml.py L121–170,207–231: load/create_new/save/add_topic; v3/topic.py L222–245: add_viewpoint_from_point_and_guids. GUID mapping не доказан. №2: BCF3 fixture.
29. ifcopenshell/api/document/add_information.py L26–63, add_reference.py L22–62, assign_document.py L27–50: IFC document/page reference. Не PDF vector parsing. №2: revision URI.
30. ifcopenshell/api/geometry/edit_object_placement.py L33–60: matrix 4x4/is_si/should_transform_children; только LocalPlacement. Не native Clone. №2: opening/port fixture.
Pinned primary sources: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/
Все 10 — проверка исходных контрактов. OFFLINE/BUILD/INSTALLED/LIVE NOT_RUN.
