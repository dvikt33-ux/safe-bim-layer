# APA-P70.A01.S03 — утверждение границ интеграции рабочего ускорителя

**Run:** `APA-RUN-20261011-160327Z-p70-a01-s03-integration-freeze` · **Дата:** 2026-10-11 · **Фаза:** SOURCE · **Исполнитель:** GPT-6 в обычном чате, GitHub connector.  
**Авторитет задач:** `PROJECT_PLAN.json`, ревизия 57 при claim; эта публикация не создаёт конкурирующего плана или writer.  
**Результат:** **SOURCE_DECISION_ACCEPTED** для архитектурных границ. Ни новый исполнитель, ни поддержка редактирования чужих проектов не реализованы этим отчётом. Синтетические тесты и пользовательские live-логи маркируются отдельно.

## 1. Приёмка D0: фиксируем ОДИН путь

```text
Один JSON/TZ input (archicad-project-intent/1)
  └─ scripts/archicad_project_accelerator.py::compile_intent
     ├─ capability gating: существующий capability-registry + ReadAdapter
     ├─ story/attribute resolver: GetStories + existing template_builder READ-ONLY donors
     ├─ component adapters (building-shell-v1, pavilion-frame-v1; следующие по мере приёмки)
     └─ scripts/archicad_bim_graph.py::compile_graph (ONE DAG, hosts/dependencies/order)
        └─ scripts/archicad_scene_run.py::SceneWriter (ONE guarded native writer)
           └─ Tapir 1.5.10 / proven native API gap adapters
              └─ native typed GUID/story/geometry/material/host readback
                 └─ evidence + separate Save As/reopen verification
```

Это **архитектурный контракт на последующие стадии**, а не утверждение, что все блоки уже соединены. Все Create/Modify должны проходить существующий writer и журнал; другие исполнительные модули — *доноры функций*, а не параллельные независимые точки записи.

## 2. Source-proven reuse map (актуальная ветка PR #35)

| Обязанность | Единственный хозяин / source SHA (Git blob) | Что доказано сейчас | Нужная минимальная дельта, без дублирования |
|---|---|---|---|
| Ввод и единый runtime orchestration | `scripts/archicad_project_accelerator.py` `59dadabf664326d8401a2514c5fd7436b7657cbb` | `compile_intent`, `run_project`; **ровно один** компонент, только pavilion или shell; old create-only mode | Поддержать typed project brief и несколько элементов/компонентов через существующий компилятор; не заводить `new_house_compiler.py` |
| Проверка доступности | `scripts/archicad_accelerator_integration.py` `b4efd579d5acc723439a1553e79b4a4b1c0074cd` | `require_capabilities`, `ReadAdapter`, исходники и dump; current `run_integration` offline/preflight only | Связать с единым входом; провайдер не получает права записи по одному только наличию schema |
| Единый BIM DAG | `scripts/archicad_bim_graph.py` `fc68f82b1d0cf89d5d4576ac03225572a6ffadf2` | Валидация команды, host `$createdGuid`, зависимости, топосортировка, fit/overlap проёмов | Ввести отдельные semantic-room/axis/structure ограничения как входные валидаторы этого DAG, а не второй graph |
| Типовая оболочка | `scripts/archicad_building_shell.py` `4e03a0143e62a416c1682129fefd4fab829c9e47` | 10×8 м, 2 named stories, 25 создаваемых сущностей для конкретного ограниченного примитива | Расширять существующие типизированные компоненты по необходимости, не подменяя архитектуру fixed `roomBays` |
| Единственная запись | `scripts/archicad_scene_run.py` `7905cfa237ec989da31b527aa931dd7f4663504e` | `SceneWriter`, точный PLN guard, durable SQLite до каждого native Create/Modify, typed readback; no replay; после ошибки GUID reconciliation | Вынести из одноразовых incident scripts обобщаемые proven `resolve existing GUID / resume only absent` и typed slab update *в тот же* SceneWriter. Не переносить hardcoded GUID/путь истории в общий runtime |
| Проектные атрибуты | `scripts/archicad_template_builder.py` `eadef8875372578609985edbd30ceced5075d4e8` | `get_fill_runtime_index`, `material_dependency_plan`; read-only поиск/зависимости BM/Fill/Surface | Адаптер semantic role→unique active-project Attribute GUID/Composite/Favorite; неоднозначность→BLOCKED, никакой копии каталога |
| Доноp slab material | `scripts/archicad_executor.py` `efbaf139c4a6707226a2e6bbe07a7cc9f5fafa28` из `feature/working-archicad-mvp` | Ранее известен `CreateSlabs` → `ModifySlabs` Basic/BM | Встроить только при подтверждении installed schema; native Create→Modify **не атомарен**, обе операции — durable intent before call |
| Инцидентное восстановление и независимый saved-copy readback | `scripts/continue_apa_after_orphan_partition.py`, `scripts/verify_apa_saved_copy_read_only.py`, PR #35 | Пользовательские живые логи: **25/25 native entities**, 45/45 total GUID, `.bpn` отклонена guard, затем exact `.pln` passed; CI #38150899253 207/207 synthetic/offline | Считать подтверждением **конкретного scratch 25-element scene**, не универсального multi-story компилятора или штатного `ADAPT_EXISTING`. Не повторять эти smoke-тесты без найденной регрессии |

**Историческая корректировка:** S01 и исходный предложенный roadmap писались до доказанного live 25/25 и saved-copy readback. Эти старые записи `LIVE NOT VERIFIED` относятся к тогдашнему состоянию. Текущая версия PR #35 и пользовательские source-safe логи повышают *только узкий shell slice*, а не всю P70.A03.S02.

## 3. Минимальные интерфейсы, которые нужно соблюдать

1. **Ввод:** `project_intent = {schemaVersion, projectId, units='meters', components[]}` — сохранять проектный hash, immutable authored intent, режим `GENERATE_FROM_ZERO` или `ADAPT_EXISTING`. Режимы — **планируемые**, существующая реализация `run_project` пока их полностью не поддерживает.
2. **Проектный контекст:** один открытый PLN; `GetProjectInfo`, `GetStories`, Tapir/installed Add-On identity, role→attribute GUID, project snapshot. User-visible architectural "1 этаж" ≠ native `floorIndex=1`: на текущем тесте floor label 1 может соответствовать native index 0. Не сканировать или переключать другие файлы.
3. **Операционный план:** детерминированные step ID/semantic entity ID, `{id, command, params, after?}`, topological host refs `$createdGuid`, BIM graph hash и binding story/project; неизвестная геометрия/отсутствующий атрибут блокируют соответствующую запись.
4. **Executor contract:** один `SceneWriter` с durable scene+step reservation **до** native вызова. Никакого blind retry после timeout. Сначала reconciling existing GUID; новый план может создавать только отсутствующее, затем readback по каждому изменённому элементу. Короткие donors не имеют самостоятельного права писать в защищённый PLN.
5. **Typed evidence:** GUID/type/story/global Z, ends/polygon/thickness, BM/Composite/Surface provenance, ownerWall GUID для дверей/окон; исходный 20-GUID inventory и итоговый 45-GUID test — отдельный зафиксированный факт, не универсальная метрика.
6. **Пользовательское управление:** один высокий уровень `Build/Update/Inspect` с одним точным approval на набор операций, без ручных 5 JSON/token/GUID для каждого шага. Прямой ChatGPT→localhost transport **NOT_VERIFIED** и не часть ближайшей поставки.
7. **Сложные алгоритмы:** HOT/WARM/COLD, Coverage Signature, provider arbitration, CSE, инженерию и тяжёлую оптимизацию подключать лениво после действующего редактируемого MVP; не ставить 104 MB dump, LLM или повторный нормативный поиск на путь каждого Wall Create.

## 4. Ближайшие поставки: сохраняем controller DAG, не создаём второй roadmap

| Порядок | Существующий S-ID | Измеримый результат и достаточный gate |
|---|---|---|
| **Сейчас — D0** | **P70.A01.S03** | Этот принятый interface/reuse contract, source SHA, точная граница одной точки записи, verified GitHub publisher receipt и controller readback |
| **Следом — D2 вход** | **P70.A02.S01** | Реальный типизированный building brief: участок, named story / level и `GENERATE_FROM_ZERO` vs `ADAPT_EXISTING`, без фиктивного нулевого архитектурного этажа; offline positive/negative, no native write |
| **Затем** | **P70.A02.S02 / S03** | Минимально достаточные атрибуты и CSE/PLP для 1 сценария; source/version/applicability и unknown→BLOCKED |
| **Модель из задания** | **P70.A03.S01 → S02** | Semantic rooms/axes/host/structural constraints→same DAG→same writer; одно реальное здание, а не только фиксированный box; не начинать S02 по DAG до завершения S01 |
| **Инкрементальный edit** | **P70.A03.S03** | Изменить 10→12 м и 1 проём в disposable PLN, **сохранить существующие GUID**, создать/изменить только delta; typed readback & separate Save As/reopen |
| **После core** | **P70.A04–A08** | Roof/footing/stairs/detail→MEP/engineering→drawings/IFC/PDF; отдельные engineering/normative gates |

**Не делать сейчас:** очередной ручной визуальный smoke-test тех же 25 элементов, третий generic writer, переписывание компилятора с нуля, повторное создание тестового PLN, инфраструктурную перестройку вместо предметного изменения.

## 5. Решение аудита / критерии принятия

**Принято:** reuse архитектуры; границы D0–D6 существующего roadmap согласуются с единственным controller. Узкие incident tests live-прошли в user logs, 25-step saved-copy typed readback воспроизводится по точной ветке PR #35. Доказано source (GitHub blob SHA), что typed semantics и append-only journal exist.

**Отложено до своих S-ID:** реализация multi-component/ADAPT_EXISTING, semantic attribute adapter, generic incremental Modify, roof and structural semantics. Предлагаемые будущие AI/Ci/Husky providers не заменяют принятую AC29/Tapir reference реализацию до отдельной capability parity. Нет подтверждённого benchmark speedup, distributed transaction или product-level LIVE PASS.

**Acceptance P70.A01.S03:** контракт `input → attribute/story resolver → one BIM graph → one SceneWriter → Tapir/native → readback` определён; определены владельцы интерфейсов/исходники с SHA, предотвращено логическое дублирование; обеспечена однозначная последовательность приёмочных ворот и сразу следующий eligible substep P70.A02.S01. **No source/PLN/APX/main mutation.** Результат этого SOURCE-аудита не означает live-внедрение всего product pipeline.
