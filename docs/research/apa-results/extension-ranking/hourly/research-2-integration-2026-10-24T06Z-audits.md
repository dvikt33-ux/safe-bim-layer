# APA №2 | 2026-10-24 06Z | Два документарных контрааудита

Контрааудиты №2, **не** независимый аудит №3; SOURCE_ONLY, без LIVE.

## A — «Synchronize=False фиксирует готовый результат GH» — ОПРОВЕРГНУТО
Гипотеза: выключение Synchronize оставляет готовый typed GH output и обеспечивает безопасную паузу перед PR74.
Контрдоказательство: официальный AC29 GC.pdf стр.17: False не генерирует элемент, выдаёт **один Null** независимо от входов. Поэтому downstream, читающий output Design-компонента, не получает frozen BIM value. Историческая Graphisoft Community 2020 описывает сохранение уже созданного элемента Archicad на паузе, но это **не** сохранение typed GH output и не AC29 LIVE. Вывод: False — stop новых GH→AC изменений, не транзакционный snapshot; **удаление ранее созданного AC-элемента при False не утверждаем**.
Решение: сохранять upstream GH/Rhino geometry в .gh/.3dm, GUID/provenance/hash, не питать authored JSON от output GH-generating компонентов; APA-owned только SceneWriter.
Источники: https://help.graphisoft.com/AC/29/INT/GC.pdf; https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/m-p/292446/highlight/true .

## B — «Двусторонность AC↔GH даёт native Multi-Plane Roof roundtrip» — ОПРОВЕРГНУТО
Гипотеза: AC Multi-Plane Roof→GH Deconstruct/Brep→Rhino modify→AC Multi-Plane Roof, тот же GUID, BIM-тип, SEO.
Контрдоказательство: AC29 GC.pdf стр.40 Deconstruct Roof принимает **только Single-Plane Roof**; стр.41 Brep перечисляет Single-Plane, не Multi-Plane. PR74 authored nativeComponents разрешает Basic Single-Plane CreateRoofs, не Multi-Plane writer; выход контура ограничен 0.35 м. IFC/Hotlink/GDL передают геометрию, но не доказывают сохранение одного native Multi-Plane Roof.
Решение: для сложной кровли только Rhino/GH parametric source + AC native read-only verification до доказанного готового native маршрута; многоплоскостные сборки из отдельных Roof — другой BIM-объект, требующий отдельного согласования.
Источники: https://help.graphisoft.com/AC/29/INT/GC.pdf; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L288-L312 .

**Приёмочные ворота:** G0 BLOCKED_RUNTIME, G1 NOT_RUN, G2 SOURCE_PARTIAL, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. OFFLINE=0, BUILD=0, INSTALLED=NOT_VERIFIED, LIVE=0, ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
