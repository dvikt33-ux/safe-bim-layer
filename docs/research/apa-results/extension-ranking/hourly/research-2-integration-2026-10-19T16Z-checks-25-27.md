# APA №2 16Z — SOURCE проверки 25–27
25. IfcOpenShell 0.8.5 util/cost.py L49–85: divide-by-zero swallowed; no quantity returns None. ADAPTER nonzero/NULL gate; next zero fixture.
26. Same source L328–356: get_cost_schedule may be None, get_cost_rate dereferences it. ADAPTER UNKNOWN_RATE; next missing schedule fixture.
27. APA PR168 C1 source L34–86: recursive_decompose returns RAW WCS, parentHandle, INSUNITS; XCLIP not applied. REUSE C1; next visibility metadata.
Sources: https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py ; https://github.com/dvikt33-ux/safe-bim-layer/pull/168
