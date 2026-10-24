# APA №2 | 2026-10-24 10Z | Индекс, публикационная квитанция

**BUILD-01 [#192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192)** — SOURCE_ONLY. Главная новая проверка: существующий `archicad_connected_components.py` требует точного полного inventory GUID и неизменной retained geometry. GH Live Connection, создавший новый native GUID в том же PLN после исходного receipt, нарушает эти инварианты. Даже два разных владельца элементов в одном PLN не означают допустимость двух независимых writers. Без нового синхронизатора для BUILD-01 разрешён только один native executor: существующий SceneWriter; Graphisoft Deconstruct/Send Changes использовать как read-only AC→GH.

**Статусы:** SOURCE 27 проверенных отдельных утверждений, два внутренних контрааудита, 10 маршрутов; OFFLINE 0 новых, BUILD 0, INSTALLED NOT_VERIFIED, LIVE 0 новых, ACCEPTED 0. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN; full native three-way sync NOT_FOUND. MODEL_MODE_NOT_VERIFIABLE.

## Опубликованные документы

| Артефакт | Git blob SHA-1 (самостоятельный расчёт и GitHub fetch) | Commit SHA |
|---|---|---|
| [Полный инженерный отчёт](research-2-integration-2026-10-24T10Z-report.md) | `5ea50bda28c9c01d08363038c2d720a1eed91ba7` | `7c573d2a6aba349c2792dbbbca3ac5d5efe95462` |
| [27 SOURCE-сверок](research-2-integration-2026-10-24T10Z-checks.md) | `6ed7ad6d2f6f53cc5b3708904c92431369ebb22e` | `75ff1bc43a5eb1777b47863e0506e5b8651a96c4` |
| [Два контрааудита](research-2-integration-2026-10-24T10Z-audits.md) | `aa22fa0caa8326c9fc2042298696d5dcea2b1d40` | `bd79da1fdfebff453a3b7293541aa55e1aac236b` |

**Метод записи:** каждый файл создан `create_file` с явным `branch=research/apa-extension-ranking-hub-20261018`, затем `fetch_file` с тем же ref, полное точное сравнение UTF-8 содержимого, независимый Git blob SHA-1 от `blob <byte_length>\\0<bytes>` и сравнение с SHA GitHub. Все три файла VERIFIED. Этот индекс подлежит той же проверке; SHA/commit самого индекса возвращаются отдельно после его публикации.

**Исходные документы прочитаны:** [NEXT_RESEARCH_PRIORITIES](../NEXT_RESEARCH_PRIORITIES.md), [TRIAD-PIVOT](research-1-20261023T11Z-TRIAD-PIVOT.md), [№1 09:55Z](research-1-20261024T0955Z-TRIAD-GH-MCP-IDLE-ROUTING-GATES.md), [№2 09Z](research-2-integration-2026-10-24T09Z-report.md), [матрица 61](../priority_matrix_20261018.json), [последний найденный №3 20.10 18Z-A](audit-2026-10-20-18-A.md), [исторический PROJECT_PLAN rev182](../../control/PROJECT_PLAN.json) только чтение. Исходный код PR74/connected CLI читался по immutable ref `5a3a9201a715a5528c93bed4a5318e2acb32eea7`.

**Следующий P0:** G0 read-only с фактическими AC29 port/PLN/APX/schema, Rhino8 SR/.3dm и GH .gh/add-on; G1 штатный offline authored compiler. Не запускать GH Design writer в BUILD-01. Встроенный `connected CLI` Beam требует accepted source receipt и закреплённый порт 19724. No main/code/PLN/APX/install/LIVE/merge/paid API changes.
