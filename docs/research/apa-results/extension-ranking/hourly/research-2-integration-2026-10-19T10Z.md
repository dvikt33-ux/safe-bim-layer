# APA AC29 — исследователь №2, 2026-10-19 10Z
**Статус: SOURCE ONLY. Фактических предметных проверок 30, собственных контрааудитов 2.** Ни одной установки, сборки, live-команды, правки кода/PLN/APX/main/очереди №3/плана №182. MODEL_MODE_NOT_VERIFIABLE. Проверки статические, не runtime и не независимая приёмка.

## 0. Входные документы и приоритет
1. [Очередь №3](../NEXT_RESEARCH_PRIORITIES.md), blob `2cb49edc410632c65503d8f17e93c58bc2d971d1`, последнее изменение 18.10 20Z. Прямые задачи №2: [T2-20-01..04](audit-2026-10-18-20-tasks-2A.md), [T2-20-05..08](audit-2026-10-18-20-tasks-2B.md). Позднейшей очереди в прочитанном каталоге нет.
2. [Матрица 61](../priority_matrix_20261018.json), blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`; [реестр 61](../candidates.json), blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`. IFCMCP исключён из внедрения; используем существующий APA.
3. Исследователь №1: [09Z технические проверки](research-1-20261019T09Z-checks.md), blob `2340deb8c810a3a1d464a944a7f457ac498f80ef`; **основного 09Z отчёта не обнаружено**. Последний полный [07Z](research-1-20261019T07Z.md), blob `677cde858cdc13dc34936bedb3c38ca5773beb69`. Не ждём.
4. Канон `docs/research/apa-results/control/PROJECT_PLAN.json`, ветка `research/apa-verified-results-hub-20261010`, blob `c2ab2f9d606db1412c4031076103c267fc463f83`, revision **182**, только чтение.
5. Реальные APA PR: [#165 V2](https://github.com/dvikt33-ux/safe-bim-layer/pull/165), [#166 B1](https://github.com/dvikt33-ux/safe-bim-layer/pull/166), [#167 B2](https://github.com/dvikt33-ux/safe-bim-layer/pull/167), [#168 C1](https://github.com/dvikt33-ux/safe-bim-layer/pull/168), [#170 B3](https://github.com/dvikt33-ux/safe-bim-layer/pull/170), [#154 PDF](https://github.com/dvikt33-ux/safe-bim-layer/pull/154), [#160 PDF-host](https://github.com/dvikt33-ux/safe-bim-layer/pull/160), [#173 Hotlink](https://github.com/dvikt33-ux/safe-bim-layer/pull/173). Эти PR открыты; их наличие не означает установленный код.

## 1. Тридцать содержательных SOURCE-проходов
Каждая строка: **вопрос → фиксированный исходник/точные поля → блокер → решение → следующая проверка**. `E` — [ezdxf v1.4.5](https://github.com/mozman/ezdxf/tree/v1.4.5/src/ezdxf) MIT; `I` — [IfcOpenShell Python 0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python); лицензии подкомпонентов проверять отдельно.

### DXF 01–10
01. Повреждённый DXF? [E recover.py L62–85](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L62-L85): `recover.readfile(filename,errors='surrogateescape')->(Drawing,Auditor)`; `strict` даёт UnicodeDecodeError. **ADAPTER** preflight C1, SHA original и журнал; далее bad encoding.
02. Можно ли `explore` для BIM? [E recover.py L112–119](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L112-L119): возможна потеря данных. **REJECT** как BIM, только forensic; далее broken tag fixture.
03. Ошибка vs исправление? [E audit.py L151–164](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L151-L164): `has_errors/has_fixes/has_issues`. **ADAPTER** CLEAN/RECOVERED/UNRECOVERABLE, не один PASS; далее fixture 3 статусов.
04. Циклы BLOCK? [E audit.py L504–512](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L504-L512): `INVALID_BLOCK_REFERENCE_CYCLE`. **REUSE** Auditor до C1 decomposition; далее A→B→A.
05. owner=0 всегда ошибка? [E audit.py L450–464](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L450-L464): RootDictionary/TABLE исключения. **REUSE** готового Auditor; далее orphan owner.
06. `find_xref` гарантирует файл? [E xref.py L308–337](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L308-L337): последний return Path без exists. **ADAPTER** is_file+SHA, missing→NOT_FOUND; далее broken relative.
07. Метаданные XREF без embed? [E xref.py L124–139](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L124-L139): `dxf_info` version/encoding/units/base. **REUSE** source manifest; далее unit mismatch.
08. Неизвестные DXF units? [E units.py L180–195](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py#L180-L195): `conversion_factor` бросает TypeError для unsupported. **ADAPTER** UNKNOWN_UNITS; далее мм→м/unitless.
09. MINSERT уже раскрывается? [E disassemble.py L542–575](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py#L542-L575): `mcount>1` вызывает `multi_insert`; XREF/XCLIP не поддержаны. **REUSE** геометрии; **ADAPTER** cell provenance; далее 2×3.
10. 2×3 всегда 6 уникальных? [E insert.py L668–702](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py#L668-L702): нулевой spacing дедуплицирует offsets, rotation применяется, spacing не масштабируется. **ADAPTER** count declared vs unique; далее 2×3 с нулевым шагом.

### IFC 11–24
11. `validate(model)` видит parse errors? [I validate.py L401–427](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/validate.py#L401-L427): рекомендован filepath для C++ parser log. **ADAPTER** B1 parse-stage; далее malformed STEP.
12. Второй GUID validator нужен? [I validate.py L470–495](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/validate.py#L470-L495): уже проверяет duplicate `IfcRoot.UR1` и base64 GUID. **REUSE**, V2 отдельная инвентаризация; далее duplicate GUID.
13. IDS с нулём правил может PASS? [I ifctester/reporter.py L250–293](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifctester/ifctester/reporter.py#L250-L293): `status=True` до цикла и при 0 specs остаётся True. **ADAPTER** nonvacuous guard; далее empty IDS.
14. IDS XML всегда XSD-validated? [I ifctester/ids.py L56–65](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifctester/ifctester/ids.py#L56-L65): `ids.open(validate=False)` default. **ADAPTER** validate=True; далее bad XSD.
15. IFC2X3 и IFC4 MEP нужны разные движки? [I util/system.py L91–108](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L91-L108): `IsNestedBy` и `HasPorts` уже учтены. **REUSE**; далее 2 схемы.
16. `get_connected_port` выдаёт все связи? [I util/system.py L111–115](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L111-L115): возвращает первый peer. **ADAPTER** iterate all relations, не считать full graph; далее multi-peer.
17. Порт всегда имеет owner? [I util/system.py L118–125](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L118-L125): `get_port_element` может вернуть None. **ADAPTER** ORPHAN; далее ownerless port.
18. Безопасен ли `get_task_work_schedule`? [I util/sequence.py L272–280](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py#L272-L280): `get_task_work_schedule(parent) or get_task_work_schedule(task)` может повторно вызвать тот же task. **ADAPTER** bounded parent/visited; далее nested without schedule.
19. Безопасен nested task traversal? [I util/sequence.py L293–303](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py#L293-L303): recursive generator без visited. **ADAPTER** cycle/depth cap; далее A→B→A.
20. Деление на 0 в 5D? [I util/cost.py L63–87](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L63-L87): ZeroDivisionError подавляется. **ADAPTER** arithmetic precheck INVALID_RATE; далее divisor=0.
21. Сметная ставка всегда в графике? [I util/cost.py L337–350](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L337-L350): `get_cost_schedule(...).PredefinedType` без None guard. **ADAPTER** MISSING_SCHEDULE; далее orphan rate.
22. Ноль количества = отсутствует? [I util/cost.py L49–60](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L49-L60): 0 и None различаются. **REUSE** типизированного значения; далее zero/missing.
23. IFC scale=1 доказывает метры? [I util/unit.py L682–719](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/unit.py#L682-L719): без UnitsInContext возвращает 1. **ADAPTER** UNKNOWN_UNITS; далее IFC без units.
24. XYZ без CRS уже мировые? [I util/geolocation.py L147–155](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/geolocation.py#L147-L155): missing conversion→identity. **ADAPTER** NOT_GEOREFERENCED; далее CRS/no-CRS.

### APA 25–30 (патчи конкретных PR)
25. Второй Router нужен? [PR165 scripts/apa_high_density_entrypoint_v2.py](https://github.com/dvikt33-ux/safe-bim-layer/pull/165/files): существующий `native_command_router`, 12 READ_ONLY, source/adapter SHA. **REUSE**; далее installed factory hash.
26. C1 делает audit и отдельные MINSERT cells? [PR168 scripts/apa_dxf_geometry_c1.py](https://github.com/dvikt33-ux/safe-bim-layer/pull/168/files): `ezdxf.readfile` без Auditor; одна сборка на parent INSERT, хотя upstream раскрыл геометрию. **ADAPTER** только preflight/cell manifest; далее cell signatures.
27. Полный IFC schema QA уже есть? [PR166 scripts/apa_ifc_reports_b1.py](https://github.com/dvikt33-ux/safe-bim-layer/pull/166/files): `validate(model,express_rules=False)`, `schemaValid=not logger.statements`. **REUSE+ADAPTER** PARSE/BASIC/EXPRESS/IDS раздельно; далее malformed/WHERE.
28. B1 защищён от пустого IDS? [PR166](https://github.com/dvikt33-ux/safe-bim-layer/pull/166/files): `ids.open` default False, `idsPassed=bool(report.results['status'])`, ноль specs→True upstream. **ADAPTER**; далее empty IDS/XSD negative.
29. Нужно ли писать второй CSV/BCF? [PR167 scripts/apa_ifc_artifacts_b2.py](https://github.com/dvikt33-ux/safe-bim-layer/pull/167/files): `filter_elements`, `B2_SELECTION_EMPTY`, private IFC copy, `IfcCsv/IfcPatch/bcf-client`, SHA readback. **REUSE**; geometry equivalence остаётся false; далее selected GUID coverage.
30. Нужен ли новый native geometry writer? [PR170 B3](https://github.com/dvikt33-ux/safe-bim-layer/pull/170/files) даёт OBJ/GLB/bounds с unverified CRS; [PR173 Hotlink](https://github.com/dvikt33-ux/safe-bim-layer/pull/173) содержит saved/reopened scratch receipt; [PR160 PDF](https://github.com/dvikt33-ux/safe-bim-layer/pull/160) host GUID неизвестен. **REUSE**, только forensic; далее SHA/GUID/BREP readback без LIVE.

## 2. Матрица 10 решений (все оценки — экспертная польза, НЕ benchmark)
| Решение/версия/лицензия | Путь APA→готовый адаптер→библиотека→результат | Контракт, reuse, блокер | Вердикт/балл/трудность/риск | Будущий ГОТОВО |
|---|---|---|---|---|
| ezdxf 1.4.5 MIT recover+Auditor | Router→C1/V2→ezdxf→JSON | source SHA, clean/fixed/errors; recovered≠clean | ADAPTER 98 БЫСТРО средний | 3 отрицательных DXF, source unchanged |
| ezdxf 1.4.5 MIT XREF+units | Router→C1→xref→manifest | path/sha/$INSUNITS/transform; missing NOT_FOUND | ADAPTER 97 БЫСТРО средний | broken/nested/unitless cases |
| ezdxf 1.4.5 MIT MINSERT | Router→C1→multi_insert→cell evidence | parentHandle/row/col/unique offset/XCLIP unsupported | ADAPTER 96 АДАПТАЦИЯ средний | normal 2×3=6, zero-step explicit dedup |
| IfcOpenShell 0.8.5 validate | Router→B1→validate→JSON | path parse + basic schema + GUID; EXPRESS отдельно | REUSE+ADAPTER 99 БЫСТРО средний | malformed/duplicate/WHERE split statuses |
| IfcTester 0.8.5 IDS+ODS | Router→B1→ifctester→ODS | XSD, >0 specs, meaningful checks, ODS SHA | ADAPTER 98 БЫСТРО высокий | empty IDS NOT_VERIFIED, invalid XSD BLOCKED |
| IfcOpenShell 0.8.5 util.system | Router→PR165→util.system→BIM Graph | IFC2X3/4, owner/peer/flow; first peer incomplete | ADAPTER 96 БЫСТРО средний | orphan/multi-peer + GUID provenance |
| IfcOpenShell 0.8.5 util.sequence | Router→B1/V2→util.sequence→JSON | IfcTask/schedule, visited/depth, no scheduler writes | ADAPTER 94 АДАПТАЦИЯ высокий | 3 tasks, no schedule, cycle |
| IfcOpenShell 0.8.5 util.cost | Router→B1/V2→util.cost→QTO JSON | None≠0, denominator/rate/unit/currency guards | ADAPTER 93 АДАПТАЦИЯ высокий | zero/missing/div0/rate negative |
| AC29 Hotlink + APA SceneWriter | Router→PR173 receipts→BIM Graph readback | saved SHA/GUID/BREP; не повторять LIVE | REUSE 97 БЫСТРО низкий при read-only | forensic comparison, ACCEPTED separately |
| pdfplumber 0.11.10 MIT + PR154/160 | Router→PDFVectors→source provenance→IFC copy | page/revision/clip/SHA, unknown host GUID BLOCKED | REUSE+ADAPTER 94 АДАПТАЦИЯ средний | 2 IFC GUID readback, no native Create |

Лицензии: ezdxf/pdfplumber MIT; IfcOpenShell 0.8.5 базовый LGPL-3.0+ с отдельной проверкой ifctester/IfcPatch/IfcCSV wheel; SDK29 — условия Graphisoft, не MIT; локальный Tapir «1.5.10» без проверенной публичной подписи APX. [Graphisoft AC29 API](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html) содержит `GetProductInfo()` (build/language) и `IsAddOnCommandAvailable(AddOnCommandId)` — будущий read-only capability gate, НЕ вызов на build 5101. Windows 11/Python wheel→локальная версия не проверены. Для read-only metadata GPU 8 GB не требуется, пик RAM при 48 GB неизвестен: нужны ограничения source bytes, decomposition, recursion, output. Не использовать платные API/ODA.

## 3. Два сравнения архитектурных путей
**DXF:** А — новый parser/writer: отклонить, дублирует C1; Б — existing C1+ezdxf recover/Auditor preflight: выбрать. `explore` только forensic; rollback = выключить opt-in, сохранить original SHA.
**IFC QA:** А — второй IFC server: отклонить; Б — existing B1 + ifcopenshell.validate(filepath) + ifctester IDS nonvacuous gate: выбрать. Разделять PARSE/BASIC_SCHEMA/EXPRESS/IDS, не один `schemaValid=True`.
**MEP/4D/5D:** А — новый граф/планировщик/сметный движок: отклонить; Б — pinned util.system/sequence/cost через существующий Router/BIM Graph, bounded read-only: выбрать.
**Hotlink/PDF:** А — повторить native Clone/Hotlink или писать второй writer: отклонить; Б — прочитать существующие PR164/173/160 receipts с SHA/GUID/BREP, provenance без native write. В очереди №3 PR173 ещё помечен не LIVE, поздний PR173 имеет scratch saved/reopened receipt; это не независимый ACCEPTED, очередь менять только №3.

## 4. Собственный контрааудит А — исходники/версии/API/лицензии
1. Сверены pinned ezdxf v1.4.5 и ifcopenshell-python-0.8.5, а не main/SDK30. Установленный wheel↔tag, локальный Tapir APX 1.5.10, AC29 5101 runtime **не проверены**.
2. Исправлена потенциальная ошибка прежних отчётов: MINSERT уже раскрыт `recursive_decompose`; недостаток C1 — отдельный cell provenance, а при нулевом spacing число уникальных offsets меньше rows×cols.
3. В 0.8.5 `validate` уже проверяет duplicate GUID. B1 `validate(model)` не является полной проверкой parse log/EXPRESS/IDS.
4. В upstream IDS reporter 0 specs→status True, B1 принимает это как `idsPassed=True`. Статический путь ложного PASS доказан; runtime ещё нет.
5. `get_connected_port` выдаёт первый peer; `get_task_work_schedule` имеет риск повторной рекурсии; `calculate_applied_value` подавляет div0. Все SOURCE findings, не локальные crash receipts.
6. MIT для ezdxf/pdfplumber; лицензии отдельных компонентов IfcOpenShell и SDK Graphisoft не смешивать. Не приписывать INSTALLED из synthetic receipts.

## 5. Собственный контрааудит Б — монтаж/дублирование/ценность/безопасность
1. Проверен reuse V2 Router, B1 schema/IDS, B2 CSV/BCF, C1 DXF, B3 geometry, PR154 PDFVectors, PR160 PDF marks, PR173 Hotlink, исходный SQLite SceneWriter. Нет второго PLN writer.
2. Цепочки не длиннее существующего Router + 1–2 внешних библиотечных звена. Недостающие защитные проверки — **минимальные будущие адаптеры**, не изображены готовыми.
3. Запрещены auto-fix/writeback DXF, IFC `assign_cost_value`, 4D `cascade_schedule`, Hotlink replay, Publisher без whitelist. Отчёты — вне stable APA.
4. Требуемый manifest: source SHA, vendor version/tag/license, adapter SHA, IFC schema/DXF units, entity GUID/STEP ID, source-vs-world frame, truncation, nativeCalls=0, modelWrites=0. IFC GlobalId ≠ доказанный native GUID.
5. Fail-closed: empty IDS, missing XREF, missing CRS/units, orphan port/schedule/rate, cyclic task, div0→NOT_VERIFIED/NOT_FOUND/BLOCKED, не PASS.
6. Ограничения 48 GB RAM не проверены измерением: max file size, max decomposed entities, visited cap, report size. Ускорение 100× не заявлять.
7. PR173 и PR164 квитанции не заменяют независимый аудит и не дают права на повторный LIVE. Очередь №3 и revision 182 не менять.

## 6. План подключения — НЕ выполнять в этом цикле
**SOURCE (сейчас):** tagged sources, existing APA PR, contracts, audits.
**OFFLINE (после утверждения):** clean/fixed/corrupt DXF; MINSERT normal/zero step; XREF missing/nested; malformed IFC/duplicate; empty IDS; MEP orphan/multi-edge; 4D missing/cycle; 5D zero/div0; PDF SHA. Source immutable.
**BUILD:** только тонкие адаптеры при необходимости в отдельной ветке, никаких новых движков.
**INSTALLED:** opt-in existing Router, exact wheel/adapter/factory SHA, rollback отключением provider, source unchanged.
**LIVE:** только с отдельным разрешением, scratch, saved readback; сейчас НЕ разрешено.
**ACCEPTED:** независимая проверка №3 всех negative cases, exact SHA/GUID/BREP и отсутствия записи. Только тогда ГОТОВО. Измерение скорости — отдельный одинаковый baseline, не оценки пользы.

## 7. Передача
**№3 на утверждение (8):** B1 IDS empty-XSD guard 98; B1 parse-vs-schema 99; C1 recover/Auditor 98; XREF+units 97; MINSERT cell provenance 96; MEP multi-edge/orphan 96; 4D schedule cycle/missing 94; 5D zero/rate/currency 93.
**Вопросы №1:** есть ли pinned empty-IDS/XSD-negative fixture? как стандартизирован MINSERT unique-cell при zero spacing? есть ли готовый nested XREF overlay audit без embed? есть ли IFC2X3/4 multi-peer fixture? есть ли готовая проверка UnitBasis/currency без своего сметного движка? подтверждены ли wheel-лицензии ifctester 0.8.5?

**Итог:** 30 SOURCE-проходов, 2 контрааудита; OFFLINE=NOT_RUN, BUILD=NOT_RUN, INSTALLED=NOT_VERIFIED_THIS_CYCLE, LIVE=NOT_RUN, ACCEPTED=NO. MODEL_MODE_NOT_VERIFIABLE.
