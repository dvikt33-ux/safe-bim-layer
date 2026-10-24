# APA №2 — TRIAD BUILD-01 / 2026-10-23 19Z — индекс

**G2 P0:** pinned Tapir 1.5.10 `CreateSlabs` не содержит трёх structure/material полей; upstream 1.7.1+ их добавил, но не установлен. **G3 P0:** Tapir GH `EmbedMetadata/ReplaceExisting` создаёт риск скрытых записей/удаления host walls и новых GUID. **G4 P0:** Tapir 1.7.2 `Get3DGeometryOfElements` даёт Mesh, а не независимый BREP. Ни один результат не выдаётся за LIVE.

## Архив (публикация create→fetch→SHA256, все файлы readback)

- [Полный инженерный отчёт](research-2-integration-2026-10-23T19Z-triad-report.md) — blob `09d971e85d10ce1dd89dbf9a7d65366e39a0b55e`.
- [Матрица 10 сценариев](research-2-integration-2026-10-23T19Z-triad-matrix.md) — blob `3cc52b4de9d8686e93dc329e6586900bade86d10`.
- [30 предметных SOURCE-проверок](research-2-integration-2026-10-23T19Z-triad-checks.md) — blob `1f20a38c18b2fe109f98c647a722c7ecfeb83bfc`.
- [Два самостоятельных контрааудита](research-2-integration-2026-10-23T19Z-triad-audits.md) — blob `4120dd0e7e9f5dfaef2638b1ae467204c163192f`.
- [SHA256/Git SHA/commit манифест](research-2-integration-2026-10-23T19Z-triad-sha-manifest.json) — blob `59dade194db39770e9dd1588a30bb524f8c00169`, commit `742d97a4bd721d65897797c416ba39063f8942ce`.

**Проверка:** 5/5 приложений повторно прочитаны; полное содержимое, SHA256 UTF-8 и Git blob SHA совпали. Индекс создан только после readback. Исторический 06Z — PARTIAL_NOT_ACCEPTED.

**G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. SOURCE=30; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0.** FULL_THREE_WAY_SYNC=NOT_FOUND. Нет нового здания, установки, WRITE, изменений main/NEXT/кода/PLN/APX или merge. MODEL_MODE_NOT_VERIFIABLE.
