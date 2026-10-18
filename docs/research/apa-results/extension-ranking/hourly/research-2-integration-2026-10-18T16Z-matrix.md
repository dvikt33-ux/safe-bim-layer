# APA AC29 16Z — integration ranking

| Candidate | Score | Effort | Decision |
|---|---:|---|---|
| IfcDiff via existing APA JSON runner | 91 | QUICK | REUSE |
| Publisher via existing Tapir/SDK29 Bridge | 90 | ADAPT | whitelist + output manifest |
| IfcTester IDS to BCF2 | 88 | ADAPT | GUID/viewpoint check and package terms |
| IfcPatch ExtractElements | 86 | ADAPT | IFC subset + relationship audit |
| Hotlink instances | 84 | ADAPT | node/instance/child GUID |
| IfcQuery | 75 | QUICK | only if 3 independent QA checks |
| SplitByBuildingStorey | 64 | ADAPT | DEFER spanning GUID coverage |
| MEP mixed transition | 58 | LONG | BLOCKED |
| SAF to PyNite | 44 | LONG | NOT_FOUND ready converter |

Scores are engineering estimates, not measured acceleration. Existing APA Router, SceneWriter, BIM Graph, IFC reader and external JSON runner must be reused. No installations or model operations. SOURCE only.
