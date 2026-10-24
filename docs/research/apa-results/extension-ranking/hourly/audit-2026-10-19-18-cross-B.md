# APA AC29 — контрааудит Б, 19.10.2026 18Z
Инженерная применимость и дублирование (независимый проход).
1. PR154 уже читает PDF/DXF; PR159 — no-replay continuation; PR160 — AP2 preflight без host; PR162 — group-first reuse; PR168 — DXF C1; PR173 — Hotlink batch receipt; PR175 — cooperative save lock.
2. Не создавать второй Router, SceneWriter, CloneNativeGroupV1, PDF/DXF parser, IFC serializer или новый journal. Предлагать только read-only адаптеры существующих маршрутов.
3. Node GUID, instance GUID, proxy GUID, source GUID — разные сущности. В GetHotlinkProxyElementTable ключ proxy, значение source. updateTime не SHA.
4. LP_XMLConverter читает GSM, но создаёт выходные XML/HSF. Обратные команды xml2libpart/hsf2libpart/x2l/hsf2l — WRITE; ни одна не запускалась.
5. IFC Hook — экспортный callback, не постоянная запись PLN. Проверить штатные IFC mappings до предложения новой регистрации.
6. PR175 scope=COOPERATING_APA_EXECUTORS_ONLY: внешняя запись не предотвращается. PR173 LIVE receipt не равно независимой приёмке.
7. Блокеры: нет локального Tapir1.5.10 readback, нет бинарной проверки guarded snapshot, №2 18Z не найден по ожидаемому пути, score_explanation устарел.
Вердикт SOURCE_PASS_WITH_GATES; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED новых 0.
