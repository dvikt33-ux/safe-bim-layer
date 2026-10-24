# APA №1 — готовые средства предотвращения потерь при AC29 + Rhino8 + Grasshopper
Дата: 2026-10-23, 19:37 UTC. Статус: SOURCE_ONLY. Ответ на запрос руководителя «Какие решения этих проблем есть?». Связано с BUILD-01 issue #192. Никакого нативного запуска или записи в PLN/APX.
 
## Вывод для BUILD-01
Предлагаемый минимальный безопасный маршрут на основе готовых средств: Rhino 8 Content Cache (отслеживаемые объекты) -> Grasshopper (параметрические зависимости, управляемый Boolean Toggle) -> Graphisoft Grasshopper-Archicad Live Connection AC29 (поддерживаемые нативные BIM-типы), при этом SceneWriter и GH не должны изменять один элемент в одной операции. Затем независимые readback/Model Compare/Save/Open. ПОЛНАЯ синхронизация произвольных изменений AC↔Rhino↔GH НЕ доказана. G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. Новых PASS нет.

## Решения: факт -> ограничение -> поручение №2
1. Незапланированная GH-запись: Graphisoft Synchronize Boolean Toggle; синхронизация только при TRUE и активном соединении; при FALSE компонент не создаёт новый элемент и возвращает Null. Это пауза, не команда удаления. Передать №2 тест на копии PLN: выключение, изменение параметра, отсутствие записи, включение и readback.
   Источник https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564 ; AC29 guide https://help.graphisoft.com/AC/29/INT/GC.pdf.
2. Дублирование геометрии Rhino: встроенный Content Cache, Push/Pull; Push отслеживает объекты и заменяет вместо дублирования, Bake без отслеживания может дублировать, Purge удаляет; не применять Purge к рабочим общим объектам. Не доказывает сохранность Archicad GUID.
   Источник https://discourse.mcneel.com/t/content-cache-updated-guide/181883 .
3. Перезапись Archicad изменений: вводим per-element ownership policy: GH управляет GH-созданными параметрами, SceneWriter — APA-созданными; в конфликте НЕ синхронизировать, передача владельца только как отдельная контролируемая операция. Это архитектурное ограничение APA, не готовый универсальный автоматический арбитр. Источник https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680 .
4. Обратное AC -> GH чтение: Send Changes для параметров связанных элементов; не означает обратную нативную запись всех Roof/Window/GDL типов. №2: разделить таблицы READ/WRITE и составить маршрут контрольной кровли. Источник https://help.graphisoft.com/AC/29/INT/GC.pdf .
5. Потеря GUID и SEO: не удалять и пересоздавать элемент при изменении, сравнивать GUID и связи до/после. Teamwork reservation: созданные GH элементы зарезервированы и должны оставаться доступными автору обновлений; иначе возможны дубликаты. Источник https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680 .
6. GH созданные библиотечные детали: удаление Object Settings, создававшего Library Part, удаляет деталь из Embedded Library и вызывает Missing Objects. Для производственных общих библиотек предпочтительны существующие устойчивые library parts; до изменения GH-компонентов сохранить архив PLN/PLA и проверить Library Manager на Missing Library Parts. PLA гарантирует включение имеющихся размещённых деталей при сохранении, но НЕ восстановит отсутствовавшие до архивирования. Источники https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-54.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-30.htm .
7. Частые пересчеты: централизованный Boolean Toggle по группе AC writing компонентов, перед изменением исходных параметров FALSE; Rhino8 Grasshopper Solver Disable/Enable доступен из команды Grasshopper; Solver disable сам по себе не служит межпрограммной блокировкой записи. Источники https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564 ; https://docs.mcneel.com/rhino/8mac/help/en-us/commands/grasshopper.htm .
8. Проверка/возврат: Rhino8 Check и SaveACopy / IncrementalSave; Archicad29 Model Compare (3D added/modified/deleted), Library Manager, снимок PLN/PLA. Model Compare не является полным доказательством GUID, BREP, СП или целостности невидимых данных. Источники https://docs.mcneel.com/rhino/8/help/en-us/commands/check.htm ; https://docs.mcneel.com/rhino/8/help/en-us/commands/save.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm .

## Минимальный протокол операции
1. Preflight: один правильный проект, документ Rhino, GH definition, версии; защищённая копия PLN/PLA+3DM+GH; снимок GUID/этаж/слой/тип/свойства/связи.
2. Выбор маршрута: стандартные BIM типы через существующий SceneWriter или Graphisoft Live Connection; сложную геометрию в Rhino/GH, но не подменять Roof/Wall немаркированным Morph.
3. Изолировать владельца: GH Synchronize FALSE для всех не изменяемых веток; у APA нет права записи в те же GUID в текущей операции.
4. Изменение в назначенной программе; Rhino Check/границы, GH валидация единиц и зависимостей.
5. После окончания расчета разрешить конкретную синхронизацию только затронутой ветки.
6. Readback в Archicad: count, GUID, тип, этаж, атрибуты, окна/двери, BREP/сопряжения; Model Compare + Library Manager Missing Parts. При ошибке STOP, без автоповтора CREATE и без произвольной автозамены.
7. Save/Open на изолированной копии выполняет только отдельный разрешённый инженерный исполнитель, сравнение после открытия. При расхождении откат к проверенной копии.
8. Следующий шаг №2: составить операции 1) простая кровля 2) многоскатная кровля 3) Slab/Opening 4) окно/дверь 5) конфликт GH/APA с запретом обоих писателей и критерием PASS.

## Два контрааудита
A. Первичный источник/версия: официальные средства действительно документированы; часть Teamwork-предупреждений историческая и не доказывает ошибку именно AC29 build 5101. Положение Content Cache подтверждено McNeel, но не является средствами AC29. Локальная установка и точные версии не проверены.
B. Применимость/недублирование: для каждого риска предлагаются существующие программы/компоненты; не предлагаются новые writer/router, платные сервисы или переустановка. Главное НЕЗАКРЫТО: универсальное автоматическое распределение владения, конфликты двух писателей, транзакционный rollback между тремя приложениями и многоскатный Roof roundtrip.

MODEL_MODE_NOT_VERIFIABLE. Ничего не установлено и не запускалось LIVE, main/код/PLN/APX/PR не изменены.
