# APA №2 09Z checks 25-27
SOURCE ONLY. Primary: https://github.com/mozman/ezdxf ; https://github.com/jsvine/pdfplumber ; https://github.com/IfcOpenShell/IfcOpenShell .
25 Snap? geometry.py L151 moves objects to cluster mean. ADAPTER raw-vs-derived diff; next tolerance fixture.
26 Curve edges? geometry.py L190 connects successive pts, not exact Bézier. REUSE PR154 raw path, reject edges for precise model; next cubic fixture.
27 IFC validate? IfcOpenShell 0.8.5 validate.py L401: validate(path,logger,express_rules=False)->None. ADAPTER inspect logger, not return value; next invalid IFC.
