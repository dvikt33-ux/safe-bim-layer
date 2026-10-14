# APA — Finch 3D / Archicad 29: возможности, бесплатность и допустимость интеграции

**Дата исследования:** 2026-10-15  
**Класс:** SOURCE_RESEARCH / OFFICIAL_VENDOR_DOCS / NO_INSTALL / NOT_TESTED  
**Приоритет для бесплатного API-встраивания в APA:** **DO_NOT_CONSIDER** в текущих условиях (пересматривать при изменении лицензий).  
**Отдельный потенциал:** **PROMISING_REFERENCE** — идеология Adaptive Plan Library / параметрическая адаптация планировок, как функциональный образец; **не** означает передачу исходников или лицензии.

## Источники с указанием факта

1. [Finch official Get started / pricing](https://www.finch3d.com/get-started) — Free: 0 €, один пользователь, редактор и real-time performance metrics; Basic: 79 €/мес. с 14-дневной пробной версией, optimized unit mix and circulation; Enterprise: от 14 500 €/год (3 seats), AI-powered floor plan generation, compliance checking, custom BIM export and integrations, AI agent.
2. [Finch download plug-ins — Archicad Beta](https://docs.finch3d.com/docs/download-plug-ins) — официальный Windows/Mac плагин Archicad 27/28/29; установка в Add-Ons, начало работы на активном плане. Это **совместимость заявленного major**, не доказательство совместимости с нашей Archicad 29.3001.
3. [Finch 101: Generating Floor Plans in Archicad](https://docs.finch3d.com/courses/finch-101/finch-101-generating-floor-plans-in-archicad) — кликом выбрать контур квартиры, проверка наружных стен и daylight, поиск подходящих plan-library вариантов; **Basic** показывает личную библиотеку, **Enterprise** — варианты Finch и организационную библиотеку. Стены, двери и зоны создаются в Archicad при принятии варианта. Существование интерфейса ≠ бесплатное право на его функционал.
4. [Finch 101: Download to Archicad](https://docs.finch3d.com/courses/finch-101/finch-101-download-to-archicad) — выбор Finch project / variant → Import; реальный объект: **walls, doors, zones, floor plates**, редактируемые элементы. Не утверждается, что это работает на тарифе Free без ограничений.
5. [Adaptive Plan Library](https://docs.finch3d.com/docs/projects-and-variants/unit-editor/adaptive-plan-library) — save plan → stretch/locked/extendable walls → plan adaptation, rule constraints; **Basic & Enterprise** могут выбирать сохранённые планы в режиме `Generate - Scan my library`. AI-generated organization's batch относится к Enterprise.
6. [Assign Adaptive Plans](https://docs.finch3d.com/docs/projects-and-variants/unit-editor/assign-adaptive-plans) — matching/adaptivity score, assign unchanged / adapt, auto-rotation, stretching constraints, варианты зеркального отражения.
7. [Finch export](https://docs.finch3d.com/docs/projects-and-variants/export) — CSV/PNG reports и BIM/CAD exports through plug-ins; **права на экспорт в Free и автоматизированный API не подтверждены**.
8. [Finch product/typology](https://www.finch3d.com/product) — firm-wide plan library, local requirements, unit/multiunit building planning, AI agent Enterprise; пример основной задачи — residential unit layouts. Маркетинговые claims о нормативном compliance не являются проверкой СП/ГОСТ для ТРЦ.

**API evidence:** в просмотренной публичной документации **не найден официально документированный публичный разработческий REST/SDK API** для программного вызова генерации/экспорта Finch из APA; это **не утверждение об абсолютном отсутствии приватного или enterprise API**. Custom integrations официально вынесены в Enterprise, значит бесплатный headless маршрут к APA НЕ ПОДТВЕРЖДЁН.

## Разделить 4 разных сценария

| Сценарий | Условия | APA |
|---|---|---|
| Установить Finch APX и войти в веб-сервис | Официальный beta-plugin для Archicad 29, учётная запись; скачивание не равно правам генерации | **Возможен ручной отдельный эксперимент**, на копии PLN |
| Бесплатно редактировать концепцию/показатели в Finch Free | Подтверждён Free без студенческой лицензии; no AI generation | **Отдельный пользовательский инструмент**, а не программное расширение APA |
| Генерировать и переносить AI планы в AC29 | Enterprise features; personal plan library scanning — Basic/Enterprise | **НЕ БЕСПЛАТНО**, не входить в базовый roadmap APA |
| Встроить генератор в APA через API без подписки | Публичный бесплатный headless API не обнаружен; custom BIM integrations — Enterprise | **NOT_AVAILABLE_AS_VERIFIED_FREE_PATH**; не пытаться вызывать скрытые веб-endpoint'ы в обход лицензии |

## Какие идеи переиспользовать внутри APA

Кандидат на **концептуальное заимствование поведения**, НЕ на копирование закрытого кода:
- **Adaptive Plan Library:** собственные шаблоны помещений/галерей/арендуемых блоков + характеристики/площади/минимальная ширина.
- **Matching score:** классификация назначения, габариты, длина наружной стены/световой фронт, доступ, встроенные MEP/core restrictions, близость к исходной типовой планировке.
- **Constraint-aware adaptation:** lock/extendable wall/allow stretch; только геометрические операции, реально представимые нашим единым ядром.
- **Variant provenance:** сохранить исходный вариант, параметры преобразования, constraints, измеренный результат / нарушения; строго `one geometry → all projections`.
- **BIM model output:** использовать только существующий APA SceneWriter и проверки GUID/readback, не загружать результат в Finch для обратной реинжиниринговой записи.

**Ограничение ТРЦ:** пример Finch — преимущественно распределение жилых квартир и типовые unit-plans. Не подтверждена нормативная генерация крупных ТРЦ с эвакуацией, атриумами, многоэтажными несущими осями и российскими СП.

## Что уже есть у APA и чего НЕ делать

APA имеет CP-SAT, Shapely/геометрические исследования, SceneWriter, IFC/GUID аудит, versioned command API registry и research knowledge gateway. Функциональная идея адаптации library variants может быть полезна, но реализовать её только если собственные модули APA не покрывают это; **никакого повторного нового геометрического движка и writer**.

**Важный контрпример:** на официальном сайте Free действительно существует. Ошибочно писать «всё платное». Но цена бесплатного редактора **не обеспечивает** бесплатную AI-генерацию и программную интеграцию.

## Если пробовать плагин ради ручного сравнения

1. Проверить файл только по официальной странице Finch и контрольную сумму; не добавлять бинарник в репозиторий.
2. Изолированная копия PLN, без ценных данных, точно Archicad 29.3001, установленная версия Finch add-on. Перед запуском snapshot,_GUID inventory.
3. Без оплаты/активации trial проверить: login, видимость команды меню, ручные Free-функции, реальные ограничения Import/Generate. Если требует Basic/Enterprise, фиксировать BLOCKED_LICENSE и прекратить тест генерации.
4. Если реальный import разрешён, проверить GUID/количество зон/стен/дверей, геометрию, истории/сохранение и readback, не заменять оригинальные элементы.
5. Реальные бенчмарки APA: скорость генерации вариантов/качество/ошибки/передача API не измерялись. Не писать `LIVE_VERIFIED`.

## Итог

**Finch 3D:** для **интеграции бесплатной AI-генерации планов в APA — DO_NOT_CONSIDER на текущих условиях** (основание: права Enterprise + отсутствие подтверждённого бесплатного программного API). **Как эталон UX Adaptive Plan Library — перспективен**, но только исследовательский ориентир. Отдельная бесплатная версия редактора существует; без студенческой лицензии. **Статус APA `NOT_TESTED`**, ничего не установлено и не запускалось.

**Для изменения приоритета требуется:** официальный бесплатный API или подтверждённая бесплатная лицензия на AI генерацию + экспорт и реальный независимый тест на Archicad 29.3001 с безопасным readback. Исследование не изменяет `main`, `PROJECT_PLAN.json`, APX, PLN и чужие рабочие ветки.
