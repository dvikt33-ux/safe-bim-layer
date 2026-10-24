# APA A5 — независимый аудит и диспетчер BUILD-01, цикл 16Z, 24.10.2026

**Объект:** issue #192, https://github.com/dvikt33-ux/safe-bim-layer/issues/192 (OPEN при проверке). **Ветка публикации:** research/apa-extension-ranking-hub-20261018. **Срез:** 24.10.2026, цикл 16:00–16:59 UTC (19:00–19:59 МСК). **Режим:** SOURCE-only, без доступа к локальному Windows, Archicad, Rhino или SQLite. **MODEL_MODE_NOT_VERIFIABLE.**

## 1. Входы: реальное наличие, независимый Git blob SHA-1

Проверены существование файлов на исследовательской ветке, фактические UTF-8 байты через GitHub connector и независимый расчёт Git SHA-1 по формуле SHA1("blob " + byte_length + NUL + bytes). Сопоставлены с SHA каталога GitHub. Это доказывает целостность текстов на ветке, **не** исполнение заявленных ими процедур.

| Роль | Файл в этом каталоге | UTC в имени | Байты | SHA-1 Git blob | Приёмка |
|---|---|---:|---:|---|---|
| R1 | research-1-20261024T1603Z-BUILD01-G0-RUNTIME-DECISION-GATES.md | 16:03 | 18203 | 10173bf788344de8a85a926c98cac44a6f6053c9 | FOUND / SHA_MATCH / 16Z |
| R2 | research-2-20261024T1603Z-BUILD01-CONFLICT-OWNERSHIP-LEDGER.md | 16:03 | 18495 | fd551db40d8d690a79a786aaa62bfe090c3e41b7 | FOUND / SHA_MATCH / 16Z |
| R3 | research-3-20261024T1602Z-BUILD01-GH-BASE-P0-CHECKLIST.md | 16:02 | 17962 | 9d04949b908b7d786172efbe290dcf2b2b7d606b | FOUND / SHA_MATCH / 16Z |
| I4 | integrator-4-20261024T1620Z-BUILD01-G0-G1-RUNTIME-STOP-CONTRACTS.md | 16:20 | 24157 | 64b30c6fa9980c3633be2332d10c5d9fa4b853f4 | FOUND / SHA_MATCH / 16Z |
| Предыдущий A5 | audit-a5-20261024T1543Z-BUILD01-G0G1-STRICT-COUNTERAUDIT.md | 15:43 | 24480 | af0ab17e54b556001a47572a5d858e8c9eda76a8 | FOUND / SHA_MATCH / контекст |

**Итог входов:** 4/4 FOUND, 4/4 независимо SHA_MATCH. Пропавших обязательных отчётов в известном окне 16Z нет. Отчёты не содержат фактического G0-manifest с ноутбука или G1 preflight receipt. Статусы этих ворот не повышать.

## 2. Контрааудит A: первоисточники, версии, лицензии и границы применимости

1. **Graphisoft, официальный дистрибутив:** https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/ — Grasshopper–Archicad **29** Live Connection, **build 3000**, Windows, Rhino **7/8**, дата публикации **01.10.2025**; несовместим с Start Edition. У Graphisoft также имеется AC30, но это не основание подменять AC29. Доступность скачивания **SOURCE**, не INSTALLED и не доказательство работы с конкретным AC29 build 5101. Лицензии Archicad/Rhino не подтверждены.
2. **Tapir, официальный upstream:** https://github.com/ENZYME-APD/tapir-archicad-automation — готовый Archicad Add-On с JSON-командами, Grasshopper Plugin описан как work in progress, исходники MIT. Фактические GetAddOnVersion=1.5.10, SHA256 локального APX, регистрация команд, совместимость runtime schema и наличие лицензий хост-приложений **не наблюдались**. Лицензия MIT исходников не доказывает состояние отдельного Yak-бинарника.
3. **Immutable PR74:** https://github.com/dvikt33-ux/safe-bim-layer/tree/5a3a9201a715a5528c93bed4a5318e2acb32eea7 — независимо прочитаны scripts/archicad_semantic_brief.py, scripts/archicad_authored_native_plan.py, scripts/archicad_scene_run.py и scripts/archicad_project_accelerator.py. В semantic_brief прямо указано, что GENERATE_FROM_ZERO описывает этажи, но **не создаёт PLN или native stories**. В authored_native_plan Evidence READS ограничен GetProjectInfo/GetStories/GetAttributesByType; наличие GetFavoritesByType в frozen Tapir не означает доступность через этот интерфейс.
4. **Схемы и атрибуты:** frozen Tapir 1.5.10 schema в PR74 — исходный артефакт, не фактический список команд локального APX. Window/Door libraryPartName, Favorites, материалы, GetAvailableLibraryParts.skippedCount и точные Roof/Slab поля требуют сравнения с локальной средой. При skippedCount>0 инвентаризация библиотеки PARTIAL, а не PASS.
5. **Rhino/Grasshopper:** GH-BASE описан как схема компонентов и параметров, но .gh, RhinoCommon NURBS/BREP и допуски не исполнялись. Численный пример не является BREP/СП PASS. IfcOpenShell/IfcTester могут быть независимым QA при наличии действительного IFC; такого результата в этом цикле нет.

**Вердикт CA-16A:** SOURCE_VERSION_CONFIRMED_SCOPED; LICENSE_RUNTIME_NOT_VERIFIED; LOCAL_SCHEMA_NOT_VERIFIED. Запрещено повышать это до INSTALLED/LIVE.

## 3. Контрааудит B: воспроизводимость, один writer, идентичность, конфликты

**Единственный утверждённый маршрут:** Rhino 8/GH (параметры и QA) → ручной перенос в существующий apa-authored-project/1 → PR74 typed compiler/BIM Graph → **один** существующий SceneWriter/SQLite → Tapir → native Archicad 29. Обратное чтение Archicad API/Graphisoft GC29 допускается только как READ. Готовый GH DataTree→PR74 адаптер **не найден лишь в ограниченно проверенных 12 Python-файлах PR #74/#126/#131/#149/#162**; это не глобальное NOT_FOUND. Автоматическая двунаправленная синхронизация **не доказана**. Запрещён второй GH Design Create/Modify, Tapir GH Push, Bake→Morph/GDL как параллельный writer для BUILD-01.

**Идентичность:** Rhino ObjectId и GH path не равны native GUID; APA projectId/stepId/scene_id/plan_hash — идентификаторы намерения; **только Archicad** выдаёт GUID нативного элемента. IFC GlobalId — отдельный ID. story nativeIndex/floorId/level берутся только из фактического GetStories. Window/Door ownerWallId обязан ссылаться на подтверждённый созданный Wall GUID; parent создаётся до child, host и story проверяются readback.

**SQLite и конкуренция:** в PR74 есть BEGIN IMMEDIATE, проверка scene_id ИЛИ plan_hash и журнал ATTEMPTED до вызова; BEGIN IMMEDIATE сериализует пишущие транзакции **в одной SQLite базе**. Отдельного UNIQUE(plan_hash) в просмотренном DDL нет. Поэтому нельзя заявлять глобальную идемпотентность при разных SQLite файлах, внешних писателях или обходе единственного процесса; отсутствие UNIQUE само по себе **не доказывает** гонку внутри одной базы. Для G3 — один процесс, один журнал, один scene_id/plan_hash, отсутствие чужих writers.

**Семь STOP-контрактов:** CREATE timeout/UNKNOWN → остановить, прочитать SQLite+Archicad, не повторять CREATE; UPDATE → только существующая проверенная Modify-команда; DELETE → запрет без явного допуска; PARTIAL_SLAB → CreateSlabs→GUID/readback→ModifySlabs в одном writer, не повторять Create; HOST_DRIFT → STOP без rehost; FEEDBACK_LOOP → отключить второй канал записи; чужой project/story/schema → STOP до вызова. SQLite rollback не откатывает PLN, Rhino Undo не откатывает Archicad; атомарный rollback между тремя программами NOT_FOUND_IN_SCOPED_SOURCES. Восстановление только из заранее сохранённой отдельной scratch-копии после независимой сверки и санкции.

**Native BIM:** Wall/Slab/Column/SinglePlane Roof/Window/Door допускаются только при реальных локальных контрактах и GUID/type/story/host/material readback. Beam присутствует в Tapir, но вне authored nativeComponents allowlist PR74; не объявлять G1 Beam PASS. GH BREP, Morph/GDL, IFC-меш и прямоугольный bounding box сложной формы не заменяют нативную конструкцию. Отверстия перекрытий, PolyRoof, сложные узлы, автоматический нормативный PASS не доказаны.

**Сохранение:** G3 COMPLETE_UNSAVED не равен сохранённому PLN. G4 требует отдельно разрешённого GuardedSave → Close → отсутствие открытого проекта → Reopen → независимый GUID/type/story/host/material/BREP diff. G5 — второе **новое** задание на другом scratch PLN; прежний CREATE не повторять.

**Пять отдельных вердиктов:** GH_GEOMETRY, AC_NATIVE, IFC_STRUCTURE, IDS_INFORMATION, NORMATIVE_REVIEW. Все UNKNOWN до фактических evidence. **Вердикт CA-16B:** SOURCE_ONE_WRITER_CONTRACT_CONFIRMED; BUILD_NOT_REPRODUCED; ROLLBACK_NOT_ATOMIC; G0_RUNTIME_REQUIRED.

## 4. Ворота G0–G5 и критерии ГОТОВО

| Gate | Фактический статус | Критерий ГОТОВО и проверяемое evidence |
|---|---|---|
| G0 | **BLOCKED_RUNTIME_NOT_OBSERVED** | С ноутбука: AC29 build 5101, действительная лицензия/порт, GetProjectInfo, путь и SHA256 утверждённого scratch PLN, GetStories минимум два native stories с index/floorId/level/activeIndex, локальный Tapir 1.5.10 GetAddOnVersion/APX SHA256/registered schema, materials/Favorites/library/skippedCount, Rhino 8 SR/units/tolerances, GC29 installed, локальный APA commit, отсутствие чужих несохранённых правок; иначе один точный BLOCKED_REASON |
| G1 | **NOT_RUN** | Только после G0: новый schema-valid двухэтажный authored JSON, реальный targetProjectPath, typed DAG/topological order, bindings, plan hash, одна команда PR74 --preflight с разрешённым read-only транспортом; result READY_FOR_EXPLICIT_TEST_RUN, modelWriteAttempts=0, inventory before=after, SHA evidence. G1 не является автономным offline запуском: читает Archicad |
| G2 | **SOURCE_PARTIAL / LOCAL_NOT_VERIFIED** | Сопоставление local/frozen/upstream команд Window/Door/Slab/SinglePlane Roof/Column, GUID/story/host/material и библиотеки; STOP при drift/неоднозначности. Beam вне обязательного P0 |
| G3 | **NOT_AUTHORIZED / NOT_RUN** | Отдельная явная санкция exact scratch PLN/port/confirmPlanHash, один SceneWriter/SQLite, intent-before-write, GUID/BREP readback, остановка при UNKNOWN. LIVE_CREATED_UNSAVED ≠ ACCEPTED |
| G4 | **NOT_RUN** | Санкционированные Save/Close/Reopen, независимый persisted native GUID/type/story/host/material/BREP diff и SHA квитанции |
| G5 | **NOT_RUN** | Второй иной план и новый scratch PLN, новый native readback и независимая проверка без повторного прежнего CREATE |

**Решение A5 по вопросам I4:** (1) SOURCE-объём R1/R2/R3 достаточен для перехода к G0; не расширять список плагинов без нового blocker. (2) Для текущего PR74 до G1 должны существовать две соответствующие native stories в утверждённом scratch PLN; GENERATE_FROM_ZERO их не создаёт. (3) G3 разрешается только отдельным явным решением владельца на exact PLN/port/hash; этот аудит разрешения не даёт. (4) Native readback + Save/Open — необходимое доказательство G4, но не заменяет IFC/IDS/нормативные вердикты, если они входят в критерии итоговой приёмки.

## 5. Открытые блокеры и следующая очередь

| ID | Приоритет | Blocker | Закрывающее доказательство |
|---|---|---|---|
| B01 | P0 | Нет доступа к фактической среде ноутбука | Реальный read-only G0 manifest; не заполненный предположениями |
| B02 | P0 | Нет доказанных двух native stories и exact scratch identity | GetStories + GetProjectInfo + SHA256 scratch + отсутствие чужих unsaved изменений |
| B03 | P0 | Не доказаны локальные APX/schema, materials, Favorites, library | SHA256 APX, actual commands, local/frozen comparison, skippedCount |
| B04 | P0 | Нет нового G0-bound authored JSON и G1 receipt | Единственный PR74 preflight после G0, immutable plan hash, inventoryUnchanged=true |
| B05 | P0 | G3 не санкционирован | Явный отдельный допуск; до него STOP |
| B06 | P1 | Автоматический GH→PR74 bridge не доказан | Для G1 использовать ручной JSON, не создавать writer/router |
| B07 | P1 | GH BREP/IFC/IDS/СП и rollback не проверены | Отдельные независимые вердикты после реальных моделей, без ложного PASS |

**Управленческий предел:** при отсутствии runtime evidence нельзя закрыть G0/G1 ещё одним SOURCE-обзором. Никаких бесконечных повторных каталогов инструментов, исследования только под конкретный новый STOP.

## 6. Четыре адресных поручения на следующий час (17Z)

### R1 — native BIM, P0 / 98
**Задача:** не повторять перечень команд; подготовить для I4 **одну компактную G0 таблицу исполнения** для AC29 build/PLN/stories/Tapir APX/schema/материалов/Favorites/library и локального решения Window/Door/Slab/Roof. Если появился runtime manifest — сверить actual с frozen и выдать точные PASS/DRIFT/STOP; если нет — явно отметить NOT_OBSERVED, передать один запрос evidence владельцу среды. **ГОТОВО:** таблица field→read source→actual/evidence→STOP, четыре решения по элементам; никаких вымышленных локальных значений, no code/no LIVE.

### R2 — мосты/синхронизация, P1 / 84
**Задача:** не искать заново GH bridge в прежних 12 файлах. Проверить на SOURCE-уровне **ровно одну** уязвимость запуска: что гарантирует BEGIN IMMEDIATE в одном SQLite файле, чего не гарантирует при разных ledger/процессах; составить STOP для duplicate plan_hash/scene_id и UNKNOWN, один read-only reconciliation runbook. Удержать запрет второго writer и авто-DELETE/UPDATE. **ГОТОВО:** матрица single-db vs multiple-db vs GH writer, exact STOP/readback, без новых router/SQLite-кода и без запуска G3.

### R3 — параметрика/геометрия/нормативы, P1 / 80
**Задача:** не расширять плагины. Свести GH-BASE в **один проверяемый P0 handoff**: метры/масштаб 0.001 при mm, outline/rooms/bearingLines/stories/roof/openings, NEG-Z/NEG-HOST/NEG-UNIT, пять независимых QA verdict. Отделить expected от executed; сложные BREP/hole/PolyRoof не маскировать bbox. **ГОТОВО:** один минимальный параметрический контракт и ожидаемые STOP, все неисполненные тесты NOT_RUN; передача I4 без нового .gh writer.

### I4 — исполнимая схема, P0 / 100
**Задача:** главный результат — **фактический G0**, затем **один G1**. Если runtime доступен и разрешён read-only доступ: получить signed/time-stamped manifest с exact scratch/port/stories/APX/schema/material/library/Rhino/GC29, сравнить с PR74, затем только разрешённый --preflight с новым output dir и immutable intent; зафиксировать before/after inventory, typed DAG, plan hash, SHA. Если runtime недоступен: не симулировать, опубликовать точный BLOCKED_RUNTIME_NOT_OBSERVED и **один** закрывающий перечень необходимых измерений; не делать повторную длинную интеграционную компиляцию. **ГОТОВО:** G0 RUNTIME_READY + G1 READY_FOR_EXPLICIT_TEST_RUN с native writes=0 и квитанциями **либо** точный блокер с отсутствующими доказательствами. G3 не выполнять.

## 7. Строгие итоговые статусы и ограничения

- **SOURCE:** четыре входа 16Z и предыдущий A5 FOUND/SHA_MATCH; официальный Graphisoft/Tapir и immutable PR74 проверены; два независимых контрааудита выполнены.
- **OFFLINE:** 0 новых запусков PR74/GH; описанные ранее численные проверки не являются G1.
- **BUILD:** 0 новых зданий BUILD-01.
- **INSTALLED:** NOT_VERIFIED (нет доступа к ноутбуку).
- **LIVE:** 0 новых native writes; G1 read-only preflight NOT_RUN.
- **ACCEPTED:** 0.
- **NOT_FOUND:** только scoped GH→PR74 auto adapter в ранее проверенных 12 файлах, atomic cross-app rollback и PolyRoof/slab-hole в проверенном authored P0; **не** утверждать глобальное отсутствие.
- **G0/G1/G2/G3/G4/G5:** BLOCKED_RUNTIME_NOT_OBSERVED / NOT_RUN / SOURCE_PARTIAL / NOT_AUTHORIZED / NOT_RUN / NOT_RUN.
- **NEXT_RESEARCH_PRIORITIES.md:** прочитан, **оставлен без изменений**: изменение при конкурирующих авторах без необходимости создаёт риск перезаписи.
- **Запреты:** main, исходники, PLN/APX, установка, LIVE, merge, платные API, Work/Codex/Arena не затрагивались.

**Публикационная приёмка этого A5:** только после GitHub create → readback по immutable commit и branch → независимый Git blob SHA-1; при любом несовпадении — WRITE_BLOCKED. **Решение:** STALLED_EXTERNAL_DEPENDENCY до реального G0, следующий критерий прогресса — runtime evidence, а не новый объём SOURCE. **MODEL_MODE_NOT_VERIFIABLE.**
