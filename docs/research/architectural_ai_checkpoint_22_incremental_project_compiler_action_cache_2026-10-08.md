# Architectural AI checkpoint 22 — Incremental Project Compiler and content-addressed evidence\n\nDate: 2026-10-08\nStatus: ACTIVE RESEARCH CHECKPOINT\nTarget: Archicad 29 first\nBranch: feature/working-archicad-mvp\nBuilds on: checkpoints 20/21 from both research tracks\n\n## Executive conclusion\n\nSBIM should behave like an incremental build system for an architectural project.\n\nTarget runtime:\nevent -> changed semantic facets -> reverse dependency cone -> recompute minimum nodes -> change pruning -> cached/reused results -> update only dirty documentation -> retain evidence.\n\nThis combines Archicad live events, ACCORD entity-scoped checker requests, RDF4J transactional incremental SHACL, Bazel/Skyframe change pruning, Bazel action cache/CAS, IFCtoLBD checksum/profile caches and Archicad Drawing dependency/update APIs.\n\n## 1. Semantic facet fingerprints\n\nA changed GUID is only the starting signal. Do not invalidate a whole BIM object.\n\nTrack independent fingerprints per entity:\n- identity_fp\n- placement_fp\n- geometry_2d_fp\n- geometry_envelope_fp\n- geometry_topology_fp\n- material_fp\n- classification_fp\n- properties_fp, preferably split by property group or rule dependency\n- host_connectivity_fp\n- documentation_fp\n\nExample: a surface/finish change can invalidate schedules, cost, LCA and visual output without invalidating evacuation geometry or room adjacency.\n\nExample: a wall endpoint change invalidates plan geometry, connectivity, room boundaries and dependent documentation but does not automatically invalidate thermal material properties if construction remains unchanged.\n\nEvent path:\n1. receive changed GUID from Tapir/Husky/native observer;\n2. read only cheap semantic data;\n3. recompute facet fingerprints;\n4. compare old/new fingerprints;\n5. dirty only subscribers of changed facets;\n6. request deep topology only if a dirty calculation needs it.\n\n## 2. Reverse dependency graph and change pruning\n\nReuse the build-system method described by Bazel Skyframe:\n- record computation dependencies;\n- invalidate reverse dependencies of changed inputs;\n- rebuild only required nodes;\n- if a rebuilt node has the same semantic result as before, stop propagation and resurrect downstream nodes.\n\nExample:\nwall endpoint -> room polygon -> room area;\nif recomputed room area/category is unchanged, downstream fire/report branches remain valid.\n\nReference: https://bazel.build/versions/8.5.0/reference/skyframe\n\n## 3. Explicit project build nodes\n\nDerived project facts become named build nodes, for example:\n- ROOM_NET_AREA(zone_guid)\n- EGRESS_WIDTH(scope)\n- WALL_FIRE_RATING(wall_guid)\n- WINDOW_REVEAL_VALIDATION(window_guid)\n- SLAB_ASSEMBLY_THICKNESS(slab_guid)\n- DAYLIGHT_RESULT(zone_guid)\n- CLASH_SET(system_a, system_b, scope)\n- VIEW_CONTENT(view_guid)\n- DRAWING_STATUS(drawing_guid)\n- COST_RESULT(scope)\n- LCA_RESULT(scope)\n\nEach node declares its input facets, project constants, rule dependencies, provider/checker capability and exact provider version.\n\n## 4. Content-addressed Project Action Cache\n\nReuse the Bazel action-cache/CAS model conceptually.\n\nActionDigest is a hash of:\n- normalized capability/action ID;\n- normalized arguments;\n- affected input facet digests;\n- applicable Rule Pack digest;\n- provider/checker name and exact version;\n- Archicad/API version where relevant;\n- project constants used;\n- deterministic environment inputs.\n\nA cached result stores output digest, measurements, pass/fail/unknown, evidence, provider logs and dependencies.\n\nIf an identical trustworthy ActionDigest already exists, do not execute the expensive computation again.\n\nHigh-value cache cases include typical floors, repeated bathroom modules, window/reveal details, wall assemblies, recurring clearance checks, CYPE/Solibri scopes and identical IFC semantic conversions.\n\nCache classes:\n- CACHE_HARD: deterministic and acceptable as compliance evidence when exact versions/inputs match;\n- CACHE_SOFT: reusable for planning but revalidated at milestones;\n- CACHE_ADVISORY: stochastic/LLM output, context only and never hard compliance proof.\n\nReference: https://bazel.build/versions/7.1.0/remote/caching\n\n## 5. IFCtoLBD already validates the cache pattern\n\nExact source inspected: jyrkioraskari/IFCtoLBD, pom.xml version 2.54.1.\n\nIts current MCP server:\n- computes SHA-256 of the IFC file;\n- builds a cache key from IFC checksum + converter version + conversion profile;\n- reuses a loaded model on exact cache hit;\n- exposes content-addressed external geometry;\n- creates SHACL report IDs from model checksum + shape packs;\n- retains revision-comparison resources.\n\nThis strongly supports content-addressed deep-state/evidence caching.\n\nImportant separation: IFCtoLBD MCP validate_model currently uses Jena standalone SHACL over the loaded model. Keep this for COLD/milestone validation; do not assume it is the live incremental validator.\n\nRepository: https://github.com/jyrkioraskari/IFCtoLBD\n\n## 6. RDF4J for WARM incremental SHACL\n\nEclipse RDF4J ShaclSail analyzes the changed statements in each transaction, builds validation plans and validates only affected shapes/data where possible.\n\nIt supports parallel validation, caching of intermediate results, shapesGraph scoping and a bulk/full-validation mode for large transactions.\n\nRecommended split:\n- WARM/live semantic validation: RDF4J ShaclSail;\n- COLD/snapshot semantic validation: IFCtoLBD + Jena + full evidence/revision/geometry.\n\nReference: https://rdf4j.org/documentation/programming/shacl/\n\nAny alternative incremental engine must prove dependency extraction, target-node calculation, deletion/update correctness and equivalence to a clean full validation before production adoption.\n\n## 7. ACCORD Results API is the checker protocol baseline\n\nExact OpenAPI inspected: Accord-Project/API-Development/Results/Results.yaml.\n\nIt already provides:\n- checker identity and capabilities;\n- supported formats and terms;\n- whole-ruleset or named-check execution;\n- async job ID and status;\n- JSON and BCF results;\n- completion webhook;\n- entityIds scope restriction;\n- true/false/unknown result;\n- missValue;\n- supporting evidence.\n\nThe entityIds field directly supports Project Compiler scope reduction: send only impacted entities to a specialist checker.\n\nSBIM should extend/wrap rather than replace this protocol. Additional execution-envelope metadata should include projectRevision, activeRulePackDigest, ActionDigest, changedFacetTypes, provider/checker version, requested evidence level and stale-result guard.\n\nRepository: https://github.com/Accord-Project/API-Development\n\n## 8. Human rule form and compiled execution form\n\nACCORD Building Codes API already distinguishes purpose=execution, purpose=visualisation and purpose=combined, with exact document-section retrieval and immutable versions.\n\nRussian rule compilation should therefore retain both:\n- human form: exact source text, clause, edition, explanation and applicability rationale;\n- machine form: RASE/AEC3PO/BCRL, IDS, SHACL, SPARQL and process/capability references.\n\nThe LIGHT path must consume compiled verified rules and should not reread natural-language SP text on every edit.\n\n## 9. Checker states remain multi-valued\n\nExternal ACCORD-compatible result states are true, false and unknown.\n\nInternal project coverage also needs not_applicable, interpretation_required, stale, blocked and not_verified.\n\nNever collapse unknown, unsupported, stale or not-run into PASS.\n\n## 10. Reuse MCP risk annotations but verify actual behavior\n\nCurrent MCP ToolAnnotations provide readOnlyHint, destructiveHint, idempotentHint and openWorldHint.\n\nThey are explicitly hints, not trustworthy safety guarantees.\n\nSBIM should consume them but maintain a measured Capability Contract per provider/tool:\n- semantic capability ID;\n- actual read/write effect;\n- actual idempotency;\n- undo scope;\n- partial failure behavior;\n- read-back method;\n- project/window preconditions;\n- blast radius;\n- latency distribution;\n- host/version bugs;\n- provider/add-on version;\n- trust level.\n\nReference: https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/\n\n## 11. Husky First, with version-specific safety\n\nCurrent official Archicad page reports v1.5.54 and 733 tools.\n\nChangelog evidence is more important than the exact tool count:\n- v1.5.54 fixes real-session wall/door/navigator/error behavior;\n- v1.5.32 adds native Archicad JSON command access and removes three calls that reproducibly closed AC29; it also fixes tools that silently did nothing or were not advertised;\n- v1.5.22 fixes Story rename/height/delete incorrectly targeting Floor 0;\n- v1.5.18 fixes property writes not consistently wrapped in undoable commands;\n- v1.5.49 terrain/massing provides a specific dry-run and one-undo compound workflow;\n- v1.5.47/.48 add MEP write/connect, associative dimensions, interior elevations, IFC import and section auto-dimensioning.\n\nConclusion: Husky remains first broad AC29 execution provider, but dry-run/undo/atomic behavior is tool-specific until live benchmarks prove otherwise.\n\nSources: https://mcp.huskybim.com/products/archicad and https://mcp.huskybim.com/docs/changelog\n\n## 12. Documentation is another incremental dependency graph\n\nArchicad 29 Drawing Manager exposes:\n- ACAPI_Drawing_GetDrawingLink: source/link identity and view path;\n- ACAPI_Drawing_CheckDrawingStatus: quickly identifies up-to-date vs modified drawing;\n- ACAPI_Drawing_Update_Drawings: updates an explicit list of Drawing GUIDs.\n\nAPI_NavigatorItem exposes sourceGuid.\n\nTherefore model documentation can be scheduled as:\nmodel facet -> navigator view -> drawing -> layout -> publisher output.\n\nAfter a change:\n1. dirty only affected view/document recipes;\n2. ask Archicad which placed Drawings are actually stale;\n3. update only those Drawing GUIDs;\n4. republish only affected outputs where the publication workflow allows it.\n\nReferences:\nhttps://graphisoft.github.io/archicad-api-devkit/group___drawing.html\nhttps://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___drawing_link_info.html\nhttps://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___navigator_item.html\n\n## 13. Two operational planes\n\nEXECUTION PLANE:\n- Fast Modeling palette;\n- Husky First;\n- Tapir fallback/reference;\n- native Add-On gaps;\n- HOT/WARM graph;\n- facet fingerprints;\n- immediate Class-A/B guards and read-back.\n\nEVIDENCE/COMPILATION PLANE:\n- Russian official normative sources;\n- ACCORD/AEC3PO/BCRL/RASE;\n- IDS;\n- RDF4J incremental SHACL;\n- IFCtoLBD;\n- SML/OPM/BOT/bSDD;\n- DIO/PROV;\n- specialist checkers;\n- ICDD milestone package;\n- Action Cache/CAS.\n\nBridge them with federated persistent IDs, Project Revision, facet digests, Coverage Signatures and Action Digests.\n\n## 14. Scheduling lanes\n\nIMMEDIATE: UI-critical semantic edit, simple guards and local read-back.\n\nINTERACTIVE BACKGROUND: WARM facet recomputation, impact cone, incremental SHACL, room/area/connectivity, dirty drawing detection and local cache lookup.\n\nDEFERRED SPECIALIST: CYPE, Solibri, Tangl, IFCtoLBD full evidence/geometry, daylight, FEA, LCA and large documentation jobs only if affected.\n\nMILESTONE: full semantic snapshot, complete coverage gate, full-document audit, evidence package and exact version/hash persistence.\n\n## 15. High-value experiments\n\nINCR-COMPILER-01:\nUse two joined walls, one window, one zone, one slab, one associative dimension and one placed drawing. Perform a material/property-only wall edit, endpoint edit, window-width edit and non-geometric window-property edit. Record changed facets, dirty nodes, invoked checks, cache hits, pruned checks, stale Drawings and elapsed time.\n\nACTION-CACHE-01:\nRepeat one deterministic detail/check with identical facet/rule/provider versions: second run must use cached evidence. Change a relevant input: cache miss. Change an irrelevant input: cache hit.\n\nCHECKER-ADAPTER-01:\nWrap one checker in ACCORD-like semantics with capability discovery, entity-scoped request, async result, true/false/unknown, evidence and stale-envelope rejection.\n\nDOC-DELTA-01:\nModify one element, trace source View/Drawing links, query Drawing status, update only stale Drawings and compare elapsed time with broad update.\n\n## Strategic conclusion\n\nDeep research now points to a compact performance architecture:\n\nArchicad event -> semantic facet diff -> minimum dependency cone -> compiled/cached rules -> only required provider/checker -> change pruning -> incremental documentation -> Coverage Signature.\n\nMany tools can coexist without making the system slow because most providers remain asleep until a changed semantic facet actually requires them.

## 16. AC29-native edit events reduce HOT-layer work further

Archicad 29 introduces ACAPI::EditNotificationInterface.

After element editing, ElementsEdited receives:
- the set of changed GUIDs;
- API_ActTranPars describing the transformation.

API_ActTranPars exposes transformation semantics such as displacement, Z displacement, rotation sine/cosine, mirror axis, resize ratio, vertical-stretch state and rotation axis.

This gives the HOT layer a fast semantic hint about what changed before any deeper reread.

Recommended event fusion:
- EditNotificationInterface for direct manual geometric edits and transformation parameters;
- Tapir/native broader element notifications for create/delete/property/classification/reservation and other changes;
- element modiStamp/project modiStamp as cheap change stamps;
- facet reread only where the event cannot identify the exact changed semantic facet.

References:
https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_edit_notification_interface.html
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___act_tran_pars.html
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___elem___head.html

## 17. ACAPI_Element_Edit makes Fast Modeling cheaper

Archicad already has a generic native transformation API rather than requiring a separate writer for every common edit.

ACAPI_Element_Edit supports API_EditCmdID operations including:
- Drag / Drag a Copy;
- Rotate / Rotate a Copy;
- Mirror / Mirror a Copy;
- Elevate;
- horizontal Stretch;
- vertical Stretch;
- Resize;
- General internal-part edit;
- preserved-height and preserved-direction stretch for slanted beams/columns.

It accepts API_Neig inputs, enabling edits of supported internal parts as well as whole elements.

Therefore Fast Modeling should first attempt:
3D hit/context gesture -> semantic rule guard -> native ACAPI_Element_Edit.

Only when the native transformation cannot express the semantic operation should the system fall back to element-specific Change/ChangeExt/memo editing or a custom native gap.

This is likely cheaper, more BIM-native and safer than rebuilding geometry manually for common manipulations.

Reference:
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___edit_pars.html
https://graphisoft.github.io/archicad-api-devkit/group___element.html

## 18. Updated Fast Modeling implementation priority

FASTMODE-NATIVE-01 should benchmark the following before any custom Push/Pull geometry engine:
1. Drag whole native element;
2. Stretch wall/slab/roof-supported neigs;
3. Vertical Stretch;
4. Rotate;
5. Mirror;
6. Resize where meaningful;
7. direct manual edit event capture;
8. semantic read-back and Rule Guard;
9. only then element-specific geometry writers.

Success criterion:
the custom Add-On should mainly provide the better hit/context/manipulator experience, constraint visualization and semantic routing while Archicad itself performs as much of the physical edit as possible.

## 19. Element Difference Generator should be the recovery backstop

Archicad 29 already provides a first-party project/model/context difference mechanism.

`API_ElemDifferenceGeneratorTypeID` has three modes:
- `APIDiff_ModificationStampBased`: modification-stamp-based project difference; the AC29 header explicitly says this mode operates only with file state.
- `APIDiff_3DModelBased`: 3D-model-based difference.
- `APIDiff_ContextBased`: project-context difference that takes element connections into account.

`API_ElemDifferenceGeneratorStateType` supports:
- `APIDiffState_InFile`;
- `APIDiffState_InMemory`;
- `APIDiffState_CurrentProject`.

For ContextBased state, `viewGuid` exists specifically so the comparison reflects used-element changes rather than merely view-setting changes.

`API_ElemDifference` returns:
- `newElements`;
- `modifiedElements`;
- `deletedElements`;
- `isEnvironmentChanged`.

`isEnvironmentChanged` covers changes to view/view settings, project information/preferences, property definitions and geolocation.

Official AC29 Plan_Dump example demonstrates the intended lifecycle:
- persist ModificationStampBased baseline to disk;
- compare stored baseline to current project;
- persist 3DModelBased baseline and compare it to `APIDiffState_CurrentProject`;
- persist ContextBased baseline with viewGuid and compare to CurrentProject.

### Revised recovery architecture

Do not rely on one event stream as the only truth.

Use:
1. `EditNotificationInterface` for immediate user transformation semantics;
2. Tapir/native element notifications for broad live create/change/delete/property/classification events;
3. facet fingerprints for precise semantic invalidation;
4. persisted `APIDiff_ModificationStampBased` checkpoint as restart/missed-event recovery;
5. `APIDiff_3DModelBased` only when geometric recovery is required;
6. `APIDiff_ContextBased` for view/context-sensitive reconciliation and dependency-sensitive comparisons;
7. milestone full semantic/IFC comparison only when needed.

This means our custom event journal remains valuable for causal order, operation identity and project history, but it no longer needs to guarantee complete change detection by itself.

### Current upstream gap

Search of current public Tapir repository found no wrapper for DifferenceGenerator / ModificationStampBased / GenerateDifference during this pass.

Therefore expose only a **thin native recovery command** if live tests confirm no Husky/open wrapper already provides equivalent semantics.

Primary references:
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___elem_difference_generator_state.html
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___elem_difference.html
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/7a94688e30ecd1157bbb78b94e3ce8bdf1fb1e55/docs/group___difference_generator.html

## 20. EVENT-RECOVERY-01

Live AC29 test sequence:
1. store ModificationStampBased baseline to file;
2. create one wall;
3. modify one existing wall;
4. delete one object;
5. change one Property Definition or project/view preference to trigger environment delta;
6. compare stored state to CurrentProject;
7. verify exact new/modified/deleted sets and environment flag;
8. restart the sidecar/add-on callback consumer without updating baseline;
9. repeat one edit while live event consumer is unavailable;
10. restart consumer and verify Difference Generator discovers the missed change;
11. repeat with 3DModelBased;
12. repeat ContextBased in a fixed view and separately change only a view setting to validate intended filtering semantics.

Acceptance:
- missed live events are recoverable without a full Model Dump;
- false-positive scope and runtime are measured;
- persisted state is project-bound and stale-project misuse is rejected by our envelope;
- recovery result becomes input to normal facet reread/invalidation rather than directly marking all modified GUID facets dirty.