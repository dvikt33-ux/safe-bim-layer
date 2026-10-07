# Architectural AI checkpoint 23 — native Archicad graph, solvers and open connector harvest

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first

## Executive conclusion

A large part of graph, solver and geometry work should come from Archicad itself or existing open source rather than being reconstructed geometrically.

New graph-source priority:
1. ARCHICAD_NATIVE_AUTHORITATIVE
2. SBIM_EXPLICIT_INTENT_OR_LEGAL
3. DERIVED_SEMANTIC
4. SPATIAL_INFERENCE_COLD_FALLBACK

## 1. Native relationships seed the WARM graph

ACAPI_Element_GetRelations and related APIs expose exact Wall/Beam connections, Zone relations and boundary fragments, Opening parent/cut relations, Solid Element Operations, Roof/Shell trims, hierarchical owners/subelements and Hotlink proxy/source mappings.

Zone relations already cover Walls, Columns, Objects, Lamps, Windows, Doors, Beams, Curtain Walls and parts, Skylights, Roofs, Shells, Morphs, Stairs and parts, Railings and parts, and Slabs.

Rule: use these authoritative edges before bbox/intersection-based inference.

## 2. MEP topology is already a first-party graph

ACAPI::MEP::DistributionSystemsGraph represents connected MEP elements grouped by common system category and domain. It exposes systems, elements, ports and tree traversal with previous/next relationships. Individual MEP elements expose direct connected element IDs.

Archicad 29 adds PhysicalSystem, a PLN-persisted database object with system identity such as name, root/calculation point, category/domain and group ownership. The current connected element set can be resolved through DistributionSystem.

Consequence: do not build generic MEP connectivity. Import it and add only design-intent, legal and cross-tool edges.

## 3. Native Stair solver is a compliance-by-construction executor

ACAPI_HierarchicalEditing_SolveStair returns Correct, Solved or NotSolved.

API_StairRulesData carries native limits for riser height, tread depth, 2R+G, landing length, walking-line/winder settings, riser/going relationships, pitch and related constraints. Headroom is represented separately in API_StairHeadroomData.

Recommended path:
Russian verified Rule IR -> compile supported numerical subset into native Stair rules -> SolveStair -> read-back -> independent full Russian verifier.

Solved never means full legal compliance. Width, headroom, evacuation applicability, railings/handrails, fire conditions and use-specific exceptions still require independent verification.

## 4. New MIT open-source candidate

Repository: davidharutyunyan/archicad-mcp-connector
Observed commit: b2a9a825d57ae9f4d0b50f66a7e413c1c0f2fff0 (2026-10-01).
License: MIT.

Current runtime is Archicad 26, not 29. README describes about 260 MCP tools in 21 families, around 170 extra Add-On JSON commands, 574 unit tests, a 413-check live regression, toolset presets and capture_view verification.

Decision: not an AC29 binary dependency; high-value source/schema/test harvest candidate.

## 5. Deep geometry overlaps Model Dump algorithmically

ElementQueryGeometry.cpp implements GetElement3DGeometry with summary and mesh modes.

Observed output includes body/vertex/edge/polygon counts, world bbox, material summary, source GUID, body index, world XYZ vertices, polygon topology/holes, body material, per-polygon material override, world normal and closed/curved flags. It handles hierarchical subelements, deduplicates bodies and uses output budgets.

It also implements GetElement2DGeometry from Archicad drawing primitives.

AC29 keeps the same underlying element/body/vertex/polygon model but API names moved toward ModelAccess and DrawingPrimitive namespaces. Therefore the algorithm is portable conceptually, not binary/source compatible without adaptation.

Our existing AC29 Model Dump remains the measured baseline. Likely evolution: keep full dump as milestone/debug snapshot and add on-demand per-element summary/mesh geometry.

## 6. GEOM-HARVEST-01

Compare current Model Dump against an AC29-adapted version of the MIT geometry contract on the same fixtures.

Verify body count, source GUID, world vertices, polygon topology/holes, face/material overrides, normals, hierarchical parts, Building Material/Composite/Profile provenance, homeStory/host semantics, memory, runtime, batch scalability and truncation.

Do not retire Model Dump until this passes. The open repo live suite proves summary use; mesh code exists but is not treated as AC29 live-proven.

## 7. Open relation extractor

ElementQueryRelations.cpp already wraps Wall/Beam connections, Zone boundary relations, Opening/owner links, SEO, Roof/Shell trims and hierarchical subelements.

This is a useful implementation and test reference for a thin AC29 native graph extractor.

## 8. Stair/Railing harvest

The open connector serializes substantial Stair state: height, top link, width, riser/tread counts and dimensions, pitch, baseline/walking line, boundaries, structures, rules and subelement GUIDs.

It serializes Railing path, length, height, offsets, segments, nodes, posts, rails, handrails, panels, baluster sets/balusters and patterns.

It creates Stairs/Railings and modifies selected high-level fields, but its AC26 implementation does not modify an existing Stair baseline or Railing path.

For AC29, evaluate native SolveStair before porting creation logic.

## 9. Safety and transaction audit

The wrapper uses strict Zod schemas and rejects unknown fields unless explicitly passthrough. Large results are bounded/truncated with a narrowing hint.

Direct delta transforms such as move, rotate, mirror, elevate and resize are correctly marked non-idempotent/destructive in MCP annotations.

The C++ Undoable wrapper uses ACAPI_CallUndoableCommand and rolls back the scope if an exception escapes.

However CreateElements and ModifyElements call per-item Try inside the outer undo scope. A bad item becomes an error result while successful sibling items commit.

Therefore: one undo step is not an all-or-none transaction.

## 10. Toolset presets

The connector already supports coarse toolsets such as minimal, modeling, documentation and data plus family include/exclude.

Recommended context hierarchy:
1. coarse family preset
2. semantic retrieval inside the family
3. expose only 3-5 exact capabilities to the reasoning model.

## 11. ElementLink as a PLN-local anchor

Archicad Element Links are Add-On-specific element associations. Graphisoft documents that Archicad tracks GUID changes and updates links accordingly.

Use only for a small set of important two-element anchors that benefit from living in the PLN, for example ACP instance to governing host or decision/verification anchor to BIM element.

Do not store the whole Canonical Project Graph there. Rich relation type, Rule IDs, evidence, rationale, time and many-to-many context remain in the external semantic graph.

## 12. Revised graph-source hierarchy

ARCHICAD_NATIVE_AUTHORITATIVE: host/owner, Wall/Beam connections, Zone boundaries, Opening cut/parent, SEO, trims, hierarchy, Hotlinks, MEP topology, story/view/drawing relations.

SBIM_EXPLICIT_INTENT_OR_LEGAL: facade rhythm, wet-core stack, grid alignment, normative applicability, decisions, ACP governance, approved substitutions and coordination ownership.

DERIVED_SEMANTIC: same module/type/favorite, repeated room pattern, likely detail family, document dependency and validity-envelope relations.

SPATIAL_INFERENCE_COLD_FALLBACK: evaluated 3D collision, nearest-neighbor inference, geometric adjacency and topology reconstruction only when no stronger source exists.

## 13. Revised custom core

Keep custom: Russian legal applicability/currentness, design intent and DDR, Rule compilation/provenance, Coverage Signatures, semantic facet fingerprints, incremental compiler/change pruning, provider Capability Contract, Action Cache, cross-provider scheduling, disruption/ranking policy and only proven AC29 gaps.

Reduce presumed ownership of generic BIM relation discovery, generic MEP topology, Stair geometry solving, generic per-element 3D extraction algorithm, generic transforms, event-recovery truth and generic tool-family discovery.

## 14. New tests

NATIVE-GRAPH-01: compare native relation extraction against geometry-inferred relations for precision/completeness/runtime.

MEP-GRAPH-01: verify systems, ports, previous/next traversal, direct connected IDs and PhysicalSystem persistence/root/category.

STAIR-SOLVER-01: intentionally invalid Stair -> compile rule subset -> Correct/Solved/NotSolved -> read-back -> independent Rule IR check.

GEOM-HARVEST-01: Model Dump vs AC29-adapted open geometry contract.

OPEN-CONNECTOR-29-PORT-01: port only selected MIT components: relations, geometry summary/mesh, Stair/Railing schema and test fixtures.

ELEMENTLINK-01: save/reopen, GUID tracking, delete, undo/redo, copy/hotlink and Teamwork behavior before production use.

## Strategic conclusion

Archicad itself should be treated as the first semantic engine:
native relationships + solvers + edit system -> SBIM intent/legal semantics and incremental compiler -> Husky/Tapir/native execution -> heavy semantic/engineering systems only when needed.

This is thinner, faster and safer than reconstructing a second BIM model beside Archicad.