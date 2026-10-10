# APA — восстановление ранее заблокированных исследований (10.10.2026)

**ПЛАН:** APA-P00 — Сохранность исследований. **ДЕЙСТВИЕ:** APA-P00.A03 — Публикация. **ПОДШАГ:** предотвратить повторение `GITHUB_PUBLISH_BLOCKED`.

## Восстановленные материалы

| Исходная тема | Отчёт в GitHub | Commit, полученный при сохранении | Проверка |
|---|---|---|---|
| Composite / Building Material | [REC-COMP](runs/2026-10-10/apa-recovered-20261010-composites-building-materials.md) | [1e13ad2](https://github.com/dvikt33-ux/safe-bim-layer/commit/1e13ad2ec85bf555a9a64177f3627f4ce8449dd4) | API readback, exact content |
| MEP ports / graph completeness | [REC-MEP](runs/2026-10-10/apa-recovered-20261010-mep-ports-network-integrity.md) | [d941ac1](https://github.com/dvikt33-ux/safe-bim-layer/commit/d941ac13a0ec22d9633f98c9fc16c8c4a5335139) | API readback, exact content |
| Tapir 1.7 Slab bbox / top story height | [REC-TAPIR](runs/2026-10-10/apa-recovered-20261010-tapir17-slab-bbox-upper-story.md) | [d205729](https://github.com/dvikt33-ux/safe-bim-layer/commit/d20572981c535efa90dd7096eed71f03ee77ce6f) | API readback, exact content |

Все три текста помечены `RECOVERED_FROM_CHAT`. Указанные внутри тесты и API-выводы — **REPORTED из предыдущих ответов**, а не новые проверенные LIVE/OFFLINE результаты. Файлы можно независимо аудировать.

## Установленная проблема

В момент восстановления GitHub contents create_file один раз ответил HTTP **409 Conflict**:
`is at 5e03f469... but expected 3b5197ad...`. Это **гонка параллельных коммитов в одну branch**, а не доказательство отсутствия права push. Последующие повторные create_file после проверки актуального состояния ветки прошли успешно.

Предыдущие сбои запланированных задач также сообщали `safety checks blocked`; **не установлено**, что все они объясняются исключительно 409. Отдельный push-triggered publisher уже развернут: [workflow](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/.github/workflows/apa-research-publisher.yml), [реальный синтетический E2E](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668). Публикация через него требует подтверждённой записи inbox request, что тоже зависит от GitHub write доступа.

## Политика, уменьшающая потери

1. **Publication-first:** до серьёзного исследования проверять действительную способность сохранения на GitHub (read+write), а не только `permissions.push=true`.
2. Для конкурентных коммитов `409`: обновить состояние ветки и повторить create_file **не более нескольких раз**, всегда с тем же уникальным путём; затем fetch проверить отсутствие/наличие файла, исключить дубли.
3. При `403/blocked` или устойчивом конфликте: не делать вид, что доступ есть; не запускать длинное новое исследование при невозможности публикации. Если исследование уже завершено, сохранить полное содержание в доступный альтернативный канал (GitHub issue comment или Slack, если write там реально работает) с пометкой PENDING_GITHUB_FILE; затем восполнить из этого durable source в canonical hub.
4. После записи всегда GitHub readback точного содержимого; после него — индекс и `APA_EVENT_V1` с прямой ссылкой.
5. Продолжать различать `SOURCE_VERIFIED`, `SYNTHETIC`, `BUILD`, `LIVE` и `REPORTED`. Публикация не заменяет технического аудита.
6. Отдельно проверять полноценную публикацию **из scheduled task**, а не переносить успешный обычный чат на его права. Гейт scheduled runner остаётся `NOT_VERIFIED`.

Исследовательская ветка: `research/apa-verified-results-hub-20261010`; `main`, PLN, APX, локальное ПО не менялись.
