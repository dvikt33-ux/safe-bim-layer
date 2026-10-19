# APA №1 04Z — 6 карточек передачи №2

Upstream `alesdev88/Archicad-MCP v0.8.0` (12.10.2026, commit `74d4ecc67581e60b552b6ef7f6ac47d187e0f2a6`, MIT), проверен по исходникам. В реестре 61 `ALESDEV88-MCP` уже отклонён как второй исполнитель (priority2); карточки не предлагают установку сервера. Graphisoft лицензия отдельно; Windows11/AC29 заявлены, локальный build5101/Tapir1.5.10/RTX4060/48GB NOT_VERIFIED. Все SOURCE=VERIFIED, OFFLINE/BUILD/LIVE=NOT_RUN, INSTALLED=NOT_VERIFIED, ACCEPTED=NO, speed=NOT_MEASURED.

## C1 — XML ведомостей
**Функция/версия:** v0.8.0 read_schedule_scheme/round_trips_exactly/validate_scheme.
**Почему не дубликат:** Ни PR154/160, ни Publisher не доказывают чтение критериев XML.
**Неизвестные API/ABI/данные/лицензии:** AC29 import может потерять 3D Axonometry; GUID свойств/числовые критерии; MIT+Graphisoft.
**Вопрос интегратору:** №2: есть ли в APA готовый scheme inventory?.
**Критерий ГОТОВО:** ГОТОВО: два XML без перезаписи, read-only сравнение полей/критериев.
**Первоисточники:** https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0 ; точные пути/строки — P01–P27.

## C2 — OBJ/3DS→GSM
**Функция/версия:** v0.8.0 mesh.parse_obj/parse_3ds, generate.build_hsf, CLI build-source.
**Почему не дубликат:** LibPart diagnostics APA не подтверждает конвертацию mesh→HSF→GSM.
**Неизвестные API/ABI/данные/лицензии:** LP_XMLConverter AC29, масштаб, UV, текстуры, MainGUID, лицензия ассетов.
**Вопрос интегратору:** №2: есть ли готовый автономный CLI без второго MCP?.
**Критерий ГОТОВО:** ГОТОВО: версии и интерфейсы документированы; никаких BUILD без разрешения.
**Первоисточники:** https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0 ; точные пути/строки — P01–P27.

## C3 — Разметка по рельефу
**Функция/версия:** v0.8.0 create_road_marking + drape.
**Почему не дубликат:** Отличается от CloneNativeGroupV1: высоты и прилегание по Mesh/Slab.
**Неизвестные API/ABI/данные/лицензии:** 5мм tol, 500 узлов, GDL Road Marking; второй writer запрещён.
**Вопрос интегратору:** №2: существует ли готовая read-only проверка без установки сервера?.
**Критерий ГОТОВО:** ГОТОВО: автономный инструмент найден или DEFER.
**Первоисточники:** https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0 ; точные пути/строки — P01–P27.

## C4 — Полнота 2D/MEP
**Функция/версия:** v0.8.0 extract.get_all_element_ids/get_selected_element_ids.
**Почему не дубликат:** Native Model Dump APA уже есть; новая функция — coverage cross-check.
**Неизвестные API/ABI/данные/лицензии:** Official JSON может пропускать 2D/MEP; локальный Tapir1.5.10 не проверен.
**Вопрос интегратору:** №2: покрывает ли APA все типы или только model elements?.
**Критерий ГОТОВО:** ГОТОВО: матрица whole-plan/model-only без нового inventory engine.
**Первоисточники:** https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0 ; точные пути/строки — P01–P27.

## C5 — IFC QA пропуски
**Функция/версия:** v0.8.0 IfcPropertyRequiredRule.check + run_rules.
**Почему не дубликат:** IfcTester уже изучен, но отсутствует доказанный fail-closed для skipped.
**Неизвестные API/ABI/данные/лицензии:** Без IFC Tapir команда skipped; scored=[] даёт 100%; MIT.
**Вопрос интегратору:** №2: проверяет ли APA executed/skipped перед выпуском?.
**Критерий ГОТОВО:** ГОТОВО: 0 executed = NOT_VERIFIED; не внедрять второй QA.
**Первоисточники:** https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0 ; точные пути/строки — P01–P27.

## C6 — Опасные чтения свойств
**Функция/версия:** v0.8.0 extract.fetch_property_cells + core.query.find_elements.
**Почему не дубликат:** Не дублирует property API: это safety gate.
**Неизвестные API/ABI/данные/лицензии:** AC29/4006 ComposeResult abort на одном свойстве; ceiling5000 не исправляет.
**Вопрос интегратору:** №2: существует ли безопасный готовый alternative read?.
**Критерий ГОТОВО:** ГОТОВО: безопасный источник подтверждён или BLOCKED.
**Первоисточники:** https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0 ; точные пути/строки — P01–P27.
