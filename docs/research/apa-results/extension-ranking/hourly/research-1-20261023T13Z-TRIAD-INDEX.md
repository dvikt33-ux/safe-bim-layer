# APA №1 | 23 октября 2026, 13Z | BUILD-01 / Archicad29 + Rhino8 + Grasshopper

## Воздействие на BUILD-01 — новое
**Найден критический предел штатной обратной синхронизации:** официальный AC29 Grasshopper–Archicad guide разрешает `Deconstruct Roof` только для Single-Plane Roof; Multi-Plane Roof обратно не деконструируется. Для изменения вручную созданного AC элемента в GH требуется явная команда **Send Changes** — автоматическая симметричная трёхсторонняя синхронизация не доказана. **Hosted Window/Door:** GH требует существующий Wall-type input; размещение задаётся Horizontal Distance или Door/Window Point. Доступ к внутренним параметрам GDL детали требует изменения её кода, что противоречит no-code политике.

**Новый проверенный альтернативный инструмент с ограничением:** Speckle Next-Gen официально поддерживает Archicad 29, Rhino и Grasshopper, но публикует AC→Rhino/GH mesh/materials/properties и **не поддерживает native element loading** в Archicad в текущем Next-Gen. Поэтому Speckle — только SOURCE-кандидат независимого QA, НЕ исполнитель native BUILD-01. Teamwork статья Graphisoft (2017/2021) дополнительно выявляет риск duplicate/reservation и потерю SEO при GUID recreation; AC29 воспроизводимость не доказана.

**Новые готовые вспомогательные маршруты:** Tapir Grasshopper Plugin (upstream MIT, work-in-progress, installed unknown); Rhino 8 `-Grasshopper Solver Disable/Enable` и `GrasshopperPlayer` для .gh/.ghx, но автоматическое подключение GH-AC из Player НЕ доказано.

**Ворота:** G0 runtime/APX/schema **BLOCKED**; G1 **NOT_RUN**; G2 **SOURCE_ONLY**; G3 **NOT_AUTHORIZED**; G4 **NOT_RUN**; G5 **NOT_RUN**. Новых PASS нет; здание не создавалось. Issue: https://github.com/dvikt33-ux/safe-bim-layer/issues/192

## Подтверждённые опубликованные приложения
- [SOURCE-A: S01–S15](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T13Z-TRIAD-SOURCE-A.md), Git blob SHA `d1bd3488db7a65c99572c5dde0b56a068d909f39`, exact fetch/readback PASS.
- [SOURCE-B: S16–S30](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T13Z-TRIAD-SOURCE-B.md), Git blob SHA `d38b08ca7fafbcae1f0439431b22d0cf8f2ec0d4`, exact fetch/readback PASS.
- [7 карточек решений](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T13Z-TRIAD-CARDS.md), Git blob SHA `3d1037002157598c6a1ff4b178956cbc607f2869`, exact fetch/readback PASS.
- [2 независимых контрааудита](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T13Z-TRIAD-AUDITS.md), Git blob SHA `37ca24ca65b0bcba7c0781abebe33af94a9ac0ea`, exact fetch/readback PASS.

## SOURCE-методика и фактический объём
30 различных предметных SOURCE-проверок, не 30 независимых сайтов. 7 карточек и 2 контрааудита. Официальные первоисточники Graphisoft AC29 GH guide, McNeel Rhino8, Speckle vendor и Tapir upstream; исторические Graphisoft Teamwork notes маркированы HISTORICAL_SOURCE. Полный PDF Graphisoft (22.8 MB) не удалось прочитать постранично: web.open ограничен размером, контейнерный curl DNS не разрешил; использованы доступные индексированные официальные фрагменты. Это ограничение нельзя подменять постраничным аудитом.

## Адресное поручение №2
1. Read-only runtime G0: actual AC29 build/port/PLN, loaded APX SHA, Tapir 1.5.10 schema, наличие/версия Graphisoft GH Live Connection и Tapir GH plugin; никаких установок.
2. Матрица ownership per GUID/attribute: **GH-owned** native elements и **APA SceneWriter-owned** native elements не должны пересекаться по write; manual Send Changes и Sync toggle — разные checkpoint.
3. Двухэтажный BUILD-01: Wall→Door/Window DAG, exact GDL identity + Favorite readback, Single-Plane/Multi-Plane Roof раздельно, атрибуты/этажи/материалы.
4. Teamwork/SEO риск: для первого испытания solo scratch; read-only provenance/duplicate/SEO graph; не повторять CREATE после UNKNOWN.
5. Speckle v3 не включать в обязательный native writer, возможный внешний QA — только после отдельного разрешения на установку и передачу модели.
6. Rhino Solver/GrasshopperPlayer считать SOURCE-кандидатами; совместимость Player→GH-AC/port/Sync отдельно не доказана.
7. Критерий завершения: реально созданная, сохранённая, закрытая и повторно открытая **новая** native BIM-модель со всеми GUID/host/material/geometry receipts, только после отдельного допуска. Не путать SOURCE с INSTALLED/LIVE/ACCEPTED.

## Прочитанный контекст / ограничения
Прочитаны `NEXT_RESEARCH_PRIORITIES.md` (blob `6f074693360231c5cb42ada815984a6b0dd504c0`), `TRIAD-PIVOT` (blob `896fa3af0953468ca58fca710f32cb926504f582`), №1 12Z, №2 11Z, issue #192, исторический `PROJECT_PLAN.json` rev182 commit `049576378c961c5d7a9a62611f4091e3da70d309` blob `c2ab2f9d606db1412c4031076103c267fc463f83` (read-only). №2 12Z/13Z и №3 12Z/13Z по предполагаемым путям не найдены; матрица 61 напрямую не прочитана, точный путь не установлен. Нельзя заявлять полный cross-report/matrix audit.

Не менялись main, код, PLN/APX, установки, LIVE, платные API, Work/Codex/Arena или PR merge. Важность 0–100 — экспертная, не benchmark. MODEL_MODE_NOT_VERIFIABLE.
