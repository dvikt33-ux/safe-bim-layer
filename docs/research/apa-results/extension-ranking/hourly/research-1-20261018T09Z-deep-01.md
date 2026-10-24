# APA AC29 — исследователь №1 — глубокий цикл, 2026-10-18 09Z (appendix 01)

**Факт:** 30 содержательных проверок первичных C++ исходников Tapir, кода APA, исходного 24-страничного PDF и официальной документации; 2 собственных повторных аудита. Исходники проверены GitHub fetch_file, Tapir и DXF/Raster2Seq также открыты через Opera. Никаких записей в PLN, APX, main, production code; ни одной установки или платного API.

## Три новых существенных результата
**1. MoveElements(copy=true) НЕ выполняет один SDK bulk на 100 элементов.** [Tapir 1.5.9 ElementCommands.cpp L3569–3622](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp#L3569-L3622): один JSON-запрос, но цикл из N `ACAPI_Element_Edit` по одному `API_Neig`; ответ без GUID новых копий. «Один native batch» в PR128 означает транспорт, не число SDK-операций.

**2. RotateElements(copy=true) уже существует.** [Тот же файл L3625–3780](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp#L3625-L3780): `APIEdit_Rotate`, beginPoint/endPoint/origin, `withDelete=!copy`. Это программное поэлементное вращение с копированием, но не полноценный групповой GUI Multiply.

**3. Оригинальный КР-12 PDF проверен векторно:** 34 размерных сегмента, 35 засечек, 4 якоря двух окон, 25-мм неоднозначность начала координат между общей и сегментированной размерными цепями. Существующие окна автоматически НЕ исправлять.

## 30 последовательных проходов
Формат: вопрос | проверенное свидетельство | вывод | контраудит. Не считать перечисление планов выполненными проходами.

| № | Вопрос | Первоисточник / контракт | Установлено | Контраудит |
|---:|---|---|---|---|
| 01 | План R1-01…04 | NEXT_RESEARCH_PRIORITIES.md | Требуются групповые схемы, Multiply, PDF, Raster2Seq; аудит №2 не дублировать. | План не доказательство. |
| 02 | Реестр | priority_matrix_20261018.json count=61 | Tapir/PDF/Hotlink уже учтены, не вводить дубль. | Балл не равен ускорению. |
| 03 | Пробел отчётов | research-1-09Z/10Z, audit-08Z | PDF оригинал и RotateElements ранее не исследованы. | Квитанция не заменяет PDF. |
| 04 | CreateGroups версии | Tapir ElementGroupingCommands.cpp tags 1.4.0,1.5.6,1.5.9 | Есть в 1.4.0. | Не абсолютная первая версия. |
| 05 | Readback версии | Тот же файл 1.4.0 vs 1.5.6 | GetGroupsOfElements/GetElementsOfGroups появились среди проверенных к 1.5.6. | Installed 1.5.10 не доказан. |
| 06 | Тег 1.5.10 | GitHub fetch ref=1.5.10 → 404 No commit found | Исходный тег не доступен. | Это не отсутствие установленного бинарника. |
| 07 | CreateGroups JSON | ElementGroupingCommands.cpp L24–72 | elementGroups[]/groupGuids[]; elements item elementId или groupId, optional parentGroupId. | Вложенность синтаксическая, LIVE не доказан. |
| 08 | CreateGroups SDK | ElementGroupingCommands.cpp L73–139 | В цикле ACAPI_Grouping_CreateGroup; ошибки per-group, callback возвращает NoError. | Нет гарантии all-or-nothing. |
| 09 | GetGroupsOfElements | ElementGroupingCommands.cpp ~L142–213 | elements[]→groupGuids[]; ungrouped = error APIERR_GENERAL. | Не пустой GUID. |
| 10 | GetElementsOfGroups | ElementGroupingCommands.cpp ~L214–291 | groups[]→elementsOfGroups[] прямых членов. | Рекурсивность не подтверждена. |
| 11 | SuspendGroups | ElementGroupingCommands.cpp Get/SetSuspendGroupsMode | Глобальный режим меняет групповые операции. | Setter в цикле не вызывался. |
| 12 | MoveElements schema | ElementCommands.cpp L3495–3566 | elementsWithMoveVectors[]: elementId, moveVector{x,y,z}, copy?; executionResults[] без GUID. | Нужен independent inventory. |
| 13 | MoveElements SDK — ключевой | ElementCommands.cpp L3569–3622 | Одна JSON-команда, но N ACAPI_Element_Edit по одному API_Neig. | Не один SDK bulk, 100x не доказан. |
| 14 | MoveElements copy | ElementCommands.cpp L3573–3578 | APIEdit_Drag, withDelete=!copy. | Только трансляция, не поворот. |
| 15 | RotateElements copy — новый факт | ElementCommands.cpp L3625–3780 | APIEdit_Rotate; beginPoint/endPoint/origin, copy:true. | Поэлементно; не GUI Multiply. |
| 16 | Hotlink версии | ProjectCommands.cpp tags 1.4.0,1.5.6,1.5.9,1.7.1 | CreateHotlinkNodes/Instances/Change есть в 1.5.9/1.7.1, нет в ранних. | Локальный 1.5.10 неизвестен. |
| 17 | Hotlink node JSON | ProjectCommands.cpp L2189–2249 | sourceLocation required; name/storyRangeType/refFloorIndex optional; hotlinkNodeId+existing. | Требует реального файла .mod/.pln. |
| 18 | Node reuse | ProjectCommands.cpp L2252–2329 | Совпадение source path → existing:true, story/name игнорируются. | Путь ≠ SHA модуля. |
| 19 | Instance JSON | ProjectCommands.cpp L2344–2431 | hotlinkNodeId+origin; radians rotationAngle; mirrored; floor/flags; elements[] IDs. | Node/instance/child GUID различны. |
| 20 | Instance defaults/cost | ProjectCommands.cpp L2434–2519 | ACAPI_Element_GetDefaults, затем N ACAPI_Element_Create. | Не один SDK create; defaults наследуются. |
| 21 | ChangeHotlinkInstances | ProjectCommands.cpp L2532–2607 | elementId required, origin/rotation/mirror/options optional. | Обычный MoveElements не эквивалентен. |
| 22 | PR159 LIVE | PR159 comments issuecomment-6244465302 | Native chain завершён после reconciliation+resume, scratch, 44 GUID. | Не единый непрерывный SceneWriter PASS. |
| 23 | PR162 selector | apa_ac29_group_strategy.py L80–146 | 2..128 members, ≤32 placements, ≤200 elements, exact sourceRef/signatures. | verified-флаги из intent, не live readback route. |
| 24 | PR162 graph | apa_ac29_group_strategy.py L160–279; accelerator.py L279–356 | CreateNativeGroupV1→$result→CloneNativeGroupV1, remainder MoveElements/create; preview no-write. | Runtime preflight ≠ integrated LIVE. |
| 25 | PDF original | Library 24-page PDF SHA256 75b3064d..., pages 12/14 | КР-10 14280 мм, КР-12 блок 1.7 14380 мм, окна 1600/800. | Чертёж не as-built. |
| 26 | PDF chain | Page14 vector: 34 segments, 35 chain ticks, 1 extra overall tick | Сумма 14355 мм; overall 14380 мм, 25 мм offset. | Не объявлять ошибкой чертежа. |
| 27 | PDF scale fit | 35 tick x positions least squares | 17.639264 мм/pt vs M1:50 17.638889; RMS 0.103мм, max 0.268мм. | PDF-fit ≠ точность стройки. |
| 28 | PDF 4 opening ticks | x=254.786453,351.163361,535.115601,586.139404pt | 875/2575 и 5820/6720 от chain start; +25мм от overall start. | Не менять PLN до выбора нуля. |
| 29 | DXF units | ezdxf DXF Units docs $INSUNITS/INSERT xscale | Единицы у контекста; блок cm→model m требует явного 0.01. | Исходный DXF отсутствует. |
| 30 | Raster2Seq | README master L75–102,122–158; LICENSE | Linux Python3.10.13 Torch2.3.1 CUDA11.8; RGB→2D polygons; MIT code. | Windows/8GB и лицензия весов NOT_VERIFIED. |

## Ссылки на первоисточники
- [Tapir ElementGroupingCommands.cpp 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementGroupingCommands.cpp)
- [Tapir ElementCommands.cpp 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp)
- [Tapir ProjectCommands.cpp 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp)
- [PR159 native group staged acceptance](https://github.com/dvikt33-ux/safe-bim-layer/pull/159), [PR162 group-first](https://github.com/dvikt33-ux/safe-bim-layer/pull/162), [PR128 copy-first](https://github.com/dvikt33-ux/safe-bim-layer/pull/128), [PR154 PDFVectors](https://github.com/dvikt33-ux/safe-bim-layer/pull/154), [PR160 hosted-opening restrictions](https://github.com/dvikt33-ux/safe-bim-layer/pull/160).
- [DXF units](https://ezdxf.readthedocs.io/en/stable/concepts/units.html), [Raster2Seq](https://github.com/Cornell-VAILab/Raster2Seq/blob/master/README.md).
