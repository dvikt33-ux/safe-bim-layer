# APA №2 — 2026-10-24 04Z | Публикационный индекс

**Новая дельта:** официальный AC29 Rhino Hotlink сохраняет Rhino original ID в свойствах импортированного .gsm, но не native Wall/Slab/Roof; hidden geometry/Surfaces/Layers/Embedded Library и Relink/Undo — риски. Неассоциативный Crop to Single-plane Roof может расщепить Wall; существующий PR74 ограничивает ассоциативный SEO одной Roof. SOURCE_ONLY.

- [Полный инженерный отчёт](research-2-integration-2026-10-24T04Z-report.md) — 10 маршрутов, версии/лицензии, ownership, G0→G5, Save/Open.
- [30 документарных SOURCE-проверок](research-2-integration-2026-10-24T04Z-checks.md) — ссылки и конкретные факты.
- [Два документарных контрааудита](research-2-integration-2026-10-24T04Z-audits.md) — provenance/sync и roof/BREP/rollback.

**Гейты:** SOURCE=30 checks; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. FULL_3WAY_NATIVE_SYNC=NOT_FOUND. MODEL_MODE_NOT_VERIFIABLE.

**Политика:** только исследовательская ветка `research/apa-extension-ranking-hub-20261018`; main, код, PLN/APX, установки, LIVE, Work/Codex/Arena, платные API, merge не трогались. Исторический PROJECT_PLAN rev182 — только чтение. **Публикационный SHA/commit receipt выдаётся после create_file→fetch_file и независимого Git blob SHA-1 сравнения; индекс не содержит выдуманных хешей.**
