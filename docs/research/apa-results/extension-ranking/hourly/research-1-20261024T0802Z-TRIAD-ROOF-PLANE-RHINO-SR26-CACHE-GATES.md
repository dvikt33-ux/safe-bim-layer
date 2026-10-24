# APA №1 | 2026-10-24 08:02 UTC | BUILD-01: плоскость нативной кровли и версионные исправления Rhino Content Cache

## 0. Реальное влияние на тройную сборку BUILD-01 #192

**P0-дельта A — GH Roof использует геометрию, а не сохранённый Favorite Pitch.** В официальном руководстве Graphisoft Archicad 29, раздел Roof Component, стр. 28, плоскость входного планарного полигона определяет **одновременно положение, уклон и высоту** нативного Single-plane Roof. Значения **Offset from Home Story** и **Roof Pitch**, хранящиеся в Favorites входа Roof Settings, **не влияют** на такую геометрию. Это важная ловушка при автоматическом выборе GH→AC вместо существующего APA CreateRoofs: одинаковый Favorite не гарантирует одинаковую кровлю. Обязательно сравнивать native Roof plane/pitch/Z, material, home story и GUID, а не только название Favorite.

**P0-дельта B — Rhino 8 SR25/SR26 содержит конкретные исправления, влияющие на корректность синхронизации.** McNeel SR25 (8.25.25314, 11.11.2025) исправил игнорирование Mesh Colors в Content Cache (RH-89804). SR26 (официальное обозначение *Service Release 26*, опубликован 16.12.2025, указанный в объявлении build **8.25.25349**) исправил отсутствие сравнения ориентации Surface/Curve при Cache Push (RH-89952), сохранение Material Content Note/Tag после GHData serialization (RH-89951) и регрессию Sweep1 (RH-90489). **Это исправления Rhino-side, не доказательство BIM-native AC roundtrip**. Установленный Rhino 8 Service Release неизвестен: ничего не обновлять без разрешения.

**P0-дельта C — выходы AC Design в GH не являются обычной Rhino-геометрией.** AC29 GC.pdf, раздел Archicad Design Components: результат GH→AC typed native component нельзя подавать напрямую в GH Move; преобразования нужно выполнять на входной геометрии до AC Design. Несколько входных кривых создают несколько отдельных AC элементов. Это ограничение автоматического маршрутизатора и сохранения соответствия один-к-одному между Rhino Object ID и Archicad GUID.

**СТАТУСЫ ЭТОГО ПРОХОДА:** SOURCE=25 отдельных документарных/репозиторных сверок (реестр ниже); OFFLINE=0 новых; BUILD=0 новых; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых. G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN. Полный AC↔GH↔Rhino нативный синхронный commit, GUID-preserving 3-way rollback, native Multi-plane Roof roundtrip = **NOT_PROVEN**. Это не 25 LIVE-тестов. MODEL_MODE_NOT_VERIFIABLE.

**База:** Windows 11, Archicad 29 build 5101, локальный Tapir 1.5.10, Rhino 8 (Service Release UNKNOWN), Grasshopper. Graphisoft AC29 Live Connection **build 3000**, Windows/Rhino7–8, 01.10.2025; наличие установки НЕ проверено. Graphisoft уже публикует AC30 build3000 от 07.10.2026, **не подменять AC29 пакетом AC30**. Пакет Graphisoft доступен для скачивания бесплатно, но Archicad и Rhino — коммерческие лицензируемые приложения, Grasshopper включён в Rhino. Не устанавливать/не менять версии.

## 1. Шесть действительно новых SOURCE-карточек

### F0802-01 | GH Roof: уклон и отметка берутся из плоскости входного полигона

- **Операция BUILD-01:** GH-owned Single-plane Roof, параметрическое изменение уклона/высоты в Rhino/GH с нативной записью в AC29; либо SOURCE-сопоставление с APA-owned CreateRoofs.
- **Официальный версионированный источник:** Graphisoft AC29 Grasshopper–Archicad Live Connection User Guide, стр.28, Roof Component: https://help.graphisoft.com/AC/29/INT/GC.pdf ; build3000 https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ .
- **Контракт/направление:** GH planar Curve/Surface polygon → AC native Single-plane Roof; ориентация плоскости задаёт roof pitch, Z и контур. Basic/Composite выбирается Roof Settings; Building Material/Composite — соответствующий параметр.
- **Ограничение:** сохранённые в Favorite Offset from Home Story/Roof Pitch **не определяют** полученную геометрию при данном входе. Это не AC→Rhino writer, не Multi-plane Roof, не сохранение GUID при recreate. Установленный add-on не проверен; GH-owned writer нельзя применять к APA-owned Roof.
- **Поручение №2 I0802-01:** SOURCE-only сравнить два контракта GH Roof polygon plane и PR74 CreateRoofs pivotLine/floorIndex/Basic/material. Подготовить матрицу pitch/Z/plane/homeStory/material/native GUID, fail-closed при несовпадении. Никаких GH write calls.

### F0802-02 | AC29 GH Design typed output и кардинальность элементов

- **Операция:** автоматический выбор маршрута для изменения стен/перекрытий/окон без потери соответствия объектов.
- **Официальный источник:** Graphisoft AC29 GC.pdf, раздел Archicad Design Components, https://help.graphisoft.com/AC/29/INT/GC.pdf ; AC29 add-on build3000.
- **Контракт/направление:** GH input geometry → Archicad native typed Design component; output Design не является Rhino Curve/Brep для стандартного GH Move. При нескольких входных curves генерируются отдельные нативные элементы. Изменение геометрии — upstream до Design; AC→GH возможен отдельный Deconstruct/Sync Changes route.
- **Ограничение:** нельзя вывести универсальный RhinoObjectID→один Archicad GUID. Сегментация кривых также может увеличивать число Wall/Beam; вторая GH→AC запись конкурирует с SceneWriter. Нет автоматического ID crosswalk/transaction.
- **№2 I0802-02:** read-only cardinality gate: количество GH входов/сегментов, ожидаемых native элементов, GUID mapping; все трансформации до AC Design; при неравенстве/UNKNOWN STOP. Не добавлять сериализатор.

### F0802-03 | Rhino SR25 RH-89804: Content Cache Mesh Colors

- **Операция:** GH→Rhino обновление меша фасада/материальной раскладки после изменения только цветов вершин.
- **Официальный источник:** McNeel Service Release 25, 11.11.2025, Rhino 8.25.25314: https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/32 .
- **Версия/лицензия:** Rhino8 SR25, коммерческая лицензия Rhino; GH Content Cache встроен, дополнительная подписка не требуется.
- **Контракт/направление:** GH Content Cache Push → Rhino mesh. В SR25 исправлена проверка Mesh Colors при решении, требуется ли обновление (RH-89804). Это **не** AC Building Material GUID и не гарантированное обновление AC.
- **Ограничение:** точная локальная версия неизвестна; материал, mesh color, vertex color и BIM Building Material — разные данные. Никаких установок/Push в текущем проходе.
- **№2 I0802-03:** в G0 добавить read-only Rhino SR/version; для будущего отдельно разрешённого QA записать сравнение vertex color + material ID до/после, не приравнивать цвет к native material.

### F0802-04 | Rhino SR26 RH-89952: ориентация Curve/Surface при Content Cache Push

- **Операция:** GH→Rhino обновление поверхности кровли после изменения направления U/V или ориентации контура без заметного изменения bbox.
- **Официальный источник:** McNeel Service Release 26, 16.12.2025: https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/34 ; исправление RH-89952.
- **Версия/лицензия:** SR26 (в официальном посте build **8.25.25349**, сохраняем эту необычную запись без исправления догадкой), Rhino8 commercial/GH built-in.
- **Контракт/направление:** GH Content Cache Push → Rhino Curve/Surface; исправлено сравнение ориентации. Ориентация влияет на нормали/контуры, не всегда обнаруживается bbox-проверкой.
- **Ограничение:** исправление Cache Push не гарантирует нормали/уклон/SEO нативной AC Roof. Не доказана поддержка локального SR.
- **№2 I0802-04:** SOURCE-only расширить будущий geometry QA полями orientation, normal, curve direction, closed/open, plane/pitch, native AC BREP; при UNKNOWN STOP. Без нового writer.

### F0802-05 | Rhino SR26 RH-89951: Material Content Note/Tag при GHData serialization

- **Операция:** перенос Rhino-side материальных меток через GH перед формированием контролируемого BIM mapping.
- **Официальный источник:** McNeel SR26, 16.12.2025: https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/34 ; RH-89951.
- **Версия/лицензия:** Rhino8 SR26 commercial, GH built-in; версия установленного SR неизвестна.
- **Контракт/направление:** сохранение Material Content Note/Tag при GHData serialization исправлено в SR26. Это внутренние метаданные GH/Rhino, **не** native AC Building Material, Surface или классификация.
- **Ограничение:** не доказано, что произвольные UserText/IFC/GDL свойства сохраняются, и не обеспечен AC GUID/material crosswalk.
- **№2 I0802-05:** SOURCE-only матрица полей: Rhino Material ID, Content Note/Tag, UserText, Mesh Color, AC Surface, AC BuildingMaterial GUID, AC Classification/Property. Не допускать автоматического равенства.

### F0802-06 | Rhino SR26 RH-90489: регрессия Sweep1 и версия геометрического генератора

- **Операция:** построение Rhino/GH sweep-профиля для сложной кровли/карниза, затем сравнение геометрии с baseline до любой передачи.
- **Официальный источник:** McNeel SR25 11.11.2025 https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/32 (обновлён Sweep 1 Rail на Brep.CreateFromSweep, RH-89549); SR26 16.12.2025 https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/34 (исправлена регрессия Sweep1, RH-90489).
- **Версия/лицензия:** Rhino8 SR25/SR26 commercial; GH built-in.
- **Контракт/направление:** Rhino/GH локальное вычисление Sweep1 → Rhino geometry; нет GH→AC native Multi-plane Roof contract.
- **Ограничение:** результаты геометрии могут различаться между SR; ни точный SR, ни результат на пользовательской модели не проверены. Нельзя объявить Sweep1 готовым нативным roof writer.
- **№2 I0802-06:** read-only список зависимых от SR геометрических операций и будущая контрольная пара .3dm/.gh hashes; для BUILD-01 зафиксировать version pin и geometry baseline, не запускать.

## 2. Реестр 25 реально выполненных SOURCE-проверок

**Метод:** отдельные сверки утверждений по прочитанным GitHub API/первичным страницам; не 25 уникальных сайтов и не 25 runtime-прогонов. Метки [I] issue #192, [P] PR74 pinned, [C] pinned compiler, [N] NEXT, [V] TRIAD-PIVOT, [M] matrix, [R2] №2 07Z, [R3] №3 20.10 18Z, [G] Graphisoft AC29 GC.pdf search-indexed excerpt, [D] Graphisoft downloads, [S25]/[S26] McNeel release posts.

| № | Проверенное утверждение | Итог/источник |
|---:|---|---|
| 01 | Исследовательская ветка существует и доступна | PASS GitHub branch search |
| 02 | Файл NEXT находится в docs/research/apa-results/extension-ranking | PASS [N], blob 6f074693360231c5cb42ada815984a6b0dd504c0 |
| 03 | TRIAD-PIVOT требует тройной маршрут, не отдельный AC writer | PASS [V], blob 896fa3af0953468ca58fca710f32cb926504f582 |
| 04 | Issue #192 содержит G0–G5 и запрет повторного CREATE | PASS [I] |
| 05 | PR74 остаётся open/draft/unmerged, head 5a3a9201 | PASS [P] |
| 06 | PR74 compiler schemaVersion=apa-authored-project/1, units=meters | PASS [C], lines 263–278 |
| 07 | PR74 nativeComponents allowlist не содержит CreateBeams | PASS [C], lines 288–296 |
| 08 | PR74 CreateRoofs требует pivotLine, Basic, buildingMaterialId | PASS [C], lines 301–305 |
| 09 | PR74 native slab footprint один на этаж, absolute level | PASS [P], authored_native_plan lines 72–111 |
| 10 | Матрица заявляет 61 items | PASS [M] |
| 11 | Матрица содержит 61 фактических элементов и 61 уникальный ID | PASS [M], JSON parsed |
| 12 | Пересчёт формулы приоритета даёт 0 расхождений по 61 элементу | PASS [M], JS recompute |
| 13 | №2 07Z подтверждает GH Beam отдельным writer и отсутствие APA Beam allowlist | PASS [R2], blob d8c6d95c93d956954e25de98a5f38a4a69ab0cf8 |
| 14 | №2 07Z два контрааудита запрещают отождествлять Synchronise=False и глобальный freeze | PASS [R2] audits, blob 3c6173309c016cc2daca06c4b3498e5e14f18167 |
| 15 | В hourly нет новых файлов №3 за 23–24.10, последние найденные №3 датированы 20.10 | PASS GitHub hourly directory listing, **ограничено этой папкой** |
| 16 | Graphisoft AC29 build3000, Rhino7/8, 01.10.2025 | PASS [D] |
| 17 | Graphisoft AC30 build3000, 07.10.2026 — отдельный пакет, не для AC29 | PASS [D] |
| 18 | GH Roof plane polygon задаёт pitch/elevation | PASS [G] стр.28 |
| 19 | Favorite Offset from Home Story/Roof Pitch не действует для GH Roof polygon plane | PASS [G] стр.28 |
| 20 | GH Design typed outputs не принимаются обычным GH Move | PASS [G], Design Components |
| 21 | GH Design multiple input curves дают несколько native элементов | PASS [G], Design Components |
| 22 | Rhino8 SR25 (8.25.25314) исправляет Mesh Colors cache comparison RH-89804 | PASS [S25] 11.11.2025 |
| 23 | Rhino8 SR26 (в посте 8.25.25349) исправляет Surface/Curve orientation RH-89952 | PASS [S26] 16.12.2025 |
| 24 | Rhino8 SR26 исправляет Material Content Note/Tag serialization RH-89951 | PASS [S26] 16.12.2025 |
| 25 | Rhino8 SR26 исправляет Sweep1 regression RH-90489 после SR25 изменения | PASS [S25]/[S26] |

**Ограничение доказательств:** Graphisoft GC.pdf большой (22+ MB) и не скачан локально; проверены индексированные фрагменты официального PDF, а не бинарный checksum. GitHub report №3 20.10 18Z является устаревшим по отношению к текущему часу; это не независимый аудит данной работы. Исторический PROJECT_PLAN rev182 в данном проходе не найден по предполагаемым путям и не изменён.

## 3. Два собственных контрааудита №1 (не независимый №3)

**A. «Одинаковые Favorite Roof Pitch и Home Story обеспечивают одинаковую кровлю GH и PR74» — ОПРОВЕРГНУТО.** Graphisoft AC29 GH Roof plane polygon определяет уклон/высоту; Favorite pitch/offset игнорируются. PR74 требует отдельный pivotLine/Basic/material и привязку этажа. Равенство исходных параметров не доказывает равенство native roof plane/pitch/height/host/SEO/GUID. **Критерий будущего допуска:** read-only native readback всех полей и одного owner; сейчас NOT_RUN.

**B. «Rhino Content Cache Push надёжно замечает все изменения, если Object ID не меняется» — ОПРОВЕРГНУТО для неподтверждённых старых SR.** В официальных SR25/SR26 явно исправлялись пропущенные Mesh Colors, Curve/Surface orientation и Material Content Note/Tag serialization; Sweep1 имел регрессию. Rhino Object ID/Cache tracking сам по себе не гарантирует сохранение геометрии/метаданных и не распространяет их в Archicad. **Критерий будущего допуска:** Rhino SR pin, compare orientation/colors/material tags/geometry, AC native readback после отдельного разрешения; сейчас NOT_RUN.

## 4. Адресное поручение исследователю №2 / критерий ГОТОВО

1. **I0802-01/02 (P0):** единая SOURCE-only таблица маршрутизации «операция → Rhino/GH/AC инструмент → входная геометрия → число элементов → owner → выходной BIM-тип → запрещённые преобразования». Отдельно GH Roof planar plane vs PR74 pivotLine, typed GH Design outputs vs GH Move, one-to-many. ГОТОВО: все несовпадения явно STOP, без второго writer.
2. **I0802-03/04/05:** read-only матрица «Rhino8 SR → cache update fields»: Mesh Colors RH-89804, orientation RH-89952, Material Note/Tag RH-89951. ГОТОВО: версия SR UNKNOWN в локальной среде; поля не смешаны с AC Building Material/Surface/GUID.
3. **I0802-06:** будущий (НЕ запускать) reproducibility gate для Sweep1: SR pin + input/output geometry hashes и native roof semantic checks. ГОТОВО: без заявления Multi-plane native support.
4. **BUILD-01 G0–G5:** G0 runtime identity unknown, G1/G2 не повышать по SOURCE, G3 запрещён, G4/G5 не запускались. GH-owned операции допускаются только после отдельного согласования и только для GH-owned элементов, APA-owned — только SceneWriter. No automatic triad sync claim.

## 5. Первичные ссылки и границы

- BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- PR74 pinned code: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py
- GH AC29 User Guide: https://help.graphisoft.com/AC/29/INT/GC.pdf
- Graphisoft AC29 add-on download: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- McNeel SR25: https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/32
- McNeel SR26: https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/34
- №2 07Z: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-24T07Z-report.md
- №3 last read: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-B.md
- TRIAD-PIVOT: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
- Matrix: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
- NEXT: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md

**Запреты:** main, код, PLN/APX, установка/обновление ПО, LIVE, Work/Codex/Arena, платные API, merge, новый writer/router/synchronizer — НЕ выполнялись. Публикация допустима только explicit create_file(branch) → fetch_file(branch) → fetch_file(commit SHA) → exact content equality + Git blob SHA. При ошибке WRITE_BLOCKED. MODEL_MODE_NOT_VERIFIABLE.
