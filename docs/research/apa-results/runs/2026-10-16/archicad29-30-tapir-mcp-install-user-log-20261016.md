# APA — пользовательская установка независимого Tapir MCP для Archicad 29 и 30

Дата отчёта: 2026-10-16. Источник: полный PowerShell log пользователя (USER_REPORTED_RUNTIME); выполнение пользователем на Windows, **не удалённый запуск** исследователем. Сохраняем проверяемую границу: установлена серверная часть MCP, но полноценная доступность AC30 не достигнута.

## Исходные наблюдения
- `uv --version`: 0.11.21; `uv tool install --python 3.12 "tapir-archicad-mcp==0.6.4"` успешно завершён: 37 packages, 1 executable `archicad-server`.
- `uv tool list`: отдельно существовал пакет `archicad-mcp-server v0.6.0` с командами `archicad-gdl`, `archicad-mcp`. Новый `tapir-archicad-mcp v0.6.4` со своей командой `archicad-server` установлен рядом, старый пакет не удалён/обновлён.
- Исполняемый MCP расположен в user-local bin: `~/.local/bin/archicad-server.exe`. `archicad-server --help` возвращает аргументы запуска (stdio, sse, streamable-http).
- Проверена реальная MCP stdio session: `initialize`, `tools/list` → ровно пять инструментов:
  `discovery_list_active_archicads`, `archicad_list_commands`, `archicad_get_command_schema`, `archicad_call_tool`, `archicad_get_job`.
- `tools/call discovery_list_active_archicads` вернул 1 active и 3 unavailable.

## Локальные экземпляры и фактическая поддержка

| Archicad | Build | Порт на момент диагностики | MCP status | Tapir |
|---|---|---|---|---|
| 30 | 3001 | 19723 | unavailable: missing_tapir | отсутствует |
| 30 | 3001 | 19724 | unavailable: missing_tapir | отсутствует |
| 30 | 3001 | 19725 | unavailable: missing_tapir | отсутствует |
| 29 | 5101 | 19726 | active: `APA_Assembly_Modify_01` | 1.5.10, предупреждение ожидаемая 1.7.0 |

Отметка: `unavailableInstances` из MCP не содержит портов; соответствие трём портам AC30 установлено отдельно через `API.GetProductInfo` в том же тестовом сеансе. UUID и имена остальных проектов ранее предоставлены пользователем. Порты могут измениться при перезапуске.

## Сравнение с upstream
- Исходники и README: https://github.com/SzamosiMate/tapir-archicad-MCP — версия 0.6.4 использует `multiconn-archicad==0.9.3`; именно discover/dispatch по `port`. `archicad_call_tool` **умеет выполнять команды записи**, и только tools/list/discovery сами по себе не означают read-only защиту.
- Официальный релиз Tapir 1.7.0: https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.0 (04.10.2026) заявляет поддержку сборки AC30, Pull Request #737. 16 assets отображаются в release listing; у текущего браузерного инструмента перечень конкретных AC30 assets не был доступен полностью, поэтому скачать/установить AC30 APX ещё необходимо **с проверкой реального asset name/digest через GitHub release API**.
- Установщик Tapir может охватить обе версии, поэтому **не использовать автоматический установщик с обновлением AC29**: APA29 с Tapir 1.5.10 является рабочей интеграцией и может зависеть от версии.
- Безопасный следующий шаг: только `TapirAddOn_AC30_Win.apx` из опубликованных assets 1.7.0, скачать в отдельную папку, сравнить SHA256 с GitHub `assets[].digest`, вручную подключить через Add-On Manager в AC30; сохранить тестовый PLN и перезапустить нужный AC30 экземпляр вручную, после чего повторить MCP discovery; AC29 не трогать.

## Что получено / не получено
- `MCP_SERVER_INSTALLED`: USER_REPORTED_PASS
- `MCP_STDIO_HANDSHAKE_AND_TOOL_LIST`: USER_REPORTED_PASS
- `AC29_TAPIR_DISCOVERY`: USER_REPORTED_PASS (не live read of one BIM command through MCP)
- `AC30_TAPIR_DISCOVERY`: BLOCKED_MISSING_ADDON
- `AC30_APX_BINARY_VERIFIED/INSTALLED`: NOT_DONE
- `IN_APP_MCP_CLIENT_CONFIGURED`: NOT_DONE
- `MODEL_WRITES`: 0 по PowerShell log, независимый PLN diff не был выполнен
- `APA29_APX_CHANGED`: NO evidence of any changes; scripts did not mutate existing APX
- `CURRENT_S_ID_CHANGED`: NO; исследовательский отчёт не является controller publisher receipt

Следующий блок работ: безопасная установка Tapir на AC30 (по желанию пользователя), затем MCP-local read-only вызовы GetProductInfo на обоих экземплярах и настройка совместимого MCP host-клиента; установка AC29 MCP на серверной стороне уже проведена.


## 6. Дозапись: AC30 Tapir 1.7.0 APX downloaded + SHA256 verified, NOT_INSTALLED

Пользователь представил продолжение PowerShell лога 2026-10-16. Команда `GET https://api.github.com/repos/ENZYME-APD/tapir-archicad-automation/releases/tags/1.7.0` обнаружила ровно один asset `TapirAddOn_AC30_Win.apx`, а `asset.digest` имел формат `sha256:<64 hex>`. Файл был загружен по `asset.browser_download_url`.

Лог вывел:
- Path: `C:\Users\Admin\AppData\Local\APA\ExternalAddons\AC30\Tapir-1.7.0\TapirAddOn_AC30_Win.apx`
- Tag: `1.7.0`
- SHA-256: `21145D75B9EF8895E192B780869B5AB5CBE6094BF9940F2025E71783A9B2B365`
- `DOWNLOAD AND HASH VERIFICATION: PASS`.
- Вызов установки/регистрации в Archicad **в пользовательском логе не представлен**. `ARCHICAD_30_ADDON_LOADED: NOT_VERIFIED`, `MCP_AC30_ACTIVE: NOT_VERIFIED`. В отличие от AC29 Tapir 1.5.10, для AC30 следующий шаг — ручное подключение файла через Add-On Manager и повторный MCP discovery.
- В рамках PowerShell загрузки не было команды записи PLN или изменения установленного Tapir AC29. Никакого независимого двоичного аудита скачанного APX или криптографической проверки подписи Graphisoft не было; SHA256 подтверждает только совпадение с хэшем официального GitHub-asset.
- Статус USER_REPORTED_HASH_VERIFIED, не SOURCE_VERIFIED_BINARY_SECURITY.
- После установки необходимо сверить версию отдельно по AC30 портам и выполнить **только read-only** тесты, не менять APA29.

Источник: пользовательский лог в чате, отсутствует независимое управление его ПК. Результаты сохраняются в draft PR, не в main и не как controller receipt.

## 7. AC29+AC30 active через один независимый MCP — пользовательский runtime PASS

**Дата:** 2026-10-16. После ручного подключения проверенного Tapir 1.7.0 APX пользователь прислал реальный вывод MCP stdio `initialize`, `tools/list`, `tools/call discovery_list_active_archicads`:

```text
MCP TOOLS:
discovery_list_active_archicads
archicad_list_commands
archicad_get_command_schema
archicad_call_tool
archicad_get_job

ACTIVE ARCHICAD:
Archicad 30 | Port 19725 | Tapir 1.7.0 | тестовый файл все типы+30
Archicad 29 | Port 19726 | Tapir 1.5.10 | APA_Assembly_Modify_01
AC29: PASS
AC30: PASS
ACTIVE INSTANCES: 2
MODEL WRITES: 0
```

Оба экземпляра обнаружены как **active**, а не только как открытые JSON API порты. Другие два AC30 экземпляра сообщают `missing_tapir`, что не препятствует выбранному тестовому AC30. AC29 Tapir 1.5.10 выдаёт предупреждение: сервер ожидает 1.7.0; ранее установленные расширения APA29 **не обновлялись**.

- `AC29_MCP_DISCOVERY`: USER_REPORTED_PASS.
- `AC30_MCP_DISCOVERY`: USER_REPORTED_PASS.
- `MCP_COMMAND_CATALOG_TOOLS`: 5 names exposed (это инструменты MCP, **не** 191 доказанных работающих операций).
- `MCP_READ_COMMAND_EXECUTION`: NOT_TESTED; `archicad_call_tool` пока не вызывался.
- `MCP_HOST_REGISTERED`: NOT_TESTED; клиент через временный Python stdio probe, без постоянной регистрации в пользовательском ИИ-клиенте.
- `MODEL_WRITES`: 0 в представленном скрипте. Independent PLN binary diff NOT_TESTED.
- Архитектура допускает управление несколькими экземплярами по портам, но соответствие версия→порт нужно перепроверять при перезапуске.

**Безопасный следующий шаг:** из MCP вызвать `app_get_add_on_version` (только чтение) на каждом из двух выбранных портов с предварительной `archicad_get_command_schema`; затем на AC30 тестовом PLN ограниченный `GetAllElements` через MCP. Не менять AC29 Tapir/APX или рабочий PLN.

Источник доказательства — консольный журнал пользователя; не считать независимым тестом on-device со стороны автора отчёта и не закрывать S-ID.
