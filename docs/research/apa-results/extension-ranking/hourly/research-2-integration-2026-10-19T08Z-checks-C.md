# APA №2 08Z — проверки 21–30

SOURCE inspections, без записи модели. Особый риск: пустой список Publisher в исходнике Tapir 1.5.9 не является безопасным no-op.

21. **Empty publisher selection** — [первоисточник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L75-L106). []→selectedLinksPtr=nullptr→ACAPI_ProjectOperation_Publish всего набора. **CRITICAL_BLOCK**. Далее: 0 selected→STOP.

22. **Publisher receipt** — [первоисточник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L93-L106). success возвращает {}, нет файлов/SHA. **BLOCK**. Далее: per-file readback.

23. **CreateLayout** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). (layoutName,LayoutParameters,masterNavigatorItemId,parentNavigatorItemId)→GUID. **ADAPTER FUTURE**. Далее: master/parent preflight.

24. **Layout mm/revisions** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). LayoutParameters horizontalSize/verticalSize=мм, currentRevisionId/hasIssuedRevision; length properties SI м. **UNIT_BLOCK**. Далее: mm→m explicit, revision≠PDF.

25. **Subset numbering** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). Subset 11 полей: includeToIDSequence, continueNumbering, startAt, ownPrefix и др.. **ADAPTER FUTURE**. Далее: ID uniqueness fixture.

26. **Official clone single** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). CloneProjectMapItemToViewMap(source,parent)→один NavigatorItemId. **REUSE**. Далее: single GUID readback.

27. **Tapir clone batch** — [первоисточник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L935-L1027). viewsData[]→navigatorItems[]; ошибки поэлементные, не atomic. **ADAPTER**. Далее: 2 clones + 1 invalid.

28. **Tapir view settings** — [первоисточник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L316-L444). GetViewSettings(ids)→modelViewOptions/layerCombination/penSetName/rotation/renovationFilterGuid. **REUSE READ**. Далее: invalid ID/unknown sourceGuid.

29. **Attribute folders** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). GetAttributeFolderStructure(type,path?) + GetAttributeFolders(ids)→OrError. **REUSE**. Далее: полный обход и ошибки.

30. **Pens/layer combo** — [первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html). GetActivePenTables: model/layout IDs; GetPenTableAttributes pens; LayerCombinationAttribute содержит IDs, не visibility. **REUSE_WITH_UNKNOWN**. Далее: UNKNOWN_VISIBILITY.
