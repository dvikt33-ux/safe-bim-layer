# APA — бесплатные готовые расширения, сервисы и библиотеки (проверка 2026-10-14)

**Статус:** SOURCE_RESEARCH / NOT_INSTALLED / NOT_TESTED_IN_APA.
**Точка публикации:** ветка `research/apa-ai-candidates-registry-20261014` → draft PR #78 → research hub.
**Цель:** расширять APA / Archicad 29 быстро, без студенческой лицензии, новой платной подписки и без дублирования работающих модулей.

Разделять **[A] готовые функции в интерфейсе Archicad** от **[B] библиотек с программным API для APA** и **[C] отдельных внешних приложений**. Установить чужой APX ≠ автоматически интегрировать его функции в APA JSON/SceneWriter. Каждый результат требует теста на изолированном проекте, source SHA, readback и оценки безопасности.

## I. Приоритетные для быстрого испытания

| Приоритет | Кандидат / официальный URL | Тип и приобретённая функция | Установка/интеграция | Ограничения / критерий |
|---|---|---|---|---|
| P0 | [IfcTester](https://docs.ifcopenshell.org/ifctester.html) | [B] IFC → IDS-валидация и отчёты HTML/BCF | `pip install ifctester`; адаптер к уже существующему IFC-потоку APA | Требуются корректные IDS и IFC; **не российский СП-чекер**. Проверить 1 заранее известный PASS/FAIL. |
| P0 | [IfcDiff](https://docs.ifcopenshell.org/ifcdiff.html) | [B] Сравнение версий IFC по GlobalId, геометрии, свойствам и отношениям | `pip install ifcdiff`; read-only сравнение файлов до/после | Вариация геометрического представления без изменения формы может считаться изменением. Не путать с native PLN diff. |
| P0 | [IfcClash](https://docs.ifcopenshell.org/ifcclash.html) | [B] Поиск пересечений между наборами элементов в IFC | `pip install ifcclash`; JSON-конфигурация групп | Только IFC; тест на эталонном столкновении + отрицательная контрольная пара. Не дублировать существующий нативный clash без доказанной пользы. |
| P0 | [buildingSMART bSDD API](https://technical.buildingsmart.org/services/bsdd/using-the-bsdd-api/) | [B] Получение классификаций, классов и свойств по API вместо AI-выдумок | GET API публичных методов без учётной записи, кешировать версии и ответ; OpenAPI: https://github.com/buildingSMART/bSDD/blob/master/Documentation/bSDD%20OpenAPI.yaml | Не нормативная база СП; нет гарантии покрытия региональных классификаций. |
| P1 | [BIMquants Lite](https://www.bimquants.com/lite/index.html) | [A] Объёмы, сметы, формулы по GUID, синхронизация и XLSX/SQL в Archicad 29 | Готовый Windows installer или APX | Бесплатно навсегда, включая коммерческое применение по заявлению автора. **Программный интерфейс для APA не подтверждён**; только самостоятельная функция в AC. |
| P1 | [Graphisoft Goodies 29](https://www.graphisoft.com/fr-fr/downloads/add-ons/goodies/) | [A] Пакет Mesh to Roof, Profiler, Accessories, Check Duplicates, PolyCount и др. | Один официальный установщик, точно версия 29 + язык сборки | Старый неподдерживаемый код, возможны сбои; API-команды APA не гарантированы. |
| P1 | [Speckle Archicad](https://speckle.systems/integrations/archicad/) / [pricing](https://speckle.systems/pricing/) | [A + облако] обмен BIM и метаданными; просмотр/дешборд вне Archicad | Готовый коннектор для AC 27/28/29 | Free Explore: **1 проект, 3 пользователя, 30 дней истории**, базовые проверки; Speckle Automate и масштабные функции платные. Не использовать как бесплатную бесконечную production-базу. |

## II. Полезные по ситуации

| Приоритет | Кандидат | Роль и бесплатность | Оговорка |
|---|---|---|---|
| P1 | [IfcCSV](https://docs.ifcopenshell.org/ifccsv.html) | [B] Выгрузка/редактирование IFC свойств/ведомостей CSV/XLSX | Независимо тестировать сохранность GUID и типов данных. |
| P1 | [Bonsai](https://bonsaibim.org/) / [Blender extension](https://extensions.blender.org/add-ons/bonsai/versions/) | [C] Полноценная визуальная проверка, редактирование и инспекция IFC бесплатно и open-source | Отдельная программа Blender, **не** Archicad APX; версии Blender/Bonsai должны совпадать. |
| P2 | [D5 Render Community + LiveSync](https://www.d5render.com/workflow/archicad) | [C + A] Рендер в реальном времени; официальный плагин для AC 21–29 | Community **только для некоммерческого использования**, отдельная программа + GPU; не расширяет BIM API APA. |
| P2 | [PVGIS v6](https://photovoltaic-geographic-information-system.ec.europa.eu/api/v6/docs) | [B] Публичный API солнечного излучения / оценки PV; добавить модуль по геокоординатам | Не замена расчёту инсоляции помещений по СП; проверить изменения формата v6 с 2026-07-23. |
| P2 | [Open-Meteo](https://open-meteo.com/) | [B] Климатические данные для предпроектного анализа | Бесплатный API без ключа до 10 тысяч запросов/сутки **только для некоммерческого использования**; требуется атрибуция. |
| P2 | [OSM Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) | [B] Дороги, остановки, окружение участка, контур окружения для генплана | Публичные серверы ограничены; данные OSM неполны, **не подтверждают юридические границы земельных участков**. |
| P2 | [Favorites Palette 2.0](https://community.graphisoft.com/t5/General-discussions/Favorites-Palette-2-0-Free-add-on-for-Archicad-29/m-p/709854) | [A] Готовая APX-палитра повторно используемых групп объектов/ламп; обновление поддерживает подписи и 2D | Сторонний бинарник с внешнего Drive: **проверить provenance/хеш/подпись, установка на копии**; нет подтверждённого API. |
| P2 | [BIMrender](https://github.com/malamalca/BIMrender) | [A + C] Бесплатный open-source APX для AI-рендера, поддерживает локальный Forge/A1111 HTTP img2img | Локальный backend требует отдельной настройки, 8 ГБ VRAM — нижняя граница; геометрия изображения может меняться. В проекте API-ключи сохраняются в PLN preferences: **риск утечки при передаче PLN**, перед использованием изучить и изолировать. |

## III. Отдельно исследовать, НЕ устанавливать в рабочий Archicad сейчас

- [alesdev88/Archicad-MCP](https://github.com/alesdev88/Archicad-MCP) — AC29, готовый .mcpb пакет для Claude Desktop (запуск одним файлом) с QA по YAML и API. **Критический известный риск:** автор предупреждает, что `GetPropertyValuesOfElements` способен аварийно завершить Archicad 29. Есть опасный режим записи, а удалённое подключение ChatGPT требует защищённого HTTPS-туннеля. Для APA уже существует управляющий Writer/bridge; изучить реализации только read-only в отдельном процессе и тестовом PLN.
- [lgradisar/archicad-mcp](https://github.com/lgradisar/archicad-mcp) — MIT, Archicad 25–29, Tapir 1.5.9, `uv`, переключаемый safe/readonly, ~250 Tapir-инструментов; **возможен дублирующий стек**. Не заменять контролируемый SceneWriter без независимого аудита.
- [IfcMCP](https://docs.ifcopenshell.org/ifcmcp.html) — бесплатный MCP-сервер для IFC (не PLN), `pip install 'ifcmcp[mcp]'`. Возможен безопасный эксперимент с read-only копией IFC; редактирование IFC необходимо блокировать.
- [Graphisoft Library Part Maker 29](https://www.graphisoft.com/en-it/downloads/add-ons/library-part-maker/) — скачивание есть, но автор указывает SSA / Trial / EDU как условия лицензирования. **Не считать гарантированно бесплатной возможностью для данной лицензии.**
- [Graphisoft Rhino–Grasshopper–Archicad Live Connection 29](https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/) — коннектор бесплатный, но необходим отдельно **Rhino 7/8**, не бесплатный на постоянной основе, поэтому не проходит критерий.
- [Solibri Connection 29](https://www.graphisoft.com/en-us/downloads/add-ons/solibri/) — коннектор устанавливается, но **Solibri Anywhere не поддерживается**; зависит от лицензии Solibri, значит не бесплатный законченный контур.
- [D5 commercial restriction](https://www.d5render.com/service-agreement): Community — non-commercial, не использовать для платных архитектурных проектов.
- [OpenTopography](https://www.opentopography.org/developers): ключ бесплатный для индивидуальных тестов, но встраивание API в **коммерческое ПО требует Enterprise-ключ**; не включать в APA как свободную распространяемую интеграцию без разрешения.

## IV. Что уже присутствует в нашем APA

- Tapir / официальный Archicad JSON API / C++ Add-On и SceneWriter — **существующий путь записи**, не ставить поверх них альтернативный неконтролируемый агент.
- IFC / CP-SAT — отдельные работающие исследованные модули, но **IfcDiff/IfcTester/IfcClash могут добавить независимые проверки**.
- Реестр controller содержит задачи `APA-P10.A02.S03` (MCP/IFC альтернативы) и `APA-P50.A02.S01` (каталог инструментов) — не создавать дубли в `PROJECT_PLAN.json`, исследование прикрепить к ним после независимого аудита.

## V. Порядок быстрых испытаний и критерии

1. **Нулевой риск для AC:** локально на копии IFC запустить IfcDiff + IfcTester + IfcClash; отчет `PASS/FAIL` с первичными артефактами и source hash. Нативный PLN не менять.
2. **Публичные API:** проверить bSDD на 3 известных IFC-классах и 3 свойствах; сохранить source URI, версию словаря и raw JSON; не выдумывать нормативные соответствия.
3. **На копии тестового PLN:** Graphisoft Goodies и BIMquants Lite с конкретным Windows Archicad 29 build, проверить запуск/сохранение/переоткрытие, GUID. Если APX меняет основной проект или Archicad падает — остановиться.
4. **Отдельный эксперимент:** Speckle Free Explorer на обезличенной модели, проверить фактическую поддержку свойств и синхронизации, API, число задач/моделей, доступность функции после 30 дней.
5. **Только после risk-audit:** MCP расширения read-only, без публикации наружу и без модификации PLN.

Для каждого кандидата обязательные поля: upstream URL, лицензия и версия/ревизия, совместимость AC29, реально бесплатные функции и ограничения, отдельный путь UI/API, установка и риск, сравнение с существующим APA модулем, план теста, статус `NOT_TESTED`. Нет реальных установок, встроенных интеграций или проверок на ноутбуке пользователя в данном проходе.

**Решение по интеграции не принимать автоматически.** Это SOURCE_RESEARCH, не `DONE_PUBLISHED` controller-задачи. Факты о наличии продукта/заявленной функциональности основаны на ссылках первоисточников; тесты APA пока не проводились.
