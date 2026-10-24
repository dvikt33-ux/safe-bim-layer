# APA №2 16Z — матрица 10 путей подключения
Оценки — экспертная польза 0–100, не benchmark. Все пути используют существующий Router/SceneWriter/BIM Graph, без второго исполнителя.
| №/польза | Готовое средство и цепочка | Контракт / лицензия | Выбор и риск | ГОТОВО |
|---|---|---|---|---|
|1/100|APA GuardedSave→PR175 ScratchWriteLease+snapshot→SHA|Python stdlib; path/expectedSHA/snapshotSHA|REUSE, БЫСТРО, средний|OFFLINE races; future independent reopen|
|2/100|APA Router→Graphisoft AC29 JSON→Tapir structured GO|1.7.2 MIT; criterion XOR criterionXML|ADAPTER, высокий|exactly-one gate, XML+scope readback|
|3/99|Router→Tapir rich GetGraphicOverrideRules/Combinations→Graph|1.7.2 MIT; GUID/style/ordered IDs|ADAPTER, средний|inventory/count/order match|
|4/98|Router→Tapir GetViewSettings→name/GUID unique join|1.5.9 source; viewSettings[] per item|REUSE, средний|ambiguity rejected|
|5/96|Router→Tapir Grid→Graph|1.7.2 MIT; beg/end, GREL, warnings[]|DEFER write, высокий|capability, warning=0, readback|
|6/95|Router→Tapir MEP preferences→V2|1.7.2 MIT; Piping/Ventilation tables|ADAPTER read-only, средний|AC29 table GUIDs verified|
|7/97|Router→PR165 V2→IfcOpenShell util.system→Graph|0.8.5 LGPL; ports/owners/peers|ADAPTER, средний|all edges enumerated|
|8/92|Router→IFC V2→IfcOpenShell util.cost→QTO|0.8.5 LGPL; schedule, quantity, rate|ADAPTER, высокий|NULL/zero fail-closed|
|9/96|Router→PR168 C1→ezdxf XClip/MINSERT→provenance|1.4.5 MIT; WCS, mcount, clip flags|ADAPTER, высокий|RAW/VISIBLE separate; exact clip NOT_FOUND|
|10/97|Router→B1 validate(filepath)→PR170 B3|0.8.5 LGPL; PARSE/EXPRESS/IDS|REUSE+ADAPTER, средний|corrupt STEP rejected|
Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED = 0. Tapir 1.7.2 AC29 Win asset существует, но локальная 1.5.10 не проверена. Windows 11, 8GB VRAM и 48GB RAM не испытывались.
