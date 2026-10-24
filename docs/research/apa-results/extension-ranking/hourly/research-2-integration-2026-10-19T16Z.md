# APA AC29 — исследователь №2, 2026-10-19 16Z

Статус SOURCE ONLY. 30 статических проверок по источникам, два контрааудита; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED новых запусков нет. Это исследование, не внедрение.

Сначала прочитаны очередь №3 15Z, матрица и каталог 61, №1 09Z checks (№1 15Z main отсутствует), PR154/159/160/162/165/168/170/173, новый PR175, Tapir 1.7.2, IfcOpenShell 0.8.5, ezdxf 1.4.5.

**Новое:** канонический PROJECT_PLAN.json в исследовательской ветке 19.10.2026 15:54Z поднят с revision 182 до 183 (commit bd164f28f4ea1e634e7f2104beb1b2ea5175c462), A11.S03 переведён в IN_PROGRESS с lease до 19:54:18Z. Ревизия 182 прочитана по commit 049576378c961c5d7a9a62611f4091e3da70d309. Обе только чтение. PR175 предлагает cooperative lease и побайтовый snapshot GuardedSave; SOURCE, не INSTALLED.

**Приоритет:** не создавать второй SceneWriter/Router. Подключать готовые Tapir команды через Graphisoft JSON AC29 и existing Router; IFC/DXF через existing V2/C1/B3. Rich Graphic Override multi-key early return требует exactly-one gate. DXF XCLIP metadata доступны, но lossless clipped BIM adapter NOT_FOUND. Локальный Tapir 1.5.10 не сверен с upstream 1.7.2.

Полные проходы, матрица, два контрааудита и задачи №1/№3 должны быть опубликованы приложениями этого же цикла. MODEL_MODE_NOT_VERIFIABLE.
