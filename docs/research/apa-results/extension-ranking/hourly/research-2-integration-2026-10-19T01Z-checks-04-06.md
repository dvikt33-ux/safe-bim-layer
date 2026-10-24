# APA №2 01Z — проверки 04–06: полнота и GDL
Tapir tag 1.5.9 MIT. Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp и https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/docs/archicad-addon/command_definitions.js

04. Вопрос: fail-closed инвентарь? C++:558–582 `ACAPI_LibraryPart_GetNum/Get`, ошибка повышает `skippedCount`, максимум 5 `skippedSample`. Требовать skippedCount=0; далее identity.
05. Вопрос: что такое `guid`? C++:589–600 `GS::UnID(libPart.ownUnID).GetMainGuid()`; revision GUID НЕ выдан, element GUID иной. Нельзя считать полный UnID. Далее GDL.
06. Вопрос: готовые GDL-параметры? schema `GetGDLParametersOfElements` v1.5.7: input required `elements`, output `gdlParametersOfElements:[GDLParameterList]`. Только placed elements, unplaced GSM NOT_FOUND. Далее SDK29.
