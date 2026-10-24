# APA №2 — проверки P21–P30 (03Z)
SDK29: https://github.com/GRAPHISOFT/archicad-api-devkit/tree/29.3100
Tapir: https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9
APA: https://github.com/dvikt33-ux/safe-bim-layer
P21. Renovation list? SDK29 docs/group___renovation.html ACAPI_Renovation_GetRenovationFilters(GS::Array<API_Guid>*). C++ ready, JSON binding NOT_FOUND in checked Tapir/official commands; defer.
P22. Current filter? SDK29 GetActualRenovationFilter(API_Guid*) reads current; SetActualRenovationFilter changes state. Use Tapir saved-view GUID instead; never call setter.
P23. Expression lint? SDK29 docs/group___property.html ACAPI_Property_CheckPropertyExpressionString(GS::UniString*) syntax only. No verified JSON binding; defer, do not claim semantic validation.
P24. Proxy source mapping? SDK29 docs/group___hotlink.html GetHotlinkProxyElementTable(hotlinkGuid,HashTable<API_Guid,API_Guid>*). C++ mapping exists; no verified JSON wrapper; defer.
P25. Tapir Hotlinks? Tagged ProjectCommands.cpp GetHotlinksCommand::Execute emits node hotlinkNodeId/name/type/location/children, NOT proxy→source mapping. Reuse node inventory only; source map remains blocked.
P26. Batch proof? PR173 live02/receipt.json: 69→119 GUID, 2 roots/48 children, one native batch, one SaveProject, reopened=true. Evidence read, no new LIVE; independent ACCEPTED not proven.
P27. Router reuse? PR165 scripts/apa_high_density_readonly_v2.py register at 381–409 calls router.add_local_provider and review_policy READ_ONLY. No second Router; integration reuse.
P28. World geometry? PR170 scripts/apa_ifc_geometry_b3.py execute at 53–80 pins ifcopenshell==0.8.5 and private IFC copy; compare bbox only, not BREP equality.
P29. License? Tapir tag1.5.9 LICENSE=MIT; Graphisoft SDK29 LICENSE=proprietary agreement. Mixed license chain must preserve notices; local binary license not inferred.
P30. Version drift? Tapir NavigatorCommands.cpp tags1.5.9 and1.7.1 contain same seven GetViewSettings fields; local labeled1.5.10 not checked. Require read-only command inventory + SHA.
SOURCE=10, OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.
