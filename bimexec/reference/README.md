# BIMEXEC v1 — рабочий скелет P0

> **ГРАНИЦА СРЕД (важно).** Этот каталог — среда Arena (Linux), а НЕ
> `C:\Users\Admin\Documents\BibimMcpRouter`. Скелет считается
> **спецификацией и тест-стендом**, а не частью рабочей системы. Он не
> подключён к production Router и не должен быть подключён до получения
> фактической capability matrix.
>
> Скрипты, которые запускаются на реальном Archicad 29, — в `tools/win/`
> (`probe_t0a.py` — read-only, `probe_t0b.py` — первый controlled write).
> План, ожидаемые выводы и go/no-go: **`tools/win/T0_PLAN.md`**.

Минимальный production-safe каркас: stdlib only, без БД и внешних зависимостей.
Назначение — быть исполняемой спецификацией, а не готовым продуктом: здесь
закодированы инварианты из `BIMEXEC_P0_review.md`, чтобы их можно было проверить
тестами до первого реального write в Archicad 29.

```
bimexec/
  journal.py    WAL: append-only JSONL, fsync до dispatch, оторванная запись
  states.py     4 машины состояний; недопустимый переход = исключение
  lock.py       singleton процесса (flock) + single-flight
  binding.py    маркер BX:<job>:<object-id>:<nonce>, identity/state fingerprint
  verify.py     capability gating, mandatory floor, агрегация вердиктов
  executor.py   шаг операции, recovery, reconcile, resume
  adapters.py   протокол адаптера + имитация с инъекцией реальных классов отказов
tests/test_p0.py   31 тест
```

Запуск:

```bash
python3 tests/test_p0.py      # 31/31
```

---

## 1. Что реализовано

| Инвариант | Где | Как проверяется |
|---|---|---|
| **I1** WAL до dispatch | `journal.py`, `executor._dispatch` | `journal_is_complete_and_monotonic` |
| **I2** single-flight, singleton, без автоповтора | `lock.py`, `_dispatch` | `single_flight_refuses_second_mutation`, `process_singleton_refuses_second_instance`, `no_automatic_retry_after_unknown` |
| **I3** halt при любом не-OK/UNKNOWN | `_step`, `_assert_no_unresolved` | `unresolved_operation_blocks_further_mutation`, `halt_inside_package_protects_dependents` |
| **I4** ответ create не доказательство; только round-trip маркера | `_marker_phase` | `create_returns_wrong_guid_does_not_tag_foreign_element`, `marker_silent_noop_is_detected` |
| **I5** VERIFIED_OK только при ≥2 независимых путях | `verify.evaluate`, `_observe` | `single_independent_path_downgrades_to_inconclusive` |
| **I6** mandatory floor из конфига, не из плана | `verify.MANDATORY_FLOOR` | `validation_rejects_empty_verify`, `..._narrowed_floor`, `..._contradicting_params` |
| **I7** зависимость удовлетворяется только COMPLETED | `PkgState.satisfied`, `_pkg_ready` | `halt_inside_package_protects_dependents` |
| **I8** identity/state fingerprint | `binding.py`, `_precheck` | `binding_mismatch_halts`, `host_geometry_drift_is_caught_before_dependent_op` |
| **I9** mapping читаем только в CONFIRMED/ADOPTED | `MapState.readable`, `_precheck` | `partial_dependency...`/`host_...` |
| **I10** orphan registry, без автоудаления | `_register_orphan` | `marker_write_unknown_is_own_failure_mode` |
| **I11** PAUSED_RECOERGY + reconcile + resume | `recover`, `reconcile`, `resume` | `create_applied_but_timeout_then_recovery` |
| Capability gating до dispatch | `verify.validate_verify_spec` | `validation_rejects_unsupported_check`, `..._non_production_safe_op` |
| Дубли от прошлых запусков | префиксный поиск | `duplicate_from_previous_run_is_ambiguous` |
| Идемпотентность доставки | `_dispatched` из journal | `repeated_delivery_does_not_redispatch` |

## 2. Классы отказов, воспроизведённые в имитации

| Тест | Что имитирует | Источник |
|---|---|---|
| `marker_write_unknown_is_own_failure_mode` | `SetPropertyValuesOfElements` → `Teamwork Permission Denied` на Solo; применилось, ответа нет | задокументированный баг API |
| `marker_silent_noop_is_detected` | write вернул ok, значение не записано | `SetDetailsOfElements` молча дропает поле |
| `readback_broken_after_marker_halts` | read-команды падают, write работает (AC29) | Tapir issue #659 |
| `create_applied_but_timeout_then_recovery` | таймаут ПОСЛЕ применения | базовая ситуация UNKNOWN |
| `create_returns_wrong_guid_does_not_tag_foreign_element` | create вернул чужой GUID | риск из решения №2 |
| `duplicate_from_previous_run_is_ambiguous` | элемент от прошлого UNKNOWN-запуска | требует префиксного поиска |

## 3. Что намеренно НЕ реализовано

- Реальный адаптер Archicad (только протокол + имитация). Capability matrix
  должна заполняться probe'ом на живом Archicad, а не из документации.
- `change` / `move` / `rotate` / `delete` / `bulk` — вне scope v1, валидатор их
  отклоняет по `allowed_ops`.
- Компенсации и транзакции: orphan регистрируется, автоматически не удаляется.
- Сохранение PLN — вне scope по принятому решению.
- Планировщик: порядок массива обязан быть топологическим, это проверяется
  на валидации (`validation_rejects_forward_dependency`).
- Автоматическая уборка orphan, `ensure_*` upsert-семантика, object-level DAG,
  параллелизм, семантическая верификация — v2.

## 4. Что вскрылось при реализации (важнее кода)

**4.1. `PARTIAL` недостижим как состояние зависимости.** При последовательном
исполнении job останавливается *внутри* пакета, и зависимый пакет не стартует
вообще. То естьdependents защищает не dependency engine, а сам halt. Правило
«PARTIAL не удовлетворяет зависимость» остаётся корректным, но в v1 оно
страховочное: реальный барьер — `Halted` + `PAUSED`. Тест
`halt_inside_package_protects_dependents` фиксирует именно фактическое поведение.

**4.2. Дешёвый fingerprint не ловит геометрический дрифт.** `state_fingerprint`
= счётчики по типам + состояние слоёв + множество GUID (1–2 read-вызова на шаг).
Он ловит добавление, удаление и Ctrl+Z, но **не** ловит «элемент подвинули»:
состав модели не изменился. Для v1 с операцией `create` это закрывается целевой
перепроверкой host-элемента перед зависимой операцией (`host_wall`), а не
глобальным хэшем геометрии — тот стоил бы O(n) вызовов `GetDetailsOfElements`
на каждый шаг. Если пойдёте в `change`/`move`, это решение придётся пересмотреть.

**4.3. `count_delta` неприменим к усыновлению.** При ADOPTED элемент уже был в
модели, дельты нет — проверка снимается для этой ветки, дубли ловит префиксный
поиск. Мелочь, но она ломает наивную реализацию ensure-ветки.

**4.4. `exists` нельзя доверять плану.** Проверка существования — структурная
предпосылка, поэтому она вынесена в `IMPLICIT_CHECKS` и требуется Router всегда,
независимо от содержания `verify_spec`.

## 5. Порядок подключения к реальному Archicad

1. Реализовать адаптер по протоколу из `adapters.py` (BIBIM / Tapir / MCP).
2. Probe: заполнить capability matrix **эмпирически**, включая 5 инфраструктурных
   строк — запись маркера, поиск точный, поиск префиксный, read-back по GUID,
   read-back по фильтру, подсчёт по типу.
3. Прогнать `tests/test_p0.py` на имитации (должно быть 31/31).
4. T0 capability probe на одноразовом PLN. Если маркера нет или он не читается —
   стоп, binding-протокол нереализуем.
5. T2 одна стена по рецепту из раздела 6 обзора P0 (`from [1.5,2.5] → to [6.5,2.5]`,
   length 5.0 ≠ height 3.0 ≠ thickness 0.30, пустой этаж, радиус 3 м свободен).
6. T3–T7 инъекции отказов на живом Archicad.
7. Только потом — второй тип элемента и второй пакет.

---

## 6. Capability probe (T0) — добавлено

`bimexec/probe.py` + `bimexec/tapir_raw.py` + `tools/run_probe.py`.

```bash
python3 tools/run_probe.py                          # read-only
python3 tools/run_probe.py --allow-write --out caps.json
python3 tools/test_all.py                           # 45 тестов
```

Код возврата: `0` — сертифицировано, `1` — не сертифицировано, `2` — нет подключения.

**Что probe делает:**

| Фаза | Проверки |
|---|---|
| Read-only | подключение, identity проекта, этажи (имя+отметка), счётчики по типам, список GUID, `GetDetailsOfElements`, поиск по фильтру, чтение маркера, **негативный контроль поиска** (несуществующий маркер → ровно 0) |
| Write (по `--allow-write`) | создание стены, поля read-back, `count_delta`, **round-trip маркера**, поиск по маркеру, **негативный контроль верификации** (корректное ожидание → OK, сдвинутое на 0.5 → FAILED) |

**Негативные контроли обязательны.** Поиск несуществующего маркера обязан вернуть 0 — если адаптер вернёт «всё» или ошибку, binding-протокол не работает, и это выявляется до первого write. Проверка верификации должна уметь сказать FAILED — иначе «проверка прошла» ничего не доказывает.

**Fail closed:** без write-фазы `marker_write_roundtrip` остаётся `SKIPPED`, capability не сертифицируется, `CapabilityMatrix.from_probe_report()` не включает её в матрицу, и `Executor` отказывает по `OUT_OF_SCOPE`.

**Деградация вместо «ок»:** если адаптер не умеет префиксный поиск, probe сообщает `duplicate_detection = EMPTY_SCOPE_FALLBACK`, и исполнитель переключается на предусловие «чистая область» на входе в пакет (`_assert_scope_clean`): в области (тип, этаж, слой) не должно быть элементов, не привязанных к этому job.

**Мост `ExecutorAdapter`.** Один raw-адаптер реализует протокол `probe.RawArchicad`; `ExecutorAdapter` адаптирует его к протоколу исполнителя. Две разные обёртки над одним Archicad = две разные правды о его возможностях. См. `bimexec/tapir_raw.py` — таблица `COMMAND_NAMES` единственное место, где править имена команд под вашу сборку, схемы `CreateWalls` помечены как TEMPLATE.

### Известные честные дырки

- **`get_layer_state()`**: мост возвращает `known=False`, если адаптер не умеет сообщать состояние слоёв, и исполнитель тогда **не** применяет предусловие по слою. Это дырка, а не «слой в порядке».
- **`find_by_marker` в `TapirRaw`** реализован сканированием всех элементов (O(n)). Для v1 приемлемо, для больших моделей — узкое место.
- **Носитель `property`** требует, чтобы свойство `BIMEXEC/BIMEXEC_MARKER` уже существовало: официальный JSON API не умеет создавать свойства. Probe честно сообщит `NOT_SUPPORTED`.
- **Probe не удаляет артефакты**: delete вне scope v1, поэтому список артефактов печатается для ручной уборки.
