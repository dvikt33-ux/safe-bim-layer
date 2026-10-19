# SAFE-01 LIVE-01: synchronous GuardedSave, поздняя scratch-запись, snapshot reopen

**19.10.2026. Статус: LIVE VERIFIED на указанной копии.** Новый результат продолжает #175 и опубликован в #178. Это отдельный прогон нового кода; прежняя LIVE-02 из #173 сохранена.

Исполненный код: `26d3f7b6e973420d8cdb6bfe7be8663e2a6725df` (исправление `a8cd4312a6a69b9f7773ebb01467ddf03cd8eac4`). Чистый изолированный checkout; AC29 build 5101 / Tapir 1.5.10, собственный PID 8760, порт 19727. Установленное ядро APA и APX не заменялись.

## Подтверждённый сценарий

1. Новая сохранённая копия принятой 69-GUID PLN; read-only проверка точного пути/build/Tapir, исходных SHA, всех BREP и двух размещений с зазором 10 м.
2. Существующий DynamicCommands → BIM Graph → code-owned scope/verifier → SceneWriter/SQLite: **один CreateHotlinkInstances** с двумя записями; полный native readback; **один SaveProject** через GuardedSaveTransport.
3. Внутри verify-after сохранения немедленно создан `guarded-save.snapshot`. SHA ниже совпал с saved receipt и снимком. Модель: **69 → 119 GUID**, два новых корня и 48 дочерних элементов, по 24 владельца на каждый корень.
4. Только свой тестовый проект закрыт через GUI **без второго сохранения**. Native API вернул 4001/no open project.
5. Смоделирована поздняя файловая запись: только закрытая disposable scratch заменена прежними валидными байтами 69-GUID источника. Оригинал и модуль не менялись. Это контролируемая симуляция, а не утверждение о реальной сторонней записи Archicad. Штатный `check_closed` отказал `HOTLINK_BATCH_PERSISTED_SCRATCH_REQUIRED_BEFORE_GUI_CLOSE`.
6. `stage_readonly_reopen` скопировал **точные сохранённые 119-GUID байты** в ещё один новый PLN и отдельный verification-only state. Исходные manifest/saved/attempted/SQLite не переписывались.
7. Реальное GUI-открытие снимка → `confirm_open_snapshot PASS` → GUI-закрытие без нового Save → штатный `check_closed` с 4001/no open project → повторное GUI-открытие → штатный `verify_reopen` **LIVE_NATIVE_HOTLINK_BATCH_SAVED_REOPENED_PASS**.
8. Дополнительный независимый read-only аудит заново сверил весь набор 119 GUID, подписи BREP всех 69 исходных элементов, SHA источника/модуля/снимка, обе SQLite scenes PASS и отсутствие лишнего native CREATE/SAVE. Второй cooperating lease на реальной scratch отказал; исходная reservation сохранена.

## Принятые данные

| Поле | Значение |
| --- | --- |
| Сохранённый / synchronous snapshot / reopened PLN SHA256 | `d471eaafb858960d47b6bf4df48864ab24d36c1667d7bf00bd1c437ba7b64a99` |
| Защищённая исходная PLN SHA256 | `98ad2144792309c208818bfdb2a5aba407c9de1f266c34abda5b00b564343acc` |
| Защищённый Hotlink-модуль SHA256 | `3a74d7cb17e460378eacfa8f933aeae29a5ca39fbf2bc73633115c9fee728750` |
| Корень 1 | `1a994e1d-d134-48d2-ab15-1078e0c93a6b` |
| Корень 2 | `5556e8c4-eda9-4abe-b088-e7ffb428e9a2` |
| Координаты origin | `(386.95, 0, 0)` и `(427.425, 0, 0)` м |
| Native batch / SaveProject / автоматический повтор | `1 / 1 / 0` |

## Квитанции

- `receipt.json`: полная машинная приёмка с точным SHA исполненного кода.
- `controlled-drift-proof.json`: точное содержание симуляции и отказа по SHA.
- `opened-before-close.json`, `closed.json`: два открытия разделены реальным закрытием.
- `independent-readback.json`: все 119 GUID, исходные 69 GUID/BREP и повторная проверка lease.
- `sqlite-audit.json`: обе оригинальные scenes PASS, SHA SQLite до/после read-only аудита совпал.
- `native-calls.json`: фактические команды из raw trace, один batch и один save.
- `original-evidence-hashes.json`: SHA оригинальных локальных квитанций; это SHA исходных байтов, а не санитизированных копий.
- `published-artifact-hashes.json`: SHA опубликованных JSON до добавления данного текстового отчёта.

Полные private paths, native model dumps, raw JSONL, SQLite и принятый PLN сохранены локально в поставке `APA29_SAFE01_LIVE01`; в GitHub опубликованы санитизированные квитанции. Кооперативная reservation не является системной Win32-блокировкой постороннего Archicad. Приёмка относится к двум экземплярам и данному снимку; 32 группы, общий scope всех типов и ускорение не выводятся из этого результата.

## Проверки исходников

Windows Python 3.11: 22 isolation + 8 geometry + 14 batch writer = **44 PASS**. Windows GitHub Actions на исходном исправлении `a8cd4312` находились в очереди в момент LIVE: [run 39281972083](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/39281972083), [batch run 39281972005](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/39281972005). Очередь CI не названа PASS. Исторический CI #175 на `24c19834` остаётся отдельным доказательством. Main/оригинальные PLN/APX не менялись; merge не выполнялся.
