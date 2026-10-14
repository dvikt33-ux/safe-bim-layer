# APA — независимый статический аудит исходников Boti-Ormandi/archicad-mcp

**Дата:** 2026-10-14  
**Тип:** SOURCE_AUDIT / NO_EXECUTION  
**Решение:** `SELECTIVE_REUSE_RESEARCH` — изучать и при необходимости заимствовать идеи **схемного read-only каталога**, но **DO_NOT_INSTALL_AS_APA_WRITER**.  
**Upstream:** https://github.com/Boti-Ormandi/archicad-mcp  
**Контрольная ревизия:** [b6557cf0455f31cc00086fdaa45fd57f429c613b](https://github.com/Boti-Ormandi/archicad-mcp/commit/b6557cf0455f31cc00086fdaa45fd57f429c613b)  
**Лицензия:** MIT (`pyproject.toml` / `LICENSE` upstream). `mcp>=2,<3`, Python >=3.11, `aiohttp`, `pydantic`, `rapidfuzz`, `openpyxl`, `filelock`.  
**Наш контекст:** Archicad 29.3001+, локальный Tapir 1.5.10 (требует независимого подтверждения активной версии на хосте), APA SceneWriter, Safe BIM Layer, исследовательский `apa_retrieve` MCP v2.  
**Не выполнялось:** установка/запуск archicad-mcp, тесты pytest, Python на хосте пользователя, тесты Archicad 29, тест на реальном PLN, сопоставление реальной схемы Tapir 1.5.10 со снимком 1.5.8, измерение качества и токенов. **НЕ утверждать `LIVE_PASS`, `TESTED`, `DONE_PUBLISHED`.**

## 1. Метод, исходники и статические проверки

Через GitHub connector считаны реальные исходники **по конкретному commit SHA**, а не README-only. Проверены 15/15 независимых **статических предикатов присутствия/отсутствия заявленных паттернов** (это source inspection, а НЕ 15 pytest tests или проверки безопасности исполняемой системы). Бинарники, модели пользователя и сеть Archicad не задействованы.

| Путь по контрольной ревизии | Git blob SHA | Подтверждение |
|---|---|---|
| [`server.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/server.py) | `84831f086abddc6c631082280edb5c21536a45eb` | MCP tools, global capability view, отсутствие привязки docs к target port, вызов executor |
| [`schemas/registry.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/schemas/registry.py) | `587e21768eb547dfcdcd81d02b7a59d6cd0a8e99` | `CapabilityView`, batch `get_many`, стабильные digest, поиск с `rapidfuzz` |
| [`schemas/tapir_source.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/schemas/tapir_source.py) | `a54927a31fae9f85bbfd235573e3c00dde273d7e` | **packaged baseline Tapir 1.5.8**, pinned upstream commit `ce033d6bdcc90b538b3c5f7ab62f676099b96823`, SHA256 inputs |
| [`scripting/worker.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/scripting/worker.py) | `523f0ea23f1403083c3810d420262f380fe49ca1` | **`compile(..., "exec"); exec(code, namespace)`** под ОС пользователем |
| [`scripting/executor.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/scripting/executor.py) | `544d6e1929b851c4d46ab8b6ccfcabe711814bb0` | subprocess, optional unlimited timeout, cancellation ограничена дочерним процессом |
| [`core/manager.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/core/manager.py) | `1f449c200df74bf8e6123c49e01650e7cc8a3dcb` | 19723–19743, Tapir version/project/path probes |
| [`core/properties.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/core/properties.py) | `53e92509c7380bf049aa0ae8281515bbadb8724d` | `PropertyCache: dict[int,...]` keyed by **port** only, calls `GetAllProperties` |
| [`core/connection.py`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/src/archicad_mcp/core/connection.py) | `3b1a...` **SHA НЕ ЗАФИКСИРОВАН; НЕ ИСПОЛЬЗОВАТЬ В КАЧЕСТВЕ ПРОВЕРЕННОГО ИДЕНТИФИКАТОРА** | HTTP JSON API, native/Tapir dispatch, returned errors |
| [`docs/schema-updates.md`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/docs/schema-updates.md) | not pinned by blob in this audit | validate cache, SemVer updates by pinned release commit, automatic optional network |
| [`docs/script-execution.md`](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/docs/script-execution.md) | available from upstream at `master`; doc code source pinned above | official explicit authority: no sandbox/allowlist/rollback |

**Важно:** статические проверки не являются автоматизированной security-проверкой зависимостей или гарантиями отсутствия других дефектов. Репозиторий не клонировался и исполняемые tests не запускались.

## 2. Подтверждённая структура и действительно новые идеи

- Сервер реализован на **официальном MCP Python SDK v2**, локальный stdio; ровно 4 экспортированных tools: `list_instances`, `get_docs`, `get_properties`, `execute_script`. `get_docs` имеет browse/search/exact/batch; `get_properties` ищет фактические property GUID через Tapir; оба режима не являются генерацией IFC/PLN сами по себе.
- **Каталог без открытого Archicad:** packaged `builtin.json` + `tapir.json` с проверенной ссылочной замкнутостью. Команда возвращает определения полей, вложенные схемы, provider/source provenance, revision и полные документы по запросу, не требует запускать BIM-приложение для документации.
- **Экономия токенов — потенциальная, не измеренная**: вместо передачи всей документации в промпт — маленький search/result, затем точная схема для 1–3 команд.
- Пакетный `get_many` допускает ограничение обращений к MCP; строгий разбор JSON отвергает дубли ключей, некорректные номера, dangling/external refs и неподдерживаемые ключевые слова разрешения схем.
- **Cache updater**: строгий SemVer, pinned source commit+hash, валидация лицензии, без выполнения upstream JavaScript, атомарная публикация в пользовательский cache и 24h rate gate. Документ [schema-updates](https://github.com/Boti-Ormandi/archicad-mcp/blob/b6557cf0455f31cc00086fdaa45fd57f429c613b/docs/schema-updates.md). Обновления можно отключить `ARCHICAD_MCP_OFFLINE=1`, `ARCHICAD_MCP_AUTO_UPDATE=0`; это не отключает сетевую установку самого `uvx`.
- `list_instances` опрашивает localhost-порты `19723…19743`, разбирает `GetProductInfo`, Tapir `GetAddOnVersion`, при доступности `GetProjectInfo`; обнаружение не блокирует изменение проекта после discovery.

## 3. Проблемы, блокировки и рекомендации

| ID | Уровень | Доказательства / фактический механизм | Последствия | Решение |
|---|---|---|---|---|
| R-01 | **BLOCKER / CRITICAL** | `scripting/worker.py:92–103` вызывает `compile` и `exec` на полном тексте сценария. Worker обладает текущими правами Windows, может обращаться к файлам, сети, процессам и любым API Archicad; subprocess **не sandbox**. | Злоумышленная подсказка или ошибка ИИ может неограниченно читать/изменять файлы, создавать процессы, портить PLN. | **Запрет `execute_script` в рабочем APA**; не передавать стороннему MCP права на writer. Если исследовать, только исходники и отдельный docs-only адаптер без `execute_script` в tools. |
| R-02 | **HIGH** | `server.py:457–505`: `get_docs` **не принимает port**; `server.py:109–176` строит единый `CapabilityView` по первому найденному экземпляру с Tapir. | При нескольких AC и разных установках Tapir docs могут не относиться к выбранному instance. | Добавить **per-instance view**, key по port + exact AC build + Tapir semver + source SHA; без совпадения запрещать write. |
| R-03 | **HIGH** | `tapir_source.py:96–103`: packaged Tapir **1.5.8**, документный cache выбирается по newer SemVer; реальный add-on может быть другой версии, а live schemas из Archicad не получаются. | Ошибки полей API; «команда известна» ≠ «поддерживается локально в AC29». | Offline diff 1.5.8 vs локальной схемы/плагина 1.5.10; только verified schemas; unknown -> NOT_VERIFIED. |
| R-04 | **HIGH** | `server.py:742–752`: writer принимает **только port + script**, не проверяет project fingerprint, write permission, plan intent; `worker.py:95–103` напрямую создаёт подключение. | Проект мог измениться между discovery и write; ошибочная цель даже при корректном порту. | Пиновать project path/identity, процесс/build + GUID inventory, preflight before each operation. Сохранение и read-back отдельно. |
| R-05 | **MEDIUM** | `core/properties.py:30–58`: cache keyed только по `port`, `get_properties` `GetAllProperties` один раз. `list_instances` refresh не вызывает clear этого cache в `server.py`. | В том же порту после смены проекта/пользовательских свойств кэш может устареть. Это **потенциальная ошибка**, не доказанный сбой в Archicad. | Key по target identity+revision; invalidate on project change, reconnect, custom property changes. |
| R-06 | **HIGH** | `scripting/executor.py:59–78`: timeout/cancel завершает собственный child; может быть `timeout=None`. Нет транзакции и компенсационных rollback. | Частично выполненные native writes при timeout, crash или cancellation. | Строгий journal/transaction, план preflight, compare requested/actual, baseline hash/Save-Open replay; запрет объявлять PASS по stdout. |
| R-07 | **MEDIUM** | `server.py:581–739`: `get_properties` получает `GetAllProperties` и строит примеры `GetPropertyValuesOfElements`. | Показанный в раннем исследовании crash другого MCP проекта на PropertyValuesOfElements **не доказан** для этого пакета; но без live safe test нельзя обещать безопасность чтения. | Проверить на копии PLN один property type; fail-closed при AC crash, не допускать массовых property queries на рабочем файле. |
| R-08 | **MEDIUM** | Набор внешних зависимостей `mcp>=2,<3`, `aiohttp`, `rapidfuzz`, `pydantic`, `openpyxl`, `filelock`; `uvx` получает код из package registry. | Непроверенный supply-chain и новые обновления перед installer. | Пиновать версии и hashes, проверить license notices и dependency advisories перед включением в APA installer. |

Нет доказательств эксплойта на ноутбуке пользователя и нет доказанного crash у Boti-Ormandi. Это **source-level risk analysis**, не результаты эксплуатации.

## 4. Сравнение с существующим APA, чтобы не дублировать

| Функция | Реально известная основа APA | Что несёт archicad-mcp | Действие |
|---|---|---|---|
| Запись BIM | `safe_bim_layer.py` on `main` имеет `TapirClient`, `validate_payload`, один write → readback, fail-closed. Далее исследован native `SceneWriter` и GUID/Save/Open в изолированном проекте. | Raw `execute_script` без safety layer / readback | **Не заменять** SceneWriter; не делать параллельный writer. |
| Документация Archicad/Tapir | Сейчас существуют pinned-схемы и тесты соответствия API; общая система `apa_retrieve` MCP ищет **документы/задачи**, не обязательно сигнатуры API. | `CapabilityView`, `get_docs`, `get_many`, provider/status, revision, fuzzy names | **Селективно заимствовать** — отдельный `apa_command_docs` lookup либо слой точных API в существующем retrieval gateway. |
| Поиск property GUID | Уже существуют Tapir/inventory/properties исследования; факт наличия полного персистентного кеша в текущем рабочем коде **не установлен**. | `get_properties` с поиском и кэшем | Потенциально полезно **после** исправления привязки cache к project identity. |
| Multi-instance | APA фиксирует target PLN/порт/приложение в нативных проверках; точный охват по всем runtime веткам не подтверждён здесь. | `list_instances` быстро собирает порт и metadata | Доработать существующую identity-проверку; не создавать конкурирующий manager. |
| MCP | В canonical research branch уже есть **один read-only tool `apa_retrieve`**, версия `mcp==2.3.0`, без права менять файлы; это **не APX runtime**. | Второй stdio MCP host с 4 tools, включая RCE | Не добавлять host по умолчанию; продумать один read-only tool и точный scope. |
| Обновление схем | APA использует pinned schema и fail-closed; реальный completeness drift status требует проверки. | Пиновка upstream commit+SHA, SemVer rules, valid cache | Рассмотреть **пакетный schema-updater** только с независимой проверкой новой версии; обновления не должны автоматически разрешать новые write. |

APA подтверждения: [Safe BIM Layer v0.1](https://github.com/dvikt33-ux/safe-bim-layer/blob/main/safe_bim_layer.py) и [исследование внедрённого retrieval MCP](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-13/apa-knowledge-gateway-research-merge-final-20261013.md). Последнее подтверждено **CI исследовательской ветки**, но НЕ установкой MCP у пользователя.

## 5. Практический эксперимент: минимальный объём, без вмешательства

**SCOPE A — read-only offline (первый).**
1. Выбрать существующие реальные контракты APA: `API.GetProductInfo`, `API.GetAllElements`, Tapir `GetAddOnVersion`, `CreateSlabs`, `CreateWalls`, `GetAllProperties`.
2. На **изолированном тестовом процессе** загрузить snapshot из upstream `b6557cf`, отключить сеть/auto-updates (без подключения внешнего MCP к ChatGPT/Archicad) и извлечь точные поля/версии/описания.
3. Сравнить c pinned contract, используемым локальным APA. Diff `added/removed/changed` по command input, output, definitions, source sha. Зафиксировать **реальные несовпадения**, вместо предположений.
4. Измерить: recall@5 на 20 фиксированных вопросах к командам (в том числе русских), точность exact-command resolution, время lookup, размер контекста/токенов относительно поиска по всей документации.
5. Публикация: `SCHEMA_CANDIDATE_DIFF.json` (input source versions) + `TEST_REPORT.md` (source refs / hashes / actual pass/fail). **Отсутствие реальных измерений — `NOT_TESTED`.**

**SCOPE B — limited live read-only (после A и отдельного согласования).**
1. В изолированном PLN под Windows AC29.3001+ выполнить точную проверку build/port/Tapir-version/project fingerprint до любой команды.
2. Тест только `GetProductInfo/GetAddOnVersion`, затем поэтапно property GUID, без `execute_script`, через свой existing APA transport и запрет записи.
3. Подтвердить, что чтение не меняет исходный GUID inventory, geometry, materials, stories, Save/Open baseline; сравнить CPU/RAM/latency с уже имеющимися tool lookup.
4. Только при измеренном преимуществе оформить `TASK_PROPOSAL_V1` в управляющий реестр, независимый audit перед допуском в `PROJECT_PLAN.json`. Связанные уже существующие темы **APA-P10.A02.S03** (MCP/IFC альтернативы) и **APA-P50.A02.S01** (API-каталог).

## 6. Итоговая оценка реестра кандидатов

**`boti-ormandi-archicad-mcp`: PROMISING, NOT_TESTED, SOURCE_AUDITED.** Понижен с VERY_PROMISING: не `drop-in` расширение для APA и основное преимущество — **выборочный read-only код**, где часть функционала уже у нас есть. Безопасный путь — минимальная schema/lookup-функция, а не installation `uvx archicad-mcp` на пользовательский компьютер с доступом к PLN. Программные изменения в APA в ходе этого аудита **0**.

**Criteria of DONE for candidate:** pinned source+compatibility, measured reduction of hallucinated API fields and real time/task, baseline tests, security gate, reproducible PR + readback. Отсутствие хотя бы одного критерия — `NOT_VERIFIED`. Решение о разработке — только после независимого аудита.

**Короткий вердикт:** **источник качественных идей для схем, но НЕ готовое безопасное расширение ускорителя.**
