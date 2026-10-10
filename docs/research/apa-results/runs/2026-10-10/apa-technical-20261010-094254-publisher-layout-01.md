# APA-DOC-PIPELINE-01 — Publisher и Layout
Дата: 2026-10-10. Phase: SOURCE; LIVE: NOT_VERIFIED.

В исходниках Tapir 1.5.9 уже реализованы команды PublishPublisherSet (0.1.0), CreateLayout и CreateDrawings (1.4.0). Писать новый экспортёр для MVP преждевременно.

Риск: при selectedNavigatorItemIds=[] в PublishPublisherSet указатель selectedLinksPtr остаётся nullptr, что приводит к публикации всего набора. Схема NavigatorItemIds не содержит minItems. Требуется fail-closed проверка до записи.

SDK 29.3100: ACAPI_ProjectOperation_Publish является complete operation и не может выполняться внутри undoable/non-undoable command.

Источники:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/DocumentCreationCommands.cpp
- https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___project_operation.html

Read-only тест: проверить регистрацию команд установленного APX, прочитать GetNavigatorItemTree для PublisherSets, LayoutBook и PublicViewMap; не вызывать Create или Publish. PASS — GUID/типы/деревья соответствуют проекту; FAIL — несовпадение или отсутствие команд.

Архитектуры: A — повторное использование Tapir + проверка аргументов + readback (предпочтительно); B — новый C++ адаптер SDK29 (больше сборки и рисков). Производительность и экономия в часах NOT_MEASURED. Вопрос аудитору: совпадает ли контракт с установленным Tapir 1.5.10?
