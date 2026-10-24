# APA №2 — 2026-10-23 23Z / TRIAD BUILD-01 — индекс
**Новый P0:** для воспроизводимого GH→JSON нужен исходный .3dm вместе с .gh, если в GH есть referenced Rhino geometry (официальный McNeel). Pinned Tapir 1.5.10 имеет готовые GetZoneBoundaries/GetRelations/GetConnected, но PR74 EvidenceAPI.READs их не содержит. Zone boundary.area — площадь 3D границы, не площадь комнаты. GetModelDumpV1 отсутствует в pinned Tapir и требует отдельной проверки runtime-провайдера.

**Файлы и подтверждённые Git blob SHA-1:**
- [Полный инженерный отчёт](./research-2-integration-2026-10-23T23Z-triad-report.md): blob 2b4e910ca11bce7f43d7a0dd6aab9cc9284dbd98; commit 9799f0dc53be5586ac9f80c0a2252cfb3f2b272e.
- [30 SOURCE-проверок](./research-2-integration-2026-10-23T23Z-triad-checks.md): blob 006ca8e8bc075188ca07359688933e346b504800; commit 3ea1595efd6131f733c06fa740431b1bdd5856dc.
- [Два контрааудита](./research-2-integration-2026-10-23T23Z-triad-audits.md): blob 843f73e66f0330569a370dcadb4bcdd6856563c4; commit 2443ea663e044271879c0eff325d1abccb6ff7e9.
- [Матрица девяти сценариев](./research-2-integration-2026-10-23T23Z-triad-matrix.md): blob 0c2b53a509abf49e0eed2756c5542ae62dacffd6; commit 0e93adaeea1523103aff681e7bf503ccdd6f56bc.
- [SHA-манифест](./research-2-integration-2026-10-23T23Z-triad-sha-manifest.json): blob 8a9ccde97f0547d1b39480ada4510be4fab88acf; commit 28f0e0fa72a13be2387564f3e10f91d30a1536f1.

**Публикация:** пять файлов выше созданы через create_file с явным branch, прочитаны fetch_file и точно сопоставлены с исходным текстом. Индекс также проходит отдельный fetch_file и exact compare. SHA256 для исследовательских файлов не вычислялся; указаны Git blob SHA-1 и commit SHA.

**BUILD-01:** SOURCE=30 предметных проверок, контрааудитов=2; OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. Full GUID-preserving Rhino↔GH↔AC sync NOT_FOUND. Не изменялись main, NEXT, исходный код, PLN/APX, historical PROJECT_PLAN rev182. Не выполнялись установки, LIVE, merge, платные API или Work/Codex/Arena. MODEL_MODE_NOT_VERIFIABLE.
