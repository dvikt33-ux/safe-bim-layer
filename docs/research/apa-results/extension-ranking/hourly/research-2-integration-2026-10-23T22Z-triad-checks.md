# APA №2 / 22Z — 30 SOURCE-проверок (НЕ 30 независимых сайтов)
Дата UTC 2026-10-23 22Z. Это 30 предметных сопоставлений опубликованных контрактов; локальные команды, установки и PLN не запускались. AC29 PDF большой, полный постраничный аудит PDF НЕ заявляется; цитируем только проиндексированные фрагменты официального руководства.

[B]: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
[P]: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
[A]: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py
[R]: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py
[G]: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
[M]: https://help.graphisoft.com/AC/29/INT/GC.pdf
[H]: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm
[D]: https://help.graphisoft.com/AC/29/INT/_AC29_Help/140_UserInterfaceDialogBoxes/140_UserInterfaceDialogBoxes-15.htm
[F]: https://help.graphisoft.com/AC/28/INT/_AC28_Help/005_NewFeatures/005_NewFeatures-9.htm
[T]: https://github.com/ENZYME-APD/tapir-archicad-automation
[J]: https://github.com/andrewheumann/jSwan
[I]: https://docs.ifcopenshell.org/ifctester.html
[Q]: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
[N]: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
[X]: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T2156Z-TRIAD-ZONES-MARKERS-RELATIONS.md

| № | Проверяемое утверждение | Основание |
|---:|---|---|
| 01 | BUILD-01 требует новое отдельное здание G0–G5, а не исторический fixture | [B] |
| 02 | PR74 исторически описывает 10 Wall, 2 Slab, 6 Window, 2 Door, 1 Roof; не является новым TRIAD BUILD-01 | [P] |
| 03 | Официальный GH–AC29 Live Connection build3000, Windows, Rhino7/8; релиз 01.10.2025 | [G] |
| 04 | Официальное руководство именно AC29, обновлено 22.01.2026; PDF 22+ MB не скачан, извлечены индексированные разделы | [M] |
| 05 | AC29 GH palette Sync Changes to GH при включении автоматически и непрерывно обновляет ссылки на элементы AC | [M] |
| 06 | При выключенном Sync Changes to GH изменения AC не отражаются автоматически в GH | [M] |
| 07 | Lock/Unlock GH Elements допускает ручные изменения GH-generated объектов в Archicad | [M] |
| 08 | При повторном Lock GH-controlled параметры возвращаются к определению Grasshopper | [M] |
| 09 | Параметры, которые GH не умеет задавать (пример: материал панели CW), сохраняют ручные настройки AC после Lock | [M] |
| 10 | Select in GH находит GH-компонент, породивший выбранный GH-generated элемент AC | [M] |
| 11 | AC Parameter Components имеют Set One Element и Set Multiple Elements для обновления ссылок | [M] |
| 12 | Clear Values очищает значения Parameter Component; это операция над GH-ссылками, не удаление AC элемента | [M] |
| 13 | GH Object Settings Create New Library Part создаёт библиотечную деталь в Embedded Library AC | [M] |
| 14 | Несколько входных Geometry объединяются в одну сложную Library Part | [M] |
| 15 | Изменение Geometry в GH обновляет соответствующую Library Part | [M] |
| 16 | Удаление GH Object Settings компонента удаляет созданную им Library Part из Embedded Library | [M] |
| 17 | Переключение GH Object Settings в Use existing Library Part также удаляет ранее созданную деталь | [M] |
| 18 | Размещённые экземпляры удалённой детали становятся Missing Objects в Archicad | [M] |
| 19 | AC29 Hotlink Update policy Ignore Hotlinks не обновляет изменённые источники при output | [D] |
| 20 | AC29 Hotlink Update policy Check and ask запрашивает подтверждение при output; это значение по умолчанию | [D] |
| 21 | AC29 Hotlink Update policy Check and update automatically обновляет модули при document output, в том числе Publish | [D] |
| 22 | Выбранная Hotlink Update policy хранится в Preferences, НЕ сохраняется внутри PLN | [D] |
| 23 | AC29 Make Backup Copy создаёт предыдущую версию проекта с расширением .bpn | [D] |
| 24 | Recovery File не заменяет ручное сохранение открытых Library Parts | [D] |
| 25 | Hotlink Module Manager различает Modified/Missing/OK; источник может быть изменён без обновления экземпляров | [H] |
| 26 | Hotlink Update, then Compare запускает штатное сравнение моделей после обновления модуля | [H] |
| 27 | GH–AC connection уже имеет нативные Beam/Column формы и Hotlink placement, но это прямой WRITE вне APA SceneWriter | [F], [A] |
| 28 | PR74 authored schema отвергает mode=offline без callable read-only transport; preflight требует реальный guard | [A] |
| 29 | PR74 authored nativeComponents whitelist включает Columns/Doors/Windows/Walls/Roofs, но не Beams; Roof требует pivotLine | [A] |
| 30 | PR74/SceneWriter — единственный одобренный writer; ни GH auto-sync, ни Library Part regeneration не обеспечивают общий SQLite lease или GUID-preserving 3-way | [A], [R], [M] |

**Состояние:** SOURCE=30 документарных утверждений; OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0 новых результатов BUILD-01. Схема pinned Tapir 1.5.10 и исходники PR74 не являются доказательством локального APX. Пункты 27/30 — инженерные выводы из указанных контрактов, а не результаты LIVE. MODEL_MODE_NOT_VERIFIABLE.
