# APA №1 — BUILD-01, 22.10.2026 04Z — проверки 01–10

**SOURCE_ONLY.** 10 независимых предметных вопросов (не LIVE). Локальная AC29 build5101/Tapir1.5.10 не опрошена; upstream не является установленной версией. Баллы не являются benchmark.

### S01 — G0: Совпадает ли архивная схема с реально установленным дополнением?
**Источник:** [L](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json) (архивный каталог Tapir 1.5.10; локальный APX не сверен; MIT только upstream). **Факт/поля:** В сохранённом каталоге есть команды и версия провайдера 1.5.10; SHA бинарного APX в нём отсутствует. **Решение/ограничение:** Не считать сохранённый каталог текущим runtime. **Адресное задание №2:** №2: сравнить GenerateDocumentation/JS SHA, GetAddOnVersion и APX SHA на активном порту только READ.

### S02 — G0/G4: Можно ли полагаться на GetModelDumpV1 как на команду из каталога?
**Источник:** [L](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json) (архивный каталог Tapir 1.5.10; локальный APX не сверен; MIT только upstream). **Факт/поля:** Ключ GetModelDumpV1 отсутствует в сохранённом JSON, хотя P/G вызывают его. **Решение/ограничение:** Разрыв между расширенным исполнителем и архивной схемой, не доказательство отсутствия в APX. **Адресное задание №2:** №2: отдельно установить namespace, регистрацию и схему GetModelDumpV1; до этого nativeGeometryAudit=BLOCKED.

### S03 — G4: Можно ли использовать Get3DGeometryOfElements без установки?
**Источник:** [L](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json) (архивный каталог Tapir 1.5.10; локальный APX не сверен; MIT только upstream). **Факт/поля:** Команда отсутствует в сохранённом каталоге 1.5.10, хотя присутствует в исходнике upstream 1.7.2. **Решение/ограничение:** SOURCE upstream не равно INSTALLED. **Адресное задание №2:** №2: не назначать её обязательным G4-readback; сначала подтвердить реальную регистрацию.

### S04 — G0: Достаточно ли GetProjectInfo для защиты несохранённых изменений?
**Источник:** [L](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json) (архивный каталог Tapir 1.5.10; локальный APX не сверен; MIT только upstream). **Факт/поля:** Выходные поля isUntitled/isTeamwork/projectLocation/projectPath/projectName; dirty/readOnly отсутствуют. **Решение/ограничение:** Нельзя делать автоматический Open на основании только GetProjectInfo. **Адресное задание №2:** №2: требовать независимый GUI close/dirty guard и защищённую копию до G4.

### S05 — G0: Проверяет ли существующий контроль точный build 5101?
**Источник:** [P](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) (APA PR74 pinned commit; внутренняя лицензия репозитория не исследована). **Факт/поля:** archicad29() проверяет product.version==29, но не сравнивает build с 5101. **Решение/ограничение:** Реальная сборка остаётся самостоятельным критерием G0. **Адресное задание №2:** №2: read-only GetProductInfo version/build/language и запись в runtime manifest.

### S06 — G0: Разрешён ли произвольный новый путь PLN через существующий writer?
**Источник:** [R](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py) (APA SceneWriter pinned commit; внутренняя лицензия не исследована). **Факт/поля:** bind_isolated_writer_pln ограничен одним путём; bind_authorized_saved_copy требует точный saved_sha256 и authorizationRef. **Решение/ограничение:** Нельзя подменять новую scratch простым CLI override. **Адресное задание №2:** №2: документировать approved binding, SHA, port и разрешение; без него STOP.

### S07 — G1: Можно ли вывести высоту верхнего этажа только из старого GetStories?
**Источник:** [T15](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp) (Tapir upstream tag 1.5.9; MIT). **Факт/поля:** В 1.5.9 height выводится лишь если i+1<storyCount; у последнего этажа поле пропущено. **Решение/ограничение:** Высота верхнего этажа должна быть явно задана. **Адресное задание №2:** №2: передать authoredStoryHeightsMeters для всех этажей, не выводить верхнюю высоту из пустого поля.

### S08 — G1: Проверяет ли authored adapter согласованность отметок?
**Источник:** [N](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py) (APA authored adapter pinned commit; внутренняя лицензия не исследована). **Факт/поля:** Требует heights для каждого story и равенство level[i]+height[i]≈level[i+1]. **Решение/ограничение:** Использовать готовую проверку, не создавать второй story compiler. **Адресное задание №2:** №2: предъявить реальные nativeStoryBindings, проверить last story height и абсолютные отметки.

### S09 — G1: Поддерживает ли PR74 балки и дополнительные Slab как authored additions?
**Источник:** [P](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) (APA PR74 pinned commit; внутренняя лицензия репозитория не исследована). **Факт/поля:** Whitelist nativeComponents: CreateColumns/Doors/Windows/Walls/Roofs; CreateBeams и дополнительные CreateSlabs исключены. **Решение/ограничение:** Нельзя считать их G1 PASS из-за наличия команд Tapir. **Адресное задание №2:** №2: для первого здания использовать существующие базовые slabs; балки пометить OPTIONAL_UNSUPPORTED.

### S10 — G1/G2: Что реально ограничивает кровлю authored-маршрута?
**Источник:** [P](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) (APA PR74 pinned commit; внутренняя лицензия репозитория не исследована). **Факт/поля:** Требуются pivotLine, structureType=Basic, buildingMaterialId; XY-контур в envelope с запасом 0.35 м. **Решение/ограничение:** Готовый маршрут ограничен односкатной Basic Roof. **Адресное задание №2:** №2: явно задать материал, угол в радианах и контур; сложные крыши вынести из первой приёмки.
