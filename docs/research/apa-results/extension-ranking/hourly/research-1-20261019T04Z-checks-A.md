# APA №1 04Z — 9 предметных проверок P01–P09

Зафиксирован upstream `v0.8.0`, коммит `74d4ecc67581e60b552b6ef7f6ac47d187e0f2a6`; методы проверены по конкретным исходникам, не только README. Чужие live-замеры не являются тестами APA.

## P01 — XML: чтение схемы (88/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/core/schemes.py#L90-L107.
**Контракт:** read_schedule_scheme читает колонки и numeric criteria экспортированного XML; не запрашивает действующую схему из PLN.
**Польза, риск и задание №2:** Польза: независимый список колонок для QA. Риск: экспорт может не соответствовать live-схеме. №2: проверить покрытие в APA.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P02 — XML: посимвольная защита (92/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/schemes/xml_io.py#L85-L118.
**Контракт:** round_trips_exactly требует точного no-op round-trip; LF/CRLF и неизвестные XML-узлы могут давать отказ.
**Польза, риск и задание №2:** Польза: защита provenance. Риск: проверка байтов не доказывает правильность импорта. №2: отличить parser-safe от Archicad-import-safe.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P03 — XML: привязка property GUID (89/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/schemes/spec.py#L119-L145.
**Контракт:** binding_from_bind принимает GUID свойства напрямую без живого Archicad; строковое Group/Name требует resolver.
**Польза, риск и задание №2:** Польза: готовый offline mapping. Риск: устаревший GUID. №2: сравнить с APA property inventory.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P04 — XML: привязка GDL параметра (86/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/schemes/spec.py#L143-L150.
**Контракт:** bind {gdl_param: name} описывает колонку по имени параметра библиотечного объекта.
**Польза, риск и задание №2:** Польза: ведомости дверей/окон/объектов. Риск: имя не гарантирует наличие. №2: проверить валидатор.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P05 — XML: builtin коды (82/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/schemes/spec.py#L150-L175.
**Контракт:** Есть named Quantity и raw param_type/param_index для прочих встроенных полей.
**Польза, риск и задание №2:** Польза: готовый формат, но raw коды эмпирические. №2: whitelist проверенных кодов; неизвестные отклонять.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P06 — XML: ширина колонок (78/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/schemes/spec.py#L264-L299.
**Контракт:** _apply_width идемпотентен для уже заданной ширины.
**Польза, риск и задание №2:** Польза: отсутствие дрейфа. Риск: portrait/landscape могут различаться. №2: read-only сверка.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P07 — XML: критерии фильтрации (81/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/docs/scheme-criteria-codes.md#L1-L82.
**Контракт:** Эмпирически измерены Param_Type=88/Relation_Index=1 и Param_Type=232/Relation_Index=12; сравнение позиций.
**Польза, риск и задание №2:** Польза: чтение фильтров. Риск: критерии редактировать нельзя, числовые коды не официальный SDK29. №2: не объявлять готовым editor.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P08 — XML: отсутствующий property GUID (90/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/schemes/validate.py#L43-L87.
**Контракт:** validate_scheme сопоставляет колонку с property_index открытого проекта и сообщает об отсутствующем GUID.
**Польза, риск и задание №2:** Польза: preflight ведомости. Риск: нужен живой проект, вычисление значения не проверяется. №2: безопасная read-only граница.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.

## P09 — XML: запрет перезаписи (84/100, экспертно)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/core/schemes.py#L295-L304.
**Контракт:** edit_schedule_scheme отклоняет одинаковый input/output путь.
**Польза, риск и задание №2:** Польза: сохранение исходного экспорта. Риск: новый XML может испортиться при импорте в AC29. №2: сравнить поля до/после.
**Совместимость/статус:** Лицензия MIT (внешний код), Graphisoft AC29/LP_XMLConverter — отдельно; Windows/AC29 заявлены, локальные build5101/Tapir1.5.10/RTX4060/48GB НЕ проверены. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; ускорение=NOT_MEASURED.
