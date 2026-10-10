# APA — восстановление исследования IfcMCP и IfcPatch MergeProjects

- **Дата:** 2026-10-10; **Original Run ID:** `APA-RUN-20261010-122445Z-ifcmcp-merge-3f759`
- **Provenance:** `RECOVERED_FROM_CHAT` — восстановлено из предыдущего ответа, который не попал в GitHub. Не выдаётся за новый независимый audit.
- **ПЛАН:** APA-P10 — Независимый технический аудит Archicad 29
- **ДЕЙСТВИЕ:** APA-P10.A02 — Инструменты и интеграции
- **ТЕКУЩИЙ ПОДШАГ:** APA-P10.A02.S03 — MCP/IFC/openBIM альтернативы
- **SOURCE:** REPORTED_FROM_PRIOR_CHAT; **OFFLINE:** NOT_RUN; **BUILD:** NOT_RUN; **LIVE:** NOT_VERIFIED; **PERFORMANCE:** NOT_MEASURED
- **Источник:** IfcOpenShell repository tag `v0.9.0`; Python IFС tools, не native Archicad add-on.
- **Лицензия по предыдущему отчёту:** LGPL-3.0-or-later (должна быть перепроверена применительно к используемым подмодулям).

## APA-IFCMCP-01 — готовый MCP для IFC

**Названные ранее прочитанные исходники:**
- https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifcmcp/ifcmcp/server.py — `build_server`, FastMCP, регистрация инструментов; ранее указан blob SHA `3a899ba9c4a0b64a8e2c7dbaf194c8179d9a2da8`.
- https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifcmcp/ifcmcp/core.py — `IfcSession`, `ifc_save`, `ifc_quantify`; SHA `3f759607f3c8f7bea2ca0d73fcda292d11cb660b`.
- https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifcmcp/pyproject.toml — `requires-python`, dependencies, license; SHA `2a34c80fa9c2868c828d95dd705c2e17bcb13272`.
- https://docs.ifcopenshell.org/ifcmcp.html — описание функций и ограничений.

Все SHA и наличие файлов **только сообщены предыдущим проходом**; независимая проверка при восстановлении не производилась.

**Ранее сообщённые факты:** `IfcSession` удерживает IFC-модель в памяти; зарегистрированы инструменты `ifc_load`, `ifc_summary`, `ifc_tree`, `ifc_info`, `ifc_select`, `ifc_relations`, `ifc_materials`, `ifc_contexts`, `ifc_clash`, `ifc_validate`, `ifc_schedule`, `ifc_cost`, `ifc_schema`, `ifc_plot`, `ifc_render`; существуют `ifc_edit`, `ifc_shape`, `ifc_quantify`, `ifc_save`. Параметры `pyproject.toml` в прошлом ответе: Python `>=3.11`, `mcp >=1.0,<2`, зависимости `ifcopenshell`, `ifcquery`, `ifcedit`. Название тега 0.9.0 не обязательно совпадает с version пакета, который в файле был указан `0.0.0`.

**Критический риск:** `ifc_save(path="")` может перезаписать исходный IFC, а `ifc_quantify()` может вносить изменения в модель. Для APA необходим **read-only allowlist**; не выдавать unrestricted MCP агенту, работающему с рабочими IFC.

**Выгода:** готовая библиотека семантических запросов IFC и MCP-interface, без собственного IFC parser/command suite. **Решение:** ИНТЕГРИРОВАТЬ ВЫБОРОЧНО в отдельный контур экспорта IFC. Нативный Model Dump/Tapir оставить основой для открытого PLN.

**Непроверенное:** фактический ответ MCP `tools/list` в 0.9.0, надежность безопасной изоляции, совместимость экспортов Archicad 29, скорость, разница против прямого Python API IfcOpenShell.

## APA-IFCPATCH-MERGE-01 — объединение IFC и геопривязка

**Названные ранее прочитанные исходники:**
- https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifcpatch/ifcpatch/recipes/MergeProjects.py — `patch`, `merge`, `get_unit_name`, `reuse_existing_contexts`; ранее приведён blob SHA `1539b2865910aca4eeb60e04ac3e500c2d445144`.
- https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.9.0/src/ifcpatch/ifcpatch/recipes/SetFalseOrigin.py — преобразование геопривязки.

**Ранее сообщённые факты:** `MergeProjects` конвертирует разные единицы длины через `ifcopenshell.util.unit.convert_file_length_units`; проверяет/преобразует геопривязку через `auto_xyz2enh`, `get_grid_north`, `SetFalseOrigin`; переносит сущности в базовый IFC, совмещает `IfcProject` и переиспользует контексты представления.

**Риски:** сохранение `GlobalId` и корректность привязок требуют отдельной проверки; в результирующем файле могут оставаться несколько `IfcSite`, `IfcBuilding`, `IfcBuildingStorey`. Ранее упоминался issue о повреждении результата в версии 0.8.4; без воспроизводимого теста нельзя утверждать, что проблема устранена в 0.9.0.

**Выгода:** объединение архитектурной, конструктивной и инженерной IFC-модели для последующих QA/IfcClash, не создавая собственный движок геопривязки.

**Решение:** ИНТЕГРИРОВАТЬ ВЫБОРОЧНО только на отдельных копиях IFC, не заменяя Hotlink внутри PLN.

## Сравнение архитектур

| Вариант | Где работает | Выгода | Риск | Выбор |
|---|---|---|---|---|
| Native Archicad/Tapir/Model Dump | Открытый PLN | Редактируемая BIM семантика | Состояние PLN/API | Основной |
| IfcMCP | Экспортированный IFC | Готовые аналитические команды | Неограниченная запись в IFC | Ограниченный read-only adapter |
| IfcPatch MergeProjects | Несколько IFC | Приведение единиц/координат, федерация | Дубликаты пространственных структур | На копиях, с validation |
| Собственный IFC parser | Внешние IFC | Контроль | Дублирование зрелых библиотек | Отклонить для MVP |

## Следующий технический вопрос и испытание

**Вопрос:** лучше использовать IfcMCP или прямой Python API IfcOpenShell для читающего контура APA; сохраняются ли GlobalId, координаты и иерархия при MergeProjects?

План: проверить exact tags/dependencies, `tools/list` и allowlist; на двух **синтетических** IFC с разными единицами/геопривязкой выполнить merge только на копиях; сравнить GlobalId, IfcSite/Building/Storey, матрицы геопривязки; повторно открыть IFC, провести schema validation и сравнить с IfcClash. Никаких PLN/APX изменений.

## Передача аудитору

1. Перечитать точные строки tag `v0.9.0`, сверить приведённые SHA и лицензионные файлы.
2. Разделить source claims и запущенный MCP; исключить `ifc_save` и `ifc_quantify` из read-only.
3. Провести synthetic OFFLINE тест MergeProjects с обратным чтением и IFC validation.
4. Сравнить прямой Python API и MCP по функциональности и цене поддержки.
5. Не повышать REPORTED до VERIFIED_SOURCE/LIVE без самостоятельных доказательств.

**Результат восстановления:** GitHub commit/readback фиксируется отдельно; это не самостоятельное подтверждение ранее заявленных source-test фактов.
