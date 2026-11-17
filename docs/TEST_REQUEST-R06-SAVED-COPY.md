# Проверка отдельно открытой копии сохранения R06

Используйте установленный Archicad 30 build 3001 с согласованным APX и Python из комплекта APA. Команды не выполняют `EXECUTE`, `SaveProject` и выпуск Publisher. Отдельный PLN получает байты уже защищённого сохранения. Рабочие файлы задания и SQLite сохраняются.

```powershell
$Base = 'C:\Users\Admin\Documents\ChatGPT\настройка адитор\APA-Integration-20261114\Universal-20261116'
$Job = Join-Path $Base 'r06-project'
$Copy = Join-Path $Base 'r06-saved-reopen-20261117'
$Python = 'C:\Users\Admin\Documents\ChatGPT\настройка адитор\APA-unified-20261112\.venv-apa\Scripts\python.exe'
Set-Location -LiteralPath 'C:\Users\Admin\Documents\ChatGPT\настройка адитор\APA-unified-20261112'
# В этой работе копия уже подготовлена. Команда нужна только для нового каталога.
# & $Python -B -X utf8 -m apa ac30-native stage-reopen-copy --job $Job --copy $Copy
$Project = (Get-Content -LiteralPath (Join-Path $Copy 'reopen-copy.json') -Raw -Encoding UTF8 | ConvertFrom-Json).verificationProject
Get-FileHash -LiteralPath $Project -Algorithm SHA256
```

Ожидаемый SHA‑256 копии `75d0717245bfbc3ab3da4440c1e2573d654437d11b47b5158a9c230350372930`. Откройте выведенный точный путь в отдельном экземпляре Archicad 30. У исходного тестового проекта такое же имя файла, но другой каталог. При диалоге восстановления сохраните состояние другого проекта и откройте указанную копию обычным способом. В исходном задании сохранены PID, время запуска прошлого экземпляра и SHA‑256 выполненной операции.

```powershell
& $Python -B -X utf8 -m apa ac30-native verify-reopen-copy --job $Job --copy $Copy
& $Python -B -X utf8 -m apa documentation --job $Job --reopen-copy $Copy --output (Join-Path $Base 'r06-bim-docs-from-saved-copy')
```

Успех сверки имеет статус `SAVE_REOPEN_COPY_VERIFIED`. В `reopened.json` проверяются точный путь, экземпляр, APX, этажи, 21 контрольная BREP-сигнатура, факты 17 операций и `verificationNativeWrites=0`. Обычная приёмка пути исходного PLN по-прежнему использует `SAVE_REOPEN_VERIFIED` и штатные квитанции исходного задания.

В комплекте ожидаются планы этажей, ведомости и `receipt.json` с тем же SHA‑256 PLN, хешем квитанции и хешами файлов. Если проверка закончилась `AC30_EXACT_TEST_PLN_NOT_OPEN_OR_API_UNAVAILABLE`, проверьте точный путь и доступность API этого экземпляра. При расхождении SHA‑256, геометрии или исходных квитанций сохраняйте оба набора для анализа. Повторное выполнение записи не требуется. Подтверждение нативных видов и PDF Publisher остаётся отдельным испытанием.

## Следующее изменение

Для изменения одного окна на отдельном PLN используйте существующий `ac30-native stage-update` с `--prior-job $Job --prior-reopen-copy $Copy --source $Project`. Укажите точный SHA‑256 принятого PLN, APX из исходного задания и его согласованные отпечатки. В проектном задании `CONTINUE_EXISTING_PROJECT` укажите `targetProjectPath` принятой копии и ширину окна 1,6 м. Состав задания и модель в исходной копии сохраняются. В новом `job.json` закрепляется SHA‑256 фактической квитанции `reopened.json`.

Для уже подготовленного изменения запустите только предконтроль в открытой тестовой копии.

```powershell
$Update = Join-Path $Base 'r06-window-update-20261117'
& $Python -B -X utf8 -m apa ac30-native preflight --job $Update
```

Проверьте `READY_FOR_EXPLICIT_TEST_RUN`, единственный `ModifyWindows`, ширину и два затронутых GUID. Запись использует отдельный локальный допуск от этой квитанции. Принятый исходный PLN и его исходная квитанция сохраняются.

[Действующий интеграционный PR №215](https://github.com/dvikt33-ux/safe-bim-layer/pull/215).
