# APA AC29 — исследователь №2, 2026-10-19 20Z

**Граница:** SOURCE-only; установки, PLN/APX, native calls, изменение кода, main, PR merge и канонического PROJECT_PLAN.json не выполнялись. 30 адресных SOURCE-проверок (ниже), два собственных контрааудита. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED в этом цикле: 0/0/0/0/0. MODEL_MODE_NOT_VERIFIABLE. Числа пользы — экспертные, не benchmark.

## Прочитано до исследования

- [Очередь №3 18Z](../NEXT_RESEARCH_PRIORITIES.md), blob b18d096e; [8 заданий I18-01..08](audit-2026-10-19-18-tasks-2.md), blob 65d942f4; [аудит №3 18Z](audit-2026-10-19-18.md), blob 0e2ed710.
- [Матрица](../priority_matrix_20261018.json), blob 9cb5e6f2, 61 кандидат; [каталог](../candidates.json), blob 87ee1c0b, 61 кандидат. Приоритеты каталогов не заменяют runtime-проверку.
- [Отчёт №1 18Z](research-1-20261019T18Z.md), blob 3614b672. Отчёты №1 19Z/20Z и аудит №3 19Z/20Z по ожидаемым путям на момент чтения НЕ НАЙДЕНЫ; продолжаем по последней подтверждённой очереди.
- PR [#173](https://github.com/dvikt33-ux/safe-bim-layer/pull/173) (head eee14936, LIVE-02 с отдельными ограничениями), [#175](https://github.com/dvikt33-ux/safe-bim-layer/pull/175) (head 24c19834, OFFLINE, не LIVE), [#162](https://github.com/dvikt33-ux/safe-bim-layer/pull/162) (group-first preview), [#171](https://github.com/dvikt33-ux/safe-bim-layer/pull/171) (один Hotlink LIVE), [#154](https://github.com/dvikt33-ux/safe-bim-layer/pull/154) (PDFVectors), [#160](https://github.com/dvikt33-ux/safe-bim-layer/pull/160) (PDF preflight, не hosted writer).
- Канон [PROJECT_PLAN.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json), blob 76234063, **revision 188** при чтении. Revision 182 — историческая редакция, не перезаписывать.

## Новый основной вывод: контракт Tapir не равен проверке результата

Tapir tag **1.5.9** в [CommandBase.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/CommandBase.cpp) (blob c39e4f34) возвращает **пустой GetResponseSchema()**; документационная схема отдельно выдаётся через **GetRawResponseSchema()** и включается в [AddOnMain.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp) (blob 9f44c2c2) через RegisterCommand. Причина: исходная проблема [#483](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/483) — ошибки вида {"error":{code,message}} отвергались строгой выходной схемой, Archicad отвечал 4009. Исправление [#544](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/544) отключило валидацию выходов **внутри Archicad**, сохранив схему для документации. Аналогичное устройство в tag 1.7.2 (blob 0d254367). Нельзя утверждать, что локальный APX с обозначением 1.5.10 побайтово совпадает с tag 1.5.9.

**Хорошая новость:** действующий APA [archicad_dynamic_commands.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/archicad_dynamic_commands.py) (blob c05017ee) уже реализует **DynamicCommands.validate_result**: проверяет документированную выходную JSON-схему и рекурсивно отвергает поля error / success=false. Следовательно, **REUSE, не второй валидатор и не MCP-сервер**. Остаточный риск — семантически неверный, но формально корректный результат (пустой массив или пустая строка).

## 30 технических SOURCE-проходов

Каждый пункт: вопрос → проверенный первоисточник/версия и точный контракт → блокер/вердикт → следующая проверка. Статус SOURCE означает анализ кода, не испытание в Archicad.

01. **Почему Tapir может скрывать ошибку 4009?** [Issue #483](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/483), воспроизведение AC28/Tapir1.5.5: выход error нарушает additionalProperties:false и required. Исправлено upstream позднее; **не переносить старое поведение на локальную 1.5.10**. Далее — сверить фактический GetAddOnVersion и error fixture.

02. **Как именно исправлено?** [CommandBase.hpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/CommandBase.hpp), blob 1cdf72bf: GetResponseSchema final, GetRawResponseSchema virtual. **REUSE upstream**, далее — локальный контракт.

03. **Есть ли host-side выходная проверка?** [CommandBase.cpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/CommandBase.cpp), blob c39e4f34: GetResponseSchema возвращает {}. **Host-side schema validation не является гарантией**, далее — APA validator.

04. **Куда попадает документированная схема?** [AddOnMain.cpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp), blob 9f44c2c2: RegisterCommand сохраняет GetRawResponseSchema в CommandInfo. **REUSE source catalog**, далее — pinned SHA.

05. **Валидирует ли APA вход?** [DynamicCommands.prepare](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/archicad_dynamic_commands.py), blob c05017ee: CONTRACTS._validator(...).validate(parameters), canonical JSON без NaN. **REUSE**, далее — malformed fixture.

06. **Валидирует ли APA выход?** [DynamicCommands.validate_result](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/archicad_dynamic_commands.py): output schema + recursive error/success=false. **REUSE**; семантический пустой ответ ещё не доказан.

07. **Как проверяется регистрация команды?** [DynamicCommands.probe_runtime](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/archicad_dynamic_commands.py): API.IsAddOnCommandAvailable, namespace+commandName. **REUSE**, но проверка наличия не доказывает поведение.

08. **Как предотвращён дрейф схемы?** [DynamicCommands.contract_hash](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/archicad_dynamic_commands.py): хеш имени, провайдера, версии, параметров, returns и implementationSHA256. **REUSE**, далее — сравнение со снимком локального runtime.

09. **Есть ли единый граф?** [DynamicCommands.run_workflow](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/archicad_dynamic_commands.py): последовательное выполнение с $result и существующим SceneWriter. **REUSE**, новый исполнитель REJECT.

10. **Почему GetHotlinks не равен полному реестру?** [Tapir ProjectCommands.cpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp), blob 99053b4c: дерево размещённых узлов; кэшированные не гарантированы. **REUSE только placed**, далее — SDK29 cached.

11. **Что значит пустой GetHotlinks?** [тот же ProjectCommands.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp): ошибки root/tree могут приводить к [] без error. **EMPTY_AMBIGUOUS**, далее — независимый SDK29 read-only контроль.

12. **Готов ли SDK для cached?** [DevKit29.3000 Hotlink](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/group___hotlink.html), blob 277e3122: ACAPI_Hotlink_GetHotlinkNodes(type,nodeRefList,enableUnplaced=true). **ADAPTER** в существующий SDK29 Bridge; публичная JSON-обёртка полного контракта NOT_FOUND.

13. **Как отличить node и instance?** [DevKit29.3000 Hotlink](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/group___hotlink.html): GetHotlinkInstances(nodeGUID, elementRefList). **ADAPTER**: отдельные GUID-типы; далее — N-instance reconciliation.

14. **Как отличить proxy от source?** [DevKit29.3000 Hotlink](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/group___hotlink.html): GetHotlinkProxyElementTable(instanceGUID, HashTable<GUID,GUID>), ключ proxy/значение source. **ADAPTER** только чтения; далее — инверсия mapping как отрицательная fixture.

15. **Есть ли готовое определение владельца?** [DevKit29.3000 Hotlink](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/group___hotlink.html): GetHotLinkOwner и GetContainingHotlinkGuid, APINULLGuid ≠ BADID. **ADAPTER**, далее — native/linked/deleted fixtures.

16. **Можно ли отличить cached от доступного источника?** [DevKit29.3000 Hotlink](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/group___hotlink.html): GetHotlinkSourceStatus(IO::Location,status), Missing/Available/NotAccessible/Incompatible/Offline/AuthCanceld. **ADAPTER**, fail-closed при неизвестном.

17. **Какие параметры размещения нельзя терять?** [DevKit29.3000 API_HotlinkType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/struct_a_p_i___hotlink_type.html): transformation, floorDifference, adjustLevelDiffs, skipNested, relinkWallOpenings, ignoreTopFloorLinks. **ADAPTER** к Graph, не пересчитывать координаты из имён файлов.

18. **Как устроен действующий Hotlink verifier?** [PR171 verifiers](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-native-hotlink-oneshot-20261018/scripts/apa_ac29_hotlink_native_verifiers.py), blob 8bf428f9: проверяет node, instance, origin, child hotlinkId. **REUSE**; новый SDK29 источник только дополнит.

19. **Как ограничена геометрия текущего batch?** [PR173 geometry](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/apa_ac29_hotlink_batch_geometry.py), blob 69685361: максимум 32, rotation=0, mirror=false, same floor, AABB tolerance 0.002 м. **Не расширять SOURCE на произвольные матрицы**, далее — отдельный gate.

20. **Есть ли второй native writer?** [PR173 batch](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/apa_ac29_hotlink_batch_oneshot.py), blob 7559f9fd: одна CreateHotlinkInstances + GuardedSave через существующий SceneWriter. **REUSE**.

21. **Может ли GetElementsByIFCIds скрыть ошибку?** [Tapir IFCCommands.cpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp), blob 401de117: FindElementsByGlobalId.IsErr() не передаётся как error; для запроса формируется пустой elements[]. **EMPTY_AMBIGUOUS**, не утверждать «IFC GUID отсутствует» без независимой проверки.

22. **Есть ли двойная IFC identity?** [тот же IFCCommands.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp): GetIFCIdsOfElements возвращает native elementId, ifcId, externalIFCId. **REUSE**, хранить три разных пространства ID.

23. **Как отражается ошибка IFC accessor?** [IFCCommands.cpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp): CreateElementObjectID.IsErr() выдаёт error, но GetGlobalId/GetExternalGlobalId.IsErr() преобразуются в пустую строку. **EMPTY_STRING_AMBIGUOUS**; далее — typed source-status.

24. **Есть ли готовый SDK IFC fallback?** [DevKit29.3000 IFC](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3000/docs/group___i_f_c.html): IFCAPI::GetObjectAccessor/GetGlobalId/GetExternalGlobalId; APIERR_CANCEL и APIERR_MODULNOTINSTALLED имеют разную семантику. **ADAPTER только если необходима дифференциация ошибок**, иначе REUSE IFC V2.

25. **Готовая библиотека-обёртка без MCP?** [MultiConn 0.9.4 pyproject](https://github.com/SzamosiMate/multiconn_archicad/blob/main/pyproject.toml), blob a2604470: Python >=3.12,<3.15; archicad>=29.3000, httpx, pydantic, psutil; MIT. **DEFER**: не заменять действующий transport, проверить локальный Python.

26. **Совместима ли MultiConn с локальным Tapir?** [MultiConn README](https://github.com/SzamosiMate/multiconn_archicad), blob c7f551bb: заявлена поддержка Tapir 1.7.1; автоматический выбор primary, background port scans, open/switch project. **Версия 1.5.10 не доказана**, потенциальный конфликт с точной привязкой PLN; REJECT как исполнитель.

27. **Может ли готовый MCP помочь без второго writer?** [Boti-Ormandi/archicad-mcp pyproject](https://github.com/Boti-Ormandi/archicad-mcp/blob/HEAD/pyproject.toml), blob 3ebaee7c: MIT, Python >=3.11, aiohttp/pydantic; get_docs доступен без Archicad, execute_script запускает код. **DEFER как источник схем; REJECT запуск сервера**.

28. **Почему нельзя ставить Boti-MCP ради схем?** [официальный README проекта](https://github.com/Boti-Ormandi/archicad-mcp): auto schema update/cache, версия Tapir в snapshot может опережать установленную; execute_script без sandbox. **SOURCE_ONLY**: при необходимости сравнить текст схем offline, не запускать MCP.

29. **Что добавляет SzamosiMate MCP?** [tapir-archicad-MCP 0.6.5 pyproject](https://github.com/SzamosiMate/tapir-archicad-MCP/blob/master/pyproject.toml), blob ecc09f27: MIT, Python >=3.12, mcp>=2,<3, multiconn-archicad==0.9.4. **REJECT**: второй слой управления/исполнения и дополнительная зависимость.

30. **Нужен ли новый механизм сохранения?** [PR175 save isolation](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-guarded-save-snapshot-20261019/scripts/apa_ac29_save_isolation.py), blob cf9ba7da: ScratchWriteLease кооперативен, snapshot SHA сверяется до/после, внешний Archicad не блокируется. **REUSE**, не приписывать OFFLINE-коду LIVE/ACCEPTED.

## Матрица интеграции — 9 конкретных решений

| Готовый инструмент → существующий интерфейс/адаптер → результат | Версия/лицензия | Повторное использование APA | Польза, трудоёмкость, риск | ГОТОВО |
|---|---|---|---|---|
| Tapir GetHotlinks → Router → placed inventory | Tapir tag1.5.9 MIT; local1.5.10 unverified | DynamicCommands + BIM Graph | 98; БЫСТРО; silent [] | runtime schema и независимый placed count |
| SDK29 GetHotlinkNodes(true) → existing SDK Bridge → cached inventory | DevKit29.3000 Graphisoft EULA | Router + Graph; адаптер NOT_FOUND | 99; АДАПТАЦИЯ; ABI | два счётчика, typed error, 0 writes |
| SDK29 proxy table/owner/instances → Graph provenance | DevKit29.3000 EULA | существующий Hotlink verifier + SceneWriter | 100; АДАПТАЦИЯ; GUID direction | proxy→source, node→N, 3 negative fixtures |
| SDK29 SourceStatus + node fields → source evidence | DevKit29.3000 EULA | существующий Graph, SHA манифесты | 98; АДАПТАЦИЯ; offline/auth | cache и source разные статусы |
| Tapir IFC GetIFCIdsOfElements → V2 identity | tag1.5.9 MIT | existing IFC V2 + Graph | 99; БЫСТРО; empty IFC ID | native/IFC/external IDs и failure gate |
| Tapir GetElementsByIFCIds → independent SDK/IFC V2 check | tag1.5.9 MIT + SDK29 EULA | existing IFC V2 | 98; АДАПТАЦИЯ; false not-found | 0 matches ≠ 0 errors, typed fallback |
| MultiConn 0.9.4 as potential Python wrapper, NOT executor | MIT, Python>=3.12; Tapir1.7.1 advertised | Router already does transport/validation | 58; ДОЛГО; auto primary/switch | только после доказанного отсутствия встроенной функции; сейчас DEFER |
| Boti-MCP / SzamosiMate-MCP schema catalogs (read-only comparison) | MIT, Python>=3.11 / >=3.12; MCP0.6.5 | existing DynamicCommands source catalog | 35; ДОЛГО; second executor | НЕ УСТАНАВЛИВАТЬ; REJECT runtime, source comparison optional |
| PR175 exact GuardedSave snapshot → existing SceneWriter | APA PR175 OFFLINE; no new license | GuardedSaveTransport + SQLite | 100; БЫСТРО reuse; external writer | независимый saved SHA + actual close/reopen + no replay |

**Цепочки не длиннее трёх внешних звеньев.** Нативные функции SDK29 существуют, но готовый публичный Tapir wrapper для cached/proxy/status не подтверждён: NOT_FOUND после просмотра GetHotlinks и альтернативных Python/MCP wrapper каталогов. Минимальный отсутствующий адаптер — *read-only* SDK29 command handler с типизированным JSON, нулём write scopes, проверкой APIERR, node/instance/source GUID, владельца, матрицы и статуса источника. Это **план**, не реализованный продукт. Не создавать новый исполнитель.

## Сравнение трёх архитектурных путей

**A — существующий APA Router + Tapir:** ноль установок, готовые схемы и проверки. Не видит надёжно cached/proxy, некоторые ошибки превращаются в []/""; выбран для placed и первичного IFC чтения.

**B — MultiConn/MCP поверх Tapir:** готовые typed Python wrappers, но auto primary, background discovery, execute_script и возможность переключать проекты конкурируют с существующими exact-PLN binding и SceneWriter. Кроме того, версии Python/Tapir не совпадают с доказанной локальной связкой. **REJECT как runtime**; документационные схемы можно сравнивать только SOURCE.

**C — существующий APA Router → ограниченный read-only SDK29 Bridge → штатные функции Hotlink/IFC → тот же BIM Graph:** наименьший путь для недостающей семантики, без второго writer; требует Graphisoft EULA, проверки API29/ABI/AC29 build5101, явной регистрации и отдельного разрешения на будущий BUILD. **Выбран для следующего исследования, не подключён.**

## Контрааудит А — исходники, версии, лицензии, точность API

- SOURCE проверен по blob/tag: Tapir1.5.9 CommandBase c39e4f34, AddOnMain 9f44c2c2, IFCCommands 401de117, MIT; DevKit29.3000 Hotlink 277e3122 и IFC, Graphisoft EULA; MultiConn0.9.4 a2604470 MIT; MCP0.6.5 ecc09f27 MIT; APA Router c05017ee. Версия команды (например, GetHotlinks 0.1.0) не равна версии APX.
- Tapir локально **обозначен** 1.5.10; его бинарный SHA и наличие конкретных новых команд не прочитаны. DevKit29.3000 ≠ доказательство готового APX для build5101; SDK30 не использовался как подтверждение.
- В отличие от старых исследований выявлено, что upstream Tapir **не применяет response JSON schema внутри Archicad**; существующий APA делает собственную проверку. Но JSON-валидность не обнаруживает семантически пустые IFC результаты. Нужен fail-closed.
- Временные затраты/ускорение, RAM, VRAM, диск не измерялись. Эти JSON/CLI/CPU операции не требуют GPU по документированному контракту; 8 GB VRAM не доказательство совместимости иных ML-кандидатов.

## Контрааудит Б — монтажный граф, дублирование, безопасность

- Единый маршрут остаётся APA Router → проверенный Tapir / SDK29 read-only adapter → BIM Graph → **существующий** SceneWriter при отдельно разрешённой записи. Не подключать Boti-MCP, SzamosiMate-MCP, MultiConn auto-switch как второй transport/writer.
- Три различаемых результата: FOUND, NOT_FOUND (проверка выполнена успешно, совпадений нет), UNKNOWN_ERROR (ошибка SDK/4009/empty ambiguous). Пустой список GetHotlinks или GetElementsByIFCIds не повышать до NOT_FOUND без независимого контроля.
- Не смешивать native GUID, Hotlink node GUID, instance GUID, proxy GUID, source GUID, IFC GlobalId и external IFC GlobalId. Не использовать нулевой GUID как ошибку без кода возврата.
- PR173 доказал конкретный native batch в отдельной сцене, не массовую произвольную трансформацию; PR175 только OFFLINE. Не повторять LIVE и не переиспользовать неизвестную операцию. Никаких чисел «100×».

## Воспроизводимые gates и откат (пока план)

**SOURCE:** закрепить tagged blob SHA, EULA, версии Python/SDK/Tapir, typed JSON контракты; сравнить локальный catalog с кодом. **OFFLINE:** fixtures: [] при ошибке, пустой IFC ID, внешний IFC ID отсутствует, node/instance/proxy inversion, cached-only, source Offline/AuthCancelled, несуществующий GUID, зеркальная матрица, неизвестный этаж; ни одного native call. **BUILD:** лишь после отдельного решения №3 — SDK29 read-only handler и компиляция для Windows x64; без замены Tapir APX. **INSTALLED:** проверка API.IsAddOnCommandAvailable и AC29 build5101, один точный порт/проект, 0 writes. **LIVE:** только разрешённая изолированная PLN, read-only counts + независимый native readback; записи не запускать этим поручением. **ACCEPTED:** независимая сверка исходных GUID, всех связей, ошибок, SHA источников и доказательство отсутствия изменений PLN. Откат исследовательского этапа — не выполнять установку; будущий adapter должен отключаться удалением регистрации/отключением отдельного add-on после резервирования и повторного контроля штатного Tapir, не удалять исходные файлы.

## Вопросы исследователю №1

1. Есть ли готовый **публичный SDK29 Hotlink read-only JSON wrapper** для GetHotlinkNodes(true), ProxyElementTable, SourceStatus с точной лицензией и tagged исходником? Если нет — NOT_FOUND.
2. Есть ли готовый read-only Python adapter, **не запускающий MCP-сервер**, для декодирования Tapir error/empty IFC ID без второго transport?
3. Есть ли в Tapir tag1.5.10/1.7.2 API-обёртка GetHotlinkSourceStatus или proxy table, которую можно доказать исходником?
4. Какая версия MultiConn гарантирует Tapir1.5.10, Python3.11 и **отсутствие auto-switch/сканирования**?
5. Есть ли штатный IFCAPI метод с явным кодом ошибки, отличающий «не найдено» от «модуль IFC недоступен»?
6. Есть ли официальный Graphisoft SDK29 sample для Hotlink provenance, пригодный как read-only адаптер к уже существующему Bridge?

## Координатору №3 — кандидаты на утверждение, без выполнения

1. **I20-01 (100):** IFC false-not-found: typed gate для GetElementsByIFCIds/IFC IDs, REUSE Router/V2.
2. **I20-02 (100):** Hotlink proxy→source и node→instances read-only SDK29 bridge, NOT_FOUND готового JSON wrapper.
3. **I20-03 (99):** cached vs placed и SourceStatus, read-only typed enum.
4. **I20-04 (99):** локальная проверка response schema/error semantics Tapir1.5.10 без установки.
5. **I20-05 (98):** защита идентичности GUID/этажей/матриц при Hotlink.
6. **I20-06 (98):** независимый SHA/close-reopen PR175 после разрешения отдельного gate.
7. **I20-07 (95):** сравнение каталогов MultiConn/MCP только SOURCE; runtime reject.

**Итог:** SOURCE_COMPLETE; никакого нового ACCEPTED. Не менять NEXT_RESEARCH_PRIORITIES.md — это полномочие №3.
