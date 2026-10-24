# APA №2 — 2026-10-23 20Z — индекс после readback
**Главный вклад BUILD-01 G4:** обнаружен штатный IFC BREP экспорт через pinned Tapir1.5.10 + существующий защищённый PR74 documentation/SceneWriter/SQLite маршрут PublishPublisherSet. Истинный независимый IFC/OpenCASCADE readback — SOURCE_CANDIDATE, не ACCEPTED. Критический риск: Publisher экспортирует только видимые элементы. `IFCFileOperation` direct save существует, но не включён в PR74 DOCUMENT_COMMANDS — обходить журнал нельзя.

- [Полный отчёт](research-2-integration-2026-10-23T20Z-triad-report.md)
- [Матрица 10 маршрутов](research-2-integration-2026-10-23T20Z-triad-matrix.md)
- [30 SOURCE-проверок](research-2-integration-2026-10-23T20Z-triad-checks.md)
- [Два контрааудита](research-2-integration-2026-10-23T20Z-triad-audits.md)
- [SHA-манифест, Git blob SHA-1 + commits](research-2-integration-2026-10-23T20Z-triad-sha-manifest.json)

Все 5 предшествующих файлов созданы в ветке `research/apa-extension-ranking-hub-20261018`, fetch_file прочитал полный текст, exact comparison = PASS. Git blob SHA-1/commit каждого — в манифесте. SHA256 исходных research-файлов не вычислялся. SOURCE=30 assertions; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. G0 BLOCKED_RUNTIME, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4 SOURCE_CANDIDATE_NOT_RUN, G5 NOT_RUN. BUILD-01 не создан; FULL_THREE_WAY_SYNC=NOT_FOUND. PROJECT_PLAN rev182 NOT_READ. 06Z PARTIAL_NOT_ACCEPTED. MODEL_MODE_NOT_VERIFIABLE.
