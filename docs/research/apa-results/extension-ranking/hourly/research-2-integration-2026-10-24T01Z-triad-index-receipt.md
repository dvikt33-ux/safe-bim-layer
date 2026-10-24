# APA №2 / 2026-10-24 01Z — индекс и квитанция публикации
**P0:** найден `SOURCE_STATIC_CONTRACT_MISMATCH` между legacy `building-shell-v1` и authored PR74 по абсолютной отметке перекрытий. Реального BUILD-01 нет. **MODEL_MODE_NOT_VERIFIABLE.**

## Пакет
| Документ | Git blob SHA-1 | Commit SHA | Проверка |
|---|---|---|---|
| [Полный отчёт](research-2-integration-2026-10-24T01Z-triad-report.md) | `2da1e6478308a05e0f17e0ac390c2c2715a16767` | `3955ccef3683231021ed21e837e08fde81e889c0` | `create_file(branch explicit) → fetch_file(ref=branch) → exact UTF-8 text equality TRUE` |
| [30 SOURCE-проверок](research-2-integration-2026-10-24T01Z-triad-checks.md) | `0821230f61ba7690fd5edd10b2f2a58dd1064fff` | `7029d365b3f264687097cbf365e53bfc525a4318` | `create_file(branch explicit) → fetch_file(ref=branch) → exact UTF-8 text equality TRUE` |
| [Два контрааудита](research-2-integration-2026-10-24T01Z-triad-audits.md) | `e0a4fa0b1f666dfbc00379da4ee402ac0d03e8b5` | `764de154d26ceec69fdd69e77286c17a3576cccb` | `create_file(branch explicit) → fetch_file(ref=branch) → exact UTF-8 text equality TRUE` |

**Ветка:** `research/apa-extension-ranking-hub-20261018`; наличие ветки проверено перед записью. Все 3 файла созданы с явно заданным `branch`, без изменений `main`. Повторное чтение подтвердило точное совпадение Unicode-текста. Git blob SHA-1 предоставлены GitHub Contents API. SHA256 исследовательских файлов отдельно не вычислялся. Этот индекс является четвёртым файлом и проверяется после публикации; собственный SHA намеренно не включён в содержимое.

**Источник:** issue #192, immutable PR74 `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, pinned Tapir schema blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`, Tapir C++ 1.5.9, Graphisoft и McNeel.

**Новые статусы:** SOURCE=30 утверждений; OFFLINE=0; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0; ACCEPTED=0. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. FULL_THREE_WAY_NATIVE_SYNC=NOT_FOUND.

**Следующее P0:** только authored preflight на разрешённой новой scratch PLN после реального read-only G0; legacy building-shell-v1 для BUILD-01 не выбирать до устранения Z-контракта. Ни новый writer, ни router, ни синхронизатор не создавались. Исходный код, PLN/APX, main и исторический PROJECT_PLAN rev182 не изменялись.
