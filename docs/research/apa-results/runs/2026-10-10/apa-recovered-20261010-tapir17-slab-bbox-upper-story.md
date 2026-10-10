# APA — восстановленный отчёт: исправления Tapir 1.7.0 для Slab BBox и высоты верхнего этажа

**ПЛАН:** APA-P10 — Независимый технический аудит AC29. **ДЕЙСТВИЕ:** APA-P10.A02 — Инструменты и интеграции. **ПОДШАГ:** APA-P10.A02.S01 — Сверка версий Tapir и локальной 1.5.10.

- Дата исходного исследования: **2026-10-10**.
- Тип: **RECOVERED_FROM_CHAT** — публикация прошлого ответа с `GITHUB_PUBLISH_BLOCKED`, а не новый эксперимент.
- Оригинал заявлял SOURCE_VERIFIED и 4/4 статических + 2/2 синтетических PASS; при восстановлении этот статус **REPORTED**, самостоятельное повторение тестов не проводилось.
- Archicad LIVE NOT_VERIFIED. Наличие патчей в установленной модифицированной Tapir 1.5.10 NOT_VERIFIED.

Закреплённые upstream commits, указанные в предыдущем ответе:
- [Tapir 1.5.9 d0dbb11b13942e014661e1402b07958b70cd9dba](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/d0dbb11b13942e014661e1402b07958b70cd9dba), 2026-09-07 (reported).
- [Tapir 1.7.0 02691b5d680b60c73317e8e49b78ab14dfd4c9d8](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/02691b5d680b60c73317e8e49b78ab14dfd4c9d8), 2026-10-04 (reported).
- [релиз 1.7.0](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.0).

## Гипотеза 1: `Get3DBoundingBoxes` старой версии может быть опасен для Slab

В предыдущем ответе приводится:
```cpp
ACAPI_Element_CalcBounds(&elemHead, &box3D);
```
По upstream [Tapir PR #694](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/694) старый Slab path способен обратиться к отсутствующему окружению 2D-отрисовки при другом активном этаже, скрытом слое или другом окне, с возможностью SIGSEGV. **Это claim исходников/PR, а не независимо воспроизведённый crash в APA.**

В [Tapir 1.7.0 ElementCommands.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/ElementCommands.cpp#L4258-L4315) сообщён новый путь `CalculateSolidBodyBounds` для `API_RoofID || API_ZoneID || API_SlabID`, использующий нативные 3D API. Для Slab заявлено отсутствие fallback на опасный `CalcBounds`, а координаты тела описаны как мировые — не применять `tranmat` повторно.

**До проверки установленной сборки запрещено считать Slab bbox read-only вызов заведомо безопасным для рабочего проекта.** Обычный read-only не означает отсутствие риска краша приложения.

**Прочитать для независимого аудита:** [старый ElementCommands.cpp 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d0dbb11b13942e014661e1402b07958b70cd9dba/archicad-addon/Sources/ElementCommands.cpp#L4157-L4206), [новый 1.7.0](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/ElementCommands.cpp#L4258-L4315).

## Гипотеза 2: 1.5.9 может не включать высоту последнего этажа в GetStories

В оригинале показана ветка 1.5.9 `if (i + 1 < storyCount)`; последняя реальная запись не получает `height`. В обновлении 1.7.0 используется число записей, вычисленное из размера `storyInfo.data`/ `API_StoryType`, включая виртуальную верхнюю запись для расчёта высоты последнего реального этажа.

**Upstream links:** [PR #670](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/670), [ProjectCommands.cpp 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/d0dbb11b13942e014661e1402b07958b70cd9dba/archicad-addon/Sources/ProjectCommands.cpp#L748-L785), [ProjectCommands.cpp 1.7.0](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/ProjectCommands.cpp#L748-L790).

**Для MVP:** отсутствие `height` — неизвестное значение, а не ноль. Виртуальную верхнюю запись не принимать за реальный этаж. Проверять `homeStory`, `floorIndex` и `floorId` раздельно.

## Reported offline checks

Исходный отчёт заявил четыре статические проверки различий Slab/Stories и две синтетические конфигурации этажей (1,2,3 и -1,0,1), в сумме 6/6 PASS. В этом восстановленном документе **тестовые скрипты и raw outputs отсутствуют**; считать их REPORTED.

## Архитектура / выбор

| Критерий | A — текущая 1.5.10 + pinpoint backports | B — заменить всю сборку на 1.7.0 | C — собственный native adapter |
|---|---|---|---|
| Сохранение локальных функций | Высокое | Требуется полный diff | Нужен новый код |
| Slab bbox | Проверь наличие исправления, затем точечно backport | Уже заявлено upstream | Писать заново |
| Upper-story height | Проверь наличие исправления, затем точечно backport | Уже заявлено upstream | Писать заново |
| Риски | provenance локальной сборки | Потеря локальных модификаций и регрессии | API/сборка/новые баги |
| Время и скорость | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |

**Выбор:** A — provenance-first, затем только отсутствующие корректировки. НЕ заменять установленный APX в рамках исследования.

## Read-only acceptance и аудит

1. Сверить актуальный исходный commit используемой сборки с binary SHA-256 установленного APX, подтвердить наличие/отсутствие PR #694 и #670 в исходниках.
2. Не выполнять опасную Slab bbox команду на рабочем PLN до статической проверки пути API.
3. На безопасном отдельном контексте проверить таблицу этажей и высоту верхнего (чтение only).
4. PASS — цепочка исходники→APX и обе исправленные ветки подтверждены; FAIL — безопасная ветка отсутствует или расчёт этажей доказанно некорректен; NOT_VERIFIED — provenance неизвестен.

**Независимый вопрос:** содержатся ли upstream исправления в установленной 1.5.10? Правильно ли `ACAPI_ModelAccess_Get3DInfo` вычисляет bbox скрытых Slab в AC29 при независимом 3D readback? Ссылка старой функции требует независимой проверки точной SDK29 сигнатуры.

**Безопасность:** только восстановление ранее выданного текста; PLN/APX/main и установленные программы не менялись.
