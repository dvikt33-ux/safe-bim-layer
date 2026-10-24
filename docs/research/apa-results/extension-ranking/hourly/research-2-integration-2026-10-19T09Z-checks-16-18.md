# APA №2 09Z checks 16-18
SOURCE ONLY. Primary: https://github.com/mozman/ezdxf ; https://github.com/jsvine/pdfplumber ; https://github.com/IfcOpenShell/IfcOpenShell .
16 ODA availability? ezdxf v1.4.5 odafc.py L102: is_installed() checks Windows converter executable path, not license. DEFER; next signed version/license.
17 DWG read? odafc.py L117: readfile uses external converter and temporary DXF, can raise ODAFCNotInstalledError. DEFER; next official terms.
18 PDF annots? pdfplumber v0.11.10 page.py L272: annots parses Rect/rotation/title/URI. ADAPTER page+source SHA, not native host; next rotated fixture.
