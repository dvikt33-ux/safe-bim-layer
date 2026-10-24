# APA №2 09Z — контрааудит А: API/версии/лицензии
1. Проверены tagged source ezdxf 1.4.5 recover/audit/xref/units/odafc, pdfplumber 0.11.10 page/geometry, IfcOpenShell 0.8.5 validate; это SOURCE, не wheel/runtime.
2. PR168 C1 uses ezdxf.readfile and recursive_decompose; no explicit recover Auditor receipt. V2 uses source SHA and new output guards. Drift local vendor unknown.
3. ezdxf MIT, pdfplumber MIT confirmed in tagged LICENSE files; IfcOpenShell COPYING+COPYING.LESSER mean check per component; ODA legal status NOT_VERIFIED.
4. Windows 11/AC29 5101/Tapir 1.5.10 not invoked. SDK30 is not SDK29. All 9 new routes NOT_INSTALLED.
VERDICT: 9 proposals SOURCE, 0 accepted.
