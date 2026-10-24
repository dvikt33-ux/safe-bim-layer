# APA 18Z: contracts 21-30 — ready integration

21. PR165 smoke receipt: 12 PASS on SYNTHETIC_IFC4_DXF, nativeCalls=0, plnWrites=0; not BDD LIVE.
22. Tapir 1.5.9 Publisher: selectedNavigatorItemIds empty leaves selectedLinksPtr null; whole set risk.
23. Tapir GetNavigatorItemTree accepts navigatorMapId=PublisherSets and publisherSetName.
24. Tapir SaveAsModuleFile takes moduleFilePath and optional elements; existing file overwritten.
25. Tapir CreateHotlinkNodes takes sourceLocation, storyRangeType and refFloorIndex.
26. CreateHotlinkInstances takes hotlinkNodeId, origin; rotationAngle in radians.
27. Local catalog 1.5.10 exposes GetIFCExportTranslators: names and preview flag only.
28. IFCFileOperation save accepts translatorName and elementsToExport; default is visible elements.
29. IfcTester reporter.Bcf writes BCF2 ZIP; existing APA V1 runner parses JSON only.
30. SAF SDK 1.7.3 imports ExcelModel; EPPlus dependency version range needs a license lock.

Sources: https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9/archicad-addon/Sources
https://github.com/IfcOpenShell/IfcOpenShell
https://www.nuget.org/packages/StructuralAnalysisFormat/1.7.3
Verdict: reuse/adapter, no new engine.
