# APA №2 04Z — проверки 11–20 (SOURCE)

Pinned первоисточники: [v0.8.0](https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0), [Tapir 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9), [Graphisoft GDL](https://gdl.graphisoft.com/tips-and-tricks/hsf-source-format/).

11. **GDL binding:** schemes/spec.py:143–150 принимает gdl_param(name); наличие параметра в конкретном libpart не гарантирует. ADAPTER; next: check GDL inventory.
12. **Builtin binding:** schemes/model.py:8–16 Quantity=(type1,index-1003), GDL type180; spec.py:150–175 принимает raw param_type/index. SOURCE; next: whitelist известных кодов.
13. **Критерии:** docs/scheme-criteria-codes.md описывает эмпирические коды; редактирование criteria не поддерживается. READ_ONLY; next: compare criteria raw values.
14. **Validation:** schemes/validate.py:12–39 property_index использует Tapir GetAllProperties, не GetPropertyValuesOfElements. REUSE; next: missing GUID negative.
15. **Definition inventory:** Tapir PropertyCommands.cpp:206–247 GetAllProperties возвращает propertyId, group/name, collection/value/measure types, expressions. REUSE; next: stable GUID inventory.
16. **AC29 XML import:** Graphisoft Community 11–12.11.2025, thread 683387: при export/import исчезает 3D Axonometry, хотя XML поле содержит. DEFER import; next: build5101 hotfix evidence.
17. **GDL CLI:** v0.8.0 pyproject.toml [project.scripts] archicad-gdl, CLI:143–184 build, build-source, inspect, deploy. ADAPTER offline only; next: no deploy.
18. **Converter pin:** gdl/toolchain.py:58–101 find_lp_xmlconverter(version), compile_hsf uses hsf2libpart, timeout=300, output existence. DEFER; next: AC29 binary SHA.
19. **Converter official:** Graphisoft GDL HSF docs: hsf2libpart для single GSM, hsf2l для folder. SOURCE; next: isolated compile only after approval.
20. **OBJ units:** gdl/mesh.py:30–38 _autoscale: span>100 mm; span>5 cm; else m; parse_obj:49–79 multiplies verts by scale. REJECT automatic units for building; next: explicit unit input.

В каждом пункте подтверждён только исходный контракт. Установка, компиляция и импорт не выполнялись.
