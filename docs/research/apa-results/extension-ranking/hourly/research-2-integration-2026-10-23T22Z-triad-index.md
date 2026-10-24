# APA №2 — 2026-10-23 22Z / TRIAD / BUILD-01

**Новые P0:** (1) Graphisoft AC29 GH Object Settings удаляет созданную Embedded Library Part при удалении компонента/смене режима; размещённые экземпляры становятся Missing Objects. (2) AC29 Publisher при пользовательском режиме Auto Hotlink Update может обновить внешние источники; этот режим хранится в Preferences, не в PLN. (3) AC→GH Parameter Component обновление **может быть автоматическим** при Sync Changes to GH; это не full 3-way. Источники: https://help.graphisoft.com/AC/29/INT/GC.pdf, https://help.graphisoft.com/AC/29/INT/_AC29_Help/140_UserInterfaceDialogBoxes/140_UserInterfaceDialogBoxes-15.htm, https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm.

**Материалы:**
- [report.md](./research-2-integration-2026-10-23T22Z-triad-report.md) — Git blob `1281808f42b882f44fbdef7aca7eab8ebfb1792c`, commit `c35e793d7e8d5fc8bb25e1d0ad47ccaef887eff8`.
- [matrix.md](./research-2-integration-2026-10-23T22Z-triad-matrix.md) — Git blob `b8172a5db82b5aa05133dd2dfe4251d89695d2b9`, commit `d9337a03cdb4127818897e74299029cddb687f0c`.
- [checks.md](./research-2-integration-2026-10-23T22Z-triad-checks.md) — Git blob `a09b41e2e1227f42810a19da5d5a7d4414e6f969`, commit `2d6a1dde5d069ccba479f84c77b9a3775b0d4335`.
- [audits.md](./research-2-integration-2026-10-23T22Z-triad-audits.md) — Git blob `0a307d3c796438aaaba91d3e8b9c7e9c3eed070b`, commit `24d824895700f984919cac1c676c008816442ba0`.
- [manifest.json](./research-2-integration-2026-10-23T22Z-triad-sha-manifest.json) — Git blob `58f110784489361a110974878c5205e6e2586de5`, commit `ee50f06e2092cd6d53a3d3af32b46ca838c94e2f`.

**Readback:** 5/5 файлов опубликованы и проверены точным сравнением; индекс проверяется отдельно после создания. SOURCE=30 отдельных документарных assertions, контрааудитов=2; OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. Полная автоматическая трёхсторонняя GUID-preserving синхронизация NOT_FOUND. Нет изменений main/NEXT/код/PLN/APX и нет установок/нативных операций/merge. MODEL_MODE_NOT_VERIFIABLE.
