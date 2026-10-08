# Architectural AI checkpoint 26 — native Issues, Keynotes, Revision state, Structural Analytical Model and Renovation

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–25

## Executive conclusion

Five more project-management/engineering semantics are already native enough that SBIM should integrate with them rather than duplicate them:

1. regular Archicad Issues / BCF are the working review and defect loop;
2. Keynotes are a native document-facing projection of stable Rule/Decision references;
3. Revision Manager is mainly release-state/readback, not a programmable issue database;
4. Structural Analytical Model is an authoritative structural topology/load model, not something SBIM should reconstruct from geometry;
5. Renovation status/filter is an authoritative native lifecycle facet.

Recommended separation:

`Rule/analysis finding -> Archicad Issue / BCF`
`verified document-facing Rule/Decision reference -> Keynote / AutoText label`
`issued-document state -> Revision Manager readback`
`structural connectivity/support/load semantics -> Structural Analytical Model`
`Existing/New/Demolished visibility -> native Renovation`.

External SBIM retains legal provenance, causal history, coverage and cross-tool semantics.

## 1. Regular Archicad Issues are a complete working review loop

Current Tapir already wraps ACAPI_MarkUp issue management.

Observed command surface includes:
- CreateIssue;
- DeleteIssue;
- GetIssues;
- AddCommentToIssue;
- GetCommentsFromIssue;
- AttachElementsToIssue;
- DetachElementsFromIssue;
- GetElementsAttachedToIssue;
- ExportIssuesToBCF;
- ImportIssuesFromBCF.

Most of these have existed since Tapir 1.0.x, so this is mature relative to newer command groups.

### Element attachment semantics

Tapir exposes the four native markup component types:
- Creation;
- Highlight;
- Deletion;
- Modification.

The newer MIT connector davidharutyunyan/archicad-mcp-connector goes further at its tool layer and supports modification pairs `{original, modified}`.

### Comments

Native issue comments expose:
- GUID;
- author;
- text;
- status;
- creation time.

The MIT wrapper maps status values:
- Error;
- Warning;
- Info;
- Unknown.

### BCF

Tapir can export selected/all issues to BCF and import BCF back into Archicad, including survey-point/project-origin alignment and IFC relationship mapping.

Conclusion:
do not build a separate visual issue/backlog subsystem for model findings.

## 2. Rule failure materialization

Recommended default mapping:

`RuleResult = false`
-> create/update SBIM finding record externally
-> create or reuse Archicad Issue
-> attach affected elements as Highlight or Modification as appropriate
-> add compact comment with Rule ID + measured value + threshold + result digest
-> optional BCF export for external coordination.

Do not place full legal source text into Issue comments. Store immutable Rule/source provenance externally and put only stable IDs/short human context in the PLN/BCF projection.

Potential severity mapping:
- hard life-safety/code violation -> Error;
- probable/conditional violation -> Warning;
- advisory/manual review -> Info;
- checker could not determine -> Unknown.

This mapping must remain project-policy configurable.

## 3. Issues are not Revision Manager Issues

Do not conflate:
- regular Issue Manager markup (`ACAPI_MarkUp_*`), which is writable and BCF-capable;
- Revision Manager Issue / Change / Document Revision (`RVM`), which has a different API and release purpose.

Official AC29 Revision API function list includes many reads:
- GetRVMChanges;
- GetRVMIssues;
- GetRVMDocumentRevisions;
- GetRVMDocumentRevisionChanges;
- GetRVMLayoutCurrentRevisionChanges;
- GetRVMElemChangeIds;
- GetRVMChangesFromChangeIds;
- custom-scheme and first-issue reads.

The only observed write-style RVM function is:
- `ACAPI_Revision_ChangeRVMIssue`, modifying an existing Revision Issue.

No public `CreateRVMChange` or `CreateRVMIssue` function was found.

The MIT connector explicitly documents its Revision Manager surface as read-only.

Conclusion:
Revision Manager is not our programmable task/finding store.

Use it as authoritative release/document-revision state and integrate with an existing office RVM workflow where present.

## 4. RVM release gate role

SBIM should read:
- current document revisions;
- changes on a layout/document revision;
- existing revision issues;
- change IDs attached to elements;
- issued/actual state.

Use these as inputs to release/coverage logic:

`all required checks valid`
+ `all required drawings current`
+ `no blocking open SBIM Issues`
+ `RVM/document state consistent`
-> release candidate.

Do not try to synthesize RVM history if Archicad public API does not support creating it.

Test: `RVM-READBACK-01`.

## 5. Keynotes are a native document projection layer

Archicad Keynote API is available from Archicad 28 and therefore usable in AC29.

Current Tapir registers the complete Keynote group since 1.5.6:
- GetKeynoteTree;
- GetKeynoteAutoTexts;
- CreateKeynoteFolders;
- CreateKeynoteItems;
- ModifyKeynoteFolders;
- ModifyKeynoteItems;
- DeleteKeynoteFolders;
- DeleteKeynoteItems;
- CreateKeynoteLabels.

Keynote Items natively expose:
- Key;
- Title;
- Description;
- Reference.

Folders provide a hierarchical tree.

## 6. Keynote AutoText behavior

`KeynoteManager::GetAutoTextTokenFor` provides tokens for:
- Key;
- Title;
- Description;
- Reference.

Tapir `CreateKeynoteLabels` builds the label text out of these AutoText tokens rather than copying the literal values.

This is ideal for document-facing stable references because one Keynote edit can propagate to labels through Archicad's AutoText mechanism.

### Important limitation

Tapir's current `CreateKeynoteLabels` creates:
`API_LabelID`
`labelClass = APILblClass_Text`
`parent = APINULLGuid`.

Therefore the created label is a free text label, not an element-associated label.

Use Keynotes for document reference content, not as the model-element relationship store.

Element/finding association remains Issue/BCF, ElementLink or another explicit relation.

## 7. Rule/Decision Keynote projection

Good use:

External authoritative Rule Record:
- Rule ID;
- exact legal source/edition/clause;
- applicability;
- machine expression;
- evidence/provenance.

Projected Keynote:
- Key: stable compact Rule/Decision ID;
- Title: short human title;
- Description: concise project-facing instruction/result;
- Reference: source clause or DDR reference.

Example identity pattern:
`RU.SP54.13330:7.2.4`
or
`DDR-ARCH-0042`.

The exact naming convention should be deterministic and project-configurable.

Do not make the Keynote itself the legal source of truth.

Test: `KEYNOTE-RULE-01`.

## 8. Structural Analytical Model is an authoritative structural graph

Official Analytical API exposes a broad structural model, not just visualization.

Observed read capabilities include:
- current Structural Analytical Model;
- model by Model Variation;
- Curve Members;
- Surface Members and segmented surface members;
- member local coordinate systems;
- member-to-member connections including Analytical Links;
- Support geometry;
- Link geometry;
- Point/Edge/Surface Load geometry;
- Releases;
- model visibility and variation.

`ACAPI_Analytical_GetAnalyticalMemberConnections` explicitly returns elements connected to a Structural Analytical Member, including connections through Structural Analytical Links.

Therefore structural connectivity should be imported as authoritative native edges rather than inferred from physical 3D intersections.

## 9. Structural analytical write surface is also substantial

Official API includes:
- SetAnalyticalRelease;
- SetCustomCurveMember stretch/cutback;
- SetElementFromSupport;
- SetElementFromLink;
- SetElementFromPointLoad;
- SetElementFromEdgeLoad;
- SetElementFromSurfaceLoad;
- ConvertAnalyticalLinkToNonShortest;
- Create/Delete Analytical Load Case;
- Create/Delete Analytical Load Group;
- Create/Delete Analytical Load Combination;
- AddLoadCaseToLoadCombination;
- UpdateAnalyticalModel.

It also supports creating physical BIM elements from analytical members:
- CreateElementFromCurveMember;
- CreateElementFromSurfaceMember;
- CreateElementFromSegmentedSurfaceMember;

with optional Favorite use for the resulting BIM element.

## 10. Structural boundary

Important: this does NOT mean Archicad is the structural solver.

Use Archicad as:
- authoritative analytical topology store;
- load/support/release model;
- generation/update host;
- BIM <-> analytical member bridge;
- SAF/engineering interoperability source where appropriate.

Use specialist structural software for:
- FEM analysis;
- code design/checking;
- reinforcement/member sizing beyond Archicad native semantics;
- structural optimization requiring solver results.

SBIM custom role:
- map Russian structural rules and project assumptions;
- orchestrate export/check/import;
- compare revisions/results;
- link calculation evidence to BIM elements;
- rank proposed corrections.

Do not build a generic structural topology engine.

Test: `STRUCT-ANALYTICAL-01`.

## 11. Renovation is authoritative native lifecycle state

`API_Elem_Head` contains:
- `renovationStatus`;
- `renovationFilterGuid`.

Native statuses include at least:
- Existing;
- New;
- Demolished;
- Default/Undefined API states where applicable.

Archicad view settings also carry the Renovation Filter GUID, and drawing/primitive visibility can be evaluated with the native Renovation filter.

Official Renovation API provides:
- GetActualRenovationFilter;
- SetActualRenovationFilter;
- GetRenovationFilters;
- GetRenovationFilterName;
- GetRenovationStatusName.

Current MIT connector already serializes/modifies renovationStatus as a common element field and respects Renovation visibility in drawing-content extraction.

## 12. Lifecycle consequence

Do not create duplicate custom lifecycle flags for standard renovation semantics.

Use native Renovation for:
- Existing;
- New;
- Demolished;
- view/filter-dependent renovation presentation.

External SBIM lifecycle graph remains necessary for richer states such as:
- design stage;
- option/candidate status;
- approval;
- tender/construction package;
- procurement/fabrication;
- temporary works;
- issue resolution;
- commissioning;
- project-specific phases not expressible by Renovation.

`renovationStatus` becomes its own semantic facet fingerprint.

Test: `RENOVATION-01`.

## 13. Revised project communication model

### Finding / defect
`SBIM Rule Result -> Archicad Issue -> comments + attached elements -> BCF if external`.

### Stable drawing reference
`Rule/Decision projection -> Keynote -> AutoText label`.

### Release status
`Revision Manager readback + Drawing status + Coverage Signature`.

### Structural semantics
`Structural Analytical Model -> native graph and loads -> specialist solver/evidence`.

### Standard renovation phase
`Element renovationStatus + View renovationFilter`.

This avoids five parallel custom databases.

## 14. New tests

`ISSUE-RULE-01`:
- create issue from synthetic Rule FAIL;
- attach Highlight and Modification elements;
- add severity comment;
- get issue/elements/comments;
- export BCF;
- import BCF into scratch copy;
- verify element identity and coordinate alignment.

`KEYNOTE-RULE-01`:
- create `SBIM Rules` folder;
- create item with Key/Title/Description/Reference;
- create free AutoText Keynote label;
- change description/reference;
- verify displayed content updates;
- save/reopen;
- verify tree/item GUID stability.

`RVM-READBACK-01`:
- inspect existing Changes, Revision Issues, Document Revisions;
- resolve element -> change IDs -> document revision;
- compare before/after an office-created revision workflow;
- confirm no unsupported create assumption enters production.

`STRUCT-ANALYTICAL-01`:
- get current analytical model;
- enumerate curve/surface members;
- compare native analytical connections to physical BIM relations;
- create support/load/link in scratch scope;
- update model;
- read back load/support/release;
- test one load case/group/combination;
- export/import via selected engineering path;
- verify persistent BIM GUID mapping.

`RENOVATION-01`:
- Existing/New/Demolished elements;
- enumerate filters;
- switch active filter;
- verify native visibility and View renovationFilterGuid;
- change status and confirm incremental invalidation/drawing dirty behavior.

## Strategic conclusion

SBIM should not invent project-management semantics already resident in Archicad.

The practical stack is now:

`Issues/BCF = working problems`
`Keynotes = document-facing references`
`RVM = release state`
`Structural Analytical Model = structural topology/load state`
`Renovation = standard lifecycle state`
`SBIM = law + intent + causality + incremental verification + evidence`.

This further reduces both custom UI and duplicated project state.