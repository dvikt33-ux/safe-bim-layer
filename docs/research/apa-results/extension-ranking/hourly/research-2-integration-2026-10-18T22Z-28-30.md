# APA №2 22Z — проверки 28–30
SOURCE и историческая LIVE-квитанция; новых LIVE нет.

28. SDK29 Publisher? Graphisoft tag 29.3100 `docs/group___project_operation.html`: `ACAPI_ProjectOperation_Publish(const API_PublishPars*,const GS::Array<API_Guid>* selectedLinks=nullptr)`; struct API_PublishPars.guid/path. SDK29 SOURCE CONFIRMED, локальный runtime не проверен. Далее: Tapir.
29. Tapir Publisher? Tag 1.5.9 `NavigatorCommands.cpp` L7–22,30–109: publisherSetName required; selectedNavigatorItemIds optional; пустой массив → nullptr (весь набор). ADAPTER: непустой whitelist, уникальное имя, output sandbox. Далее: Hotlink.
30. Hotlink batch? APA PR173 live02/receipt.json: 1 CreateHotlinkInstances, 2 экземпляра, 69→119 GUID, 24 дочерних на каждый, saved/reopened SHA. Поздняя PLN изменилась; принят только SHA-связанный снимок. REUSE, без повтора. Далее: аудит №3.

Источники:
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___project_operation.html
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp
https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/docs/evidence/apa-ac29-hotlink-batch-20261018/live02/receipt.json
