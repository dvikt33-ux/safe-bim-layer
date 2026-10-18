# APA AC29 IFC geometry B3

Three independent operations through existing DynamicCommands:

| Command in AddOn.APAIFCGeometryB3 | Upstream implementation | Artifact |
|---|---|---|
| IFCGeometryOBJ | geom.iterator + serializers.obj | model.obj + model.mtl |
| IFCGeometryGLB | geom.iterator + serializers.gltf | model.glb |
| IFCGeometryBounds | util.shape.get_vertices/get_bbox | geometry-bounds.json |

All take `a` (IFC), `output` (new directory), `query` (IfcOpenShell selector).
This fulfills geometry conversion through the ready Python API rather than
requiring a separate IfcConvert executable. The exact installed 0.8.5 serializer
signatures were inspected and executed. Unlike newer online examples, this
version takes separate geometry settings and serializer settings objects.
No separate IFC geometry engine or native Archicad bridge is introduced.

The upstream API is documented at
https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html .
Newer online examples are reference material; version 0.8.5 execution is the
contract proof. IfcOpenShell is an independently installed LGPLv3+ distribution.

The existing B2 runtime, B2 parameter guards and V2 hash/path helpers are reused.
Each execution uses a private SHA-verified IFC copy. All selected objects must
be represented IfcProducts. Every requested STEP ID must be processed; partial
conversion fails without a success receipt. Bounds use IFC world coordinates
in SI metres (including placements). Mesh export does not establish native BIM
semantics, georeference calibration, physical quantities or regulatory compliance.

Typed readers count OBJ vertices/faces, hash the accompanying MTL, validate the
GLB v2 header/length and parse only its explicitly typed JSON chunk (binary mesh
bytes never enter a JSON parser). Parent process checks source/adapter/artifact
SHA and report disk readback. New output directories are exclusive.

Eight real-vendor tests PASS: OBJ mesh/material output, binary GLB mesh,
measured 5 x 0.2 x 3 m wall bounds, translated world placement, non-geometric
selection failure, nonoverwrite, version drift and preservation of 27 existing
contracts (30 after adding B3). Windows Python 3.11/3.12 CI runs these together
with B1/B2/C1/V2 tests, **62 total per interpreter**.

SOURCE VERIFIED / OFFLINE PASS / BUILD Python. INSTALLED requires the separate
source-only sidecar smoke; LIVE native Archicad NOT RUN; ACCEPTED NO.
No core, main, original PLN/APX or existing running APA process modifications.

## Installed acceptance update — 2026-10-18

The source-only B3 sidecar is installed with its SHA receipt, reusing the tested
B2 vendor environment and extending the verified installed C1 factory. All three
installed operations passed through the original router with actual vendor
subprocesses and independently checked output files. The composed factory exposes
**30 READ_ONLY contracts** (6 V1 + 12 V2 + 3 B1 + 3 B2 + 3 C1 + 3 B3).
The generated input IFC SHA stayed unchanged. No existing session was rebound.
Receipt: B3_INSTALLED_SMOKE_RECEIPT_20261018.json. Reproduce using
`tests/apa_ifc_geometry_installed_smoke_b3.py --output-dir NEW_DIRECTORY`.

SOURCE VERIFIED / OFFLINE PASS / BUILD Python / INSTALLED PASS (opt-in) /
LIVE NOT RUN / ACCEPTED file-sidecar smoke only. Original PLN/APX and native core
remain untouched; geometry serialization is not a native Archicad acceptance.
