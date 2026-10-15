# Archicad 30 Public MCP — лицензионные условия, загрузка и самостоятельные локальные альтернативы
Дата: 2026-10-16; статус **SOURCE_RESEARCH**; установка и локальные испытания альтернатив **NOT_TESTED**.

## 0. Цель, границы, режим
- **Цель:** ответить на вопрос, можно ли «докачать» полный официальный MCP Graphisoft в локальной инсталляции Archicad 30 (в том числе через иную сборку), либо получить эквивалентную функцию через открытый сервер.
- В предыдущем пользовательском runtime: `Archicad MCP Server 1.0.0`, `tools/list = ["GetArchicadInstances"]`, после сохранения тестового PLN обнаружены экземпляры Archicad. Для отдельного тестового проекта AC30 JSON API работал на `19725`: 678 элементов, 18 типов; 18/18 ответов по идентификаторам свойств; 15/18 3D bbox, три оставшихся типа имели 2D bbox.
- Это ранее предоставленные пользователем логи, не независимый remote native test.
- **Никаких инструкций по патчу исполняемых файлов, взлому лицензии или загрузке неизвестных торрент-репаков**; альтернативы используют документированные штатные API и должны проходить отдельный аудит безопасности.

## 1. Официальный Graphisoft Public MCP (SOURCE_VERIFIED)

**Документация Graphisoft:**
1. [Archicad 30 — Manage BIM elements via MCP](https://help.graphisoft.com/AC/30/INT/Topics/001_GettingHelp/AI_Assistant/ManageElementsMCP.html): функции MCP доступны только с подпиской **Collaborate или Max**; для Public MCP предусмотрено локальное подключение внешнего клиента, включая локально размещённые модели.
2. [Archicad 30 — Public MCP Connection](https://help.graphisoft.com/AC/30/INT/Topics/001_GettingHelp/AI_Assistant/public_mcp_connection.html): сервер запускается штатными `node.exe` и `mcp-node-app.js`; отдельно нужен поддерживаемый план Collaborate/Max и локальный MCP-клиент; подключение stdio.
3. [Graphisoft AI solutions — product/plan matrix](https://www.graphisoft.com/en-gb/plans-and-products/ai-solutions/): в AC30 Studio доступны иные AI-функции, но agentic Assistant/Public MCP относятся к Collaborate/Max.

**Вывод:** в проверенной локальной установке сервер уже имеется и технически запускается; `GetArchicadInstances` подтверждает связь с Archicad. Нет найденного официального способа скачать другой штатный MCP-бинарник и получить не предоставленные планом инструменты. Отсутствие полного каталога нельзя приписывать недостающему файлу. Указанный в локальной схеме инструмента лицензирующий диагноз — наблюдение из установленного сервера; действующий тип лицензии пользователя не прочитан отдельным системным источником.

**Легальный официальный путь:** обеспечить право на Collaborate/Max и проверить повторно tools/list в открытом пустом PLN. [Graphisoft trial process](https://help.graphisoft.com/store/en/Topics/trial_process.html) указывает на 30-дневную пробную Collaborate, но состав актуально предлагаемой конкретному аккаунту пробной версии и доступность MCP требуют подтверждения. Переустановка полной программы не требуется, если нужный сервер и Add-On уже загружены.

## 2. Обнаруженные бесплатные независимые MCP-мосты (source review, not tested)

| Источник | Открытый контракт | Что понадобится | Статус |
|---|---|---|---|
| [SzamosiMate/tapir-archicad-MCP](https://github.com/SzamosiMate/tapir-archicad-MCP) | В README заявлено **191+** инструментов из Graphisoft JSON API + Tapir; схемы по запросу, `archicad_list_commands`/`archicad_get_command_schema`/`archicad_call_tool`; stdio и HTTP, MIT | Python 3.12+, uv, локальный MCP-клиент, Archicad; Tapir Add-On для Tapir-команд | PROMISING, INSTALL_NOT_TESTED |
| [Boti-Ormandi/archicad-mcp](https://github.com/Boti-Ormandi/archicad-mcp) | Четыре инструмента: `list_instances`, `get_docs`, `get_properties`, `execute_script`; штатный JSON API, опционально Tapir | Python 3.11+, uv, локальный MCP-клиент; безопасный тест `get_docs` без модели | PROMISING, INSTALL_NOT_TESTED |
| [alnumdot/Archicad-MCP-Server](https://github.com/alnumdot/Archicad-MCP-Server) | Небольшой Python bridge штатного JSON API, `list_archicad_instances`, `get_all_elements`, `call_archicad_command` и другие | Python 3.10+, первый online install | PROMISING_SIMPLE, INSTALL_NOT_TESTED |
| [alesdev88/Archicad-MCP](https://github.com/alesdev88/Archicad-MCP) | 309 доступных команд официального JSON API+Tapir в документированной тестовой среде **AC29**, выделены режимы read/write и подтверждение записей; есть Windows `.mcpb` | README ориентирован на AC29, опыт на AC30 не подтверждён; предупреждение: GetPropertyValuesOfElements может вызвать сбой AC29 в тестах автора | RESEARCH_CANDIDATE_AC29, AC30_NOT_TESTED |
| [3d-mcp/archicad-mcp](https://github.com/3d-mcp/archicad-mcp) | Экспериментальный Node.js 22+ мост JSON API для Archicad 26+; базовый read, расширенный вызов по отдельному флагу | npm install из исходников, alpha-качество; нет нативных add-ons | LOW_PRIORITY, AC30_NOT_TESTED |

**Смежные зависимости:**
- [ENZYME-APD Tapir Releases](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.0): релиз 1.7.0 (04.10.2026) заявляет «Build and release the Add-On for Archicad 30»; конкретный архив AC30 Win APX не был независимо прочитан из assets инструментария текущего исследования, **DOWNLOAD_ARTIFACT_NOT_VERIFIED**. Для реальных Tapir-команд требуется совместимый APX под AC30; нельзя просто брать AC29 APX.

## 3. Главные ограничения и риски

- **Независимый MCP-мост не превращает лицензию в Graphisoft Collaborate/Max.** Он опирается на штатные доступные JSON-команды и опциональные native add-ons; команды, которых нет в установленном JSON API/Add-On, не появляются автоматически.
- Большое число опубликованных команд — **каталог**, а не результат LIVE-проверки конкретного AC30 пользователя.
- Сторонний MCP/скрипты могут запускаться под учётной записью пользователя с правом менять PLN и файлы. [Boti execution trust model](https://github.com/Boti-Ormandi/archicad-mcp/blob/master/docs/script-execution.md) прямо указывает отсутствие sandbox/allowlist/transaction rollback. При тестировании: офлайн код-ревью, тестовый PLN, read-only commands, stdio только локально; не поднимать без авторизации публичный HTTP.
- Для APA: уже собственные SceneWriter/JSON API/Tapir/SDK адаптеры в AC29; дополнительный независимый MCP должен быть проверен на реальные недостающие операции, иначе это дублирование функций.

## 4. Рекомендации

**Если требуется именно фирменный набор Graphisoft:** проверить официальное право доступа (Collaborate/Max). Не найдено официальной отдельной загрузки для снятия лицензионного ограничения; торрент-переустановка не является подтверждённым методом и повышает риск вредоносного кода.

**Если требуется рабочий бесплатный MCP-интерфейс:** приоритет — Tapir MCP (богаче типизированные команды, но требует совместимого Tapir Add-On для полного перечня), Boti-Ormandi MCP для compact discovery/скриптов или простой alnumdot JSON bridge. Сначала `tools/list` и `list_instances`, затем read-only `API.GetProductInfo` на **точном порту** выбранного тестового AC30, только затем ручной gate на writes в копии PLN.

**Решение для APA:** не начинать полноценную миграцию к AC30 до закрытия основных задач AC29. Исследование AC30 на изолированной тестовой модели без изменений в APA29. Без отдельного разрешения ничего не устанавливать в рабочий Archicad 29.

## 5. Статусы доказательств

- GRAPHISOFT_LICENSE_GATING: SOURCE_VERIFIED
- OFFICIAL_SERVER_INSTALLED_IN_USER_AC30: USER_REPORTED_PASS
- STANDALONE_OFFICIAL_UNLOCK_DOWNLOAD: NOT_FOUND_IN_SOURCES
- ALTERNATIVE_PROJECT_README_CLAIMS: SOURCE_VERIFIED (documentation only)
- INDEPENDENT_AC30_ALT_LIVE: NOT_TESTED
- TORRENT_FILES_EXECUTED: NO
- PLN/APX/MAIN/WORKING_29_MODIFIED: NO (в рамках этого research pass)

Публикация в исследовательской PR-ветке не закрывает S-ID и не заменяет controlled publisher receipt.
