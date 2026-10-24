# APA №2 01Z — проверки 01–03: готовый Tapir Library
SOURCE tag 1.5.9, MIT; локальная 1.5.10 не проверена.
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/docs/archicad-addon/command_definitions.js

01. Вопрос: как проверить runtime версию? `GetAddOnVersion` v0.1.0: input=null, output `version:string` required. REUSE Bridge; не вызывался. Далее: библиотечный инвентарь.
02. Вопрос: готовая команда инвентаря? `GetAvailableLibraryParts` v1.5.0: optional `filterByTypeId:LibraryPartType`. REUSE, не создавать сканер. Далее: output.
03. Вопрос: какие данные доступны? Output `libraryParts:[{guid,index,documentName,fileName,typeId}]`, `skippedCount`, `skippedSample:[{index,code}]`. Package dependencies отсутствуют; ADAPTER только для пробела. Далее: skippedCount.
