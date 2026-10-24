# APA №2 | 2026-10-24 11Z | Два внутренних контрааудита

**Область:** опровержение чрезмерных заявлений о синхронизации. Это не независимый аудит №3, не LIVE и не нативная приёмка.

## Контрааудит A — «GH Synchronize=False удаляет ранее созданный Archicad элемент»

**Проверяемое утверждение:** GH Design выдаёт `Null`, значит нативный GUID удалён из PLN и откат безопасен.

**Опровержение:** [Graphisoft AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf) документирует `Null` как **GH output** и отсутствие коммуникации, но не гарантирует удаления ранее созданного native элемента. [Исторический Graphisoft Community 2020](https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/td-p/292443) наблюдал сохранение Wall/Window/Object в AC после FALSE; отдельный `Stream Filter→empty` выполнял **другое** действие удаления. [Graphisoft User Guide 2.3](https://gsdownloads.graphisoft.com/cdn/ftp/techsupport/documentation/addons/archicad-rhino-grasshopper/AC-Grasshopper%20Connection%20User%20Guide%202.3.pdf) описывал persistence native элементов при отсутствии GH code после Save/Open. Эти исторические источники **не доказывают** поведение AC29 build5101, но запрещают принимать FALSE за delete без LIVE readback.

**Результат:** `PAUSE_NOT_DELETE` как безопасное предположение; фактическое AC29 deletion behavior = **NOT_VERIFIED**. В BUILD-01 запрещены auto delete/recreate и retry. Будущий тест только после допуска: GH-owned scratch element GUID→FALSE→GetAllElements→Save/Open→TRUE→сверка GUID/host/SEO, но в этом проходе **НЕ выполнялся**.

## Контрааудит B — «Sync Changes to GH ON = полная автоматическая трёхсторонняя BIM-синхронизация»

**Проверяемое утверждение:** AC29 автоматически обновляет GH, значит изменение Archicad обновляет Rhino, а последующая запись GH Design/APA обеспечивает общий roundtrip.

**Опровержение:** [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf) ограничивает `Sync Changes to GH` **подключёнными AC элементами → GH reference**, не обещает Rhino Object ID и не выдаёт общий transaction ID. [APA connected CLI](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L425-L440) фиксирует exact inventory всех GUID; [L549–575](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L549-L575) сравнивает retained geometry/materials/relations. GH Design `Synchronize=True` — второй writer AC, а Rhino Content Cache Push — writer только Rhino. [№1 10:56Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T1056Z-TRIAD-SPECKLE-RHINO-REFERENCE-QA.md) дополнительно подтверждает, что Speckle Rhino→AC возвращает GDL, а не native Wall/Slab/Roof. Значит даже при AC→GH auto нет native AC↔Rhino↔GH GUID-preserving roundtrip.

**Результат:** `AC_TO_GH_AUTO_REFERENCE_SOURCE_VERIFIED`; `TRIAD_NATIVE_SYNC_NOT_FOUND`. Условия будущего ACCEPTED: два направления для одного Wall/Beam/Roof; exact identity native GUID, Rhino Object ID, GH provenance, floor/host/material/BREP, no loop/duplicate/delete, conflict policy, Save/Close/Reopen, restore after crash. Ни одного из этих критериев текущий SOURCE не закрыл.

**Статусы обоих:** SOURCE_ONLY; OFFLINE=0 новых, BUILD=0, INSTALLED=NOT_VERIFIED, LIVE=0 новых, ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
