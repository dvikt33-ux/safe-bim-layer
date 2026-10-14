# APA — исследование по скриншоту: Spare Parts 3D, Hermes Agent и CAD MCP

> **Update after independent source review (2026-10-14):** Оценка Boti-Ormandi archicad-mcp понижена с VERY_PROMISING до **PROMISING** для APA: см. [source audit](ARCHICAD_MCP_SOURCE_AUDIT_20261014.md). Этот документ — первичный screening, а не итоговое решение; authoritative rank — `candidates.json`.

**Дата:** 2026-10-14. **Тип:** SOURCE_RESEARCH / proposed candidates. **Статус:** NOT_INSTALLED / NOT_TESTED_WITH_APA. **Источник идеи:** пользовательский скриншот YouTube с надписью SpareParts3D и комментарием «подключил hermes к solidworks через mcp сервер». Заявления автора комментария (6% недельного лимита Claude, «30% быстрее») — **НЕ проверенные независимые измерения, непригодны как benchmark**.

## 1. Разделить четыре несвязанные вещи

| Продукт | Что делает | Бесплатность | APA-решение |
|---|---|---|---|
| [Spare Parts 3D / THEIA](https://spare-parts-3d.com/) | Восстанавливает механические 3D CAD детали из PDF/DXF/скан-чертежа с инженерной валидацией, выдаёт STEP | [Официальный FAQ](https://spare-parts-3d.com/faq/): **pay per use**, платно за каждый чертёж; DigiPART service/subscription | **DO_NOT_CONSIDER** для бесплатной прямой интеграции в APA. Примечание: интересная идея, но обратный импорт PDF→BIM отдельно отложен в конец roadmap. |
| [Hermes Agent (Nous Research)](https://github.com/NousResearch/hermes-agent) | Открытый AI-агент, управляет инструментами по MCP, может использовать локальный OpenAI-compatible LLM | MIT; программный агент без лицензии на разработку/установку; облачные модели/портал по отдельным тарифам | **PROMISING** как альтернативный локальный MCP-клиент / ревизор, не заменять основной контроллер APA. Идентичность упомянутого в комментарии «Hermes» **не подтверждена автором**. |
| [SolidWorks MCP — hjbaard](https://github.com/hjbaard/SolidWorks-MCP) и [HarrierPigeon](https://github.com/HarrierPigeon/Solidworks-MCP-Server) | Реальное параметрическое моделирование, замеры модели, constraint/dimension checks, файлы SolidWorks, чертежи/виды | MCP-код открыт, но требует установленный SOLIDWORKS на Windows (**не бесплатен**) | **LOW_PRIORITY** как **образец реализации проверяемого CAD Tool API**, **NOT_ELIGIBLE** как прямое бесплатное расширение Archicad. |
| [Boti-Ormandi/archicad-mcp](https://github.com/Boti-Ormandi/archicad-mcp) | MCP через штатный Archicad JSON API и Tapir, discovery instances, search точных command schema, поиск свойств, workflows | MIT, Python 3.11+, uv; `uvx archicad-mcp`; доступ к AC/Tapir зависит от установки | **VERY_PROMISING for AUDIT** как источник готового command-schema lookup и адаптер API, но **NOT_APPROVED for runtime** из-за `execute_script`, выполняющего несанкционированно Python-код от имени ОС. |

## 2. Риск у archicad-mcp / почему не включать «одним кликом»

В README Boti-Ormandi сказано буквально, что `execute_script` исполняет Python от имени текущего пользователя **без sandbox**. Это опаснее, чем узкоспециализированные операции read-only JSON API; стороннему агенту нельзя давать такой инструмент в production. Возможен обход нашего SceneWriter, порча PLN и утечка файлов.

**Предлагаемый аудит без запуска**: изучить только `get_docs`, `get_properties`, `doctor --json`, источники упакованных схем Archicad/Tapir и методы их обновления; сверить с нашей **локальной Tapir 1.5.10** и SDK Archicad 29. Не считать README свидетельством совместимости с конкретной сборкой 29.3001. У `execute_script` нет подтверждённого read-only enforcement. Если потребуется интеграция, не использовать произвольный скриптовый инструмент: только отдельный allowlist-адаптер с проверкой API команд, идентичности PLN, корневого каталога и readback.

Другие проекты из предыдущего обзора:
- [alesdev88/Archicad-MCP](https://github.com/alesdev88/Archicad-MCP) — 1-file .mcpb, но автор предупреждает о возможном crash на `GetPropertyValuesOfElements`.
- [lgradisar/archicad-mcp](https://github.com/lgradisar/archicad-mcp) — Tapir-native MCP, значительный overlap с нашим bridge; без отдельного аудита не включать запись.

## 3. Что заимствовать из SolidWorks MCP (без SOLIDWORKS)

1. **Нативная параметрическая геометрия, а не картинки:** GPT/локальная модель генерирует только высокоуровневое намерение; APA компилирует в проверенные C++/Tapir вызовы.
2. **Exact contracts:** поддерживаемая версия API, сигнатура команды, типы параметров, версия Add-On и чёткая ошибка при неподдерживаемом поле.
3. **Native readback on every write:** уникальный GUID, свойства, этаж, численные bounds/геометрия, связи элементов, сравнение requested-vs-actual; после сохранения и повторного открытия PLN.
4. **Constraint relations:** планы, фасады, разрезы, 3D выходят из *одного* источника геометрии; не генерировать проекции независимо.
5. **Evidence per step:** каждое изменение содержит source-model identity, command, JSON/schema version, preview, readback, expected-vs-measured diff и сохранённые артефакты; любое неуспешное наблюдение даёт `NOT_VERIFIED`.
6. **Safety:** одно активное записывающее подключение, запрет произвольных инструментов ОС, блокировка новых внешних AI-серверов на продуктивный PLN, отмена/откат только с гарантированным snapshot.

**Не заявлять новые возможности уже реализованными**: наша существующая APA SceneWriter / Tapir / native bridge уже реализует часть этих принципов; исследование должно проверять **разницу** и подтверждать новые пробелы, а не дублировать стек.

## 4. Минимальные проверки перед допуском

1. Источники pinned на commit SHA, license/security audit (включая цепочку зависимостей, permissions и network).
2. Проверка docs-only `uvx archicad-mcp` в изолированном окружении **без работающего Archicad**, считать названия и точные типы команд; никогда не предоставлять `execute_script` неконтролируемому агенту.
3. Сверка schemas с документами **Archicad 29.3001 + Tapir 1.5.10**, матрица missing/extra/incompatible.
4. Отдельный безопасный тест read-only на копии PLN — только после независимого подтверждения запрета записи, GUID, нормальные таймауты.
5. Сравнить with existing APA (покрытие методов, эффективность, расход токенов, количество необоснованных утверждений, стабильность). Только подтверждённый gain идёт в controller `TASK_PROPOSAL_V1`; без автоматической записи в `PROJECT_PLAN.json`.

## 5. Вывод

**Первый на исследование: Archicad MCP (Boti-Ormandi)** — готовый поиск точных команд API; полезная потенциальная экономия на модуле схем. **Hermes Agent** — перспективный альтернативный MCP-хост локальной модели; не гарантирует качества ответов и не должен становиться ещё одним writer. **SolidWorks MCP** — пример архитектуры проверяемого CAD, не готовый плагин в Archicad. **Spare Parts 3D** — вне критерия бесплатного внедрения и вне архитектурной геометрии.

Идентичность сервиса из комментария и результаты работы пользователя YouTube **не подтверждены**. Ни одна интеграция, испытание или установка не выполнены.

### Первичные источники

- https://spare-parts-3d.com/faq/ (модель оплаты, форматы, тип деталей)
- https://github.com/NousResearch/hermes-agent (MIT, локальные модели, Windows)
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md (MCP)
- https://github.com/Boti-Ormandi/archicad-mcp (доступные инструменты, risk statement)
- https://github.com/hjbaard/SolidWorks-MCP (проверка геометрии)
- https://github.com/HarrierPigeon/Solidworks-MCP-Server (эскизы, дерево построений, экспорт)
