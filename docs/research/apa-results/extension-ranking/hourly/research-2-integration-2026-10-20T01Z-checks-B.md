# APA №2 — SOURCE проверки 06–10

06. [Tapir1.5.9 NavigatorCommands.cpp L83–105](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L83-L105): пустой selectedNavigatorItemIds передаёт nullptr. Вердикт DENY; next missing/[] fixture.
07. [Graphisoft SDK29.3100 ProjectOperation](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___project_operation.html): Publish с optional selectedLinks выполняет публикацию. Вердикт DEFER; next GUID whitelist.
08. [SDK29 API_PublishPars](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/struct_a_p_i___publish_pars.html): local/LAN path; Tapir outputPath optional. Вердикт DENY unknown path; next sandbox/UNC/traversal.
09. [APA PR162 Router](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/scripts/archicad_project_accelerator.py#L140-L150): native_command_router использует DynamicCommands. Вердикт REUSE; next typed contract.
10. [APA PR168 C1](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py#L35-L85): parentHandle, DXF_WCS, $INSUNITS, unitConversionApplied=false. Вердикт REUSE RAW; next XCLIP.
