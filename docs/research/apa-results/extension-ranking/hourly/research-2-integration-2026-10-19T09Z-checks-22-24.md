# APA №2 09Z checks 22-24
SOURCE ONLY. Primary: https://github.com/mozman/ezdxf ; https://github.com/jsvine/pdfplumber ; https://github.com/IfcOpenShell/IfcOpenShell .
22 Text dedupe? page.py L573 dedupe_chars changes char set. Preserve raw evidence; next overlapping text fixture.
23 Bbox overlap? geometry.py L54: zero width/height edge cases have nontrivial semantics. ADAPTER boundary policy; next touching boxes.
24 Clip? geometry.py L76 clip_obj updates bbox/doctop copy, not true Bézier clipping. REJECT as exact geometry; next curved boundary.
