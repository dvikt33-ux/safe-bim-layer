# APA AC29 — исследователь №2, 19 октября 2026, 08:00 UTC

**SOURCE ONLY.** Фактически выполнены **30** содержательных статических проверок первоисточников, **2 собственных контрааудита**, исследованы **10** путей подключения готовых решений к уже существующему Router/BIM Graph/SceneWriter. Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED — **0**. Никаких установок, операций Archicad, изменений PLN/APX, кода, main, плана revision182 или очереди №3. `MODEL_MODE_NOT_VERIFIABLE`.

## Полный исследовательский пакет
- [Проверки 01–10](research-2-integration-2026-10-19T08Z-checks-A.md), [11–20](research-2-integration-2026-10-19T08Z-checks-B.md), [21–30](research-2-integration-2026-10-19T08Z-checks-C.md): вопрос, независимый первоисточник, точный контракт, адаптер/блокер, вердикт, следующая проверка.
- [Матрица решений 01–03](research-2-integration-2026-10-19T08Z-matrix-01-03.md), [04–05](research-2-integration-2026-10-19T08Z-matrix-04-05.md), [06–08](research-2-integration-2026-10-19T08Z-matrix-06-08.md), [09–10](research-2-integration-2026-10-19T08Z-matrix-09-10.md): цепи ≤3 звеньев, версии, лицензии, переиспользование APA, оценка пользы/риска и ГОТОВО.
- [Контрааудит А](research-2-integration-2026-10-19T08Z-audit-A.md): код, версии, лицензии, API/ABI. [Контрааудит Б](research-2-integration-2026-10-19T08Z-audit-B.md): монтажный граф, дублирование и безопасность.
- [Альтернативные архитектуры, гейты, вопросы №1, восемь предложений №3](research-2-integration-2026-10-19T08Z-handoff.md).

## Главная находка: опасный Publisher без ограничителя
В [Tapir 1.5.9 NavigatorCommands.cpp L36–106](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L36-L106) пустой `selectedNavigatorItemIds=[]` оставляет `selectedLinksPtr=nullptr`; вызывается `ACAPI_ProjectOperation_Publish` без ограничения выбранных листов. `outputPath` необязателен (может использоваться сохранённый путь), успешный ответ `{}` не содержит файловых SHA. **Вердикт: будущий Publisher разрешать только с непустым whitelist, явным безопасным путём и файловым readback; сейчас не запускать.** Это статический вывод по тегу 1.5.9, не подтверждение локальной сборки 1.5.10.

## Второй контрактный риск
Официальный [Graphisoft AC29 JSON API](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html) `CloneProjectMapItemToViewMap` принимает **один** source/parent GUID, а Tapir 1.5.9 — `viewsData[]` и поэлементные результаты, без доказанной атомарности. `LayoutParameters.horizontalSize/verticalSize` измеряются в **мм**, обычные длины свойств — в **м**. Не смешивать контракты и единицы; `hasIssuedRevision` не доказывает PDF.

## Контроль исходных данных
Прочитаны очередь №3 20Z, матрица и реестр **61** кандидата, отчёт №1 07Z, PR154/159/160/162/165/168/170/173 и канон [PROJECT_PLAN revision182](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json) только чтение. У №1 07Z заявленные `cards.md` и `checks-B.md` на исследовательской ветке отсутствуют (404), использованы доступные карточки 06Z. Очередь №3 не исправлялась. Исторический PR173 saved/reopened подтверждён, но независимый ACCEPTED не доказан.

**Ни одна оценка 0–100 не является измерением ускорения.** AC29 build 5101 и локальный Tapir 1.5.10 не проверены в runtime; SDK30 не использован как доказательство SDK29.
