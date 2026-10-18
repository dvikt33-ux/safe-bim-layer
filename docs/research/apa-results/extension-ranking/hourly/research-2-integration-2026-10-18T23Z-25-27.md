# Проверки 25–27 — Clash и BCF3

25. **Достаточен ли Clash JSON?** `ifcclash.py:45–55,140–155`: a_global_id,b_global_id,p1,p2,distance. Вердикт пригоден для BIM Graph QA при проверке единиц; далее экспорт.

26. **BCF какой версии?** `ifcclash.py:225–243`: `from bcf.v2.bcfxml import BcfXml`. Вердикт BCFv2, не BCF3; PR167 уже BCF2.1. Далее v3 API.

27. **Готов ли BCF3 ZIP?** `bcf/v3/bcfxml.py:121–170`: load/create_new/save; `topic.py:222–245`: add_viewpoint_from_point_and_guids(position,*guids). Вердикт API есть, GUID/camera roundtrip не доказан; далее license.

Источники: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcclash/
https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/bcf/
