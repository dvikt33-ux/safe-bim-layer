# Native construction junctions after PR56

A04.S01 joins the accepted native model to73context Details and1142source
details without reconstructing any accepted element. All95GUID/body signatures
are pinned. The existing Native Model Dump, NetworkX and Shapely face-contact
analyzer remain the geometry authority; no second geometry engine or writer.

Coverage includes wall/floor, wall/window/door, upper-wall/roof (including real
gaps), roof members/abutments, cladding/structure, wall ties/intersections and
column/floor. Each actual candidate retains GUID, absolute XYZ body bounds,
floor, material bindings, source/detail/page and source compile blockers.
Missing cladding, reinforcement and fastener schedules remain explicit gaps.

Physical shared-face area is distinct from a logical host binding, native
volume collision and structural capacity. Inner BREP contours remain holes.
Unsupported body contact analysis stays NOT_VERIFIED. No full manufacturer
assembly is source-approved. Research normative references are candidates;
their applicability and engineering verification are not inferred.

The next concrete source-supported sub-junction is the existing25x150mm ARMO
batten supported by a new50x50mm counterbatten, following the measured roof
inclination. Source ARMO_SELFLOCK_ROOF__P0003, page3, facts PF001/PF002 and the
explicit battens_supported_by_counterbattens relation. Preserve the existing
batten, derive the new member's placement/span from actual native geometry,
reuse the existing structural-timber Building Material and SceneWriter, then
prove physical contact and absence of new native intersections. This is a
bounded support sub-junction; roof sheets, fixings, loads and the complete
manufacturer assembly remain unverified.

Tests cover true area contact, edge-only contact, overlap, polygon holes,
nonplanar limitations, untrimmed roof gaps, missing cladding and source gates.
