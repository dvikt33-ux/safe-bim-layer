# APA AC29 — №2, 2026-10-19 09Z
SOURCE ONLY: 30 проверок кода, 2 контрааудита; не runtime. №1 09Z: только checks, основного отчёта нет; №3 последняя очередь 18.10 20Z. Канон revision182 — чтение.
Находки: C1 использует ezdxf.readfile без Auditor; upstream recover.readfile возвращает (Drawing,Auditor). xref.find_xref может вернуть несуществующий Path: требуется is_file+SHA.
Матрица: DXF recover 98 ADAPTER; XREF manifest 97 ADAPTER; IFC validate 97 ADAPTER; MINSERT cells 96 ADAPTER; MEP owners 96 ADAPTER; DXF units 95 ADAPTER; PDF raw/derived 94 REUSE; PDF annotations 93 ADAPTER; ODA DWG 58 DEFER.
Источники: ezdxf 1.4.5 MIT; pdfplumber 0.11.10 MIT; IfcOpenShell 0.8.5 LGPL/GPL компоненты. ODA лицензия неизвестна.
OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED: не выполнялись. main, PLN/APX, код, PR, очередь и план не изменены. MODEL_MODE_NOT_VERIFIABLE.
