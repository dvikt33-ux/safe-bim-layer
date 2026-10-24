# APA №2 01Z — проверки 16–18: native MEP / GUID
Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/MEPCommands.cpp ; https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py

16. Вопрос: полный ли GetMEPPorts? Tapir 1.5.9 C++:453–456 `Port::Get(portId).IsErr() → continue`, без счётчика ошибок. Нельзя утверждать полный port graph. Далее output.
17. Вопрос: как связать результат с элементом? C++:429–486 `elementPorts` сохраняет порядок запроса, но успешный `elementPortsOs` не содержит element GUID; ошибки отдельными строками. Только позиционный join и проверка размера массива; native completeness NOT_VERIFIED. Далее IFC GUID.
18. Вопрос: готова ли проверка IFC GUID? PR165:112–133 `_ifc_globalids` считает `duplicateCount/missingCount`, но не валидирует base64. REUSE upstream validate, не второй engine. Далее json_logger.
