# APA №1 — 23.10.2026 14:57Z — Rhino 8 готовые no-code компоненты для APA triad

## Реальное влияние на BUILD-01
**Новое:** обнаружен штатный Rhino8 Grasshopper Content Cache с Push/Pull/заменой Rhino объектов без дублирования, плюс Query Model Objects, UserText, Group/Filter Content, Blocks, Import Model. Это расширяет Rhino↔GH управление геометрией/атрибутами без нового writer. **НЕ означает** симметричную синхронизацию AC29↔Rhino↔GH или сохранение Archicad GUID. Самая существенная граница: Rhino object ID и native Archicad GUID — разные пространства идентичности.

**Ворота:** G0 BLOCKED (нет локального build/SR/AC add-on/APX/PLN/port/gh plugin inventory); G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4 NOT_RUN; G5 NOT_RUN. Новый BUILD-01 не создавался. Issue: https://github.com/dvikt33-ux/safe-bim-layer/issues/192

## Проверенные приложения (create→fetch, точное сравнение)
- [SOURCE](research-1-20261023T1457Z-TRIAD-RHINO8-SOURCE.md): blob `23c9e95d06cdc17e57eca34a0c5c55e2fea50a52`; commit `2dc15162b399321604c335b3b6375feea1c3147d`; exact_readback=true; chars=5626
- [CARDS](research-1-20261023T1457Z-TRIAD-RHINO8-CARDS.md): blob `17887db18cc721d08b1f44bf8a0b54cd072713fc`; commit `63d5dea798523df3368a36b5fd65d3e80e056981`; exact_readback=true; chars=5211
- [AUDITS](research-1-20261023T1457Z-TRIAD-RHINO8-AUDITS.md): blob `1b322fc09b8e4904ccc84f798502e4a5e3bed015`; commit `395b6d0756f2849ffbe8deb80d231c9fc63101d1`; exact_readback=true; chars=3230

**Объём:** 28 предметных SOURCE-проверок, 6 карточек, 2 контрааудита. Не 28 независимых источников; никаких OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED тестов.

## Техническое решение для №2
1. Подготовить read-only/no-code Rhino↔GH DAG: Query Model Objects→Model Object(+attributes/UserText)→Content Cache(Pull/Push with Action gate)→GH geometry→GH-AC supported native type, только SOURCE-документация, без реальной записи.
2. Проверить **exact Rhino8 SR** против Content Cache 8.8 RC описания, и наличие штатных компонентов. Не считать Rhino GUID тождественным AC GUID.
3. Составить ownership matrix: Rhino/GH geometry, GH-AC native writer только для GH-owned; существующий APA SceneWriter только для APA-owned; ни одного shared write.
4. Для сложной кровли: separate GH geometry/source objects, AC native roof geometry/host/SEO, before-after Rhino IDs и AC GUID; multi-plane обратный Deconstruct не доказан.
5. Проверить Rhino layers/UserText Building ID/Owner/AC_GUID_REFERENCE как фильтры и вспомогательные метки, а не native identity.
6. Для групп элементов: Query/Group/Filter + вычисляемая площадь vs UserText Area; Rhino Blocks — только geometry reuse, не нативный GDL.
7. Для G0 дополнительно подтвердить AC29 build5101, GH-AC29 build3000, Rhino8 SR, Tapir1.5.10, current PLN/port/APX/command schema, библиотеки, exact local identity.

## Контекст, ограничения
Прочитаны NEXT_RESEARCH_PRIORITIES.md, TRIAD-PIVOT, №1 13Z и 13:56Z, PR74, issue192. Актуальные №2/№3 и матрица 61 напрямую не прочитаны: точные пути не установлены. Исторический PROJECT_PLAN rev182 не изменён. Main, код, PLN/APX, установки, LIVE, платные API, merge не затрагивались. MODEL_MODE_NOT_VERIFIABLE.
