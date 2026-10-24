# APA R1 17Z — доказательства 01–15

Формат: вопрос → первоисточник → конкретное свидетельство → вывод → контраудит/поручение №2. Проверены исходные тексты, не только заголовки.

01. **Очередь:** NEXT_RESEARCH_PRIORITIES.md blob 8e69df9c8c9881a6d46262dbb19f68646f09c9c1 → F01–F09, включая Multiply/IFC openings/MEP/SAF/STEP/Hotlink → искать возможности, не подключать → №2 ведёт I01–I10.
02. **Канон:** PROJECT_PLAN.json Git blob c2ab2f9d606db1412c4031076103c267fc463f83 → revision182, 91 tasks; A11.S03 PARTIAL, A11.S08/S10 BLOCKED, A07.S03 READY → не объявлять DONE → проверять квитанции, а не чат.
03. **Реестр:** candidates.json blob 87ee1c0b66233bf713e273b8b7cd00eff3a422f9, 61 items → строки 'stephen'/'step-to-json' отсутствуют → два новых именных кандидата → отсутствие имени не доказывает функциональной уникальности.
04. **PDF:** https://github.com/dvikt33-ux/safe-bim-layer/pull/154 → PDFVectors full paths/Bezier/cp1251, Windows CI → не создавать второй PDF extractor → installed-router pending.
05. **Группы:** https://github.com/dvikt33-ux/safe-bim-layer/pull/159 → group acceptance mailbox, scratch PLN only; поздний LIVE указан аудитом 16Z → не дублировать group writer → production SceneWriter LIVE не доказан.
06. **Hosted openings:** https://github.com/dvikt33-ux/safe-bim-layer/pull/160 → 22 PDF mark placements; windows/doors only HOSTED_BATCH_CREATE_IF_QUALIFIED → марка не физический anchor → нет независимой проверки original PDF в этом цикле.
07. **Групповой выбор:** https://github.com/dvikt33-ux/safe-bim-layer/pull/162 → CloneNativeGroupV1, BIM Graph/SceneWriter route, nativeWritePermission=false → существующий высокоуровневый writer → PR162 LIVE NOT_VERIFIED.
08. **SDK29 Tool:** https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___grouping.html (blob 96995b5061db78d1dd898df88151c5631dac3eaa) → ACAPI_Grouping_Tool(elemGuids, API_ToolCmdID, void*); APITool_Group/Ungroup/Lock/Unlock → готовые group commands → не Multiply.
09. **SDK29 Edit:** https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___edit_pars.html (blob fb02dfa13460ab4d984ea1359bb3df3d4a85982c) → typeID, withDelete, origC, begC/endC; нет matrix count → прямой GUI Multiply контракт не найден → отсутствие не доказано для всего SDK.
10. **Tapir MOD:** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp (blob 99053b4ce5f32b33ae456a076f4355a68994e207) → SaveAsModuleFile(moduleFilePath required,elements optional), существующий путь перезаписывается → готовый экспорт модуля → нужен explicit output guard.
11. **Tapir empty elements:** тот же tagged source → SaveAsModuleFile::Execute отклоняет переданный пустой elements без elementId с APIERR_BADPARS → не fallback на selection → но при ОТСУТСТВИИ elements берётся selection.
12. **Hotlink node:** тот же tagged source → CreateHotlinkNodes(hotlinkNodes[]), sourceLocation required, case-insensitive existing:true; name/storyRangeType/refFloorIndex игнорируются для существующего node → готовый node lookup → source path ≠ child GUID.
13. **Hotlink instance:** тот же tagged source → CreateHotlinkInstances(hotlinkInstances[]) требует hotlinkNodeId+origin; rotationAngle в радианах, mirrored, floorIndex/layerIndex/skipNested → готовая batch placement схема → per-item ошибки возможны.
14. **Hotlink transform:** тот же tagged source → ChangeHotlinkInstances(hotlinkInstances[]) требует elementId; origin/rotationAngle/mirrored optional → нативная специализированная трансформация → MoveElements/RotateElements могут вернуть NoError без движения.
15. **Hotlink readback:** тот же tagged source → CreateHotlinkNodes returns hotlinkNodes[] node-or-error; CreateHotlinkInstances returns elements[] ID-or-error; ChangeHotlinkInstances returns executionResults[] → проверять каждый ответ → общий PASS не означает успех каждого экземпляра.

**Лицензия Tapir 1.5.9:** MIT LICENSE blob 1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd. Установленный Tapir 1.5.10 и ABI AC29 build5101 NOT_VERIFIED. Все 15 проверок SOURCE, не BUILD/LIVE.
