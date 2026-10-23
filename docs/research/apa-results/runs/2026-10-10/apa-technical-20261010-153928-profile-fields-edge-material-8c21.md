# APA-P10.A01.S02 — source audit: этажи, composites, profiles, edge materials

**UTC:** 2026-10-10T15:39:28Z. **Executor:** `chatgpt:apa-technical`; **claim_ref:** `apa-tech-20261010T153651Z-stories-attributes-8c21`. **План:** APA-P10 → **действие:** APA-P10.A01 → **подшаг:** APA-P10.A01.S02.  
**Status:** SOURCE VERIFIED; статические 7/7 PASS; SYNTHETIC 4/4 PASS; BUILD/LIVE/installed custom Tapir 1.5.10 NOT_VERIFIED. Это read-only изучение первоисточников, без обращения к Archicad.

## Версии и прочитанные строки

- Tapir 1.5.9, commit `d0dbb11b13942e014661e1402b07958b70cd9dba`: [GetProfiles L1755–1975](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d0dbb11b13942e014661e1402b07958b70cd9dba/archicad-addon/Sources/AttributeCommands.cpp#L1755-L1975), [GetComposites L2030–2121](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d0dbb11b13942e014661e1402b07958b70cd9dba/archicad-addon/Sources/AttributeCommands.cpp#L2030-L2121).
- Tapir 1.7.0, commit `02691b5d680b60c73317e8e49b78ab14dfd4c9d8`: [GetFieldsFilter L22–48](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L22-L48), [GetProfiles schema L1153–1175](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L1153-L1175), [GetProfiles body L1827–1979](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L1827-L1979), [GetComposites L2042–2133](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L2042-L2133), [GetBuildingMaterials L2459–2552](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L2459-L2552), [GetAttributesByType L139–171](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L139-L171).
- Graphisoft SDK **29.3100**: [API_ProfileAttrType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___profile_attr_type.html), [API_AttributeDefExt](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___attribute_def_ext.html), [API_StoryInfo](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___story_info.html), [API_StoryType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___story_type.html), [API_CompWallType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___comp_wall_type.html), [API_BuildingMaterialType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___building_material_type.html).

## Новая гипотеза 1 — skinOutlines-only silently omitted

**Проблема:** в `GetProfiles` поле `skinOutlines` разрешено схемой, но отсутствует в `wantsGeometryDerivedFields` (L1827–1833). Ветвь `outlineCoords`/`outlineSubPolyEnds`/`outlineArcs` (L1928–1941) дополнительно вложена в `if (Wants("skins"))` (L1903). `GetFieldsFilter::Wants` при пропущенном `fields` возвращает true (L25–43).

**SOURCE VERIFIED в 1.5.9 и 1.7.0:** запрос `fields:["skinOutlines"]` не достигает формирования контуров. Для MVP использовать `fields:["skins","skinOutlines"]` либо опустить `fields`; не считать отсутствие outline доказательством отсутствия геометрии. SDK сообщает, что `profile_vectorImageItems` содержит также линии, сплайны, тексты, hotspots и изображения: hatch outlines не эквивалентны всей raw 2D геометрии.

**Read-only тест:** на неизменяемом тестовом PLN прочитать профиль четырьмя запросами (см. таблицу), сравнить raw JSON с нативными контурами и arcs. PASS — ожидаемые arrays и их полнота доказаны; FAIL — воспроизводимое несоответствие; NOT_VERIFIED — нет доступа к установленному APX или нативному эталону. **Вопрос аудитору:** воспроизводится ли projection issue в модифицированной установленной Tapir 1.5.10, можно ли исправить вызов только в клиенте?

## Новая гипотеза 2 — edge-level Building Materials в профилях

**Проблема:** `GetProfiles` выдаёт `skin.buildingMaterialId`, `skin.surfaceId`, `skin.fillId` (L1908–1920), а при `HatchHasProfileInfo` через `ForEachProfileEdge` сериализует **отдельный** `edges[].buildingMaterialId`, pen, line type и флаги видимости (L1943–1970). Это отдельная связь, а не доказательство, что edge и skin materials всегда различаются. HashTable `GetConstHatchObjects` не даёт явной гарантии стабильного порядка; сохранять `skinId`, не полагаться на индекс позиции.

**Кратчайший MVP:** читать `GetProfiles(fields:["skins","skinOutlines"])`, хранить `profile.skin.material` и `profile.skin.edge.material` отдельно от `face.surface` и element overrides. **Read-only тест:** профиль с контролируемыми edge materials, GUID → Building Material catalog, независимый native readback. PASS — все links/edge counts совпали; FAIL — пропуск или несовпадение; NOT_VERIFIED — эталон отсутствует. **Вопрос аудитору:** нужна ли отдельная parity-задача или покрыта `APA-P20.A01.S03`?

## Матрица native API → Tapir → ограничение

| Домен | Native SDK29 | Tapir source | MVP gate |
|---|---|---|---|
| Stories | `API_StoryInfo`, `API_StoryType.index/floorId/level` | `GetStories` в 1.7.0 использует виртуальную верхнюю запись для высоты последнего реального этажа | `floorId` — уникальный ID, не `index`; `skipNullFloor` не означает наличие этажа 0 |
| Composites | `API_CompWallType.nComps/totalThick`; `API_AttributeDefExt.cwall_compItems/cwall_compLItems` | `GetComposites` ограничивает длину skins `Min(handleCount,nComps)`, не выдаёт nComps; GetDefExt failure не превращает ответ в error | Fail-closed проверка независимого числа skins и separators (nComps+1) |
| Building Materials | `API_BuildingMaterialType`: priority, cutMaterial, cutFill, physical | `GetBuildingMaterials`: `cutSurfaceIndex` числовой индекс; `connPriority` переводится из internal в UI через Elem2UIPriority | GUID resolution и отдельный surface/face mapping |
| Surfaces | `API_MaterialID` attribute | `GetSurfaces`: GUID, index, texture, optical fields | Не подменять 3D face material или Building Material |
| Profiles | `API_ProfileAttrType`, `profile_vectorImageItems` | `GetProfiles`: useWith, modifiers, skins, outlines/arcs/edges | Не полная vector geometry; проверить `fields` и edge materials |

Ранее известный, здесь **SOURCE подтверждённый**, но не новая задача: `GetAttributesByType` вызывает `ACAPI_Attribute_GetAttributesByType` без проверки return code (L153–169); пустой каталог не всегда доказательство отсутствия атрибутов. Аналогично неполные composite skins нельзя автоматически считать PASS.

## OFFLINE/SYNTHETIC проверки

По фактически прочитанному C++ исходнику сделано **7/7 source-pattern PASS**: gate `skinOutlines`, nested `skins`, edge material, composite count truncation, отсутствие explicit GetDefExt error, virtual top story, raw-vector limitation. Первый шаблон поиска был слишком широким и дал ложный FAIL; повторно извлечено строго выражение `bool wantsGeometryDerivedFields = ... ;` — PASS. Не является runtime-испытанием.

| `fields` | derived | skins | outlines | SYNTHETIC |
|---|---|---|---|---|
| omitted | true | true | true | PASS |
| [skinOutlines] | false | false | false | PASS (ожидаемое отсутствие) |
| [skins] | true | true | false | PASS |
| [skins,skinOutlines] | true | true | true | PASS |

**Итого:** static 7/7, synthetic 4/4; BUILD NOT_VERIFIED; LIVE NOT_VERIFIED; installed Tapir 1.5.10 NOT_VERIFIED. Ни одной проверки PLN, сборки APX или измерения ускорения не было.

## Сравнение архитектур

| Критерий | A — Tapir + schema-aware validator | B — C++ native attribute/profile resolver |
|---|---|---|
| Внедрение | Использовать GetStories/GetProfiles/GetComposites/GetBuildingMaterials/GetSurfaces | Писать SDK29 bridge для counts, profiles, error codes |
| Покрытие | Skin/edge materials, outlines, modifiers; нет полного raw vector | Может покрыть весь native vector при реализации |
| Стоимость | Меньше нового кода, но требуется read-only parity | Больше C++ кода, сборка/регрессии |
| Риск | Silent partial results, неизвестная локальная версия | Ownership/API lifetime, новый APX |
| Ускорение | NOT_MEASURED | NOT_MEASURED |

**Выбор MVP: A** до доказанного пробела. Отдельный C++ resolver — только после read-only parity FAIL.

## Новый блок P/A/S на аудит

[PENDING_AUDIT proposal](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/proposals/APA-CAND-20261010-profile-field-edge-material-8c21.md), commit `673bac40f87a7ea9cfaa4bd08bca4f9f88132ca4`, readback PASS. Предварительный `APA-P20.A01.S05` — read-only parity профилей и edge materials, **не** зарегистрирован как исполняемая задача. Аудитор проверит дубли и зависимости.

## Итог / следующий шаг

Исходная задача `APA-P10.A01.S02`: source matrix составлена, **readback установленной 1.5.10 и независимый native reference отсутствуют**, поэтому **PARTIAL**, не DONE_PUBLISHED. Следующая eligible из свежего реестра предлагается `APA-P10.A02.S01` (version/compatibility), но требуется повторная проверка статуса перед claim.

Никаких изменений main/master, PLN, APX, ПО, рабочих веток. Этот документ — SOURCE исследование, не LIVE.
