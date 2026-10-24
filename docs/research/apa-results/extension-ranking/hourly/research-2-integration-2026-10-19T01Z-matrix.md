# APA №2 — матрица подключений, 2026-10-19 01Z
Все решения SOURCE в этом цикле, оценки экспертные, не ускорение.
| Решение | Балл | Способ | Трудоёмкость | Контракт и ограничение |
|---|---:|---|---|---|
| Tapir LibraryParts | 96 | REUSE | БЫСТРО | GetAvailableLibraryParts(filterByTypeId?)→libraryParts,skippedCount; GUID только main |
| SDK29 LibraryManager/GSM | 81 | ADAPTER | ДОЛГО | GetPackageDependencies(): vector<tuple<name,Guid,subversion>>; JSON binding NOT_FOUND |
| IFC MEP util.system | 94 | REUSE | БЫСТРО | get_ports/get_port_element/get_connected_port; IFC4 Nests, IFC2X3 ContainedIn |
| IFC validate | 95 | REUSE | БЫСТРО | json_logger, UR1, validate_guid; не создавать новый валидатор |
| ezdxf MINSERT | 92 | ADAPTER | АДАПТАЦИЯ | mcount/multi_insert; PR168 считает один parent как одну assembly |
| Hotlink PR173 | 97 | REUSE | БЫСТРО | 2 instances/1 native call, 69→119 GUID; ACCEPTED не доказан |
| IFC4D util.sequence | 78 | ADAPTER | АДАПТАЦИЯ | get_work_schedule_tasks, task inputs/outputs, no scheduler |
| IFC5D util.cost | 77 | ADAPTER | АДАПТАЦИЯ | None vs 0; ZeroDivisionError swallowed |
| PR170 B3 | 88 | REUSE | БЫСТРО | use-world-coords, convert-back-units=False; world/mirror unit QA |
| SDK29 SAM | 62 | DEFER | ДОЛГО | GetAnalyticalLoadCombinations, loadFactors; no JSON bridge |
Licenses: Tapir MIT, ezdxf MIT, IfcOpenShell LGPL-3.0-or-later, Graphisoft SDK EULA. ifcbench license=null and POSIX runner => REJECT.
