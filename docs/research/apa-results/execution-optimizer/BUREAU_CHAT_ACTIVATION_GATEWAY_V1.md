# Проектное бюро — событийный шлюз запуска существующих чатов (V1)

Дата: 20.10.2026. Изолированная ветка. PR #139 не изменяется.

## Что действительно реализовано

Приём ограниченного события из GitHub -> SQLite-очередь -> запуск URL-триггера Automa в установленной Opera -> отдельное подтверждение выбора вкладки. На первом рубеже **нет ввода, отправки сообщений, автоматического исследования, изменения Archicad или публикации отчёта**.

Исходный PR #139 уже проверил GitHub inbox -> локальный APA read-only -> GitHub result. Это не доказательство запуска Automa. Новый шлюз использует тот же транспорт safe-bim-bridge, но отдельную папку и не соединяется с исполнительными возможностями APA.

Automa v1.28.26+ документирует URL-триггер: https://www.goautoma.com/extension/docs/blocks/trigger.html . Доступность такого триггера в конкретной установке Opera и корректность ID рабочего процесса остаются предметом LIVE-проверки.

## Контракт события

Местоположение: dvikt33-ux/safe-bim-bridge, main,
safe-bim-mailbox/chat-dispatch/jobs/<jobId>.json

Пример JSON (времена перед испытанием заменить на актуальные UTC):

    {
      "schema": "BUREAU_CHAT_ACTIVATION_V1",
      "jobId": "d03-probe-20261020",
      "eventType": "TRIGGER_PROBE",
      "targetChat": "D-03",
      "action": "ACTIVATE_ONLY",
      "createdAt": "2026-10-20T00:00:00Z",
      "expiresAt": "2026-10-21T00:00:00Z",
      "sourceRef": null
    }

Поддерживаемые сигналы: REPORT_READY, DEPARTMENT_REPORT_READY, HQ_BRIEF_READY, ARENA_RESULT_READY, TRIGGER_PROBE.

Это только **событие маршрутизации**. В промышленных событиях REPORT_READY нужно дополнительно проверять факт публикации документа и принадлежность исходному поручению; текущая реализация проверяет только формат ссылки-источника (sourceRef), не её содержание.

Защита: строгая схема полей, допустимый тип действия только ACTIVATE_ONLY, локальный белый список адресатов, сверка SHA GitHub blob, уникальность jobId и запрет незаметной подмены опубликованного jobId. Удалённое событие не может передать произвольный URL чата, текст сообщения, путь EXE или shell-команду.

## Состояния и очередь

QUEUED -> LAUNCHING -> AWAIT_TAB_PROOF -> TAB_SELECTED_CONFIRMED

Ошибка запуска: LAUNCHING -> BLOCKED_NEEDS_RECONCILE. Если срок действия уже принятого в очередь события истёк, оно переводится в EXPIRED до запуска Opera.

Состояние LAUNCHING записывается в SQLite до обращения к Opera. Неопределённое завершение и BLOCKED_NEEDS_RECONCILE не переисполняются автоматически. Событие другого отдела не исчезает: остаётся QUEUED.

Одновременно допускается **одно UI-переключение Opera**. Это более строгий барьер, чем один активный job на чат, потому что независимые Automa-процессы могут конфликтовать за активную вкладку. Ранее запущенное исследование в другом чате при этом может продолжаться, если это обеспечивает приложение.

TAB_SELECTED_CONFIRMED означает только подтверждённое переключение вкладки; исследование не завершено. Для следующего этапа требуется отдельный протокол приёма ChatGPT и квитанция отчёта.



Если после локальной проверки выяснилось, что запуск не состоялся, снять блокировку **без повтора** можно явной командой:

    python scripts/bureau_chat_activation_gateway.py --db C:\LocalAI\bureau-gateway\state.sqlite --config C:\LocalAI\bureau-gateway\config.json cancel-blocked JOB_ID --proof "Reviewed and cancelled without retry"

Отмена допускается только из LAUNCHING / BLOCKED_NEEDS_RECONCILE; следующий ожидающий job сохраняется. Состояния EXPIRED, CANCELLED_AFTER_REVIEW и TAB_SELECTED_CONFIRMED — терминальные для пилотной операции активации.

## Подготовка и проверка на локальной Windows-машине

1. Проверить установленную версию Automa и реальный ID расширения в Opera. ID из примера не обязательно совпадает с установленным.
2. Подготовить уже существующий рабочий процесс Automa, который только выбирает существующую вкладку Д-03. Не добавлять блок отправки сообщения и блок создания новой вкладки ChatGPT.
3. Скопировать examples/bureau-chat-activation-config.example.json во вне-репозиторный config.json и задать точный путь к EXE Opera и существующий workflowId. Не публиковать приватные URL чатов.
4. Создать в safe-bim-bridge/main отдельную папку jobs и уникальный тестовый JSON из примера с актуальными временами. Доступ к GitHub через gh должен быть уже авторизован.
5. Выполнить из локальной копии safe-bim-layer (каждая строка — отдельная команда):

    python scripts/bureau_chat_activation_gateway.py --db C:\LocalAI\bureau-gateway\state.sqlite --config C:\LocalAI\bureau-gateway\config.json scan

    python scripts/bureau_chat_activation_gateway.py --db C:\LocalAI\bureau-gateway\state.sqlite --config C:\LocalAI\bureau-gateway\config.json status

    python scripts/bureau_chat_activation_gateway.py --db C:\LocalAI\bureau-gateway\state.sqlite --config C:\LocalAI\bureau-gateway\config.json dispatch

6. В реальной Opera визуально подтвердить переключение на **ранее существовавшую** вкладку Д-03, отсутствие отправленного сообщения и отсутствие второго экземпляра чата. После этого зафиксировать доказательство:

    python scripts/bureau_chat_activation_gateway.py --db C:\LocalAI\bureau-gateway\state.sqlite --config C:\LocalAI\bureau-gateway\config.json confirm-tab d03-probe-20261020 --proof "Existing D-03 tab selected locally"

7. Только после удачной ручной проверки включать постоянный короткий опрос (если процесс завершён, опрос останавливается):

    python scripts/bureau_chat_activation_gateway.py --db C:\LocalAI\bureau-gateway\state.sqlite --config C:\LocalAI\bureau-gateway\config.json watch --interval 5

Указанный watch **является опросом**, а не push/WebSocket. Он не требует публичного локального HTTPS-сервера. Отдельный постоянно подключённый push-транспорт с безопасной аутентификацией ещё не создан. Код не устанавливает автозагрузку Windows, службу, не изменяет UI Dispatcher, Arena, PR #139, PLN и APA/main.

## Приёмочные требования

- Отдельный CI: синтаксис, тесты очереди, иммутабельность jobId, запрет отправки текста, блокировка повторных запусков и отказоустойчивость.
- Первый LIVE: уникальное тестовое событие GitHub фактически вызывает запуск Automa, переключение на существующую вкладку Д-03 подтверждено внешней квитанцией, никакого сообщения не отправлено.
- Дальнейшее расширение после LIVE: отдельные события SEND_REQUEST, CHAT_ACCEPTED, REPORT_PUBLISHED, DIRECTOR_REVIEWED; надёжная доставка и защита от дублей на каждом уровне.
- Статус CI PASS **не равен** LIVE PASS. Без доступа к установленной Opera результат только офлайн.

## Отношение к дипломному штабу

Д-01—Д-08 — исследовательские сотрудники. После публикации и регистрации документа возникает REPORT_READY, затем директор соответствующего направления принимает результат, после чего секретариат передаёт утверждённый пакет штабу. Этот маршрут описан как целевая система; в версии V1 единственный проверяемый адресат — Д-03, только переключение вкладки. Другие отделы, отправка и приём отчётов не объявляются реализованными.
