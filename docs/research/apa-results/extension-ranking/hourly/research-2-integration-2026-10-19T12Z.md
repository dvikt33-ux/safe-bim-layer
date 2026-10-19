# APA №2 — 2026-10-19 12Z: способы подключения готовых решений

**SOURCE ONLY: 30 адресных source-inspection, два независимых контрааудита; НЕ 30 runtime-тестов.** Без установки, изменения кода, PLN/APX, main, живых операций и изменения очереди №3. `MODEL_MODE_NOT_VERIFIABLE`.

## Прочитано первым
[Очередь №3](../NEXT_RESEARCH_PRIORITIES.md) blob `2cb49edc410632c65503d8f17e93c58bc2d971d1`, последняя 18.10 20Z; [задания 2A](audit-2026-10-18-20-tasks-2A.md), [2B](audit-2026-10-18-20-tasks-2B.md). [Матрица 61](../priority_matrix_20261018.json) blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`; [каталог 61](../candidates.json) blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`. №1: последние [09Z checks](research-1-20261019T09Z-checks.md), основной 09Z не найден; последний полный [07Z](research-1-20261019T07Z.md). №3 новее 20Z не найден. Канон [PROJECT_PLAN revision 182](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json) blob `c2ab2f9d606db1412c4031076103c267fc463f83`, только чтение.

Сверены исходники APA: [C1 PR168](https://github.com/dvikt33-ux/safe-bim-layer/blob/7589c5dcee1fb71edae64e1d3bc9b1de14693e8e/scripts/apa_dxf_geometry_c1.py), [V2 PR165](https://github.com/dvikt33-ux/safe-bim-layer/blob/5c0dc009e729db9834301b4a369512490a205ef7/scripts/apa_high_density_readonly_v2.py), [PDF PR154](https://github.com/dvikt33-ux/safe-bim-layer/blob/ca28e9b8003eeb3a38ca201ea96c0096e07b677f/scripts/apa_external_readonly.py), PR160/164/167/170/173. Тегированные версии: ezdxf 1.4.5 [MIT](https://github.com/mozman/ezdxf/blob/v1.4.5/LICENSE), pdfplumber 0.11.10 [MIT](https://github.com/jsvine/pdfplumber/blob/v0.11.10/LICENSE.txt), IfcOpenShell Python 0.8.5 [LGPL-3+](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/__init__.py). Windows 11 wheel hashes, local Tapir 1.5.10 APX provenance и SDK29 ABI не проверялись.

## 30 фактических проверок
Каждая: вопрос → фиксированный первоисточник → точный контракт → reuse/adapter/blocker → следующая проверка.

01. **C1 baseline?** APA PR168 C1:95-105: pin ezdxf==1.4.5; readfile(source), SHA before/after. **REUSE C1; preflight separately**; далее verify bad-DXF route.
02. **DXF recovery?** [E recover.py:62](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L62): readfile(filename,errors=surrogateescape)->Drawing,Auditor. **ADAPTER no source rewrite**; далее record fixes/errors.
03. **Binary recovery?** [E recover.py:89](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L89): read(stream:BinaryIO)->Drawing,Auditor. **REUSE original byte stream**; далее strict decode fixture.
04. **Forensic explore?** [E recover.py:112](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L112): explore(errors=ignore), likely data loss. **REJECT for BIM acceptance**; далее negative loss fixture.
05. **Unfixed errors?** [E audit.py:152](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L152): has_errors=bool(errors). **ADAPTER ERROR not PASS**; далее unrecoverable fixture.
06. **Repaired errors?** [E audit.py:157-163](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L157): has_fixes and has_issues distinct. **ADAPTER CLEAN/REPAIRED/ERROR**; далее fix log readback.
07. **Block cycles?** [E audit.py:504](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L504): check_block_reference_cycles -> INVALID_BLOCK_REFERENCE_CYCLE. **REUSE before recursive_decompose**; далее A→B→A.
08. **Owner exception?** [E audit.py:450](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L450): owner 0 legal for root/table. **REUSE Auditor, no blanket error**; далее root vs orphan.
09. **XREF header?** [E xref.py:124](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L124): dxf_info version/encoding/units/base. **ADAPTER source manifest**; далее version+unit fixture.
10. **Missing XREF?** [E xref.py:308-337](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L308): find_xref returns original Path even if missing. **ADAPTER is_file+SHA fail closed**; далее missing relative path.
11. **Attach overlay?** [E xref.py:209](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L209): define(...overlay=False), attached transitive. **REUSE metadata, not AC Hotlink**; далее nested XREF.
12. **XREF placement?** [E xref.py:249](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L249): attach insert/scale/rotation/overlay. **DEFER writes, inspect existing INSERT**; далее rotation+scale.
13. **Embed XREF?** [E xref.py:340](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L340): embed load_fn/search_paths/conflict_policy. **DEFER mutation**; далее conflict fixture.
14. **Detach XREF?** [E xref.py:413](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L413): detach returns Drawing; caller saveas. **REJECT export claim without file**; далее write authorization.
15. **DXF units?** [E units.py:180](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py#L180): conversion_factor; unitless unsupported. **ADAPTER UNKNOWN_UNITS**; далее mm→m fixture.
16. **MINSERT count?** [E entities/insert.py:659](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py#L659): mcount collapses zero-spacing axes. **ADAPTER raw vs effective count**; далее 2×3 zero spacing.
17. **MINSERT virtual?** [E entities/insert.py:668-702](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py#L668): multi_insert unique offsets; rotates offset, no scale. **ADAPTER C1 unique positions**; далее 6/3/1 cases.
18. **ODA DWG?** [E addons/odafc.py:102,117](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/addons/odafc.py#L102,117): is_installed and readfile use external ODA converter. **DEFER license/version not verified**; далее legal Windows check.
19. **PDF annotation?** [P page.py:273](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L273): annots Rect rotation/URI/title. **REUSE PR154/160; NOT_HOST**; далее rotation cases.
20. **PDF hyperlinks?** [P page.py:339](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L339): hyperlinks filters annots where uri!=None. **REJECT URI→BIM GUID**; далее verified host map.
21. **PDF coordinates?** [P page.py:349](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L349): point2coord mediabox offset, Y inversion. **ADAPTER PDF_TOP_LEFT_POINTS**; далее bbox transform.
22. **PDF search?** [P page.py:509](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L509): search regex/case returns text locations. **REUSE PR160; LABEL_NOT_OPENING**; далее physical anchor.
23. **PDF crop?** [P page.py:545](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L545): crop bbox relative/strict returns derived page. **ADAPTER source vs crop bbox**; далее boundary clipping.
24. **PDF dedupe?** [P page.py:573](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L573): dedupe_chars tolerance filters characters. **DEFER derived only, preserve raw**; далее overlap signature.
25. **PDF MCID?** [P page.py:117](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L117): begin_tag captures optional MCID. **REJECT MCID→Archicad GUID**; далее page scope.
26. **PDF clip?** [P utils/geometry.py:76](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py#L76): clip_obj rewrites bbox/doctop copy. **REJECT as lossless geometry**; далее Bézier crossing.
27. **PDF snap?** [P utils/geometry.py:151](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py#L151): snap_objects averages cluster coordinates. **ADAPTER derived diff+tolerance**; далее shift limit.
28. **PDF edges?** [P utils/geometry.py:190](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py#L190): curve_to_edges connects pts, not cubic control path. **REUSE PR154 m/l/c/h**; далее cubic controls.
29. **IFC validation?** [I validate.py:401](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/validate.py#L401): validate(f,logger,express_rules=False) excludes some parser/WHERE, not IDS. **ADAPTER PARSE/SCHEMA/EXPRESS/IDS**; далее corrupt STEP, empty IDS.
30. **MEP ports?** [I util/system.py:111](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L111): get_connected_port returns first edge; V2 already enumerates IfcRelConnectsPorts. **REUSE full V2 + owner/flow**; далее 3 IFC fixtures.

## Интеграционная матрица: 10 решений
Все цепочки начинаются с существующего APA Router, без второго исполнителя и с максимум двумя внешними звеньями. Польза 0–100 — экспертная, не benchmark.

| Инструмент/версия → способ подключения | APA reuse, контракт и ограничение | Выбор; польза; сложность/риск | Критерий ГОТОВО (будущий) |
|---|---|---|---|
| ezdxf recover 1.4.5 | Router→C1 preflight→recover→JSON Auditor | ADAPTER 98 БЫСТРО/средний | CLEAN/REPAIRED/ERROR + SHA |
| MINSERT 1.4.5 | Router→C1→multi_insert; declared≠unique | ADAPTER 97 АДАПТАЦИЯ/средний | 2×3=6; zero spacing 3/1; handles |
| XREF 1.4.5 | Router→C1→find_xref/dxf_info, missing Path possible | ADAPTER 97 БЫСТРО/высокий | exists+SHA+version+units |
| DXF units 1.4.5 | Router→C1→conversion_factor, unitless blocked | ADAPTER 95 БЫСТРО/высокий | мм→м; UNKNOWN_UNITS |
| ODA via ezdxf 1.4.5 | Router→C1→odafc→external ODA | DEFER 55 ДОЛГО/высокий | license/version/Windows, converted SHA |
| PDF annots 0.11.10 | Router→PR154/160→Page.annots/search | REUSE 93 БЫСТРО/средний | page/rotation/URI; NOT_HOST |
| PDF Bézier 0.11.10 | Router→PR154→raw m/l/c/h; curve_to_edges lossy | REUSE 96 БЫСТРО/средний | cubic control points preserved |
| PDF provenance 0.11.10 | Router→PR154→page/MCID/raw vs derived | ADAPTER 91 АДАПТАЦИЯ/средний | page bbox/transform/SHA; MCID≠GUID |
| IFC validate 0.8.5 | Router→B1/PR167→validate+IfcTester | ADAPTER 99 БЫСТРО/высокий | PARSE/SCHEMA/EXPRESS/IDS, 0 checks ≠ PASS |
| MEP util.system 0.8.5 | Router→PR165 V2→full relations+owner/flow | ADAPTER 98 БЫСТРО/средний | 3 IFC fixtures, all peers, GlobalId |

## Альтернативы и NOT_FOUND
DXF: новый parser/writer **REJECT**, выбрать C1+Auditor preflight. MINSERT: «row×column всегда столько же физических размещений» **REJECT**, выбрать upstream `multi_insert`+raw/unique/geometry counters. PDF: MCID/URI/label→host GUID **REJECT**; выбрать PR154/160 provenance + доказанный host lookup. Готовый bridge PDF label→Archicad host **NOT_FOUND**: минимально недостаёт проверенной таблицы source SHA/page/mark/physical opening/host GUID, не угадывать по тексту. MEP: `get_connected_port` first-edge **REJECT**; выбрать существующий V2 полный `IfcRelConnectsPorts` + `get_port_element/get_ports`. IFC relation не доказывает нативную MEP-связь AC29.

## Контрааудит А: исходники, API, лицензии
(1) Проверены E/P/I фиксированных тегов и лицензии; ODA — отдельная внешняя лицензия, НЕ проверена. (2) C1 уже pin `ezdxf==1.4.5`, readfile, recursive_decompose, source+adapter SHA; V2 перечисляет связи; PR154 сохраняет raw m/l/c/h. Не создавать дублирующие ядра. (3) `find_xref` действительно возвращает исходный Path при missing, `multi_insert` действительно дедуплицирует offsets; это SOURCE, не Windows LIVE. (4) `validate` не покрывает весь STEP syntax и IDS; MCID и URI не являются GUID. (5) SDK30 не доказательство SDK29, локальный Tapir 1.5.10 SHA не известен.

## Контрааудит Б: монтаж, польза, безопасность
(1) Каждый путь Router→C1/PR154/V2/B1→готовая библиотека, максимум два внешних звена; не новый исполнитель. (2) Fail-closed статусы: MISSING_XREF, UNRECOVERABLE_DXF, UNKNOWN_UNITS, PDF_NOT_HOST, IDS_ZERO_CHECKS, MEP_RELATION_UNVERIFIED. (3) DXF declared row×column, unique offsets и число геометрических примитивов — разные знаменатели. (4) PDF raw Bézier/bytes/text хранить отдельно от crop/snap/dedupe; PDF points, DXF INSUNITS, IFC SI/WCS и map CRS не смешивать. (5) Для метаданных GPU 8GB не нужен; peak RAM при 48GB не измерен. Limits file/recursion/time, SHA readback, rollback opt-in. (6) PR173 saved/reopened scratch не равен независимому ACCEPTED; PR164/Hotlink не повторять.

## Будущие безопасные gates — НЕ запускались
SOURCE=этот отчёт. OFFLINE=DXF clean/repaired/error, XREF missing, A→B→A, MINSERT 2×3 normal/zero, unitless; PDF rotation/MCID/Bézier/crop; IFC corrupt STEP/empty IDS/3-port. BUILD=тонкие adapters в отдельной ветке с regression. INSTALLED=opt-in Windows 11 pinned wheel+SHA+rollback; без перенастройки текущих процессов. LIVE=только отдельное разрешение scratch AC29 5101. ACCEPTED=независимый №3 readback SHA/GUID/units/negative fixtures. **ГОТОВО только ACCEPTED**, ускорение не измерялось.

## Передача
№1 вопросы: готовый XREF graph validator с overlay/SHA? MINSERT 2×3 zero-spacing fixture? официальный PDF MCID→IFC GlobalId bridge? полный IFC2X3/4 MEP owner/flow traversal? лицензия ODA Windows 11? negative IDS/EXPRESS fixtures?
№3 семь кандидатов для утверждения (не утверждены): IFC validation 99; DXF recover 98; MEP owners 98; MINSERT 97; XREF manifest 97; PDF provenance 96; DXF units 95. **SOURCE=30, контрааудитов=2; OFFLINE/BUILD/INSTALLED/LIVE этого цикла=0; ACCEPTED=NO.**
