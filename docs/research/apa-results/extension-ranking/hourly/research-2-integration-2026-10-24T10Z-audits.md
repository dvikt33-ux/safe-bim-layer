# APA №2 | 2026-10-24 10Z | Два внутренних контрааудита

**Scope:** SOURCE-only, это не независимая приёмка исследователя №3.

## Контрааудит A: «Разные владельцы элементов → безопасные параллельные writer в одном PLN»

**Проверяемая гипотеза:** GH Live Connection создаёт только GH-owned балки, APA SceneWriter создаёт только APA-owned стены, следовательно они не конфликтуют.

**Попытка опровержения:** [connected_components.py L323–359](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L323-L359) собирает весь `GetAllElements`; [L539–551](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L539-L551) сравнивает **весь** inventory с сохранённым receipt, а не только APA-owned; [L432–438](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L432-L438) после записи требует точное множество ожидаемых GUID. [L424–431](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L424-L431) хеширует retained geometry/материалы/relations. Новый GH-owned native GUID после source receipt вызывает дрейф, даже без изменения APA-owned. Изменение удерживаемого элемента также может нарушить retained signature. Если GH-элемент был частью исходного inventory, это не гарантирует безопасность его последующих изменений.

**Вывод:** **DUAL_WRITER_SAME_PLN_NOT_QUALIFIED**, полный 3-way NOT_FOUND. Без нового sync нельзя автоматически принимать GH-created GUID. Для BUILD-01 только SceneWriter native writes; GH Deconstruct read-only. Не путать GH read-only с гарантией отключения всех side-effect компонентов: определение нужно инвентаризовать.

**Что потребовалось бы для снятия запрета:** фактический G0, разрешённая политика ownership/ledger, точное GUID reconciliation, проверка no-loop, сохранение и readback, независимый ACCEPTED. В этой задаче новый writer/router/sync запрещён, поэтому результат NOT_FOUND.

## Контрааудит B: «Официальная GH связь + Rhino Cache + IFC Diff = автоматический круговой BIM-sync»

**Проверяемая гипотеза:** AC Deconstruct/Send Changes → GH → Rhino Content Cache Push → GH Design → AC формирует одну и ту же модель без потерь GUID, материалов, параметров, BREP, hosted openings и SEO.

**Попытка опровержения:**
1. [GC AC29](https://help.graphisoft.com/AC/29/INT/GC.pdf) Deconstruct читает вручную выбранный AC элемент и `Send Changes` обновляет GH reference; это не автоматический глобальный AC change event/merge. Deconstruct Roof не поддерживает Multi-Plane.
2. [GC AC29](https://help.graphisoft.com/AC/29/INT/GC.pdf) `Synchronize=False` возвращает Null; `True` активирует отдельный native writer, не SceneWriter. GH source component identity не равна AC GUID.
3. [McNeel Content Cache](https://discourse.mcneel.com/t/content-cache-updated-guide/181883) Push/Pull касается Rhino Object ID, Bake без ID может дублировать; [8.13 material bug](https://discourse.mcneel.com/t/content-cache-push-doesnt-update-material-data/194222) исправлен в 8.14, но локальный SR неизвестен.
4. [Graphisoft Teamwork](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680) delete/recreate может менять GUID и терять SEO; историческая статья не гарантирует конкретную AC29 конфигурацию.
5. [IfcDiff](https://docs.ifcopenshell.org/ifcdiff.html) предполагает стабильный GlobalId и сравнивает представления, но не переносит изменения в native Archicad и не выполняет rollback; GlobalId ≠ native Archicad GUID.
6. [connected CLI](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L515-L582) требует accepted source receipt, typed operations и отдельный preflight; не принимает произвольный GH BREP как Beam intent.

**Вывод:** **TRIAD_ROUNDTRIP_NOT_PROVEN**, GH idle/Content Cache Push/IfcDiff не доказывают AC commit и не снимают G0–G5. Предпочтителен односторонний native writer APA + read-only GH и независимая IFC QA.

**Критерий проверки в будущем:** два направления изменения одного Wall/Beam/Roof, сохранение identity across three apps, exact story/material/BREP/SEO, удаление/host, конфликт, crash recovery, Save/Close/Reopen. Пока все такие утверждения **NOT_FOUND/NOT_TESTED**.

**Итог:** оба контрааудита внутренние; SOURCE_ONLY; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED новых PASS нет; MODEL_MODE_NOT_VERIFIABLE.
