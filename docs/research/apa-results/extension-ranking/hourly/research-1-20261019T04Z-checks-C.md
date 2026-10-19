# APA №1 — SOURCE проверки P19–P27

Зафиксировано по тегу `v0.8.0` (коммит `74d4ecc67581e60b552b6ef7f6ac47d187e0f2a6`), а не по неограниченному main. Исследование только исходников, не запуск. Общий контекст: Windows 11/Archicad29 заявлен автором; локальная сборка 5101, Tapir 1.5.10 и RTX4060/48GB НЕ испытывались. Чужие LIVE-замеры не считаются нашими.

## P19 — Генплан: допуски прилегания (85/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/core/drape.py#L425-L465 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** drape задаёт tol=0.005 м, step=0.1, lateral_step=0.5, max_nodes=500 и отказ без поверхности.
**Ограничение:** Числа — дефолты кода, не доказанная инженерная точность; сложный Mesh может превысить предел.
**Инженерная польза / поручение №2:** Готовые диагностические границы; №2: оценить fail-closed для крайних рельефов.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P20 — QA: готовые пять видов правил (80/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/rules/loader.py#L10-L22 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** YAML loader регистрирует property/classification/layer/zone/ifc-property checks.
**Ограничение:** Правила не эквивалентны СП/ГОСТ; часть читает опасные свойства.
**Инженерная польза / поручение №2:** Идея повторного использования только rule data, не второго MCP; №2: определить какие правила уже есть.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P21 — IFC QA: отсутствие данных не считается провалом (95/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/rules/builtin/ifc_readiness.py#L35-L56 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** IfcPropertyRequiredRule возвращает skipped, если нет GetIFCPropertiesOfElements.
**Ограничение:** Без отдельного gate пропуск может выглядеть как успешная проверка.
**Инженерная польза / поручение №2:** Отчёт должен показывать coverage/skipped; №2: не объявлять IFC PASS при SKIP.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P22 — QA: ложный балл 100 при нуле правил (99/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/rules/engine.py#L19-L27 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** run_rules выставляет score=100, если scored=[]; passed=all(empty)=true.
**Ограничение:** 100% здесь НЕ свидетельство качества BIM и опасен для выпуска.
**Инженерная польза / поручение №2:** Критическая поправка оценки; №2: fail-closed по total/scored/skipped.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P23 — QA: неполная инвентаризация official JSON (97/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/extract.py#L153-L188 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** GetAllElements/GetSelectedElements используют Tapir при наличии, иначе official JSON; внешний замер 63122 vs 16221, включая 2D.
**Ограничение:** Числа из чужого проекта, не benchmark APA; не считать official 0 отсутствием.
**Инженерная польза / поручение №2:** Нужен coverage flag для независимого QA; №2: сверить с существующим Native Model Dump.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P24 — QA: риск краха при чтении свойств (99/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/extract.py#L242-L273 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** fetch_property_cells вызывает API.GetPropertyValuesOfElements; автор зафиксировал ComposeResult abort даже на одном property/element.
**Ограничение:** Ограничение 5000 элементов не предотвращает одиночный крах; другие build/локализации неизвестны.
**Инженерная польза / поручение №2:** Запрет считать live property audit безопасным; №2: найти готовый read-only альтернативный путь.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P25 — QA: опасность активного окна (94/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/core/editability.py#L97-L141 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** refusals учитывает GetCurrentWindowType и IsEditable; автор воспроизвёл молчаливый no-op удаления при активном Layout.
**Ограничение:** Это внешний опыт AC29/5101 Tapir1.5.10, не проверка нашего APA; писать ничего нельзя.
**Инженерная польза / поручение №2:** Готовая идея окна/БД в preflight; №2: проверить существующий GuardedSave/SceneWriter gate.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P26 — QA: фильтры до рискованных property reads (87/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/core/query.py#L141-L185 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** find_elements сначала сужает GUID по типу/этажу/классификации и проверяет availability, затем читает значения.
**Ограничение:** Не исключает crash для builtin property и не выполняет серверную фильтрацию по свойствам.
**Инженерная польза / поручение №2:** Готовый принцип сдерживания риска, не отдельный движок; №2: не дублировать APA semantic selector.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.

## P27 — Teamwork: неявное резервирование связанных элементов (89/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/docs/known-issues.md#L287-L304 (v0.8.0; указаны строки/метод).
**Проверенный контракт:** Автор проверил на AC29/5101 Tapir1.5.9: резервирование двери затронуло её стену и другую дверь; замер 8.6 с.
**Ограничение:** Чужой проект и другая версия Tapir; действия изменяют Teamwork и запрещены в текущем цикле.
**Инженерная польза / поручение №2:** Требование проверять побочные GUID; №2: оценить только готовую dry-run проверку.
**Лицензия/Windows/AC29/железо:** MIT (Archicad-MCP v0.8.0); лицензия Graphisoft для AC29/LP_XMLConverter отдельно; Windows/AC29 SOURCE-заявлены, runtime APA/железо NOT_VERIFIED. **Статусы:** SOURCE=checked; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO; benchmark=NOT_MEASURED.
