# APA №2 — проверки 01–05, 01Z
SOURCE only. Вопрос → первоисточник → контракт → решение → следующий gate.

01. **Publisher tree?** [Tapir1.5.9 Navigator L1518–1610](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L1518-L1610): GetNavigatorItemTree(PublisherSets,publisherSetName) возвращает navigatorItemTree с GUID и children. **REUSE**, проверить локальную команду.
02. **Регистрация?** [Tapir1.5.9 AddOnMain L1023](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp#L1023): зарегистрирован GetNavigatorItemTreeCommand с версией команды 1.1.7, не APX. **SOURCE_FOUND**, local 1.5.10 unverified.
03. **Полнота?** [Tapir Navigator L1499–1515](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L1499-L1515): ошибка GetNavigatorChildrenItems скрывается, children отсутствуют. **PARTIAL_UNVERIFIED**; нужен независимый error-aware census.
04. **Publisher identity?** [Tapir Navigator L8–24](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L8-L24): helper name→rootGuid пропускает неуспешные sets. **DENY** ambiguous name/partial; проверить все GUID.
05. **SDK census?** [Graphisoft SDK29.3000 Navigator](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/group___navigator.html): GetNavigatorSetNum/GetNavigatorSet/GetNavigatorChildrenItems дают GUID и ошибки. **ADAPTER** минимальный read-only handler в существующем Bridge, ABI gate.
