# SOURCE checks 16–20

16. PR165 source L260–279: INSERT counted once, transformsApplied=false. Verdict: MINSERT grid not expanded; next ezdxf.
17. ezdxf 1.4.5 Insert.mcount>1, row_count/column_count/spacing. Verdict: ready array metadata; next expansion.
18. Insert.multi_insert() yields virtual INSERT for each MINSERT grid cell. Verdict: use existing library, no custom loop; next WCS.
19. Insert.dxf.insert is OCS, Insert.matrix44() maps block to WCS. Verdict: coordinate provenance required; next clipping.
20. virtual_entities() ignores XCLIP and MINSERT beyond first, nonuniform TEXT/ATTRIB can be wrong. Verdict: warnings, not full geometry QA; next units.

Primary: https://ezdxf.readthedocs.io/en/stable/blocks/insert.html and https://github.com/dvikt33-ux/safe-bim-layer/blob/5c0dc009e729db9834301b4a369512490a205ef7/scripts/apa_high_density_readonly_v2.py#L260-L279.
