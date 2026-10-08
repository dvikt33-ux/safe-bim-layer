# Architectural AI checkpoint 28 — native visual QA: Graphic Overrides, highlights, selection and 3D drill-down

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–27

## Executive conclusion

A separate SBIM model-violation viewer is no longer justified for the AC29 MVP.

Archicad already provides two complementary native visualization layers:

1. persistent project/view visualization through Custom Properties + Graphic Override Rules/Combinations;
2. ephemeral exact-GUID drill-down through Element Highlight + Selection + Zoom + Show Selection in 3D.

Tapir already wraps the most important ephemeral primitives, including per-element RGBA highlights and zoom.

Recommended split:

`persistent status -> SBIM Review Status property -> stable Graphic Override Combination`

`interactive finding -> exact failing GUIDs -> Tapir HighlightElements -> ZoomToElements / selection -> optional ShowSelectionIn3D`.

Rule IR, evidence and legal provenance remain external/authoritative; Archicad visualization is only a projection.

## 1. Graphic Overrides are a full public API surface

Official Graphisoft API exposes CRUD for:
- Override Rules;
- Override Rule Groups;
- Override Combinations;
- rule ordering/moving;
- active Override Combination;
- visually overridden image generation.

Observed public functions include:
- ACAPI_GraphicalOverride_CreateOverrideRule;
- ACAPI_GraphicalOverride_ChangeOverrideRule;
- ACAPI_GraphicalOverride_DeleteOverrideRule;
- ACAPI_GraphicalOverride_CreateOverrideRuleGroup;
- ACAPI_GraphicalOverride_ChangeOverrideRuleGroup;
- ACAPI_GraphicalOverride_DeleteOverrideRuleGroup;
- ACAPI_GraphicalOverride_CreateOverrideCombination;
- ACAPI_GraphicalOverride_ChangeOverrideCombination;
- ACAPI_GraphicalOverride_DeleteOverrideCombination;
- ACAPI_GraphicalOverride_SetActualOverrideCombination;
- ACAPI_GraphicalOverride_GetVisualOverriddenImage.

`API_OverrideRule` contains:
- GUID;
- name;
- style;
- criterionXML.

`API_OverrideRuleStyle` contains the actual visual overrides for surfaces/fills/pens/lines/contours.

## 2. Do not dynamically generate criterionXML unless unavoidable

Graphic Override rule criteria use Archicad's criteria system. The public rule structure stores criteria as XML.

The API documentation does not expose a pleasant typed Rule-criteria AST. Graphisoft's own guidance points developers toward producing/inspecting criteria XML from Archicad configurations.

Therefore dynamic criterionXML generation for every Rule Result is unnecessary complexity.

Preferred architecture:
- create a small fixed property group once;
- create stable GO rules/combinations once in template or setup;
- update only element property values during checks.

## 3. Persistent SBIM review property

Recommended minimal property:
`SBIM Review Status`

Candidate enum values:
- OK;
- Error;
- Warning;
- Unknown;
- Changed;
- NotVerified.

Optional additional lightweight properties:
- SBIM Primary Rule ID;
- SBIM Finding Count;
- SBIM Last Verified Revision.

Do not store full legal source text/evidence in these properties.

## 4. Persistent Graphic Override projection

Create stable rules such as:
- SBIM Error;
- SBIM Warning;
- SBIM Unknown;
- SBIM Changed;
- SBIM Not Verified.

Each rule filters by the custom property value.

Create one or several combinations:
- `SBIM Review`;
- `SBIM Errors Only`;
- `SBIM Changed Since Verify`.

Saved Views can store the Graphic Override Combination.

The open MIT connector already supports changing a saved View's `graphicOverrides` setting by combination name.

Conclusion:
persistent QA visualization should be declarative and property-driven.

## 5. Graphic Override is a projection, not source of truth

Do not make color/GO status authoritative.

The Project Compiler retains:
- RuleResult;
- exact measured values;
- applicability;
- legal source/version;
- dependency coverage;
- Action Digest;
- evidence;
- project revision.

GO status is regenerated from authoritative results.

This allows deleting/rebuilding visualization without losing compliance state.

## 6. Native temporary exact-GUID highlight

Official API provides:
`ACAPI_UserInput_SetElementHighlight`

Input semantics:
- map from element GUID to individual RGBA color;
- optional `wireframe3D` for non-highlighted elements;
- optional color for non-highlighted elements.

It works in:
- Floor Plan;
- Sections;
- 3D window.

`ACAPI_UserInput_ClearElementHighlight` clears temporary highlights.

After changing highlight state, the view must be redrawn.

This is ideal for interactive Rule/Issue drill-down because it requires no model mutation.

## 7. Tapir already wraps temporary highlighting

Current Tapir contains `HighlightElementsCommand` registered since version 1.0.3.

Tapir input includes:
- `elements`;
- `highlightedColors`;
- `wireframe3D`;
- `nonHighlightedColor`.

An empty elements array clears highlights.

Tapir source calls:
- `ACAPI_UserInput_SetElementHighlight`;
- `ACAPI_UserInput_ClearElementHighlight`;
- redraw.

Tapir already contains examples, including multi-color highlighting and dimming/wireframe context.

Decision:
do NOT write a custom highlighting bridge.

## 8. Native zoom and selection

Official Archicad APIs provide:
- element selection;
- deselect all;
- zoom to selected;
- zoom to explicit element GUIDs.

Tapir already wraps `ZoomToElements`.

The MIT open connector additionally exposes:
- `get_selection`;
- `set_selection`;
- zoom modes including elements and selection;
- `show_in_3d` for all / selection / explicit elements.

## 9. 3D isolate path

The MIT connector's `show_in_3d {mode:'elements'}` performs:
1. resolve explicit element GUIDs;
2. clear selection;
3. select the requested elements;
4. call Archicad `Show Selection in 3D`;
5. leave them selected;
6. later `show_in_3d {mode:'all'}` restores all elements.

This is simple enough to:
- use through that provider where compatible;
- port into AC29 if Tapir does not already expose an equivalent command;
- or keep as a very thin residual command.

It is not a custom viewer.

## 10. Recommended drill-down workflow

`RuleResult / Issue selected`
-> obtain affected GUID(s)
-> HighlightElements with severity colors
-> ZoomToElements
-> optionally set selection
-> optionally Show Selection in 3D
-> optionally capture current view/image
-> user inspects/fixes
-> clear temporary highlight
-> incremental recheck.

All these steps are native/open primitives.

## 11. Persistent versus ephemeral projection

Use persistent Property + Graphic Override when:
- user wants an overview of many findings;
- status should survive navigation/session;
- drawings/views need a review overlay;
- status is useful in schedules/filtering.

Use temporary Highlight when:
- user selects one finding;
- exact GUID set is already known;
- no BIM data should be mutated;
- multiple individual colors are useful;
- context should be dimmed or wireframed.

Use Issue/BCF when:
- finding must persist as a work item;
- comments/coordination are required;
- external exchange is needed.

These are complementary, not duplicate systems.

## 12. VISUAL-QA-01

On AC29 scratch project:
1. create/reuse `SBIM Review Status` enum property;
2. assign Error/Warning/Unknown to fixture elements;
3. create or import stable GO rules/combo;
4. attach combination to saved View;
5. verify 2D/3D appearance;
6. update status property and verify automatic visual update;
7. save/reopen;
8. verify View retains combination.

Acceptance:
no custom scene/viewer required for persistent overview.

## 13. HIGHLIGHT-01

Using existing Tapir `HighlightElements`:
1. color three element groups differently;
2. dim non-highlighted model;
3. test wireframe3D true/false;
4. verify Floor Plan;
5. verify Section;
6. verify 3D;
7. clear highlights with empty array;
8. ensure no model modification/revision side effect.

## 14. DRILLDOWN-01

From a synthetic Rule FAIL:
1. retrieve affected GUIDs;
2. highlight them;
3. zoom to them;
4. select them;
5. show only them in 3D;
6. capture screenshot/view if needed for Issue evidence;
7. restore Show All in 3D;
8. clear highlight;
9. rerun check after edit.

Measure total interaction latency.

## 15. Graphic Override limitations

Graphic Override criteria remain Archicad criteria semantics.

Surface-based criteria can have caveats where final visible surfaces are inherited/altered by connections, openings, model edits or Solid Element Operations.

Therefore:
- use explicit SBIM status properties for Rule projection;
- do not try to reconstruct arbitrary final-face compliance solely through GO surface criteria;
- use evaluated geometry/material provenance only when a rule truly needs final evaluated face semantics.

## 16. Roadmap deletion

STOP / DO NOT BUILD:
- custom violation 3D viewer;
- custom per-GUID highlight renderer;
- custom selection manager;
- custom zoom-to-finding implementation;
- custom persistent color-overlay database;
- dynamic GO criterion generator for ordinary SBIM statuses.

KEEP:
- thin mapping from Rule/Issue result to native visualization;
- one small governed SBIM review property schema;
- stable GO template/configuration;
- optional thin ShowSelectionIn3D wrapper if provider coverage requires it;
- screenshots/captures only where useful as evidence.

## Strategic conclusion

The model itself remains in Archicad and the review UX should stay there.

Best AC29 visualization stack:

`Rule IR result`
-> `Property + Graphic Override` for persistent overview
or
-> `Tapir HighlightElements + Zoom/Selection/3D isolate` for interactive inspection
-> `Issue/BCF` for persistent work item.

This eliminates the need for an SBIM model viewer in the MVP.