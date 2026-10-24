# APA №1 — BUILD-01 — SOURCE 10–14 (G2 GDL/библиотеки)

Tapir upstream 1.7.2, MIT. Права на локальный модифицированный APX не меняются.

10. **Доказано ли исправление GDL-массивов?** [PR558](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/558): автор прямо пишет unbuilt/unreviewed; merge не доказывает AC29 runtime. **№2:** не применять в G2 без отдельной приёмки.

11. **Можно ли менять размер GDL array?** [PR558](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/558): новый контракт отклоняет список, длина которого не совпадает с dimension1×dimension2. **№2:** read-only сверить размеры целевой детали до любого изменения.

12. **Как записывается массив?** [PR558](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/558): элементы через ACAPI_LibraryPart_ChangeAParameter, перечитывание параметров после каждого item. **№2:** считать потенциально дорогим, не обещать ускорение без benchmark.

13. **Исправлен ли любой GDL hang?** [PR558](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/558): автор предупреждает, что зависание внутри parameter script может сохраниться. **№2:** не выполнять неизвестные GDL writes в BUILD-01.

14. **Есть ли полный setter маркеров?** [PR815](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/815): Get/SetMarkerParametersOfElements, setter только простых не-array параметров; автор пишет unbuilt/untested. **№2:** оставить optional, базовый Door/Window не блокировать.

**5 проверок, 2 первоисточника, 0 runtime тестов.** MODEL_MODE_NOT_VERIFIABLE.
