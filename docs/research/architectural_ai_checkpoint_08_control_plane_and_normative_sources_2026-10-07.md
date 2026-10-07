# Architectural AI checkpoint 08 — workstation control plane and normative-source pivot

Date: 2026-10-07
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp

## Executive conclusions

This research changes two assumptions:

1. **Archicad extensions should not be "embedded in the TPL".**
   Add-Ons are application/workstation-level. The correct deployable unit is an Archicad Workstation Bundle: TPL + Work Environment + Add-On manifest + libraries/fonts/translators + runtime control plane.

2. **We should stop treating the Russian normative corpus as something we must manually rebuild from PDFs.**
   Existing products already expose large parts of the content, versioning, extracted requirements and change tracking. Our custom work should become an integration + causal/legal semantics layer.

## Evidence: Archicad deployment model

Graphisoft AC29 documentation states:
- a TPL contains project preferences, placed elements/defaults and project setup;
- a new project separately selects a Template and a Work Environment Profile;
- the Work Environment can override template-side settings;
- Work Environment profiles/schemes are exportable and stored separately;
- Add-Ons are loaded from Archicad's Add-Ons folder or another designated Add-On folder stored at workstation/user level;
- company-default unattended installation can deploy Work Environment + Template + DXF/DWG translators through `--customEnvironment`.

Implication:
If a new/blank project appears to "lose an extension", distinguish:
- Add-On not installed/loaded;
- command hidden by Work Environment;
- required companion library missing;
- project-specific data/connection absent.

Do not solve all four by bloating the TPL.

## Recommended control-plane stack

### Provisioning: WinGet Configuration + vendor installers

WinGet Configuration uses declarative YAML + DSC to establish desired machine state and can test whether the current Windows machine conforms.

Use for:
- common tools;
- build tools;
- Git;
- CMake/Ninja if packaged;
- Docker/Open WebUI/LiteLLM dependencies where applicable.

For proprietary/vendor installers:
- keep version/hash/install-scope manifest;
- use vendor-supported silent install only;
- verify after install.

### Native process supervision: Process Compose

Process Compose is a mature docker-compose-style orchestrator for non-containerized applications:
- parallel/serial execution;
- dependencies/startup order;
- recovery policies;
- liveness/readiness checks;
- TUI/CLI;
- REST API;
- logs;
- namespaces/profiles;
- Windows support.

This maps closely to:
- local model server;
- project engine;
- retrieval service;
- normative adapter;
- graph service;
- local MCP bridge;
- optional dashboards.

Do not write our own scheduler/process supervisor.

Use Windows-specific probe overrides where necessary.

### MCP lifecycle: LiteLLM MCP Gateway or Docker MCP Gateway

LiteLLM currently supports a central MCP endpoint over stdio/SSE/streamable HTTP and can namespace multiple MCP servers while also serving as the multi-model gateway.

Docker MCP Gateway can centrally manage server lifecycle, routing, credentials, profiles and isolation for containerized/remote MCP servers.

Decision for MVP:
- prefer one gateway, not both;
- benchmark LiteLLM first because it can cover both models and MCP;
- use Docker MCP Gateway if isolation/security/catalog management becomes more valuable than unified model routing.

### Unified AI UI: Open WebUI — optional

Current Open WebUI supports:
- multiple model providers;
- OpenAI-compatible endpoints;
- native MCP (HTTP) and MCP proxying;
- model-specific tools/knowledge;
- multi-model chat.

Potential role:
- one local "cockpit" when direct ChatGPT UI cannot access the entire local tool fabric.

Do not force this onto the user if the ordinary ChatGPT workflow remains preferable. It is an optional front-end, not project authority.

## Runtime profiles

To preserve speed and laptop resources, do not launch every component.

### CORE_INTERACTIVE
Archicad + essential add-ons + event/revision bridge + compact project engine.

### DEEP_COMPILER
Starts deep local LLM/retrieval/normative compilation only for L0/L1 work.

### RELEASE_AUDIT
Starts IFC and independent checkers only for milestones.

### VISUALIZATION
Starts GPU-heavy render tools separately from deep local LLMs whenever possible.

## Major normative-source discovery

### 1. GARANT Connect already has REST API AND MCP

Current public documentation for GARANT Connect API v2.3.0 exposes:
- full-text search;
- snippets inside documents;
- automatic hyperlinking of references to normative documents;
- whole-document export;
- block/fragment export;
- document change detection;
- fragment-on-control change detection;
- document metadata;
- redaction/version history.

The same capabilities are exposed through `mcp.garant.ru`.

This is almost exactly what our normative ingestion/version watcher needs.

Important:
- requires a separate API token/rights from the servicing GARANT organization;
- browser authorization alone does not imply API entitlement.

Potential use:
- source retrieval;
- exact clause/block identity;
- citation/reference extraction;
- redaction tracking;
- normative-change notifications.

Do not scrape GARANT HTML in production if licensed API/MCP access is available.

### 2. TechExpert "Requirements Registry: Construction"

Current product documentation says it contains an expert-selected target base of construction requirements and supports:
- working with current requirements;
- project-specific requirement sets;
- checklists/control;
- links to requirements;
- export outside the system.

"TechExpert SMART" describes deeply structured SMART documents where requirements can be classified, tracked for changes and exported into third-party software such as CAD.

TechExpert also advertises the Kodeks API for individual integration with CAD/CAM/CAE/PDM/CRM/PM/MDM/RM systems.

This is the closest existing product found so far to our planned normalized requirement database.

Priority: request/demo/evaluate licensing and API/export structure before manually normalizing thousands of requirements ourselves.

### 3. Government "Stroykompleks.RF" Requirements Registry

The state system contains:
- Requirements Registry;
- Documents Registry;
- Construction Information Classifier.

Minstroy previously stated that the Requirements Registry contained more than 100,000 requirements across about 600 normative documents and that machine-readable/machine-understandable formats were planned toward 2027.

The current public landing page observed during this audit shows zero in its displayed counters, so availability/data-export behavior must be verified rather than assumed.

Role:
- authoritative applicability/source index;
- potentially a future machine-readable source;
- not yet assumed to be our only runtime feed.

### 4. NormaCS

NormaCS remains a large current construction standards/document corpus with status/catalog functionality.
It should be evaluated as a source/catalog and cross-check layer.

In this pass, no equally clear public evidence was found that it exposes the same clause-level requirement/export API as TechExpert's Requirements Registry.

## New normative architecture

Do NOT build:
`PDF -> OCR/manual parse -> our private copy of the whole Russian standards universe`

as the primary path.

Build adapters:

`GARANT API/MCP`
`TechExpert Requirements/Kodeks API`
`Stroykompleks.RF`
`NormaCS`
`official Minstroy/Rosstandart sources`
        ↓
`Normative Source Adapter Layer`
        ↓
`Normalized Clause/Requirement IDs`
        ↓
`our legal/applicability/reference graph`
        ↓
`Active Project Rule Pack`

Our unique layer remains:
- legal/applicability semantics;
- dated/undated reference behavior;
- conflict/specialization/exception resolution;
- connection from requirements to project variables and BIM entities;
- deterministic formulas/constraints;
- project impact propagation.

Existing hand-curated YAML rules are retained as:
- verified seeds;
- tests;
- regression fixtures;
- audit evidence.

They are not wasted.

## Target one-click working experience

Conceptual user flow:

`SBIM START`
  -> workstation preflight
  -> start CORE_INTERACTIVE profile
  -> verify Archicad build
  -> verify TPL/schema
  -> verify Work Environment
  -> verify required Add-Ons
  -> verify libraries/fonts/translators
  -> verify project engine
  -> verify tool/model gateway
  -> open project + preferred AI front-end
  -> READY

When a deep task appears:
`Router -> start DEEP_COMPILER namespace -> perform job -> persist Project Kernel -> stop heavy worker`.

The user does not pick ports/models/services manually.

## What still justifies custom software

A small **SBIM Control Center** may still be justified, but only as a thin UI/control layer over existing supervisors/gateways.

It should NOT implement:
- process supervision;
- package management;
- model gateway;
- MCP gateway;
- vector DB;
- database;
- container runtime.

Potential custom responsibilities:
- project selection;
- profile selection;
- workstation preflight summary;
- project/template/add-on compatibility matrix;
- one-click start/stop;
- current Archicad project identity;
- project revision;
- resource profile;
- warnings/blocks;
- links/buttons to ChatGPT/Open WebUI/Archicad/logs.

The first prototype can simply consume Process Compose REST status and our project-health endpoint.

## Immediate priority sequence

1. Finish current AC29 template materialization and validation.
2. Export/version the matching AC29 Work Environment profile.
3. Define Workstation Bundle manifest.
4. Install/evaluate HuskyBIM.
5. Evaluate dRofus.
6. Evaluate GARANT Connect API/MCP access.
7. Evaluate TechExpert Requirements Registry + Kodeks API/export.
8. Verify Stroykompleks.RF machine access/export.
9. Prototype Process Compose runtime manifest.
10. Only after these results decide whether to build a custom SBIM Control Center UI.

## Search-before-build rule applied

This checkpoint explicitly avoids custom-building:
- Add-On installer manager;
- process supervisor;
- MCP server manager;
- model gateway;
- normative full-text database;
- generic requirement management;
- package manager.

Build only the architectural/project-specific gaps.
