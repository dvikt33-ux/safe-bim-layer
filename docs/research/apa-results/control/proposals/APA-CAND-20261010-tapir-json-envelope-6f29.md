# TASK_PROPOSAL_V1 — fail-closed Python/JSON transport для Tapir

```yaml
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-20261010-tapir-json-envelope-6f29
origin: technical
proposer_run_id: APA-RUN-20261010-163950Z-tapir-compat-6f29
source_substep_id: APA-P10.A02.S01
proposed_parent_plan: APA-P20
proposed_action: APA-P20.A01
suggested_substep_id: APA-P20.A01.S06
work_key: tapir-python-json-envelope-guard
title: "Проверить fail-closed JSON envelope, timeout и identity в Python-клиенте Tapir"
kind: VALIDATION
priority: 1
depends_on: [APA-P00.A02.S02]
related: [APA-P10.A02.S01, APA-P20.A01.S01, APA-P20.A01.S02]
inputs: [ART-REGISTER]
outputs: ["Версионированный contract-test report для HTTP/JSON transport и identity"]
acceptance: "Offline deterministic tests проверяют missing succeeded/result, succeeded=false, nested addOnCommandResponse.error, unexpected/missing addOnCommandResponse, wrong namespace, timeout/connection refused и отказ от использования неподтверждённого Archicad endpoint; raw test evidence и безопасный read-only plan опубликованы; LIVE отдельно NOT_VERIFIED"
requires_approval: false
expected_mvp_benefit: "Не допускать ложных PASS и запросов в неверный процесс при нескольких экземплярах Archicad; количественное ускорение NOT_MEASURED"
evidence_urls:
  - "https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Examples/aclib/__init__.py#L5-L69"
  - "https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/ApplicationCommands.cpp#L55-L86"
risks: "Текущая локальная 1.5.10 модифицирована, точный APX provenance не подтверждён; не подменять test-double LIVE."
```

## Зачем нужен отдельный подшаг

В upstream Tapir 1.5.9/1.6.0/1.7.0 Python `aclib.RunCommand` отправляет JSON на `http://127.0.0.1:19723` по умолчанию (порт можно передать `--port`), не задаёт timeout, при `succeeded=false` возвращает `None`. `RunTapirCommand` возвращает вложенный `addOnCommandResponse`, а при `error` только печатает ошибку и всё равно возвращает словарь. Это **SOURCE_VERIFIED** по upstream коду, но не runtime наблюдение локальной сборки.

Уже зарегистрированы `APA-P20.A01.S01` (provenance APX), `APA-P20.A01.S02` (доступность команд), `APA-P10.A02.S01` (source compatibility). **Новая проверка НЕ дублирует** их: она фокусируется на транспортном JSON-контракте, ошибках и fail-closed semantics перед вызовом BIM writer. При аудите допускается объединить её с существующим S-ID, если acceptance уже охватывает все указанные failure modes; тогда решение `DUPLICATE` вместо регистрации.

## Тесты без Archicad/PLN/APX

- Мок локального HTTP сервера: 200 OK с `succeeded=true` и `result.addOnCommandResponse` — строгий успешный разбор.
- `succeeded=false`, отсутствие `result`, отсутствие `addOnCommandResponse`, `error` в nested payload — явный FAIL, не тихий `None`/print.
- Timeout, отказ соединения, malformed JSON, неверный `commandNamespace`, `GetAddOnVersion` без проверенной версии и process identity — fail-closed.
- В реальном AC29 (позже, read-only) сверить PID/port, путь исполняемого Archicad, project identity, установленный APX hash, доступность `GetAddOnVersion`, затем неразрушающий запрос. Это отдельный LIVE gate; никакого самовольного переключения PLN или APX.

## Audit decision requested

Проверить отсутствие семантического дубля с P20.A01.S01/S02 и существующими адаптерами; оценить, стоит ли выделять отдельный S06 или расширить acceptance существующего S02. Если одобрено — уникальный ID/work_key, `topics.task_ids`, симметричные `related`, зависимости и validator CI обязательны. Пока **PENDING_AUDIT**, не исполняемая задача.
