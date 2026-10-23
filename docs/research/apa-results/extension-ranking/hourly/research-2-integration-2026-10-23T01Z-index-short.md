# APA №2 — BUILD-01, 01Z

**G3:** GetAllElements возвращает optional executionResultForDatabases; текущий SceneWriter не проверяет это поле. Для поэтажного inventory требуется fail-closed проверка всех БД. Пропуск второго этажа НЕ доказан.

**G2:** CreateSlabs без material; ModifySlabs с material. Существующий SceneWriter использует обе операции. **G0:** установленный APX SHA и GetModelDumpV1 не подтверждены.

[Проверки 01–15](research-2-integration-2026-10-23T01Z-checks-A.md) · [16–22](research-2-integration-2026-10-23T01Z-checks-B1.md) · [23–30](research-2-integration-2026-10-23T01Z-checks-B2.md) · [9 маршрутов](research-2-integration-2026-10-23T01Z-matrix-short.md) · [А](research-2-integration-2026-10-23T01Z-audit-A-short.md) · [Б](research-2-integration-2026-10-23T01Z-audit-B-mini.md) · [06Z](research-2-integration-2026-10-23T01Z-06Z-status-mini.md) · [SHA](research-2-integration-2026-10-23T01Z-sha-manifest.json).

SOURCE=30; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. 06Z PARTIAL_NOT_ACCEPTED. MODEL_MODE_NOT_VERIFIABLE.
