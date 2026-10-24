# APA №2 | 2026-10-24 09Z | индекс и контроль публикации

**Главный P0:** native Beam для APA-owned элементов **SOURCE_ROUTE_FOUND** через существующий `archicad_connected_components.py` CLI (`enabled:['beam']` → typed `CreateBeams` → тот же SceneWriter/SQLite), но не через authored `nativeComponents`. Нужен уже принятый source receipt и отдельная санкционированная фаза. Это не новая модель BUILD-01 и не новый writer. **Rhino 8 GrasshopperPlayer** — готовый локальный запуск существующего `.gh`, не глобальный синхронизатор.

- [Полный инженерный отчёт](./research-2-integration-2026-10-24T09Z-report.md) — 10 маршрутов, G0–G5, GUID/BREP/owner/Save/Open.
- [26 проверенных SOURCE-фактов](./research-2-integration-2026-10-24T09Z-checks.md) — 15 официальных HTML + 11 GitHub static.
- [Два документарных контрааудита](./research-2-integration-2026-10-24T09Z-audits.md) — false-negative Beam и false-positive GHPlayer.

**Статусы:** SOURCE=26; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. Native full triad synchronization = NOT_FOUND.

**Публикационная процедура:** явный branch `research/apa-extension-ranking-hub-20261018`, create_file → fetch_file → exact UTF-8 content comparison → Git blob SHA-1 and commit SHA. Квитанции SHA/commit выдаются отдельно после фактического readback, не подменяются заранее вписанными значениями. При отказе WRITE_BLOCKED. Main/код/PLN/APX/исторический PROJECT_PLAN rev182 не изменять. MODEL_MODE_NOT_VERIFIABLE.
