# APA №2 / 2026-10-24 01Z — два независимых контрааудита
**Область:** только документарная и статическая проверка, без исполнения локальных тестов и без LIVE. MODEL_MODE_NOT_VERIFIABLE.

## Контрааудит A — может ли найденное расхождение Slab Z быть ложной тревогой?
**Гипотеза опровержения:** `CreateSlabs.level` с явным `floorIndex` является локальным offset, значит legacy `level=0` на втором этаже корректен.

**Проверка 1 — pinned schema 1.5.10:** `commands.CreateSlabs.parameters.slabsData.items.properties.level` описывает **Z coordinate** опорной плоскости; `floorIndex` optional, derived from level. Это согласуется с абсолютным Z, но само по себе ещё не раскрывает реализацию.

**Проверка 2 — исходный Tapir C++ 1.5.9:** `CreateSlabsCommand::SetTypeSpecificParameters` читает `inputLevel` и вызывает `ResolveFloorIndexAndOffset(parameters,"floorIndex",inputLevel,stories)`. `ResolveFloorIndexAndOffset` при переданном `floorIndex` возвращает `zPos - GetZPos(floorIndex,0,stories)`. При уровне этажа +3 и inputLevel=0 получается внутренний offset −3. Утверждение «level локальный» **опровергнуто для исходного C++ 1.5.9**.

**Проверка 3 — APA PR74:** legacy `archicad_building_shell.py#L120` передаёт `level=0` на обоих этажах, authored `archicad_authored_native_plan.py#L108` передаёт `level=story.level`. Последний отдельно проверен synthetic тестом [0,3]. В legacy тесте synthetic transport не вычисляет физический Slab Z.

**Проверка 4 — защитный readback:** `archicad_scene_run.py#L404-L413` для legacy ожидает `details.level=0`, но реальный C++ на втором этаже должен вернуть `details.level=-3` и `zCoordinate=0`. Значит ожидается **FAIL после native CREATE**, а не безопасный preflight отказ. Это прогноз, не выполненный LIVE.

**Ограничение/контраргумент:** точный исходник и бинарник локального Tapir **1.5.10** в этом прогоне не извлечены; публичный upstream tag 1.5.10 не найден, но 1.5.9 и 1.6.0 содержат одну и ту же формулу. Нельзя утверждать, что реальная установка 1.5.10 идентична C++. Не исправлять старый код без отдельного инженерного решения.

**Вердикт A:** `STATIC_CONTRACT_MISMATCH_HIGH_CONFIDENCE`, `LIVE_NOT_VERIFIED`. **Fail-closed:** не выбирать legacy `building-shell-v1` для G3 BUILD-01; выбрать уже существующий authored путь, а до любого WRITE сверить absolute Slab Z в G1.

## Контрааудит B — доказывает ли триада автоматическую двусторонность и полную BIM-приёмку?
**Гипотеза опровержения:** Graphisoft GH–AC + Rhino Content Cache + Tapir автоматически синхронизируют один BIM-элемент в трёх программах, значит APA SceneWriter можно считать уже интегрированным.

**Проверка 1 — три пространства идентичности:** Rhino Object ID (Content Cache) ≠ Archicad native GUID (Tapir) ≠ GH component/param identity. Нет проверенного штатного глобального реестра соответствий GUID, ownership и версии транзакции.

**Проверка 2 — независимые механизмы записи:** `Synchronize=True` Graphisoft GH–AC выполняет native write в Archicad вне SQLite SceneWriter. Если такой же элемент пишет APA, появляется два исполнителя. Boolean Toggle уменьшает вероятность самопроизвольной записи, но не является транзакционной блокировкой или откатом.

**Проверка 3 — обратный канал:** `Send Changes` / `Sync Changes to GH` относятся к поддерживаемым GH input/parameters. Даже успешная передача параметров не доказывает сохранение native Roof MultiPlane GUID, GDL ownership, hostWall/SEO и независимого BREP.

**Проверка 4 — удаление и циклы:** Rhino Cache `Bake` без ID может дублировать, `Purge` удаляет Rhino-объекты, а Graphisoft GH-generated библиотечные объекты могут иметь отдельный жизненный цикл. Нет единого механизма согласованного delete/undo между AC, Rhino, GH и APA.

**Проверка 5 — полнота BUILD-01:** legacy synthetic 25 элементов не содержит Roof и не удовлетворяет минимуму issue #192. Authored исторический PR74 21-элементный прототип — не новое здание. Колонны SOURCE_PARTIAL, балки NOT_WIRED, MultiPlane Roof NOT_WIRED, G0 runtime отсутствует.

**Проверка 6 — нормативы и геометрия:** сравнение размеров и IFC Mesh не доказывает соответствие СП, несущую способность, эвакуацию, доступность или тождественность исходного нативного BREP. Нужны независимые checks и экспертная верификация.

**Вердикт B:** `FULL_AUTOMATIC_NATIVE_THREE_WAY_SYNC=NOT_FOUND`; `BUILD01_ACCEPTED=NO`. Единственный допустимый пока SOURCE-маршрут: Rhino/GH → JSON → authored PR74 → SceneWriter → Tapir → AC, затем независимое readback/IFC/Save/Open. Не включать прямую GH–AC запись для APA-owned элементов.

## Общая матрица доказательности
| Уровень | Итог этого прохода |
|---|---|
| SOURCE | 30 проверенных утверждений, 2 документарных контрааудита |
| OFFLINE | 0 новых тестов |
| BUILD | 0 новых моделей |
| INSTALLED | локальные версии/порты/PLN/APX не проверены |
| LIVE | 0 новых операций |
| ACCEPTED | 0 |
| G0/G1/G2/G3/G4/G5 | BLOCKED_RUNTIME / NOT_RUN / SOURCE_PARTIAL / NOT_AUTHORIZED / NOT_RUN / NOT_RUN |

**Безопасный следующий шаг:** read-only G0 с реальным `GetStories` и scratch identity, затем штатный authored preflight. При UNKNOWN — STOP. Никаких новых writer/router/синхронизаторов.
