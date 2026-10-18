# APA AC29 — focused research: high-level operations — 2026-10-18 09 UTC

## Evidence inspected
- Current research instructions: NEXT_RESEARCH_PRIORITIES.md, branch research/apa-extension-ranking-hub-20261018.
- Independent audit: hourly/audit-20261018T08Z.md.
- Recovered researcher report: hourly/research-1-20261018T08Z.md (summary only; not original evidence).
- Official Archicad 29 Multiply help: https://help.graphisoft.com/AC/29/INT/_AC29_Help/030_Interaction/030_Interaction-96.htm (referenced by audit; programmatic SDK API NOT_VERIFIED).
- Tapir source: https://github.com/ENZYME-APD/tapir-archicad-automation (exact command signatures NOT_VERIFIED in this cycle).

## Findings and implementation implications
1. **Group operations** — P0. A successful aggregate CreateGroups response is insufficient to prove each group was created. Require element GUID → group GUID mapping, cardinality, error list and readback by GetGroupsOfElements. Local Tapir 1.5.10 support NOT_VERIFIED. Compare with PR #159/#162 before proposing code.
2. **Multiply** — P0. User-interface Multiply is documented for AC29, but this is not evidence of an exposed Python/Tapir/SDK29 batch command. Public programmatic invocation NOT_VERIFIED. Do not label a UI command as automation-ready.
3. **Group replication** — P0. Compare three strategies: native group clone, module/hotlink instance, and vectorized element copies. Preserve transforms, source identifiers, dependency links, and undo semantics. Hotlink defaults may inherit tool settings: test contract before any write.
4. **DXF units** — P0. Nested blocks can have units different from document units; preserve block-local transform and unit conversion before BIM coordinate reconstruction. Source: https://ezdxf.readthedocs.io/en/stable/concepts/units.html (link from recovered summary, not independently re-fetched).
5. **PDF→BIM** — P1. No verified three-anchor scale calibration, physical opening endpoints, or error budget in current reviewed reports. Do not claim ready for model write.

## Ranked next actions (expert priority, not measured speed)
| Action | Benefit | Effort | Status |
|---|---|---|---|
| Per-group readback and mapping | high | low | SPEC_READY / LIVE_NOT_VERIFIED |
| Deduplicate Tapir grouping vs APA PR #159/#162 | high | low | NEEDS_SOURCE_DIFF |
| Native group Multiply SDK29 search | high | medium | NOT_VERIFIED |
| Hotlink module replication contract | high | medium | NOT_VERIFIED |
| DXF transform + units normalization | high | medium | NEEDS_SAMPLE |
| Raster2Seq on Windows 8GB | uncertain | high | NOT_VERIFIED |

## Verification gates
SOURCE=PARTIAL (links known; exact signatures not inspected this cycle).
OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_CHECKED; LIVE=NOT_RUN; ACCEPTED=NO.

## Next precise questions
1. Which command signatures and output schemas exist in Tapir 1.5.9, 1.5.10 and 1.7.1 for grouping and hotlinks?
2. Does the AC29 SDK expose group Multiply, and through which class/function, if any?
3. What does PR #159/#162 already implement, down to command name and per-element error handling?
4. On which AR/KR sheet are three independent dimension anchors available for geometric calibration?

No main/PLN/APX/code modifications; research only.
