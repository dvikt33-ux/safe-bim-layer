# APA №1 · 01Z · SOURCE проверки 01–10

DevKit29 tag 29.3100, Graphisoft EULA. Windows11/AC29 build5101/Tapir1.5.10 NOT_VERIFIED. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=NOT_RUN. Скорость не измерялась.

**1. FindLibraries** — Вопрос: Список библиотек? Источник: [SDK29 162](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library_manager.html#L162), blob `b1aa8915bf6461c2073ae3a1ad0741a105d95558`. Контракт: `FindLibraries`. Вывод: Возвращает список Library по selector. Контрааудит: Не доказано наличие каждой GDL детали; SOURCE не LIVE. Далее: Встроенная библиотека.

**2. GetEmbeddedLibrary** — Вопрос: Встроенная библиотека? Источник: [SDK29 171](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library_manager.html#L171), blob `b1aa8915bf6461c2073ae3a1ad0741a105d95558`. Контракт: `GetEmbeddedLibrary`. Вывод: Получение embedded library. Контрааудит: Не все внешние библиотеки; SOURCE не LIVE. Далее: Поиск LibPart.

**3. FindLibParts** — Вопрос: Поиск LibPart? Источник: [SDK29 177](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library_manager.html#L177), blob `b1aa8915bf6461c2073ae3a1ad0741a105d95558`. Контракт: `FindLibParts`. Вывод: Поиск по selector. Контрааудит: Найденный объект не обязательно размещаемый; SOURCE не LIVE. Далее: Поиск по имени.

**4. GetLibPartByName** — Вопрос: Поиск по имени? Источник: [SDK29 183](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library_manager.html#L183), blob `b1aa8915bf6461c2073ae3a1ad0741a105d95558`. Контракт: `GetLibPartByName`. Вывод: Поиск имени файла. Контрааудит: Имя не GUID и не уникальный ключ; SOURCE не LIVE. Далее: Provenance детали.

**5. GetLibraryTreePathOfLibPart** — Вопрос: Provenance детали? Источник: [SDK29 189](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library_manager.html#L189), blob `b1aa8915bf6461c2073ae3a1ad0741a105d95558`. Контракт: `GetLibraryTreePathOfLibPart`. Вывод: Возвращает LibraryTreePath. Контрааудит: Путь не гарантирует лицензию; SOURCE не LIVE. Далее: Метаданные GSM.

**6. GetGSMObjectOfLibPart** — Вопрос: Метаданные GSM? Источник: [SDK29 195](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library_manager.html#L195), blob `b1aa8915bf6461c2073ae3a1ad0741a105d95558`. Контракт: `GetGSMObjectOfLibPart`. Вывод: Возвращает GSMObject. Контрааудит: Не BIM элемент; SOURCE не LIVE. Далее: Отсутствующая библиотека.

**7. IsMissing** — Вопрос: Отсутствующая библиотека? Источник: [SDK29 173](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library.html#L173), blob `943b5cccea7b952e72a18061e1bf7b850796828b`. Контракт: `IsMissing`. Вывод: Флаг отсутствия файла/TW ресурса. Контрааудит: Не проверяет каждую деталь; SOURCE не LIVE. Далее: Формат .libpack.

**8. IsPackage** — Вопрос: Формат .libpack? Источник: [SDK29 185](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library.html#L185), blob `943b5cccea7b952e72a18061e1bf7b850796828b`. Контракт: `IsPackage`. Вывод: Распознаёт пакет. Контрааудит: Не относится ко всем каталогам; SOURCE не LIVE. Далее: Идентификатор пакета.

**9. GetPackageID** — Вопрос: Идентификатор пакета? Источник: [SDK29 188](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library.html#L188), blob `943b5cccea7b952e72a18061e1bf7b850796828b`. Контракт: `GetPackageID`. Вывод: Package ID. Контрааудит: Не GUID размещённого элемента; SOURCE не LIVE. Далее: Минимальная версия.

**10. GetPackageMinACVersion** — Вопрос: Минимальная версия? Источник: [SDK29 197](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library.html#L197), blob `943b5cccea7b952e72a18061e1bf7b850796828b`. Контракт: `GetPackageMinACVersion`. Вывод: Возвращает UInt32. Контрааудит: Не LIVE совместимость; SOURCE не LIVE. Далее: минимальная сборка и зависимости .libpack.

