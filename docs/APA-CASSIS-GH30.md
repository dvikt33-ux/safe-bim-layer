# APA — Cassis — Grasshopper / Archicad 30

Статус: локальный маршрут APA Control → Cassis реализован. Запись нативного BIM в PLN не принята.

## Архитектура

В существующем scripts/apa_control_mcp.py разрешены операции apa_execute: gh-read, gh-rectangle, gh-verify. Они вызывают scripts/apa_cassis_bridge.py через штатные очередь, уникальный job_id, журнал и apa_read. Второго APA MCP-сервера нет. Cassis работает на штатном http://127.0.0.1:3003/mcp/.

Мост допускает только заранее закрепленный GHX (точный путь, SHA-256 и три GUID) и новые файлы APA_Cassis_Rectangle_*.ghx в testRoot. Другие команды Cassis на запись запрещены. Версия Cassis закреплена: 1.6.0. Нативных операций Archicad в этом мосте нет.

## Подключение

1. Открыть Rhino 8 / Grasshopper с Cassis 1.6.0. Проверить localhost:3003.
2. Создать полный релизный манифест APA с обновленными SHA-256. В профиль APA_MCP_PROFILE_V1 добавить cassisProfile со ссылкой на профиль APA_CASSIS_PROFILE_V1. Тестовый манифест из experiments не использовать в производстве.
3. Запустить существующий apa mcp-control --profile <путь> (или scripts/apa_control_mcp.py --profile <путь> --port <порт>).
4. Вызвать apa_execute(operation=gh-read, job_id=<новый>, intent={schemaVersion:apa-gh-command/1, tool:get_componentcount, arguments:{}}). Результат читается через apa_read(kind=job,job_id=...).
5. Для изменения размеров: operation=gh-rectangle, intent с schemaVersion, widthMm, heightMm, outputFile. Выходной файл должен быть новым.
6. Проверка: operation=gh-verify с outputFile, outputSha256, expectedPerimeterMm. В случае ошибки повтор не выполняется автоматически.

## Фактические испытания 16.11.2026

- Cassis MCP 1.6.0: HTTP и tools/list — PASS.
- GH исходник 4000×3000 мм: периметр 14000 мм; Save/Reopen — PASS.
- tests/test_apa_cassis_bridge.py: 7/7 PASS, включая защитные негативные проверки.
- Через APA Control gh-read — COMPLETE; gh-rectangle 5000×4000 мм — COMPLETE, сохранен APA_Cassis_Rectangle_5x4m_apa_mcp.ghx.
- SHA-256 GHX: b29cf20d5fe9e2c1387664841e8fd577ba915ba278e9366f1d9e9a64975cd699.
- Через APA Control gh-verify: FAILED с GH_VERIFY_REOPEN_FILE_MISMATCH в двух отдельных проверках. Отдельное последующее read-only чтение подтвердило тот же SHA, три GH-объекта, две связи, периметр 18000 мм. Это НЕ переводит failed job в PASS.
- ArchicadConnection.gha 30.0.0.3000 обнаружена и зарегистрирована; в Grasshopper есть Archicad / Design / Slab. Активная связь с определенной тестовой PLN и создание нативного Slab НЕ проверены.
- Облачный MCP_APA Windows туннель Offline; локальный APA работоспособен без DC, но текущий чат не имеет прямого доступа к новому маршруту до переподключения и развертывания обновленного APA.

Запрещены: любые изменения производственных PLN; запуск нативной записи без подтвержденного тестового проекта и допуска; автоматический повтор неопределенной записи; объявление Morph нативным Slab.
