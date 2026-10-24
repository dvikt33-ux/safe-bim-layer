# APA — исследование трёх уровней №1 (2026-10-24)
Статус SOURCE_ONLY. BUILD-01 #192. Без LIVE/установок/нового writer.
## 1. Управление: Hops
Официальный источник https://developer.rhino3d.com/guides/compute/hops-component/ . Rhino 7/8 Windows, Grasshopper Hops вызывает GH-определение как функцию, Enabled, асинхронное выполнение, локальный Rhino.Compute. Возможность разделить compute и запись; НЕ управляет Archicad, НЕ BIM транзакция. Контрааудит: Hops Enabled не заменяет разрешение GH AC Synchronize; вычисление может завершиться после изменения входных параметров — проверять ревизию задания.
## 2. Моделирование: GH AC Synchronize
Официальный источник https://help.graphisoft.com/AC/29/INT/GC.pdf . Boolean Synchronize для Design/Document компонентов. FALSE: не создаёт элемент, возвращает Null; TRUE: синхронизирует при активной связи. Рекомендуемая цепь расчёт->проверка->синхронизация->readback->запрет дальнейшей записи. Не утверждать, что FALSE откатывает изменения или сохраняет библиотечные части; удалить GH компонент рискованно.
## 3. Согласование: IfcDiff
Официальный источник https://docs.ifcopenshell.org/ifcdiff.html . Added/Deleted/Changed по GlobalId; type/property/container/aggregate/classification; геометрия. Не гарантирует AC GUID; разные representations одной геометрии могут вызвать ложный diff; экспорт IFC должен сохранять GlobalId.
## Предлагаемый сквозной маршрут (не испытан)
APA назначает job_id, model_revision, BIM element target; Hops Enabled TRUE только для расчёта, возвращает результат; GH Synchronize FALSE до валидации; если поддерживаемый тип и разрешение записи, переключить TRUE; Archicad Python API/Tapir readback GUID, тип, свойства, bbox; сравнить IFC snapshot IfcDiff; при несовпадении остановка, не выполнять второй writer. Это архитектурная гипотеза, НЕ готовый автоматизированный оркестратор.
## Открытые проблемы
Автоматическая передача результатов Hops в существующую GH дефиницию, выбор writer для roof/windows, identity AC GUID/Rhino Object ID/IFC GlobalId, conflict merge, rollback, гарантии сохранения Embedded Library, Save/Close/Reopen BUILD-01.
## Два контрааудита
A: Hops Enabled и GH Synchronize — разные переключатели; не соединять напрямую без контроля ревизии, иначе stale-result race.
B: IfcDiff не подтверждает native GUID и не восстанавливает модель. Нельзя называть PASS.
## Следующий цикл трёх уровней
Управление: поиск готового механизма job/revision lock с безкодовой интеграцией.
Моделирование: официальная матрица native AC29 GH roof/windows/host/SEO.
Согласование: стабильный GUID↔GlobalId и воспроизводимый IFC экспорт.
G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.
