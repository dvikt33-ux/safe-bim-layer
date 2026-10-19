# APA №2 — матрица интеграции B

| Готовый инструмент | Цепочка через APA | Версия, контракт, лицензия | Решение, балл, сложность | Риски и ГОТОВО |
|---|---|---|---|---|
| MEP PhysicalSystem | Bridge→binding NOT_FOUND→SDK29 read-only→BIM Graph | Graphisoft SDK29 EULA; FindSystemIdsFromElementIds, GetRootElementId optional | DEFER 83 ДОЛГО | MEP license/ABI; physical flags+root, A11.S10 BLOCKED |
| IFC HookManager | Сейчас штатный export→B2; C++ callback отложен | SDK29 EULA; RegisterPropertyHook/UnregisterPropertyHook | DEFER 71 ДОЛГО | callback lifetime, IFCHook_Test; export GUID readback |
| APA B2 PR167 | Router→B2→IFCCSVExport/IFCExtractElements/IFCBCFIssues | IfcOpenShell 0.8.5; READ_ONLY private copy, GlobalId subset | REUSE 94 БЫСТРО | geometryEquivalenceVerified=False; relations/host fixtures |
| APA B3 PR170 + Hotlink PR173 | Router→B3 world bounds; Hotlink через существующий SceneWriter | B3 use-world-coords action != glb; PR173 historical LIVE-02 | REUSE 90 БЫСТРО | units/mirror, original SHA; no new LIVE |
