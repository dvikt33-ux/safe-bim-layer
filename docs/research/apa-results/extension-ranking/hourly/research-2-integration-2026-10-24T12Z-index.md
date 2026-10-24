# APA №2 | 2026-10-24 12Z | Индекс и квитанция публикации

**P0-дельта:** GH-created native BIM зависит от скрытых AC Tool Defaults; только один .gh может быть подключён; модальный диалог AC приостанавливает GH связь; Copy/Paste GH-native теряет GH provenance; Content Cache Purge потенциально удаляет definitions. Готового native AC↔GH↔Rhino commit/rollback нет.

- [Инженерный отчёт с 10 маршрутами](research-2-integration-2026-10-24T12Z-report.md)
- [30 предметных SOURCE-проверок](research-2-integration-2026-10-24T12Z-checks.md)
- [Два внутренних контрааудита](research-2-integration-2026-10-24T12Z-audits.md)

**Приёмка публикации:** создавать с явным `branch=research/apa-extension-ranking-hub-20261018`; повторно читать каждый файл через `fetch_file`; сравнить точный UTF-8 текст, Git blob SHA-1 и сохранить commit SHA из `create_file`. Если любой шаг не выполнен — `WRITE_BLOCKED`, не `VERIFIED`.

**Состояние BUILD-01:** SOURCE=30, OFFLINE=0 новых, BUILD=0, INSTALLED=NOT_VERIFIED, LIVE=0 новых, ACCEPTED=0; G0 BLOCKED_RUNTIME, G1 NOT_RUN, G2 SOURCE_PARTIAL, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. main, исходники, PLN/APX, установка, LIVE, Work/Codex/Arena, платные API и merge не выполнялись. MODEL_MODE_NOT_VERIFIABLE.
