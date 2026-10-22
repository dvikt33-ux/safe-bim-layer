# APA integration — installation and evidence plan R01
Date: 2026-10-22. Status: design only; no local integration tests.

## Target
Production: Archicad 29; Rhino 8 with Grasshopper. Archicad 30 is not a dependency. No paid third-party MCP subscription required.

## Candidate components (verify versions and licenses before installation)
1. Archicad 29, valid license.
2. Rhino 8, valid license (Grasshopper included).
3. Graphisoft Grasshopper–Archicad Live Connection matching Archicad 29.
4. Tapir for Archicad: https://github.com/ENZYME-APD/tapir-archicad-automation
5. Archicad MCP candidate: https://github.com/lgradisar/archicad-mcp
6. Rhino MCP candidate: https://github.com/firstofthekind/rhino-mcp
7. Python runtime and MCP client/orchestrator — exact versions to derive from selected repositories.
8. RhinoCommon and Grasshopper SDK are programming APIs included with Rhino/Grasshopper, not necessarily separate installers.
Optional: Rhino.Compute only if headless computation is justified; review licensing.

## Architecture
Task specification -> orchestrator -> Rhino/Grasshopper adapter -> geometry/graph evidence -> validated handoff -> Archicad 29 adapter -> BIM evidence -> acceptance report.
MCP is transport, not an assurance of geometry creation or validation.

## Required evidence per operation
- task_id, operation_id, revision, software versions, units, coordinate reference and tolerance
- Rhino object GUIDs and geometry type; Brep validity, closedness, topology; bounding box; mass properties when defined
- Grasshopper document and component instance IDs, input values, wires/dependencies, solver errors
- geometry revision and checksum or stable reference to full serialized geometry
- Archicad element GUIDs, type, placement, dimensions, classifications and source-object mapping
- machine-readable pass/fail checks, error details, timestamps
Screenshots are supplemental, never substitutes for geometric evidence.

## First acceptance test (when laptop available)
A. Read-only: inspect a known Rhino Brep and Grasshopper graph; compare against expected values.
B. Parameter change: modify one parameter, recompute, confirm geometric invariants and diff.
C. Transfer to Archicad 29: create supported native BIM element, read it back, compare with design intent.
D. Rollback: failed validation must not corrupt the production project; use a copy and preserve logs.
No unattended modeling until tests pass.

## Unverified / risks
- MCP repositories' current licenses, command lists, maintainers, dependencies and Rhino 8 / Archicad 29 compatibility require code-level review.
- Grasshopper Live Connection does not guarantee every Rhino shape maps to native BIM semantics.
- JSON API / Tapir coverage must be audited operation by operation.
- ChatGPT has no direct connection to local Rhino in this conversation.
- No installation, interoperability test, or independent audit has occurred.

## Installation sequence (provisional)
Check OS and licensing -> install/verify Archicad 29 -> install/verify Rhino 8 and Grasshopper -> matching Live Connection -> test manual BIM transfer -> Tapir -> test read-only Archicad API -> Rhino MCP in isolated environment -> test read-only graph and geometry -> Archicad MCP in isolated environment -> integrate orchestrator -> evidence acceptance tests.
Do not install unreviewed code into production projects.
