# APA №2 | 2026-10-24 09Z | два внутренних контрааудита

## Контрааудит A: «CreateBeams отсутствует в authored PR74, значит APA не умеет native Beam» — ОПРОВЕРГНУТО С УСЛОВИЕМ

**Тезис:** раз `compile_authored_intent.nativeComponents` запрещает `CreateBeams`, нативная APA-owned балка требует второго GH writer или нового router.

**Проверка противоположного:** `archicad_scene_run.EXTENDED_WRITES` включает `CreateBeams`; `archicad_connected_components.adapters(['beam'])` создаёт typed adapter; `bind_plan` валидирует через существующий graph; CLI `--mode offline/preflight/execute` использует тот же `SceneWriter` и SQLite. `NativeAdapter.verify` проверяет parent Beam, child BeamSegment, material и closed BREP. [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L96), [adapter](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L98), [CLI](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L522).

**Контрариск:** authored entry не включает beam автоматически; connected CLI требует **accepted локальный source receipt**, typed JSON, runtime catalog и разрешение. Существующий `prepare_beam` ограничен c4/c5, а не generic GH. Поэтому вывод «всё BUILD-01 уже умеет собирать балки автоматически в один проход» также ЛОЖЕН.

**Вердикт:** `APA_NATIVE_BEAM_CONNECTED_ROUTE_SOURCE_FOUND`; `ONE_SHOT_AUTHORED_BEAM_NOT_FOUND`; `G0/G1/G3 NOT_PROVEN`. Никакого LIVE PASS.

## Контрааудит B: «GrasshopperPlayer + Solver Disable/Enable дают трёхстороннюю синхронизацию» — ОПРОВЕРГНУТО

**Тезис:** scriptable `-GrasshopperPlayer` и блокировка GH solver обеспечивают безопасный завершённый transaction Rhino→GH→AC→Rhino.

**Проверка противоположного:** McNeel описывает только запуск локального GH definition, выбор пути, GH command-line input/output и вычислительный lock. Нет обязательного соответствия активного `.3dm/.gh/PLN`, API native GUID, commit/rollback SceneWriter, обновления Rhino после AC и conflict ownership. GH Player может исполнить уже существующие компоненты с побочными эффектами. Даже basename resolution может выбрать не тот `.gh` через Search Paths. [Rhino 8 Help](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm), [Player](https://www.rhino3d.com/features/grasshopper/player/), [Graphisoft connection](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/).

**Вердикт:** `GHPLAYER_LOCAL_RUN_SOURCE_FOUND`, `TRIAD_SYNC_NOT_FOUND`, `SAFE_AUTO_EXECUTION_NOT_AUTHORIZED`. Требуются hash-проверка полного пути, plugin/side-effect inventory, единственный writer per GUID, read-only native diff и отдельное разрешение.

Оба контрааудита — **внутренние документарные проверки**, не независимая оценка №3 и не нормативная экспертиза. OFFLINE/INSTALLED/LIVE/ACCEPTED не выполнялись. MODEL_MODE_NOT_VERIFIABLE.
