# APA №2 — два самостоятельных SOURCE-контрааудита, 2026-10-23 18Z

## Контрааудит A — единая координата Z во всех программах (опровержение)

**Проверяемая гипотеза:** один и тот же глобальный GH Z можно без преобразования записывать в Wall.zCoordinate и Slab.level при floorIndex=1.

**Отрицательный сценарий:** второй этаж имеет отметку +3.000 м. Если GH передаст Wall.floorIndex=1 и Wall.zCoordinate=3.000, Tapir интерпретирует Z стены как **смещение от этажа** → ожидаемая абсолютная отметка +6.000 м. Для Slab.floorIndex=1 и Slab.level=3.000 проектный Z = +3.000 м. Это различие непосредственно следует из [CreateWalls schema](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json), [authored Slab emitter](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_native_plan.py), [Wall/Slab readback](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py).

**Контрпроверка:** BUILD.wall задаёт zCoordinate=0.0 при floorIndex; SceneWriter проверяет `expected_story_level + expected["zCoordinate"]`; authored Slab пишет `float(s["level"])` и сверяет абсолютный zCoordinate. Схемный вывод однозначен, но реальный Tapir binary/AC29 runtime ещё не проверен.

**Вердикт:** `UNIFORM_GLOBAL_Z_REJECTED`; обязательна типоспецифичная координатная нормализация GH→JSON до PR74; никаких новых writer. `SOURCE_PASS; INSTALLED/LIVE=0`.

## Контрааудит B — сохранение Slab holes и безопасный откат (опровержение)

**Проверяемая гипотеза:** достаточно отправить `ModifySlabs.polygonOutline` для изменения наружного контура, и внутренние отверстия автоматически сохранятся; если нет — всегда поможет Undo.

**Отрицательный сценарий 1:** pinned Tapir 1.5.10 `ModifySlabs.slabsWithDetails[].polygonOutline` явно **заменяет весь полигон вместе с отверстиями**; без `holes` прежние отверстия удаляются. Поле `holes` допускается отдельно, без `polygonOutline`. Это не косметическое отличие: шахтный проём может исчезнуть при GH→APA обновлении. Источник: [pinned schema](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json).

**Отрицательный сценарий 2:** официальный [Archicad 29 Undo/Redo](https://help.graphisoft.com/AC/29/INT/_AC29_Help/030_Interaction/030_Interaction-67.htm) прямо сообщает: добавление/удаление этажа либо изменение его высоты **полностью очищает очередь Undo**. Поэтому `SetStories` нельзя считать обратимым «просто Undo». У [SetStories](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) статус WRITE, не READ. Требуются отдельная новая scratch PLN, снимок до изменения и Save/Open/rollback по защищённой копии.

**Отрицательный сценарий 3:** [официальный Graphisoft GH–AC29 Guide](https://help.graphisoft.com/AC/29/INT/GC.pdf) определяет `Synchronize=false` как отсутствие генерации элемента и `Null` на выходе; это **не доказательство** сохранения уже созданного элемента, и не контроль APA SQLite. [Rhino8 GH Solver Disable](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) блокирует пересчёт GH, но не заменяет блокировку внешних writer.

**Вердикт:** `MODIFY_SLAB_HOLES_MUST_BE_EXPLICIT`, `UNDO_NOT_TRANSACTIONAL_ROLLBACK`, `GH_SYNC_FALSE_NOT_APA_TRANSACTION`; `SOURCE_PASS; LIVE=0`. Оба аудита — независимые отрицательные гипотезы, выполненные одним исследователем на исходниках/официальных документах, не внешний runtime-аудит.
