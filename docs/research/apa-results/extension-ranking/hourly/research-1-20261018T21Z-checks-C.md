# APA №1 21Z — 10 SOURCE-проверок C (21–30)
21. **ezdxf v1.4.5 pin.** GitHub tag `v1.4.5` commit `84ae31976940f99e6d5f4d3b2e9131da02b574fe`, LICENSE MIT, PyPI 16.10.2026 Python>=3.11. Контрааудит: docs stable 1.4.4 ранее отличались. №2: pinned Windows3.11/3.12 fixture.
https://github.com/mozman/ezdxf/tree/v1.4.5
https://pypi.org/project/ezdxf/1.4.5/

22. **Insert.virtual_entities ограничен.** `src/ezdxf/entities/insert.py` L603–650: возвращает геометрию первого INSERT, не все MINSERT; XCLIP не применяется, TEXT/MTEXT/ATTRIB с nonuniform неточны. №2: не считать virtual_entities полным результатом.
https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py#L603-L650

23. **MINSERT recursive_decompose уже готов.** `src/ezdxf/disassemble.py` L542–575: если `entity.mcount>1`, вызывает `recursive_decompose(entity.multi_insert())`. Контрааудит: PR168 C1 уже использует decomposition, новый provider не нужен. №2: 2×3 nested fixture.
https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py#L542-L575

24. **Нулевой шаг MINSERT.** `insert.py` L662–706: `multi_insert` применяет `done=set()` к offsets; одинаковые координаты выдаются один раз. `mcount` может быть больше числа уникальных ячеек. Контрааудит: ожидаемый count 6 при row/column spacing=0 может быть ложным. №2: explicit effective unique count.
https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py#L662-L706

25. **XCLIP не обрезает decomposition.** `disassemble.py` L557–563 предупреждает: clipping path игнорируется, возвращаются все entities. Контрааудит: визуально скрытая геометрия не должна становиться BIM автоматически. №2: fail-closed при active XCLIP.
https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py#L557-L563

26. **XClip метаданные готовы.** `src/ezdxf/xclip.py` L67–148: `has_clipping_path`, `is_clipping_enabled`, `is_inverted_clip`, `get_block_clipping_path`; 2D-only. Контрааудит: metadata ≠ clipping geometry. №2: enabled/inverted flags and uncertainty.
https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xclip.py#L67-L148

27. **MEP лицензия AC29.** Graphisoft AC29 `Modeling with MEP Designer`: `Available with Archicad Collaborate`; в AC28 иные условия. Контрааудит: entitlement пользователя NOT_VERIFIED. №2: license gate до native MEP.
https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-1.htm

28. **MEP расчёты/IFC fallback.** Graphisoft AC29 System Browser/Display ventilation data: Volume Flow/Velocity только cloud licenses, loops не рассчитываются; `Refresh MEP Properties` появился AC29.1.0. AC29 IFC Import «MEP elements, otherwise Objects» может породить непараметрические объекты. №2: version/entitlement+port mapping QA.
https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-34.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-37.htm
https://help.graphisoft.com/MEP/29/INT/_MEP_Designer_Help/085_MEPDesigner/085_MEPDesigner-49.htm

29. **Publisher AC29 уже поддерживает SAF.** Официальная справка `Publisher File Formats`: PDF, DWG/DXF translators, .mod, IFC translator, SAF из Structural Analytical Model views. Контрааудит: GUI ≠ callable SDK29/Tapir, A11.S08 остаётся BLOCKED. №2: только matrix command↔version↔installed evidence.
https://help.graphisoft.com/AC/29/INT/_AC29_Help/070_Documentation/070_Documentation-119.htm

30. **ifc4d-gantt 0.1.0 НЕ автономный HTML.** `brunopostle/ifc4d-gantt` HEAD `ed3779fa1ef5b34256a0fc07742ecc2135e22a98`, `__init__.py` L172–224: `cdn.jsdelivr.net/npm/jsgantt-improved@2.1.0` для JS/CSS, `schedule_name` и `ifc_filename` без HTML escaping; `json.dumps(tasks)` прямо внутри script. Контрааудит: README «standalone» опровергнут кодом; HTML/script injection только SOURCE_RISK, exploit не запускался. №2: не внедрять offline viewer, оставить util.sequence→JSON.
https://github.com/brunopostle/ifc4d-gantt/blob/ed3779fa1ef5b34256a0fc07742ecc2135e22a98/src/ifc4d_gantt/__init__.py#L172-L224

Итог C: 10 SOURCE checks; все OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED в текущем цикле NOT_RUN/NOT_CHECKED/NO.
