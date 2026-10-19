# APA №2 09Z checks 10-12
SOURCE ONLY. E1 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py ; E2 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py ; E3 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py ; E4 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py
10 XREF metadata? xref.py L124 dxf_info returns version/encoding/units/insertion base. ADAPTER dependency manifest; next 2 unit fixtures.
11 XREF attach? xref.py L249 attach creates INSERT with scale/rotation, units NOT auto-converted. DEFER any mutation; next unit conversion.
12 Missing XREF? xref.py L308 find_xref returns original Path if no match. ADAPTER mandatory is_file+SHA; next missing file fixture.
