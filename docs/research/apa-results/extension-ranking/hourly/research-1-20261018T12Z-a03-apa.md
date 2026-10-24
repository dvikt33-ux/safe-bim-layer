# APA 12Z checks 15–20 — APA code audit

15. AP-2026 PDF page16 contains ОК-1..ОК-4 and door marks; these are text, not physical opening anchors. Counteraudit: AP not same site as KR-2022.

16. PR160 apa_ap2_massops_preflight.py requires wall host GUID, type, story, size, rotation/flip; mark midpoint NOT an opening. Counteraudit: read-only preview, PR OPEN.

17. PR154 apa_external_readonly.py preserves PDF_TOP_LEFT_POINTS and cubic Bezier; scaleConfirmed=false. Counteraudit: primitives not BIM semantics, PR OPEN.

18. PR162 group_strategy.py COPYABLE={Column,Beam,Object}; Wall/Slab/Window/Door excluded. Counteraudit: not whole-house group support.

19. PR162 enforces 2..128 members, <=32 placements, members*placements<=200. Counteraudit: planner policy, not SDK limit.

20. PR162 requires sourceRef and externally supplied dependenciesVerified/nativeReadbackVerified/groupReadbackVerified. Counteraudit: boolean assertion without evidence is not proof.
