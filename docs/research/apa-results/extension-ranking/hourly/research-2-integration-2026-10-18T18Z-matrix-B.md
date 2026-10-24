# APA №2 18Z — matrix 2/2

| Candidate | Score | Existing integration path | Cost and DONE |
|---|---:|---|---|
| Hotlink | 86 | Bridge → Tapir hotlink commands → AC29 | АДАПТАЦИЯ; verify source hash, node and child GUID. |
| IfcDiff | 87 | Existing APA external runner → IfcDiff JSON | БЫСТРО; compare geometry and relationships separately. |
| BCF2 | 83 | IfcTester reporter → BCF ZIP → BCF reader | АДАПТАЦИЯ; validate version and viewpoint GlobalId. |
| IfcPatch | 77 | Existing IFC export → prepared recipe → IFC QA | АДАПТАЦИЯ; immutable input and separate output. |
| SAF SDK | 65 | SAF XLSX → SDK 1.7.3 → typed evidence | ДОЛГО; mapping and dependency license gates. |

Licenses: Tapir MIT, IfcOpenShell LGPL-3+, SAF core Apache-2.0. All SOURCE only.
