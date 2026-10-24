# APA №2 | 2026-10-24 09Z | 26 реально сверенных SOURCE-фактов

Каждая строка — отдельное проверенное утверждение по прочитанному официальному HTML или конкретному исходному файлу GitHub. Это **26 утверждений, а не 26 сайтов и не 26 тестов**. Прочитанный pinned commit: `5a3a9201a715a5528c93bed4a5318e2acb32eea7`. Репозиторные SOURCE-факты не доказывают installed/runtime. Graphisoft GC.pdf в этом проходе локально не прочитан (22+ МБ и недоступен инструменту); выводы о Beam/Column Sorter из отчёта №1 09Z не входят в счёт.

| № | Проверенное утверждение | Первичный источник | Статус |
|---|---|---|---|
| 01 | Graphisoft AC29 GH Live Connection указан как build 3000 | https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ | SOURCE |
| 02 | AC29 build 3000 поддерживает Rhino 7/8 и Windows | https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ | SOURCE |
| 03 | Дата AC29 add-on Oct 1 2025, не AC30 Oct 7 2026 | https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ | SOURCE |
| 04 | Rhino8 `-Grasshopper Solver Disable/Enable` блокирует/возобновляет локальные вычисления | https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm | SOURCE |
| 05 | `GrasshopperPlayer` выполняет `.gh/.ghx` без окна GH | https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm | SOURCE |
| 06 | `-GrasshopperPlayer` принимает env vars/quoted paths, basename ищет в `.3dm` directory/Search Paths | https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm | SOURCE |
| 07 | `-GrasshopperPluginList` перечисляет плагины текущего GH файла в Command History | https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm | SOURCE |
| 08 | GH Player имеет GH Input/Output для Rhino Command Line | https://www.rhino3d.com/features/grasshopper/player/ | SOURCE |
| 09 | AC29 Rhino .3dm import создаёт non-editable GDL Object, а не native Wall | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm | SOURCE |
| 10 | Импортируемые Rhino элементы хранят исходные Rhino Layer/ID как свойства | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm | SOURCE |
| 11 | Rhino цвета импортируются как AC Surface, не доказанный BuildingMaterial | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm | SOURCE |
| 12 | AC29 позволяет Hotlink .3dm; segmentation после размещения не менять | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm | SOURCE |
| 13 | Hotlink элементы редактируются как модуль, не по одному | https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm | SOURCE |
| 14 | Для AC-based Hotlink host атрибут с совпадающим именем имеет приоритет | https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm | SOURCE |
| 15 | Удаление всех AC-based Hotlink instances может удалить их embedded library parts после reopen | https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm | SOURCE |
| 16 | `SceneWriter.ALLOWED_WRITES` не содержит CreateBeams; `EXTENDED_WRITES` содержит | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L96 | SOURCE_STATIC |
| 17 | SceneWriter добавляет расширенные команды **только** через `adapters` | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L499 | SOURCE_STATIC |
| 18 | Authored `nativeComponents` allowlist не включает CreateBeams | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L293 | SOURCE_STATIC |
| 19 | `archicad_connected_components.adapters(['beam'])` отображает Beam→CreateBeams | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L288 | SOURCE_STATIC |
| 20 | `bind_plan` компилирует connected operations через существующий catalog/BIM Graph | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L392 | SOURCE_STATIC |
| 21 | Connected CLI имеет `--source/--intent/--mode/--output`, режим offline по умолчанию | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L522 | SOURCE_STATIC |
| 22 | Connected execute использует `RUN.SceneWriter` и SQLite с typed adapters, требует fresh plan hash | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L553 | SOURCE_STATIC |
| 23 | Beam NativeAdapter ограничивает геометрию straight Basic и явные параметры | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L98 | SOURCE_STATIC |
| 24 | Beam verify проверяет parent native Beam, дочерние BeamSegment, материал и закрытый BREP | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L158 | SOURCE_STATIC |
| 25 | `prepare_beam` рассчитан только на source-bound `c4/c5`, не произвольный GH BREP | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_native_beam_details.py#L16 | SOURCE_STATIC |
| 26 | `prepare_building_parameter_edit` запрещает add/remove/type change, допускает Wall height, Door/Window width/height, Roof level; не roof pitch | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_extension.py#L117 | SOURCE_STATIC |

**Результат:** 15 официальных HTML проверок + 11 статических проверок pinned GitHub кода = **26 SOURCE**. Не проверялись: фактический установленный Rhino SR, AC29 build 5101, GH add-on, local Tapir command registration, реальные GUID, Save/Close/Reopen. Текущая онлайн-документация Tapir может описывать команды новее локальной 1.5.10; не считать её runtime доказательством.
