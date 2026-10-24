# APA — расширенное трёхуровневое исследование R02
Дата 2026-10-24; BUILD-01 #192; SOURCE_ONLY; без LIVE, нового writer, установок и изменения main.
## Дельта к R01
1. УПРАВЛЕНИЕ: n8n документирует Redis queue mode, worker concurrency и ограничение production executions: https://docs.n8n.io/hosting/scaling/queue-mode/ ; https://docs.n8n.io/hosting/scaling/concurrency-control/ . Это готовая очередь, но не BIM element lock и не готовый коннектор GH-AC. Предлагаемый последовательный маршрут: job_id + revision + lock на запись в модель + preflight + writer + readback + commit; это архитектурный контракт, а не готовая установленная реализация. Не добавлять n8n в обязательный стек без проверки готового коннектора и лицензии.
2. МОДЕЛИРОВАНИЕ: https://community.graphisoft.com/t5/Parametric-design/Updating-existing-Roof-Components-instead-of-creating-new-ones/td-p/592049 . Пользователь сообщил о пересоздании GH roof при перемещении колонн AC, новом GUID и потере SEO/окон. Другой пользователь продемонстрировал workaround Synchronize FALSE -> изменение колонн -> TRUE с сохранением roof GUID и окон в частном примере. НЕ гарантия AC29/BUILD-01; проверить readback GUID, hosted windows, SEO, save/reopen, и отсутствие F5 recompute recreation.
3. СОГЛАСОВАНИЕ: https://docs.ifcopenshell.org/autoapi/ifcopenshell/guid/index.html . guid.compress/expand конвертирует UUID ↔ IFC 22-char; это формат, НЕ identity mapping AC GUID ↔ IFC GlobalId. https://docs.ifcopenshell.org/ifcdiff.html : IfcDiff added/deleted/changed, geometry and optional property/container/aggregate/type/classification. IFC representation drift может давать ложный geometry diff. Проводить identity mapping только с проверенным экспортом.
## Предлагаемый контракт операции (не реализация)
Job: job_id, source_program, source_revision, element_guid, expected_ifc_global_id, operation, selected_writer, dependency_set, validation_plan.
Этапы: snapshot -> freeze GH Synchronize -> detect change -> verify source revision -> compute -> inspect -> enable exactly one writer -> readback -> export/IfcDiff -> commit -> unfreeze.
Остановка при: GUID mismatch, missing windows/GDL, SEO broken, story mismatch, conflict, stale revision, unrecognized roof type. Rollback только из подтверждённых резервных копий; Archicad Undo не считать транзакцией.
## Контрааудит 1
n8n queue concurrency не является блокировкой элемента. Установка очереди не решает конфликт с ручной правкой AC. Нужен revision check и запрет конкурирующих writers.
## Контрааудит 2
Roof workaround пользовательский, не официальный универсальный контракт. Смена GH topology, изменение количества выходных объектов и F5 recompute могут пересоздать объект; AC GUID и IFC GlobalId нельзя отождествлять без доказательства.
## Нерешённое и следующая исследовательская тройка
Управление: найти готовый AC29/Rhino8 event adapter + queue и контракт идемпотентности, исключить ручные writer конфликты.
Моделирование: матрица roof single/multi-plane, hosted windows, openings, SEO, GDL object, modifications vs recreations.
Согласование: source identity registry AC GUID/Rhino ID/GH provenance/IFC GlobalId, cross-app snapshot/rollback and cycle suppression.
## Gate
G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN; MODEL_MODE_NOT_VERIFIABLE.
