# APA №2 — 23.10.2026 14Z — BUILD-01: проверяемый GH→JSON→PR74 без нового writer

## Новый вклад в G1/G2: найден готовый кандидат на БЕСКОДОВУЮ передачу параметров Rhino/Grasshopper в существующий APA (P=99/100)
Предыдущий статус «произвольный GH-output→PR74 typed DAG NOT_FOUND» уточнён: **появился воспроизводимый SOURCE-кандидат на перенос ограниченных типизированных параметров**, но не доказанный универсальный готовый транслятор.

- **jSwan**, Andrew Heumann, MIT, индексируемая версия **1.2.1 (03.10.2020)**: Grasshopper компоненты `Serialize JSON`, `Serialize Keys and Values`, `Merge JSON`, `Deserialize JSON`. Автор описывает формирование вложенных объектов и управление `Item/List access`, `Lock Structure`. Источники: https://github.com/andrewheumann/jSwan ; https://grasshopperdocs.com/addons/jswan.html ; https://grasshopperdocs.com/components/jswan/mergeJson.html
- **Штатный Grasshopper Panel → Stream Contents / Stream Destination** может выгружать **один текстовый JSON-объект** в промежуточный файл. Не нужен новый file writer. Подтверждение функции: https://smorgasbord.cdp.arch.columbia.edu/modules/5-computational-design-modeling-in-grasshopper/5-7_design-space/ ; handbook https://gdocu.upv.es/alfresco/service/api/node/content/workspace/SpacesStore/9e7ef2af-c4da-4fdb-b4ca-0d2a5fe970f2/TOC_0270_03_01.pdf?guest=true
- **Существующий PR74** уже принимает JSON `--intent` и имеет схему `apa-authored-project/1`, обязательные `projectId,units,brief,cseCandidate,layout,storyHeights`; `nativeComponents` опциональны. Внутри: `compile_authored_intent` → `compile_candidate` → BIM Graph → SceneWriter/SQLite. Источники: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py, https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_native_plan.py, https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/examples/accelerator/model-first-building.json.
- **Граница:** jSwan 1.2.1 старый; **Rhino8 compatibility NOT_VERIFIED**, локальная установка отсутствует; Panel Stream пишет при пересчёте и может перезаписать незавершённым содержимым. Нельзя направлять stream непосредственно на разрешённый вход выполнения или SQLite. GH сам не запускает PR74, не создаёт нативный GUID и не синхронизирует три приложения. Для произвольных NURBS→native Roof/всех BIM-типов универсальный no-code mapper **NOT_FOUND**.

### Минимальный маршрут, без программирования и без нативной записи (ещё НЕ ИСПЫТАН)
1. В Rhino8/GH создать **геометрические параметры**: контур XY, толщины, отметки, оси стен, положения проёмов. Зафиксировать единицы **meters**, системы координат и типы данных. Источник проекта — отдельно утверждённая новая scratch PLN.
2. В GH из **заранее подготовленного полного `apa-authored-project/1` шаблона** получить JSON через jSwan `Deserialize JSON` / `Merge JSON` / `Serialize JSON`; менять только разрешённые `layout`, `storyHeights`, `nativeComponents` и иные явно разрешённые поля. Сохранять `brief.projectId == projectId`; `brief.targetProjectPath == RUN.EXPECTED_PATH`. Существующие story/material/GDL bindings не угадывать.
3. Подключить **один JSON string** к Panel, `Stream Destination` = отдельный **staging** `.json`; на завершении GH расчёта остановить поток (`Stream Contents OFF`). Учитывать, что Panel перезаписывает файл на изменении: это НЕ commit/transaction.
4. **До выполнения** независимо проверить JSON parse, типы, обязательные ключи, массивы/вложенность, отсутствие NaN/Inf, `projectId`, `targetProjectPath`, актуальные этажи/материалы, SHA256 файла и отсутствие незавершённого streaming. Передать immutable copy существующему CLI `--intent ... --schema ... --output <new> --isolated-port <approved> --preflight`. Этот preflight делает READ из реального Archicad и НЕ равен `OFFLINE_PASS` без фактического запуска.
5. Только отдельное разрешение G3: `--execute --run-id ... --confirm-plan-hash ... --data-dir <existing-ledger>`, единственный writer SceneWriter, GH Design Synchronize=FALSE для APA-owned. После native GUID/BREP readback → GuardedSave/Close/Reopen → независимый readback. UNKNOWN → STOP + READ-only reconcile, **никакого повторного CREATE**.
6. На **другом** задании и новой scratch PLN повторить G0–G5, не перезаписывая старые receipts.

### Два дополнительных барьера, выявленных непосредственно из кода
**G1: compiled authored ≠ pure offline.** `run_project` запрещает authored-intent `mode=offline` и требует callable native READ transport (`AUTHORED_NATIVE_REQUIRES_EXPLICIT_READ_ONLY_PREFLIGHT`). Поэтому GH→JSON может быть создан автономно, но авторская компиляция G1 не получает `OFFLINE_PASS` до READ-only Archicad preflight. Более того `evidenceKind='LIVE'` у `--preflight` не является native CREATE. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py.

**G2: шаблон жёстко привязан к проекту.** `compile_authored_intent` сравнивает `brief.targetProjectPath` с `RUN.EXPECTED_PATH`; `compile_candidate` требует **точного** `nativeStoryBindings`, актуального material GUID, согласованной высоты/уровня. Простая передача GH координат без этих полей будет отклонена. Это правильный защитный контракт, а не ошибка GH. Источники: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py, https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_native_plan.py.

## Официальная связка и ownership
Graphisoft AC29 Grasshopper Live Connection **build 3000, Windows 16.8 MB, 01.10.2025, Rhino7/8**, источник https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ . **AC30 build3000 — ДРУГОЙ installer.** Бесплатное дополнение не заменяет лицензии Rhino/Archicad. **Фактическая совместимость с AC29 build5101 и installed APX Tapir1.5.10 NOT_VERIFIED**.

Два допустимых раздельных ownership:
- **APA-owned** Walls/Slabs/Roof/Doors/Windows: GH геометрический preview/JSON staging; **SceneWriter единственный native writer**; GH AC Design `Synchronize=FALSE`.
- **GH-owned** экспериментальные элементы только на отдельно разрешённой scratch модели: GH AC Design/Document может писать напрямую, но это **другой writer**, не доказанный общий ledger/GUID. Не использовать для строгого BUILD-01.
- **AC→GH** Deconstruct/Parameter/Send Changes — выборочная ассоциативная READ-связь; не универсальная AC↔GH↔Rhino native roundtrip. SinglePlane Roof Deconstruct возможен; сложный MultiPlane — ограничен. GH `Synchronize=FALSE` возвращает Null и не является preview нативного элемента. Rhino preview создавать **геометрическими GH компонентами**, а не AC Design.

## G0–G5 / доказательность
| Gate | Вывод |
|---|---|
| G0 | BLOCKED_RUNTIME: локальные APX/SHA, loaded command inventory, AC29 build5101, Rhino8 license, GH add-on и scratch PLN не проверены |
| G1 | SOURCE_CANDIDATE: no-code GH→JSON staging; обязательный read-only authored preflight НЕ выполнен |
| G2 | SOURCE_ONLY: стены/плиты/балки/колонны/простая кровля/проёмы по pinned schema; Slab CREATE не задаёт Basic/material, нужен отдельно разрешённый MODIFY; Beam adapter не wired; GDL expectations условны |
| G3 | NOT_AUTHORIZED: никаких native WRITE |
| G4 | NOT_RUN: GuardedSave/GUI close/reopen и независимый BREP ещё не проверены |
| G5 | NOT_RUN: второе новое задание не запускалось |

**SOURCE** = проверка первоисточников/репозитория; **OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0** в этом исследовательском проходе. Исторический 21-элементный PR74 не является новым BUILD-01. Отчёты №1 TRIAD-PIVOT 11Z и №2 13Z прочитаны; новый отдельный №3 за 23.10 по проверенным путям не найден, NEXT (20.10) прочитан. Матрица 61 прочитана: `GRASSHOPPER`=40 — оценка до triad-pivot, не статус интеграции. Исторический `PROJECT_PLAN.json rev182` не найден по проверенным путям и не менялся. 06Z PARTIAL_NOT_ACCEPTED.

**Контрааудиты** в отдельном файле; 28 SOURCE-проверок в отдельном файле. Никаких main/NEXT/code/PLN/APX/install/LIVE/merge/Work/Codex/Arena/paid API. MODEL_MODE_NOT_VERIFIABLE.
