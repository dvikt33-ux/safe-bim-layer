# Construction detail machine library

This directory is the canonical machine-readable construction-detail layer for the Archicad safety/execution project.

## Active release

`ACTIVE_RELEASE` points to **v2.2**.

The v2.2 systematized snapshot contains the complete active state captured from the construction-detail processing workflow:

- 1,211 detail units;
- 1,211 active detail → Archicad IR bindings (the database also preserves non-active/historical IR revisions inside the source working release, but the systematized snapshot exports only the active binding for every detail);
- 1,155 typed parameter facts;
- 536 component variants;
- 610 unresolved dimension-binding tasks;
- 24 logical source documents, deduplicated across PDF/DXF/DWG representations where applicable.

## Layout

- `index/sources.json` — source registry.
- `index/source_counts.json` — per-source counts and system metadata.
- `index/systems.json` — high-level source grouping for selective loading.
- `releases/v2.2/machine-state-v2.2.tar.gz.b64` — base64-encoded full **systematized active machine state**, not the raw source PDFs/DXF/DWG. `tools/unpack_release.py` decodes it, verifies the decoded tarball SHA-256, and extracts it.
- `releases/v2.2/manifest.json` — file-level hashes and release contents.
- `releases/v2.2/audit.json` — release audit.
- `releases/v2.2/summary.json` — release counts.
- `releases/v2.2/source_verify.json` — SHA-256 verification state for the 40 preserved source files.
- `tools/unpack_release.py` — deterministic unpack/check helper.

## Safety policy

1. Manufacturer technical solutions are **not** promoted to mandatory normative requirements.
2. Normative references quoted by a source remain `claimed_by_source` until independently verified against the applicable current SP/GOST edition.
3. Raster/pixel measurements are never converted into construction dimensions.
4. DXF/DWG geometry is not interpreted 1:1 until drawing scale/units are resolved.
5. `commit_allowed=false` is the default whenever a critical dimension, host, material, structural calculation, fastener, or geometric binding is unresolved.
6. The runtime must load only the requested system/source/detail family; unrelated building classes must not be injected into the agent context.

## Source preservation

The raw 40 source files are intentionally not duplicated in Git. Their verified hashes and representation metadata are stored in the release registry/verification files; the FULL offline archive remains the evidence-preservation package.