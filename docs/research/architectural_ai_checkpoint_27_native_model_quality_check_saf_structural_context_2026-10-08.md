# Architectural AI checkpoint 27 — AC29 native Model Quality Check UI and SAF structural exchange

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–26

## Executive conclusion

Archicad 29 adds a first-party extensibility surface for Model Quality Check.

This can remove part of our custom QA UI, but only in the disciplines for which Graphisoft publishes a parent Model Check Type ID:
- MEP;
- Structural Analytical Model.

No public general/architectural Model Check Type ID was found in the AC29 DevKit during this pass.

Therefore the correct split is:

`Project Compiler / Rule IR = authoritative computation and evidence`
`native Model Quality Check = thin in-Archicad projection/navigation surface for MEP + Structural checks`
`Issues/BCF = persistent working findings`
`custom compact architectural QA surface = only where no native parent type exists`.

SAF export is also already programmable through the public ProjectOperation Save API, using a named existing SAF Translator.

## 1. AC29 Model Quality Check extensibility

`ACAPI::ModelCheckManager` is available since Archicad 29 and gives access to Model Quality Check services.

`RegisterGroup(modelCheckTypeId, groupId, localizedName)` registers an Add-On group under an existing Model Check Type.

`ACAPI::ModelCheckMethodCallback` is explicitly intended for Add-Ons to extend the list of Model Check methods with their own logic.

Constructor:
`ModelCheckMethodCallback(parentModelCheckTypeId, uniqueNonLocalizedMethodName)`.

The callback lifecycle is registered through the Add-On service interface.

## 2. Native check-method UI contract

A custom method supplies:
- localized method name;
- localized result name;
- optional localized info/hover text;
- optional icon;
- optional group ID;
- default enabled/selected state;
- check setting type;
- default setting values;
- `CheckProcess(...)` implementation.

Supported setting UI types are:
- OnlySelection;
- Angle;
- Length;
- Area;
- Real;
- Interval.

`CheckProcess(ProcessControl, values)` returns the elements filtered out by the check.

This is a strong fit for parameterized geometry/connectivity checks such as:
- minimum clearance;
- maximum gap;
- angle limits;
- area thresholds;
- pairwise connection/collision checks;
- selection-only diagnostic passes.

## 3. ModelCheckResult is intentionally small

`ModelCheckResult` can be constructed from:
- one element GUID;
- two element GUIDs.

It exposes only the first/second element identities.

No per-result arbitrary text, severity, Rule ID or evidence payload is present in the public result object.

Therefore:
- do not make native Model Quality Check the Rule IR source of truth;
- do not store legal evidence there;
- do not collapse SBIM result status into the native result.

The Project Compiler retains:
- exact Rule ID;
- measured values;
- thresholds;
- pass/fail/unknown/not-verified state;
- source/provenance;
- Action Digest;
- evidence;
- project revision.

The native check callback simply projects the current failing GUID(s) for fast user navigation.

## 4. Published parent Model Check Types

Public AC29 DevKit search found two explicit Model Check Type ID providers:

### MEP
`ACAPI::MEP::GetMEPModelCheckTypeId()`.

### Structural Analytical
`ACAPI_Analytical_GetModelCheckTypeId(API_Guid&)`.

No public architectural/general type-ID function was found.

Do not register architectural checks under MEP or Structural merely to obtain native UI placement.

If later AC30 or another supported API publishes a general type, reevaluate.

## 5. Best first native projections

### MEP
- unconnected network components;
- illegal/undesired route gap;
- clearance threshold;
- slope/angle threshold;
- system/category inconsistency;
- pairwise interference where the check naturally returns one/two elements.

### Structural Analytical
- disconnected analytical members;
- gap/overlap between analytical members;
- suspicious link/support/release state;
- local connectivity checks;
- checks parameterized by Length/Angle/Interval.

The callback may compute directly or, preferably, query current cached Project Compiler results.

Heavy external checks must not block interactive UI unnecessarily.

## 6. MODEL-CHECK-01

Build the smallest AC29 Add-On experiment:
1. obtain MEP Model Check Type ID;
2. register `SBIM / MEP` group;
3. register one single-element check;
4. register one pair-element check;
5. use Length or Interval setting;
6. return fixture GUIDs from CheckProcess;
7. verify native dialog grouping, localized name/info, result palette and element selection/navigation;
8. verify OnlySelection semantics;
9. test cancellation through ProcessControl;
10. repeat under Structural Analytical Model Check Type.

Acceptance:
- native UI is reliable and low-overhead;
- Project Compiler results can be surfaced without duplicated check logic;
- no unsupported general/architectural parent assumption.

## 7. Q4–Q6 implication

Existing architectural rules such as:
- WALL_FRAGMENTATION;
- WALL_CONNECTIVITY;
- WALL_OPENING_CONFLICT;
- OPENING_EDGE_CLEARANCE;
- ROOF_COLLISIONS;
- ROOF_GAPS

should NOT automatically be moved to native Model Quality Check merely because the API exists.

Only rules that legitimately belong under published MEP or Structural parent types should use that native UI.

Architectural Q4–Q6 remain in SBIM QA/Issues unless a valid general Model Check parent becomes available.

## 8. SAF export is already public and scriptable

Official Project Operation API overload:
`ACAPI_ProjectOperation_Save(fileSavePars, API_SavePars_Saf*)`
exports SAF.

`API_SavePars_Saf` contains:
- `elementsToSAFExport`: all project / visible / selected scope;
- `selectedSAFTranslatorName`: name of an existing SAF Translator.

The translator affects:
- profiles/material mapping;
- output version;
- other SAF translation semantics.

Conclusion:
do not build a SAF serializer.

## 9. SAF Translator boundary

The public API exposes Teamwork permission:
`APISAFTranslatorsManage`
and save permission:
`APISaveAsSAF`.

However this pass found no public AC29 API to enumerate/edit the internal SAF Translator configuration programmatically.

The save call expects the name of a translator already configured in Archicad.

Recommended production contract:
- define office/project SAF translator(s) in template/setup;
- treat translator identity/configuration as controlled project input;
- SBIM selects by exact name and exports deterministically;
- record translator name plus an externally maintained configuration/version fingerprint in the Action Digest/evidence envelope.

Do not infer that the presence of a Teamwork permission means translator CRUD is exposed by C++ API.

## 10. SAF-EXPORT-01

On AC29 scratch project:
1. configure a known translator manually/template-side;
2. export whole project;
3. export only visible analytical members;
4. export selected elements;
5. verify deterministic file generation;
6. compare material/profile mapping;
7. import/open in selected structural solver;
8. round-trip one changed structural property/result where supported;
9. record exact translator name and project state.

Failure on missing translator name must be explicit and must never silently choose another translator.

## 11. Structural analytical state has non-element dependencies

Official Analytical API documentation states that the Structural Analytical Model is generated from:
- cores of load-bearing physical elements;
- 3D core connectivity;
- Analytical Model generation rules;
- Renovation Filter;
- layer connection class IDs.

The model is view-dependent through its `API_AnalyticalModelVariation`.

`ACAPI_Analytical_GetAnalyticalModelVariation(modelGuid, variation)` returns the variation used to create the model.

Generation is lazy; `ACAPI_Analytical_UpdateAnalyticalModel` is required when latest state must be guaranteed.

Therefore structural topology can change without a simple element-geometry delta.

## 12. Structural Action Digest / invalidation

Any cached structural-analysis or structural-connectivity result must include at least:
- affected element structural facets;
- Analytical Model Variation GUID;
- Renovation Filter context;
- relevant layer/connection-class state;
- load/support/release state;
- structural generation-rule configuration identity;
- provider/solver version;
- SAF Translator identity when SAF is involved.

If exact generation-rule internals are not readable, the variation/project modification state must act as a conservative invalidation boundary.

Never reuse a structural result solely because physical element GUIDs/geometry are unchanged.

## 13. Generation-rule API boundary

The public Analytical API exposes:
`ACAPI_Analytical_SetGenerationSettingsToNoRule()`
for setting the current analytical model generation settings to no rules.

Teamwork exposes permission to manage Structural Analytical Model Generation Rules.

This pass did not find a complete public structured CRUD API for arbitrary generation-rule definitions.

Therefore:
- generation rules are project/template-controlled configuration;
- SBIM may read resulting model/variation and force update;
- do not plan a custom generation-rule editor until a proven requirement/gap exists.

## 14. Structural exchange architecture

Recommended structural loop:

`native physical BIM`
-> `native Structural Analytical Model`
-> `native connectivity/support/load/release state`
-> `SAF export using controlled translator`
-> `specialist structural solver`
-> `result/evidence adapter`
-> `SBIM Rule/decision layer`
-> `Issue/BCF or proposed BIM correction`.

Archicad remains topology/model host; specialist software remains analysis/design solver.

## 15. Roadmap changes

STOP / DO NOT BUILD:
- generic MEP Model Check palette;
- generic Structural Model Check palette;
- SAF serializer;
- structural topology reconstruction from physical mesh;
- arbitrary SAF Translator editor without a proven public seam.

KEEP:
- Rule IR and rich result store;
- native Model Check adapter for MEP/Structural;
- architectural QA UI only where native type unavailable;
- SAF export wrapper with strict translator contract;
- external solver adapters and evidence mapping;
- structural context fingerprint/invalidation.

## Strategic conclusion

AC29 can now host part of our checks inside the same native UI engineers already use, without surrendering rule provenance or building a parallel checker interface.

The correct architecture is:

`Project Compiler computes`
-> `Model Quality Check projects element GUID results for MEP/Structural`
-> `Issue/BCF persists actionable findings`
-> `SAF transports controlled analytical state to specialist solvers`.

This removes more UI and exchange code while preserving the legal/evidence layer outside Archicad.