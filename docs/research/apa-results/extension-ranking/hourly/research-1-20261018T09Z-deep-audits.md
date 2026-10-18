# APA AC29 — глубокий цикл №1: численный PDF-анализ и два независимых аудита

**Дополнение к [30 проверкам](research-1-20261018T09Z-deep-01.md).** Отдельный файл создан потому, что GitHub update_file для существующего отчёта трижды блокировался до исполнения; основной отчёт не перезаписывался. 30 source checks и два аудита составляют один исследовательский цикл.

## Оригинальный PDF, новая численная проверка

Пользовательский файл `3_этап_КП_КОМФОРТ_без_замазок.pdf`, 24 страницы, SHA256 `75b3064dec93245a986e5060540651acfa5d6a87fd1a137d5b46eb591a7462e1`. Визуально и векторно прочитаны стр.12 (КР-10, 14280 мм по оси) и стр.14 (КР-12, блок 1.7, общий размер 14380 мм, световые ширины окон 1600/800 мм). Применён PyMuPDF `get_drawings()` и `get_text('words')`, без OCR.

Найдено **34 подписанных сегмента**, **35 засечек сегментированной цепи** и отдельная левая засечка общей линии. Размеры, мм: `413,412,50,550,550,550,50,600,600,600,460,468,467,50,425,425,50,335,518,517,50,1650,50,520,315,205,600,50,850,50,1050,50,400,425`. Сумма **14355 мм**. Четыре значения «50» находятся на y≈314 pt, тогда как остальные подписи на y≈322 pt: без их учёта возникает ложная невязка 200 мм.

**PDF-засечки:** общая левая x=203.743942 pt; сегментная левая x=205.161270 pt; правая x=1018.985657 pt. Линейная регрессия x по накопленным размерам: **17.639264 мм/pt**, теоретически для М1:50 **17.638889 мм/pt**, отличие +0.00213%; RMS **0.103 мм**, максимум |ошибки| **0.268 мм**. Векторная общая длина **14380.264 мм**. Эти остатки характеризуют согласование подписей и векторных засечек, **не строительные допуски**.

| Рама | PDF x, pt | От сегментного нуля, мм | От общей левой засечки, мм |
|---|---:|---:|---:|
| Окно 1, левый край | 254.786453 | 875 | 900 |
| Окно 1, правый край | 351.163361 | 2575 | 2600 |
| Окно 2, левый край | 535.115601 | 5820 | 5845 |
| Окно 2, правый край | 586.139404 | 6720 | 6745 |

Typed-квитанция [КР-12](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ap2-massops-preflight-20261018/docs/research/apa-results/bdd-house/KR12_NORTH_TWO_WINDOWS_TYPED_SOURCE_20261016.json) использует сегментные центры **1725/6270 мм** и вычитает 50 мм, получая native X **1675/6220 мм**. От общего нуля центры **1750/6295 мм**, после такого же вычитания **1700/6245 мм**. Выявлена **25-мм неоднозначность нуля**, но не доказана ошибка уже размещённых окон: ось native wall необходимо независимо совместить с PDF-датумом. Никаких исправлений PLN не выполнялось.

## Собственный аудит №1: первоисточники, статусы, лицензии

1. **Tapir 1.5.10:** публичный GitHub ref=1.5.10 для группового исходника вернул 404. Источник 1.5.9 подтверждён, но точное соответствие локальной установленной 1.5.10 — **NOT_VERIFIED**. Отсутствие тега не означает отсутствие бинарника.
2. **PR159:** начальный PR body — SOURCE_ONLY. Поздний комментарий [LIVE verification update](https://github.com/dvikt33-ux/safe-bim-layer/pull/159#issuecomment-6244465302) говорит о native LIVE после read-only reconciliation и отдельного resume: 44 GUID, scratch PLN, SaveProject. Следовательно, **staged native chain PASS**, но не единый непрерывный SceneWriter integration PASS.
3. **PR162:** `route()` требует `groupReadbackVerified`, `ungroupedReadbackVerified`, `nativeReadbackVerified` как входные флаги; сам selector не читает Archicad. `prepare_current_runtime_group_native_task` проверяет identity/registration, но не заменяет independent membership readback.
4. **Tapir ошибки:** `CreateGroups`, `MoveElements`, `CreateHotlinkInstances` выполняют циклы и собирают per-item errors; `ACAPI_CallUndoableCommand` callback может завершиться `NoError` при отдельных неудачах. Общий транспортный PASS не доказывает атомарность.
5. **Лицензии:** Tapir, pdfplumber, ezdxf, Raster2Seq **код** — MIT в официальных LICENSE; права на PDF и веса Raster2Seq отдельно. Windows 11/8GB VRAM для Raster2Seq не измерены.

## Собственный аудит №2: инженерная полезность и стоимость

1. **Критическая поправка скорости:** [MoveElements](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp#L3569-L3622) использует N `ACAPI_Element_Edit` внутри одного JSON вызова; `RotateElements` тоже N edits; [CreateHotlinkInstances](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp#L2434-L2519) — N `ACAPI_Element_Create`. Формула: `T(N)=T_transport+ΣT_native_i+T_readback`; **100x НЕ доказан**.
2. **Повторное использование:** APA уже имеет `CloneNativeGroupV1`, group-first selector и SceneWriter. Новый writer дублировал бы существующий путь. Программный `RotateElements(copy=true)` уже существует, но не равен GUI Multiply для всей группы.
3. **Hotlink:** node reuse по совпадению пути не доказывает неизменность SHA модуля; floorDifference/layerIndex/flags могут наследоваться от tool defaults. Для воспроизводимости нужны явные значения, pinned source и проверка child GUID.
4. **PDF:** систематическая неоднозначность 25 мм может распространяться на все окна/двери при массовой записи. До создания нужно доказать `overall datum → segmented datum → native host axis`, host GUID, handedness и реальные границы проёма.
5. **Безопасность:** не делать auto retry после неоднозначного native ответа; требовать inventory GUID, parent/child, BREP, сохранение исходного SHA и SceneWriter ledger. SOURCE/офлайн PDF QA не разрешают модельную запись.

## Рейтинг пригодности (экспертный, не benchmark)

| Кандидат | 0–100 | Трудоёмкость | Граница |
|---|---:|---|---|
| APA CloneNativeGroupV1/PR162 | 95 | БЫСТРО | Native staged PR159, интегрированный LIVE не проверен |
| PDFVectors + векторная сверка | 94 | БЫСТРО | PDF QA PASS, 25-мм origin unresolved |
| Tapir grouping/readback | 92 | БЫСТРО | SOURCE; installed 1.5.10 NOT_VERIFIED |
| Tapir MoveElements(copy=true) | 90 | БЫСТРО | N SDK edits, ответ без GUID |
| Tapir RotateElements(copy=true) | 87 | БЫСТРО | Поэлементный rotate-copy, не full Multiply |
| Tapir Hotlink | 85 | С АДАПТАЦИЕЙ | Tool defaults, external file, N SDK create |
| ezdxf | 78 | С АДАПТАЦИЕЙ | BLOCK/INSERT units explicit; нет DXF |
| Raster2Seq | 43 | ДОЛГО | Linux source; Windows/8GB NOT_VERIFIED |

**Ворота цикла:** SOURCE=PASS для перечисленных файлов; OFFLINE=**PDF_VECTOR_QA_PASS**, OFFLINE_APA=NOT_RUN; BUILD=NOT_RUN; INSTALLED_1.5.10=NOT_VERIFIED; LIVE_THIS_CYCLE=NOT_RUN; ACCEPTED=NO. Нативных записей 0. main/PLN/APX/production code не менялись.

**Следующие вопросы:** (1) сколько SDK edits внутри `CloneNativeGroupV1`; (2) есть ли `RotateElements` в локальном 1.5.10; (3) какой PDF datum совпадает с native wall axis; (4) каков immutable receipt PR159; (5) можно ли безопасно pin hotlink source SHA и defaults; (6) как PR160 запрещает hosted opening copy в PR162; (7) как читать вложенные группы рекурсивно.
