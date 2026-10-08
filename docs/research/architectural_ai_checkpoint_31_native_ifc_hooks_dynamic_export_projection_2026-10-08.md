# Architectural AI checkpoint 31 — native IFC export hooks remove metadata post-processing

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–30

## Executive conclusion

Archicad 29 already provides a first-party runtime extension layer for IFC export metadata:
`IFCAPI::HookManager`.

IFC hooks can dynamically add export-only data without creating persistent IFC data in the PLN.

Combined with current Tapir:
- list valid IFC export translators;
- select translator by exact name;
- export IFC;
- inject generated properties/attributes/classifications/assignments at export time.

Therefore a custom IFC post-processor is not justified for ordinary SBIM metadata projection.

Correct split:
- stable BIM/project data -> Archicad Properties/Classifications + normal IFC mappings;
- export-only SBIM verification/provenance/decision/system projection -> IFC hooks;
- geometry/export filtering/schema/version -> Archicad IFC Translator;
- conformance validation -> IDS/independent IFC validation;
- IFC geometry rewriting -> only if a separate proven requirement appears.

## 1. Graphisoft explicitly recommends this runtime extension path

Official IFC API overview states that:
- persistent IFC data can be queried;
- creating/changing persistent IFC data is generally not the intended modern API path;
- normal Archicad data + IFC mappings should be preferred when sufficient;
- if mappings are insufficient, IFC hooks can add custom data dynamically;
- hook callbacks are called when relevant IFC data is queried;
- this avoids setting persistent IFC data in Archicad.

This matches SBIM's need to export verification/evidence identifiers without polluting the authoring model.

## 2. HookManager export hooks

Available since Archicad 28 and therefore available in AC29:
- RegisterPropertyHook;
- RegisterAttributeHook;
- RegisterClassificationReferenceHook;
- RegisterAssignmentsHook;
- RegisterTypeObjectPropertyHook;
- RegisterTypeObjectAttributeHook;
- RegisterTypeObjectClassificationReferenceHook;
- corresponding unregister operations.

Each registration must remain valid while the Add-On is loaded until explicitly unregistered.

Attempting to register an already-registered hook returns APIERR_BADPARS.

Architecture consequence:
centralize each hook type behind one SBIM dispatcher; do not let independent internal modules race to register separate callbacks.

## 3. Property hook

Callback signature:
`(const IFCAPI::ObjectID&, std::vector<IFCAPI::Property>&)`.

Official description:
add generated IFC properties to IFC objects.

`IFCAPI::PropertyBuilder` can construct:
- IFC Value;
- PropertySingleValue;
- PropertyTableValue;
- PropertyListValue;
- PropertyBoundedValue;
- PropertyEnumeratedValue.

Thus SBIM export does not need string-only flattening.

Use explicit IFC value types and canonical units where possible.

## 4. Attribute hook

Callback signature:
`(const IFCAPI::ObjectID&, std::vector<IFCAPI::Attribute>&)`.

`PropertyBuilder::CreateAttribute(name, optionalValue)` creates schema-named IFC attributes.

Attributes are semantically stronger/more fragile than custom Psets.

Policy:
- avoid overriding/competing with normal translator-generated core attributes unless a project exchange contract explicitly requires it;
- prefer custom property sets for SBIM metadata.

## 5. Classification hook

`RegisterClassificationReferenceHook` can add generated IFC classification references.

`PropertyBuilder` can construct:
- Classification;
- ClassificationReference;
- referenced source metadata;
- identification/name/description/location;
- explicit RelAssociatesClassification name.

Use this only for genuine classification semantics.

Do NOT encode arbitrary Rule failures as fake IFC classifications merely because the API permits it.

## 6. Type Object hooks

Separate hooks are available for IFC Type Object:
- properties;
- attributes;
- classification references.

Graphisoft notes that type objects are generated from element data and similar type objects are merged at the end.

Potential SBIM use:
- governed Recipe/Favorite identifier;
- approved type/version;
- type-level specification/provenance;
- type-level classification.

Important:
test merge behavior when hook-provided type data differs between otherwise-similar elements before using type hooks in production.

Test: IFC-TYPE-HOOK-01.

## 7. Assignment hook is especially powerful

`RegisterAssignmentsHook` receives `IFCAPI::HookAssignments`.

HookAssignments can dynamically create IFC group structures of types:
- IfcGroup;
- IfcSystem;
- IfcBuildingSystem;
- IfcDistributionSystem;
- IfcZone.

`CreateIfcGroup` requires a deterministic unique API_Guid; Graphisoft explicitly says it should be fixed/content-based, not random, so identification remains stable during hook processing.

It also automatically creates necessary IFC relations.

Available operations include:
- AssignObjects(groupID, objectIDs);
- ServiceBuildings(systemID, spatialObjectIDs);
- access generated IfcRelAssignsToGroup;
- access generated IfcRelServicesBuildings.

This can project system/group semantics without persisting duplicate group data inside the PLN.

## 8. Object identity mapping is native

`IFCAPI::ObjectAccessor` supports:
- CreateElementObjectID from API_Elem_Head;
- GetAPIElementID(ObjectID) -> Archicad API_Guid;
- GetGlobalId(ObjectID);
- GetExternalGlobalId(ObjectID);
- FindElementsByGlobalId;
- GetStoryIndex;
- GetIFCType;
- GetTypeObjectIFCType;
- persistent assignment tree access.

Therefore hook lookup can use canonical Archicad GUID identity.

No separate IFC-ID-to-Archicad-GUID database is required for ordinary export hooks.

## 9. Safe SBIM IFC Pset

Recommended export-only custom property set:
`Pset_SBIMVerification`.

Candidate fields:
- RuleSetId;
- VerificationStatus;
- VerifiedProjectRevision;
- VerificationTimestampUTC;
- EvidenceDigest;
- DecisionRecordId;
- RecipeId where relevant;
- ProviderProfileId / compiler version if required.

Keep values compact and machine-readable.

Do not export full normative documents, reasoning traces, or large evidence payloads into IFC.

External evidence stays in SBIM storage and is addressed by stable IDs/digests.

## 10. What should remain normal Archicad data

Prefer persistent Archicad Properties/Classifications + standard IFC mappings for data that:
- is genuine BIM authoring information;
- users should inspect/edit in Archicad;
- belongs in schedules;
- should survive even if SBIM Add-On is absent;
- is part of the office/template information model.

Examples:
- fire rating;
- load-bearing flag;
- occupancy/use;
- type code;
- material/specification fields.

Do not replace normal BIM data with ephemeral hooks.

## 11. What should use hooks

Good hook candidates:
- verification status at export revision;
- RuleSet/version identifier;
- evidence hash/reference;
- decision-record ID;
- external analysis run ID;
- project-compiler release signature;
- dynamic IfcGroup/System assignment that only exists for exchange;
- export-specific classification/provenance required by a receiving workflow.

## 12. Hooks are not an IFC geometry post-processor

These hooks manipulate IFC data projection, not arbitrary exported geometry.

They do NOT replace:
- translator geometry options;
- tessellation/representation logic;
- export element filtering;
- IFC schema/version choice;
- coordinate/georeferencing setup;
- external IDS validation;
- specialist post-processing if a future contract truly requires rewriting geometry.

## 13. Translator discovery is already wrapped by Tapir

Official API:
`ACAPI_IFC_GetIFCExportTranslatorsList`
returns valid IFC Export Translators.

`API_IFCTranslatorIdentifier` includes:
- translator name;
- internal reference.

Current Tapir 1.6.0+ already exposes:
`GetIFCExportTranslators`.

Tapir `IFCFileOperation` can save IFC using a requested `translatorName`.

Tapir documentation explicitly instructs using a name returned by `GetIFCExportTranslators`.

Decision:
no custom translator enumeration/selection wrapper.

## 14. Open MIT connector also already covers IFC translator/export path

`davidharutyunyan/archicad-mcp-connector` exposes:
- get_ifc_translators;
- export_ifc;
- export scope including explicit elements in live tests.

This is another implementation/reference path.

## 15. Export hook performance rule

Hook callbacks execute inside the IFC data/export process.

Production rule:
NEVER perform network calls, long LLM calls, or heavy Project Compiler recomputation inside a hook callback.

Before starting export:
1. resolve exact project revision;
2. run required verification/release gate;
3. build immutable in-memory `IfcProjectionSnapshot` keyed by Archicad GUID/IFC projection identity;
4. register/enable hooks;
5. export with exact validated translator;
6. hooks only perform deterministic in-memory lookup + PropertyBuilder construction;
7. unregister/clear snapshot after export where lifecycle requires.

This prevents nondeterministic/slow exports.

## 16. Export ActionDigest

IFC export evidence should include at least:
- project identity;
- verified project revision;
- RuleSet/legal-source versions;
- Project Compiler version;
- IfcProjectionSnapshot digest;
- IFC translator name/internal identity where accessible;
- export scope;
- Design Option / Renovation / View context if relevant;
- hook schema/version;
- output file digest;
- independent validation result.

## 17. IFC-HOOK-01

AC29 scratch test:
1. register PropertyHook;
2. map ObjectID -> Archicad GUID;
3. add `Pset_SBIMVerification.VerificationStatus` to two elements;
4. export through Tapir IFCFileOperation with exact translator;
5. inspect IFC independently;
6. verify no persistent Archicad IFC data/property was created;
7. unregister hook;
8. export again and confirm generated Pset disappears.

## 18. IFC-HOOK-CONFLICT-01

Test collisions/conflicts:
- hook property with same Pset/property name as translator-mapped property;
- attribute name already populated by normal export;
- duplicate classification association name;
- two generated properties with same key;
- registration when same hook already registered.

Do not define production merge/override semantics until measured.

## 19. IFC-ASSIGNMENT-01

Create deterministic export-only groups:
- one IfcGroup;
- one IfcSystem or IfcDistributionSystem;
- assign selected native elements;
- optionally connect system to serviced spatial object;
- add hook properties to generated group/relation if supported by ObjectID recognition.

Validate IFC graph in an independent viewer/parser.

## 20. IFC-TYPE-HOOK-01

Take two otherwise-similar types/elements.
Add same type-hook metadata, then differing metadata.

Verify:
- generated Type Object count;
- merge behavior;
- GlobalIds;
- property placement;
- repeat-export determinism.

Do not use type-level hooks for Recipe IDs until this is understood.

## 21. IFC-EXPORT-01

End-to-end deterministic release:
1. enumerate translators through Tapir;
2. assert required exact translator exists;
3. build projection snapshot;
4. run release gate;
5. export IFC with translator name;
6. verify generated hooks;
7. run IDS/IFC validation;
8. hash output;
9. store export evidence envelope.

Failure to find exact translator is BLOCKED, never fallback silently to first/default translator.

## 22. Roadmap changes

STOP / DO NOT BUILD:
- generic IFC metadata post-processor;
- duplicate IFC-to-Archicad identity map for export;
- persistent PLN fields solely to carry export-only SBIM evidence;
- custom IFC translator enumerator;
- custom IFC export command;
- fake classifications for generic Rule findings.

KEEP / SMALL GAP:
- central AC29 IFC Hook dispatcher;
- deterministic export projection snapshot;
- translator/release contract;
- independent IFC/IDS validation;
- specialist post-processing only if future exchange contract requires geometry/schema changes unavailable through native exporter.

## Strategic conclusion

The AC29 IFC release path can now remain entirely inside Archicad for generation:

`verified SBIM facts`
-> `immutable IfcProjectionSnapshot`
-> `native IFC Hooks`
+ `native exact IFC Translator`
-> `native IFC export`
-> `independent IDS/IFC validation`.

This removes the need to reopen and rewrite ordinary IFC files after export.