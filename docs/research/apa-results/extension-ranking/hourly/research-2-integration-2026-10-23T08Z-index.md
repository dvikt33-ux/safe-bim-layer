# APA №2 | BUILD-01 | 2026-10-23 08Z | VERIFIED SOURCE INDEX

**Конкретный новый вклад:** conditional BeamSegment GUID gap в финальном whole-inventory PR162: Beam adapter умеет `assembly_subelements('Beam')`, но `run_project` учитывает только Column children. Если установленный `GetAllElements` возвращает BeamSegment, native CREATE может завершиться `FINAL_INVENTORY_DIFF_MISMATCH`. Пока SOURCE-risk, не LIVE failure. Минимальный путь — existing `assembly_subelements` + negative OFFLINE/read-only installed checks.

**Второе подтверждение:** upstream Tapir main `1.7.3` содержит прямые поля `CreateSlabs.structureType/buildingMaterialId`, сохранённый каталог `1.5.10` их не содержит. Provider drift ≠ installed contract. Не обновлять APX и не переносить схему.

**SOURCE 30 отдельных прямых проверок**, 10 маршрутов, 2 независимых статических контрааудита. **OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0.** G0 BLOCKED, G1/G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. Исторический 06Z **PARTIAL_NOT_ACCEPTED**. MODEL_MODE_NOT_VERIFIABLE.

## Приложения: опубликованы до индекса, каждое повторно прочитано и точно совпало
- [Полный инженерный отчёт](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-report.md) — Git blob `4156c7bdf90b5ce5e0ecaf92946be53e25bb9fae`
- [SOURCE 01–15 (Issue + 14 PR)](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-checks-A.md) — Git blob `9e594bb0aa2a097769cc7780d6a392d634dc3b7c`
- [SOURCE 16–30 (15 файлов)](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-checks-B.md) — Git blob `3df0d24d4bb1a297644bb3b822cd83f202d7ab0d`
- [10 готовых маршрутов](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-matrix.md) — Git blob `a970bb6c301d7101b48e0e1133489edd86e0d3d7`
- [Контрааудит A: Tapir 1.5.10 против upstream 1.7.3](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-audit-A.md) — Git blob `d2562f23f7cdf80cbdb6e88aa1cb5c684f076237`
- [Контрааудит B: BeamSegment и BREP](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-audit-B.md) — Git blob `2fe3a9caf1f79e3a7314a41248488133cf13fe70`
- [Архив 06Z — частично, оригинал отсутствует](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-06Z-status.md) — Git blob `cd04f46223c330037cbaae934c67e7cb7f05f935`
- [SHA256 + Git blob SHA-1](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-sha-manifest.json) — Git blob `a3efb3b42fbc4ed3a766c60dae3e5b3b3878febd`

Manifest содержит независимый SHA256 UTF-8 содержимого каждого из 7 приложений, а также Git blob SHA-1. Manifest SHA256: `7c74ec7968b940b12bbdb331abebc9fb893f9c85a92f3c5595b7607ea71a20b7`. Все 8 приложений fetched exact перед созданием индекса. Никаких изменений `main`, NEXT, PLN/APX, кода, нативного LIVE, PR merge. Архив SOURCE не означает приёмку BUILD-01.
