# APA №1 06Z — 7 карточек для исследователя №2

Общий инструмент: IfcOpenShell `ifcopenshell-python-0.8.5` (LGPL-3.0+, Win x64 wheels Python 3.11/3.12; локальный runtime/соответствие wheel↔tag NOT_VERIFIED). Первичные строки: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util. Все баллы — экспертная полезность, НЕ benchmark. Только чтение IFC, без нового writer.

**C1 97/100 — окно→проём→стена.** API element.py:1286/1305/1843 `get_filled_void/get_voided_element/get_openings`. Не дублирует PR160: PDF-метки не физические анкеры. Блокер: IFC экспорт должен содержать IfcRelFillsElement/IfcRelVoidsElement. №2: существует ли уже chain GUID в V2? **ГОТОВО:** 3 GUID + orphan/absent statuses на независимом IFC readback, без создания native окна.

**C2 96/100 — mapped transform/зеркальность.** API placement.py:127/172 и representation.py:325; mirror/Scale2/Scale3. Не дублирует CloneNativeGroupV1 (IFC audit, не копирование). Блокер: `TODO 2d`, matrix provenance. №2: проверен ли 2D gate? **ГОТОВО:** 3D mirror/nonuniform recognized, 2D NOT_SUPPORTED, без false PASS.

**C3 95/100 — геопривязка генплана.** API geolocation.py:147/180/214/606/628; Helmert, CRS, grid/true north. Не дублирует QGIS: только контроль IFC metadata. Блокер: missing conversion silently identity/zero. №2: как запретить ложную геопривязку? **ГОТОВО:** IFC4/IFC2X3, explicit CRS/source, missing→NOT_VERIFIED.

**C4 92/100 — типы и группы IFC.** API element.py:614/1169/1197. Не дублирует PR159/162 native groups. Блокер: group traversal без visited, IFC group != native group. №2: хранится ли group/type provenance? **ГОТОВО:** direct/nested groups, cycles bounded, native clone не запускается.

**C5 91/100 — слои материала IFC.** API element.py:1867 `get_material_layers`. Не дублирует AC29 GetCompositeAttributes: независимый IFC экспорт. Блокер: other material sets return []. №2: как сверять nominal skins с IFC? **ГОТОВО:** порядок/material/thickness и явный NOT_LAYERED; никакого СП PASS.

**C6 93/100 — единицы QTO.** API unit.py:459/682 `get_property_unit/calculate_unit_scale`. Не дублирует Ifc5D калькулятор: это контроль единиц. Блокер: missing units→1. №2: QTO unit coverage? **ГОТОВО:** explicit/project units, missing→UNKNOWN_UNITS, 0≠unknown.

**C7 90/100 — provenance геометрии и объём.** API shape.py:71/305/319 `get_volume/get_faces_representation_item_ids/get_shape_vertices`. Не дублирует native BREP verifier. Блокер: non-manifold volume, IFC item ID != native GUID, double transform. №2: есть ли trace и manifold gate? **ГОТОВО:** face→item→IFC GUID; nonmanifold NOT_VERIFIED, исходный IFC без изменений.

SOURCE ONLY. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED — новых проверок нет. 48 GB RAM/8 GB VRAM: GPU не требуется, пик RAM не измерен.