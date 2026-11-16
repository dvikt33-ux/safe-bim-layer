# APA — внедрение внешних технологий, 17.11.2026

**Цель:** ChatGPT → существующий APA Windows MCP → защищённое выполнение → Archicad 30 / Rhino 8, без Codex как промежуточного агента.

**Исходное исследование:** технический отчёт от 16.11.2026. Это перечень возможностей и кандидатов, НЕ доказательство общей установки.

## Таблица решений

| Источник | Решение APA | Фактическое состояние |
|---|---|---|
| MultiConn Archicad | ADAPT: чтение и точная привязка экземпляров | Этот PR: `apa_archicad_instances.py`, 13/13 offline tests, 2 живых AC30-порта |
| SzamosiMate Tapir MCP | REUSE PATTERN: компактный инструмент, каталог по запросу | DynamicCommands и `apa_tapir_bridge.py` уже существуют; НЕ устанавливать второй MCP |
| Tapir 2.0 | REUSE: основной native backend | Каталог и защищённое чтение присутствуют; новая native запись в AC30 отдельно |
| IfcTester | REUSE существующий `apa_ifc_reports_b1.py` | Код IDSReportODS и закреплённые версии 0.8.5 уже имеются; повторная приемка IFC/ODS требуется |
| Archicad-MCP | ADAPT: безопасное подмножество YAML-правил на закреплённом снимке | Этот PR: `apa_rule_audit.py`, 12/12 offline tests, MCP `apa_bim_rules` PASS на синтетическом снимке; native PLN не испытан |
| Cassis 1.6.0 | COMPOSE с APA MCP | Готов отдельный draft PR #217; безопасный локальный MCP проверен, облачный туннель не подключён |
| Grasshopper Live Connection 30 | ADAPT только после привязки PLN | Установлен, но нативная запись и reopen НЕ испытаны |
| Graphisoft Public MCP | REVIEW в контексте лицензии/preview | Не внедрён, не делать второй исполнитель без gap evidence |
| Archicad MCP Connector | BUILD GAP ONLY | Потребуются ABI/build/license проверки для отдельных native операций |
| RoomKit / Graph2Plan | BENCHMARK против APA Spatial | Не интегрированы; сравнить одинаковое задание, геометрию, связи, время |
| HarnessBIM / Text2BIM | DESIGN REFERENCE | Код в APA не копирован, не принят |
| Boti-Ormandi MCP | REVIEW ONLY | Произвольный Python в производственной цепочке не разрешать |
| MEPbridge | BACKLOG | Инженерные сети отложены |

## Новая защита многопроектного Archicad

`scripts/apa_archicad_instances.py` использует штатный транспорт APA (не MultiConn как зависимость). Допустимы только `API.GetProductInfo`, `GetProjectInfo`, `GetAddOnVersion`. Подключение строго к `127.0.0.1` через существующий API. Явный список портов: не более 16, в диапазоне 19720..19820.

- `list`: показывает идентичность экземпляров; **никогда не выбирает первый автоматически**.
- `match`: принимает ОДИН порт, точный путь `.pln`, ожидаемую версию Archicad и Tapir. При любом расхождении `BLOCKED`.
- Ни модели, ни PLN не изменяются; любой результат содержит `modelWrites:0`.
- Доступен как opt-in инструмент `apa_instances` в существующем `apa_control_mcp.server_for` с `--discover-instances`.

### Выполненные проверки

- Windows, 13/13 unittest: PASS (моки идентификации, запреты, отрицательные сценарии).
- Локальный MCP HTTP 127.0.0.1:18789: initialize 200, tools/list показывает `apa_instances`, tools/call `list`: PASS.
- Живой `list` через API: порт 19723 → AC30 build 3001, Tapir 2.0.0, `APA-AC30-stair-test.pln`; порт 19724 → AC30 build 3001, Tapir 2.0.0, `APA-AC30-project-test.pln`.
- `match` для каждой индивидуальной идентичности: PASS; попытка сопоставить путь другого проекта с портом 19723: `BLOCKED APA_DISCOVERY_WRONG_INSTANCE`.
- Это подтверждает **read-only identity**, не сохранение и не работу с Live Connection.

## Последующие шлюзы приёмки

1. Нативная запись в AC30: только изолированный PLN, точная идентичность + резервная копия + явный допуск.
2. Повторно открыть файл и проверить GUID/BREP/геометрию; проверить выдачу планов, разрезов, фасадов.
3. Подключение к самому ChatGPT: текущий APA Secure MCP Tunnel офлайн; для запуска клиенту требуется ограниченный `CONTROL_PLANE_API_KEY`, вводимый локально. Не записывать секрет в GitHub/Fibery.
4. Интеграции с внешними алгоритмами — только после независимого сравнения с APA Spatial. Не утверждать общую приёмку дома по разным историческим тестам.

**Общий статус этого PR:** `IMPLEMENTED / READ_ONLY_LIVE_PASS / RELEASE_PENDING`.

## YAML-аудит BIM — опциональный read-only механизм

`scripts/apa_rule_audit.py` поддерживает четыре типа правил: `property-required`, `classification-required`, `layer-compliance` (список допустимых слоёв) и `zone-number-required`. Это **подмножество** схемы Archicad-MCP, не импорт чужого Python-кода. Условия `where`, regex, произвольные расширения и нативные вызовы намеренно не разрешены.

Входы: только `.json` снимок и `.yaml` набор правил в каталоге `experiments`, плюс локально подтверждённый профиль `APA_RULE_AUDIT_PROFILE_V1`, содержащий точные SHA-256 каждого файла. Снимок обязан явно перечислять прочитанные группы свойств/классификаций и флаги доступности слоёв/зон. Отсутствие прочитанных данных даёт `SKIPPED`, а не ложный `PASS` или `FAIL`. Перед и после работы проверяется SHA-256. Ни одна операция не пишет в Archicad.

Доступ через существующий APA MCP: `--rule-audit-profile path` (opt-in), инструмент `apa_bim_rules(operation="audit"|"status")`.

Проверка Windows 17.11.2026: `py_compile` PASS; 12/12 Python unittest PASS; HTTP MCP 127.0.0.1:18791 (тестовый процесс) инициализация 200, tool discovery, `apa_bim_rules status/audit` PASS; 3 успешных правила, `nativeCalls=0`, `modelWrites=0`, `liveModelVerified=false`. **Переход к нативному снимку отдельным шагом**, только после привязки точного проекта и подтверждения полноты данных.

Проверка существующего APA B1 (17.11.2026): синтетический IFC4 + IDS прошёл через `apa_ifc_reports_b1.call("ids-ods",...)` в изолированном Python-процессе; `idsPassed=true`, ODS SHA readback соответствует, версии `ifcopenshell=ifctester=0.8.5`, `modelWrites=0`. В Fibery сохранён артефакт `APA-IFC-B1-IDS-ODS-20261117`. Реальный PLN/IFC не проверялся.
