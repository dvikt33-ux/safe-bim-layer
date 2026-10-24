# APA29 — исследование исходных контрактов Tapir, проход 02 (18.10.2026)

**Метод:** чтение исходников официального тега Tapir `1.5.9` через подключённый GitHub; никаких вызовов Archicad, установок или изменений модели. Поисковые веб-запросы за последние 30 дней точных совпадений не дали; поэтому первичным доказательством служат исходники тега, а не выдача поиска.

## 1. Публикация: точный контракт
[NavigatorCommands.cpp, tag 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp)

`PublishPublisherSet` — входная JSON-схема: обязательный `publisherSetName` (непустая строка), необязательные `outputPath` (непустой локальный/LAN путь) и `selectedNavigatorItemIds` (список элементов дерева публикации); `additionalProperties: false`. Реализация сопоставляет имя с GUID Publisher Set, затем вызывает `ACAPI_ProjectOperation_Publish(&publishPars, selectedLinksPtr)`. При неверном имени возвращает ошибку; при ошибке публикации — `Publishing failed. Check output path!`.

**Вывод:** готовый нативный программный вызов публикации есть в исходниках тега 1.5.9. Он не равнозначен `SaveProject`; не утверждать отсутствие побочных эффектов или невозможность перезаписи выходных файлов. **Источник: PASS; локальный INSTALLED/LIVE/ACCEPTED: NOT_VERIFIED**.

## 2. Иерархические группы: пример
[create_groups.py, tag 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/create_groups.py)

Пример вызывает `RunTapirCommand("CreateGroups", {"elementGroups": element_groups})`, извлекает `groupGuids`, исключает результаты с `error`, затем вызывает `CreateGroups` ещё раз с `{"elementGroups": [{"elements": valid_groups}]}` для создания надгруппы.

**Вывод:** иерархия групп реализована готовой командой; это **не** доказательство группового Multiply, сохранения GUID после копирования, поведения при разгруппировке или наличия команды в локальной сборке 1.5.10. Сопоставить с PR #159/#162 до добавления кода.

## 3. Следующие строго определённые вопросы
- **P0 / исследователь №1:** прочитать C++-схему `CreateGroups` и `GetGroupsOfElements` в теге 1.5.9 и сопоставить с примером, обработкой ошибок и существующим APA. ГОТОВО: таблица JSON и возвратов, а также перечень недостающих операций.
- **P0 / исследователь №2:** проверить наличие `PublishPublisherSet` и его схему именно в локальной 1.5.10, определить риск перезаписи файлов по `outputPath` и существующим настройкам Publisher Set. ГОТОВО: безопасный read-only preflight, без исполнения публикации.

**Ограничение:** исходники и пример подтверждены, но BUILD, INSTALLED, LIVE, ACCEPTED не проверялись. Основной план №182, main, PLN, APX и Archicad не изменялись.
