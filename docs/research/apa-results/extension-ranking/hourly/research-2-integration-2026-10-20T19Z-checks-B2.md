# APA №2 · 19Z · SOURCE 22–28

22. **PR126:** batch 1–200, Walls/Slabs/Beams/Columns/Windows/Doors, Roof отсутствует. Source: PR126 scripts/archicad_dynamic_commands.py, pinned f12aeba017ecd34a13989998f0b7700f6a0107d2. DEFER.

23. **PR162:** group-first требует проверенные member GUID, story, family signature и coverage target indices. Source: PR162 scripts/apa_ac29_group_strategy.py, pinned f7c37b84b76c040c417ccd58a5543326e50f673a. REUSE after runtime.

24. **PR74:** SQLite synchronous FULL и SCENE_ALREADY_RESERVED защищают от повторного plan hash. Source: PR74 scripts/archicad_scene_run.py, pinned 5a3a9201a715a5528c93bed4a5318e2acb32eea7. REUSE.

25. **PR175:** byte-exact saved snapshot сверяет protected SHA; blocksExternalArchicadWrites=false. Source: PR175 scripts/apa_ac29_save_isolation.py, pinned 24c198344a75dfa9a4515cca4df23badf3557d3d. REUSE.

26. **PR175:** stage_readonly_reopen требует Hotlink manifest APA_AC29_HOTLINK_BATCH_V1. Source: same pinned PR175. Generic BUILD-01 receipt NOT_FOUND.

27. **PR97:** ModelDump geometryScope ограничен доступными телами текущего 3D-вида, layer/design-option filters remain. Source: PR97 archicad-addon/Sources/ModelDumpCommands.cpp, pinned 8f134001ca0e3250eda587db61ac01dbd6357326. Нужна сверка GUID census.

28. **Tapir PR785:** CreateSlabs расширен, но PR описывает изменение как not built/reviewed. Source: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785. INSTALLED_UNKNOWN.

SOURCE_ONLY; новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.
