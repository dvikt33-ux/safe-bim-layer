# APA Archicad 29: семантические расширения V1 (18.10.2026)

Рабочая ветка: feature/apa-semantic-ready-tools-20261018, draft PR #156.
Существующие 6 расширений сохраняются без изменений.

## Готовые команды через оригинальный DynamicCommands

| Команда | Назначение | Библиотека | Условия |
|---|---|---|---|
| AddOn.APASemantic.PDFPaths | PDF векторные пути, сохранённые группы, слои, графические кластеры | PyMuPDF 1.26.4 | Выполняется при установленном sidecar |
| AddOn.APASemantic.PDFPageRaster | Одна страница PDF -> PNG с коэффициентом координат | PyMuPDF 1.26.4 | Выполняется при установленном sidecar |
| AddOn.APASemantic.OpenBIMSegments | Стены, окна и двери в пикселях | OpenBIM FloorPlan AI | Отдельная ML-среда и доверенные веса обязательны |
| AddOn.APASemantic.RasterFloorplan | Помещения, оси стен, проёмы и связанные вершины | floorplan-back / Raster2Seq | Отдельная ML-среда и доверенные веса обязательны |

Графический кластер PyMuPDF не является семантической стеной.
Координаты нейросетей — пиксели исходного изображения, не метры.
Автоматической записи в Archicad, IFC и PLN эти команды не делают.

## Как подключить к установленному APA

1. Получить исходники ветки PR #156 в отдельный checkout (не изменять main).
2. В Windows из Python 3.11/3.12 старого vendor-v1 вызвать:
   python scripts/install_apa_semantic_bridge.py
   Это только проверка. Затем единожды:
   python scripts/install_apa_semantic_bridge.py --install
3. Инсталлятор создаёт только C:\LocalAI\APA_AC29_Stable\external-tools\apa-semantic-v1, ставит PyMuPDF в отдельный venv, записывает контрольные SHA и вызывает --probe к исходному APA Router через уже работавший vendor-v1 Python.
4. Для запуска APA Router использовать уже проверенный старый интерпретатор:
   C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\venv\Scripts\python.exe
   совместно с:
   C:\LocalAI\APA_AC29_Stable\external-tools\apa-semantic-v1\apa_semantic_entrypoint.py

Реальные команды:
- --probe
- --command PDFPaths --a PDF_PATH --page 1 --output NEW_PATHS.json
- --command PDFPageRaster --a PDF_PATH --page 1 --output NEW_RASTER.json

Второй результат создаёт NEW_RASTER.png в той же папке. Это проверенный путь подготовки изображений для модели, без копирования всех графических линий в элементы здания.

## Модели (отдельный этап)

Для OpenBIM использовать оригинальный inference_api.py из Chunling1/OpenBIM-FloorPlan-AI и модель M2_DA_FT_v2_best.pt. Для Raster2Seq оригинальный scripts/parse_floorplan.py из Takheer/floorplan-back и checkpoint по пути models/raster2seq/cubicasa5k/checkpoint.pth.

Модельная конфигурация создаётся исключительно через configure_apa_semantic_models.py с аргументами:
--vendor openbim|raster2seq --python PYTHON_EXE --root UPSTREAM_REPO --model WEIGHTS --trust-checkpoint

Без моделей команды OpenBIM и RasterFloorplan отказывают. Веса не скачиваются автоматически. Реализации upstream используют torch.load(weights_only=False): модель из неизвестного источника может исполнять код. Доверие к источнику должен подтвердить владелец.

Оба инструмента принимают PNG/JPG; PNG из PDFPageRaster можно подать напрямую.
Включения в имеющиеся постоянно запущенные APA-сессии нет: нужно создать новую сессию через semantic entrypoint.

## Статусы, которые нельзя смешивать

- ROUTER_SOURCE_CONNECTED: создан исходный интеграционный код и 4 reviewed команды.
- PYMUPDF_VENDOR_CI_PASS: реальное выполнение на Windows с Python 3.11 и 3.12.
- LOCAL_APA_INSTALLED: только после выполнения install на Windows пользователя.
- OPENBIM_MODEL_LIVE_PASS: только после отдельного реального запуска с доверенными весами.
- RASTER2SEQ_MODEL_LIVE_PASS: только после отдельного реального запуска с доверенными весами.
- BIM_SEMANTIC_ACCEPTANCE: ещё не проверено.

Следующая задача: реальные сравнения на одной странице BDD, затем довести до подключения остальные исследованные IFC/DXF/CAD-инструменты.


## Реальная независимая проверка BDD PDF (локальный контейнер исследования)

Источник: 3_этап_КП_КОМФОРТ_без_замазок(1).pdf
SHA-256: 75b3064dec93245a986e5060540651acfa5d6a87fd1a137d5b46eb591a7462e1
Библиотека: PyMuPDF 1.26.7 в контейнере исследования (НЕ Windows APA 1.26.4).

| Страница | get_cdrawings(extended=True) | get_drawings() | cluster_drawings() |
|---|---:|---:|---:|
| 1 | 18 | 9 | 1 |
| 19 | 22 352 | 22 134 | 1 |

PDF содержит 24 страницы; doc.get_ocgs() вернул пустой словарь. На странице 19 единственный кластер охватывает почти весь лист: это НЕ восстановление отдельных стен, а нерелевантная для BIM крупная визуальная группа. Поэтому команда маркирует такие случаи PAGE_WIDE_CLUSTER_NOT_SEMANTIC и не конвертирует их в BIM.

Отдельно: цифры исходного pdfplumber не сопоставимы 1:1 с PyMuPDF, потому что первый считает элементарные линии/кривые, а второй группы инструкций PDF. Сокращение 53 тысяч примитивов до 22 тысяч путей само по себе не доказательство распознавания строительных элементов.
