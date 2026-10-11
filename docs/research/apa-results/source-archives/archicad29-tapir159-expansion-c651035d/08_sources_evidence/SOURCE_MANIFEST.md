# Source/evidence manifest

This manifest lists the principal source families used by the research. Detailed claim-to-source links are embedded in the individual audit files.

## Upstream Tapir baseline

- Repository: `ENZYME-APD/tapir-archicad-automation`
- Tag: `1.5.9`
- Tag commit: `d0dbb11b13942e014661e1402b07958b70cd9dba`
- Release date observed from GitHub release metadata: 2026-09-09.

Principal source files:

- `archicad-addon/Sources/AddOnMain.cpp`
- `ElementCreationCommands.cpp/.hpp`
- `ExtendedElementCommands.cpp/.hpp`
- `ElementCommands.cpp`
- `ProjectCommands.cpp`
- `FavoritesCommands.cpp`
- `LibraryCommands.cpp`
- `DesignOptionCommands.cpp`
- `SolidElementOperationCommands.cpp`
- `NotificationCommands.cpp`
- `ScriptUICommands.cpp`
- `NavigatorCommands.cpp`
- `DocumentCreationCommands.cpp`
- `ElementGroupingCommands.cpp`
- `PropertyCommands.cpp`
- `ClassificationCommands.cpp`
- `MEPCommands.cpp`
- `IFCCommands.cpp`
- `IssueCommands.cpp`
- `RFIX/Images/CommonSchemaDefinitions.json`

Examples used as behavioral evidence include:

- `Examples/hotlink_instances.py`
- `Examples/roof_details.py`
- `Examples/trim_elements.py`
- `Examples/get_details_of_elements_filtered.py`
- `Examples/get_point_from_user.py`
- `Examples/get_3d_bounding_box_of_stairs.py`

## Tapir 1.5.8 -> 1.5.9 delta

GitHub compare baseline:

- 1.5.8 commit: `ce033d6bdcc90b538b3c5f7ab62f676099b96823`
- 1.5.9 tag commit: `d0dbb11b13942e014661e1402b07958b70cd9dba`
- observed delta: 258 commits ahead.

Large changed areas include element creation, element details, project commands, common schemas, libraries, SEO, navigator/docs and Grasshopper bindings.

## Safe BIM sources

Repository: `dvikt33-ux/safe-bim-layer`

Important research/product snapshots:

- `14bc0d2a37a751029381e506809025eb434aa721` — runtime-safety hardening.
- `ebbe7794ad9f7b7c9c921c3d0d8c0494fa6f4808` — wall absolute-readback-Z fix.
- `f7d38af825de57fc57660eeddf1186cc5b21ac71` — offline future-house primitive builders.
- `c6ab4749e8784cc65170167d166daa6cc219a931` — offline hardening after independent audit.

## Graphisoft official documentation families

### Archicad API / automation technologies

- `https://archicadapi.graphisoft.com/`
- Automation API / Python Connection documentation.
- C++ Add-On API / type documentation.

### GDL / library-part development

- `https://gdl.graphisoft.com/gdl-basics/about-gdl/`
- `https://gdl.graphisoft.com/tips-and-tricks/how-to-use-the-lp_xmlconverter-tool/`
- Archicad 29 GDL Reference Guide / library-part identity documentation.

### Archicad 29 Help

- Template/TPL behavior and project default/settings content.
- Favorite import/export/dependency behavior.
- Grasshopper–Archicad Live Connection AC29 guide.

## External/reference repositories

### Progressive MCP discovery

- `SzamosiMate/tapir-archicad-MCP`
- Used as an architectural reference for progressive tool discovery/schema retrieval.
- Safe BIM research explicitly does **not** adopt unrestricted MCP->Tapir writes.

### BIBIM

- `SquareZero-Inc/bibim-archicad`
- Used as a reference for Archicad AI UX/provider/context/tool patterns.
- Not treated as a replacement for Safe BIM receipt/reconciliation semantics.

## AI runtime sources

Principal public documentation/repositories referenced by the AI resource audit:

- Ollama API/FAQ: keep-alive, model residency, concurrency/KV controls.
- `ggml-org/llama.cpp` server docs: sleep/idle and OpenAI-style serving.
- `mostlygeek/llama-swap`: on-demand multi-model process broker pattern.
- LM Studio developer docs: JIT load/TTL/auto-evict.
- TabbyAPI repository: alternative NVIDIA-focused inference server.
- Microsoft Windows docs: process priority and Job Objects.

## Evidence classification rule

Research distinguishes:

- `SOURCE`: code/docs at a known version/ref;
- `OFFLINE_TEST`: deterministic local/fake test evidence;
- `LIVE_READ`: read-only observation from Archicad;
- `LIVE_WRITE_PROBE`: controlled write + exact GUID/raw readback;
- `INDEPENDENT_AUDIT`: separate adversarial audit.

Source evidence can establish a contract or narrow a probe, but it does not automatically promote a mutation to production. Live certification and independent audit remain required where the capability matrix says so.
