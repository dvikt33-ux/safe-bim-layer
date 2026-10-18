# APA 29 — пакетная интеграция: максимальное число полезных функций при минимуме зависимостей

Дата: 2026-10-18. Статус: **отбор и технический план, НЕ установка и НЕ LIVE**. Источник: точные исходники PR #154 (feature/apa-external-pdf-lossless-20261018), исследование №2 16Z и матрица 61 кандидата. Никакого объявления новых команд INSTALLED/ACCEPTED без квитанций.

## Фактическая исходная база

- В `scripts/apa_external_readonly.py` PR #154 уже реализованы **6** обработчиков: `ifc-diff`, `ifc-clash`, `ids-validate`, `ifc-qto`, `pdf-vectors`, `dxf-vectors`. Это SOURCE в открытом draft PR, статус на установленной машине не подтверждён.
- `scripts/apa_external_catalog.py` и `scripts/apa_external_analytics_entrypoint.py` регистрируют те же шесть через существующий `DynamicCommands`, без нового SceneWriter и без нативной записи.
- `scripts/apa_external_session_factory.py` и `scripts/install_apa_external_session_factory.py` содержат инвариант **len == 6**. Обновление только `OPERATIONS` сломает маршрут.
- Манивест `installation.json`, установщик и фабрика сессий используют SHA256 адаптера и каталога. Пакет расширения НЕ должен вносить скрытые изменения в установленный `apa-readonly-v1`; нужен отдельный v2/side-by-side с новым манифестом и явной приёмкой.
- В `scripts/requirements-external-readonly.txt` уже закреплены ifcopenshell/ifcclash/ifcdiff/ifctester 0.8.5, pdfplumber 0.11.10, ezdxf 1.4.5, networkx 3.6.1; метаданные источника НЕ равны подтверждённой установке. Windows+Python 3.11/3.12, основной Python 3.14 не подменять.
- Нативный `CloneNativeGroupV1` в PR #162 уже существует, новый исполнитель групп не создавать; `PublishPublisherSet`/Hotlink проверять по фактически зарегистрированным командам локального Tapir 1.5.10 (upstream 1.5.9/1.7.1 недостаточно).

## Рейтинг НАБОРОВ (не формальный рейтинг библиотек)

| Порядок | Пакет | Новые отдельно вызываемые обработчики, ЦЕЛЬ | Существующие зависимости | Трудность и риск | Решение |
|---|---|---:|---|---|---|
| 0 | Завершить уже реализованный внешний READ_ONLY V1 | **0 новых / 6 ранее написанных** | 10 закреплённых дистрибутивов, исходный Router | малая правка кода; локальный installer/doctor ещё не принят | Первый gate: доказать имеющиеся 6 |
| 1 | IfcOpenShell 0.8.5: независимый контроль IFC | **8 новых** | один уже предусмотренный ifcopenshell | Низкий риск для PLN, адаптация v2 | Главный кандидат по функциональной плотности |
| 2 | ezdxf 1.4.5: детальное чтение DXF | **4 новых** | один уже предусмотренный ezdxf | Низкий риск для PLN; BIM-семантика не возникает сама | Подключать вместе с пакетом 1 |
| 3 | networkx 3.6.1: QA существующего BIM Graph | **4 новых при отсутствии дубликатов** | уже предусмотренный networkx | только после anti-duplication audit с Native Model Dump/BIM Graph | Условный пакет |
| 4 | IfcCSV / IfcConvert / BCF-отчёты IfcTester | **3–5 дополнительных маршрутов** | совместимые версии текущего IfcOpenShell; проверить раздельные дистрибутивы | средний: CSV/ZIP/OBJ не JSON, нужен безопасный файловый выход | Вторая волна |
| 5 | Tapir Hotlink, Publisher и нативные группы | количество НОВЫХ команд зависит от локального discovery | Archicad 29 + реальный локальный Tapir | запись в BIM / файлы, выше риск | Отдельный write-gate, не смешивать с READ_ONLY |
| Не сейчас | MEP-переходы, SAF→PyNite, генерация из растра, GUI Multiply API | **0 подтверждённо готовых к быстрому подключению** | дополнительные лицензии/контракты | высокий | Не считать быстрой массовой интеграцией |

*Цифры 8+4+4 — план количества самостоятельных проверяемых обработчиков, **не установленный функционал**, не 16 реализованных API, не измеренное ускорение.*

### Пакет IFC: 8 новых команд-кандидатов

1. `IFCSchemaInventory`: версия IFC, распределение физических/spatial классов (независимый exported IFC snapshot).
2. `IFCGlobalIdAudit`: пустые и повторяющиеся GlobalId, не путать IFC GlobalId с native Archicad GUID.
3. `IFCSpatialRelations`: `IfcRelAggregates` и `IfcRelContainedInSpatialStructure`, граф зданий/этажей/элементов.
4. `IFCOpeningRelations`: `IfcRelVoidsElement` и `IfcRelFillsElement`, окно/дверь/основание.
5. `IFCPortRelations`: `IfcRelConnectsPorts`, наличие и взаимность MEP связей на экспортированном IFC, НЕ LIVE связность MEP модели.
6. `IFCPropertySetCoverage`: таблица присутствия `IfcRelDefinesByProperties` и имён Pset без интерпретации СП.
7. `IFCClassificationCoverage`: `IfcRelAssociatesClassification` с устойчивым идентификатором.
8. `IFCGeoReferenceAudit`: координатные операции/CRS/единицы; IFC2x3 отсутствие `IfcMapConversion` — допустимый типовой случай, не ошибка само по себе.

### Пакет DXF: 4 новые команды-кандидата

1. `DXFLayerInventory`: слои/признаки видимости/счётчики элементов.
2. `DXFBlockInsertions`: BLOCK/INSERT, точка вставки, rotation/scale/attributes, без выдумывания семантики BIM.
3. `DXFTextAnnotations`: TEXT/MTEXT, положение, исходный Unicode и стиль.
4. `DXFDimensionEntities`: DIMENSION-объекты и исходные геометрические параметры, но **не** автоматически достоверные строительные размеры.

### Пакет графа: условные 4

Кандидаты: компоненты связности, циклы, недостижимые узлы, граф различий; **до создания** сверить с реализованными функциями BIM Graph и Native Model Dump. Если уже есть — считать 0 новых.

## Безопасная последовательность реальной интеграции

1. **V1 baseline:** локальная проверка установленного оригинального isolated sidecar (doctor, hash, provider count=6, read-only ticket и возврат JSON; без повторных тестов уже принятого Native Model Dump).
2. **V2 contract:** отдельная ветка + draft PR, новая таблица `commands→schema→handler→permission→output`; старый V1 не переписывать, разместить отдельным opt-in provider/sidecar, без main/PLN/APX.
3. **OFFLINE:** минимум по одному fixture каждой группы IFC2x3/IFC4, DXF INSERT/MText/DIMENSION; snapshot+readback отчётов, модель и исходники не изменяются, все ошибки fail-closed.
4. **BUILD / INSTALLED:** только после явного разрешения и Windows doctor под Python 3.11/3.12, версия и SHA256 каждого модуля, регистрация без затрагивания живых сессий, результат count=6+доказанные новые.
5. **LIVE / ACCEPTED:** отдельный user-authorized gate для чтения экспортированной IFC/DXF копии в изолированной сессии, сравнение GUID/составов/полноты, а для нативных изменений отдельный readback+сохранённая копия PLN. Не объявлять ACCEPTED по статическому анализу.

## Инженерные критерии «ГОТОВО»

- Каждая **новая** команда получает уникальное имя и валидируемую JSON-схему, точный upstream API/версию, запись происхождения (SHA256 исходников и результата), отсутствие перезаписи.
- Адаптер не обращается к Archicad и не пишет в PLN; `nativeCalls=0`, `modelWrites=0` подтверждаются структурой исполнения.
- Нет запуска shell-команд из входных строк, нет записи вне явно заданной директории, лимиты времени/памяти, whitelist действий, контроль суффикса/размера.
- Число новых команд проверено через реальные зарегистрированные имена и end-to-end execution, НЕ через число строк каталога.
- Вторая волна IfcCSV/IfcConvert/BCF — только отдельным бинарным/CSV выводом, не передавать ZIP/OBJ в существующий JSON-парсер.
- No-op по main/PLN/APX/продуктивному коду до явной приёмки. AC29 сначала, AC30 потом.

## Первоисточники

- https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_readonly.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_catalog.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_session_factory.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/install_apa_external_session_factory.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-18T16Z-matrix.md
- https://docs.ifcopenshell.org/ifcopenshell.html
- https://ezdxf.readthedocs.io/
