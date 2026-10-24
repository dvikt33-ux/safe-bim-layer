# APA R03 — десять проходов по трём уровням с контрааудитами
Дата 2026-10-24. Исследование по документации, а не 10 LIVE-прогонов. BUILD-01 #192. SOURCE_ONLY; нет установок/нового writer/LIVE; main не изменять.

## Метод
Каждый проход содержит управление, моделирование, согласование и два контрааудита (ложная интеграция и сохранность данных). Проходы являются 10 последовательными проверками проектных гипотез по первоисточникам, НЕ 10 независимыми испытаниями. Отсутствие проверки в AC29 отмечается OPEN.

## Проход 01: События изменений
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: RhinoDoc events Add/Delete/Replace/ModifyAttributes.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): События Replace порождают Delete/Add; без нормализации ложные удаления.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Нужен event coalescing; готовый коннектор APA не подтверждён. SOURCE_ONLY, не LIVE PASS.

## Проход 02: Запуск вычислений
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: Hops/Rhino.Compute HTTP, GH function.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): Async/cache может вернуть устаревший результат; API доступен, но не вызывает native AC writer.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Каждое вычисление связывать с revision; LIVE не разрешён. SOURCE_ONLY, не LIVE PASS.

## Проход 03: Очередь и параллелизм
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: n8n queue/Redis; Hops max concurrent requests.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): Queue не блокирует ручную правку Archicad, не заменяет ownership.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Не ставить n8n без подтверждённого коннектора; нужен revision gate. SOURCE_ONLY, не LIVE PASS.

## Проход 04: Выбор writer
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: GH Live Connection, Tapir, существующий SceneWriter.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): Одна команда не обязана поддерживать все типы; dual writer создаёт гонку.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: На каждый элемент единственный writer в рамках операции. SOURCE_ONLY, не LIVE PASS.

## Проход 05: Roof и BIM-зависимости
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: GH Roof + Synchronize Boolean.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): Пользовательский workaround не универсален; GH recreation меняет GUID/SEO.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: GUID/readback, hosted windows, SEO обязательны. SOURCE_ONLY, не LIVE PASS.

## Проход 06: Teamwork и атрибуты
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: Graphisoft Teamwork reservation; GH source definition metadata.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): Без reservation возможны дубликаты; свойства источника исторические.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Проверить AC29 и блокировать при reservation conflict. SOURCE_ONLY, не LIVE PASS.

## Проход 07: Идентичность
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: Archicad GUID, Rhino Object ID, IFC GlobalId, GH provenance.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): UUID compress/expand меняет формат, не доказывает соответствие.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Нужен проверяемый crosswalk по контрольным элементам. SOURCE_ONLY, не LIVE PASS.

## Проход 08: Сравнение
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: IfcDiff type/property/container/aggregate/classification; Model Compare.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): IFC export может менять GlobalId/representation; ложные diff.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Два уровня проверки: native readback и IFC diff. SOURCE_ONLY, не LIVE PASS.

## Проход 09: Качество
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: IfcTester IDS, IfcClash, Archicad model QA.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): IDS не проверяет все СП и конструктивную безопасность; clashes зависят от фильтров.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Не выдавать нормативный PASS на основании одного IDS. SOURCE_ONLY, не LIVE PASS.

## Проход 10: Recovery и BUILD-01
- Управление: назначить job_id, revision, writer, precondition; запретить устаревшую запись.
- Моделирование/готовое средство: PLN/PLA, 3DM, GH, сохранение+повторное открытие.
- Согласование: фиксировать native GUID/IFC GlobalId/зависимости до и после; не принимать геометрический mesh за native BIM.
- Контрааудит A (интеграция): Undo не транзакция; нет атомарного rollback; missing library parts.
- Контрааудит B (данные): проверить дубликаты, BIM type, hosted openings, library parts, story, SEO и идентичность, иначе FAIL/UNKNOWN.
- Вердикт: Доказать snapshots, restore, save/reopen и full native types. SOURCE_ONLY, не LIVE PASS.

## Сквозная архитектура
Archicad29 является авторитетным носителем native BIM; Rhino8/GH выполняют геометрию/параметры; APA задаёт маршрут и допускает одну запись за раз; GH Live Connection — предпочтительный native bridge для поддерживаемых типов; SceneWriter/Tapir — существующий альтернативный writer; Hops/Compute — только compute; RhinoDoc events — API источник событий, требует адаптера; IfcDiff/IfcTester/IfcClash — независимые проверки; Speckle — опциональный version/transport, не native wall writer.

## Минимальный контракт задания
job_id, operation, model_revision_before, ac_guid, rhino_object_id, ifc_global_id, gh_source_definition, dependencies, selected_writer, expected_native_type, required_properties, rollback_snapshot, status. Контракт — проектная спецификация, не уже работающий код.

## Stop conditions
stale revision; reservation conflict; unrecognized native type; changed GUID; missing hosted window/door; missing GDL library; changed SEO; IFC GlobalId drift; duplicated native object; unvalidated rollback.

## Реестр остающихся дыр после десяти проходов
P0-1 нет готового end-to-end event adapter AC29↔Rhino8↔GH; P0-2 нет доказанного stable crosswalk AC GUID↔Rhino ID↔IFC GlobalId; P0-3 нет универсального update-in-place Roof/Window/Opening/SEO; P0-4 нет semantic conflict merge; P0-5 нет cycle suppression; P0-6 нет atomic rollback; P0-7 нет BUILD-01 LIVE triad acceptance. Обнаружение Rhino events, compute Hops, source metadata, IfcDiff/IfcTester/IfcClash — SOURCE подтверждены, интеграция в APA не подтверждена.

## Рекомендации следующего R04
Управление: искать существующий ready-made Rhino events→HTTP/MQTT adapter и официальный Archicad event bridge без C++ AddOn; проверять лицензию, build и факт готовой поставки. Моделирование: матрица AC29 GH native roof single/multi-plane, walls/slabs, doors/windows, SEO/GDL, compare SceneWriter. Согласование: native GUID/IFC GlobalId readback, graph dependency validation, rollback recovery test plan. Без установки и LIVE.

## Источники
1. https://developer.rhino3d.com/api/rhinocommon/rhino.rhinodoc?version=8.x
2. https://developer.rhino3d.com/api/RhinoCommon/html/E_Rhino_RhinoDoc_ReplaceRhinoObject.htm
3. https://developer.rhino3d.com/guides/compute/hops-component/
4. https://developer.rhino3d.com/guides/compute/compute-faq/
5. https://help.graphisoft.com/AC/29/INT/GC.pdf
6. https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
7. https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680
8. https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
9. https://docs.ifcopenshell.org/ifcdiff.html
10. https://docs.ifcopenshell.org/ifctester.html
11. https://docs.ifcopenshell.org/ifcclash.html

## Gates
G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.
