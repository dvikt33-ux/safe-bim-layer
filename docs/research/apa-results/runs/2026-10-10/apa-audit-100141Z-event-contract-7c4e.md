# APA — независимый аудит, 2026-10-10T10:01:41Z

**ПЛАН:** APA-P00 — Централизация результатов.
**ДЕЙСТВИЕ:** APA-P00.A03 — Режим публикации.
**ПОДШАГ:** APA-P00.A03.S01 — Проверка GitHub write/read и качества событий.
**RUN_ID:** APA-RUN-20261010-100141Z-7c4e.
**Среда:** ChatGPT Plus; GitHub/Slack connectors. Archicad 29 build 5101 — целевая, live-вызовов нет.

## Источники и границы
Прочитаны [PR #22](https://github.com/dvikt33-ux/safe-bim-layer/pull/22), документы README, research-register, CURRENT_BLOCKERS, PUBLISHING_PROTOCOL, MASTER_PLAN, CURRENT_STATUS, RESEARCH_QUEUE, ARTIFACT_REGISTER и единственный прежний [run](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-technical-20261010-094254-publisher-layout-01.md). Сопоставлены [PR #16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [#17](https://github.com/dvikt33-ux/safe-bim-layer/pull/17), [#20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [#21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21). Прочитаны сообщения Slack #apa-research до 12:31 MSK.

## Находка 1 — конфликт контракта событий
**Гипотеза:** часть сообщений APA_EVENT_V1 не может попасть в SQLite приёмник.
**SOURCE/CONFLICT:** сообщение Slack 10.10 12:24:03 MSK, TS 1791624243.296309, [ссылка](https://app.slack.com/archives/C0C886E1PGR/p1791624243296309), имеет phase=AUDIT и JSON в одиночных обратных кавычках. В [coordinator.py PR #21](https://github.com/dvikt33-ux/safe-bim-layer/blob/1a6c5e62ab3bd0f262bd3ba89445e8d4199e9123/scripts/apa_sync/coordinator.py) PHASES ограничены SOURCE/OFFLINE/SYNTHETIC/BUILD/LIVE, а EVENT_PATTERN требует тройной Markdown fence. Это две независимые причины отказа parse_event. [socket_mode.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/1a6c5e62ab3bd0f262bd3ba89445e8d4199e9123/scripts/apa_sync/socket_mode.py) пропускает InvalidEvent при bootstrap. **Не утверждается фактическая потеря запущенным демоном:** Socket Mode NOT_DEPLOYED.

**OFFLINE/PASS (только минимальная проверка regex):** точные EVENT_PATTERN и PHASES применены к форме события: inline_match=False, fenced_match=True, AUDIT_allowed=False. Это не live-испытание.

**Риск MVP:** неполный журнал противоречий и блокировок; повторение работы между чатами.
**Альтернативы:** A — строгий единый форматтер/валидатор с явным reject и тестами (предпочтительно); B — произвольный JSON и фазы (выше риск неоднозначности).
**Следующий тест:** оригинальный parse_event с двумя фикстурами (невалидное 12:24 и валидное 12:31), затем fake Slack bootstrap. PASS — валидные принимаются, неверные диагностируются, состояние не объявляется синхронизированным при отказе. FAIL — silent loss/ложная доставка. LIVE — NOT_VERIFIED.

## Находка 2 — предел 22/22 BIM-классификации
**Гипотеза:** новый результат PR #20 классифицирует элементы, но не подтверждает полную 3D-геометрию.
**SOURCE/INFO:** [PR #20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20) сообщает о read-only 22/22 GUID (18 Object, 4 Elevation), но raw локальный JSON независимо не получен: **REPORTED LIVE; independently LIVE NOT_VERIFIED**. В [Tapir ElementCommands.cpp 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp) прочитаны реальные реализации GetDetailsOfElements и Get3DBoundingBoxes: fields=[type,floorIndex,layerIndex] избегает ненужных полей; bbox использует CalcBounds для многих типов и не удостоверяет BREP. [Официальный GetAllElements](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.html) не доказывает идентичность охвата с Tapir. Код модифицированного установленного 1.5.10 не сверялся с upstream 1.5.9. [Лицензия Tapir MIT](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/LICENSE).

**Риск MVP:** ошибочно принять классификацию GUID/bbox за безопасное размещение GDL и проверку коллизий.
**Альтернативы:** A — дешёвая классификация + отдельный native body/3D visibility audit (предпочтительно); B — bbox-only, неполное доказательство.
**Следующий тест:** на одной неизменной копии PLN сравнить GUID обоих API, типы, layer и физические body для каждого Object; Elevation считать документным типом. PASS — каждый физический GUID имеет body либо обоснованное исключение; FAIL — необъяснённые пропуски. Производительность NOT_MEASURED.

## Фазовая матрица и решение
- PR #16: SYNTHETIC/OFFLINE reported PASS; создание сцены LIVE NOT_VERIFIED.
- PR #17: BUILD reported PASS; SyncGuids LIVE NOT_VERIFIED.
- PR #20: read-only LIVE reported; независимый readback raw logs NOT_VERIFIED.
- PR #21: OFFLINE 18/18 reported PASS; Socket Mode LIVE NOT_VERIFIED.
- Текущий аудит: SOURCE подтверждён по коду; OFFLINE минимальный regex PASS; никакого Archicad LIVE PASS.

**Приоритет:** сначала устранить форматный конфликт синхронизации, затем подтвердить body coverage перед GDL-записью. PLN, APX, исходники, main/master не менялись.

## Публикация
Branch: research/apa-verified-results-hub-20261010.
Path: docs/research/apa-results/runs/2026-10-10/apa-audit-100141Z-event-contract-7c4e.md.
Commit SHA и GitHub readback фиксируются **только после** подтверждённой записи; Slack событие только после readback.
