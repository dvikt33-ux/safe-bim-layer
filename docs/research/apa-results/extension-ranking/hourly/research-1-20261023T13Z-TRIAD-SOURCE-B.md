# APA №1 | 2026-10-23 13Z | TRIAD | 30 новых SOURCE-вопросов

Новые относительно отчёта 12Z вопросы: мультиплоскостная кровля, hosted Door/Window, GDL-параметры, Teamwork/GUID/SEO, Speckle Next-Gen, Tapir GH plugin, Rhino solver/Player. Это **30 конкретных проверок контрактов**, а не 30 независимых сайтов. Исторические Teamwork-утверждения 2017/2021 не переносятся автоматически на AC29. SOURCE не равно INSTALLED/LIVE/ACCEPTED. Лицензии: AC29/Rhino8 — базовые лицензии; Tapir upstream MIT; Speckle Free ограничен условиями текущего тарифа; никаких установок/платных API.

## S16 — Что происходит с лишними Slabs при сокращении GH списка?
**Факт / поля / направление:** Graphisoft Teamwork пример: 15→9 Slabs оставляет 6, если они не reserved для модификации/удаления.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE; это риск сирот, не доказательство AC29.
**Ограничение и адресное задание №2:** №2: inventory before/after + explicit deletion scope, не удалять без разрешения.

## S17 — Изменение атрибутов AC отражается в GH немедленно?
**Факт / поля / направление:** Teamwork note: attributes managed by ID; после изменения атрибута GH connection надо остановить и запустить заново.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE; AC29 проверить отдельно.
**Ограничение и адресное задание №2:** №2: запретить Sync после изменения Composite/Material/Layer до refresh и сравнения атрибутов.

## S18 — Сохраняется ли Solid Element Operation при модификации GH-элемента?
**Факт / поля / направление:** Teamwork note: SEO между GH и ручным элементом сохраняется, если исходный GH элемент изменён без пересоздания.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE, AC29 не проверено.
**Ограничение и адресное задание №2:** №2: проверять SEO graph после изменения при сохранённом GUID.

## S19 — Сохраняется ли SEO при delete/recreate?
**Факт / поля / направление:** Teamwork note: SEO теряется, потому что новый элемент имеет другой GUID.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE; риск реальной геометрии/стыков.
**Ограничение и адресное задание №2:** №2: STOP при GUID churn; read-only сравнение SEO edges до/после.

## S20 — Есть ли готовые поля происхождения GH элементов?
**Факт / поля / направление:** Teamwork note: Grasshopper Source Definition (file name) и Last update from Grasshopper (date/time) добавляются в классификацию/свойства.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE, AC29 property names/availability NOT_VERIFIED.
**Ограничение и адресное задание №2:** №2: проверить presence/provenance read-only; не заменять этими полями native GUID.

## S21 — Есть ли готовая обратная навигация между GH узлом и AC элементом?
**Факт / поля / направление:** Teamwork note: выбор GH node выделяет элементы в AC, а выбор AC элемента через palette может выделить GH node.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE, не automatic write.
**Ограничение и адресное задание №2:** №2: рассмотреть ручной ownership audit и диагностическое выделение, не автоисправление.

## S22 — Поддерживает ли Speckle официальный Archicad 29?
**Факт / поля / направление:** Официальная страница Speckle: supported versions 27/28/29; connector download.
**Первоисточник, версия, лицензия, статус:** https://speckle.systems/integrations/archicad/; SOURCE_2026, Speckle binary локально не установлен/не проверен.
**Ограничение и адресное задание №2:** №2: рассматривать Speckle только как дополнительный SOURCE-кандидат read/QA, без установки.

## S23 — Что AC→Rhino переносит через Speckle?
**Факт / поля / направление:** Speckle: meshes с materials, слои по этажам/типам, AC properties как Rhino user text.
**Первоисточник, версия, лицензия, статус:** https://speckle.systems/integrations/archicad/; SOURCE_2026; не native Wall/Roof в Rhino.
**Ограничение и адресное задание №2:** №2: возможный контроль геометрии/атрибутов, не применять как write-back BIM.

## S24 — Что AC→Grasshopper переносит через Speckle?
**Факт / поля / направление:** Speckle: meshes с materials и Archicad properties для downstream analysis.
**Первоисточник, версия, лицензия, статус:** https://speckle.systems/integrations/archicad/; SOURCE_2026; mesh не native parametric wall.
**Ограничение и адресное задание №2:** №2: только независимый аналитический канал; сопоставить число элементов и property IDs.

## S25 — Умеет ли Speckle Next-Gen создавать native Archicad стены на receive?
**Факт / поля / направление:** Официальный переходный guide: Next-Gen connectors НЕ поддерживают native element loading в Archicad; legacy и next-gen несовместимы.
**Первоисточник, версия, лицензия, статус:** https://www.speckle.systems/blog/guide-how-to-switch-to-next-gen-connectors; SOURCE_VENDOR, версия Next-Gen v3; не использовать для G3.
**Ограничение и адресное задание №2:** №2: исключить Speckle v3 из обязательного native writer; оставить read/QA кандидат.

## S26 — Есть ли native schema components в Speckle GH 3.6?
**Факт / поля / направление:** Сообщение команды Speckle 17.07.2025: GH connector stable 3.6.0, но legacy schema components для создания native элементов отсутствуют в Design Coordination.
**Первоисточник, версия, лицензия, статус:** https://speckle.community/t/grasshopper-is-officially-stable/18824; SOURCE_VENDOR_2025, не AC29 native writer.
**Ограничение и адресное задание №2:** №2: не считать Speckle DataObject равным Archicad Wall/Slab; использовать лишь анализ.

## S27 — Стабильны ли свойства Speckle GH DataObject для автоматического diff?
**Факт / поля / направление:** Speckle staff 10.09.2025: v3.8.2 добавил Expand Properties; пользователи сообщали проблемы Deconstruct outputs при смене типа и списковых свойств.
**Первоисточник, версия, лицензия, статус:** https://speckle.community/t/grasshopper-is-officially-stable/18824; SOURCE_COMMUNITY_2025, bugfix не доказан в локальной сборке.
**Ограничение и адресное задание №2:** №2: для QA предпочесть фиксированный набор свойств; не строить GUID diff на динамическом Deconstruct без проверки.

## S28 — Есть ли готовые GH-компоненты Tapir без собственного кода?
**Факт / поля / направление:** Tapir README: Grasshopper plugin via Rhino Package Manager, package 'tapir'; помечен work in progress; release 1.5.4 PR #457 указывает 193/196 commands coverage на тот момент.
**Первоисточник, версия, лицензия, статус:** https://github.com/ENZYME-APD/tapir-archicad-automation ; https://github.com/ENZYME-APD/tapir-archicad-automation/releases ; MIT upstream; installed GH plugin UNKNOWN.
**Ограничение и адресное задание №2:** №2: read-only проверить наличие GH tapir и версию, составить пересечение GH commands с локальным APX 1.5.10; не делать вторым writer.

## S29 — Есть ли готовое средство остановить GH solver при подготовке параметров?
**Факт / поля / направление:** McNeel Rhino 8 -Grasshopper: Solver Disable/Enable/Toggle; Document Open/Save/Close/CloseAll.
**Первоисточник, версия, лицензия, статус:** https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm; SOURCE_RHINO8; это вычислительный gate, не транзакция AC и не rollback.
**Ограничение и адресное задание №2:** №2: включить в no-code безопасный preflight, но AC Sync должен оставаться отдельным FALSE.

## S30 — Есть ли готовый запуск GH определения без открытия окна Grasshopper?
**Факт / поля / направление:** McNeel Rhino 8 GrasshopperPlayer выполняет .gh/.ghx без GH UI; scriptable -GrasshopperPlayer принимает path.
**Первоисточник, версия, лицензия, статус:** https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm; SOURCE_RHINO8; совместимость с AC Live Connection и выполнение Sync НЕ доказаны.
**Ограничение и адресное задание №2:** №2: только SOURCE-кандидат на последующий отдельный sandbox тест; не запускать на текущем PLN.
