# APA №1 | BUILD-01 | 2026-10-23 08Z | Шесть карточек решений

**Ранг 0–100 — экспертная важность, не benchmark.** SOURCE ≠ INSTALLED/LIVE/ACCEPTED. Цель — снять блокеры issue #192 без второго writer и без изменения APX/PLN.

## C01. G0 — Microsoft Sysinternals ListDLLs + PowerShell Get-FileHash — 99/100 (экспертно)
**Первоисточники:** [source](https://learn.microsoft.com/en-us/sysinternals/downloads/listdlls); [source](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-5.1).

**Версия/лицензия/статус:** ListDLLs v3.2; Windows 11 PowerShell; Microsoft licensing; installation/availability NOT_VERIFIED.

**Проверенный факт:** ListDLLs показывает загруженные DLL/APX для PID и версию, PowerShell Get-FileHash вычисляет SHA256 по точному пути. Это два разных измерения; SHA файла на диске без PID/module identity не доказывает, что именно он загружен.

**Готовое применение и адресное задание №2:** №2: определить процесс Archicad29, порт и активный PLN; получить loaded APX path, затем SHA256 того же файла; read-only GetAddOnVersion и API.IsAddOnCommandAvailable. Не запускать GenerateDocumentation (пишет файлы) без отдельного допуска.

**Критерий закрытия:** G0 может перейти к RUNTIME_READY только при совпадении PID/port/project identity/module SHA/registered schema. Сейчас SOURCE_ONLY; не установлен/не запускался.

## C02. G4 — безопасное закрытие GUI при Tapir Palette scripts — 97/100 (экспертно)
**Первоисточники:** [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1440); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/775).

**Версия/лицензия/статус:** Tapir upstream PR1440 OPEN 23.10.2026, протестирован автором на AC29.0 JPN build5101 Windows; PR775 OPEN, unbuilt. MIT. Не доказано для установленной локальной 1.5.10..

**Проверенный факт:** PR1440: при закрытии Archicad с долгим скриптом в палитре может происходить crash из-за фонового UIUpdaterThread и отложенных message-loop tasks; автор проверил патч на том же номере build. PR775: Stop uv может оставлять Python-child, что создаёт риск двух параллельных relay.

**Готовое применение и адресное задание №2:** №2: добавить операционный G4 pre-close checklist: нет работающих palette scripts/relay и дочерних процессов; не устанавливать патч и не изменять APX. При сомнении G4 BLOCKED, без принудительного Close и без повтора CREATE.

**Критерий закрытия:** Состояние скриптов подтверждено на Windows; GUI Close/Open выполняется только отдельным исполнителем после санкционированного scratch и GuardedSave. SOURCE не означает установленное исправление.

## C03. G2 — существующий compiler preflight против schema-valid/post-CREATE failure — 100/100 (экспертно)
**Первоисточники:** [source](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py#L535-L628); [source](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py#L411-L510); [source](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T07Z-audit-A.md).

**Версия/лицензия/статус:** APA PR162 immutable f7c37b8; source license NOT_CONFIRMED; существующие функции, никакой новой установки.

**Проверенный факт:** Provider schema допускает пропуски width/height/sillHeight у hosted opening и отдельных полей Slab/Column, но SceneWriter индексирует их после CREATE. Для добавленных Slabs/Beams не хватает проверки story/envelope. Это условные статические пути, не наблюдавшийся LIVE сбой.

**Готовое применение и адресное задание №2:** №2: в существующем compiler/preflight fail-closed проверить writer-required поля, единицы, hostWall, floorIndex, envelope, adapter eligibility. Отдельно оформить CREATE и MODIFY для Slab. Не создавать новый writer, не обходить offline guard.

**Критерий закрытия:** Отрицательные OFFLINE-кейсы не доходят до WRITE, успешный read-only preflight создаёт typed DAG/hash; настоящий OFFLINE_PASS только по выполненному тесту.

## C04. G2 — штатная проверка классификаций/свойств Graphisoft AC29 — 96/100 (экспертно)
**Первоисточники:** [source](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html); [source](https://help.graphisoft.com/AC/29/RUS/_AC29_Help/045_PropertiesClassifications/045_PropertiesClassifications-6.htm).

**Версия/лицензия/статус:** Graphisoft AC29 b3000 JSON API и AC29 RUS Help; proprietary; штатный API, не отдельный платный сервис.

**Проверенный факт:** GetPropertyDefinitionAvailability(propertyIds) перечисляет классификации, для которых определение свойства доступно; GetClassificationsOfElements и GetPropertyValuesOfElements дают независимый readback. Это не равнозначно editability каждого элемента.

**Готовое применение и адресное задание №2:** №2: при structuralFunctions сначала определить реальные property IDs, классификации стен/перекрытий/кровли и доступность; затем отдельно подтверждать фактическую запись и readback только по разрешению.

**Критерий закрытия:** Доступность определений/классов подтверждена локально и независимым чтением; не заявлять прочность/нормативную пригодность.

## C05. G2 — upstream CheckPropertyValues как будущий read-only validator — 82/100 (экспертно)
**Первоисточники:** [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1147); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1238); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1279).

**Версия/лицензия/статус:** Tapir 1.7.x proposed; PR1147/1238/1279 OPEN; MIT; unbuilt/unverified on local 1.5.10.

**Проверенный факт:** CheckPropertyValues проверяет value по property definition без записи; GetPropertyEditability и GetPropertyAvailabilityOfDefaults различают editable/visible/available. Команды не подтверждены установленными.

**Готовое применение и адресное задание №2:** №2: не делать эти PR обязательными G0/G2. Пока использовать штатный API29 для доступности и fail-closed type/enum checks по существующему каталогу; отдельное решение об обновлении APX только владельцу.

**Критерий закрытия:** DEFER до merge+build+runtime registration+schema readback. SOURCE_ONLY, не INSTALLED.

## C06. G2/G1 — фильтр ложной готовности upstream merged компонентов — 94/100 (экспертно)
**Первоисточники:** [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1141); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/968); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1140); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1149); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1025); [source](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/964).

**Версия/лицензия/статус:** Tapir MIT; PR1141/1149/1025 merged 23.10.2026, но backend PR968/1140/964 OPEN; PR1149 guard AC27-only.

**Проверенный факт:** Merged GH-компонент #1141 без backend возвращает unknown command; #1149 в AC29 возвращает not supported; #1025 основан на не объединённом #964 и не проверен DevKit. Статус merged не является runtime capability.

**Готовое применение и адресное задание №2:** №2: исключить эти PR из обязательной цепочки BUILD-01; не расширять каталог кандидатами вместо решения G0/G1; при необходимости проверять dependency graph и конкретный installed schema.

**Критерий закрытия:** Решения помечены DEFER/EXCLUDE, G0/G2 не становятся PASS от публикации исходников.

**Вывод:** наиболее полезные немедленные действия — G0 loaded APX identity и G1/G2 строгий preflight уже существующего SceneWriter. PR1440 — значимый условный риск G4, но не оправдывает самостоятельную установку. MODEL_MODE_NOT_VERIFIABLE.
