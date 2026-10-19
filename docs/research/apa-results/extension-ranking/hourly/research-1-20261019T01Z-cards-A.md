# APA №1 — карточки C1–C3, 2026-10-19 01Z

Готовые функции, не проект интеграции. Приоритеты 0–100 — не benchmark. SOURCE only; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=NO.

## C1 LibraryManager — 95/100
Функция и найденное: SDK29 29.3100: FindLibraries/FindLibParts, Library::IsMissing/IsPackage/GetPackageMinACVersion/GetPackageMinACBuildNumber/GetPackageDependencies.
Не дубликат: Не CloneNativeGroupV1: контроль пакетов и GDL до размещения.
Что искать: Готовый read-only library inspector.
Лицензия/Windows/AC29/API/риски: Graphisoft EULA; local AC29/Tapir1.5.10 binding NOT_VERIFIED; .libpack vs обычная библиотека.
Вопрос №2: Есть ли готовый SDK29 sample package dependencies без записи?
ГОТОВО: Read-only список package ID/min build/missing/dependencies, без PLN записи.

## C2 GSMObject — 91/100
Функция и найденное: SDK29 29.3100: GetGSMObjectOfLibPart/GetUnID/GetParameters/GetLicense/IsPasswordProtected.
Не дубликат: Не PDFVectors PR154/160, не native group PR159/162: квалификация исходной GDL детали.
Что искать: Готовый read-only GSM metadata provider.
Лицензия/Windows/AC29/API/риски: Graphisoft EULA + права GSM; UnID != element GUID; защищённые scripts; local ABI NOT_VERIFIED.
Вопрос №2: Какой официальный sample читает GSM metadata без Modify/CopyTo?
ГОТОВО: Два GSM: UnID/params/license/protection/library path с readback.

## C3 MEP Transition — 93/100
Функция и найденное: SDK29 29.3100: Transition::GetNarrowerPortID/GetWiderPortID, RoutingNode::GetTransitionIds, VentilationPort::GetShape.
Не дубликат: IFC port graph PR167 не native transition; A11.S10 BLOCKED.
Что искать: Готовый read-only native Transition/Port inspector.
Лицензия/Windows/AC29/API/риски: Graphisoft EULA, MEP entitlement NOT_VERIFIED, Tapir1.5.10 schema unknown; SetShape default != mixed writer.
Вопрос №2: Есть ли SDK29 read-only sample transition→ports→shape/size без GUID изменений?
ГОТОВО: Два native port IDs, размеры/формы и topology с независимым readback, без writes.

Источники: [SDK29 Library](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library.html#L197), [GSM](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_g_s_m_object.html#L177), [MEP](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_transition.html#L164).
