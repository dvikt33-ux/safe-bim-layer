# APA №2 04Z — проверки 21–30 (SOURCE)

Pinned исходники: [v0.8.0](https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0), [Tapir 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9).

21. **HSF identity:** gdl/generate.py:370–400 записывает cfg.resolve_guid(name) в MainGUID, не GUID размещения. ADAPTER; next: duplicate MainGUID collision fixture.
22. **GSM validation:** gdl/toolchain.py:106–137 l2x + convertlibrary -interpret; автор прямо предупреждает, что чистая интерпретация не доказывает 3D geometry. DEFER; next: independent preview/geometry gate.
23. **Terrain tolerance:** core/drape.py:426–427 tol=0.005m, path_tol=0.002, step=0.1, lateral_step=0.5, max_nodes=500. ADAPTER; next: over-limit fail.
24. **Terrain surface:** core/drape.py:173–258 Slab/Mesh, story-level, holes; cdt.py triangulation. SOURCE; next: 3 independent surfaces and units.
25. **Road writer:** core/road_marking.py:190–280 dry_run default true, but when false invokes pp.place/write_parameters. REJECT write path; next: isolate pure read-only drape.
26. **IFC missing:** rules/builtin/ifc_readiness.py:35–56 returns skipped=true if IFC unavailable. BLOCKER; next: require executed count.
27. **False score:** rules/engine.py:19–27 when scored=[] score=100, passed=all(empty)=true. BLOCKER; next: fail-closed wrapper in existing APA.
28. **Coverage:** extract.py:151–188 Tapir GetAllElements whole-plan vs official API.GetAllElements model-only, selected MEP/markers may be missed. REUSE; next: scope+GUID diff vs Native Model Dump.
29. **Property crash:** extract.py:21–34,242–273 describes official API.GetPropertyValuesOfElements ComposeResult abort, even one cell; max5000 doesn't fix. BLOCKED for unguarded live; next: independent build5101 evidence.
30. **Ready Tapir alternative:** Tapir PropertyCommands.cpp:294–430 GetPropertyValuesOfElements uses ACAPI_Element_GetPropertyValuesByGuid with per-cell errors; :571–677 GetPropertyValuesOfAttributes uses ACAPI_Attribute_GetPropertyValue. ADAPTER attribute, DEFER element until crash safety; next: local 1.5.10 inventory.

Два разных property entrypoints не означают гарантии безопасности native evaluation. SOURCE only.
