# APA №1 — research-1-20261023T1559Z-TRIAD-AC29-QA — 28 проверенных технических утверждений
Дата: 2026-10-23; направление P0: AC29 + Rhino8 + GH. SOURCE_ONLY, без OFFLINE/INSTALLED/LIVE.
**Метод:** 28 различных технических пунктов, НЕ 28 независимых документов. Проверены публичные страницы Graphisoft для AC29, версия скачивания AC29 и текстовая выдержка GC.pdf; полный постраничный PDF-аудит не выполнялся. Никаких проверок локальной Windows-среды.

S01 [SOURCE] AC29 Grasshopper Live Connection build 3000 имеет Windows-дистрибутив и заявляет Rhino 7/8; локальная установка НЕ подтверждена.
Первоисточник: https://www.graphisoft.com/it-it/downloads/add-ons/rhino-grasshopper/

S02 [SOURCE] Параметр Synchronize есть у генерирующих AC элементов GH; TRUE автоматически отправляет изменения GH→AC при активной связи.
Первоисточник: https://help.graphisoft.com/AC/29/INT/GC.pdf

S03 [SOURCE] Synchronize FALSE не выполняет генерацию и возвращает Null; НЕ считать это доказательством безопасного отката уже созданных элементов.
Первоисточник: https://help.graphisoft.com/AC/29/INT/GC.pdf

S04 [SOURCE] Archicad 29 принимает Rhino .3dm как Hotlink Module; это отдельный маршрут от GH native writer.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm

S05 [SOURCE] Hotlink Source со статусом Modified требует Update для обновления размещённых экземпляров; мгновенная синхронизация не подтверждена.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm

S06 [SOURCE] Hotlink Manager хранит даты Modified и Last updated, позволяя выявить устаревший источник.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm

S07 [SOURCE] Relink может очистить очередь Undo; автоматический откат без резервной копии не гарантирован.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm

S08 [SOURCE] Open/Merge .3dm создаёт не редактируемую нативную стену, а GDL Object; использовать только для геометрической подложки.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm

S09 [SOURCE] Импортированные объекты .gsm размещаются в Embedded Library, по файлам и слоям.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm

S10 [SOURCE] Rhino Original Layer и Original ID сохраняются как свойства импортированного объекта Archicad; это НЕ native Archicad GUID.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm

S11 [SOURCE] Увеличение сегментации криволинейной поверхности повышает количество полигонов и нагрузку.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm

S12 [SOURCE] Model Compare AC29 классифицирует изменения 3D как new/modified/deleted; 2D элементы исключены.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm

S13 [SOURCE] Model Compare может сопоставить текущую модель с ранее сохранённой версией.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-3.htm

S14 [SOURCE] После Hotlink Update штатный флажок Compare Models показывает различия до/после.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-5.htm

S15 [SOURCE] Результат сравнения привязан к временным снимкам; после новых изменений требуется новый Compare.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm

S16 [SOURCE] Collision Detection AC29 сравнивает два набора 3D-элементов, определённых критериями.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-64.htm

S17 [SOURCE] Только видимые слои учитываются в Collision Detection: скрытые конструкции могут быть пропущены.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-64.htm

S18 [SOURCE] При наличии выделения проверяются только выделенные элементы: требуется сброс выбора перед полным QA.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-64.htm

S19 [SOURCE] SEO и priority-based connections уже учтены и не считаются коллизиями; чистый отчёт не доказывает правильность узлов.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-64.htm

S20 [SOURCE] Volume/Surface tolerances задаются в рабочих единицах проекта и меняют перечень найденных конфликтов.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-64.htm

S21 [SOURCE] Physical Model Quality Check встроен в AC29 и проверяет аномалии физических конструктивных элементов.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-2.htm

S22 [SOURCE] Lack of Core connection выявляет стены/перекрытия с пересечением отделки, но без соединения несущих сердечников.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-3.htm

S23 [SOURCE] Another Load-Bearing Element closer than обнаруживает малые зазоры несущих элементов, не пересекающихся геометрически.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-3.htm

S24 [SOURCE] Import IDS AC29 создаёт классификации/свойства из файла buildingSMART IDS для IFC mapping.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-17.htm

S25 [SOURCE] Уже существующие классификации/свойства при IDS Import не модифицируются автоматически.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-17.htm

S26 [SOURCE] IDS Import может частично извлечь данные при ошибках файла; сам по себе НЕ валидирует соблюдение СП и полноту значений.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-17.htm

S27 [SOURCE] Solibri Inside (Design Checker) прекращён к AC29; нельзя рекомендовать как доступную штатную бесплатную проверку.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/005_NewFeatures/005_NewFeatures-27.htm

S28 [SOURCE] Расчётные функции MEP Designer требуют cloud license; исключить из обязательного бесплатного BUILD-01 QA.
Первоисточник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-41.htm

## Проверка контекста GitHub
Прочитаны docs/research/apa-results/extension-ranking/hourly/../NEXT_RESEARCH_PRIORITIES.md, docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md и №1 14:57Z CARDS/INDEX. PR74 и BUILD-01 #192 прочитаны через GitHub поиск. Свежие отчёты №2/№3 и матрица 61 напрямую НЕ установлены и НЕ заявляются прочитанными. Исторический PROJECT_PLAN rev182 не менялся.

## Строгая граница
Все пункты SOURCE. Никакой native GUID preservation, полной AC↔GH↔Rhino двусторонней синхронизации, нормативной экспертизы или Save/Open приёмки на новой модели не доказано.
MODEL_MODE_NOT_VERIFIABLE.
