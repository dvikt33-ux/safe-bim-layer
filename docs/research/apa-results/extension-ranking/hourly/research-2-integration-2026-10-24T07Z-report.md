# APA №2 | 2026-10-24 07Z | BUILD-01: официальный GH Beam против PR74 allowlist; два Synchronise и три write-gates

**Объект:** issue #192, Archicad 29 build5101 / Tapir 1.5.10 / Windows 11 + Rhino 8 + Grasshopper. **Статус:** SOURCE_ONLY. Ожидаемые версии НЕ проверены в установленной среде. Ни установки, ни LIVE, ни модификации PLN/APX/кода, ни merge. MODEL_MODE_NOT_VERIFIABLE.

## P0: что добавлено к исследованию 06Z

**НОВОЕ I07-01 — готовая официальная native Beam-команда есть, но не в разрешённом контуре APA.** В AC29 Grasshopper–Archicad Live Connection (официальное руководство GC.pdf, стр.26) компонент **Beam** создаёт нативные Archicad Beam по линиям/полилиниям/кривым 3D; **Beam Settings** допускает Rectangular/Circular/Complex Profile, Building Material, Home Story и другие параметры. При 3D кривой получаются **несколько сегментов**, а не один криволинейный Beam. В PR74 commit 5a3a9201, функция compile_authored_intent, allowlist nativeComponents содержит ровно CreateColumns, CreateDoors, CreateWindows, CreateWalls, CreateRoofs; **CreateBeams отсутствует**. Это не отсутствие функции в Archicad и не доказательство, что Beam может пройти через SceneWriter. Официальный GH Beam — **отдельный готовый writer GH→AC**, допустимый только для отдельно обозначенных GH-owned элементов на изолированной scratch-модели ПОСЛЕ разрешения. Для APA-owned BUILD-01 без изменения кода **BEAM_ROUTE_NOT_FOUND**. Прямая запись GH Beam в те же GUID, что APA SceneWriter, запрещена.

**НОВОЕ I07-02 — одноимённые переключатели имеют противоположные readback-контракты.** Rhino 8 Query Model Objects / Query, Synchronise=False (исправление McNeel 8.1) удерживает frozen copy до expire/ручного Query; это временная ссылка в GH, не durable snapshot. Graphisoft GH Design/Document Synchronize=False (AC29 GC.pdf стр.17, подтверждено №2 06Z) возвращает Null; его нельзя использовать для получения frozen typed output. Эти компоненты не взаимозаменяемы.

**НОВОЕ I07-03 — Rhino Content Cache Action=False не означает «никакого обмена».** Документация разработчика McNeel (17.05.2024, на тот момент Rhino 8.8 RC) прямо говорит: при Action=False действие Push/Bake/Purge не выполняется, **но открытый Result продолжает Pull**. Для прекращения фонового чтения Result следует скрыть. Content Cache Push с входным ID заменяет объект; Bake без ID создаёт новый объект; Purge может удалять также определения слоёв/блоков/материалов. Это Rhino-side контур, не Archicad BIM writer. Точное поведение на установленном Rhino 8 SR не проверено.

**НОВОЕ I07-04 — порт и GH document являются отдельными идентификаторами адресата.** Graphisoft Connection Palette имеет Port Number и Connect Document to Archicad (AC29 GC.pdf, стр.7; источник №1 0655Z). Порт официального соединения не следует молча приравнивать к ожидаемому порту Tapir 19723. Одно Connected не доказывает активный PLN, .gh, .3dm или owner. G0 требует одновременную read-only сверку обоих транспортов и трёх документов.

## Точные источники и лицензии

- Graphisoft: https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/ — официальный AC29 Live Connection **build 3000**, Windows, Rhino 7/8, 01.10.2025. Сам add-on скачивается без отдельной подписки; Archicad и Rhino требуют лицензий. **Установка и фактическая совместимость build5101 НЕ ПРОВЕРЕНЫ.**
- Graphisoft AC29 manual: https://help.graphisoft.com/AC/29/INT/GC.pdf — Beam стр.26, Connection Palette стр.7, Synchronize стр.17, Deconstruct Roof стр.40. Извлечение PDF из web search подтверждает Beam; остальные пункты сверены с архивными SOURCE-карточками №1/№2, не с локальным GUI.
- McNeel Rhino8: https://www.rhino3d.com/features/grasshopper/content-cache/ — штатный Content Cache, без стороннего плагина; Rhino коммерческий, GH встроен.
- McNeel developer 16.11.2023: https://discourse.mcneel.com/t/model-object-component-update-problem/168818/5 — frozen Query Synchronise=False, исправление 8.1.
- McNeel developer guide 17.05.2024: https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1 — Push/Pull/Bake/Purge, ID, Result, Action. **Предупреждение:** первоначально руководство для 8.8 RC; не выдавать за проверенную локальную стабильную сборку.
- Pinned APA PR74 code: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py ; authored plan https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py .

## Без нового writer/router/synchronizer: три независимых контура

| Контур | Источник → получатель | Готовый инструмент | Когда допустим | Что НЕ обеспечивает |
|---|---|---|---|---|
| R (Rhino-owned) | Rhino→GH Query; GH→Rhino Content Cache | Rhino8 Query / Content Cache | SOURCE read-only; будущий Push только отдельно разрешён | Native Wall/Beam/Roof AC GUID |
| G (GH-owned) | GH→AC native Beam/Wall/etc; AC→GH references | Graphisoft Live Connection build3000 | Только изолированный GH-owned scratch, с отдельным допуском | SceneWriter receipt, atomic triad, сохранение GUID после recreate |
| A (APA-owned) | authored JSON→PR74→BIM Graph→SceneWriter/SQLite→Tapir→AC | существующий PR74 | G0/G1/G2 до G3; запись лишь по разрешению | Универсальный Rhino BREP→native BIM, Beam в authored allowlist, full triad |

**Правило владения:** один элемент = один writer. GH-owned нельзя редактировать SceneWriter; APA-owned нельзя писать GH Beam/Property Settings. При UNKNOWN owner — STOP. Rhino Object ID, GH component, AC native GUID, IFC GlobalId, GDL type GUID — разные идентичности.

## G0: воспроизводимое read-only подключение (НЕ выполнено)

1. Считать ожидаемые версии: AC29 build5101, Tapir 1.5.10, Rhino 8 SR=UNKNOWN, Graphisoft add-on build3000=NOT_INSTALLED_VERIFIED; проверить официальные установочные пакеты/лицензии только по документации, не устанавливать.
2. AC: GetProjectInfo (path/name/isUntitled/isTeamwork), story index/floorId/elevation, GetAddOnVersion, фактический порт, command availability/schema, SHA APX/PLN и saved scratch identity. При отсутствии path или неизвестном PLN STOP.
3. Rhino: active document full .3dm path, units, Rhino version/SR, Object ID inventory; GH: active .gh full path/hash, подключённый документ и граф GH outputs.
4. Graphisoft Connection Palette: отдельно проверить **Port Number** и **Connect Document to Archicad**; не путать с Tapir JSON портом. Connected недостаточно: AC projectPath + GH document + Rhino .3dm должны совпасть с разрешённым заданием.
5. Read-only graph audit: GH→Rhino Content Cache (Push/Action/Purge), GH→AC Design Synchronize, AC→GH Sync Changes to GH, APA SceneWriter; на APA-owned не должно быть GH write branches. Никаких переключений/нажатий в данном исследовании.
6. G1: для authored PR74 нужен callable read-only transport и mode=preflight, точный targetProjectPath, bindings, typed schema, material GUID. **mode=offline не годится** для authored schemaVersion. Без G0 — STOP.

## Десять сценариев: выбор→изменение→завершение→синхронизация→QA→Save/Open/откат

| № | Операция / инструменты | Окончание и передача | Проверка ГОТОВО и статус |
|---|---|---|---|
| 01 | Этажи: AC native Stories; PR74 storyBindings | AC read-only story map→authored preflight; GH/Rhino только геометрические отметки | floorId/index/elevation и привязка PLN совпали; Save/Open повторный readback; SOURCE, G0 BLOCKED |
| 02 | Стены: Rhino Query curves→GH параметрика→authored PR74 CreateWalls | Frozen Query для контрольной геометрии; для APA-owned только SceneWriter после approval | AC Wall GUID, этаж, материал, толщина, BREP, hosted elements; нет автоматического GH→authored JSON: NOT_PROVEN |
| 03 | Перекрытия: GH contour→PR74 CreateSlabs | Один rectangular slab/story, абсолютный Z; запись только APA | Native Slab GUID, material GUID и holes, Z, BREP, reopen; arbitrary polygon/holes через authored: NOT_FOUND |
| 04 | Колонны: GH anchors→nativeComponents CreateColumns | typed story/XYZ/outline gate→APA writer | native Column, профиль/материал, story, GUID, BREP; SOURCE |
| 05 | Балки: GH Curve→Beam Settings→AC Beam **или** APA authored | GH-owned direct native Beam — официальный writer; APA-owned CreateBeams отсутствует | GH-owned native Beam после отдельного LIVE/Save/Open — NOT_RUN; APA-owned Beam **NOT_FOUND**; 3D curve segments count проверить |
| 06 | Простая кровля: GH plane→PR74 CreateRoofs | Basic single-plane + pivotLine/material/story; roof contour within outline+0.35m | native Roof, pitch, GUID, SEO, BREP, materials, reopen; SOURCE |
| 07 | Сложная кровля: Rhino NURBS/GH→AC Multi-Plane | Deconstruct Roof только single-plane; PR74 Multi-Plane native create отсутствует | единый native Multi-Plane GUID/roundtrip **NOT_FOUND**, не заменять GDL/IFC/набором single planes |
| 08 | Двери/окна: APA nativeComponents CreateDoors/CreateWindows | hostWall native GUID, library part, размеры; один writer | host relation, opening BREP, GUID, GDL part, story, reopen; SOURCE, library NOT_VERIFIED |
| 09 | Библиотеки/материалы: AC GetLibraries/GetAvailableLibraryParts/GetBuildingMaterials | Только read-only сверка Favorites/part/material GUID; GH Create New Library Part не использовать для APA-owned | отсутствие Missing Objects, skippedCount, materials/part GUID; SOURCE |
| 10 | QA/нормативы: native readback + IFC BREP/parametric + GH geometric checks | После разрешённой записи Save/Close/Reopen + inventory; rollback только snapshot, не GH Undo | GUID/tool/story/host/material/geometry/IFC mapping, floors/clearances/accessible routes; нормативная экспертиза NOT_DONE |

**Общий критерий ГОТОВО для каждого:** SOURCE контракт → фактический OFFLINE/preflight → INSTALLED runtime → разрешённый LIVE на новой scratch PLN → native GUID/tool/material/BREP + Save/Close/Reopen → независимая ACCEPTED. Пропуск любой ступени запрещён. При изменении AC→GH допустим read-only reference update, но **AC→Rhino .3dm write отсутствует без отдельного Content Cache Push**. При одновременных изменениях AC и Rhino — конфликт/STOP, а не last-write-wins. Удаления и recreate: baseline GUID diff + host/SEO check, неизвестный исход STOP. Откат только восстановлением заранее сохранённых файлов и повторной сверкой, не atomic rollback.

## Приоритетное инженерное решение

**P0-BEAM-OWNER-07:** официальная GH Beam устраняет отсутствие native Beam в *продукте*, но НЕ закрывает пробел в allowlist PR74. Не расширять код. До разрешения нового GH-owned write-контра и доказанной приёмки балки оставить **NOT_FOUND для APA-owned BUILD-01**. P0-QUERY-07: использовать frozen Rhino Query только как временную read-only reference; для воспроизводимости обязательно сохранять .3dm+.gh с SHA. P0-CACHE-07: скрытый Result/Pull и Action/Purge учитывать отдельно; не объявлять False глобальной остановкой обмена.

**Контрааудиты:** см. companion audits. **Ворота:** G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. Новые OFFLINE=0, BUILD=0, INSTALLED=NOT_VERIFIED, LIVE=0, ACCEPTED=0. Full three-way native BIM sync = **NOT_FOUND**.
