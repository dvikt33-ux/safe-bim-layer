# Checkpoint 38 — Cross-engine orchestration, semantic interoperability, parametric geometry
Date: 2026-10-08
Status: RESEARCH_ONLY; no PLN changes; user goal full-cycle automated architecture to final release.
Branch: feature/working-archicad-mvp

## Verified new integrations

### CYPE/BIMserver.center as a reference architecture for discipline decoupling
CYPE documents IFC-centric separation of architectural model, structural physical model, structural analytical model, reinforced concrete design and reinforcement fabrication/detailing. CYPECAD, CYPE 3D, CYPE Connect, StruBIM Rebar, StruBIM Steel exchange through BIMserver.center. Source https://info.cype.com/en/blog/how-to-integrate-reinforced-concrete-structures-into-the-open-bim-workflow/
CYPE Connect imports structural models and forces from JSON from any program, ETABS/SAP2000 XML, IFC structural models and exports drawings/reports and fabrication IFC/DSTV/STEP. Source https://info.cype.com/en/product/cype-connect-home/
Potential LIRA-FEM RES API -> normalized member forces -> CYPE Connect JSON. DO NOT CLAIM DIRECT COMPATIBILITY; JSON schema, units, load combinations, local axes, material sections, model/member IDs, engineer approval, licenses and country-specific codes must be benchmarked.
CYPE Architecture -> Open BIM Analytical Model -> Construction Systems -> CYPETHERM is thermal/acoustic/energy workflow, NOT a structural analytical replacement. https://learning.cype.com/en/faq/how-to-export-from-cype-architecture-to-open-bim-analytical-model-open-bim-construction-systems-and-programs-from-the-cypetherm-family/
BIMserver.center can import Archicad IFC through IFC Uploader; don't assume proprietary bidirectional native Archicad connector or local-only operation. https://blog.bimserver.center/en/6-ways-to-start-a-project-in-bimserver-center/

### buildingSMART bSDD
Production REST/GraphQL dictionary API, source https://technical.buildingsmart.org/services/bsdd/using-the-bsdd-api/ and https://services.buildingsmart.org/
Use classification/parameter semantic dictionary; NEVER confuse terminology mapping with code compliance, tested product performance or approved manufacturer construction assembly. Norm editions and jurisdiction stay in separate authoritative rulepack. Schema key {dictionary_uri, class_uri, property_uri, unit, datatype, property_version, provenance, mapping_confidence}; collision and unit conversions explicit.

### Official Graphisoft Grasshopper-Archicad 29 Live Connection
Graphisoft downloads AC29 Windows build 3000 (Oct 1, 2025), Rhino 7/8 supported. https://www.graphisoft.com/en-gb/downloads/add-ons/rhino-grasshopper/
Consider optional parametric executor for complex façade grids, geometry grammar, stairs/cores/flexible modules; NOT automatically the main executor: license, installation, ID stability, change propagation, materials, GUID preservation and geometry readback must be tested. No reason to duplicate native C++/Tapir wall/window writes for ordinary geometry.

## Refined project accelerator architecture
1. COLD Research Compiler: norm sources + product assemblies + project-specific library pack, system interface coverage, provenance, license, technical standards.
2. Semantic Bridge: bSDD/IFC classes + Russian code-specific fields + product technical metadata, typed units, stable identity.
3. Option Generator: space graph and layout CP-SAT, structural grids, program, engineering reserves, compliance constraints; all options BIM-derived.
4. Engine Router: native AC29 writer/Tapir, optional Rhino/Grasshopper, optional LIRA-FEM structural, optional CYPE engineering; each route has capabilities and tests, no blind fallback.
5. Interchange Contracts: IFC/SAF/JSON plus stable mapping GUID->analytical member ID->solver element ID; axes, units, load cases and provenance.
6. Feedback Compiler: engineering result -> reviewable design change proposals -> affected model elements -> dependent native documentation views/schedules.
7. Release Gate: cross-model consistency, Russian norm applicability, engineer approvals, final published outputs.

## Key novel reuse opportunity
An **Engineering Result Bridge** may let a single LIRA result feed:
- primary engineer-approved structural corrections in AC29,
- CYPE Connect steel connection design where compatible,
- cost/quantity and schedule implications,
- documentation update,
WITHOUT recreating FEM or detail compiler.

Do not assume automatic direct API method for unattended CYPE Connect execution or compatibility of LIRA force combinations. Separate source-result adapter from engineering decision maker.

## Specific test contracts
- BSSD_CLASSMAP_01: 20 real AC29 material/assembly properties mapped to bSDD with zero guessed units or fake norm approval.
- IFC_CYPE_ROUNDTRIP_01: small AC29 physical IFC through IFC Uploader, validate storeys/coordinates/openings/IDs; no live project mutations.
- LIRA_CYPE_FORCES_01: solved steel beam example, RES API forces -> explicit JSON CYPE schema -> compare moments/shear/local axes and case combinations to independent known result.
- GH_AC29_IDEMPOTENCY_01: run same parametric generation 3x, verify no duplicate walls, GUID/element references and materials, rollback in scratch PLN.
- ENGINE_ROUTER_01: same simple geometry via native writer and optional GH compare time, element semantics, change impact, failure recovery.
- SEMANTIC_VOCAB_01: bSDD mappings and local Russian SP rule pack separation.
- FULL_CYCLE_01: small project from blank brief through architecture, engineering response and final release with measured human time.

## Architecture decisions
P0: bSDD semantic bridge feasibility, normalized cross-engine exchange contracts and optional source metadata, reuse existing CYPE workflow ideas.
P1: Grasshopper-AC29 only when native writer inadequate for selected parametric geometry.
P1: LIRA-to-CYPE adapter only after installed licensed software and end-to-end benchmark.
No new monolithic BIM engine, no giant flat library imported into PLN, no forced cloud dependency for local MVP.
