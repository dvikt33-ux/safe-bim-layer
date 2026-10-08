# Checkpoint 29 addendum — native AC29 MEP connectivity graph
Date: 2026-10-08
Status: DOCUMENTED / NOT AC29_TESTED
Target: AC29 only
Branch: feature/working-archicad-mvp
Precedent: architectural_ai_checkpoint_29_ac29_native_events_zone_adjacency_and_freshness_2026-10-08.md

## Finding

Archicad 29 already exposes ACAPI::MEP::DistributionSystemsGraph, introduced in AC28.
This is a true built-in graph of connected MEP entities, partitioned into distribution systems sharing the same MEP domain and system category.

Direct API:
- ACAPI::MEP::CreateDistributionSystemsGraph()
- DistributionSystemsGraph::GetSystems()
- DistributionSystemsGraph::GetElements()
- DistributionSystemsGraph::GetPorts()
- DistributionSystemsGraph::TraverseTree(system, traversalFunction)
- DistributionSystem::GetElements()
- DistributionSystem::GetMEPDomain()
- DistributionSystem::GetSystemCategory()
- DistributionSystem::GetPhysicalSystemIDs()
- DistributionSystem::TraverseTree(callback, rootElement)
- DistributionSystemsGraphTreeNode::GetElement / GetPreviousElement / GetNextElements
- DistributionSystemsGraphTreeNode::GetConnectedPortFromPreviousElement
- DistributionSystemsGraphTreeNode::GetConnectedPortFromThisElement

Sources:
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_distribution_systems_graph.html
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_distribution_system.html
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_distribution_systems_graph_tree_node.html
- https://graphisoft.github.io/archicad-api-devkit/group___m_e_p.html

**AC29 additional capability**: ACAPI::MEP::PhysicalSystem, new in Archicad 29, represents an instance with name/root/domain. It is persisted to PLN, while DistributionSystem is a temporary graph wrapper NOT serialized to PLN. PhysicalSystem::FindSystemIdsFromElementIds can reuse an existing DistributionSystemsGraph for efficiency.
Source: https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_m_e_p_1_1_physical_system.html

## Consequence

Do not implement MEP connectivity by naive geometric AABB or manual neighbor-distance heuristics while native system/port identity works. The existing graph is a read-only substrate for identifying impacted connected components, paths and dependencies, not a code compliance or hydraulic design engine.

Proposed impact path:
AC29 change event -> changed MEP element / equipment ports -> native DistributionSystemsGraph -> connected system IDs / elements / ports -> impacted subsystem contracts -> deterministic rule/engineering check -> readback/status.

Cross-links with ZONE graph:
- equipment GUID -> containing Zone GUID (separate geometry/semantic computation);
- MEP element GUID -> native MEP system(s);
- routing penetration -> wall/slab/shaft GUIDs (separate geometry/host relation);
- design intent -> CSE/VCE and regulations.
The project dependency graph stores cross-domain edges only, not duplicate native MEP connectivity logic.

## Limits and red flags

- Connections require native MEP objects and ports, not mere graphic proximity.
- A generic GDL object may lack a usable MEP connection; verify actual object type.
- Result does not imply correct hydraulic pressure, fixture units, flow, ventilation rates, short-circuit/current ratings, fire compartment performance, clearance, or Russian regulatory compliance.
- The API graph is ephemeral; do not persist DistributionSystem as if it were a PLN entity.
- Unknown system or missing ports => NOT_VERIFIED, not PASS.
- Actual AC29 performance, MEP fixture availability in the user's current model, system domain support, disconnect/reconnect observer coverage and licensing are NOT TESTED.

## Test MEP-GRAPH-01 (scratch PLN only)

1. Create two connected pipe segments + branch + terminal with consistent MEP domain/category.
2. Create an unconnected pipe with the same category.
3. Build graph; list system IDs, elements and ports; verify connected component count.
4. Traverse from root; inspect GetPreviousElement and GetNextElements and port identity.
5. Remove/replace a segment; rebuild graph; confirm network split and changed endpoints.
6. Place a visually touching but unconnected GDL object; assert no false native connection.
7. Repeat on ducts and cable carriers if their source domains are available.
8. Create/inspect PhysicalSystem, reopen scratch PLN and verify persisted PhysicalSystem vs transient DistributionSystemsGraph.
9. Correlate change events with systems invalidated and readback.
10. Compare manual GUID graph construction time vs native graph build, memory and sensitivity.
11. Mark unmodelled/externally linked networks outside the tested scope as NOT_VERIFIED.

Success gate:
- 100% precision/recall on synthetic known native port connections;
- no stale PASS on disconnection, duplication, undo and reconnection;
- no unwarranted claim of engineering calculation validity.

Decision: REUSE_NATIVE_AC29_MEP_NETWORK_QUERY; specialized engineering solvers remain separate; no runtime installation until fixture tests.
