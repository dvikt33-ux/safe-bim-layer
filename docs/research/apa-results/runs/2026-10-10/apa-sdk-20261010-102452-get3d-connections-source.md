# APA / Archicad 29 — первоисточники 3D и связей элементов: сверка сохранившихся находок

**ПЛАН:** APA-P10 — Независимый технический аудит AC29.  
**ДЕЙСТВИЕ:** APA-P10.A01 — SDK и нативная модель.  
**ТЕКУЩИЙ ПОДШАГ:** APA-P10.A01.S01 — Проверить официальные API/сигнатуры; **частичная проверка**, не закрытие всего S01.  
**UTC:** 2026-10-10T10:24:52Z. **Фаза:** SOURCE. **Статус:** SOURCE_VERIFIED (документация), BUILD/LIVE NOT_VERIFIED.  
**Цель:** сохранить техническую дельту из уже опубликованных сообщений #apa-research и сверить её с первоисточниками. Это **не** восстановление исчезнувшего полного отчёта Deep Research.

## 1. Две документированные формы Get3DInfo — не переименовывать API на основании одного сообщения

В [официальном справочнике AC29 ModelAccess](https://graphisoft.github.io/archicad-api-devkit/group___model_access.html#gab) в перечне и разделе функции присутствует:

`GSErrCode ACAPI_ModelAccess_Get3DInfo(const API_Elem_Head& elemHead, API_ElemInfo3D* info3D)`.

В [другой официальной странице Graphisoft](https://archicadapi.graphisoft.com/documentation/acapi_element_get3dinfo) приведено:

`GSErrCode ACAPI_Element_Get3DInfo(const API_Elem_Head& elemHead, API_ElemInfo3D* info3D)`.

Обе страницы были **прочитаны** в этом проходе. Поэтому сообщение Slack APA-GEOM-03 о том, что единственно корректное имя — `ACAPI_Element_Get3DInfo`, **нельзя принимать как окончательное**: оно конфликтует с опубликованной документацией AC29, где указан `ACAPI_ModelAccess_Get3DInfo`. Возможные объяснения (переход между поколениями API, alias, документационная рассинхронизация) пока **НЕ ПРОВЕРЕНЫ**.

**Применение:** не выполнять механическую замену имени в коде. Следующий read-only gate — открыть фактические заголовки SDK 29.3100 и проверить оба объявления, затем выполнить изолированную компиляцию без установки APX и без записи PLN. `BUILD_PASS` возможен только после такой проверки.

Документация говорит, что функция выдаёт диапазон 3D body indices и может построить 3D-представление элемента независимо от текущего 3D-окна. Перспективные отсечения и 3D cutting planes при этом не учитываются. Важны ошибки `APIERR_BADID`, `APIERR_LOCKEDLAY`, `APIERR_HIDDENLAY`, `APIERR_GENERAL`. Нельзя считать этот вызов эквивалентом текущего полного scene dump.

## 2. Нативная таблица контактов не является коллизиями

[Официальный AC29 ModelAccess](https://graphisoft.github.io/archicad-api-devkit/group___model_access.html) документирует:

`ACAPI_ModelAccess_GetConnectionTable(const GS::HashSet<API_Guid>& elementList, API_ElementConnectionTable* connectionTable)`.

Входные GUID должны относиться к **активному 3D sight**; результат — пары элементов и полигоны соединяющей поверхности. Ошибки включают `APIERR_REFUSEDCMD` (3D-модель недоступна) и `APIERR_GENERAL` (активный sight).

**Применение:** кандидат на отдельный слой графа геометрических контактов. Не заменять им collision detection, host/dependent ownership и полное BREP-покрытие. Отдельно проверить активный sight, список GUID и сравнить с существующим Native Model Dump. Операции смены sight/генерации отдельной модели требуют контролируемого read-only сценария и очистки временного sight; нельзя без проверки менять состояние пользовательского 3D-окна.

## 3. Generic Opening: подтверждена связь с host, не геометрия выреза

[Официальный ACAPI_Element_GetConnectedElements](https://archicadapi.graphisoft.com/documentation/acapi_element_getconnectedelements) имеет сигнатуру:

`GSErrCode ACAPI_Element_GetConnectedElements(const API_Guid& guid, const API_ElemType& connectedElemType, GS::Array<API_Guid>* connectedElements, API_ElemFilterFlags filterBits = APIFilt_None, const API_Guid& renovationFilterGuid = APINULLGuid)`.

Документированная связь: `API_OpeningID` → `API_WallID`, `API_SlabID`, `API_MeshID`, `API_BeamID`. Это **ownership/semantic relationship**, а не доказательство геометрии отверстия, формы проёма или корректности выреза.

**Применение:** в инвентаре хранить `opening_guid -> host_guid(s)` отдельно от геометрического тела/полигона выреза. Тестировать read-only на известном PLN: прямоугольный, круглый и полигональный Generic Opening, несколько host-типов, ошибки/фильтры, сверка с моделью 3D.

## 4. Минимальная архитектурная дельта для APA

1. **Element/semantic layer:** GUID, тип, этаж, атрибуты, Opening→host и прочие документированные ownership-связи.
2. **Geometry layer:** существующий scene Model Dump + отдельный per-element body audit + при необходимости connection-table для поверхностей контакта.
3. **Parity gate:** сопоставить GUID множества, видимость, body ranges, holes, контакты и ошибки; для отсутствующего body хранить причину, а не молча исключать элемент.
4. **Writer gate:** создание/изменение BIM, GDL, Roof, MEP остаётся запрещено до отдельного разрешения и live acceptance; текущий проход ничего не изменял в PLN/APX.

**Сравнение A/B:** A — дополнять текущий Model Dump нативными семантическими и контактными API (меньше риска, предпочтительно для проверки); B — заменить им текущий dump (не доказана полнота, НЕ РЕКОМЕНДОВАНО без parity test). Производительность не измерена.

## Происхождение, расхождения, следующие проверки

- Slack [APA-GEOM-03/05](https://app.slack.com/archives/C0C886E1PGR) — сообщения о per-element 3D и connection table, использованы только как вход для независимой проверки.
- [AC29 ModelAccess API — список функций, Get3DInfo, GetConnectionTable, separate components](https://graphisoft.github.io/archicad-api-devkit/group___model_access.html).
- [Graphisoft ACAPI_Element_Get3DInfo — сигнатура, ограничения и ошибки](https://archicadapi.graphisoft.com/documentation/acapi_element_get3dinfo).
- [Graphisoft ACAPI_Element_GetConnectedElements — Opening/host types](https://archicadapi.graphisoft.com/documentation/acapi_element_getconnectedelements).
- [APA existing findings APA-05/07](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/2026-10-10-research-register.md) — уже содержали темы, но не разбирали конфликт двух документированных имён API.
- **NOT_VERIFIED:** содержимое фактических SDK 29.3100 headers; сборка AC29; работа с установленным APX; live parity, performance; полный текст пропавшего Deep Research.
- **Следующий S-ID:** продолжить APA-P10.A01.S01: точный SDK header/compile gate; затем APA-P10.A01.S03 для Model Dump parity и side effects.

**Безопасность:** не изменены main/master, production/code ветки, PLN, установленный APX; не запускался Deep Research. Отчёт — только исследовательский Markdown.
