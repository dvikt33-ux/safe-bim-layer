# APA — массовый параллельный офлайн-аудит PR #88

**Дата отчёта:** 2026-10-15. **Исполнитель:** независимый GPT-6. **Статус:** WINDOWS_CI_PASS_WITH_KNOWN_XFAIL.

## Точные версии и воспроизведение

- **Проверяемый функциональный код APA:** [draft PR #88](https://github.com/dvikt33-ux/safe-bim-layer/pull/88), source SHA **`07e73f9c3f634ed93ea06be79bdf603bf0124abf`**.
- **Изолированная QA-ветка:** `audit/apa-mass-parallel-offline-20261015`; [draft PR #89](https://github.com/dvikt33-ux/safe-bim-layer/pull/89) к `feature/apa-sdk-module-expansion-20261015`. Изменены только QA-скрипты и тесты, исходники Work не изменены.
- **Финальный проверенный запуск:** [GitHub Actions #38649516535](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38649516535), `APA massive parallel offline QA`, 12 выполненных Windows jobs, **весь workflow SUCCESS**. Проход выполнен после исправления механизма учёта дубликатов; первый запуск #38649319198 *не является PASS*, поскольку остановился на 37 повторных ID.
- **Версия плана по выводу core smoke:** 163.
- **Среда:** GitHub-hosted `windows-latest`, Python 3.11; никаких обращений к Archicad или пользовательскому PLN/APX.

## Массовые unit-тесты и полнота охвата

Восемь независимых матричных заданий обнаруживали полный набор `tests/test_*.py` и запускали каждый **уникальный** ID на одном раннере. При первоначальном обнаружении 772 вхождения 37 ID дублировались в legacy `unittest` suite — это не дополнительные уникальные тесты.

- **735 уникальных unit-тестов выполнено ровно по одному разу**.
- **727 обычных PASS + 8 ожидаемых XFAIL**.
- **Неожиданные FAIL = 0, ERROR = 0, UNEXPECTED_SUCCESS = 0, SKIPPED = 0**.
- Ни одного потерянного/дважды выполненного уникального ID, 8/8 согласованных `suiteSHA256`.
- Контрольная сумма общей коллекции: `0d3d640e7cd5df4a519dd77bc2b05dac0985e6412503f063a619f43e64937244`.
- 8 шардов: `0:84 (XFAIL1), 1:99 (XFAIL0), 2:120 (XFAIL2), 3:99 (XFAIL1), 4:89 (XFAIL2), 5:69 (XFAIL0), 6:81 (XFAIL2), 7:94 (XFAIL0)`; сумма 735.
- Все XFAIL из независимого QA набора `test_archicad_independent_provider_audit.py`; они **не означают, что дефекты исправлены**.

Непосредственный CI-вывод финальной агрегации: `APA_PARALLEL_AGGREGATE: discoveredTests=735, testsRun=735, failures=0, errors=0, expectedFailures=8, unexpectedSuccesses=0, issues=[]`. `APA_MATRIX_JOB_STATUS` подтверждает 4 success: shards, graph, core, static.

## Остальные группы, выполненные параллельно

| Проверка | Реальное подтверждение |
| --- | --- |
| Upstream Knowledge Graph | **102/102 PASS**, отдельный Windows job |
| Существующий MCP stdio / core integration | `APA_CORE_AND_STDIO_INTEGRATION_PASS`, 9 core-сценариев, plan revision 163 |
| Archicad batch contracts | PASS |
| BIM Graph offline sample | PASS |
| Python tracked syntax | **181/181 PASS** |
| JSON tracked parse | **93/93 PASS** |
| PowerShell tracked parse | **4/4 PASS** |
| Пересечение и полнота 8 шардов | PASS, агрегирующий job |

Дополнительно исходный PR #88 прошёл свой штатный Windows CI [#38648982543](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38648982543): **744/744 unittest-вхождений и 102/102 upstream graph tests**, без независимых 28 тестов PR #87. Числа 744 и 735 **нельзя складывать как независимые**: основная часть тестов перекрывается, а новые QA cases и исключённые дубликаты меняют подсчёт.

## Восемь подтверждённых ещё не исправленных дефектов (XFAIL)

1. Неатомарная регистрация duplicate add-on command может оставить чужую общую схему изменённой.
2. Коллизия имён схем: `A__B/C` и `A/B__C` могут дать одинаковый ключ.
3. `_schema_at` принимает относительный JSON Pointer, `_result_at` отклоняет.
4. JSON Pointer с пустым именем свойства `/a/` обрабатывается неверно.
5. JSON Pointer с отрицательным индексом массива `/arr/-1` допустим в runtime, хотя должен отклоняться.
6. GUID `ownerWallId.guid` вне affected/retained может не попадать в scope-проверку (native exploitation **не** доказана; SceneWriter сохраняет дополнительные барьеры).
7. Успешный ответ с полем `error: null` ошибочно трактуется как failure.
8. Пример параметра, синтезируемый `_schema_example`, нарушает JSON Schema `maximum:0`.

Каждый XFAIL реально зарегистрирован unittest на **импортируемых исходных классах APA**, а не только на копии алгоритма. Более широкий список пограничных кейсов документирован в [PR #86](https://github.com/dvikt33-ux/safe-bim-layer/pull/86) и [PR #87](https://github.com/dvikt33-ux/safe-bim-layer/pull/87). Приоритет исправления перед массовой записью новых модулей: атомарность регистрации, коллизии схем и fail-closed область GUID.

## Границы доказательств

- Проверены все обнаруженные в `tests/` Python unittest и все отслеживаемые Python/JSON/PowerShell исходники; upstream KG, MCP и batch/graph — отдельно.
- **Не исполнялись:** C++ компиляция/линковка нового Archicad APX без соответствующего DevKit в GitHub-runner, LIVE Native SDK/PLN, реальный runtime всех сторонних расширений, ручные операции в Archicad, содержательные инженерные расчёты. Эти категории требуют отдельного Windows SDK/Archicad окружения и никогда не объявляются PASS только по JSON-схеме.
- Параллелизация уменьшает последовательное время выполнения unit-сценариев, но каждый из 8 Windows runners отдельно устанавливал зависимости; измеренного ускорения относительно последовательного CI **не заявляем**. Возможные будущие улучшения: кэш зависимостей и балансировка по длительности, а не только по SHA ID.
- Конкретные дефекты переданы разработчику через исследовательские PR, не блокируя независимую интеграцию новых SDK/APX и не изменяя исходный функциональный PR #88.

## Состав PR #89

- `scripts/apa_parallel_unittest_shard.py`: детерминированная SHA-256 разбивка, единый ID, отчёты по тестам, сохранение provenance дубликатов.
- `scripts/apa_parallel_offline_aggregate.py`: проверка 8/8, контроль списка ID, одинаковых SHA и суммарных результатов.
- `scripts/apa_repo_offline_static_audit.py`: проверка всех отслеживаемых файлов Python и JSON.
- `tests/test_archicad_independent_provider_audit.py`: 28 адресных проверок, 8 известных XFAIL.
- `.github/workflows/apa-mass-parallel-offline.yml`: 8 параллельных Windows шардов + graph + core + static + aggregate.

**GitHub является источником правды**: ссылки на реальные CI run, SHA и коммиты обязательны, локальная работа без публикации не считается законченной. Статус канонической задачи A11.S03 этот QA-проход самостоятельно не изменяет; приёмка результатов производится через существующий реестр.


## Верификация публикации следующего коммита Work

Пока выполнялись массовые тесты, Work опубликовал дополнительный head PR #88 `a444d5a6b481bfabd9c48f23c17df05c51ab0ea4`. GitHub compare `07e73f9... → a444d5a...` показывает **ровно один дополнительный коммит, два изменённых файла: `docs/APA_FUNCTIONAL_MODULES.md` и новый `docs/evidence/APA_FUNCTIONAL_MODULE_BUILD.json`**. Никакой Python/C++ исходник или тест не изменён, поэтому результаты массовой проверки кода остаются применимы.

Новый JSON receipt отдельно успешно разобран. Его статус `BUILD_PASS_BINARY_IDENTITY_VERIFIED_NOT_INSTALLED` с 281 source registrations (280 Tapir + 1 DevKit namespace), 5 SDK-контрактами и сохранёнными 12 candidate commands. Однако запись прямо указывает `runtimeRegistration=NOT_VERIFIED` и `liveVerification=NOT_RUN`. Это отчёт о сборке, не доказательство работы с установленным Archicad. На новом SHA также завершился отдельный стандартный Windows CI [#38649371374](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38649371374) со статусом SUCCESS.

