# Architectural AI checkpoint 32 — native Navigator Add-On viewpoints for SBIM reports and drawing sources

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–31

## Executive conclusion

Archicad Navigator Add-On Viewpoints are substantially more capable than a metadata tree.

A custom Add-On viewpoint can:
- live in Project Map as root/group/leaf;
- carry Add-On-owned payload;
- define supported View settings;
- open its own native Archicad window/tab;
- generate a serialized 2D Drawing source through CreateIDFStore;
- report model element dependencies for drawing up-to-date checks;
- be cloned from Project Map into View Map;
- then participate in the normal Drawing/Layout/Publisher workflow.

Therefore stable SBIM reports do not need a separate browser/dashboard document system.

Recommended split:
- interactive model review -> Highlight / Issues / native Model Check / selection;
- stable tabular/document reports -> Navigator Add-On Viewpoints;
- authoritative facts/evidence -> Project Compiler store;
- layout/release -> normal Archicad Drawings + Publisher.

## 1. Native viewpoint data model

`API_NavigatorAddOnViewPointData` represents:
- root;
- group;
- leaf.

Observed fields include:
- guid;
- parentGuid;
- displayId;
- displayName;
- itemType;
- iconId;
- Add-On-owned `data` handle;
- `viewSettingsFlags` for leaf nodes.

Public CRUD exists:
- ACAPI_Navigator_CreateNavigatorVPItem;
- ACAPI_Navigator_GetNavigatorVPItem;
- ACAPI_Navigator_ChangeNavigatorVPItem;
- ACAPI_Navigator_DeleteNavigatorVPItem;
- children enumeration.

Creation is explicitly in Project Map.

## 2. View Map path is native

Official API:
`ACAPI_Navigator_CloneProjectMapItemToViewMap(sourceItemId, parentItemId, createdItemId)`
clones a Project Map Navigator item into View Map.

Leaf nodes expose `API_NavigatorViewSettingsFlags` so the Add-On declares which saved View settings are meaningful for its content.

This means SBIM report viewpoints can use the normal saved-view pipeline instead of inventing an external report registry.

## 3. Callback interface is a real document contract

`INavigatorCallbackInterface`, registered through `ACAPI_Navigator_RegisterCallbackInterface`, includes:
- OpenView;
- OpenSettings;
- CreateIDFStore;
- GetElemsForDrawingCheck;
- NewItem;
- DeleteItem;
- RenameItem;
- GetIcon;
- merge/version compatibility callbacks and context/teamwork behavior.

`OpenView(viewPointID, newWindow)` is called on normal Navigator Open/Open in New Tab actions.

The Add-On chooses how to open/render the content.

## 4. CreateIDFStore makes the viewpoint a Drawing source

`CreateIDFStore(...)` is called when a drawing from the viewpoint is created or updated.

The callback returns:
- opaque serialized drawing store;
- clip-box dimensions;
- bounding box;
- padding;
- GUIDs of model elements represented/dependent on the viewpoint.

The standard pattern is:
1. start Archicad drawing-data session;
2. create normal 2D primitives such as Text/Line/Fill;
3. stop drawing-data session;
4. return generated IDF memory and bounds.

Therefore a compliance summary, decision register or release report can be generated as native Archicad 2D drawing content and placed on layouts.

## 5. Drawing freshness can be dependency-aware

`GetElemsForDrawingCheck(viewPointID, elems)` is called when Archicad checks whether a placed Drawing is current.

For model-derived reports, return relevant model GUIDs so normal drawing status can participate in release decisions.

However SBIM reports often also depend on non-element facts:
- RuleSet/legal-source revision;
- Property Definitions;
- global project preferences;
- external calculation/evidence;
- Project Compiler version.

These cannot be represented solely by `elems`.

Therefore each report viewpoint must also carry an external/project-side report digest and regenerate when that digest changes.

Do not assume native element dependency checking covers legal/external dependencies.

## 6. Good first SBIM viewpoint leaves

Recommended stable leaves:
- SBIM Compliance Summary;
- Open Blocking Findings;
- Verification Coverage Summary;
- Decision Register;
- Release Evidence Summary;
- MEP Calculation Summary where a sheet/report is required;
- Structural Coordination Summary;
- Normative Basis / RuleSet Revision Summary.

Do not create one Navigator leaf per low-level rule or per individual finding.

Individual findings belong in Issues/BCF and interactive drill-down.

## 7. Add-On data payload should be minimal

`API_NavigatorAddOnViewPointData.data` can persist Add-On-owned data.

Do NOT serialize the whole report or legal evidence graph into this payload.

Recommended payload:
- schema version;
- stable report kind / report ID;
- optional user formatting/configuration;
- last rendered Project Compiler revision/digest;
- migration/version marker.

Authoritative report content remains derivable from Project Compiler state.

This makes merge/version recovery manageable.

## 8. OpenView architecture

Recommended `OpenView` behavior:
- open one native MyDraw/custom drawing window associated with viewpoint GUID;
- render the same deterministic report model used by CreateIDFStore;
- allow Open in New Tab semantics where practical;
- expose navigation actions from report rows to model GUIDs through Highlight/Zoom/Issue drill-down.

A rich browser UI is not required for the MVP.

If a later interactive dashboard proves valuable, it can coexist, but stable reporting should remain Navigator-native.

## 9. Real-world implementation evidence

Public repository `kuvbur/AddOn_SomeStuff` contains an implementation of exactly this pattern:
- Navigator Add-On leaf;
- OpenView -> MyDraw window;
- table renderer using normal 2D Text/Line/Fill primitives;
- CreateIDFStore -> StartDrawingData -> Draw -> StopDrawingData;
- drawing bounds;
- window validator;
- GetElemsForDrawingCheck;
- New/Delete/Rename viewpoint callbacks.

Its documentation reports runtime self-test success for the table/drawing-data path on an earlier Archicad version.

### Licensing boundary

`kuvbur/AddOn_SomeStuff` is GPL-3.0.

Decision:
- use it as architectural/reference evidence;
- DO NOT copy/adapt its implementation into our code unless the project's licensing strategy explicitly accepts GPL obligations;
- implement our thin AC29 bridge independently from Graphisoft's public API contract.

## 10. Complexity is localized

The custom code needed is not a general document system.

Minimal modules:
- `SbimNavigatorProvider` — root/group/leaf CRUD and callback lifecycle;
- `SbimReportModel` — deterministic rows/cells from already-computed facts;
- `SbimReportRenderer2D` — small Text/Line/Fill renderer into current DrawingData session;
- `ReportDigest` — external/global dependency fingerprint;
- row action mapping to existing Highlight/Zoom/Issue tools.

No separate browser, PDF engine, sheet manager or layout engine is required.

## 11. Table renderer implementation rule

Do not over-generalize early.

MVP renderer only needs:
- title;
- fixed columns;
- wrapped text;
- simple row heights;
- grid/borders;
- basic fills;
- deterministic paper-space font sizes;
- multipage/split only when a real report requires it.

Use normal Archicad 2D primitives so Drawings remain native.

Do not build HTML/CSS rendering inside the Add-On just to generate a sheet table.

## 12. Report update model

Recommended digest:

`ReportDigest = hash(`
` report_kind,`
` project_revision,`
` relevant RuleResult digests,`
` relevant element facet digests,`
` RuleSet/legal-source revision,`
` external analysis run IDs,`
` formatting schema version`
`)`.

On:
- element/global events;
- reconnect reconciliation;
- RuleSet update;
- external-result update,

mark affected report leaves dirty.

Render only on OpenView / Drawing update / release preparation.

## 13. NAV-SBIM-01

AC29 live test:
1. register callback interface;
2. create root `SBIM`;
3. create groups `Checks`, `Decisions`, `Reports`;
4. create one leaf under each;
5. save PLN;
6. close/reopen;
7. verify GUID/name/payload persistence;
8. rename/delete/new item lifecycle;
9. verify callback object lifetime;
10. inspect Teamwork behavior later if/when needed.

## 14. NAV-VIEWMAP-01

1. create `SBIM Compliance Summary` leaf in Project Map;
2. set viewSettingsFlags;
3. clone to View Map with official clone API;
4. verify saved scale/pens/layers behavior;
5. rename source and saved view independently;
6. save/reopen.

## 15. NAV-DRAWING-01

1. render deterministic 3x5 SBIM table through DrawingData;
2. return IDF store/bounds;
3. create Drawing from saved SBIM View;
4. place it on Layout;
5. update source data;
6. verify Drawing becomes/currently reports out-of-date as expected;
7. update Drawing;
8. publish Layout/PDF through existing Publisher stack;
9. verify text/line/fill fidelity.

## 16. NAV-DEPENDENCY-01

Test Drawing freshness for:
- direct dependent model element edit;
- Property Definition change;
- RuleSet/legal-source change;
- external analysis result change;
- report formatting change.

Determine which dependencies Archicad catches through `GetElemsForDrawingCheck` and which require SBIM report-digest invalidation.

## 17. NAV-MERGE-01

Before production:
- merge a PLN containing SBIM viewpoints into another;
- duplicate display IDs/names;
- Save As;
- older/newer file format path if relevant;
- deleted report kind;
- payload schema migration.

Implement deterministic collision/migration policy before relying on navigator data for durable project state.

## 18. Roadmap changes

STOP / DEFER:
- separate report-document dashboard;
- custom sheet report registry;
- custom report PDF generator;
- custom report placement engine;
- browser UI solely for printable compliance/decision tables.

KEEP / SMALL NATIVE BRIDGE:
- Navigator Add-On viewpoint provider;
- minimal deterministic 2D report renderer;
- report digest/global invalidation;
- optional lightweight interactive UI only if it adds value beyond native drill-down.

## Strategic conclusion

For stable deliverables, SBIM should behave like another native Archicad documentation source:

`Project Compiler facts`
-> `Navigator Add-On report viewpoint`
-> `Saved View`
-> `Drawing`
-> `Layout`
-> `Publisher`.

This keeps compliance/decision reports inside the same documentation pipeline as the architectural project and eliminates another parallel UI/document subsystem.