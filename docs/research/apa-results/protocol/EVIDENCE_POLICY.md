# APA Research OS — политика доказательств и воспроизводимости

**ПЛАН:** APA-P00 → **ДЕЙСТВИЕ:** APA-P00.A03 → **ПОДШАГ:** APA-P00.A03.S03. **Статус:** POLICY_PUBLISHED; runtime validation NOT_DEPLOYED.

## Независимые оси состояния

**Публикация:** DRAFT / EVIDENCE_READY / COMMITTED / READBACK_VERIFIED / INDEXED / DONE_PUBLISHED / GITHUB_PUBLISH_BLOCKED / PUBLISH_READBACK_FAILED.

**Достоверность утверждения:** USER_SUPPLIED / REPORTED / SOURCE_VERIFIED / NOT_VERIFIED / TEST_REQUIRED / OFFLINE_PASS / BUILD_PASS / LIVE_PASS / CONFLICT. Эти две оси нельзя смешивать: `GITHUB_READBACK_VERIFIED` доказывает наличие файла, **не** корректность Archicad API или результат live-теста.

**Применимость:** версии Archicad, SDK, Tapir, установленного APX, source SHA, PLN context, test date и ограничения; если неизвестно — NOT_VERIFIED. Данные разных PLN и разных каталогов нельзя смешивать.

## Проверка и цитирование

1. `SOURCE_VERIFIED` — первичный официальный документ или точный исходный код прочитан; сохранить постоянный URL, tag/commit, конкретную функцию/фрагмент и дату. Поисковый сниппет не достаточен.
2. `REPORTED` — утверждение присутствует в переданном отчёте, Slack, PR или чужом логе, но не воспроизведено. Ссылка на PR не делает его `LIVE_PASS`.
3. `OFFLINE_PASS` — выполнена конкретная локальная/статическая проверка с тестовыми входами и результатом; не повышать до BUILD/LIVE.
4. `BUILD_PASS` — сборка подтверждена для конкретного SDK/конфигурации, но runtime не проверен.
5. `LIVE_PASS` — конкретная операция выполнена на идентифицированной изолированной среде с raw readback; разрешение на writer обязательно.
6. `NOT_VERIFIED — DOCUMENT_NOT_READ` — исходник не прочитан; не подменять общей модельной осведомлённостью.
7. `USER_SUPPLIED_REPORT` — исходный текст сохранён по предоставленному владельцем файлу. Его исторические filecite/cite-маркеры не являются автоматически разрешимыми GitHub-ссылками.
8. Сведения о возможности write/schedule/Deep Research/Opera фиксируются **по конкретной сессии**; устаревший результат не переносить на другие чаты.

## Обязательные поля evidence

`evidence_id`, `uri`, `kind`, `verification`, `source_revision` (если известна), `sha256` (если фактически вычислен). Никогда не подставлять выдуманный hash. Отдельно связывать `claim_id` с `evidence_ids`.

## Безопасность

Не публиковать токены, персональные данные, приватные логи, коммерческие библиотеки, PLN, APX. Main/master, проверенные ветки, BIM-модели и установленные Add-On не изменять без отдельного разрешения. Не запускать Deep Research/Work/Codex/платные модели без разрешения.

**Связано:** [RUN_EVENT_V2.schema.json](RUN_EVENT_V2.schema.json), [PUBLISHER_CONTRACT.md](PUBLISHER_CONTRACT.md), [AGENT_PROTOCOL](../AGENT_PROTOCOL.md).
