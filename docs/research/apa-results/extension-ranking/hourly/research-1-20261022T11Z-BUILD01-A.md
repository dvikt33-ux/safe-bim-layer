# APA №1 — BUILD-01 / SOURCE 01–10 / 2026-10-22 11Z

**Контекст:** P0 [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192); SOURCE_ONLY. Исходники Tapir 1.5.9 — MIT (LICENSE проверен); закреплённый снимок 1.5.10 — контракт из другого проекта, не установленный APX. API Graphisoft — проприетарный. Ни один пункт не означает INSTALLED/LIVE. Все задания №2 — только исследование/подготовка, без WRITE.

### 01. G0 — Как установить фактически загруженный APX, а не установленную на диске копию?
**Источник/версия/лицензия:** Microsoft Process Explorer 17.14, 10.09.2026; проприетарная Microsoft, EULA не перепроверена. [Первоисточник](https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer).
**Проверенный факт:** DLL mode показывает модули выбранного процесса и их путь; Add-On Manager сам по себе не связывает путь с PID.
**Решение/ограничение:** Сверять DLL/APX из PID Archicad с проектом/портом; без совпадения G0 BLOCKED.
**Задание №2:** №2: read-only скрин/экспорт PID→полный путь APX и отметка процесса.

### 02. G0 — Есть ли альтернативный готовый CLI-инвентарь загруженных модулей?
**Источник/версия/лицензия:** Microsoft ListDLLs 3.21, обновление 15.10.2026; проприетарная Microsoft, EULA не перепроверена. [Первоисточник](https://learn.microsoft.com/en-us/sysinternals/downloads/listdlls).
**Проверенный факт:** `listdlls -v <pid>` перечисляет загруженные DLL и версию; `-d <dllname>` показывает процессы; это не SHA.
**Решение/ограничение:** Использовать вместо нового диагностического кода, если утилита уже имеется; не устанавливать без отдельного разрешения.
**Задание №2:** №2: указать необязательный read-only способ сверки APX/PID и предусмотреть fallback Process Explorer.

### 03. G0 — Чем доказать байтовую идентичность найденного APX?
**Источник/версия/лицензия:** Microsoft PowerShell Get-FileHash, Windows 11; штатная команда, отдельная лицензия/установка не нужна. [Первоисточник](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash).
**Проверенный факт:** `Get-FileHash -Algorithm SHA256 -LiteralPath <путь>` хеширует файл; версия Tapir из API не является SHA.
**Решение/ограничение:** Считать SHA256 именно загруженного файла; сохранить путь, размер, дату и SHA.
**Задание №2:** №2: в manifest выделить `loadedApxPath`, `loadedApxSha256`, `pid`, `port`.

### 04. G0 — Можно ли принять сохранённую schema 1.5.10 за нынешний runtime?
**Источник/версия/лицензия:** Pinned Tapir snapshot 1.5.10, `archicad-mcp.tapir-snapshot/1`; лицензия снимка APA не проверена, upstream Tapir MIT. [Первоисточник](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json).
**Проверенный факт:** `_metadata.binding` относится к прежнему `Тест MER .pln`, порту 19723, story 0; это историческая привязка, не текущая.
**Решение/ограничение:** Разделить snapshot provenance и фактический PID/APX/schema/PLN.
**Задание №2:** №2: явный флаг `SNAPSHOT_NOT_RUNTIME`; read-only проверка живых команд.

### 05. G0 — Как проверить build 5101 именно работающего экземпляра?
**Источник/версия/лицензия:** Graphisoft Python API Archicad 29, b3000commands; проприетарный API Graphisoft. [Первоисточник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Проверенный факт:** `GetProductInfo()` возвращает version/build/language, а не сведения о PLN.
**Решение/ограничение:** Проверить `build==5101` вместе с портом и проектом; несовпадение — STOP.
**Задание №2:** №2: включить ответ `GetProductInfo` в G0 receipt без вывода из имени exe.

### 06. G0 — Доказывает ли GetCurrentWindowType правильную базу для CreateWindows?
**Источник/версия/лицензия:** Tapir 1.5.9 `ApplicationCommands.cpp` и `ExtendedElementCommands.cpp`; MIT. [Первоисточник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp#L275-L323).
**Проверенный факт:** GetCurrentWindowType сообщает активное окно; исходник создания проёмов отдельно переключает CURRENT DATABASE через `ACAPI_Database_ChangeCurrentDatabase`.
**Решение/ограничение:** Не путать UI окно и базу данных; не менять UI в G0.
**Задание №2:** №2: проверить наличие upstream DB-guard в установленном APX без пробного CREATE.

### 07. G0 — Достаточно ли GetProjectInfo для контроля несохранённых изменений?
**Источник/версия/лицензия:** Pinned Tapir 1.5.10 `GetProjectInfo`; upstream MIT, лицензия снимка APA не проверена. [Первоисточник](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json).
**Проверенный факт:** В схеме обязательны `isUntitled/isTeamwork`, `projectPath/name/location` необязательны; `dirty/readOnly` отсутствуют.
**Решение/ограничение:** Fail-closed GUI/операторский dirty guard, без Close/Open при неизвестном состоянии.
**Задание №2:** №2: отдельно фиксировать GUI dirty state, путь, untitled/teamwork и права.

### 08. G1 — Может ли PR74 authored compiler принять произвольные балки и дополнительные перекрытия?
**Источник/версия/лицензия:** PR74 immutable 5a3a9201, `archicad_project_accelerator.py` строки 284–299; лицензия APA NOT_VERIFIED. [Первоисточник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L284-L300).
**Проверенный факт:** `nativeComponents` whitelist: `CreateColumns`, `CreateDoors`, `CreateWindows`, `CreateWalls`, `CreateRoofs`; `CreateBeams/Slabs` не допускаются.
**Решение/ограничение:** Не расширять код; балки optional, базовые Slabs строятся штатным authored-путём.
**Задание №2:** №2: отразить реальные whitelist ограничения в G1 typed plan.

### 09. G1 — Как обнаружить несогласованные высоты этажей до нативной записи?
**Источник/версия/лицензия:** PR74 immutable, `archicad_authored_native_plan.py` строки 33–46; APA license NOT_VERIFIED. [Первоисточник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L33-L47).
**Проверенный факт:** `storyHeights` требует ключи всех story ID, значения 2.4–4.5 м, а промежуточные `level + height == next level` с допуском 1e-5.
**Решение/ограничение:** Не подставлять высоту верхнего этажа из отсутствующего поля GetStories.
**Задание №2:** №2: передать инженерному исполнителю offline критерий согласованности этажей.

### 10. G1 — Как исключить подмену строительного материала между CSE и preflight?
**Источник/версия/лицензия:** PR74 immutable, `archicad_authored_native_plan.py` строки 49–75; APA license NOT_VERIFIED. [Первоисточник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L49-L75).
**Проверенный факт:** Проверяются CSE для всех этажей, nativeStoryBindings и повторно GUID материала при неизменном GetProjectInfo.
**Решение/ограничение:** Сохранять исходную цепочку CSE→GUID без нового resolver.
**Задание №2:** №2: фиксировать несовпадение material GUID/storyBindings как BLOCKED, не предупреждение.

**Счёт:** 10 предметных проверок, полученных из проверенных в этом проходе первоисточников; разные вопросы могут опираться на один исходный файл. Не суммировать с прежними hourly.
