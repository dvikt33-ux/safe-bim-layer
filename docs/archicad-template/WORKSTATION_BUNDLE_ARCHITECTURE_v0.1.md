# Archicad 29 Workstation Bundle Architecture v0.1

Date: 2026-10-07
Status: DRAFT / active implementation direction
Target: AC29_RU_SBIM_1.0 workstation environment

## Critical correction

An Archicad `.tpl` is NOT the container for installed Add-Ons.

Graphisoft's own documentation separates:
- Project Template;
- Work Environment;
- application-level Add-Ons;
- libraries;
- translators/defaults.

On Windows, Archicad discovers Add-Ons from its application Add-Ons folder or the designated Add-Ons folder stored in the user's Graphisoft/Archicad Add-On Manager registry settings. This is application/workstation state, not project-template state.

The New Project dialog separately selects:
1. Template;
2. Work Environment Profile.

A Work Environment profile can hide or expose Add-On commands through its command/menu layout even when the Add-On itself is installed.

Therefore the deliverable must be a **Workstation Bundle**, not "one TPL containing all extensions".

## Workstation Bundle layers

### Layer A — Project Template: `TDK_AC29.tpl`

Contains project-dependent defaults:
- project preferences;
- project structure;
- attributes;
- semantic classifications/properties;
- Favorites;
- Views/Navigator;
- layouts/master layouts;
- Publisher definitions where materialized;
- project library links;
- IFC translator configuration;
- project information;
- project-side automation metadata.

Current repository work remains the base for this layer.

### Layer B — Work Environment Profile: `TDK_AC29_WE`

Contains:
- command layout;
- menus;
- toolbars;
- workspace/palettes;
- shortcuts;
- company standard schemes;
- user/tool schemes as appropriate.

This profile must be exported and versioned separately from the TPL.

It must be derived from the current Archicad 29 Work Environment, not from an older-version profile, so newly introduced Archicad commands are not accidentally hidden.

### Layer C — Add-On Manifest

Application-level extension inventory.

Each entry records:
- stable ID;
- product/add-on name;
- required version/build;
- installer source;
- installation path/scope;
- expected Archicad version;
- license/account requirement;
- required libraries;
- menu/command expectations;
- process/MCP endpoint if any;
- health check;
- update policy;
- rollback/uninstall procedure;
- status: REQUIRED / OPTIONAL / EXPERIMENTAL / BLOCKED.

Initial candidates:
- HuskyBIM for Archicad 29;
- dRofus Archicad Add-On;
- Safe-BIM native Add-On / Model Dump bridge;
- Tapir only for capabilities still required after HuskyBIM comparison;
- official Graphisoft add-ons actually used by the workflow;
- Rhino/Grasshopper Live Connection when required;
- Solibri connection if retained after QA-tool comparison.

### Layer D — Libraries / fonts / exchange presets

Versioned separately:
- Global Library;
- SBIM library packs;
- manufacturer/project packs;
- fonts manifest;
- DWG translators;
- external reference policies;
- transfer sets;
- classification/property XML;
- any required Add-On companion library.

Template links may refer to these resources, but their installation/presence must be verified by workstation preflight.

### Layer E — Runtime Control Plane

Does not belong inside Archicad/TPL.

Responsibilities:
- start/stop background services;
- resolve service dependencies;
- perform health checks;
- expose logs/status;
- manage model endpoints;
- manage MCP/tool endpoints;
- load resource profiles;
- open the selected AI front end;
- report Archicad/template/add-on compatibility.

Candidate foundation:
- Process Compose for native/local processes;
- LiteLLM as model/MCP gateway when useful;
- Docker MCP Gateway as an alternative for containerized/isolated MCP servers;
- Open WebUI as an optional unified AI interface;
- WinGet Configuration for repeatable workstation provisioning.

Do not code a process manager, MCP gateway, model gateway or package manager from scratch.

## Resource profiles

Do not run the full stack permanently.

### CORE_INTERACTIVE

Always-available working profile:
- Archicad 29;
- required Add-Ons;
- Safe-BIM event/revision bridge;
- lightweight project engine;
- model/tool gateway only if required.

No large local model by default.

### DEEP_PROJECT_COMPILER

Started only for L0/L1 analysis:
- local deep LLM (if benchmark proves useful);
- normative source adapters;
- graph/rule compiler;
- retrieval/embedding stack;
- long-running analysis workers.

Stop/unload after compilation to return RAM/VRAM to Archicad/Twinmotion.

### RELEASE_AUDIT

Starts independent validators:
- IFC export/check;
- IfcOpenShell/IfcTester/IfcClash as applicable;
- Solibri or BIMcollab if selected;
- deep discipline checks;
- release comparison.

### VISUALIZATION

Starts rendering/visualization tools only when required.
Must not compete with a memory-heavy local deep model unless explicitly scheduled.

## Reproducible machine setup

Use WinGet Configuration/DSC for packages that can be provisioned by WinGet.

For vendor products not in WinGet:
- maintain signed/hashed installer metadata;
- perform version/health detection;
- install manually or through the vendor-supported silent installer;
- never download/execute unknown installers automatically.

Graphisoft supports company-standard defaults during unattended installation via `--customEnvironment`, including:
- Work Environment;
- Archicad Template;
- DXF/DWG translators.

This is an installation/deployment mechanism, not a dependable runtime profile switch.

## New-project startup contract

A project is READY only when all gates pass:

1. Archicad build/version PASS.
2. `TDK_AC29.tpl` version PASS.
3. `TDK_AC29_WE` profile present/current.
4. required Add-Ons installed and loaded.
5. required Add-On commands visible/usable.
6. required libraries resolved.
7. fonts PASS.
8. DWG/IFC translators PASS.
9. Safe-BIM bridge health PASS.
10. project schema/version fields PASS.
11. selected Runtime Profile health PASS.

Failure returns `BLOCKED_SETUP`, with exact missing component(s).

## User workflow target

Desired normal startup:

1. User starts **SBIM Control Center** (or the reusable supervisor/UI selected after benchmark).
2. Selects project/profile or accepts auto-detected project.
3. Control plane starts only CORE_INTERACTIVE dependencies.
4. Archicad opens with the standard workstation environment.
5. Preflight verifies template + Work Environment + Add-Ons + libraries + services.
6. User opens/uses the preferred AI client.
7. Heavy services are started automatically only when a task escalates to a deep-analysis profile.

The user should not manually start six terminals, choose ports or select AI backends.

## Work Environment vs template rule

Work Environment settings can override settings associated with opening the template.
Therefore the released workstation pair is:

`TDK_AC29.tpl + TDK_AC29_WE`

Both are versioned and tested together.

## Immediate implementation order

1. Finish materializing and validating the current AC29 template candidate.
2. Create/export the AC29-native Work Environment profile.
3. Make it the default profile on the development workstation after validation.
4. Create Add-On manifest.
5. Install/evaluate HuskyBIM first.
6. Evaluate dRofus.
7. Add template/add-on/library preflight.
8. Prototype Process Compose runtime manifest for background services.
9. Only then decide whether a custom graphical SBIM Control Center is still needed.

## Primary sources checked

- Graphisoft AC29: Template Files.
- Graphisoft AC29: Work Environment Profiles / Schemes.
- Graphisoft API: Structure of an Add-On.
- Graphisoft AC29 BIM Manager guide: Customized Company Defaults for Unattended Installation.
- Graphisoft AC29: Create New Project.
