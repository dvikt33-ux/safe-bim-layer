# APA-P70.A02.S01 — семантическое архитектурное задание и GetStories-only разрешение этажей

**Тип результата:** OFFLINE_PASS + SOURCE_VERIFIED · **Дата:** 2026-10-11 · **Task:** APA-P70.A02.S01.  
**Исходная ветка:** [draft PR #40](https://github.com/dvikt33-ux/safe-bim-layer/pull/40) `feature/apa-semantic-brief-story-resolution-20261011`, основана на проверенном PR #35; `main`, проверенные ветки, PLN, APX не изменены.

## Что реализовано

**Два режима в единственной существующей точке входа:** `scripts/archicad_project_accelerator.py::compile_project_brief` делегирует лёгкому `archicad_semantic_brief.normalize` и (только по желанию клиента) read-only `resolve_stories`. Это *не* второй BIM-компилятор/граф/SceneWriter и не имеет Create/Modify команд.

- `GENERATE_FROM_ZERO`: валидирует intent нового проекта. Без созданного и открытого PLN возвращает `NEEDS_NEW_PROJECT_SETUP`, **не** придумывает этажи и **не** создаёт новый PLN автоматически.
- `ADAPT_EXISTING`: требует **точный абсолютный путь .pln** единственного активного проекта; чтение `GetProjectInfo` → `GetStories` и bind по уникальным, явно ожидаемым named stories, floorId, levels. Поддерживает реальные native indices **0, 1 или любые другие**. Конфликты/недостающие этажи → `NEEDS_STORY_RESOLUTION`, без скрытого переименования/переключения проекта.
- Архитектурный первый наземный уровень — **«1 этаж» на ±0,000 м** (проверяется валидатором). Название `0 этаж` отклоняется как неверная трактовка архитектурной нумерации. `floorIndex` не выводится из имени.
- Семантическая структура: `projectId`, `mode`, `siteId` и `region`, именованные этажи/отметки, комнаты (ID/имя/этаж/minAreaM2), ограничения (ID/текст/evidenceStatus).
- В этой стадии статус ограничений допускается **только `UNVERIFIED`**. Источники и применимые СП/ГОСТ должны пройти отдельный P70.A02.S02; пользовательская строка `SOURCE_VERIFIED` без проверенного доказательства не создаёт нормативный PASS.
- `existingNativeLabel` позволяет владельцу явно сопоставить название существующего этажа с архитектурным (например `Первый Этаж` → `1 этаж`), без изменения исходного PLN. Смена projectPath, `.bpn`, относительные Windows пути, повторные floorId/index, дубли/невалидные rooms и ложные normative marks отклоняются.

## Source-backed интерфейс и будущая композиция

| Контракт | Состояние на SHA/PR | Следующий потребитель |
|---|---|---|
| `compile_project_brief(brief, read_api=None)` | **Код + tests на PR #40**. Два режима, typed normalization, safe GetStories mapping; никакого access token и native writer | **P70.A02.S02/S03** — verified applicable requirements, Building Material/Composite/Favorite/PLP |
| `compile_intent` / `run_project` | **Поведение не изменено**; по-прежнему принимает fixed `pavilion-frame-v1` и `building-shell-v1` в одном компоненте, а не произвольную комнатную модель | P70.A03.S01/S02 — связать approved brief/rooms/structural axes → существующий DAG и один SceneWriter |
| `RUN.SceneWriter` и `GetDetailsOfElements` | **Не изменены и не задействованы** этим S01. Live 25-element scratch success — другое уже опубликованное доказательство | P70.A03.S02/S03 — разрешённый live diff/update с сохранением GUID |

Важно: parser contract не представляет собой готовое создание нового проекта или редактирование существующего. Именно эту границу устанавливал S03, поэтому не объявлять `GENERATE_FROM_ZERO` / `ADAPT_EXISTING` product LIVE_PASS. Не повторять уже пройденный 25-element smoke без регрессии.

## Проверка качества

- [PR #40](https://github.com/dvikt33-ux/safe-bim-layer/pull/40) — **draft, не merge**; исходники и tests в отдельной новой ветке.
- [CI #38154611226](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38154611226) — **SUCCESS, 219/219 offline unit tests**. Первичный прогон [#38154488040](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38154488040) тоже PASS 219/219, затем затянуты ограничения безопасности.
- Новые 12 тестов: генерация без ложных native bindings; ADAPT_EXISTING без открытого PLN; произвольные native story indices (0 и 1); явное сопоставление названий; exact path, missing story, invalid first floor level/name, room assignment, normative status, ambiguous story ID; regression старого `compile_intent`.
- `nativeWriteCalls=0`, Archicad/PLN **не запускались/не открывались** из этого CI. No claim of BUILD/LIVE performance, material coverage, roof, normative engineering readiness.

**Вывод:** S01 source+offline acceptance для *семантического контракта* выполнена, интерфейс S03 сохранён. **Следующий existing S-ID:** `APA-P70.A02.S02` — вернуть требования с версией/применимостью/доказательством и pass/fail/not-verified без самопровозглашённого approval. Затем `P70.A02.S03` — проектные атрибуты и CSE/PLP. Нет оснований создавать новый P/A/S или переписывать BIM pipeline.
