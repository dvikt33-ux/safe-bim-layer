# APA №1 — 30 предметных SOURCE-проверок, 2026-10-19 09Z

Каждый проход: функция → фиксированный первоисточник/строка → готовое поведение и ограничение → вопрос №2. Это 30 статических проверок, НЕ 30 runtime-тестов или продуктов.

Версии/лицензии: ezdxf 1.4.5 MIT, pdfplumber 0.11.10 MIT, IfcOpenShell 0.8.5 LGPL-3.0-or-later. Windows 11/Python 3.11–3.12 потенциально совместимы, локально НЕ проверено. RTX 4060/8GB VRAM для read-only Python API не требуется; пик RAM на 48GB неизвестен. ODA — внешняя программа с НЕПРОВЕРЕННОЙ лицензией. Tapir 1.5.10 не содержит автоматически эти Python API. SOURCE_CONFIRMED; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED не проверялись.

## Пинованные первоисточники
- E1: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py
- E2: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py
- E3: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py
- E4: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py
- E5: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/addons/odafc.py
- P1: https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py
- P2: https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py
- I1: https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/validate.py

## Проверки 01–30
01. **recover.readfile(filename,errors='surrogateescape')** — [E1:62](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L62). DXF: готовое восстановление + Auditor; исправление НЕ lossless. **Вопрос №2:** №2: отдельные SHA оригинала, ошибки и исправления.
02. **recover.read(stream:BinaryIO)** — [E1:89](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L89). DXF: бинарный поток, автокодировка, Auditor; текстовый поток не подходит. **Вопрос №2:** №2: подтвердить передачу исходных байтов.
03. **recover.explore(filename,errors='ignore')** — [E1:112](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py#L112). DXF: крайний recovery; документация предупреждает вероятную потерю данных. **Вопрос №2:** №2: forensic-only, запрет BIM-приёмки.
04. **Auditor.has_errors** — [E2:152](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L152). DXF: неисправленные ошибки, отличные от предупреждений. **Вопрос №2:** №2: fail-closed при errors.
05. **Auditor.has_fixes / has_issues** — [E2:157](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L157). DXF: фиксирует исправленные дефекты, clean != recovered. **Вопрос №2:** №2: журнал fixes в readback.
06. **Auditor.check_block_reference_cycles** — [E2:504](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L504). DXF: обнаруживает INVALID_BLOCK_REFERENCE_CYCLE перед рекурсией INSERT. **Вопрос №2:** №2: проверить guard до recursive_decompose.
07. **Auditor.check_owner_exist / entity.dxf.owner** — [E2:450](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L450). DXF: потерянные owners; корневой owner=0 иногда законен. **Вопрос №2:** №2: отличить валидный root от missing owner.
08. **Auditor.check_entity_linetype** — [E2:359](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py#L359). DXF: undefined linetype; BYLAYER/BYBLOCK исключения. **Вопрос №2:** №2: переиспользовать готовый audit.
09. **xref.dxf_info(filename)** — [E3:124](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L124). DXF: HEADER version, encoding, drawing units, insertion base point. **Вопрос №2:** №2: сохранить эти поля в source manifest.
10. **xref.define(...,overlay=False)** — [E3:209](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L209). DXF: attach транзитивен, overlay нет; не Archicad Hotlink. **Вопрос №2:** №2: квалифицировать вид внешней ссылки.
11. **xref.attach(...,insert,scale,rotation,overlay)** — [E3:249](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L249). DXF: размещение XREF через INSERT, риск конфликта имени. **Вопрос №2:** №2: проверить сохранность transform.
12. **xref.find_xref(filename,search_paths)** — [E3:308](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L308). DXF: поиск внешнего файла; missing dependency не пустая геометрия. **Вопрос №2:** №2: явный NOT_FOUND при отсутствии.
13. **xref.embed(...,load_fn,search_paths,conflict_policy)** — [E3:340](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L340). DXF: встраивание и конфликты имён; версия XREF может быть новее host. **Вопрос №2:** №2: QA ресурсов, без нового writer.
14. **xref.detach(block,xref_filename,overlay)** — [E3:413](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py#L413). DXF: возвращает Drawing; сохранение должен сделать вызывающий код. **Вопрос №2:** №2: не объявлять экспортом без файла/SHA.
15. **units.conversion_factor(source_units,target_units)** — [E4:180](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py#L180). DXF: unsupported/unitless -> TypeError; invalid enum -> ValueError. **Вопрос №2:** №2: unitless fail-closed, явный коэффициент.
16. **odafc.is_installed()** — [E5:102](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/addons/odafc.py#L102). DWG: проверяет внешний ODA File Converter в Windows. **Вопрос №2:** №2: без установки не заявлять DWG ready.
17. **odafc.readfile(filename,version=None,audit=False)** — [E5:117](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/addons/odafc.py#L117). DWG: ODA→временный DXF, отдельная лицензия/версия, исключения. **Вопрос №2:** №2: установить юридический блокер, не запускать.
18. **Page.annots** — [P1:272](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L272). PDF: rect+rotation, page_number, title, contents, URI; это аннотации, не физический host. **Вопрос №2:** №2: ANNOTATION_NOT_HOST + source SHA.
19. **Page.hyperlinks** — [P1:338](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L338). PDF: фильтр annots по uri, не все выноски. **Вопрос №2:** №2: не считать URI BIM-связью.
20. **Page.point2coord(pt)** — [P1:349](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L349). PDF: mediabox offset и инверсия Y; не масштаб BIM. **Вопрос №2:** №2: явно хранить систему координат.
21. **Page.process_object(obj)** — [P1:353](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L353). PDF: извлекает object_type/text с unicode normalization; метка не геометрия. **Вопрос №2:** №2: raw vs normalized text.
22. **Page.search(pattern,regex,case,main_group)** — [P1:508](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L508). PDF: текстовые совпадения с позициями; не физические анкеры окон. **Вопрос №2:** №2: не повторять PR160, provenance только.
23. **Page.crop(bbox,relative,strict)** — [P1:545](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L545). PDF: CroppedPage, возможное отсечение объектов. **Вопрос №2:** №2: источник+обрезанный bbox раздельно.
24. **Page.dedupe_chars(**kwargs)** — [P1:573](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L573). PDF: удаляет наложенные символы по tolerance; риск потери подписи. **Вопрос №2:** №2: не менять raw evidence.
25. **PDFPageAggregatorWithMarkedContent.begin_tag / MCID** — [P1:117](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/page.py#L117). PDF: tagged-content MCID опционален, не BIM GUID. **Вопрос №2:** №2: MCID только page-scoped.
26. **get_bbox_overlap(a,b)** — [P2:54](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py#L54). PDF: нулевое пересечение не всегда считается overlap. **Вопрос №2:** №2: зафиксировать boundary semantics.
27. **clip_obj(obj,bbox)** — [P2:76](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py#L76). PDF: меняет bbox/doctop копии, не точный контур кривой. **Вопрос №2:** №2: не использовать как точную геометрию.
28. **snap_objects(objs,attr,tolerance)** — [P2:151](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py#L151). PDF: сдвигает координаты к среднему кластера. **Вопрос №2:** №2: хранить source-vs-derived diff.
29. **curve_to_edges(curve)** — [P2:190](https://github.com/jsvine/pdfplumber/blob/v0.11.10/pdfplumber/utils/geometry.py#L190). PDF: аппроксимация кривой chord-edges; теряет точный Bézier PR154. **Вопрос №2:** №2: не подменять lossless vectors.
30. **ifcopenshell.validate.validate(path,json_logger,express_rules=True)** — [I1:401](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/validate.py#L401). IFC: типы/кардинальности/GlobalId/заголовки; не вся синтаксическая порча и не IDS. **Вопрос №2:** №2: отдельные PARSE/EXPRESS/IDS статусы.

## Сводка аудируемости
30/30 функций сверены с файлами фиксированных тегов. Установленный APA runtime, wheel↔tag, peak RAM, ODA лицензия, AC29/Tapir bridge и скорость не проверялись. Не предлагается второй writer, DXF-parser или PDF-recognizer. Исторические PR154/160/162/170 не являются новым LIVE доказательством.
