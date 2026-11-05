# Archicad 30 RUS — локальный MCP и JSON API, наблюдения на BIM-модели из 18 типов (2026-10-16)

## 0. Статус и происхождение

- **Класс:** USER_SUPPLIED_RUNTIME_LOG / USER_REPORTED; не независимая нативная проверка исполнителем и не SOURCE_VERIFIED Graphisoft SDK.
- **Проект:** `тестовый файл все типы+30`; файл PLN не публиковался, его байты и SHA не исследовались.
- **Среда из логов пользователя:** Archicad 30 RUS, build 3001, Windows PowerShell, локальный JSON API `http://127.0.0.1:19725`.
- **Задача:** независимое исследование AC30 для возможного будущего использования в APA; **не** объявлять выполнение текущего S-ID, не менять PROJECT_PLAN, не переносить разработку с Archicad 29.
- **Границы:** только штатные команды чтения; операции записи, SDK-совместимость, независимый офлайн-тест с отключённым интернетом не выполнялись.

## 1. Обнаружение интерфейсов

Локальный MCP-сервер через установленный Node.js сообщил `serverInfo.name = "Archicad MCP Server"`, `version = "1.0.0"`, протокол `2025-06-18`. `tools/list` вернул **ровно одну** команду: `GetArchicadInstances`. После сохранения пустого тестового PLN команда обнаружила запущенный Archicad. Из самого описания `GetArchicadInstances` следовало, что при непустом списке экземпляров и единственном MCP-инструменте ограничение связано с лицензией/подпиской. Это сообщение **сервера**, а не самостоятельно проверенное состояние лицензии.

Между первым вызовом с `instances: []` и последующим появлением экземпляра пользователь сохранил проект: временная связь подтверждена, но причинная связь исключительно с сохранением PLN не доказана.

Штатный **JSON API** независимо ответил `succeeded: true` на:
- `API.IsAlive`, `API.GetProductInfo`, `API.GetAllElements` в начальном тестовом проекте;
- `API.GetElementsByType`, `API.GetTypesOfElements` на реальной стене;
- `API.Get2DBoundingBoxes`, `API.Get3DBoundingBoxes`, `API.GetComponentsOfElements`, `API.GetAllPropertyIdsOfElements` на реальной стене.

Для тестовой стены осевой bounding box составлял **5.00 × 0.30 × 3.00 м**; обнаружено два component ID и **442 property ID** (не 442 проверенных значения). Эти результаты относятся к предыдущему маленькому PLN и не заменяют тесты на 18 типах.

## 2. Текущая тестовая модель: полный типовой инвентарь

По логу пользователя запрос `API.GetAllElements` вернул **678** элементов, чтение `API.GetTypesOfElements` пакетами по 100 вернул **678** разрешённых типов, **0** ошибок. Таблица сгруппирована по `elementType`; это не доказательство возможности редактировать каждый тип.

| Тип JSON API | Количество |
|---|---:|
| Column | 156 |
| Morph | 122 |
| Wall | 114 |
| Window | 108 |
| Beam | 69 |
| Roof | 27 |
| Slab | 26 |
| Door | 16 |
| Object | 10 |
| Mesh | 8 |
| Stair | 6 |
| Skylight | 5 |
| CurtainWall | 3 |
| Lamp | 3 |
| Shell | 2 |
| Railing | 1 |
| Zone | 1 |
| Opening | 1 |
| **Итого** | **678** |

**18 типов, 678/678 классифицировано, 0 ошибок**. Уникальность GUID, полнота видимых объектов и физическая целостность проекта ещё не подтверждены независимым readback.

## 3. Разграничение статусов

| Claim | Статус |
|---|---|
| На конкретном пользовательском ПК MCP handshake и tools/list успешны | USER_REPORTED_PASS |
| MCP доступен в полном объёме | NOT_VERIFIED; доступна только команда GetArchicadInstances |
| Штатный локальный JSON API читает модель AC30 | USER_REPORTED_PASS |
| В текущем тестовом PLN 678 элементов / 18 типов по JSON API | USER_REPORTED_PASS |
| На каждом из 18 типов доступны геометрия, компоненты, свойства | NOT_TESTED |
| JSON API позволяет нативно менять параметры всех 18 типов | NOT_TESTED |
| AC30 расширяет функциональность по сравнению с AC29 | NOT_VERIFIED |
| MCP и JSON API работают при физически отключённой сети | NOT_TESTED |
| Изменения в рабочем APA 29 / PLN / APX / main | NONE в рамках описанных read-only команд |

## 4. Следующий минимальный доказательный тест

1. На **той же модели** по одному элементу каждого типа безопасно запросить `Get3DBoundingBoxes`, `GetComponentsOfElements`, `GetAllPropertyIdsOfElements`; фиксировать точные API-ошибки отдельно по типу.
2. Не трактовать отсутствие bounding box для Railing как повреждение модели.
3. После read-only матрицы сопоставить реальные схемы и поддерживаемые функции SDK/API 29 vs 30; результаты не переносить между версиями без испытаний.
4. Для операций записи использовать **отдельную копию** тестового PLN, предварительный снимок GUID/параметров, разрешение на запись и независимый readback.

**Не выполнены:** локальный эксперимент шага 1 на 18 типах, сравнение SDK/API с Archicad 29, тесты записи, отключение интернета. Никакой S-ID не закрыт.

## 5. Evidence / воспроизводимость

Источники измерений — текстовые ответы и консольные логи, переданные пользователем в ChatGPT 2026-10-16 в диалоге по локальному MCP/JSON API Archicad 30. Прямого удалённого доступа к компьютеру, исходному PLN или исходному stderr/log-файлу не было. Данные и результаты зафиксированы как **USER_REPORTED**, а не как независимая аттестация. Указанные адрес localhost/порт относятся к времени тестов и не гарантированы в последующих запусках.

Отчёт является отдельной заметкой с результатами наблюдений; он не является publisher receipt, не обновляет канонический PROJECT_PLAN и не означает DONE_PUBLISHED.


## 6. Дозапись — матрица чтения по одному представителю всех 18 типов

**Происхождение:** консольный вывод пользователя из Archicad 30 RUS, API порт 19725; USER_REPORTED. Использован read-only script: три вызова `Get3DBoundingBoxes`, `GetComponentsOfElements`, `GetAllPropertyIdsOfElements` на один элемент каждого из 18 типов (всего 54 вызова, нет исключений API).

| Тип | Count | 3D Bounding Box | Components одного элемента | Показанное PropertyIDs |
|---|---:|---|---:|---:|
| Beam | 69 | PASS | 1 | 0* |
| Column | 156 | PASS | 1 | 0* |
| CurtainWall | 3 | PASS | 153 | 0* |
| Door | 16 | PASS | 1 | 0* |
| Lamp | 3 | PASS | 1 | 0* |
| Mesh | 8 | PASS | 1 | 0* |
| Morph | 122 | PASS | 1 | 0* |
| Object | 10 | PASS | 1 | 0* |
| Opening | 1 | NO_DATA | 0 | 0* |
| Railing | 1 | NO_DATA | 1060 | 0* |
| Roof | 27 | PASS | 2 | 0* |
| Shell | 2 | PASS | 2 | 0* |
| Skylight | 5 | PASS | 1 | 0* |
| Slab | 26 | PASS | 1 | 0* |
| Stair | 6 | NO_DATA | 47 | 0* |
| Wall | 114 | PASS | 1 | 0* |
| Window | 108 | PASS | 1 | 0* |
| Zone | 1 | PASS | 1 | 0* |

**Критическая ошибка в тестовом коде подсчёта PropertyIDs:** использовано `$r.propertyIdsOfElements[0].propertyIds`, однако структура фактического JSON-ответа из предыдущего пользовательского лога: `$r.propertyIdsOfElements[0].propertyIdsOfElement.propertyIds`. Следовательно все 18 значений `0*` являются **INVALID_MEASUREMENT** и не могут интерпретироваться как отсутствие свойств. Требуется повторить исключительно запросы свойств с правильным путём; остальные вызовы не повторять без причины. Предыдущая тестовая стена на другом PLN возвращала 442 property ID.

3D Bounding Box вернулся для **15/18 типов**. NO_DATA для Opening, Railing, Stair — пустое поле в успешно выполненном API-запросе, а не ошибка API или признак повреждения объекта. Составные компоненты обнаружены у Railing (1060), CurtainWall (153), Stair (47), Shell и Roof (по 2). Это **чтение component ID**, не проверка возможности изменять дочерние части.

**После этой дозаписи:**
- Классификация 678 / 678 / 18 типов: USER_REPORTED_PASS.
- 3D Bounding Box 15 / 18: USER_REPORTED_PASS_PARTIAL.
- GetComponentsOfElements: USER_REPORTED_PASS_RESPONSE, число ID для выбранных экземпляров показано в таблице.
- GetAllPropertyIdsOfElements: API-вызовы без ошибок, но **все измеренные количества INVALID_MEASUREMENT**.
- Нативная геометрия, обновление параметров/материалов, лицензия MCP, отличие AC29 от AC30: NOT_VERIFIED.
- Файл PLN, APX, main: без изменений в рамках описанных read-only операций; ни один контролируемый S-ID не переводится в DONE.

### Минимальный следующий тест

1. Существующие GUID примеров каждого типа → только исправленный `GetAllPropertyIdsOfElements`; сохранить число свойств по типам.
2. Необязательно, но полезно: `Get2DBoundingBoxes` только для Opening/Railing/Stair, чтобы различить отсутствие 3D и полный отказ bbox.
3. Без новых проверок write-команд до безопасной копии PLN и отдельного допуска.


## 7. Дозапись — 2D Bounding Box для исключений (USER_REPORTED)

Пользователь представил вывод исправленного диагностического скрипта для файла `тестовый файл все типы+30`, локальный JSON API `127.0.0.1:19725`.

| Тип | 3D Bounding Box по предыдущему тесту | 2D Bounding Box, новый тест |
| --- | --- | --- |
| Opening | NO_DATA | PASS |
| Railing | NO_DATA | PASS |
| Stair | NO_DATA | PASS |

Обработка прошла по трем названным типам, пользовательский вывод: `2D EXCEPTION TYPES: 3`, `MODEL WRITES: 0`, `FINISHED`.

Вывод: API возвращает 2D-границы для всех трёх типов, где ранее отсутствовали 3D-границы. Это не подтверждает наличие полной 3D-геометрии или нативную возможность редактирования каждого типа.

Вывод `PROPERTY TYPES: 18` подтверждает только количество **сформированных записей в результирующей переменной** `$propertyResults`. Сам список `Type / PropertyIDs / Status` пока **не представлен**. Корректное число идентификаторов свойств и количество PASS/ERROR для этих 18 вызовов остаются **NOT_VERIFIED**. Не утверждать, что все свойства прочитаны или что все 18 запросов прошли успешно.

Доказательство: консольный текст пользователя в том же диалоге; независимый доступ к ПК отсутствовал. Модель только читалась, без заявлений об изменении файлов PLN/APX. Сводка не переводит S-ID в DONE.

## 8. Исправленная матрица PropertyIDs — 18/18 PASS (USER_REPORTED)

**Источник доказательства:** последующий полный консольный вывод пользователя от 2026-10-16 с командой `$propertyResults | Format-Table Type, PropertyIDs, Status`. Использована исправленная структура `propertyIdsOfElements[0].propertyIdsOfElement.propertyIds`.

| Тип | PropertyIDs у выбранного экземпляра | Статус |
|---|---:|---|
| Beam | 475 | PASS |
| Column | 492 | PASS |
| CurtainWall | 280 | PASS |
| Door | 309 | PASS |
| Lamp | 251 | PASS |
| Mesh | 256 | PASS |
| Morph | 238 | PASS |
| Object | 251 | PASS |
| Opening | 264 | PASS |
| Railing | 218 | PASS |
| Roof | 351 | PASS |
| Shell | 321 | PASS |
| Skylight | 279 | PASS |
| Slab | 335 | PASS |
| Stair | 274 | PASS |
| Wall | 442 | PASS |
| Window | 308 | PASS |
| Zone | 308 | PASS |

- **18/18 PASS**, `Group-Object Status` сообщил `PASS 18`.
- Сумма 18 чисел = **5652** (арифметическая сумма количеств ID по 18 разным представителям типов, **не** число уникальных свойств в проекте: IDs разных типов могут пересекаться).
- Успех запроса ID **не подтверждает** значения, редактируемость, уникальность property IDs, классификации, GDL-параметры и нативную геометрию.
- При проверке 3D границ получили 15/18, для Opening/Railing/Stair дополнительно получены 2D границы 3/3. Это отдельные операции с отдельными статусами.
- Подтверждение из текущего пользовательского лога: модель не изменялась через диагностический скрипт; независимый diff PLN не проводился.
- **Следующая проверка:** сравнение с AC29 SDK/JSON API на основании текущих проверенных функций и контрактов, только затем минимальные целевые тесты новых возможностей на копии PLN. Не заявлять уникальные функции AC30 без сравнительного исходника/проверки.


## 9. Официальный Graphisoft SDK 30: отличия для приоритизации APA (SOURCE_VERIFIED, не LIVE_PASS)

**Первичный источник:** Graphisoft [New API features in Archicad 30](https://graphisoft.github.io/archicad-api-devkit/newfeatures.html), просмотрен 2026-10-16. Этот перечень описывает функции, заявленные **новыми для AC30**. Статус ниже относится к документации, а не к реальной работе функций в установленном AC30.

| Подсистема | Новая возможность/изменение SDK 30 | Значение для APA | Статус |
|---|---|---|---|
| 3D изображения | `ACAPI_View_GetCurrentImage`, `API_ImageSource`: текущий 3D или render window в `NewDisplay::NativeImage` | нативный экспорт изображения для проверки видов | SOURCE_VERIFIED / LOCAL_NOT_TESTED |
| Project Info | `ACAPI_ProjectInfo_GetGroups/GetFields/GetField/CreateField/SetFieldValue` и проч. | машиночитаемые и редактируемые реквизиты документации, зависимость полей | SOURCE_VERIFIED / LOCAL_NOT_TESTED |
| Атрибуты | `ACAPI_Attribute_GetCreationInfo`, `API_AttributeCreationInfo`, новые параметры `ACAPI_Attribute_Create/CreateExt` | provenance / источник создания атрибута | SOURCE_VERIFIED / LOCAL_NOT_TESTED |
| 3D события | `API_IView3DSettingsEventHandler` и `NotifyView3DSettingsEvent` | отслеживание смены проекции, фильтров, навигации | SOURCE_VERIFIED / LOCAL_NOT_TESTED |
| MEP | `GetElemId`, `GetPorts`, port defaults getters | облегчённое чтение MEP-портов и defaults | SOURCE_VERIFIED / LOCAL_NOT_TESTED |
| Publisher | новые callbacks и `ACAPI_AddOnIntegration_InstallPublisherSaveWithOptionMethod`, `...WithTranslatorMethod` и другие | новые сценарии публикации, но обязательная адаптация | SOURCE_VERIFIED / LOCAL_NOT_TESTED |
| Размеры | независимые перья/линии выносок и зазоры `API_DimElem` | гибкое оформление документации | SOURCE_VERIFIED / LOCAL_NOT_TESTED |
| Graphical Overrides | `ACAPI_GraphicalOverride_GetActualOverrideCombination/SetActualOverrideCombination` | проверка и управление актуальной комбинацией отображения | SOURCE_VERIFIED / LOCAL_NOT_TESTED |

**Breaking changes:** удалена `ACAPI_AddOnIntegration_InstallPublisherSaveMethod`; заменены `SaveProc` и `PublishFormatMethods::saveProc`. Кроме того, изменены отдельные сигнатуры, появилось несколько deprecation. Нужен source-level migration review при будущей AC30-компиляции.

**Совместимость:** официальный Graphisoft [API Compatibility](https://graphisoft.github.io/archicad-api-devkit/apicompatibility.html) прямо указывает отсутствие бинарной совместимости между основными версиями Archicad: существующий AC29 APX нельзя считать загружаемым в AC30 без пересборки с подходящим DevKit. И [Getting Started](https://graphisoft.github.io/archicad-api-devkit/) перечисляет для AC29 и AC30 Visual Studio 2022 v143, но разные DevKit versions. Это не означает подтверждённую сборку APA 30.

**Public MCP:** официальный Graphisoft [Manage BIM elements via MCP](https://help.graphisoft.com/AC/30/INT/Topics/001_GettingHelp/AI_Assistant/ManageElementsMCP.html) ограничивает инструменты тарифами Collaborate и Max. Реальный пользовательский `tools/list` вернул только GetArchicadInstances; обход лицензии не исследовался. Штатный JSON API независимо работает.

**Следующий выбор:** сперва сравнить с реальным инвентарём APA AC29, приоритет 3D view-image-export и Project Info; затем, **только после стабилизации AC29 и явного разрешения**, экспериментальная AC30 APX-сборка на отдельной ветке/стенде. Новая функция в документации не равно новая функциональность подключённая к APA.
