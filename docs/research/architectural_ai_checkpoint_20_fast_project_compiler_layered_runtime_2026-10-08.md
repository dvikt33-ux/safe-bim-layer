# Architectural AI checkpoint 20 — Fast Project Compiler layered runtime

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Builds on: checkpoints 17, 18 and 19

## Executive conclusion

The system is now optimized around one metric: minimum human time from design intent to a verified deliverable project.

The correct architecture is not one AI agent and not one BIM provider. It is a layered Fast Project Compiler with one user interface, semantic commands, provider arbitration, incremental verification and heavy analysis only on demand.

## 1. Coverage Signature — how to eliminate manual rechecking

Each verified object or Approved Construction Primitive should store a Coverage Signature containing project revision, Active Rule Pack version, source/norm edition IDs, checked rule IDs, evidence class, dependent GUIDs, relevant geometry/property hashes, checker/provider, verification time and invalidation triggers.

If a neighboring wall, host, rule edition or other dependency changes, only affected signatures are invalidated and automatically rechecked.

The user experience can therefore be: create/edit -> verified -> continue. The honest technical claim is compliance against the declared Active Rule Pack with explicit coverage evidence, never an unqualified claim that every possible rule was checked.

## 2. HOT / WARM / COLD project state

HOT is always resident: current selection, active story/view, nearby/host/dependent GUIDs, current semantic target, applicable Class-A/B rules, active ACP, provider shortlist and current operation identity.

WARM is incrementally maintained: GUID/type/story/bbox, key properties/classifications, host links, evaluated plan polygons where useful, graph adjacency, active design-intent constraints and verification signatures.

COLD is loaded only on demand: full evaluated 3D topology, face/material provenance, IFC federation, document-wide audit payloads, analysis datasets and donor-project models.

Performance rule: load depth on demand, never make the 104 MB Model Dump or full graph a prerequisite for ordinary editing.

## 3. Semantic Direct Modeling is feasible in AC29

Archicad 29 API_Get3DComponentType returns pointed element GUID, body index, polygon index, clicked model coordinate and polygon normal. ModelAccess exposes polygon material/normal data.

This makes the preferred interaction: clicked evaluated face -> owner BIM element -> semantic face classification -> native BIM parameter edit.

Examples: wall end face changes endpoint; top face changes height/top relation; opening face changes width/height/reveal; slab side face changes polygon edge; roof eave changes native roof geometry.

Do not implement generic Push/Pull as Morph conversion. Preserve native BIM semantics and use raw geometry only as fallback.

Primary API references:
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___get3_d_component_type.html
https://graphisoft.github.io/archicad-api-devkit/group___user_input.html
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___pgon_type.html

## 4. One UI, many hidden providers

The planner reasons in normalized semantic capabilities, not vendor tool names.

Example capability opening.resize can have HuskyBIM, Tapir, native-gap and specialized add-on implementations.

Provider registration records supported AC version, semantic fidelity, latency history, read-back quality, transaction/undo behavior, known limitations, required context, availability/license and provider version.

Selection priority: semantic fidelity -> safety/read-back -> latency -> availability -> cost/context overhead.

Husky remains first broad AC29 execution candidate. Tapir remains transparent reference/fallback. Native C++ owns only proven gaps and low-latency interactive tools.

## 5. LIGHT / MEDIUM / HEAVY runtime

LIGHT: gesture -> semantic command -> rule guard -> execute -> read-back. No neural model on the critical path.

MEDIUM: intent -> semantic retrieval -> 3-5 candidate capabilities -> bounded macro -> execute -> incremental verification. Use deterministic aliases first, semantic retrieval second, tiny function-calling model only when ambiguous.

HEAVY: problem -> impact graph -> design intent -> hard constraints -> analyses -> candidate search -> ranked repair -> execution -> coverage gate.

Heavy layer reuses BIGs/DIO/PROV, CAM/DSM, Design Healing, OpenMDAO, pymoo/Optuna/OR-Tools/Z3, IFC-Agent and specialist external checkers instead of inventing generic algorithms.

## 6. Local neural network is a dispatcher

Archicad 29 Graphisoft AI Assistant is cloud-based and subscription-dependent; its current AC29 public role is chiefly knowledge/help and BIM query/selection. Newer MCP preview workflows remain a future provider rather than the AC29 foundation.

Our local neural component should run as a separate sidecar process between the AC29 palette and provider registry. It classifies intent, retrieves relevant capabilities, extracts parameters, chooses short macros and decides escalation. It does not own norms, canonical state or unrestricted mutation.

FunctionGemma-class small function-calling models are an example of the model category to benchmark; deterministic and embedding routing remain preferred when sufficient.

## 7. Approved Construction Primitives should wrap Archicad-native mechanisms

Use Favorites, Transfer Sets, classifications/properties, Complex Profiles, GDL editable hotspots and PARAM-O rather than replacing them.

ACP adds only missing semantics: Rule IR IDs, allowed parameter envelope, verification recipe, dependency/invalidation definition, provenance, approved version and documentation/detail recipe.

PARAM-O in AC29 is a node-based parametric-object environment and saves results as regular Archicad objects.

Reference: https://help.graphisoft.com/AC/29/INT/_AC29_Help/065_PARAM-O/065_PARAM-O-1.htm

## 8. Grasshopper remains the heavy parametric geometry path

Graphisoft maintains Grasshopper-Archicad 29 Live Connection. Complex facade/roof/terrain generation and evolutionary exploration should reuse this route where advantageous rather than forcing a full parametric node engine into SBIM.

Reference: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/

## 9. Ci Tools / ProKit validates the productivity-extension direction

Graphisoft announced on 2026-10-07 that the tools formerly known as Ci Tools become Archicad ProKit in the Archicad 30/2026 portfolio. ProKit Suite includes Cabinets, Coverings, Doors/Windows, Electrical, Fitout, Keynotes, MetaData, Quantities, Site, Stairs and Structure.

For AC29, legacy Ci tooling remains available to licensed users. Therefore audit and reuse these workflows now; do not duplicate whole tool families unnecessarily. Re-audit overlap after the future AC30 migration.

Reference: https://support.graphisoft.com/hc/en-us/articles/51633416621073-Introducing-Archicad-ProKit

## 10. Qonic legal boundary

Qonic remains a public-market reference for hybrid direct/object BIM interaction, but its current EULA prohibits using or referencing the software to develop a competing product, reverse engineering and competitive benchmarking.

Therefore do not use the Qonic software for reverse engineering or competitive benchmarking. Use only general publicly documented industry concepts, and derive implementation from Archicad APIs, open research and permitted tools.

Reference: https://www.qonic.com/terms-of-use

## 11. Neighboring checkpoint 19 strengthens the HEAVY layer

Change propagation: reuse Cambridge Advanced Modeller/DSM Change Prediction concepts at coarse system level.

Design intent: adapt Design Intent Ontology plus W3C PROV, BCF, IFC/BOT/bSDD and a small set of architecture-specific predicates.

Multidisciplinary optimization: use OpenMDAO and existing optimizers rather than implementing optimization algorithms.

Detailing: BIM Library Transplant research reports that detailing can consume 50-60% of design time and demonstrated approximately 60-70% detailing-time reduction in its Revit prototype by transplanting high-LOD donor-model content, with reported matching accuracy of 65-80%.

Primary references:
https://nimonika.github.io/ontologies/dio/doc/
https://openmdao.org/newdocs/versions/latest/features/core_features/running_your_models/finding_feasible_solutions.html
https://ascelibrary.com/doi/10.1061/JCCEE5.CPENG-5680

## 12. Donor Project + ACP hierarchy

For repeated details use this order:
1. verified current-project ACP;
2. verified firm ACP;
3. matched donor-project detail;
4. manufacturer/TPD detail;
5. generated candidate only if no reusable solution exists.

Do not repeatedly ask AI to invent reveals, jambs, sills, slab edges, parapets, restroom modules, stairs, penetrations or facade modules when a verified previous solution can be adapted.

## 13. BHoM as an interoperability reference

BHoM provides an open software-agnostic AEC object model and generic Push/Pull adapter framework across many engineering domains. No Archicad toolkit was found in the BHoM GitHub organization during this pass.

Use BHoM as a reference for normalized engineering objects and adapter design. Consider a thin Archicad-to-BHoM adapter only if it measurably reduces integrations with downstream engines.

References:
https://github.com/BHoM/BHoM
https://github.com/BHoM/BHoM_Adapter

## 14. Performance rule

Research breadth may be large, but runtime complexity must stay hidden and lazy.

One visible interface. Semantic provider abstraction. HOT/WARM/COLD data depth. Incremental recomputation. Full audit only at milestones, after major changes, after Rule Pack update or on explicit request.

## 15. P0 research continuation

1. Husky full tool/schema/geometry/transaction audit.
2. Ci/ProKit AC29-now / AC30-later function inventory.
3. Semantic Direct Modeling API map for each major AC29 element type.
4. ACP schema plus first opening/reveal or wall/slab system.
5. Donor-detail reuse pipeline.
6. Local semantic tool-router benchmark over real provider manifests.
7. Coverage Signature and invalidation graph.
8. CYPE/Proektologiya/Tangl/Speckle/Solibri executor comparisons.
9. DIO/BIGs/PROV unified intent graph.
10. CAM/OpenMDAO/Design-Healing composition for HEAVY mode.

Governing criterion: does this remove human project-development time without sacrificing proof of correctness?