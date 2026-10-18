# APA research №1 — source follow-up, 2026-10-18 09Z

## Primary source verification through connected Opera
1. Graphisoft AC29 Multiply: https://help.graphisoft.com/AC/29/INT/_AC29_Help/030_Interaction/030_Interaction-96.htm . **Documented UI behavior**: duplicates selected element(s); Drag (linear/polyline), Rotate (arc), Elevate (vertical), Matrix (rectangular grid). **Programmatic call NOT_VERIFIED**; this page describes UI actions, not a JSON or SDK29 entrypoint.
2. Tapir 1.5.9 grouping source was opened via Opera: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementGroupingCommands.cpp . Exact per-command field schemas not extracted in this pass; NOT_VERIFIED.
3. Tapir 1.5.9 project commands source was opened via Opera: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp . Exact CreateHotlinkInstances schema not extracted in this pass; NOT_VERIFIED.
4. Tapir official release history: https://github.com/ENZYME-APD/tapir-archicad-automation/releases . Release notes for 1.5.6 explicitly mention GetGroupsOfElements, GetElementsOfGroups and Get/SetSuspendGroupsMode. This proves release-history existence, not installed 1.5.10 behavior.
5. Tapir repository README https://github.com/ENZYME-APD/tapir-archicad-automation documents AC29 add-on downloads; installed binary/commands NOT_VERIFIED.

## New operational distinction
- **Confirmed**: native AC29 GUI Multiply offers four high-level geometric patterns for a selection (including multiple selected elements).
- **Not confirmed**: a public command to invoke the same operation from APA. Do not equate UI availability with automation readiness.
- **Engineering consequence**: avoid introducing another element-by-element writer until native API gap and existing APA PR #159/#162 are compared.

## Candidate prioritization
| Candidate | Score (expert, 0–100) | Effort | Existence | Function | Programmable | Installation | Tests |
|---|---:|---|---|---|---|---|---|
| AC29 UI Multiply | 94 | С АДАПТАЦИЕЙ | verified | four patterns verified | NOT_VERIFIED | built-in | NOT_RUN |
| Tapir grouping | 89 | С АДАПТАЦИЕЙ | verified | read group commands in 1.5.6 release notes | exact API NOT_VERIFIED | AC29 download documented | NOT_RUN |
| Tapir hotlinks | 82 | С АДАПТАЦИЕЙ | verified | source exists | exact schema NOT_VERIFIED | AC29 download documented | NOT_RUN |

## Next questions (not instructions to user)
1. Does AC29 DevKit expose any Multiply-equivalent operation for a multi-element selection?
2. Which Tapir grouping command fields are accepted and returned at tag 1.5.9?
3. Which native-group operations in PR #159/#162 are already implemented?
4. Are module node and instance GUIDs stable after repeating placements and readback?

SOURCE=PARTIAL_VERIFIED; OFFLINE/BUILD/INSTALLED/LIVE=NOT_RUN. No changes to main, PLN, APX or installed add-ons.
