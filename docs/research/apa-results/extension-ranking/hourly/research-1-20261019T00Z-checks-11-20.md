# APA №1 — SOURCE-исследование готовых возможностей, 19.10.2026, UTC 00Z

**Проведено 29 последовательных содержательных проверок первоисточников**, а не названий продуктов. Ни одна не является BUILD/INSTALLED/LIVE тестом. Каждая: незакрытая функция → pinned первоисточник → точное поле/метод → вывод → контрааудит → следующий технический вопрос №2. Рейтинги — экспертная пригодность 0–100, не ускорение.

### 11. Можно ли прочитать стержневую геометрию?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html) (`A`). **Свидетельство:** ACAPI_Analytical_GetCurveMember(amGuid,elemGuid,API_AnalyticalCurveMember&), строка 546.
**Вывод:** SOURCE: typed curve-member readback. **Контрааудит:** Не смешивать физический Beam/Column и generated SAM member. **Следующий вопрос №2:** Уточнить units/cross-section и node GUID. **Приоритет:** 90/100.

### 12. Есть ли отдельные поверхностные элементы SAM?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html) (`A`). **Свидетельство:** ACAPI_Analytical_GetSurfaceElements и GetSurfaceMember, строки 555/558.
**Вывод:** SOURCE: нативные surface members и типизированная геометрия. **Контрааудит:** Не приравнивать Wall/Slab к SAM surface без модели варианта. **Следующий вопрос №2:** Проверить мембраны, проёмы и idMapping. **Приоритет:** 90/100.

### 13. Есть ли нативный граф связей SAM?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html) (`A`). **Свидетельство:** ACAPI_Analytical_GetAnalyticalMemberConnections(amGuid,elemGuid,GS::HashSet<API_Guid>&), строка 579.
**Вывод:** SOURCE: список связей, включая Analytical Links. **Контрааудит:** Это не IFC port graph и не расчёт FEM. **Следующий вопрос №2:** Сравнить связность с native graph при разрешённом read-only. **Приоритет:** 94/100.

### 14. Можно ли читать расчётные случаи без solver?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html) (`A`). **Свидетельство:** ACAPI_Analytical_GetAllAnalyticalLoadCases(GS::Array<API_Guid>&), строка 663.
**Вывод:** SOURCE: перечень Load Cases. **Контрааудит:** Наличие cases не подтверждает утверждённые нагрузки по СП или решатель. **Следующий вопрос №2:** Уточнить unit/load metadata и пустые модели. **Приоритет:** 87/100.

### 15. Можно ли читать сочетания нагрузок?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html) (`A`). **Свидетельство:** ACAPI_Analytical_GetAnalyticalLoadCombinations(GS::Array<API_Guid>&), строка 678.
**Вывод:** SOURCE: GUID сочетаний доступны. **Контрааудит:** Документация EN/IBC типов не означает соответствие российским СП. **Следующий вопрос №2:** Проверить национальные правила отдельно. **Приоритет:** 86/100.

### 16. Есть ли новый AC29 идентификатор проверки SAM?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html) (`A`). **Свидетельство:** ACAPI_Analytical_GetModelCheckTypeId(API_Guid&), строка 693; Since Archicad 29.
**Вывод:** SOURCE: только идентификатор типа проверки. **Контрааудит:** Это НЕ метод запуска проверки и НЕ вердикт SAM. **Следующий вопрос №2:** Найти зарегистрированный callback/report API29 либо NOT_FOUND. **Приоритет:** 89/100.

### 17. Есть ли нативный physical MEP system inventory?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_physical_system.html) (`M`). **Свидетельство:** PhysicalSystem::FindSystemIdsFromElementIds(vector<UniqueID>,DistributionSystemsGraph*), строка 192; Since AC29.
**Вывод:** SOURCE: system IDs по элементам, новый класс AC29. **Контрааудит:** Не дублировать IFC owner/peer graph PR167; локальные системы PLN отличаются от IFC. **Следующий вопрос №2:** Проверить nullable graph и уникальность system root. **Приоритет:** 91/100.

### 18. Что является эфемерным MEP-графом?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_distribution_system.html) (`T`). **Свидетельство:** DistributionSystem::GetPhysicalSystemIDs(), строка 164; docs: wrapper не сериализуется в PLN, lifetime связан с owning graph.
**Вывод:** SOURCE: различие transient DistributionSystem и persistent PhysicalSystem. **Контрааудит:** Не сохранять временный ID как доказательство PLN-состояния. **Следующий вопрос №2:** Уточнить lifecycle и readback persistent root. **Приоритет:** 90/100.

### 19. Можно ли отличить логическую связь от физической?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_routing_element.html) (`R`). **Свидетельство:** RoutingElement::GetLogicallyConnectedPortIdAtRouteBegin(), строка 189; документация требует PortBase::IsPhysicallyConnected для физической.
**Вывод:** SOURCE: нативное различение двух типов связности. **Контрааудит:** Не объявлять MEP route ACCEPTED по логической связи; A11.S10 остаётся BLOCKED. **Следующий вопрос №2:** Найти native read-only PortBase physical flags и endpoint diameter. **Приоритет:** 95/100.

### 20. Как выдавать IFC свойства без записи PLN?
Источник: [официальный исходник/документация конкретного тега](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_i_f_c_a_p_i_1_1_hook_manager.html) (`H`). **Свидетельство:** IFCAPI::HookManager::RegisterPropertyHook(PropertyHookFunction), строка 168; Since AC28, IFCHookManager.hpp.
**Вывод:** SOURCE: динамический export hook, альтернатива удалённому в AC29 SetIFCProperty. **Контрааудит:** Callback в add-on не равен JSON API/Tapir; жизненный цикл/ABI и права не проверены. **Следующий вопрос №2:** Проверить пример IFCHook_Test SDK29 и контракт выгрузки. **Приоритет:** 88/100.

