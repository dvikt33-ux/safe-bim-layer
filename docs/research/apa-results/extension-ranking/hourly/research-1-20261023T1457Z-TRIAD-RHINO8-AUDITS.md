# APA №1 — 23.10.2026 14:57Z — два контрааудита

## A1 — первоисточник, версия, лицензия
1. Content Cache, UserText, Blocks, Query/Group/Filter, Import Model документированы производителем McNeel для Rhino 8: https://www.rhino3d.com/features/grasshopper/content-cache/, https://www.rhino3d.com/en/docs/guides/grasshopper/object-attributes/, https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/, https://www.rhino3d.com/features/grasshopper/usertext/, https://www.rhino3d.com/en/features/grasshopper/blocks/. Это встроенные GH компоненты Rhino 8; отдельная лицензия на эти компоненты не обнаружена, Rhino8 требует лицензию.
2. Подробная инструкция Content Cache от 17.05.2024 явно требует Rhino 8.8 **Release Candidate** (https://discourse.mcneel.com/t/content-cache-updated-guide/181883). Нельзя переносить её поведение без проверки на конкретный стабильный Rhino 8 SR, установленный у пользователя. Официальная feature-page подтверждает наличие Content Cache в Rhino8 в целом, но не все нюансы действий в каждой сборке.
3. Graphisoft GH-AC29 build3000 Windows/Rhino8: https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/; local installed/plugin/AC edition не считаны. Документ AC29 GC.pdf слишком велик для постраничного web.open, поэтому новое утверждение о полном AC update GUID контракте не делалось.
**Результат A1:** SOURCE_VALID_FOR_RHINO8_GENERAL; EXACT_SR_CONTRACT=UNVERIFIED; AC29_CONNECTOR_LOCAL=UNKNOWN.

## A2 — инженерная применимость и недублирование
1. Content Cache управляет Rhino object ID, не Archicad GUID. UserText AC_GUID_REFERENCE — копия строки, не реальный BIM identity и не доказательство сохранения SEO/host. Никакой транзакционной атомарности между .3dm/.gh/.pln источники не обещают.
2. Для AC29 запись только через уже согласованные GH-AC Live Connection (GH-owned) или существующий APA SceneWriter (APA-owned), не одновременно по одному элементу. В PR #74 исторический отдельный нативный двухэтажный прототип, но не текущий BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/pull/74 .
3. При повторном Push/Sync: проверить Rhino ID, AC GUID, количество, geometry BREP, тип/этаж/host/material/SEO до и после; при UNKNOWN остановить повтор CREATE. Community roof-case (https://community.graphisoft.com/t5/Parametric-design/Updating-existing-Roof-Components-instead-of-creating-new-ones/td-p/592049) демонстрирует риск, но не AC29 доказательство.
4. Group/Filter, UserText, Blocks и Import Model не дублируют native SceneWriter: они готовят и проверяют Rhino/GH геометрию; им запрещено принимать статус native writer. Локальный G0 заблокирован.
**Результат A2:** KEEP_SOURCE_CANDIDATES_R1457-01..06; THREE_WAY_SYMMETRIC_SYNC=NOT_PROVEN; NATIVE_GUID_STABILITY=NOT_PROVEN; NO_NEW_WRITER.

## Состояние и пропуски
Прочитаны NEXT_RESEARCH_PRIORITIES.md, TRIAD-PIVOT, отчёты №1 13Z и 13:56Z, PR74, issue192. Точные пути актуальных №2/№3 и матрицы 61 в исследовательской ветке не установлены; GitHub search по default branch результатов не дал. Поэтому независимый cross-report и matrix audit НЕ ВЫПОЛНЕНЫ, их нельзя считать частью A1/A2. PROJECT_PLAN rev182 не менялся. G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.
