# Единый мост Tapir

Транспорт Archicad передаёт вызовы Tapir через `API.ExecuteAddOnCommand`. Его используют DynamicCommands, SceneWriter и унаследованные команды AC30. Для каждой команды общего маршрута DynamicCommands проверяет метаданные разрешённого эффекта, схему входа, факт регистрации в открытом экземпляре и схему ответа. Мост связывает чтение с локальным профилем, проверяет версию Archicad, сборку, версию Tapir и путь открытого PLN. Хеш APX в профиле относится к файлу на диске. В журнале сохраняются запросы и ответы.

| Каталог | Происхождение | Схемы | Проверенные политики чтения |
| --- | --- | ---: | ---: |
| Tapir 1.5.10 / AC29 | Исходный экспорт использованной APA сборки | 262 | 6 |
| Tapir 2.0.0 / AC29 и AC30 | Официальный выпуск `bb71abf12f37273f47a9ea0f3daeabae0578225d` | 789 | 9 |

Каталог показывает описанный контракт отдельно от регистрации в конкретном процессе. Точную совместимость с фактической версией проверяет мост. Версия без подходящего каталога видна в статусе. Для вызова требуется каталог этой версии и политика чтения, привязанная к хешу полного контракта. [Документация Graphisoft](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac30.html) · [Выпуск Tapir 2.0.0](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/2.0.0)

## Подключение

Профиль `APA_TAPIR_READ_PROFILE_V1` содержит поля `schema`, `port`, `archicadVersion`, `tapirVersion`, `project`, `backup`, `addon` и соответствующие `projectSha256`, `backupSha256`, `addonSha256`. Укажите абсолютные пути к открытой разрешённой копии .pln, её отдельной побайтовой копии и .apx. Профиль AC30 пилота `APA_AC30_TAPIR20_READ_ONLY_V1` принимается также. Журналы чтения появляются в папке `<имя профиля>-tapir-evidence` рядом с профилем.

```powershell
$apa = '.\.apa-runtime\Scripts\python.exe'
& $apa -m apa tapir status --profile $profile
& $apa -m apa tapir catalog --profile $profile --command GetStories --probe
& $apa -m apa tapir read --profile $profile --command GetStories
& $apa -m apa mcp-control --profile $profile
```

В MCP этим операциям соответствует один инструмент `apa_tapir`. Для совмещения с существующими кампаниями добавьте в их профиль абсолютный путь в поле `tapirProfile`. При запуске MCP непосредственно с профилем чтения доступен только `apa_tapir`. Совместимый вход `ac30-mcp` с `--elements` использует общий MCP-сервер и сохраняет отдельную сверку типизированных ведомостей с поэлементным расчётом.

Запись выполняется существующими типизированными кампаниями и SceneWriter. Допуск к записи, точные условия конкретного PLN и сборки, квитанции, журналы SQLite и защита от повторного исполнения действуют для этих кампаний. Каталог общего чтения не создаёт новый сценарий записи. В Windows-комплекте сохранён бинарник APA для AC29. Для AC30 профиль указывает на отдельный совместимый APX Tapir.

## Обновление каталога

Возьмите Git-ревизию исходников конкретного выпуска Tapir. Файл `--review` содержит карту «название команды → путь к проверенной реализации» в этой ревизии. Сверьте эффект по исходникам. Импорт читает официальные схемы из Git, записывает SHA-256 исходных байтов и связывает политики чтения с контрактами. Сгенерированный JavaScript разбирается как JSON после удаления объявления переменной.

```powershell
& $apa -m apa tapir import-catalog --source-repo $tapirRepo --revision $revision `
  --tapir-version 2.0.0 --archicad-version 29 --archicad-version 30 `
  --review 'schemas/tapir-bridge/2.0.0-reviewed-reads.json' --output $catalog
(Get-FileHash -LiteralPath $catalog -Algorithm SHA256).Hash.ToLowerInvariant()
```

Чтобы применить дополнительный каталог, заполните `catalog` и `catalogSha256` в локальном профиле и запустите его заново. Выбор нового контракта идёт через тот же инструмент MCP. Изменения в списке команд отображаются при чтении нового каталога. [Лицензия данных Tapir](../schemas/tapir-bridge/LICENSE-TAPIR.txt)
