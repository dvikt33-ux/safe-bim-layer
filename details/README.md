# Construction detail machine library

This directory is the canonical machine-readable construction-detail layer for the Archicad safety/execution project.

## Active release

`ACTIVE_RELEASE` points to **v2.3**.

The v2.3 systematized snapshot contains the complete active state captured from the construction-detail processing workflow:

- 1,211 detail units;
- 1,211 active detail → Archicad IR bindings;
- 1,179 typed parameter facts;
- 546 component variants;
- 598 unresolved dimension-binding / source-binding tasks;
- 24 logical source documents, deduplicated across PDF/DXF/DWG representations where applicable.

### v2.3 focus

FAVORIT «Листовые материалы», section 1 (sheets 1.1–1.12 / PDF pages 4–15) was re-read directly from the supplied source. The release adds a 36-entry source component catalogue, six facade-subframe system variants, 24 typed technical facts, 10 explicit dimensioned component variants and 14 manufacturer-printed SP/GOST/TU references stored only as unverified source claims. Twelve high-priority catalogue transcription tasks were closed.

## Layout

- `index/sources.json` — source registry.
- `index/source_counts.json` — per-source counts and system metadata.
- `index/systems.json` — high-level source grouping for selective loading.
- `releases/v2.3/machine-state-v2.3.tar.gz.b64` — base64 transport form of the complete systematized active machine state.
- `releases/v2.3/SHA256SUMS.txt` — SHA-256 of the decoded `machine-state-v2.3.tar.gz`.
- `releases/v2.3/manifest.json` — file-level hashes and release contents.
- `releases/v2.3/audit.json` — release audit.
- `releases/v2.3/summary.json` — release counts.
- `releases/v2.3/source_verify.json` — SHA-256 verification state for the 40 preserved source representations.
- `tools/unpack_release.py` — deterministic decode/check/unpack helper for the active release.

## Safety policy

1. Manufacturer technical solutions are **not** promoted to mandatory normative requirements.
2. Normative references quoted by a source remain `claimed_by_source_not_independently_verified` until independently verified against the applicable current SP/GOST edition.
3. Raster/pixel measurements are never converted into construction dimensions.
4. DXF/DWG geometry is not interpreted 1:1 until drawing scale/units are resolved.
5. `commit_allowed=false` is the default whenever a critical dimension, host, material, structural calculation, fastener, or geometric binding is unresolved.
6. Source anomalies are preserved explicitly; missing catalogue rows, ambiguous mappings and suspected source typos are not silently repaired.
7. The runtime must load only the requested system/source/detail family; unrelated building classes must not be injected into the agent context.

## Source preservation

The raw 40 source files are intentionally not duplicated in Git. Their verified hashes and representation metadata are stored in the release registry/verification files; the separate FULL offline archive remains the evidence-preservation package.