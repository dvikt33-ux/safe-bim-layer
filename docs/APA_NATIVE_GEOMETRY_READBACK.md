# Native geometry on the existing authored readback

An authored intent may set `nativeGeometryAudit: true`. After the existing
SceneWriter completes typed whole-assembly readback, the same Project
Accelerator invokes `archicad_authored_geometry.run`. Existing intents keep their
current behavior. Install `scripts/requirements-geometry.txt` when enabling this
option. No second graph executor, writer, dump format or boolean engine is added.

The adapter reuses the retained Model Dump V1 normalizer and strict topology
verifier. It checks exact project identity and inventory before and after reads,
and verifies every primary GUID/type/story through the existing typed readback.
Column bodies are attributed to the parent only through explicitly confirmed
ColumnSegment ownership. Native XYZ bounds, building material GUIDs and declared
XY envelopes are checked for the accepted walls/slabs/rectangular columns;
opening host identity uses the native relationship. GDL frame bounds do not
replace nominal opening dimensions verified by typed readback.

Tapir `GetCollisions` tests disjoint groups, once per unordered primary pair,
with and without surface checking. Shapely XY/AABB intersections remain
candidates. A separate contact table intersects actual coplanar native BREP
face contours, retaining holes. NetworkX relates these contacts and native
host/collision evidence to the retained primary GUIDs. Contact is distinct from
body penetration and structural load transfer. Invalid or nonplanar face
polygons block this bounded adapter. Coordinates are absolute project meters;
its plane/contact tolerances are geometric tolerances, not normative criteria.

On Archicad 29 build5101 RUS / installed Tapir1.5.10, the accepted isolated
17-element example produced 39 retained GUIDs, 56 bodies, 788 vertices, 524 faces
and 12 hole contours. Two parent columns had no direct bodies: their explicitly
owned native segments supplied geometry. All 17 primary elements passed bounds,
material, story and host checks. Native collision queries returned no volume or
surface-check pairs; a positive collision calibration is not claimed. Native
face contours established 34 contact pairs and a connected primary graph.
Forty XY overlaps without volume collision were classified separately. The
audit issued zero model writes and preserved the full 39-GUID inventory.

Seven synthetic tests cover the historical upper-slab elevation error, missing
geometry, wrong segment ownership, wrong material identity, stacked slabs,
parent/segment coverage and coplanar contact with a hole. Synthetic negatives
remain distinct from captured live readback. Visible UI, general curved/complex
geometry, roof/shell/SEO integration, arbitrary GDL envelopes, joint quality,
normative compliance, structural adequacy and Archicad30 remain unverified.
The dump retains the active 3D view's visibility filters; acceptance is scoped
to its explicitly checked element coverage.

Reuse sources: published `ART-APA-REUSE-NATIVE-20261011`, `ART-SDK-GET3D` and
`ART-SDK-SEO` in the canonical APA plan. The installed schema export contains
263 commands; the adapter uses the existing supported read path needed here.
