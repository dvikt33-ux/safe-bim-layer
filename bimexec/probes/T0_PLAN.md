# BIMEXEC — план T0A / T0B

**Статус:** готово к запуску на Windows-машине.
**Редакция 2** — переписано по локальной инвентаризации от 2026-09-26.

---

## 0. Что изменилось после вашей инвентаризации

Инвентаризация опровергла четыре моих допущения. Все четыре исправлены в коде.

### 0.1 MCP-клиент был написан неверно — поэтому и был HTTP 400

Я отправлял `POST /call {"tool":..., "arguments":...}`. Настоящий MCP
streamable HTTP требует:

```
POST http://127.0.0.1:8001/mcp
Content-Type: application/json
Accept: application/json, text/event-stream     <-- обязательно оба

{"jsonrpc":"2.0","id":1,"method":"initialize",
 "params":{"protocolVersion":"2025-06-18","capabilities":{},
           "clientInfo":{"name":"bimexec-probe","version":"1.0"}}}
```

дальше: `Mcp-Session-Id` из заголовка ответа пересылать обратно, отправить
`notifications/initialized` **без id**, затем `tools/list` и `tools/call`.
Ответ может прийти как JSON **или** как SSE (`data:`-строки) — клиент умеет оба.

`McpClient` в `backends.py` теперь делает именно это, с перебором версий
протокола `2025-06-18 → 2025-03-26 → 2024-11-05` и печатью тела ошибки.
Если 400 повторится — в отчёте будет тело ответа, по которому видно причину
(версия протокола, префикс пути, заголовки).

### 0.2 `GetDetailsOfElements` отдаёт индексы, а не имена

Фактический ответ: `type`, `id`, `floorIndex`, `layerIndex`, `drawIndex`,
`hotlinkId`, type-specific `details`, `floorPlanPolygons`.

**Ни имени этажа, ни имени слоя в ответе нет.** Следствия:

- **Этаж.** Единственный идентификатор — `floorIndex`. Я предупреждал, что
  индекс как идентичность опасен (в Tapir недавно чинили баг, где `SetStories`
  использовал позицию в массиве вместо реального индекса). Теперь это не
  предостережение, а **фактическое ограничение**: имя и отметку этажа надо
  получать отдельно из `GetStories` и сопоставлять по индексу. Проверка
  `stories_index_map` в T0A требует, чтобы у каждого этажа были `index`,
  `name` и `elevation` — иначе сопоставление невозможно и верификация
  «стена на том этаже» остаётся недоказуемой.
- **Слой.** Имя берётся через property `ModelView_LayerName`. Добавлена
  отдельная проверка `layer_name_via_property`. Без неё верификация
  «стена на том слое» невозможна, а заблокированный/скрытый слой — это
  классический ложный `VERIFIED_FAILED`.

### 0.3 Префиксного поиска в Tapir нет — но это не деградация

Вы нашли: отдельной команды prefix-search по user-defined property нет; MCP
`find_elements` сужает по типу/story/classification и сравнивает значения
**на стороне клиента**.

Моя прежняя классификация была неверной: я помечал отсутствие серверной
команды как `EMPTY_SCOPE_FALLBACK` (деградацию). На самом деле клиентский
скан + `startswith` **полноценно реализует** и точный, и префиксный поиск.
Поэтому в отчёте появился корректный статус:

```
duplicate detection : SCAN_PREFIX
```

`EMPTY_SCOPE_FALLBACK` остаётся только для случая, когда прочитать значения
свойств по набору элементов вообще нельзя. Это честнее: мы не объявляем
деградацию там, где её нет.

### 0.4 Схема `CreateWalls` — совпадает с рекомендациями, но есть деталь

Обязательные поля: `begCoordinate`, `endCoordinate`, `height`, `thickness`.
Опциональные: `floorIndex`, `zCoordinate`, `offset`, `arcAngle`,
`referenceLineLocation`, `structureType`, `buildingMaterialId`,
`compositeId`, `profileId`. `additionalProperties: false`.

Это подтверждает два требования из аудита:
- `referenceLineLocation` — параметр обязателен **смысленно**. Без него
  позиция стены не определена однозначно: референсная линия по центру,
  внутренней или внешней грани даёт расхождение в половину толщины.
- `floorIndex` — этаж задаётся индексом, значит он должен быть разрешён
  **до** создания и проверен по имени + отметке (см. 0.2).

Плюс новая деталь: `offset` — это смещение референсной линии. Если
`referenceLineLocation` и `offset` не заданы явно, верификация геометрии
станет неточной. В v1 передаём оба поля явно.

### 0.5 Что закрывает T0A из вашего списка NOT FOUND

| Было NOT FOUND | Закрывает | Как |
|---|---|---|
| Версия Tapir add-on 1.5.9 не подтверждена | `tapir_addon_version` | live-вызов `GetAddOnVersion` |
| Текущий `.pln` не подтверждён | `port_project_discovery` | перебор портов + `GetProjectInfo` |
| Активный порт не подтверждён | `port_project_discovery` | то же; печатается причина по каждому порту |
| Runtime MCP `tools/list` не получен | `mcp_tools_list` | исправленный MCP-клиент; печатается inferred mode |
| Отдельный Tapir prefix-search | `tapir_native_prefix_search` | зафиксировано как NOT FOUND, поиск = `SCAN_PREFIX` |
| Property «Element ID» не подтверждено | `read_element_id` | перебор 5 кандидатов адреса, фиксируется сработавший |
| Схемы BIBIM не найдены | — | **см. 0.6** |

### 0.6 BIBIM — предлагаю считать вне scope v1

По инвентаризации: package/source не найден; имена `create_wall`,
`get_element_info`, `get_elements_by_type`, `change_element_parameter`
присутствуют **только как ожидаемые строки в router.py**. Это не доказательство
ни существования, ни схем аргументов.

Предложение: **`BibimBackend` остаётся заглушкой, BIBIM не участвует в v1.**
Write-путь и так доступен: Tapir даёт `CreateWalls` и
`API.SetPropertyValuesOfElements`, MCP (`full`) даёт `create_elements` и
`set_element_data`. Если BIBIM понадобится — реализуется свой модуль с
`BACKEND = ...` и подаётся через `--backend-module`, без правки наших файлов.

Отдельно: в режиме `full` у MCP есть `set_selection` и `clear_selection`.
Это разделяемое мутируемое состояние. **Router не должен использовать эти
инструменты никогда**, и v1 не должен зависеть от выделения: адресация
только по GUID. Если другой агент или человек поменяет выделение во время
прогона — для корректности это должно быть безразлично.

### 0.7 Главный оставшийся неизвестный

Есть ли координаты стены (`begCoordinate`/`endCoordinate`) внутри
type-specific `details`? Инвентаризация это **не подтвердила** — там указано
«type-specific details» в общем виде.

Поэтому T0A делает **сырой дамп** ответа `GetDetailsOfElements` для одной
стены и кладёт его в отчёт (`raw_dumps.GetDetailsOfElements_sample`).
Проверка `wall_geometry_endpoints` ищет координаты в нескольких вероятных
местах, но если не находит — честно пишет NO и показывает сырой JSON.
От этого проверки зависит вся верификация позиции.

---

**Кому:** выполняется оператором на Windows, из отдельной папки, а не из
`C:\Users\Admin\Documents\BibimMcpRouter`. Интерпретатор — тот, где установлен
`archicad` (`...\archicad-mcp-server\Scripts\python.exe`).
**Ничего из этого не интегрируется в production Router до результатов T0B.**

---

## 0-1. Подтверждено живьём на Windows (2026-09-26, Archicad 29)

Источник: read-only live baseline от ChatGPT/Work (PR #1). Это факты, а не
документация:

| Факт | Значение |
|---|---|
| Интерпретатор с `archicad==29.3000` | `C:\Users\Admin\AppData\Roaming\uv\tools\archicad-mcp-server\Scripts\python.exe` |
| `ACConnection.connect(19723)` | работает |
| official `commands.GetProjectInfo` | **отсутствует** (hasattr = False) |
| official `commands.GetProductInfo` | есть |
| official `commands.ExecuteAddOnCommand` | есть |
| Tapir `GetAddOnVersion` | `{'version': '1.5.9'}` |
| Tapir `GetProjectInfo` | `projectPath`/`projectLocation` = `C:\Users\Admin\Downloads\MCP_TEST.pln`, `projectName` = `MCP_TEST`, `isUntitled`=False, `isTeamwork`=False |
| Tapir `GetStories` | `firstStory=0 lastStory=2 actStory=0`; элементы несут `index`, `level`, `name` |

Следствия, уже реализованные в `backends.py`:

1. `TapirBackend.available()` проверяет доступность через read-only Tapir
   `GetProjectInfo` (и попутно `GetAddOnVersion`), а **не** через official
   `GetProjectInfo`. Раньше из-за этого T0A ложно сообщал
   `port_project_discovery = NO` и `tapir = down`.
2. `project_info()` берёт путь/имя/untitled/teamwork из Tapir, а версию и
   сборку — отдельно из official `GetProductInfo` (best effort; отсутствие
   не влияет на доступность).
3. Запускать T0A/T0B нужно тем интерпретатором, где стоит `archicad` —
   иначе бэкенд честно скажет «package 'archicad' is not installed».

---

## 0. Граница сред — важно

| Каталог | Чей | Статус |
|---|---|---|
| `C:\Users\Admin\Documents\BibimMcpRouter` | ваш, Windows | **рабочая система**. Здесь Archicad 29, BIBIM, Tapir/MCP |
| Arena / Linux (вне Windows) | Arena | **не рабочая система**. Спецификация + тест-стенд логики |

Скелет в среде Arena (Linux, вне Windows) — это исполняемая спецификация инвариантов и
45 тестов на ней. Он **не** подключён к вашему Router и не должен быть
подключён, пока T0A/T0B не дадут фактическую capability matrix. Переносить
надо **результаты** (матрицу и решения), а не код.

Скрипты T0A/T0B — standalone, Python 3.10+, stdlib (опционально `archicad`).
Они не импортируют ничего из Router.

---

## 1. Что где выполняется

| Шаг | Где | Кто |
|---|---|---|
| Установить `pip install archicad` (если используете Tapir-бэкенд) | Windows | оператор |
| Подготовить `MCP_TEST.pln` (см. §2) | Windows, Archicad | оператор |
| `probe_t0a.py` | Windows | оператор |
| `probe_t0b.py --dry-run` | Windows | оператор |
| `probe_t0b.py` (реальная запись) | Windows | оператор |
| Анализ результатов, решение по носителю | — | совместно |

На Linux-стороне эти скрипты уже прогнаны против in-memory модели:
проверены happy path и все четыре пути отказа (см. §6).

---

## 2. Подготовка `MCP_TEST.pln` (одноразовый проект)

1. Создать пустой PLN, **сохранить** под именем `MCP_TEST.pln` (не untitled).
2. Убедиться, что это **не** Teamwork/BIMcloud.
3. Разместить **одну тестовую стену** вручную, в стороне от начала координат —
   например с `[1.5, 2.5]` до `[6.5, 2.5]`, высота 3.0, толщина 0.30.
4. Присвоить этой стене **непустой Element ID**, например `W-TEST-001`.
   Это нужно не для маркера, а для позитивного контроля поиска в T0A:
   если ни у одного элемента нет заполненного Element ID, поиск нечем
   проверить, и T0A честно скажет NO вместо «наверное работает».
5. Запустить Archicad, открыть именно этот PLN, убедиться что JSON-интерфейс
   включён и Tapir/BIBIM активны.

GUID тестовой стены возьмите из вывода T0A (`capabilities.wall_geometry_endpoints.evidence.guid`)
или из `capabilities.list_guids`.

---

## 3. T0A — read-only capability probe

Запускать ВНЕ каталога production Router (например, из копии `probes`),
интерпретатором, в котором установлен `archicad`:

```bat
cd /d C:\TEMP\bimexec_t0\probes
"C:\Users\Admin\AppData\Roaming\uv\tools\archicad-mcp-server\Scripts\python.exe" probe_t0a.py --out capability_matrix.json --ports 19723,19724 ^
    --mcp-url http://127.0.0.1:8001/mcp --expect-project "C:\Users\Admin\Downloads\MCP_TEST.pln"
```

Если `python` уже указывает на окружение с `archicad`, команду можно сократить
до `python probe_t0a.py ...`.

Свой бэкенд подключается без правки наших файлов:

```bat
python probe_t0a.py --backend-module .\bibim_backend.py --backend-order bibim,tapir,mcp
```

Модуль должен определить `BACKEND = <наследник backends.Backend>`.
`BibimBackend` в `backends.py` — заглушка с контрактом; минимально достаточно
реализовать `project_info`, `all_elements`, `details`, `get_property_values`.

**Мутирующих вызовов нет вообще.** Ни создания геометрии, ни записи свойств,
ни смены выделения/вида.

### Что проверяется

| Проверка | Зачем | Критерий OK |
|---|---|---|
| `project_identity` | к чему мы вообще подключены | путь/имя/версия/сборка получены; не untitled; не Teamwork; путь == `--expect-project` |
| `stories_index_map` | `floorIndex` из details надо сопоставить с именем и отметкой | у каждого этажа есть `index`, `name`, `elevation` |
| `layer_name_via_property` | `layerIndex` не даёт имени; имя нужно для верификации и для проверки блокировки слоя | `ModelView_LayerName` вернул имя |
| `list_guids` | база для `state fingerprint` | ≥1 GUID |
| `count_by_type` | детектор дублей через дельту счётчиков | все типы вернули целое ≥0 (`-1` = команда не отвечает, а не «ноль») |
| `elements_by_type` | независимый путь read-back | отвечает |
| `wall_geometry_endpoints` | **главное**: можно ли подтвердить позицию стены | в details есть `ref_line` (endpoints). Без него верификация позиции невозможна |
| `read_element_id` | носитель маркера №1 | значение читается |
| `read_custom_property` | носитель маркера №2 (`BIMEXEC/BIMEXEC_MARKER`) | значение читается |
| `search_probe` | поиск по маркеру: точный и по префиксу | **позитивный контроль**: существующее значение Element ID находится само в себе; **негативный контроль**: заведомо отсутствующее значение даёт 0 |
| `ac29_read_commands` | поведение каждой read-команды в AC29 | все отвечают; любая не отвечающая попадает в `broken` и даёт `??` (UNKNOWN), а не «ок» |

У каждой возможности в отчёте указано поле `backend` — **какой именно бэкенд
её дал** (BIBIM / Tapir / MCP). Это прямое требование: матрица без атрибуции
бэкенда бесполезна, потому что завтра вы поменяете канал и матрица станет
ложью.

### Ожидаемый вывод (пример)

```
BIMEXEC T0A read-only capability probe 1.0
host: Windows 10 python 3.11.9
  backend tapir    OK   ACConnection + official commands reachable
  backend mcp      down URLError
  backend bibim    down not implemented

capabilities:
  [OK  ] project_identity             backend=tapir
  [OK  ] stories_read                 backend=tapir
  [OK  ] list_guids                   backend=tapir
  [OK  ] count_by_type                backend=tapir
  [OK  ] elements_by_type             backend=tapir
  [OK  ] wall_geometry_endpoints      backend=tapir
  [OK  ] read_element_id              backend=tapir
  [NO  ] read_custom_property         backend=tapir
          note: носитель недоступен: user-defined property ... does not exist
  [OK  ] search_probe                 backend=tapir
  [??  ] ac29_read_commands           backend=tapir
          note: часть read-команд не отвечает: ['tapir.GetAddOnVersion']

readable marker carriers : ['element_id']
create_wall production_safe: False
  blocked by              : ['T0B_marker_roundtrip_not_run']

T0A GO
next: T0B
```

Обратите внимание на две вещи, которые этот вывод делает правильно:

- `create_wall production_safe: False` — **всегда** до T0B, независимо от
  того, насколько хорошо прошла T0A. Это не пессимизм, это единственный
  честный ответ: мы ещё ни разу не доказали, что запись маркера вообще
  читается обратно.
- неработающая read-команда даёт `??` (UNKNOWN), а не зелёную галочку.

### Go / No-Go для T0A

**GO (можно идти в T0B), только если всё одновременно:**

- [ ] `project_identity` = OK, и путь проекта совпал с ожидаемым
- [ ] `stories_index_map` = OK (index + name + elevation у всех этажей)
- [ ] `layer_name_via_property` = OK
- [ ] `list_guids` = OK
- [ ] `count_by_type` = OK
- [ ] `wall_geometry_endpoints` = OK (есть endpoints)
- [ ] `search_scan` = OK: `positive_exact_hits` ≥ 1, `positive_prefix_hits` ≥ 1,
      `negative_exact_hits` = 0, `negative_prefix_hits` = 0
- [ ] `raw_dumps.GetDetailsOfElements_sample` содержит координаты стены
- [ ] хотя бы один носитель маркера читается
- [ ] `ac29_read_commands` — все команды, которые нужны для binding, отвечают.
      Отсутствие `GetAddOnVersion` не блокирует; отсутствие
      `GetDetailsOfElements` или `GetPropertyValuesOfElements` — блокирует.

**NO-GO** в любом из случаев:

- нет endpoints у стены → верификация позиции невозможна, `create_wall`
  остаётся вне scope;
- не читается ни один носитель → binding-протокол нереализуем;
- `search_probe` провалил негативный контроль → поиск возвращает мусор,
  и привязка будет биться в чужие объекты;
- проект untitled или Teamwork.

---

## 4. T0B — controlled marker round-trip

**Это первый настоящий write в Archicad.** Геометрия не создаётся.

```bat
REM шаг 1: предпроверка без записи
python probe_t0b.py --guid <GUID_ТЕСТОВОЙ_СТЕНЫ> ^
    --expect-project "C:\PLN\MCP_TEST.pln" --carrier both --dry-run

REM шаг 2: реальный прогон — носитель property (рекомендуемый)
python probe_t0b.py --guid <GUID_ТЕСТОВОЙ_СТЕНЫ> ^
    --expect-project "C:\PLN\MCP_TEST.pln" --carrier property ^
    --allow-write --i-understand-this-writes-to-archicad

REM шаг 3: реальный прогон — носитель Element ID
python probe_t0b.py --guid <GUID_ТЕСТОВОЙ_СТЕНЫ> ^
    --expect-project "C:\PLN\MCP_TEST.pln" --carrier element_id ^
    --element-id-address General_ElementID ^
    --allow-write --i-understand-this-writes-to-archicad
```

**Правило двух ключей.** Запись включается ТОЛЬКО двумя флагами одновременно:
`--allow-write` И `--i-understand-this-writes-to-archicad`. Один флаг без
второго — ошибка запуска (exit 1), запись не выполняется. Ни один из флагов
не переопределяет другой и не является «укороченной формой».

`--element-id-address` необязателен: без него probe перебирает 5 кандидатов
адреса Element ID. Но лучше передать явно то, что T0A записал в
`capabilities.read_element_id.address` (и печатает как
`element_id address (для T0B --element-id-address): ...`).

### Протокол

```
PRECHECK           read-only: проект тот, элемент существует, details читаются,
                   носители читаются, BX:PROBE:* в модели НЕ найдено
SAVED              исходное значение поля сохранено в receipt (fsync ДО записи)
WRITTEN            записан BX:PROBE:<nonce>          — одна попытка
READ_BACK          прочитано, строковое равенство
FIND_EXACT         поиск по точному маркеру → ровно [GUID]
FIND_PREFIX        поиск по префиксу BX:PROBE: → ровно [GUID]
RESTORED           записано исходное значение
VERIFY_RESTORE     прочитано, восстановление доказано
FINAL_SWEEP        BX:PROBE:* в модели снова 0
```

### Правила, зашитые в код

- **Одна попытка на шаг. Повторов нет** ни при каком исходе.
- Любой `timeout / ambiguous / write-ok-но-read-back-не-совпал` → `UNKNOWN` → STOP.
- **Receipt пишется до каждой мутации.** Если процесс умрёт, в
  `t0b_receipt.json` лежит ровно то значение, которое осталось в модели,
  и то, во что его надо вернуть:

```json
"cleanup": {
  "carrier": "element_id",
  "guid": "G-0001",
  "value_to_remove": "BX:PROBE:60fdfc19...",
  "restore_to": "W-101",
  "how": "в Archicad вручную вернуть значение поля"
}
```

- Lock-файл `t0b_receipt.json.lock` не даёт запустить два probe одновременно.
- Повторный запуск с существующим receipt **блокируется**: прошлый прогон мог
  оставить маркер, сначала разберитесь.
- `exit 0` только если все шаги прошли **и** восстановление доказано.

### Ожидаемый вывод (успех)

```
  backend tapir    OK
  element <GUID>: type=Wall story={'name': 'Ground Floor', ...} layer=A-WALL
  carrier element_id   readable, current='W-TEST-001'
  carrier property     readable, current=None

--- carrier element_id (builtin:General_ElementID)
  OK: round-trip + restore доказаны

--- carrier property (user:BIMEXEC/BIMEXEC_MARKER)
  OK: round-trip + restore доказаны

T0B GO. Проверенные носители: ['element_id', 'property']
Рекомендуемый носитель: property
```

### Ожидаемый вывод (silent no-op — класс дефекта E3)

```
--- carrier element_id
STOP at READ_BACK: element_id: write прошёл, но прочитано 'W-TEST-001' !=
'BX:PROBE:60fdfc19...'. Класс дефекта «silent no-op» — этот носитель непригоден.
receipt: t0b_receipt.json (там значение маркера для ручной уборки)
exit 1
```

Именно этот исход — самый ценный результат T0B: он ловится **до** того, как
мы начнём создавать геометрию и привязывать к ней проёмы.

### Go / No-Go для T0B

**GO, только если:**

- [ ] `status: OK` в receipt
- [ ] для выбранного носителя пройдены **все** шаги, включая `VERIFY_RESTORE`
- [ ] `FINAL_SWEEP` показал 0 оставшихся `BX:PROBE:*`
- [ ] `exit 0`
- [ ] исходное значение поля в Archicad визуально совпадает с тем, что было
      до прогона (проверьте глазами — это стоит десяти секунд)

**NO-GO / STOP:**

- любой `UNKNOWN` → STOP. Маркер мог остаться в модели — уборка по receipt.
- `FIND_EXACT` или `FIND_PREFIX` вернули не ровно один GUID → STOP.
- `VERIFY_RESTORE` не доказал восстановление → STOP и вернуть значение вручную.
- носитель, проваливший round-trip, **вычёркивается** из capability matrix.

---

## 5. Какой носитель предпочтителен

### Сравнение

| | `Element ID` (`General_ElementID`) | User-defined property `BIMEXEC/BIMEXEC_MARKER` |
|---|---|---|
| Существует без подготовки | да, встроенное свойство | **нет**, должно быть создано заранее |
| Кто может создать | — | **только Add-On или вручную**: официальный Python/JSON API не умеет создавать свойства, только устанавливать значения |
| Путь записи | `SetPropertyValuesOfElements` | тот же |
| Путь чтения | `GetPropertyValuesOfElements` | тот же |
| Поиск | сканирование значений по элементам, O(n) | то же сканирование, той же ценой |
| Видимость пользователю | **да**: попадает в ведомости, марки, списки | нет, пока свойство не добавят в схему |
| Известные дефекты | `SetPropertyValuesOfElements` → `Teamwork Permission Denied` (error 6001) **на Solo-проекте**; конфликты Element ID в практике | те же, что у пути записи (это один и тот же вызов) |

### Рекомендация

**Основной носитель — user-defined property `BIMEXEC/BIMEXEC_MARKER`.
Fallback — `Element ID`.**

Чем подтверждено:

1. Оба идут через **один и тот же вызов** `SetPropertyValuesOfElements`,
   поэтому надёжность записи у них одинаковая. Значит, решающий фактор — не
   надёжность, а **побочный эффект**: Element ID — пользовательские данные.
2. Element ID виден в ведомостях и марках. Записать туда `BX:PROBE:<nonce>`
   — значит на время изменить видимое содержание проекта. T0B это
   восстанавливает, но при крахе между записью и восстановлением в
   пользовательском поле остаётся мусор. У выделенного свойства такого
   побочного эффекта нет.
3. Официальный JSON API **не умеет создавать свойства** — только устанавливать
   значения. Значит свойство надо создать один раз: вручную через Property
   Manager или одноразовой командой Add-On. **Router не должен создавать
   свойства в рантайме** — это изменение схемы проекта, а не данных.
4. Уточнение по вашей инвентаризации: путь `Group/Name` → `API.GetPropertyIds`
   → `API.SetPropertyValuesOfElements` — это тот же механизм, которым уже
   работает `ModelView_LayerName`. То есть адресация свойства **подтверждена
   рабочей на практике**; вопрос только в том, существует ли наше свойство.
   Поэтому до T0B нужно одно действие вручную: создать в `MCP_TEST.pln`
   свойство `BIMEXEC` / `BIMEXEC_MARKER` типа string.

**Тие-брейкер в коде:** если оба носителя прошли round-trip, отчёт T0B
рекомендует `property`; если доступен только `element_id` — рекомендует его.
Если не прошёл ни один — см. ниже.

### Если не прошёл ни один носитель

Binding по маркеру нереализуем. Остаётся привязка **по якорю**
(тип + этаж + слой + геометрия + счётчик), и она безопасна только под
предусловием «чистая область»: перед созданием в области (тип, этаж, слой)
не должно быть элементов, не привязанных к этому job. Это уже заложено в
сkeleton (`duplicate_detection = EMPTY_SCOPE_FALLBACK`), но это **существенно
слабее**: дубли от прошлых прерванных запусков перестают детектиться на
уровне операции.

В этом случае `create_wall` остаётся `production_safe: false`, и первая
геометрия не создаётся, пока вопрос не закрыт.

---

## 6. Что уже проверено на Linux-стороне

T0A и T0B прогнаны против in-memory модели, проверены пять сценариев:

| Сценарий | Ожидание | Факт |
|---|---|---|
| Нормальный прогон T0A | `create_wall: production_safe=false`, `T0A GO` | совпало |
| T0B happy path (оба носителя) | `exit 0`, `T0B GO`, рекомендация `property` | совпало |
| Write возвращает ok, значение не записано | STOP на `READ_BACK`, `status=UNKNOWN`, cleanup в receipt | совпало |
| В модели уже есть `BX:PROBE:*` от прерванного прогона | STOP на `PRECHECK`, `exit 1` | совпало |
| Путь проекта не совпал с `--expect-project` | STOP на `PRECHECK`, `exit 1` | совпало |
| Повторный запуск при существующем receipt | блокировка, `exit 1` | совпало |

Тестовые двойники (in-memory модель вместо Archicad) лежат в
`bimexec/tests/fakes/` репозитория — **на Windows они не нужны**, они только
для проверки логики probe без Archicad. Прогон без Archicad:
`python bimexec/tests/selftest_probes.py`.

---

## 7. Что прислать обратно

1. `capability_matrix.json` (вывод T0A) — целиком.
2. Консольный вывод T0A.
3. `t0b_report.json` и `t0b_receipt.json` (вывод T0B).
4. Консольный вывод T0B — целиком, даже если это STOP.
5. Какой бэкенд фактически ответил (`backend` в отчётах) и GUID тестовой стены.

Дальше по результатам:

- закрываем вопрос носителя;
- переносим фактическую capability matrix в среду Arena (Linux) и прогоняем
  скелет с реальной матрицей;
- **только после этого** обсуждаем первый `create_wall` — одну стену по
  рецепту из `BIMEXEC_P0_review.md` (раздел 6.2): `[1.5, 2.5] → [6.5, 2.5]`,
  length 5.0 ≠ height 3.0 ≠ thickness 0.30, пустой этаж, радиус 3 м свободен.

До результатов T0B ни `create_wall`, ни интеграция скелета в Router
не выполняются.
