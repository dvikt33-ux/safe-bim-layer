# APA №2 | 23.10.2026 11Z | BUILD-01 — INDEX

## Конкретный новый результат P0

**G1 (100/100):** `SceneWriter.scan_for_existing_geometry` использует `GetModelDumpV1` **условно** при sentinel bbox существующих элементов. Для **доказанно пустой scratch PLN** (`GetAllElements.elements=[]`) этот вызов не нужен. Поэтому read-only preflight PR74 можно планировать без обязательного BREP на G1; G4 BREP по-прежнему обязателен. **Это SOURCE-маршрут, не проведённый OFFLINE_PASS.**

**G2 (99/100):** существующий readback Door/Window проверяет native type/host/размеры, но не конкретный GDL `libraryPartName/favoriteName`; sample не фиксирует эти поля. Не считать идентичность окон/дверей принятой без read-only catalog и независимого runtime readback. **G2 (99/100):** sample содержит literal material GUID, который нельзя переносить между scratch PLN без GetAttributesByType. **G3/G4 (100/100):** sample flags `nativeGeometryAudit/nativeRoofJunctions=true` требуют GetModelDumpV1, которого нет в pinned 262; локальный installed contract неизвестен.

## Публикация и доказательства

Все **7 приложений** созданы `create_file` с явной веткой, каждое отдельно прочитано `fetch_file` и сравнено по полному тексту; blob SHA зафиксированы в манифесте. Манифест опубликован и прочитан **до** этого индекса.

- [Инженерный отчёт](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-report.md) — G1/G2/G3/G4 и SOURCE/статусы.
- [SOURCE S01–S15](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-checks-A.md) — 15 прямых file checks.
- [SOURCE S16–S30](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-checks-B.md) — 11 file checks + 4 контрольных документа/issue; всего **30** прямых проверок.
- [Матрица 9 интеграций](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-matrix.md) — конкретные функции, поля, версии, блокеры, критерии ГОТОВО.
- [Контрааудит A](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-audit-A.md) — условность BREP на G1.
- [Контрааудит B](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-audit-B.md) — неполнота GDL readback.
- [Контроль 06Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-06Z-status.md) — 4 оригинальных приложения и recovery index сохранены, основной оригинал отсутствует; PARTIAL_NOT_ACCEPTED.
- [SHA-манифест](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T11Z-sha-manifest.json) — семь blob SHA-1, семь create commit SHA, 7/7 exact readback; blob манифеста `c9c2a2c977f0e0fe9058aac5ad31116d3417529a`, commit `0bbeec73c647710b90f683cdf5c34aeddfe6dd0a`.

**SOURCE=30 · OFFLINE=0 · BUILD=0 · INSTALLED=0 · LIVE=0 · ACCEPTED=0.** G0 BLOCKED; G1 SOURCE_ROUTE_NOT_RUN; G2 SOURCE_ONLY/DUAL_SCOPE_AND_GDL_BLOCKED; G3 NOT_AUTHORIZED; G4 BREP_NOT_PROVEN; G5 NOT_RUN. Ни одного нового здания. Не менялись NEXT, main, PLN/APX, код; не запускались установка, native WRITE, Work/Codex/Arena, PR merge. **MODEL_MODE_NOT_VERIFIABLE**.
