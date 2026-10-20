# APA №2 — интеграция готовых решений, 2026-10-20 01Z

**Опубликован комплект отчёта:** 30 SOURCE-проверок по первоисточникам, 2 независимых контрааудита, 9 маршрутов, альтернативы, гейты и передача №3. Новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE. Никаких установок, живых операций, изменений кода/PLN/APX/main/канона/NEXT.

**Проверки:** [01–05](research-2-integration-2026-10-20T01Z-checks-A.md), [06–10](research-2-integration-2026-10-20T01Z-checks-B.md), [11–15](research-2-integration-2026-10-20T01Z-checks-C.md), [16–20](research-2-integration-2026-10-20T01Z-checks-D.md), [21–25](research-2-integration-2026-10-20T01Z-checks-E.md), [26–30](research-2-integration-2026-10-20T01Z-checks-F.md).

**Матрица:** [I00-01..03](research-2-integration-2026-10-20T01Z-matrix-A.md), [I00-04..06](research-2-integration-2026-10-20T01Z-matrix-B.md), [I00-07..09](research-2-integration-2026-10-20T01Z-matrix-C.md). [Два контрааудита](research-2-integration-2026-10-20T01Z-audits.md). [Альтернативы, гейты, вопросы №1, передача №3](research-2-integration-2026-10-20T01Z-handoff.md).

**Контроль:** [№3 00Z](audit-2026-10-20-00-tasks-2.md), [№2 00Z](research-2-integration-2026-10-20T00Z.md), последний основной [№1 18Z](research-1-20261019T18Z.md). Новых основных №1 в каталоге не найдено. 61/61 уникальных ID и формул проверены; benchmark 0, live_accepted 0. Текущий канон revision197, исторический rev182 только чтение.

**Новые важные находки:** Tapir1.5.9 уже предоставляет Publisher GUID tree и native CreateWindows/CreateDoors; не нужен новый writer. Однако tree может скрыть ошибку чтения детей, а PDF-метки не дают wall GUID/offset. Существующие Router, SDK Bridge, C1, IFC V2, BIM Graph и SceneWriter переиспользуются. Готового полного end-to-end XCLIP или PDF→host adapter в проверенных источниках не найдено.

**Статус:** SOURCE_RESEARCH_COMPLETE; PUBLICATION_READBACK_PENDING до проверки этого индекса. Это не приёмка интеграции.
