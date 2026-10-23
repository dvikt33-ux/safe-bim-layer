# APA — Native Solid Links, Roof/Shell Trim и Morph Boolean: границы повторного использования

## 0. Навигационная лестница
- **ПЛАН:** APA-P10 — Независимый технический аудит AC29
  - **ДЕЙСТВИЕ:** APA-P10.A01 — SDK и нативная модель
    - **ТЕКУЩИЙ ПОДШАГ:** APA-P10.A01.S01 — Проверить официальные AC29 SDK headers/документацию, версии и сигнатуры native create/change/get
- **RUN_ID:** APA-RUN-20261010-102440-SLINKTRIM-9F2B7
- **Task ID:** APA-NATIVE-JOINTS-01
- **Дата UTC:** 2026-10-10T10:24:40Z
- **Исполнитель:** ChatGPT Plus, исследование через GitHub connector и официальные Graphisoft API reference; без Work/Codex/API-платных моделей.
- **Цель:** определить, какие нативные операции Archicad позволяют отказаться от самописных boolean/roof-trim алгоритмов, и исключить разрушительную Morph-операцию из обычного BIM-контура.
- **Входное состояние:** APA-P10.A01.S01 QUEUED; PR #20, #21, #16, #22 и Slack #apa-research сверены до исследования.
- **Границы:** никаких вызовов Archicad, тестов APX, изменений PLN или исходного кода.

## 1. Версии, происхождение, лицензия
- Цель APA: Archicad 29 build 5101; установленный Tapir 1.5.10 **не вызывался**.
- Проверен **текст** `GRAPHISOFT/archicad-api-devkit` на ref `29.3100`: `README.md`, `docs/_dev_kit.html` (заголовок «Archicad 29 C++ API: General API Development Kit 29») и `LICENSE`.
- Прямые ссылки: https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/README.md ; https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/_dev_kit.html ; https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/LICENSE .
- **Лицензия SDK:** Graphisoft Software License Agreement, **не MIT/Apache и не свободная лицензия**. Нельзя копировать/распространять SDK как часть APA без отдельной проверки условий. Наличие опубликованной документации не даёт бесплатной лицензии Archicad. Для исследования и будущего использования предполагается уже установленный Archicad 29; новые платные иностранные AI-сервисы не нужны.
- Отдельные HTML-страницы функций прочитаны на официальном `archicadapi.graphisoft.com/documentation/`; они помечены минимальными версиями API 4.2, 15 или 20. **Проверка буквального совпадения всех сигнатур с локальными заголовками DevKit 29.3100 не проводилась**. Нельзя считать это BUILD/LIVE.

## 2. Три проверенных вывода

### APA-C-NATIVE-JOINTS-01 — параметрические Solid Operation Links (SOURCE_VERIFIED)
**Прочитанный раздел:** `ACAPI_Element_SolidLink_Create`, сигнатура, Remarks, ошибки, официальный пример «Subtract Slab from Wall»:
https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_create

`GSErrCode ACAPI_Element_SolidLink_Create(API_Guid guid_Target, API_Guid guid_Operator, API_SolidOperationID operation, GSFlags linkFlags)`.

- Факт: метод создаёт **связь** Solid Operation Link между двумя строительными элементами, а не вызывает описанную ниже Morph-only операцию.
- Официальный пример: вычитание Slab из Wall в `ACAPI_CallUndoableCommand` с `APISolid_Substract` и `APISolidFlag_OperatorAttrib`.
- Ограничения: нужен undoable command scope; `APIERR_LINKEXIST` при существующей связи; `APIERR_REFUSEDPAR` для запрещённой связи hotlinked elements; недопустимые GUID и параметры дают ошибки.
- **Read-only проверка существующей связи:** `ACAPI_Element_SolidLink_GetOperators(target, &operators)` https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_getoperators ; `ACAPI_Element_SolidLink_GetOperation(target, operator, &operation)` https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_getoperation ; `ACAPI_Element_SolidLink_GetFlags(target, operator, &flags)` https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_getflags .
- **Важный неочевидный факт:** `ACAPI_Element_SolidLink_GetTime(target, operator, &linkTime, &linkSubTime)` возвращает дополнительный `linkSubTime`, потому что обычная секундная точность `GSTime` недостаточна для восстановления порядка нескольких SEO операций, созданных в одну секунду. Источник, Remarks: https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_gettime .
- Атрибуты поверхностей: `APISolidFlag_OperatorAttrib` наследует поверхности оператора; `APISolidFlag_SkipPolygonHoles` игнорирует отверстия в roof/slab операторе. Нельзя безусловно выбирать эти флаги: https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_getflags .
- **Решение:** ИНТЕГРИРОВАТЬ нативные связи и readback; **не писать** собственный Boolean engine для типовых BIM SEO. Связь и материал/порядок операций должны храниться как BIM-семантика отдельно от итоговых 3D faces.

### APA-C-NATIVE-JOINTS-02 — штатная подрезка Roof/Shell (SOURCE_VERIFIED)
**Прочитанный раздел:** `ACAPI_Element_Trim_ElementsWith`, сигнатура, ошибки, Remarks:
https://archicadapi.graphisoft.com/documentation/acapi_element_trim_elementswith

`GSErrCode ACAPI_Element_Trim_ElementsWith(const GS::Array<API_Guid>& guid_ElementsToTrim, const API_Guid& guid_Element, API_TrimTypeID trimType)`.

- Факт: метод подрезает переданные строительные элементы **конкретной Roof или Shell**; при иной геометрии обрезающего элемента возможен `APIERR_BADELEMENTTYPE`.
- Типы `APITrim_No`, `APITrim_KeepInside`, `APITrim_KeepOutside`, `APITrim_KeepAll` документированы в https://archicadapi.graphisoft.com/documentation/api_trimtypeid .
- Нужен undoable scope: `APIERR_NEEDSUNDOSCOPE`.
- **Read-only readback:** `ACAPI_Element_Trim_GetTrimmingElements(element, &roofShellGuids)` https://archicadapi.graphisoft.com/documentation/acapi_element_trim_gettrimmingelements ; `ACAPI_Element_Trim_GetTrimmedElements(roofOrShell, &trimmedGuids)` https://archicadapi.graphisoft.com/documentation/acapi_element_trim_gettrimmedelements ; `ACAPI_Element_Trim_GetTrimType(guid1, guid2, &type)` https://archicadapi.graphisoft.com/documentation/acapi_element_trim_gettrimtype .
- **Решение:** ИНТЕГРИРОВАТЬ как отдельный native Roof/Shell trim path; **не путать** с произвольными 3D коллизиями, MEP-connectivity и SEO links. Это особенно полезно для кровельного MVP, но **не исправляет автоматически** прежний Roof surface/material writer BLOCKED.

### APA-C-NATIVE-JOINTS-03 — Morph boolean уничтожает исходники (SOURCE_VERIFIED)
**Прочитанный раздел:** `ACAPI_Element_SolidOperation_Create`, Parameters, Remarks и пример:
https://archicadapi.graphisoft.com/documentation/acapi_element_solidoperation_create

`GSErrCode ACAPI_Element_SolidOperation_Create(API_Guid guid_Target, API_Guid guid_Operator, API_SolidOperationID operation, GS::Array<API_Guid>* guid_Results = nullptr)`.

- Факт: операция предназначена для **двух Morph/freeshape**; при успехе **target и operator удаляются**, а GUID результата возвращаются через `guid_Results`. `APIERR_NO3D` при неподходящих типах. Нужен undoable scope.
- Поддерживаемые коды операции описаны в `API_SolidOperationID`: subtract, upward/downward subtraction, intersection, add: https://archicadapi.graphisoft.com/documentation/api_solidoperationid .
- **Решение:** ОТКЛОНИТЬ как универсальный путь «подрезать стену/кровлю»; использовать только в отдельном явно разрешённом Morph workflow, с предварительным сохранением GUID provenance и обязательным readback. В данном исследовании ничего не вызывалось.

## 3. Сравнение архитектур и экономия времени

| Критерий | A: native SolidLink | B: native Roof/Shell Trim | C: native Morph Boolean | D: собственный mesh/CSG |
|---|---|---|---|---|
| Основной сценарий | SEO target/operator | Подрезка Roof/Shell | Morph↔Morph | Внешняя геометрия/нестандартные проверки |
| Семантика BIM | Пары GUID, operation, flags, time/subtime | Пары GUID, trim type | Результирующие GUID, исходники удаляются | Нужно реализовать собственную связь |
| Сохранение исходных BIM элементов | Связь, исходники не описаны как удаляемые | Подрезка штатных элементов | **Нет** при успешной операции | Зависит от реализации |
| Проверяемый read-only API | GetOperators/GetTargets/GetOperation/GetFlags/GetTime | GetTrimming/GetTrimmed/GetTrimType | Сравнение исходных/результирующих GUID после разрешённого теста | Самостоятельная аттестация |
| Ограничение | hotlinks, undoable scope, SEO semantics | только Roof/Shell как cutter | Morph-only, удаление исходников | Стоимость, BIM-происхождение, расхождение с Archicad |
| Решение APA | **ИНТЕГРИРОВАТЬ** | **ИНТЕГРИРОВАТЬ** | **ОТКЛОНИТЬ как общий метод** | **НЕ ПИСАТЬ для уже покрытых сценариев** |

**Преимущество для APA:** готовые операции с BIM-семантикой и обратными API-запросами сокращают объём собственного CSG-кода. **Численного ускорения проектирования или выполнения не измерено.** Не утверждать, что все типы конструктивных стыков автоматически поддерживаются.

## 4. Уровни проверки и технические риски
- SOURCE: **SOURCE_VERIFIED** — прочитаны полные релевантные разделы официальных функций и лицензионный файл DevKit 29.3100.
- OFFLINE: **NOT_RUN** — ни тестов исходников, ни парсинга модели.
- BUILD: **NOT_RUN** — компиляция against AC29 headers не проводилась.
- LIVE: **NOT_VERIFIED** — не было вызовов в Archicad 29 build 5101 и чтения реальных SEO/Trim связей.
- Критические риски: версии заголовков, отсутствие API-команды в текущем Tapir APX, неверные GUID/классы элементов, модификация PLN при writer, порядок SEO, материальные флаги, ограничения hotlink, ошибочное использование разрушительного Morph boolean.
- Стоимость: Graphisoft API в имеющемся DevKit; **не open source**; дополнительных облачных AI лицензий не требуется. Наличие у пользователя установленного Archicad не заменяет проверку лицензионных прав на использование и распространение SDK.

## 5. Следующее испытание и передача аудитору
**Следующий технический вопрос:** для одного проверенного test PLN может ли отдельный read-only native Add-On перечислить SEO links и Roof/Shell trims, получить пары GUID, `operation`, `flags`, `linkTime+linkSubTime` и `trimType` и сопоставить с текущим Native Model Dump без переключения проекта?

**Процедура (только после отдельного допуска к test instance):**
1. Проверить PID/порт/путь проекта, версии AC29/APX/SDK и неизменность GUID inventory.
2. Только read-only `GetOperators/GetTargets/GetOperation/GetFlags/GetTime` и `Trim_GetTrimmingElements/GetTrimmedElements/GetTrimType`; не вызывать `Create`, `Remove`, `Trim_ElementsWith`.
3. Записать для каждой связи обе стороны GUID, operation/trimType, флаги, `linkTime` и `linkSubTime`; проверить симметрию обратных списков.
4. Сопоставить с Native Model Dump; отдельно показать случаи отсутствия тел/невидимых слоёв; не выводить из связей факт 3D-коллизии.
5. **PASS** только при реальном readback на указанной версии и сохранённой evidence; иначе `NOT_VERIFIED`.

**Аудитору:** независимо сверить сигнатуры в локальных headers DevKit 29.3100 и допустимость лицензии; проверить, нет ли уже реализованных команд в deployed Tapir 1.5.10/APA, прежде чем добавлять C++ wrapper. При расхождении — `CONFLICT`, не разрешать writer.

## 6. Публикация
- GitHub branch: `research/apa-verified-results-hub-20261010`
- Markdown path: `docs/research/apa-results/runs/2026-10-10/apa-discovery-20261010-102440-slinktrim-9f2b7.md`
- Commit SHA и readback: фиксируются **после** записи в ARTIFACT_REGISTER; наличие этого текста само по себе не доказывает успешную публикацию.
- Изменения main/master, существующих code-веток, PLN, APX, установленного ПО: **NONE**.
