# APA №1 — research-1-20261023T1723Z-TRIAD-OWNERSHIP — 30 предметных SOURCE-проверок
Дата: 23.10.2026 17:23Z. Контекст: Archicad29 build5101, Tapir1.5.10, Rhino8, GH. Цель: выявить не рассмотренные в 15:59Z/16:55Z ограничения владения, удаления и повторного соединения. **Не 30 независимых сайтов, не 30 runtime-тестов**.

## Список проверенных утверждений
| № | Техническое утверждение | Первичный источник | Доказательный статус |
|---|---|---|---|
| S01 | AC29 GC.pdf имеет титул User Guide 2.1, обновлён 22.01.2026 | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S02 | Официальная версия GH–AC29 Live Connection — build 3000 от 01.10.2025 | [B](https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/) | AC29_OFFICIAL |
| S03 | Официально указана совместимость GH–AC29 с Rhino 7 и Rhino 8 | [B](https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/) | AC29_OFFICIAL |
| S04 | GH–AC Live Connection несовместима с Archicad Start Edition | [B](https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/) | AC29_OFFICIAL |
| S05 | GH-generated native Archicad elements сохраняются в PLN без доступного GH-кода | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S06 | Оригинальная GH definition при повторном соединении с исходной PLN распознаётся для продолжения параметрического редактирования | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S07 | В один момент с Archicad соединяется только одна открытая GH definition | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S08 | Для выбора активной definition существует File → Connect Document to Archicad | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S09 | При повторном подключении GH контролируемые ею параметры имеют приоритет над ручными правками AC | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S10 | Ручные AC-изменения параметров, не контролируемых GH, могут сохраняться при GH пересчёте | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S11 | Copy/Paste GH-generated AC elements создаёт копии, потерявшие связь с исходной GH definition | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S12 | Открытое модальное окно AC с ожиданием пользовательского ввода приостанавливает GH–AC соединение | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S13 | При suspended connection GH элементы с ожидающими AC данными подсвечиваются жёлтым, индикатор AC перестаёт вращаться | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S14 | GH Object Settings поддерживает Create New Library Part с входами Geometry и Object Name | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S15 | Созданная GH библиотечная деталь размещается в Embedded Library активного AC проекта | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S16 | Изменение исходной GH геометрии обновляет созданную Library Part | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S17 | Удаление GH Object Settings удаляет созданную им Library Part из Embedded Library | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S18 | Переключение GH Object Settings на Use existing Library Part также удаляет ранее сгенерированную Library Part | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S19 | Размещённые экземпляры удалённой Library Part становятся Missing Objects в AC | [A](https://help.graphisoft.com/AC/29/INT/GC.pdf) | AC29_OFFICIAL |
| S20 | GDL GLOB_INTGUID — внутренний GUID, который пользователь не может контролировать | [E](https://help.graphisoft.com/AC/29/INT/GDL.pdf) | AC29_OFFICIAL |
| S21 | GDL GLOB_ID — пользовательский Element ID, отличный от внутреннего GUID | [E](https://help.graphisoft.com/AC/29/INT/GDL.pdf) | AC29_OFFICIAL |
| S22 | В Teamwork GH-generated элементы резервируются создавшим их пользователем | [C](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680) | HISTORICAL_2017_2021 |
| S23 | При Teamwork reservation другим пользователем повторная генерация GH может создать дубликат | [C](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680) | HISTORICAL_2017_2021 |
| S24 | Если GH элемент не зарезервирован текущим пользователем, его изменение может не примениться | [C](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680) | HISTORICAL_2017_2021 |
| S25 | Если не зарезервированы удаляемые элементы, GH может оставить лишние старые элементы | [C](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680) | HISTORICAL_2017_2021 |
| S26 | При GH update исходного элемента SEO может сохраняться; при delete/recreate GUID меняется и SEO связь теряется | [C](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680) | HISTORICAL_2017_2021 |
| S27 | GH source definition и Last update from Grasshopper указаны как служебные свойства происхождения | [C](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680) | HISTORICAL_2017_2021 |
| S28 | Историческое поведение: GH Synchronize=False останавливает обновление, но не удаляет ранее созданные AC элементы | [D](https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/m-p/292446/highlight/true) | HISTORICAL_2020 |
| S29 | Исторический no-code workaround удаления: Stream Filter + Boolean Toggle + пустой вход вместо обычного Disable | [D](https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/m-p/292446/highlight/true) | HISTORICAL_2020 |
| S30 | В существующем APA PR74/issue192 SceneWriter — единственный approved writer для APA-owned GUID; №2 17Z подтверждает SOURCE-путь floorPlans с polygon holes и предупреждает о конкурирующем GH writer | [F](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) · [G](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) · [H](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T17Z-triad-report.md) | INTERNAL_SOURCE |

## Границы проверки
- S01–S21: официальный AC29 guide / AC29 GDL guide и официальный каталог загрузок. PDF Graphisoft индексирован поиском по тематическим фрагментам; **полный постраничный разбор 22.8 MB PDF не выполнен** (прямое получение файла не удалось). В частности S05–S13 и S14–S19 основаны на индексированных точных фрагментах официального AC29 руководства.
- S22–S29: официальное сообщество Graphisoft, но статьи 2017–2021/2020; это **исторические свидетельства**, НЕ гарантия идентичного поведения на GH–AC29 build3000.
- S30: подтверждено чтением [issue192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) и [№2 17Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T17Z-triad-report.md); это внутренний SOURCE-контракт, не LIVE. [Матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) прочитана, count=61, не является доказательством установки.
- Не проверены: локальная установка GH–AC29, фактический GH palette, наличие source properties в текущем проекте, Teamwork сценарии AC29, API управления Sync, сохранность GUID при удалении, Save/Open на BUILD-01.
- SOURCE=30 отдельных технических вопросов; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
