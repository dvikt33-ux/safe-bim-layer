# APA 03Z — independent counteraudits

Audit A (source/version): Graphisoft Python ac29.b3000commands was checked against official documentation. SDK source was checked at Graphisoft archicad-api-devkit tag 29.3100. Hotlink/renovation/property/database symbols exist in C++ SDK, but a Tapir 1.5.10 JSON binding is not demonstrated. Graphisoft DevKit license is proprietary, not MIT. GetLocOrigo is user origin, not survey origin; SetActualRenovationFilter mutates state. No local Windows11/AC29 build5101 testing. Result: SOURCE_PASS, INSTALLED/LIVE_NOT_VERIFIED.

Audit B (utility/deduplication): PR159/162 already cover native groups and CloneNativeGroupV1; PR154/160 already cover PDF. PR173 reports batch Hotlink LIVE saved/reopened (69 to 119 GUID), so a new Hotlink writer is redundant. Researcher 2 already covers Publisher names and attribute inventory; this cycle only identifies missing layout QA. C1/C2 native read-only zone/component functions are highest priority; C3/C5/C6 are SDK-only pending a verified existing binding. BBox is not BREP, related-to-zone is not geometric adjacency. No benchmark and no ACCEPTED result. Canonical plan revision182 was read, not edited.

30 SOURCE passes are recorded in checks-A and checks-B; all other stages NOT_RUN or NOT_VERIFIED. MODEL_MODE_NOT_VERIFIABLE.
