# APA №1 — семь карточек исследователю интеграции №2

Оценки 0–100 — инженерный приоритет, не benchmark. Интеграцию не выполняли.

## C1 Design Options — 95/100
**Найдено:** SDK29 DesignOptionManager GetAllDesignOptions/GetElementsOfDesignOption/GetHotlinkInstanceDesignOptionTable. **Недублирование:** Новый уровень вариантов, не CloneNativeGroupV1. **Лицензия/версия/риск:** Graphisoft EULA; local ABI/Tapir1.5.10 NOT_VERIFIED. **Вопрос №2 и ГОТОВО:** Найти готовый read-only route и проверить GUID/вид/Hotlink без PLN записи.

## C2 Native SAM inventory — 93/100
**Найдено:** SDK29 Analytical GetCurrentAnalyticalModel/GetCurveElements/GetAnalyticalMemberConnections. **Недублирование:** Native structural graph, не IFC geometry PR170. **Лицензия/версия/риск:** Нет SAF artifact/solver/СП, канон A11.S08 BLOCKED. **Вопрос №2 и ГОТОВО:** Найти готовый SDK29 sample; ГОТОВО: variation+GUID+connections readback.

## C3 IDS Audit Tool — 93/100
**Найдено:** buildingSMART ids-tool/ids-lib source 1.0.124, MIT, net8 CLI. **Недублирование:** Проверяет IDS файл, а IfcTester — IFC на IDS. **Лицензия/версия/риск:** NuGet SHA, .NET runtime INSTALLED NOT_VERIFIED; IDS schema CC BY-ND. **Вопрос №2 и ГОТОВО:** Найти 2 отрицательных IDS; ГОТОВО: XSD vs semantic error раздельно.

## C4 MEP PhysicalSystem — 91/100
**Найдено:** SDK29 PhysicalSystem::FindSystemIdsFromElementIds; DistributionSystem::GetPhysicalSystemIDs. **Недублирование:** Persistent native system, не IFC port graph PR167. **Лицензия/версия/риск:** Graphisoft EULA, MEP entitlement/ABI NOT_VERIFIED; A11.S10 BLOCKED. **Вопрос №2 и ГОТОВО:** Готовый read-only sample; ГОТОВО: persistent system IDs + physical port flags.

## C5 IFC HookManager — 88/100
**Найдено:** SDK29 IFCAPI::HookManager::RegisterPropertyHook/RegisterAssignmentsHook. **Недублирование:** Export-time IFC metadata, не persistent PLN property и не второй IFC parser. **Лицензия/версия/риск:** Callback lifetime/SDK ABI/rights NOT_VERIFIED. **Вопрос №2 и ГОТОВО:** Найти IFCHook_Test и Unregister; ГОТОВО: source contract + export readback design.

## C6 Ifc2Sql — 86/100
**Найдено:** IfcOpenShell 0.8.5 Ifc2Sql SQLite/id_map/psets/optional geometry, LGPL3+. **Недублирование:** Independent IFC QA snapshot, не второй APA Router. **Лицензия/версия/риск:** Пишет SQL на диск, default geometry expensive, installed wheel NOT_VERIFIED. **Вопрос №2 и ГОТОВО:** ГОТОВО: IFC fixture→SQL GUID/pset/quantity readback без PLN.

## C7 IFC CRS QA — 89/100
**Найдено:** IfcOpenShell 0.8.5 auto_xyz2enh/get_crs, LGPL3+. **Недублирование:** Углубление существующей библиотеки, не новый конвертер. **Лицензия/версия/риск:** Missing CRS silently returns unchanged XYZ; source version != installed. **Вопрос №2 и ГОТОВО:** ГОТОВО: 3 negative/positive offline fixtures и inverse transformation.

Источники: [SDK29 DesignOptions](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_design_options_1_1_design_option_manager.html), [SDK29 SAM](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html), [SDK29 MEP](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_physical_system.html), [IDS Audit](https://github.com/buildingSMART/IDS-Audit-tool), [Ifc2Sql](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py).
