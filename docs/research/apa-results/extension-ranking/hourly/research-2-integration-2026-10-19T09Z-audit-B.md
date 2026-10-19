# APA №2 09Z — контрааудит Б: граф/дублирование/безопасность
1. No second DXF/PDF/IFC parser: existing Router/V1/V2/C1/B2 and PR154 are reused.
2. DXF recover inside C1 would silently change accepted geometry; choose separate preflight. Fixes != clean. Source original SHA mandatory.
3. XREF embed mutates loaded graph; choose dependency-only manifest. find_xref returns Path even when missing: is_file required.
4. PDF URI/annotation/MCID are not host GUID. Crop/snap/curve_to_edges are derived, not lossless BIM geometry.
5. IFC schema validator != IDS; empty logger alone cannot prove all project requirements. ODA installation/licensing blocks DWG.
6. C1 decomposition bound 50000 and samples 5000; truncation never full PASS.
VERDICT: fail-closed, no model writes; ACCEPTED=NO.
