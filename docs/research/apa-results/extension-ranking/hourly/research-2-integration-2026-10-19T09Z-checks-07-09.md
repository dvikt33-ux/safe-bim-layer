# APA №2 09Z checks 07-09
SOURCE ONLY. E1 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/recover.py ; E2 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/audit.py ; E3 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py ; E4 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py
07 Cyclic blocks? audit.py L504: check_block_reference_cycles detects INVALID_BLOCK_REFERENCE_CYCLE. REUSE before recursive_decompose; next self-cycle fixture.
08 C1 recursion? APA PR168 apa_dxf_geometry_c1.py: MAX_DECOMPOSED=50000; excess raises C1_DECOMPOSITION_LIMIT. REUSE limit; next oversized fixture.
09 MINSERT cells? C1 analyze() groups by parent INSERT handle after recursive_decompose; cell provenance absent. ADAPTER Insert.multi_insert per cell; next 2x3 fixture.
