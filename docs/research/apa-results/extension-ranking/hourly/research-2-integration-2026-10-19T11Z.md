# APA №2 — AC29 — 19.10.2026 11Z
**SOURCE ONLY.** 30 технических проверок в [01–10](research-2-integration-2026-10-19T11Z-checks-01-10.md), [11–20](research-2-integration-2026-10-19T11Z-checks-11-20.md), [21–30](research-2-integration-2026-10-19T11Z-checks-21-30.md). Два собственных контрааудита — ниже. Никаких установок, кода, PLN/APX, LIVE.

**Входы:** [очередь №3](../NEXT_RESEARCH_PRIORITIES.md) 18.10 20Z, blob `2cb49edc410632c65503d8f17e93c58bc2d971d1`; [61 кандидатов](../candidates.json) blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`; [матрица 61](../priority_matrix_20261018.json) blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`; [задачи №2](audit-2026-10-18-20-tasks-2A.md), [продолжение](audit-2026-10-18-20-tasks-2B.md). №1: последний найденный [09Z checks](research-1-20261019T09Z-checks.md), основной 09Z и 10–11Z **не найдены**, последний полный [07Z](research-1-20261019T07Z.md). №3 после 20Z не найден. Канон [PROJECT_PLAN rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json), blob `c2ab2f9d606db1412c4031076103c267fc463f83`, только чтение.

**Новое:** [IfcDiff 0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcdiff/ifcdiff.py#L77-L253) по умолчанию geometry-only, shallow early-exit, исключает IfcFeatureElement и отключает opening subtractions. Нельзя считать его «полным отсутствием изменений» без дополнительной проверки. [IfcOpenShell document API](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/document/assign_document.py#L27-L103) позволяет привязать PDF к IFC-копии с последующим readback, но **не** определяет host GlobalId из PDF. [B3](https://github.com/dvikt33-ux/safe-bim-layer/pull/170) world coordinates не равны подтверждённой map CRS; [geolocation](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/geolocation.py#L147-L177) при отсутствии conversion возвращает входные XYZ.

## Матрица 10 решений
Оценки 0–100 — инженерная полезность, не замеры ускорения. Цепочки ≤3 внешних звеньев, через существующий Router.
| Готовый инструмент/версия | Цепочка и reuse | Контракт/блокер → решение | Балл, сложность/риск | Будущее ГОТОВО |
|---|---|---|---|---|
| IfcOpenShell document 0.8.5 LGPL-3+ | Router→B2 IFC-copy→api.document | PDF page/revision/SHA, host GlobalId неизвестен → ADAPTER/NOT_FOUND | 97 АДАПТАЦИЯ/высокий | 2 GUID, relation readback, source SHA |
| pdfplumber 0.11.10 MIT | Router→PR154/160→pdfplumber | rect/rotation/URI ≠ BIM host → REUSE | 96 БЫСТРО/средний | raw coords, NOT_HOST |
| IfcOpenShell geolocation 0.8.5 | Router→B3→util.geolocation | optional map CRS → ADAPTER | 98 БЫСТРО/высокий | missing CRS fail-closed |
| IfcOpenShell placement/shape 0.8.5 | Router→B3→util.placement | mirror/nonuniform; no double transform → ADAPTER | 96 АДАПТАЦИЯ/средний | 2 mirrored instances |
| IfcDiff 0.8.5 LGPL-3+ | Router→B1/V2→IfcDiff | shallow/opening exclusions → ADAPTER | 97 АДАПТАЦИЯ/высокий | attr+geometry+opening |
| IfcCSV 0.8.5 LGPL-3+ | Router→B2→IfcCsv.export | null='-' ambiguous, import writes → REUSE export-only | 90 БЫСТРО/средний | GUID/typed null SHA |
| bcf-client 0.8.5, BCF 2.1 | Router→B2→BcfXml | BCF ZIP, IFC GUID ≠ native → REUSE | 92 БЫСТРО/средний | ZIP/version/GUID |
| Graphisoft AC29 Python JSON | Router→AC29 API→publisher names | names не подтверждают выпуск → REUSE | 91 БЫСТРО/низкий | read-only build gate |
| Tapir '1.5.10' unverified | Router→Tapir Publisher→files | whitelist/APX SHA/output SHA → DEFER | 89 АДАПТАЦИЯ/высокий | nonempty selection+SHA |
| AC29 Hotlink/SceneWriter | Router→PR173 receipt→BIM Graph | scratch 69→119 GUID, 2 instances → REUSE forensic | 95 БЫСТРО/низкий | provenance+independent ACCEPTED |

## Контрааудит А — исходники, API, лицензии
1. Сверены tagged `ifcopenshell-python-0.8.5`, `pdfplumber v0.11.10`, официальная [AC29 API](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html) и PR #154/#160/#165/#166/#167/#170/#173, не SDK30.
2. IfcDiff shallow/geometry-only/opening exclusions; сравнение container объектами, а не явно GlobalId — **риск**, ложноположительность ещё не воспроизведена.
3. IFC2X3 DocumentId/ItemReference против IFC4 Identification; IFC GlobalId не равен доказанному Archicad GUID.
4. BCF default 2.1, IfcCSV меняет переданный список attributes, null превращает в '-'; автоматический Import запрещён.
5. Graphisoft SDK29 [29.3000](https://github.com/GRAPHISOFT/archicad-api-devkit/releases/tag/29.3000) под соглашением Graphisoft, не MIT. AC29 build 5101 и локальный Tapir 1.5.10/APX SHA не проверены.
6. [PR167 lock](https://github.com/dvikt33-ux/safe-bim-layer/pull/167/files) pin 0.8.5 не доказывает INSTALLED Windows 11. 8 GB VRAM не требуется для metadata, 48 GB RAM не гарантирует безопасный geometry diff.

## Контрааудит Б — монтаж, дублирование, безопасность
1. Reuse Router/B1/B2/B3/PR154/160/SceneWriter; никакого второго PLN writer, IFC движка, MCP сервера.
2. PDF→host готовый мост **NOT_FOUND**; минимальный adapter — доказанная карта page/mark/clip/SHA→IFC GlobalId, без угадывания по подписи.
3. Frames PDF points, IFC project units, IFC world SI, map CRS раздельны; identity при missing placement/CRS не означает PASS.
4. Fail-closed для orphan host, 2D mapped, cyclic placement, null CSV, incomplete diff; исходные IFC/PDF immutable.
5. PR173 saved/reopened scratch receipt не равен независимому ACCEPTED. Никаких повторов LIVE.
6. Opt-in, pinned source/wheel/adapter SHA, ограничения времени/памяти/размера, rollback отключением provider; 100× не заявлять.

**Архитектурные альтернативы:** PDF→IFC: новый native writer REJECT, выбрать B2+api.document на копии только с проверенным host. Геометрия: новый движок REJECT, выбрать B3+util.placement/geolocation. Diff: второй QA server REJECT, выбрать B1/V2+IfcDiff full categories+opening graph. BCF/Publisher: второй BCF server/autopublish REJECT, выбрать B2 ZIP+AC29 names-only.

**Gates:** SOURCE=сейчас; OFFLINE=fixtures IFC2X3/4 doc links, PDF rotation/no-host, mirror/nonuniform/no CRS/cycle, diff attr+geometry+opening, CSV null, BCF2.1; BUILD=тонкие адаптеры в отдельной ветке; INSTALLED=wheel/APX SHA+AC29 5101+rollback; LIVE=только отдельное разрешение scratch; ACCEPTED=независимый №3 SHA/GUID/units/negative cases. **ГОТОВО только ACCEPTED.**

**№3 (7):** IFC document link 97, CRS guard 98, mirror 96, IfcDiff full 97, BCF readback 92, CSV null 90, Publisher names gate 91. **№1 вопросы:** готовый PDF→IFC host bridge? IFC2X3/4 document fixtures? 2D mapped wrapper? IfcDiff GUID container/openings patch? BCF2→3 adapter? публичный Tapir 1.5.10 APX provenance?

Opera connector: `UNAVAILABLE Browser not connected`; использованы браузер GPT и GitHub. **SOURCE=30; audits=2; OFFLINE/BUILD/LIVE=0; INSTALLED_NOT_VERIFIED; ACCEPTED_NO; MODEL_MODE_NOT_VERIFIABLE.**
