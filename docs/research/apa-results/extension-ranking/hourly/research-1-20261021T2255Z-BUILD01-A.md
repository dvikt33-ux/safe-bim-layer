# APA №1 | BUILD-01 | 2026-10-21 22:55 UTC | SOURCE 01–10

**Воздействие:** обнаружен штатный `IsAddOnCommandAvailable` для G0 без исполнения CREATE; G0 всё ещё BLOCKED до runtime APX SHA/PLN/схемы. Новых PASS=0, здание не создано. [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192).

Конфигурация Windows11/AC29 build5101/Tapir1.5.10 заявлена, но не проверена на локальной машине. Важность экспертная; лицензия Graphisoft Python Apache, Tapir MIT, пользовательский репозиторий без лицензионной оценки. Каждая строка — отдельный проверенный контрактный вопрос, НЕ запуск Archicad.

### 01 · G0 · Чем адресовать установленную команду без CREATE?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** Официальный AC29 AddOnCommandId(commandNamespace,commandName), клиент Graphisoft 29.3000/Apache: оба поля — строки, не один name.
**Решение/ограничение и №2:** Пара {tapir,CreateSlabs} должна проверяться как пара, не по имени файла; №2: сверить namespace и имена из pinned schema.

### 02 · G0 · Есть ли штатная проверка регистрации команды?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** AC29 IsAddOnCommandAvailable(AddOnCommandId) возвращает bool, без выполнения команды; официальный Graphisoft/Apache.
**Решение/ограничение и №2:** Прямой read-only G0-пробник для каждого обязательного Create*; true НЕ доказывает корректность schema/APX SHA. №2: список обязательных команд и результаты.

### 03 · G0 · Можно ли считать IsAlive достаточным G0?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** AC29 IsAlive() возвращает bool соединения; Graphisoft/Apache.
**Решение/ограничение и №2:** Нет: не доказывает номер сборки, открытый PLN или загруженный Tapir. №2: IsAlive только первым фильтром.

### 04 · G0 · Безопасно ли ExecuteAddOnCommand использовать для проверки наличия?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** AC29 ExecuteAddOnCommand исполняет зарегистрированную команду; Graphisoft/Apache.
**Решение/ограничение и №2:** Для Create*/Save/Open не использовать как probe. №2: IsAddOnCommandAvailable, затем только разрешённые read-only вызовы.

### 05 · G0 · Равны ли 262 команды из PR74 живой регистрации?
**SOURCE:** https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json
**Факт/версия:** Pinned tapir-scene-live.json, immutable PR74, 262 записей, api=tapir, версии отдельных команд отличаются (например GetAddOnVersion=0.1.0, CreateWindows=1.4.0); лицензия пользовательского репозитория не проверена.
**Решение/ограничение и №2:** Это каталог, не live registration и не APX binary SHA. №2: разделить SCHEMA_SNAPSHOT/COMMAND_AVAILABLE/APX_SHA.

### 06 · G0 · Достаточен ли GetProductInfo для APX SHA?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** AC29 GetProductInfo возвращает version/build/language запущенного Archicad; Graphisoft/Apache.
**Решение/ограничение и №2:** Сверить build=5101, но APX SHA считать отдельным требованием файлового read-only манифеста. №2: не объявлять RUNTIME_READY по GetProductInfo.

### 07 · G1 · Есть ли официальный read-only способ получить дерево этажей?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** AC29 GetNavigatorItemTree(NavigatorTreeId) возвращает NavigatorTree; Graphisoft/Apache.
**Решение/ограничение и №2:** Получить идентификаторы навигатора; они не заменяют floorIndex/floorId Tapir. №2: построить таблицу сопоставления без SetStories.

### 08 · G1 · Можно ли проверить тип найденного navigator item?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** AC29 GetNavigatorItemsType(ids) возвращает type либо ошибку на каждый ID; Graphisoft/Apache.
**Решение/ограничение и №2:** Отфильтровать именно Story items перед сопоставлением с native story bindings. №2: сохранить ошибки как BLOCKED_MISMATCH.

### 09 · G1 · Дают ли story navigator items абсолютные отметки Tapir?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** AC29 GetStoryNavigatorItems(ids) возвращает детали story items; Graphisoft/Apache; контракт не обещает Tapir floorId/elevation.
**Решение/ограничение и №2:** Не заменять GetStories. №2: crosswalk navigator IDs↔index/elevation, при отсутствии доказательства не связывать автоматически.

### 10 · G0 · Как отличить доступность команды от соответствия входной схеме?
**SOURCE:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Факт/версия:** IsAddOnCommandAvailable даёт только bool; pinned schema хранит JSON input/returns; два независимых официальных/immutable источника.
**Решение/ограничение и №2:** №2: отдельные результаты COMMAND_PRESENT и SCHEMA_MATCH; не принимать true за готовность CREATE.

**Контроль:** 10 SOURCE, OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0/0/0/0/0. MODEL_MODE_NOT_VERIFIABLE.
