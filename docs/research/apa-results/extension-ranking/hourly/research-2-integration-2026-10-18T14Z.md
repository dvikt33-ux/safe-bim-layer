# APA AC29 — исследователь №2: монтаж готовых решений, 2026-10-18, 14:00 UTC

## Статус и происхождение
Публикационная редакция технического отчёта, сохранённого локально после предыдущего сбоя GitHub. Исходный текст содержал 27 последовательных технических проверок и два контрааудита. Ниже приведены все 27 проверок и ключевые ссылки; локальная версия содержит расширенные замечания и полные сведения о первоначальных ошибках публикации.

Статус: SOURCE (исходники и документация); новые OFFLINE, BUILD, INSTALLED, LIVE, ACCEPTED — НЕ ПРОВОДИЛИСЬ. MODEL_MODE_NOT_VERIFIABLE. Использован подключённый GitHub; Opera в исходном цикле была недоступна. Archicad, PLN, APX, main, рабочий код, план revision 182 не изменены.

Источники APA: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_readonly.py
https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/archicad_connected_ifc.py
Upstream pin: https://github.com/IfcOpenShell/IfcOpenShell/tree/b139fe1c355d6e29f36f430ad4e26f8910bc5958
Реестр: docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md, priority_matrix_20261018.json, candidates.json (61 кандидат). Канонический PROJECT_PLAN.json revision 182 только чтение. Сопоставлены PR104, PR154, PR160, PR162.

## 27 реальных технических проверок исходного цикла

| № | Проверенный контракт, ограничение | Вывод / следующая проверка |
|---|---|---|
| 01 | APA VERSIONS: ifcopenshell=0.8.5, pdfplumber=0.11.10, ezdxf=1.4.5 | Значение в коде не доказывает установленную версию: runtime doctor |
| 02 | invoke_module: whitelist ifcclash/ifcdiff/ifctester, timeout=1200, результат JSON до 200 MiB | Переиспользовать существующую изоляцию CLI, не создавать Router |
| 03 | inspect_quantified_exchange(path,native,native_ifc_map) | Существует Qto и связь IFC GlobalId с native GUID: reuse |
| 04 | IfcPatch execute(recipe,file,input,arguments), write(output,path) | Готов Python wrapper; нужен version pin |
| 05 | Patcher(file,logger,*args) и Patcher(src,file,logger,*args) встречаются в разных ревизиях | Несовместимость сигнатур: нельзя переносить latest на 0.8.5 |
| 06 | CLI IfcPatch: -i, -r обязательны, -o необязателен, output=input без -o | Риск перезаписи исходного IFC, требовать отдельный output |
| 07 | ExtractElements(query='IfcWall', assume_asset_uniqueness_by_name=False) | Работает запрос выбора; нужны реальные GUID/relations |
| 08 | ExtractElements: by_guid, append_asset, create_spatial_tree | Наличие ссылок не доказывает целостность всех отношений |
| 09 | SplitByBuildingStorey(output_dir): имена i-{storey.Name}.ifc | Готовая схема поэтажного экспорта IFC, не нативных этажей |
| 10 | is_in_storey сравнивает ContainedInStructure[0].RelatingStructure.GlobalId | Проверить многoэтажные элементы и потери GUID |
| 11 | Raw storey.Name используется в имени файла | Windows invalid chars / traversal: sandbox и preflight |
| 12 | ifcopenshell.util.geolocation.auto_xyz2enh(ifc_file,x,y,z) | Учитывать единицы IFC и три контрольных георепера |
| 13 | SetFalseOrigin: name,x,y,z,e,n,h,gn_angle,rotate_angle,reset_spatial_elements | Не менять геопривязку без отдельного разрешения |
| 14 | Migrate(schema='IFC4'): IFC4→IFC2X3 может терять семантику | Native translator предпочтительнее; нужен loss report |
| 15 | ConvertPropertiesToQuantities(property_name,quantity_name); if value | Нулевые значения могут пропускаться: zero fixture |
| 16 | IfcDiff: -o diff.json -r 'type property container aggregate classification' | Default attributes/geometry не эквивалентен этому набору |
| 17 | IfcDiff зависит от ifcopenshell,numpy,deepdiff,orderly_set | Check imports прежде оценки готовности |
| 18 | IfcTester: ids ifc -r Json -o report.json | Existing external provider: reuse, IDS applicability gate |
| 19 | IfcClash: clashsets.json -o report.json, APA tolerance=0.001 | Единицы измерения обязательны; допуск не универсален |
| 20 | BCF-XML: from bcf.bcfxml import load; 2.1/3.0, bcf-client отдельно | Offline ZIP предпочтительнее сетевого BCF API |
| 21 | BCF ZIP содержит bcf.version, выбираются v2/v3, иначе ValueError | Version gate, BCF roundtrip |
| 22 | BcfXml.create_new, add_topic, save, load есть в upstream tests | Библиотека готова, адаптер APA viewpoint/GUID не найден |
| 23 | Лицензии upstream IfcPatch, IfcDiff, IfcTester, BCF: LGPL-3.0-or-later | Проверить каждый package/distribution и зависимости |
| 24 | pdfplumber 0.11.10: pdfminer.six==20260107, Pillow>=12.2.0, pypdfium2>=5.9.0, MIT | Reuse PR154, локальное Windows окружение не проверено |
| 25 | ezdxf 1.4.5: Python>=3.10, numpy,fonttools,pyparsing,typing_extensions, MIT | DXF parser не BIM semantic engine |
| 26 | APA check_environment проверяет метаданные и Python 3.11/3.12, но не ifcpatch/bcf imports | Нужен отдельный import gate |
| 27 | IfcPatch IFCPATCH_RECIPE_DIR разрешает дополнительные recipes | Только whitelist, controlled env, safe output path |

## Матрица внедрения
Экспертные баллы 0–100 — полезность, не измеренное ускорение. Для всех новых цепочек SOURCE ONLY.

| Решение | Балл | Путь и APA reuse | Сложность / критический gate |
|---|---:|---|---|
| ExtractElements | 86 | APA IFC export → IfcPatch Python recipe → subset IFC; existing IFC reader and GlobalId map | АДАПТАЦИЯ; GUID/spatial/host relationships |
| IfcTester | 83 | existing external provider → ifctester CLI → JSON | БЫСТРО; IDS positive/negative, minOccurs |
| BCF-XML | 79 | existing BIM Graph → bcf.bcfxml → BCF ZIP | АДАПТАЦИЯ; camera/viewpoint/GlobalId roundtrip |
| SplitByBuildingStorey | 74 | APA IFC → IfcPatch recipe → storey IFC, compare via existing graph | АДАПТАЦИЯ; all GUID, multi-storey, Windows-safe names |
| Geolocation READ | 61 | APA IFC → auto_xyz2enh, no project edits | АДАПТАЦИЯ; units/CRS/three control points |
| ConvertPropertiesToQuantities | 55 | APA IFC → IfcPatch recipe → QA via existing Qto reader | АДАПТАЦИЯ; zero values and units |
| Geometry iterator | 51 | existing IfcOpenShell → geometry iterator → QA | АДАПТАЦИЯ/DEFER; RAM baseline and shape equality |
| Migrate | 48 | APA IFC → IfcPatch schema migration → independent IFC | ДОЛГО/DEFER; schema/GUID/geometry loss |
| IfcQuery | 39 | existing IFC access → upstream query utility → results | АДАПТАЦИЯ/DEFER; avoid BIM Graph duplication |

## Альтернативы и выбор
ExtractElements и SplitByStorey: путь A — штатный IFC export filter AC29 без нового пакета; путь B — IFC → готовая IfcPatch recipe (одно внешнее звено). Выбрать A при доказанном покрытии, B только для отсутствующей функции и на копии. BCF: A — локальный BCF XML ZIP с одной библиотекой; B — BCF-API с сервером и авторизацией. Выбор A. Qto: сначала штатная схема маппинга, затем постобработка лишь при доказанной необходимости. Готовый APA-specific адаптер с sandbox, output whitelist, version pin и GUID reconciliation пока NOT_FOUND; разрабатывать собственный IFC/Router/SceneWriter не требуется.

## Контрааудит A: доказательства, версии и лицензии
Upstream commit b139 — commit, не тег установленного 0.8.5. Сигнатуры Patcher различаются; CLI без -o рискован; split использует имя этажа без доказанной санации; zero Qto требуется проверить. LGPL-3+ исходника и MIT pdfplumber/ezdxf не доказывают лицензии бинарных зависимостей. Docker/build Windows и локальные imports не проверялись. Ни один SOURCE не повышен до INSTALLED/LIVE.

## Контрааудит B: монтаж, дублирование, инженерные риски
Не создавать новые Router, SceneWriter, BIM Graph, Qto engine. Postprocess IFC не ускоряет Archicad PLN операции; 100x не доказано. IFC GlobalId и native Archicad GUID — разные идентификаторы. Split может терять multi-storey элементы; BCF требует компонентных ссылок и камеры; MapConversion не исправляет ошибки PDF геометрии. Следующий безопасный приоритет: existing IfcTester → ExtractElements → SplitByStorey → BCF XML.

## Ворота подключения
SOURCE: pinned API, source, license. OFFLINE: отдельный IFC, SHA/units/GlobalId manifest, positive/negative fixtures, controlled output dir. BUILD: import/CLI check только после разрешения. INSTALLED: actual wheel/version/hash. LIVE: изолированный сохранённый проект и отдельное разрешение; rollback/readback. ACCEPTED: independent engineering acceptance. Сейчас только SOURCE.

## Передача координатору №3
Кандидаты на рассмотрение: IfcTester 83, ExtractElements 86, SplitByBuildingStorey 74, BCF-XML 79, geolocation READ 61. Не утверждать подключение без gate.

Вопросы №1: (1) какие штатные IFC filters AC29 заменяют ExtractElements/SplitByStorey? (2) где эталонная nativeGuid→GlobalId карта? (3) есть ли готовый BCF viewpoint converter? (4) где три проверенных геодезических репера? (5) какие Qto поля действительно требуют patch?

Источники: 
- https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcpatch/ifcpatch/__init__.py
- https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcpatch/ifcpatch/__main__.py
- https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcpatch/ifcpatch/recipes/ExtractElements.py
- https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcpatch/ifcpatch/recipes/SplitByBuildingStorey.py
- https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/bcf/bcf/bcfxml.py
- https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/bcf/tests/v3/test_bcf_xml.py
