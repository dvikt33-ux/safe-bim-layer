# APA №1 — два контрааудита — research-1-20261023T1723Z-TRIAD-OWNERSHIP

## A1: Первоисточники, версия, лицензии, ложная актуальность
1. AC29 GC.pdf — официальный guide с индексированными точными фрагментами про удаление Library Part, параметрический приоритет, копирование, модальные окна и единственную GH definition. Официальный add-on GH–AC29 build3000 от 01.10.2025, поддерживает Rhino8. **SOURCE**, не INSTALLED; полный PDF 22.8 MB не удалось скачать/постранично проверить. Источники: https://help.graphisoft.com/AC/29/INT/GC.pdf; https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/.
2. Teamwork reservation/duplicate/stale и source property — официальная статья сообщества Graphisoft 2017, ред.2021. **HISTORICAL_SOURCE**, не считать AC29 behavior без runtime-проверки: https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680.
3. Synchronize=False / Stream Filter null — форум Graphisoft 2020. **HISTORICAL_WORKAROUND**, не разрешение на DELETE, не доказанный AC29 контракт: https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/m-p/292446/highlight/true.
4. GLOB_INTGUID vs GLOB_ID — официальный GDL Reference Guide AC29: https://help.graphisoft.com/AC/29/INT/GDL.pdf. **GUID нельзя задать из GDL**; не подменять native identity user ID.
5. Лицензии: GH–AC дополнение доступно от Graphisoft бесплатно, но требует отдельно действующих Archicad и Rhino; установленный add-on и лицензии не проверены. AC30 release build3000 не использовать вместо AC29.
**Вердикт A1:** 30 SOURCE-утверждений в SOURCE-файле, из них 21 AC29/официальных и 8 исторических + 1 внутренний; 0 runtime PASS. Исторические риски явно размечены.

## A2: Инженерная применимость, конфликт владельцев, недублирование
1. **Library deletion:** C01 — опаснее простой геометрической потери: удаление GH settings может нарушить Embedded Library и превратить множество объектов в Missing. Требовать library inventory before/after и сохранение на копии.
2. **Param precedence:** C03 — единый owner элемента недостаточен; нужен owner каждого параметра. GH-controlled fields могут перезаписать ручные AC edits после reconnect.
3. **Copy/paste:** C06 — сохранение native GUID исходника не означает, что копии остаются связанными с GH. Source metadata не гарантирует текущий link.
4. **Teamwork:** C04 — historical duplicate/stale behavior не применять автоматически к solo PLN. При неизвестном резервировании запретить write.
5. **Sync pause:** C05 — Boolean FALSE не гарантирует удаления и не является транзакцией. Модальные окна AC могут блокировать live connection без ошибки компилятора.
6. **No duplicate writer:** PR74/SceneWriter для APA-owned элементов уже существует; прямой GH→AC writer допускать лишь на GH-owned элементах с явным разделением GUID и source provenance. GH→jSwan→typed JSON→PR74 путь №2 17Z остаётся SOURCE_ONLY; полигональные holes уже поддерживаются на уровне исходников, не повторять ложный NOT_FOUND. Источники: https://github.com/dvikt33-ux/safe-bim-layer/issues/192, https://github.com/dvikt33-ux/safe-bim-layer/pull/74, https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T17Z-triad-report.md.
7. **No universal sync:** одна GH definition, GH param precedence, manual AC edit и Rhino geometry updates не создают доказанной двусторонней native-GUID записи. FULL_THREE_WAY_SYNC=NOT_FOUND.
8. **G0–G5:** G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4 NOT_RUN; G5 NOT_RUN. SOURCE=30; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. No Save/Open test.
**Вердикт A2:** новые P0 для №2 — GH library lifecycle и точная GH↔PLN identity, затем параметрический ownership и Teamwork gate. Изменения main, кода, PLN/APX, установок, LIVE и merge не выполнялись.
MODEL_MODE_NOT_VERIFIABLE.
