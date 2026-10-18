# APA R1 16Z — приложение A: AC29/SDK29/PR, первоисточники
**Это часть отчёта 16Z; только SOURCE, не BUILD/LIVE.** Проходы 01–14 и 25 из основного отчёта.

**План:** canonical PROJECT_PLAN.json Git blob c2ab2f9d606db1412c4031076103c267fc463f83: revision182, 91 tasks. A11.S03 PARTIAL, A11.S08/A11.S10 BLOCKED, A07.S03 READY. NEXT priorities blob db88a1014d578e6fb99eed2f57268d0e1f86e413. Матрица 61 кандидата. Последние отчёты: audit14Z blob 35581c923b2c7ea10f49c0f9f4b51dad6adc9823, R2-12Z 09c86e212b6caf96fc9066b1d989a1028574c7aa, R1-14Z b82c8d683fe24d321fe75c1101aa4287c647872a.

**PR anti-duplication:** PR159 head f13b1dcd: `SOURCE_ADDED_NOT_LOCALLY_EXECUTED`. PR162 head f7c37b84: `CloneNativeGroupV1`, `nativeWritePermission=false`, but body claims LIVE PR159; independent receipt not located in examined PR bodies. PR160 head e8cbbf97: hosted windows/doors `HOSTED_BATCH_CREATE_IF_QUALIFIED`, not generic copy. PR154 head ca28e9b8: PDFVectors vector lines/Bezier/cp1251 already implemented in draft; local installed-router acceptance pending. None merged.

**Graphisoft 29.3100 (not SDK30):** `API_EditPars` has `API_EditCmdID typeID`, `bool withDelete`, `bool topNodeStretched`, `API_Coord origC`, `API_Coord3D begC/endC/endC2`. No matrix repetition count in this struct: cannot claim SDK29 has programmatic GUI Multiply from this evidence. `ACAPI_Grouping_CreateGroup(const GS::Array<API_Guid>&, API_Guid*, const API_Guid*)` supports nested parent; already existing group mechanism. `RoutingElementDefault::Place(vector<API_Coord3D>, map<UInt32,RectData>, map<UInt32,CircData>, optional<API_Guid>)` exposes per-segment maps; not proof of terminal/Transition. `API_SavePars_Saf` fields: `elementsToSAFExport`, `selectedSAFTranslatorName`; exporter, not solver.

**AC29 UI:** Multiply Drag/Rotate/Elevate/Matrix, Increment/Spread/Distribute; GUI not API. MEP Route Magic Wand documented **Available with Archicad Collaborate**, local entitlement unknown. SAF `*.xlsx` export Entire/Visible/Selected or Publisher; Frilo/SCIA connectors mentioned, no claim of free licensing. Model Compare handles 3D new/modified/deleted, PLN/PLA/SAF/Hotlink before-after, excludes 2D; no verified programmatic entrypoint.

**Licenses:** SDK29 Graphisoft Software License Agreement v2, NOT MIT. Upstream Tapir MIT does not prove local binary command availability. SDK29.3100 docs do not prove binary ABI with AC29 build5101.

**Sources:**
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___edit_pars.html
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___grouping.html
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_routing_element_default.html
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___save_pars___saf.html
https://help.graphisoft.com/AC/29/INT/_AC29_Help/030_Interaction/030_Interaction-96.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-4.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/091_StructuralAnalysisFormat/091_StructuralAnalysisFormat-2.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm
