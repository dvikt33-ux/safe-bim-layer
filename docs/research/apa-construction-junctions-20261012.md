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

## Source-bound native support junction

The new counterbatten uses PF00250x50mm, follows the measured roof/batten slope
and physically supports the unchanged PF00125x150mm batten. Its5.9801000489m
length comes from the actual batten underside edge and upper-wall inner face.
The native result has0.007500000016m2shared surface contact, no new native body
collision, home story1and the accepted structural-timber Building Material.
All95old GUID/body signatures remain unchanged; the model now has96GUID and
38shared-context records. Only the new element receives the existing native
Archicad2.0Beam classification; its editable tool remains Morph. Classification
systems, defaults, original elements and the installed APX are unchanged.

Source, roof, batten and endpoint-wall geometry/material/story pins invalidate
the graph before another write if dependencies drift. Exact source dimensions,
right-handed native placement-matrix rows and contact area are tested. Native
classification readback accepts only the catalog's exact wrapper and the
installed provider's exact direct ClassificationId row. The observed wrapper
discrepancy was reconciled through read-only facts without replaying the setter.

This completes the bounded batten/counterbatten support sub-junction. Fixings,
timber grade, rafter support capacity, complete roof assembly and engineering
remain NOT_VERIFIED; another family's completion is not inferred.

## Independent qualification after persistence

The isolated model was saved and reopened successfully; all96body signatures,
classification, timber material, story and75cm2contact match independent native
readback. The first Open response timed out; a second controlled Open occurred
only after exact saved/current state reconciliation. No geometry or classifier
mutation was replayed.

The reusable qualifier grades49actual model interface pairs:34PASS_GEOMETRY,
one PASS_DOCUMENTED bounded source support,14NOT_VERIFIED and zero
PASS_ENGINEERING. The49include the original47interfaces plus two candidates
introduced by the new counterbatten. Source support proof must match the exact
pair and measured area; missing/duplicate/stale proofs and volume intersections
cannot be promoted. Generic Opening host holes are independently checked.
Cladding is absent and four upper-wall/roof interfaces retain real gaps.
Each family remains NOT_VERIFIED as a complete construction assembly.

## Separate MEP preference qualification

Read-only live inspection found an existing Ventilation preference row:
referenceId200, diameter0.2m. The installed CreateMEPRoutingElements contract
already exposes crossSectionReferenceId, and retained native source applies it
to a local segment default before placing a new route. User preference tables
and global defaults need not be changed. The earlier gap statement that all
route contracts lacked this selector was incomplete.

ModifyMEPRoutingElements exposes no reference selector in either the actual
schema or source; the donor example's broader claim cannot be used as proof.
No explicit transition or terminal port-size setter was qualified. The existing
terminal remains unconnected. Reference-based route creation and a reciprocal
terminal connection require a separate unambiguous native probe; no MEP write
was repeated during this qualification. S10 remains BLOCKED for the actual
transition/connection criterion.
