# D-03 | Надёжная активация существующего чата через Automa — контрольный маршрут v1

**Состояние на 27.10.2026:** маршрут ещё не прошёл сквозной LIVE-тест. Документ — проверенный по исходному коду контракт настройки, а не свидетельство окончательной приёмки.

**Область:** пилотный D03-ACK-PILOT в Opera / Automa 1.30.02, отдельный Windows-процесс Python 3.14.6, GitHub private mailbox и SQLite. Выполнение сообщений **не разрешено**. APA не подключать. Этот документ не содержит приватных URL бесед или токенов.

## Уже доказано пользователем на Windows (21.10.2026)

1. `GET http://127.0.0.1:18765/health` вернул 200, `BUREAU_UNIFIED_ALIVE`, `apaAttached=false`, `dispatchArmed=false`.
2. Штатный HTTP Request Automa успешно обращался к локальному серверу.
3. URL-параметры Workflow (тестовые `jobId=test-variables-only`, `token=TEST-ONLY`, `callbackPort=18765`) попали в Variables.
4. GitHub event `d03-probe-20261021-transport` автоматически поступил в SQLite со статусом `QUEUED`. Он **истёк 23.10.2026 00:00 UTC** и теперь не пригоден для реальной активации.
5. Не доказано: `GET /task` с действительным токеном; проверка фактического conversationId; `POST /ack` и переход `COMPLETE_ACTIVATION`; однократная отправка текста и результаты.

## Контракт проверенного текущего исходника

Точная закреплённая версия локального кода: commit `03de836e0bcb70c4c54419f1f939d406d22bbec1` в draft PR #187, `scripts/bureau_unified_service.py`.

- `GET /task?jobId=<jobId>&token=<token>` возвращает **плоский объект** JSON с `jobId`, `targetChat`, `chatUrl`, `action`, `conversationId`, `instruction`; при невалидном токене — HTTP 403.
- `POST /ack` принимает JSON `jobId`, `token`, `stage`, `proof` (последняя строка длиной 1–500); при `stage=TAB_SELECTED` для действия `ACTIVATE_ONLY` переход `WAIT_TAB → COMPLETE_ACTIVATION`, HTTP 200 и `{"status":"COMPLETE_ACTIVATION"}`; при неудаче — ошибка HTTP 409.
- `/health` подтверждает живой процесс, но не действительность задания.
- `dispatchArmed=false` запрещает старт очередного задания, но не блокирует чтение `/health`.
- Для V2 `DELIVER_TASK` в текущей локальной конфигурации `externalEntryTargets=[]`; сначала принимаем только `ACTIVATE_ONLY`.

**Важно:** HTTP Request Automa с `Data path = $response` и включённым `Assign to variable=currentResponse` сохраняет весь транспортный ответ в объект `currentResponse = {status,statusText,data,...}`. Так, `currentResponse.data.jobId` соответствует полю верхнего уровня JSON, возвращённого Python, а НЕ `currentResponse.data.data.jobId`.

## Единственная разрешённая цепочка для D03-ACK-PILOT

```text
Trigger (jobId, token, callbackPort)
  → HTTP Request GET /task [success only]
  → Conditions A [четыре AND]
  → Switch tab [существующая беседа; Create If No Match OFF]
  → Delay 2000ms
  → JavaScript Code [Active tab; проверка реального conversationId]
  → Conditions B [AND: verifiedJobId, verifiedConversationId]
  → HTTP Request POST /ack [TAB_SELECTED]
  → Conditions C [ACK 200 + COMPLETE_ACTIVATION]
  → Finish
```

**Запрещено:** любой переход по `Fallback` к Switch tab, соединение с `Forms`, `Click element` или вводом текста. Нижний запасной Trigger и цепочку ввода оставить разъединёнными. `fallback` всех критичных блоков оставить разъединённым или завершать отдельной ошибкой.

### Первый HTTP Request: получение задания

- Method: `GET`
- URL: `http://127.0.0.1:18765/task?jobId={{variables.jobId}}&token={{variables.token}}`
- Content type: `application/json`, timeout 10000ms.
- Response type `JSON`; Data path `$response`; Assign to variable: `currentResponse`; Insert to table **OFF**.
- Продолжение — только по **верхнему** основному выходу.

### Conditions A — Path 1, логическое AND

| Левое Value | Сравнение | Правое Value |
|---|---|---|
| `{{variables.currentResponse.status}}` | Equals | `number::200` |
| `{{variables.currentResponse.data.jobId}}` | Equals | `{{variables.jobId}}` |
| `{{variables.currentResponse.data.targetChat}}` | Equals | `D-03` |
| `{{variables.currentResponse.data.action}}` | Equals | `ACTIVATE_ONLY` |

Два типа элементов — `Value`, не `Code`. Только выход `Path 1` подключать к Switch Tab; Fallback не подключать. Для настоящего `jobId` и `token` значения в URL приходят из закреплённого Python dispatch; не вставлять токен из журнала вручную.

### Switch tab

Использовать существующее правило выбора ранее опознанного Д-03, без создания вкладки при отсутствии совпадения (`Create If No Match = OFF`). **Нельзя** переключать вкладку по порядковому номеру и считать успех Switch tab доказательством верного чата. Следующим блоком после переключения должна быть независимая проверка URL.

### JavaScript Code: сверка фактической активной беседы

Execution context: **Active tab**. `Execute in every new tab` — **OFF**. Запускать после Switch tab и Delay. Копировать текст целиком:

```javascript
const r = automaRefData("variables", "currentResponse");
const jobId = automaRefData("variables", "jobId");
const task = r && r.data;
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
if (!r || Number(r.status) !== 200 ||
    !task || task.jobId !== jobId ||
    task.targetChat !== "D-03" ||
    task.action !== "ACTIVATE_ONLY" ||
    typeof task.conversationId !== "string" ||
    !uuid.test(task.conversationId)) {
  throw new Error("INVALID_TASK_RESPONSE");
}
const match = location.pathname.match(/\/c\/([0-9a-f-]{36})\/?$/i);
if (location.origin !== "https://chatgpt.com" ||
    !match || !uuid.test(match[1]) ||
    match[1].toLowerCase() !== task.conversationId.toLowerCase()) {
  throw new Error("WRONG_ACTIVE_CONVERSATION");
}
automaSetVariable("verifiedJobId", jobId);
automaSetVariable("verifiedConversationId", match[1].toLowerCase());
automaSetVariable("tabProof", "EXACT_CONVERSATION_ID:" + match[1].toLowerCase());
automaNextBlock();
```

**Отказ при ошибке обязателен:** после JS всё равно ставим Conditions B, потому что документация Automa допускает продолжение после timeout JavaScript. Отсутствующие переменные в Conditions B = отказ, без POST.

### Conditions B — Path 1, логическое AND

| Левое Value | Сравнение | Правое Value |
|---|---|---|
| `{{variables.verifiedJobId}}` | Equals | `{{variables.jobId}}` |
| `{{variables.verifiedConversationId}}` | Equals | `{{variables.currentResponse.data.conversationId}}` |

Выход Path 1 → POST. Fallback не подключать. Если требуется защита от несоответствия регистра UUID — Python отдаёт UUID в нижнем регистре; JS нормализует.

### Второй HTTP Request: квитанция

- Method `POST`
- URL `http://127.0.0.1:18765/ack`
- Content type `application/json`, timeout 10000ms, JSON body:

```json
{
  "jobId": "{{variables.jobId}}",
  "token": "{{variables.token}}",
  "stage": "TAB_SELECTED",
  "proof": "{{variables.tabProof}}"
}
```

- Response type `JSON`, Data path `$response`, Assign to variable `ackResponse`, Insert to table OFF.
- Продолжать только при `ackResponse.status = 200` и `ackResponse.data.status = COMPLETE_ACTIVATION` (отдельные Conditions C AND).
- Никаких сообщений в ChatGPT.

### Запрет ложного успеха

Зелёный Automa Succeeded, успешный Switch Tab или `GET /health` **не подтверждает квитанцию**. Принимать тест только при **обоих** доказательствах:

1. Automa POST /ack успешен, `ackResponse.data.status=COMPLETE_ACTIVATION`.
2. Локальная CLI `status` видит тот же ID события в `COMPLETE_ACTIVATION`:

```powershell
$dir = 'C:\LocalAI\BureauUnified\pilot'
py "$dir\bureau_unified_service.py" --config "$dir\config.json" --db "$dir\jobs.sqlite" status
```

После перезапуска процесса статус должен сохраниться, повторной активации не должно быть.

## Подготовка новой LIVE-пробы после сборки блоков

*Не публиковать новую команду до сохранения и проверки безопасной цепочки.* Событие от 21.10 истекло; не изменять его SHA/content, не переиспользовать старый ID. При готовности публиковать **новый уникальный** `BUREAU_CHAT_ACTIVATION_V1 / TRIGGER_PROBE / ACTIVATE_ONLY` c `createdAt`, `expiresAt` в будущем и ограниченным TTL. Сверить результат импорта в SQLite как `QUEUED`.

Затем проверить, что приватная локальная конфигурация имеет ровно один target `D-03`, `externalEntryTargets=[]`, `apaEnabled=false`, а у Automa отсутствует путь к отправке текста. Только после этого в **изолированном пилоте** остановить сервис, временно установить `dispatchArmed=true`, снова запустить и проконтролировать ровно одну активацию; далее вернуть `dispatchArmed=false`. Для штатного эксплуатационного режима понадобится более узкий режим разрешения конкретного job и независимые тесты доставки текста. Прежний APA worker не трогать.

**Конфиденциальность:** не включать экспорт URL с `token=` в публичные логи и не отправлять в чат реальные токены. Внутренние `jobId`, `token`, `callbackPort` разрешено получать через URL только от Python. Документы публикации не должны содержать секретов.

## Первоисточники

- Python: `scripts/bureau_unified_service.py` и `scripts/bureau_chat_activation_gateway.py` draft PR #187, commit `03de836`.
- HTTP Request: https://www.goautoma.com/extension/docs/blocks/webhook.html
- Conditions: https://www.goautoma.com/extension/docs/blocks/conditions.html
- Condition Builder: https://www.goautoma.com/extension/docs/reference/condition-builder.html
- URL Trigger / Parameters: https://www.goautoma.com/extension/docs/blocks/trigger.html
- Switch Tab: https://www.goautoma.com/extension/docs/blocks/switch-tab.html
- JavaScript Code: https://www.goautoma.com/extension/docs/blocks/javascript-code.html

**Приёмка:** OPEN / NOT ACCEPTED до предъявления настоящих SQLite `COMPLETE_ACTIVATION` и неизменного окна Д-03 без отправки сообщения.
