# Проверки 22–24 — зависимости и Clash

22. **Зависимости IDS?** `ifctester/pyproject.toml:7–20`: LGPL3+, version=0.0.0 в теге; xmlschema,odfpy,pystache,bcf-client,flask. Вердикт source tag ≠ installed wheel; далее Clash.

23. **Контракт режимов?** `ifcclash.py:37–74`: ClashSet mode intersection/collision/clearance, a/b sources, tolerance/allow_touching/clearance. Вердикт fixed whitelist; далее вызов.

24. **Clearance работает готовым методом?** `ifcclash.py:93–131`: `clash_clearance_many(...,clearance,check_all)`. Вердикт reuse upstream; единицы и baseline требуют fixtures.

Источники: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifctester/
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcclash/ifcclash/ifcclash.py
