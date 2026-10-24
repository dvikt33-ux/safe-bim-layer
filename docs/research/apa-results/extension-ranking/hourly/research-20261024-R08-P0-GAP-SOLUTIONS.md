# APA R08 — предметные решения критических пробелов
Дата 2026-10-24. RESEARCH ONLY, SOURCE_ONLY, LIVE_NOT_RUN. Только существующие writer; без установки, изменений main, PLN/APX и без нового Add-On.

## P0-A: События Archicad
Решение v1: после завершения операции опрашивать официальный AC29 JSON API, строить snapshot контролируемых GUID, сравнивать их и явно проверять удаление/появление. Это не real-time observer и не полный журнал всех промежуточных изменений. Стабильный hash нормализованного BIM-состояния и revision — проектная логика APA, а не штатная команда AC. Проверять охват доступных полей, полную модель и скорость. Официальный JSON API one-way HTTP: https://archicadapi.graphisoft.com/JSONInterfaceDocumentation/ . Решение v2: готовый Add-On с экспортом observer events, если найден; C++ API существует, но готового мостика не подтверждено: https://archicadapi.graphisoft.com/documentation/acapi_notify_installelementobserver ; https://archicadapi.graphisoft.com/documentation/acapi_element_attachobserver . Уведомления сгруппированы Begin/End и могут дублироваться, нельзя интерпретировать каждый callback как отдельную транзакцию: https://archicadapi.graphisoft.com/documentation/notification-manager .

## P0-B: Identity
Нельзя предполагать AC GUID=IFC GlobalId=Rhino ID. Использовать APA logical ID + verified crosswalk AC GUID, Rhino Object ID, GH source definition, IFC GlobalId, version, dependencies. Grasshopper Source Definition/Last update from Grasshopper — подтверждённые свойства происхождения (документация историческая, проверять AC29): https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680 . IfcOpenShell guid.compress/expand — только преобразование формата, не identity resolver: https://docs.ifcopenshell.org/autoapi/ifcopenshell/guid/index.html . Смена GUID означает возможную потерю hosted openings/SEO; блокировать commit до проверки.

## P0-C: Conflict and rollback
Решение v1: последовательные изменения, precondition revision, single writer per operation, snapshot before write, readback, dependency audit, commit/stop. Изменения извне могут происходить в обход APA, поэтому lock APA не гарантирует lock Archicad; повторная проверка до и после записи обязательна. Ни JSON API, ни GH Live Connection не предоставляют доказанную общую атомарную транзакцию для PLN+3DM+GH. Restore — только из проверенных snapshot с отдельным приёмочным тестом, а не гарантированный Undo. При обнаружении конфликта не применять last-write-wins.

## 3 последовательных испытания после отдельного разрешения
A. Read-only: контрольные 20 GUID; изменение вручную в копии AC; после опроса найти изменённый GUID и зависимые объекты; проверить отсутствующие поля и время.
B. Identity: создать/обновить один GH Roof; прочитать AC GUID, свойства происхождения, Rhino ID и IFC GlobalId; Save/Reopen; проверить стабильность и SEO/hosted windows.
C. Recovery: snapshot копий PLN/3DM/GH; создать намеренный конфликт; убедиться, что writer не запущен; для отказа после частичной записи проверить восстановление копии и контрольный diff.

## Статусы
A: DESIGN_SOLUTION_IDENTIFIED, IMPLEMENTATION_NOT_TESTED. B: DESIGN_SOLUTION_IDENTIFIED, MAPPING_NOT_VERIFIED. C: DESIGN_SOLUTION_IDENTIFIED, ATOMIC_ROLLBACK_NOT_AVAILABLE. Universal variant B remains OPEN. G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN.
