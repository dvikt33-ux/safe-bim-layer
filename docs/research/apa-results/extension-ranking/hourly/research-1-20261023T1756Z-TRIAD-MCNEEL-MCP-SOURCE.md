# APA №1 — 30 реальных SOURCE-проверок, research-1-20261023T1756Z-TRIAD-MCNEEL-MCP
Дата: 2026-10-23 17:56 UTC. Только исследование документации и чтение GitHub. **30 различных проверенных технических утверждений, НЕ 30 независимых сайтов, НЕ 30 тестов установленного ПО.** Приоритет: новая официальная Rhino MCP Platform, которой НЕТ среди 61 ID прежней матрицы. Ссылки указывают на первичные документы производителя и каталоги дистрибутивов; статус VENDOR_CLAIM означает неподтверждённое локально утверждение поставщика.

| ID | Проверенное утверждение / ограничение | Первичный документ | Доказательность |
|---|---|---|---|
| S01 | Rhino MCP Platform выпускается McNeel как готовый MCP для Rhino/Grasshopper | [M](https://mcneel.github.io/RhinoAI/) | FIRST_PARTY_SOURCE |
| S02 | Производитель называет Rhino MCP Platform бесплатным инструментом; это не означает бесплатную лицензию Rhino | [M](https://mcneel.github.io/RhinoAI/) | FIRST_PARTY_SOURCE |
| S03 | В репозитории mcneel/RhinoAI обнаружена лицензия MIT; лицензия бинарного Yak-пакета отдельно не заявлена в каталоге | [L](https://github.com/mcneel/RhinoAI/blob/rhino-9.x/LICENSE) | GITHUB_READBACK_PLUS_CAVEAT |
| S04 | Yak Rhino-MCP-Platform 0.3.0 обозначен для Rhino 8 и Windows | [Y](https://rhinopackages.github.io/package/Rhino-MCP-Platform) | YAK_CATALOG |
| S05 | В каталоге для Windows v0.3.0 указан пакет rh8_19-win: нижняя метка совместимости 8.19, не любой Rhino 8 | [Y](https://rhinopackages.github.io/package/Rhino-MCP-Platform) | YAK_CATALOG |
| S06 | Yak v0.3.0 датирован 29.09.2026, пакет около 8.6 MB | [Y](https://rhinopackages.github.io/package/Rhino-MCP-Platform) | YAK_CATALOG |
| S07 | Официальный путь установки Rhino MCP: PackageManager → Rhino-MCP-Platform; установка в данном исследовании НЕ выполнялась | [C](https://mcneel.github.io/RhinoAI/docs/getting-started/codex/) | FIRST_PARTY_SOURCE |
| S08 | Штатная команда MCPConnect выдаёт параметры подключения MCP router | [C](https://mcneel.github.io/RhinoAI/docs/getting-started/codex/) | FIRST_PARTY_SOURCE |
| S09 | В инструкции для MCP router предусмотрен --default-version 8; это выбор версии Rhino, не идентификатор конкретной модели | [C](https://mcneel.github.io/RhinoAI/docs/getting-started/codex/) | FIRST_PARTY_SOURCE |
| S10 | Rhino MCP предоставляет AI доступ к содержимому Rhino и Grasshopper-документов | [M](https://mcneel.github.io/RhinoAI/) | FIRST_PARTY_SOURCE |
| S11 | Официально заявлены создание геометрии Rhino и выполнение команд через MCP | [M](https://mcneel.github.io/RhinoAI/) | FIRST_PARTY_SOURCE |
| S12 | Официальный пример показывает размещение и соединение компонентов GH с решением GH canvas | [G](https://mcneel.github.io/RhinoAI/docs/try-it-out/examples/build-grasshopper/) | FIRST_PARTY_SOURCE |
| S13 | Официальный MCP поддерживает подключение локального LM Studio; не требуется облачный API для самого моста | [Q](https://mcneel.github.io/RhinoAI/docs/getting-started/lm-studio/) | FIRST_PARTY_SOURCE |
| S14 | LM Studio по умолчанию спрашивает разрешение перед MCP tool call, а tool-use нужно явно включить | [Q](https://mcneel.github.io/RhinoAI/docs/getting-started/lm-studio/) | FIRST_PARTY_SOURCE |
| S15 | Инструменты Grasshopper 2 (gh2_) по документации требуют Rhino 9 WIP/BETA; для Rhino 8 опираться на GH1 | [T](https://mcneel.github.io/RhinoAI/docs/troubleshooting/) | FIRST_PARTY_SOURCE |
| S16 | McNeel прямо предупреждает: при нескольких окнах Rhino агент может изменить другое окно | [T](https://mcneel.github.io/RhinoAI/docs/troubleshooting/) | FIRST_PARTY_SOURCE |
| S17 | Политика конфиденциальности McNeel заявляет отсутствие собственной телеметрии и накопления данных connector | [P](https://github.com/mcneel/RhinoAI/blob/rhino-9.x/PRIVACY.md) | GITHUB_READBACK |
| S18 | Результаты MCP tool call могут уходить из локальной машины в выбранный AI-клиент; локальность транспорта не гарантирует локальность модели | [P](https://github.com/mcneel/RhinoAI/blob/rhino-9.x/PRIVACY.md) | GITHUB_READBACK |
| S19 | MCP может выполнять произвольные run_command/run_python/run_csharp и операции open_doc/save_doc; необходим allowlist и запрет записи без допуска | [P](https://github.com/mcneel/RhinoAI/blob/rhino-9.x/PRIVACY.md) | GITHUB_READBACK |
| S20 | В Rhino 8 команда -Grasshopper поддерживает Solver Disable/Enable, что позволяет остановить перерасчёт GH без разработки | [H](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) | FIRST_PARTY_SOURCE |
| S21 | Команда -Grasshopper поддерживает Document Open/Save/Close, но не даёт гарантий транзакционности с Archicad | [H](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) | FIRST_PARTY_SOURCE_PLUS_BOUNDARY |
| S22 | Graphisoft рекомендует Boolean Toggle на Synchronize, чтобы не писать в Archicad до завершения GH-входов | [S](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564) | FIRST_PARTY_HISTORICAL |
| S23 | Graphisoft предупреждает о возможных зависаниях при синхронизации тысяч нативных BIM-элементов | [S](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564) | FIRST_PARTY_HISTORICAL |
| S24 | Elephant для Rhino 8 заявляет отдельный elephant_stable_id и lineage после destructive операций; это не Archicad GUID | [E](https://dfma.tools/products/elephant/) | VENDOR_CLAIM_NOT_LOCAL |
| S25 | Elephant заявляет бесплатный локальный плагин для личного и коммерческого использования без обязательной cloud-подписки | [E](https://dfma.tools/products/elephant/) | VENDOR_CLAIM_NOT_LOCAL |
| S26 | Elephant автоматически пишет JSON sidecar на сохранении .3dm и может делать git add/commit в отслеживаемом репозитории | [E](https://dfma.tools/products/elephant/) | VENDOR_CLAIM_CRITICAL_WRITE_RISK |
| S27 | Elephant Cloud отделён от бесплатного плагина и предполагает платную подписку после beta | [E](https://dfma.tools/products/elephant/) | VENDOR_CLAIM |
| S28 | ggRhinoIFC v26.10.19.8 доступен для Rhino 8; IFC-обмен не является native GUID-preserving 3-way live sync | [IY](https://rhinopackages.github.io/package/ggRhinoIFC) | YAK_CATALOG_PLUS_BOUNDARY |
| S29 | Geometry Gym документирует IFC2x3/IFC4, опции экспорта и ошибки геометрии при импорте в принимающее приложение | [I](https://technical.geometrygym.com/rhino-grasshopper/ifc/ifc-for-rhino/ifc-export) | VENDOR_SOURCE |
| S30 | Geometry Gym указывает trial 30 дней и бесплатную академическую лицензию; без такой лицензии это не постоянное бесплатное решение | [IL](https://technical.geometrygym.com/getting-started/licencing) | VENDOR_LICENSE |

## Контекст из APA
- [BUILD-01 issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192): один writer DynamicCommands→BIM Graph→SceneWriter/SQLite; новый проект G0 BLOCKED, G1/G2 не выполнены, G3 не разрешён.
- [PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74): исторический ограниченный 21-элементный нативный прототип с Save/Open, не новый BUILD-01.
- [Исследователь №2 17Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T17Z-triad-report.md): существующий GH→jSwan→typed JSON→PR74, а не второй GH writer; SetStories есть в схеме, но NOT_WIRED; Slab polygon holes уже SOURCE-wired.
- [Матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json): прочитана, JSON count=61, items.length=61; есть GRASSHOPPER, но НЕТ Rhino-MCP-Platform / Elephant / ggRhinoIFC. Матрица не редактировалась.
- [Последний подтверждённый №3](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07.md): 20.10 07Z; более свежий №3 в этом проходе не доказан.

## Границы
S01–S23 относятся к первичным материалам McNeel/Graphisoft; S04–S06, S28 к данным Yak-каталога, S24–S27 к заявлению Elephant, S29–S30 к документации Geometry Gym. Точные MCP tool schemas установленной версии 0.3.0, локальный Rhino 8 build, GH add-on, выбранное Rhino окно, подключение к AC29 и native GUID не проверены. Отсутствие подтверждения не равно отсутствию функции. Ни одна программа не установлена, LIVE не выполнялся.

SOURCE=30; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. FULL_THREE_WAY_SYNC=NOT_FOUND_IN_CHECKED_SOURCES. MODEL_MODE_NOT_VERIFIABLE.
