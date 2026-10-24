# APA №1 20261019T03Z — содержательные проверки P16–P30

### P16 Publisher names
**Вопрос и свидетельство:** GetPublisherSetNames() → List[str]; AC29 Python lines 1062–1075; [SDK29/AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Источник имён наборов, уже покрыт №2. **Контрааудит:** Имя ≠ опубликованный PDF. **Следующий вопрос:** №2: reuse, не дублировать.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P17 Hotlink proxy GUID
**Вопрос и свидетельство:** GetHotlinkProxyElementTable, lines 735–766; key=proxy, value=source; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___hotlink.html#L735).
**Вывод:** Read-only source↔proxy mapping. **Контрааудит:** SDK C++ ≠ JSON/Tapir binding. **Следующий вопрос:** №2: найти готовый binding.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P18 Hotlink source
**Вопрос и свидетельство:** GetHotlinkSourceStatus, lines 829–859; invalid location→APIERR_REFUSEDPAR; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___hotlink.html#L829).
**Вывод:** Проверка доступности. **Контрааудит:** Доступность ≠ SHA. **Следующий вопрос:** №2: enum и binding.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P19 Nested Hotlink
**Вопрос и свидетельство:** GetContainingHotlinkGuid, lines 434–466; APINULLGuid для обычного элемента; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___hotlink.html#L434).
**Вывод:** Read-only принадлежность. **Контрааудит:** Null GUID ≠ error. **Следующий вопрос:** №2: nested/ordinary.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P20 Hotlink instances
**Вопрос и свидетельство:** GetHotlinkInstances, lines 471–503; возвращает корни; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___hotlink.html#L471).
**Вывод:** Счётчик размещений PR173. **Контрааудит:** Корни ≠ все дети. **Следующий вопрос:** №2: 2 roots vs 48 children.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P21 Hotlink owner
**Вопрос и свидетельство:** GetHotLinkOwner, lines 698–730; APINULLGuid для обычного; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___hotlink.html#L698).
**Вывод:** Прямой owner. **Контрааудит:** Не приравнивать к containing без nested test. **Следующий вопрос:** №2: сравнить owner/containing.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P22 Renovation filters
**Вопрос и свидетельство:** GetRenovationFilters, lines 224–250; Array<API_Guid>; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___renovation.html#L224).
**Вывод:** Перечень фильтров. **Контрааудит:** C++ only; JSON NOT_FOUND. **Следующий вопрос:** №2: готовый binding?.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P23 Active renovation
**Вопрос и свидетельство:** GetActualRenovationFilter, lines 159–184; GUID; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___renovation.html#L159).
**Вывод:** Снимок current filter. **Контрааудит:** Current ≠ saved view. **Следующий вопрос:** №2: проверить saved view.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P24 Filter names
**Вопрос и свидетельство:** GetRenovationFilterName, lines 189–219; localized name; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___renovation.html#L189).
**Вывод:** GUID primary, name label. **Контрааудит:** Локализация меняет имя. **Следующий вопрос:** №2: GUID/name across languages.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P25 Mutation gate
**Вопрос и свидетельство:** SetActualRenovationFilter, lines 301–327; changes current filter; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___renovation.html#L301).
**Вывод:** Исключить из read-only. **Контрааудит:** Смена состояния ≠ чтение. **Следующий вопрос:** №2: НЕ вызывать.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P26 Property expression lint
**Вопрос и свидетельство:** CheckPropertyExpressionString, lines 2269–2296; APIERR_BADEXPRESSION; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___property.html#L2269).
**Вывод:** Готовый syntax check. **Контрааудит:** Syntax ≠ semantic validity. **Следующий вопрос:** №2: existing binding?.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P27 Property reference
**Вопрос и свидетельство:** GetPropertyExprReferenceString, lines 2566–2594; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___property.html#L2566).
**Вывод:** Готовая ссылка для выражения. **Контрааудит:** Строка ≠ GUID. **Следующий вопрос:** №2: built-in/user-defined.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P28 Property value type
**Вопрос и свидетельство:** IsValidValue, lines 2865–2893; checks valueType/collectionType/enums; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___property.html#L2865).
**Вывод:** Готовый type gate. **Контрааудит:** Type ≠ units/norms. **Следующий вопрос:** №2: valid/invalid read-only.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P29 Owner database
**Вопрос и свидетельство:** GetContainingDatabase, lines 630–662; APIERR_NOPLAN; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___database.html#L630).
**Вывод:** Read-only owner DB. **Контрааудит:** DB ≠ этаж. **Следующий вопрос:** №2: plan vs layout.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.

### P30 Local origin
**Вопрос и свидетельство:** GetLocOrigo, lines 1048–1075; user origin relative virtual origin; [SDK29/AC29](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___database.html#L1048).
**Вывод:** Только coordinate context. **Контрааудит:** User Origin ≠ survey origin. **Следующий вопрос:** №2: independent survey anchor.
**Статус:** SOURCE_VERIFIED; OFFLINE/BUILD/LIVE_NOT_RUN; INSTALLED_NOT_VERIFIED; ACCEPTED_NO.
