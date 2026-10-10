# APA-P10.A02.S01 — Tapir upstream 1.5.9 / 1.6.0 / 1.7.0 vs локальная модифицированная 1.5.10

**Run:** `APA-RUN-20261010-163950Z-tapir-compat-6f29` · **Phase:** SOURCE · **Task:** `APA-P10.A02.S01` · **Executor:** `chatgpt:apa-technical` · **Дата:** 2026-10-10.

## 1. Версионированная матрица

Официальные теги Tapir проверены по Git refs и исходникам (не по поисковым сниппетам):

| Upstream | Git commit | Released (UTC) | GetStories top-height fix | Slab bbox safe 3D branch | GetIFCExportTranslators | SetIFCPropertiesOfElements |
|---|---|---|---|---|---|---|
| 1.5.9 | `d0dbb11b13942e014661e1402b07958b70cd9dba` | 2026-09-09 | Нет в проверенной ветке | Нет в проверенной ветке | Не зарегистрирована | Не зарегистрирована |
| 1.6.0 | `e0d4cca231f15c99da0b91cb2e591ab3758ae97a` | 2026-09-30 | Да | Да | Зарегистрирована | Не зарегистрирована |
| 1.7.0 | `02691b5d680b60c73317e8e49b78ab14dfd4c9d8` | 2026-10-04 | Да | Да | Зарегистрирована | Зарегистрирована |
| Локальная изменённая 1.5.10 | **UNKNOWN** | **UNKNOWN** | **NOT_VERIFIED** | **NOT_VERIFIED** | **NOT_VERIFIED** | **NOT_VERIFIED** |

Источники: [1.5.9 tag](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/d0dbb11b13942e014661e1402b07958b70cd9dba), [1.6.0 tag](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/e0d4cca231f15c99da0b91cb2e591ab3758ae97a), [1.7.0 tag](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/02691b5d680b60c73317e8e49b78ab14dfd4c9d8), [release 1.6.0](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.6.0), [release 1.7.0](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.0).

Проверено наличие `RegisterCommand<...>` в `AddOnMain.cpp` каждого из трёх SHA и конкретные функции `GetStoriesCommand::Execute` и `Get3DBoundingBoxesCommand::Execute`. Это **SOURCE_VERIFIED** по upstream, не доказательство функциональности установленного APX.

## 2. Python/JSON — отдельный слой, не новая native реализация

Файл `archicad-addon/Examples/aclib/__init__.py` **текстуально идентичен** во всех трёх прочитанных upstream commits (1.5.9/1.6.0/1.7.0). Его `RunTapirCommand` вызывает JSON API команду `API.ExecuteAddOnCommand` с `addOnCommandId.commandNamespace="TapirCommand"` и `commandName` ([1.7.0 lines 46–69](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Examples/aclib/__init__.py#L46-L69)). Это обёртка над HTTP/JSON интерфейсом Archicad, а не собственный Python-движок BIM-геометрии. Наличие Python-скрипта не доказывает, что соответствующая команда зарегистрирована в установленном APX.

Конкретные особенности [upstream aclib lines 5–44](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Examples/aclib/__init__.py#L5-L44):
- `--host` и `--port` допускают явный адрес, но значение по умолчанию `127.0.0.1:19723`. Несколько экземпляров Archicad требуют проверки адресата **до** запросов; порт сам по себе не удостоверяет файл/процесс.
- `urllib.request.urlopen(connection_object, request_string)` не задаёт timeout; HTTP exception не преобразуется в нормализованный BIM-result.
- При отсутствии `succeeded` или `result` функция возвращает `None`; при `succeeded=false` тоже возвращает `None`.
- `RunTapirCommand` извлекает `commandResult['addOnCommandResponse']`; если nested `error` присутствует, код его печатает, но **возвращает** response. Без внешней проверки легко принять ошибочный ответ за нормальный.
- [`CommandBase.cpp`](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/CommandBase.cpp#L7-L64) использует namespace `TapirCommand`, планирует вызовы в main thread, а некоторые команды возвращают `{"success":false,"error":...}`. Нельзя смешивать верхний `succeeded`, вложенный `success` и наличие `error`.

Пример [GetSectionElements Python](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Examples/get_section_elements.py) подтверждает комбинирование `API.GetNavigatorItemTree` и `TapirCommand.GetSectionElements`; пример [MEP](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Examples/mep_elements.py) вызывает `GetMEPPorts` и `GetMEPDistributionSystems`, но также **создаёт, изменяет и удаляет** элементы — его нельзя запускать как read-only тест.

## 3. Существенные различия версий для APA

**GetStories:** [1.7.0 lines 748–790](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/ProjectCommands.cpp#L748-L790) вычисляет число записей из размера handle, включая виртуальный этаж над последним реальным, и рассчитывает `height` для верхнего этажа. В 1.5.9 такого `recordCount` нет; изменение заявлено в [PR #670](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/670), вошло в 1.6.0. В модели APA верхний этаж не равен «нулевой высоте» при отсутствии поля.

**Get3DBoundingBoxes:** [1.7.0 lines 4258–4305](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/ElementCommands.cpp#L4258-L4305) направляет `Slab`, `Roof`, `Zone` на `CalculateSolidBodyBounds`. Комментарий в коде описывает crash risk `ACAPI_Element_CalcBounds` для Slab, не отображённого в текущем окне; fallback для Slab намеренно отсутствует. В 1.5.9 этой ветки нет; исправление [PR #694](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/694) вошло в 1.6.0. **Не вызывать Slab bbox на рабочем PLN до подтверждения бинарной реализации локального APX.**

**Команды:** `GetAddOnVersion`, `GetStories`, `Get3DBoundingBoxes`, `GetProfiles`, `GetMEPPorts`, `GetMEPPreferenceTables`, `GetGeoLocation`, `GetDetailsOfElements` зарегистрированы во всех трёх проверенных upstream `AddOnMain.cpp`; `GetIFCExportTranslators` появляется к 1.6.0, `SetIFCPropertiesOfElements` к 1.7.0. [1.7.0 ApplicationCommands.cpp lines 55–86](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/ApplicationCommands.cpp#L55-L86) показывает, что `GetAddOnVersion` возвращает `ADDON_VERSION`, но эта строка **не** доказывает SHA или идентичность бинарника.

**Локальная 1.5.10:** Git ref `refs/tags/1.5.10` в upstream возвращает 404; это не доказательство отсутствия локальной версии, а лишь отсутствия **этого публичного тега**. Для модифицированного локального APX нет доступного в этом запуске подтверждённого source SHA, binary SHA и manifest. Не утверждать, что upstream 1.6/1.7 fixes отсутствуют в локальной сборке.

## 4. Архитектуры A/B и решение

| Критерий | A. Сохранить установленный Tapir и выборочно backport | B. Заменить на upstream 1.7.0 |
|---|---|---|
| Локальные расширения APA | Сохраняются при provenance-first и контролируемом патче | Требуется diff, возможна потеря кастомных команд |
| Исправления Slab/top-story | Сначала проверить локальные исходники и APX | Есть в upstream исходниках |
| Python/JSON транспорт | Та же upstream aclib, нужен строгий guard | Та же upstream aclib, guard также нужен |
| Сборка и риск | Точечная проверка/патч при необходимости | Полная миграция и регрессии |
| Время/производительность | NOT_MEASURED | NOT_MEASURED |

**Предварительный выбор A** для быстрого MVP: read-only provenance (`APA-P20.A01.S01`), список доступных команд (`APA-P20.A01.S02`), source-diff и лишь затем точечный backport. Не устанавливать новый APX автоматически. B не исключать по факту существования A; пересмотреть после матрицы локального diff и регрессий.

## 5. Evidence, acceptance и границы

- SOURCE: **VERIFIED** — 3 Git refs, релизы, точные функции и Python aclib прочитаны; сравнительная матрица upstream составлена.
- OFFLINE: source-level сравнительная проверка в этом исследовании, **без запуска test suite**; статус `TEST_REQUIRED`, не `OFFLINE_PASS`.
- BUILD: **NOT_RUN**. LIVE: **NOT_VERIFIED**. Изменения PLN/APX: **0**. Performance: **NOT_MEASURED**.
- Acceptance `APA-P10.A02.S01` — «Compatibility matrix с source SHA»: для upstream **выполнено**, для **локальной модифицированной 1.5.10 не выполнено** (нет provenance), поэтому итог задачи **PARTIAL**, не DONE_PUBLISHED.
- Read-only gate: удостоверить PID, порт, Archicad project identity и APX SHA; сверить установленный binary с локальными исходниками и diff upstream, безопасно вызвать `GetAddOnVersion`/проверить `IsAddOnCommandAvailable`, только затем безопасные GetStories/GetProfiles; Slab bbox — только после статического подтверждения safe branch.
- PASS — независимая локальная матрица команд/исправлений + SHA source/binary, совпадение readback и отсутствие скрытых ошибок. FAIL — доказанный конфликт команд/ответов. NOT_VERIFIED — нет бинарного происхождения или endpoint identity.

## 6. Новая задача-кандидат для аудита

[APA-CAND-20261010-tapir-json-envelope-6f29](../../control/proposals/APA-CAND-20261010-tapir-json-envelope-6f29.md): отдельная offline проверка fail-closed Python JSON response envelope, timeout и адресата. **PENDING_AUDIT**, не добавлена в `PROJECT_PLAN.json`. Дубли с `APA-P20.A01.S01/S02` аудитор обязан проверить; допустимо отклонить как DUPLICATE.

**Следующая eligible RESEARCH задача:** `APA-P10.A02.S02` (GDL/TN, Unicode и 92 ошибки), после нового чтения плана и подтверждения отсутствия claim.

**Безопасность:** только upstream source/GitHub метаданные, запись исследовательских файлов в canonical research branch. Ни main, ни PLN, ни APX, ни протестированные ветки не изменялись.


## 7. Публикация V2 заблокирована контроллерными тестами (2026-10-10)

- GitHub inbox: [PUBLISH_REQUEST_V1](../../inbox/APA-RUN-20261010-163950Z-tapir-compat-6f29.json) — commit `792b84804cbee8faf49cc91ef414bfbe6a4ffd71`, readback PASS.
- [GitHub Actions run 38068756071](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38068756071): **FAIL** на шаге `Project Controller DAG, claim and dispatch tests`. Следующие шаги публикации skipped; `REPORT.md` V2, receipt и generated index НЕ подтверждены.
- Статический анализ [test_controller.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/tools/apa_controller/tests/test_controller.py#L93-L128) выявил **вероятную причину**: тесты `test_unclaimed_active_rejected` и `test_new_inbox_must_be_claimed_and_owned` используют реальный `APA-P10.A02.S01` как заведомо незанятый fixture. В текущем `PROJECT_PLAN.json` этот S-ID законно `IN_PROGRESS`, поэтому ожидания тестов не изолированы от live controller state. **Точный traceback CI недоступен через используемый GitHub connector**; причина пока SOURCE_DIAGNOSIS / NOT_RUN, не подтверждённый test PASS/FAIL конкретного assertion.
- Для исправления в отдельной зарегистрированной задаче: строить fixture из копии плана и явно обнулять owner/lease/claim_ref для ожидаемого READY состояния; тестировать CLAIMED/IN_PROGRESS независимо от текущих реальных статусов. Проверить на реальном активном claim и затем повторить publisher.
- Этот flat Markdown — **резервная долговременная публикация**, а не receipt V2. Не объявлять DONE_PUBLISHED, пока publisher не завершил работу.
