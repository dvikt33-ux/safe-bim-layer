# APA №2 09Z checks 04-06
SOURCE ONLY. E1 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py ; E2 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py ; E3 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py ; E4 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py
04 Clean status? audit.py L152: has_errors = bool(errors), not fixes. ADAPTER explicit UNRECOVERABLE; next broken-owner fixture.
05 Repaired status? audit.py L157: has_fixes distinct; has_issues=errors OR fixes. ADAPTER RECOVERED_NOT_CLEAN; next recovered-vs-original diff.
06 Missing owner? audit.py L450: invalid owner may trash entity; root owner=0 may be valid. BLOCK autoaccept repaired DXF; next owner fixture.
