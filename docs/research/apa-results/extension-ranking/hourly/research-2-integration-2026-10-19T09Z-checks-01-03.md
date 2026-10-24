# APA №2 09Z checks 01-03
SOURCE ONLY. E1 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py ; E2 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py ; E3 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py ; E4 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py
01 DXF corruption? ezdxf v1.4.5 recover.py L62: readfile(path,errors='surrogateescape')->(Drawing,Auditor). C1 currently readfile only. ADAPTER preflight, no automatic repaired geometry; next strict fixture.
02 Binary input? recover.py L89: read(BinaryIO,errors) auto-detects encoding. Text stream wrong. REUSE binary input + SHA; next encoding fixture.
03 Salvage? recover.py L112: explore(errors='ignore') warns likely data loss. REJECT for BIM geometry, forensic only; next loss audit.
