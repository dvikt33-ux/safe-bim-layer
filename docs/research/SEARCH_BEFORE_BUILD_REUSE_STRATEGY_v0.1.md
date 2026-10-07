# SEARCH-BEFORE-BUILD / REUSE-FIRST strategy v0.1

Date: 2026-10-08
Status: ACTIVE DESIGN PRINCIPLE
Branch: feature/working-archicad-mvp

## Core thesis

Before implementing any substantial capability, assume that at least part of it may already exist.

The default workflow is:

1. Define the exact capability we think we need.
2. Search broadly for existing implementations, APIs, SDKs, MCP servers, open-source libraries, commercial tools, government data feeds, CAD plugins and academic projects.
3. Test promising candidates against the real SBIM requirements.
4. Classify each capability as:
   - REUSE_AS_IS
   - WRAP
   - ADAPT
   - EXTEND
   - REPLACE
   - WRITE_ONLY_IF_GAP_PROVEN
5. Only then write code.

## Target outcome

The project should be primarily an integration/orchestration system, not a collection of reimplementations.

Prefer:
- existing Archicad tools/plugins over writing geometry commands from scratch;
- existing graph, solver and spatial-index libraries over custom algorithms;
- state/open normative sources and existing legal MCPs over manual legal ingestion;
- existing technical-detail libraries over rebuilding catalogues one album at a time;
- existing IFC/BIM validators over duplicate QA engines;
- existing AI/local-model runtimes over custom inference infrastructure.

## What is likely reusable

### BIM execution
- Archicad Add-On API
- Graphisoft JSON/Python API
- HuskyBIM and similar existing Archicad AI/control layers
- Hotlink modules / repeated-storey workflows
- IFC/BCF tooling

### Geometry / optimization
- Boost.Graph
- Boost.Geometry R-tree
- GEOS/Shapely
- CGAL where needed
- OR-Tools CP-SAT
- Z3

### BIM validation/interchange
- IfcOpenShell
- IfcTester
- IfcDiff
- IDS tooling

### Normative / legal
- pravo.gov.ru public interfaces
- pravo-mcp
- RusLawOD
- Стройкомплекс.РФ requirements registry
- protect.gost.ru
- Minstroy official sources
- TechExpert / NormaCS where access exists
- FPPD / EGRKN / regional GIS for spatial constraints

### Details / standard solutions
- TechExpert TPD and other existing catalogues
- manufacturer technical albums
- existing typical series
- project-specific curated detail library only for verified selected solutions

### AI/runtime
- cloud GPT for high-level reasoning
- smaller/local models only where latency/privacy/cost/batch-processing justify them
- existing model routers/agent frameworks before custom orchestration engines

## What is still likely unique to SBIM

Existing components will not eliminate all custom development.

The most project-specific layer is likely to be:

- Canonical Project World Model
- Canonical Requirement / Rule IR
- normative-to-project bindings
- typed causal dependency graph
- design-intent representation
- change-transaction orchestration
- impact-cone discovery
- multi-domain invalidation and propagation
- escalation policies
- candidate ranking by project disruption
- source reconciliation/provenance
- Archicad-specific semantic mapping where no existing tool exposes required semantics
- unified UI/control plane

This is where custom code should concentrate.

## Architecture implication

Think of SBIM as an operating system / integration kernel:

Existing tools
    -> capability adapters
    -> canonical semantic layer
    -> causal/normative/project graphs
    -> transaction planner
    -> validation/ranking
    -> BIM executor
    -> independent audit

The adapters should be replaceable.

No commercial provider, MCP server, local model or BIM plugin becomes the single point of failure.

## Coding gate

A new module above trivial glue should not be implemented until a reuse audit records:

- capability needed;
- search queries/sources examined;
- candidate products/projects;
- license/cost;
- API/automation availability;
- freshness/maintenance status;
- test result;
- reason for rejecting reuse.

If no gap is proven, custom implementation is BLOCKED_BY_REUSE_AUDIT.

## Expected benefit

This strategy should reduce:
- implementation time;
- maintenance burden;
- duplicate bugs;
- long-term API surface;
- runtime overhead from unnecessary custom layers.

It should improve:
- speed to MVP;
- interoperability;
- replaceability;
- auditability;
- access to mature algorithms/data.

## Warning

"Found existing software" does not mean "trust and adopt it".

Every external component still requires:
- capability test;
- provenance/security review;
- license check;
- update/freshness audit;
- performance benchmark;
- failure-mode analysis;
- fallback plan.

The goal is minimal **necessary** code, not minimal due diligence.
