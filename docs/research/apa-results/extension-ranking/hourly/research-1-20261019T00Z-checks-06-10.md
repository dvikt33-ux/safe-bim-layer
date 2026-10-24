# APA №1 — проверки 6–10, 19.10.2026 00Z

Источник: официальный DevKit29 **tag 29.3100**, не живой Graphisoft Doxygen (теперь AC30). Каждая запись — самостоятельный контракт; SOURCE, не LIVE.

### 6. Проверить статус элемента по GUID
[SDK29 D, L223](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_design_options_1_1_design_option_manager.html#L223): `GetDesignOptionStatusOf(API_Guid)`. **Вывод:** Готовый статус привязки. **Контрааудит:** Не эквивалент группам APA. **Следующее №2:** Проверить missing/default. Статус SOURCE.

### 7. Перечислить активные варианты комбинации
[SDK29 D, L160](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_design_options_1_1_design_option_manager.html#L160): `GetActiveDesignOptionsOfCombination(combination)`. **Вывод:** Возможен QA выбора варианта. **Контрааудит:** Комбинация может не быть назначена виду. **Следующее №2:** Сопоставить с #03. Статус SOURCE.

### 8. Прочитать текущий SAM
[SDK29 A, L516](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html#L516): `ACAPI_Analytical_GetCurrentAnalyticalModel(API_Guid&)`. **Вывод:** Native SAM read-only entrypoint. **Контрааудит:** View-dependent; SAF/solver не доказан. **Следующее №2:** Проверить lazy generation. Статус SOURCE.

### 9. Закрепить variation SAM
[SDK29 A, L522](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html#L522): `ACAPI_Analytical_GetAnalyticalModelVariation(amGuid,variation&)`. **Вывод:** Есть typed контекст аналитической модели. **Контрааудит:** Без variation GUID недостаточен. **Следующее №2:** Проверить serialization fields. Статус SOURCE.

### 10. Перечислить SAM стержни
[SDK29 A, L543](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html#L543): `ACAPI_Analytical_GetCurveElements(amGuid,Array<API_Guid>&)`. **Вывод:** Готовая curve inventory. **Контрааудит:** Физический Beam != SAM member. **Следующее №2:** Сравнить native count с IFC. Статус SOURCE.

