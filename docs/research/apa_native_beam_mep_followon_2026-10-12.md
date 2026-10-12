# APA native Beam / reference200 MEP follow-on

Base: exact PR57 head `b1abd584585feb0f286621337986c8a5d3077507`.
The published A04.S01–S03 remain accepted; this package continues A11.S03.

## Working native functions

* `circular_reference_selection` reads the installed Ventilation table and pins
  the unique reference200 / diameter0.2m row. SceneWriter rechecks the table
  and route-local selector before one Create. Global preferences are unchanged.
  The new circular lead has actual0.2m ports and automatically connects at the
  exact terminal port. Reciprocal physical readback confirms this connection.
  The terminal pair remains separate from the original rectangular network:
  no circular/rectangular transition or whole-network completion is claimed.
* `prepare_native_batten` and `prepare_native_counterbatten` use existing
  Details source joins, measured roof/support bodies and explicit materials.
  They select real `CreateBeams` through the existing SceneWriter. Both Morph
  and actual SDK-owned Beam segments can supply the measured batten geometry.
  Parent GUID, BeamSegment ownership, story, section and material are read back.
* A separate actual25×150mm Beam and actual50×50mm Beam form a native support
  contact of75cm². The original accepted Morph junction remains intact.
  The new50×50mm Beam also contacts the original batten over73.1108100945cm².
  Its native vertical end cut differs from the Morph perpendicular cut; the
  source section is preserved, but identical end geometry is not claimed.
* Beam cross-section rotation uses Archicad's opposite angle convention to the
  retained Morph matrix. Readback accepts equivalent angles modulo2pi.
  One confirmed profile edit corrected the new Beam. No Create/Modify replay
  occurred; the temporarily joined new counterbatten body was restored exactly.
* A separate Wall/Roof specimen uses measured wall span/thickness, native roof
  polygon/pitch/material and the existing TrimElements contract. Actual native
  trimming and material joining produce a perimeter abutment through the roof
  layer: shared surface3.236340608m² and no resultant volume collision.
  This is not underside bearing. The four original upper-wall/roof gaps remain.
* GetElementTrims returns the roof's actual trimmed-wall identity. The installed
  provider discards the target Wall row when GetTrimmedElements is inapplicable.
  That reverse metadata remains explicitly unverified. An accepted new SEO
  SubtractionUpwards link produced no incremental body change with the joined
  roof cutout; it does not qualify underside bearing.

## Shared contracts and exchange

The same BIM Graph, source-bound SceneWriter, Details, Shapely face analysis,
native dump and dedicated MEP readers are retained. Actual BeamSegment bodies
feed shared context, junction coverage and IFC quantity comparisons through
their SDK host GUIDs. An auto-connected terminal keeps its existing context
identity instead of gaining a duplicate GUID entry.

Actual local IFC has50elements,43/43native world-bound matches,
18quantity matches/0mismatch,12port relations and6opening hosts.
Both new native Beams export as IfcBeam with structural timber material and
matching actual BREP quantities. The accepted classified Morph counterbatten
also exports as IfcBeam; its native tool remains Morph. The original unclassified
Morph batten exports as IfcBuildingElementProxy. Classification is not tool proof.
Native trim/SEO or structural connection semantics are not inferred from bounds.
Complete receiver compatibility and engineering approval remain unverified.

## Persistent native state and limits

The isolated model now contains107GUID and43shared records. All96previous
GUID/body/material/story signatures are unchanged. New typed elements and
contacts survived Save/Open; final independent readback found no new native
collision. The known diagnostic roof/Morph collision is retained.
Final PLN SHA256: `47366e08ecdc7cd5340480c7e0bd455e8ab0aaea64b1321085d9fdbad1a2591c`.

The23new unit checks cover reference ambiguity/drift, native Beam selection,
hierarchy, typed section defaults, shared identities, actual-owned quantities,
contact attribution and partial trim metadata. Full Windows host suite passes
455tests; published Windows/Linux CI is recorded with the evidence package.

A11.S03 stays PARTIAL. A11.S10 stays BLOCKED for a sized native transition and
baseline-preserving bridge to the rectangular network. ConnectLogically can
delete or split a target routing GUID, so it was not applied to retained routes.
Manufacturer grade/fixings, eight assembly dimensions and load-bearing capacity
remain unverified. A11.S04 optimization is not started ahead of those criteria.

## Permanent native-first rule

Use the appropriate native parametric BIM tool before considering Morph.
An absent APA adapter is not a reason to select Morph. New Morph creation and
geometry edits require documented native contract/geometry limitations and
preservation of mandatory BIM properties and relations. Source c4/c5 rectangular
members are refused as Morph and routed to the real Beam adapter.
This rule is also published in the canonical operating instruction and plan.

Next: qualify a ready circular/rectangular transition contract without global
preference changes or retained-GUID deletion; independently address the measured
roof underside-bearing gap using supported native geometry and verified sources.
