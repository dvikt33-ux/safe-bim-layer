# APA — почему повторно исследовали и написали то, что уже нашли: root-cause review

Дата: 2026-10-16. Статус: **POSTMORTEM / SOURCES_MIXED / CODE_DEDUP_NOT_AUDITED**. Это документирование причин, **не** исправление архитектуры или новый функционал. Источник исторических разговоров — поиск предыдущих бесед пользователя; первичные отчёты и указанные SHA/PR требуют дополнительной проверки при точном code-diff.

## Наблюдаемый симптом и повторная ошибка

Пользователь справедливо указал, что глубокие исследования Tapir/MCP проводились неоднократно. В текущей беседе сторонний Tapir MCP был представлен как новое решение; затем пользователь через PowerShell установил `tapir-archicad-mcp 0.6.4`, включил `TapirAddOn_AC30_Win.apx 1.7.0`, и показал реальный MCP `app_get_add_on_version` PASS на Archicad 29 (Tapir 1.5.10/port 19726) и Archicad 30 (Tapir 1.7.0/port 19725). Подробные USER_REPORTED логи: [archicad29-30-tapir-mcp-install-user-log-20261016.md](archicad29-30-tapir-mcp-install-user-log-20261016.md).

**Критический дополнительный факт:** во время инсталляции `uv tool list` **уже содержал** пакет `archicad-mcp-server v0.6.0` с исполняемыми `archicad-mcp` и `archicad-gdl` **до** добавления нового пакета. В предыдущем ответе это не было трактовано как обязательный повод сначала сравнить уже установленное с предлагаемым. Нельзя утверждать, что этот старый MCP тогда был зарегистрирован в текущем клиенте или работал постоянно, но он определённо присутствовал как установленный пакет.

## Восстановленная хронология (PRIOR_CONVERSATION_RETRIEVED; конкретные GitHub code-diff не подтверждены)

| Дата | Уже известный факт / решение | Упущенное следствие |
|---|---|---|
| 2026-09-10 | В обсуждении сравнивали Archicad MCP, предпочтён `alesdev88/Archicad-MCP`, `SzamosiMate` назван резервом. | Составить обязательную карту reuse для API/MCP, не искать повторно без сверки |
| 2026-09-18 | Описан Tapir Archicad MCP (191+ заявленных команд), выбор запущенных экземпляров по порту. | Универсальное MCP-проксирование считать solved-by-upstream |
| 2026-09-25 | Использован `archicad-mcp-server 0.6.0`, `multiconn-archicad`, Tapir; пользовательская проверка: `get_model_summary` через MCP→Archicad 29 на 20 элементах; найдено обходное решение startup/discovery issue и NO_PROXY для localhost. | Это уже был эксперимент с готовым MCP, не просто обзор статей |
| 2026-10-07 | Аудит исходников Tapir обнаружил повторную реализацию Window/Door/Roof/Morph writer, notifications, undo; готовый registry/schema discovery также известен. Точная текущая степень дублирования в APA не перепроверена. | Изменить roadmap и удалить новые задачи по дублям |
| 2026-10-08 | Изучены HuskyBIM MCP, `lgradisar/archicad-mcp`, `alesdev88/Archicad-MCP`; пользователь потребовал best-of-breed reuse, а не новый router. | Превратить выбор в исполняемый prerequisite разработки |
| 2026-10-13 | `apa_knowledge_graph` и one-tool `apa_retrieve` MCP, PR #69, research CI 102 PASS Windows/Linux. Отдельная проблема: поиск по проектным документам, а не Tapir JSON API routing. | Не путать специфичный knowledge gateway с дублирующим generic Archicad MCP |
| 2026-10-16 | Повторное «открытие» Tapir MCP; установка ещё одного server; рабочие вызовы на AC29/AC30. | Явный провал применения предыдущих исследований и inventory installed stack |

## Проверенный GitHub-контекст, который показывает отличие APA knowledge gateway

- [Канонический research merge PR #69](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-13/apa-knowledge-gateway-research-merge-final-20261013.md): `tools/apa_knowledge_graph/mcp_adapter.py` реализует read-only `apa_retrieve` для PLAN, Artifact IDs, multi-doc references, provenance; **не** является интерфейсом к Archicad geometry/JSON API. Этот MCP был предметным и не должен автоматически объявляться лишним. PR #69 research merge и 102 test PASS подтверждают выбранный research checkout, но не production client install.
- [AGENT_PROTOCOL](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/AGENT_PROTOCOL.md) требует читать HANDOFF/CONTROL_BOARD/TASK_CARDS/PLAN и прежние доказательства, не начинать незарегистрированный S-ID, не модифицировать main/PLN/APX. В самом документе сказано, что это **не системная инструкция другому чату и не гарантия автоматического просмотра**. То есть формально описанный контракт сам по себе не принуждает агентскую работу к переиспользованию.
- [Независимый upstream Tapir MCP](https://github.com/SzamosiMate/tapir-archicad-MCP): открытый `archicad_list_commands`, `archicad_get_command_schema`, `archicad_call_tool`, `discovery_list_active_archicads`; **191+ заявлены в README, не 191 independently LIVE-tested user commands**.

## Root cause (диагноз, отделённый от оценки ущерба)

1. **Research → implementation разрыв:** исследование фиксировалось в беседе/отчёте; его вывод не становился обязательным, машиночитаемым `REUSE / EXTEND / BUILD_GAP` решением, проверяемым до написания новой функции.
2. **Нет достаточного сквозного inventory по возможности:** названия Tapir API/JSON commands, сторонних MCP routers, локальных APX, порты, версии и источники смешивались; уже установленный `archicad-mcp-server v0.6.0` не был проверен как кандидат до следующей установки.
3. **Локальные оптимумы разных исполнителей/чатов:** отдельный агент может успешно реализовать и протестировать компонент, не столкнувшись с причиной «не строить это» в другой ветке/исследовании. Инструкция читать protocol ≠ технический запрет duplicate code.
4. **Неверная метрика прогресса:** число реализованных/зарегистрированных команд и offline PASS не доказывают прирост архитектурных способностей APA; поиск upstream equivalence и сравнение реальные AC29 outcomes нужно проводить до нового adapter/writer.
5. **Нет stopping rule по дублированию:** найденный функциональный аналог не замораживал новообразование собственных gateway/writer до мотивированной проверки missing gap.

Недостаточно оснований утверждать, что «весь собственный MCP был лишним» или что «все сотни APA-команд переписаны зря». Для этого нужен code-to-code diff с актуальными ветками и версиями. Затраты/строки дублирования НЕ ИЗМЕРЕНЫ.

## Исправление должно быть исполняемым, а не ещё одним правилом в Markdown (PROPOSED_NOT_IMPLEMENTED)

1. **Зафиксировать единую capability ownership matrix** в машинном формате с полями `capability_id`, `user_goal`, `existing_provider+version+source`, `AC29_LIVE_status`, `AC30_status`, `chosen_route` (`REUSE|EXTEND|BUILD_GAP`), `missing_gap`, `evidence_ref`, `implementation_owner`, `rollback_path`. Не путать каталог команд с архитектурной функцией.
2. **PR gate на коде:** при изменениях в API-wrapper, MCP router, writers, schema registry, Add-On adapter требовать `capability_id` и upstream comparison; CI отказывает при отсутствии записей или новом адаптере поверх равнозначного active provider, кроме явно обоснованного `BUILD_GAP` с human review. CI нельзя автоматически доверить 100% семантических сопоставлений.
3. **Аудит 4 buckets по существующим функциям APA:** KEEP unique (Graph/norms/SceneWriter/SDK gap), REUSE existing without rewriting, ADAPT compatibility, REMOVE/SUSPEND provable duplicates **после** readback и регрессионной проверки. Не удалять код лишь по совпадению названий.
4. **Приоритет 29**: AC29 как стабильная production target, Tapir 1.5.10 без апгрейда до code-compatibility review; AC30 Tapir 1.7.0 только изолированные tests.
5. **Acceptance по полезной операции**, а не по числу JUnit/команд: взять характерную end-to-end задачу Archicad 29, установить экономию реализации и реально работающий правильный результат через выбранного upstream provider. Не запускать очередные сотни offline-тестов, чтобы обойти факт непроверенного runtime.
6. **Сначала проверить installed stack** (прежде чем ставить новый backend): `uv tool list`, активный stdio/host config, каталог существующих APX/MCP и фактический provenance пакетов.

## Статус и граница публикации

- Этот root cause audit записан в **существующую draft PR #110 branch**, без изменений `main`/production и без task claim.
- Протокол research hub указывает, что draft PR сам по себе **не является** canonical publication receipt или закрытием S-ID. Эту заметку нельзя считать исправлением дефекта.
- `CODE_DIFF_DUPLICATION`: NOT_PERFORMED.
- `PREVENTION_CI_GATES`: NOT_IMPLEMENTED.
- `USER_RUNTIME_MCP_AC29/AC30`: USER_REPORTED_PASS (одна read-only команда на версию).
