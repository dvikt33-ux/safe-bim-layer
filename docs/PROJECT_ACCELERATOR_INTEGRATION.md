# Project Accelerator: integration prototype, 2026-10-09

Build on commit `308264c`, retaining all 113 research files, current modified
Tapir export, native Model Dump sources, BIM graph, SceneWriter and whole-scene
readback. This branch adds a registry and thin adapters, not another writer.

The first complete scenario is the existing **12-element pavilion frame**:
intent → source package index → registry coverage gate → existing dependency
graph → existing guarded scene runner → whole assembly readback → evidence and
metrics. It is a frame, not a finished building or approved engineering design.
Roof, finishes, MEP, calculations and issued drawings remain unsupported.

Stages execute sequentially. A mandatory missing capability blocks before
transport. Candidate providers cannot obtain execution permission from a schema
or a marketing claim. Direct modified Tapir and installed alesdev88 connection
are compared on identical read-only workloads, with explicit raw measurements.
The second adapter reuses the installed MIT `archicad_mcp.connection` implementation;
it does not start an MCP server or claim an MCP-session test. No wrapper binaries
are copied into this repo. Optional providers remain explicit blocked entries.

The integration CLI exposes offline planning and read-only preflight only.
The existing executor retains its separate `--execute` gate; this task authorizes
no live writes. Main, watcher, production PLN and stock Tapir API remain untouched.
No add-on installation, downloads of binaries, restart, project switching,
saving, tunnelling, property-value reads or automatic retries are introduced.

Native Model Dump adapter validates saved polygon-model evidence and preserves
absolute project coordinates, material-pool IDs, owner-vs-host semantics and
visibility scope. Its sample is historical and never verifies the new pavilion.
Live registration is checked using `API.IsAddOnCommandAvailable`; absence blocks
deep geometry coverage. AABB checks remain conservative envelope checks, not
proof of solid intersections or normative clearance.

Normative and detail adapters hash and index existing source packages. They
neither invent applicability nor certify compliance. Existing Favorites, GDL,
Hotlink, native MEP and IFC remain in the registry with their documented surface,
dependencies and current proof level. Optional IfcOpenShell requires an installed
runtime and a separate roundtrip; it is not silently substituted by JSON geometry.

Inventory scope: Archicad 29 installed APX folders, existing uv MCP environment,
Claude Store configuration, SafeBIM logs, local GDL artifacts and repo research.
Not found in this scope is not a whole-machine absence proof. Archicad executable
reports `29.0.0 R1 (5101)`; installed application UI previously reported 29.2.1.
Tapir installed APX is 4,953,088 bytes, SHA256
`75d719938426a8b954173539dd5264ab90d83e23db6507b1eb1462f44c8400fe`.
Licensing entitlement for Archicad/MEP is not independently verified.

The user disavowed the word “клавиат”: it was a GPT-generated task term.
Status `USER_DISAVOWED_GPT_GENERATED_TASK_TERM`; no replacement is authorized.
Historical `No module named sync_bridge` is recorded as a diagnostic observation,
not an identification of that term or a reason to change the watcher.

Acceptance: one complex synthetic scenario including all 12 related elements,
host references, final inventory and geometry readback; negative coverage,
wrong-project, transport error and drift checks; current read-only preflight;
measurement-backed comparison with unavailable variants reported NOT_MEASURED;
separate review PR. No live creation PASS may be claimed.

Verified: 101/101 selected offline checks pass on the final PR base. Complex
synthetic assembly includes all 12 related elements and final whole-scene
readback. Final live read-only preflight inspected 22 elements on AC29 build
5101 / modified Tapir 1.5.10 with unchanged inventory, 25 allowed read calls,
zero model writes and zero saves. GenerateDocumentation exported 262 commands;
API.IsAddOnCommandAvailable(GetModelDumpV1) returned false.

Three paired preflights per transport: direct median 0.498 s (0.487-0.746 s),
installed alesdev88 connection median 0.814 s (0.740-0.918 s). Includes local
source indexing and registration checks. Project, inventory and native workload
match. No write-speed or long-run-reliability conclusion follows.

Full historical dump structure validated: 9,261 bodies, 340,188 vertices,
242,264 faces, 570 hole contours, 2.525 s. 5,297 owner records include 5,296
known elements and one unresolved owner. This does not prove current geometry,
solid intersection, normative clearance or the new pavilion.

The generic retained runner labels injected transports SYNTHETIC. The closed
read-only integration adapters add transportEvidenceKind=LIVE_READ_ONLY;
synthetic tests retain SYNTHETIC labels.

PR is stacked on chatgpt/whole-scene-v1-20261009 (PR #15), exact base
f02a167eb73cb149713cf5e613911b144fce5be2. No watcher source changes are included.
Schema-path/hash fixes from the prior MVP are retained in SceneWriter. Two
SQLite test connections are closed explicitly for Windows temporary cleanup.

Run from repo root (new evidence folders are required):

```powershell
python scripts/archicad_accelerator_integration.py --output <offline-folder> --saved-dump examples/model_dump_v1.sample.json
python scripts/archicad_project_accelerator.py --refresh-schema --output <schema-folder>
python scripts/archicad_accelerator_integration.py --preflight --schema <schema-folder>/tapir-scene-live.json --output <preflight-folder>
python scripts/archicad_accelerator_integration.py --compare-readonly --schema <schema-folder>/tapir-scene-live.json --output <comparison-folder>
python -m unittest discover -s tests -p 'test_archicad_*.py' -v
```

Offline CLI compiles the plan. Complex synthetic execution is covered by
test_archicad_accelerator_integration.IntegratedTests and never calls Archicad.
--require mep-designer blocks before host access. No integration --execute exists.

Current [lgradisar pyproject](https://raw.githubusercontent.com/lgradisar/archicad-mcp/main/pyproject.toml)
declares 0.2.0, MIT, Python>=3.10, FastMCP>=4,<5; it is absent in inspected runtime/config.
[alesdev88 release](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.7.1)
is v0.7.1; installed version remains 0.6.0.
[Husky requirements](https://mcp.huskybim.com/docs/requirements) name v1.5.54;
[vendor pricing](https://huskybim.com/pricing) states free-account access with
activation limits, updating the earlier paid-dependency assumption. No installer
was downloaded or license activated. [IfcOpenShell source/license](https://github.com/ifcopenshell/ifcopenshell)
is LGPL-3.0 and absent from the inspected uv runtime; native IFC roundtrip is unverified.
