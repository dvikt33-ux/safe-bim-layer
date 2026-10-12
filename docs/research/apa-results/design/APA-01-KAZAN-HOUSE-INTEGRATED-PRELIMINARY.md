# APA-01 — Kazan two-storey house: integrated preliminary design package
Date: 2026-10-12. Status: PRELIMINARY / NOT STRUCTURALLY APPROVED. This is not a construction-ready structural design, nor an actual PLN.

## 0. Scope and user decisions
Kazan, Tatarstan. Two full floors. Approximate external envelope 10 x 12 m, subject to masonry and precast modular coordination. Three levels of floor structures: ground-over-foundation precast RC; between floors timber joists with acoustic infill and decking; above second floor precast RC. Warm 35-degree gable roof, insulated along slopes; NO cold attic. Covered terrace off kitchen-living room and covered entrance porch. First floor: kitchen-living room, pantry adjacent to kitchen, wardrobe, bathroom, laundry, boiler room, entrance/hall/stair. Second floor: three bedrooms, bathroom, hall/stair. Warm ceramic structural masonry, self-supporting face brick veneer, proposed no ventilated cavity subject to full system and hygrothermal approval. Native Archicad Beam for joists and rafters; Slab for sheathing/decking; Morph only if demonstrably unavoidable. Precast slabs are one-way and bear on ONLY TWO OPPOSITE SHORT ENDS. No unverified bearing on longitudinal edges. All major elements must remain individually editable and persist after PLN save/reopen.

## 1. Corrected coordinate framework (do not confuse with previous incorrect sketch)
X runs across 10m width, Y along 12m length. Provisional wall axes: X=0, 5000, 10000 mm (two ~5m bays); Y=0, 12000 mm. The central longitudinal bearing wall is at X=5000 and runs in Y. X=0 and 10000 are provisional WALL AXES, NOT confirmed external-face coordinates. Therefore actual outside dimensions and clear spans will differ. Central loadbearing wall needs a continuous load path through both floors to foundations. Stair opening must not cut the support line. A complete Y-axis transverse bracing/return-wall scheme and lateral stability calculation remain required.

## 2. Masonry coordination and preliminary arithmetic
Candidate ceramic unit Porotherm 38 Thermo 380 x 250 x 219 mm (verify product technical datasheet, orientation, mortar/vertical joint requirements, actual availability). Thickness 380mm is NOT yet verified for Kazan thermal, structural or acoustic performance. Candidate face brick 250 x 120 x 65mm (actual purchased SKU must be verified).
- Ceramic horizontal course with a **hypothetical** 12mm bed joint: 219+12=231mm. 12 courses -> 2772mm; 13 -> 3003mm. Actual course dimension must use approved mortar system; thin-bed system may require much thinner joint. These are alternative examples, not a selected mortar specification.
- Facing brick course with hypothetical 10mm bed joint: 65+10=75mm; 4 courses -> 300mm. Ceramic 231mm and brick 75mm courses do NOT automatically align. Ties must be detailed for actual coursing and movement.
- Facing brick running bond with 10mm vertical joints -> 250+10=260mm module; 12000/260=46.1538, 10000/260=38.4615. Thus neither 10m nor 12m is an exact brick module; openings/corners/dobors need a full bond layout, not rounding.
- Ceramic 250mm length + hypothetical 10mm head joint -> 260mm only if the manufacturer-approved vertical joint actually uses mortar. Tongue-and-groove products may have dry vertical joints. Never force a 260mm module without approval.
- Face brick veneer is SELF-SUPPORTING, not gravity loadbearing for floors or roof. It needs independently verified support, ties, differential movement, lintels, thermal bridges and moisture detailing. No air cavity does not prove composite structural action.
- Interior insulation is not approved: first check whether single-leaf ceramic plus facing achieves Kazan heat resistance, then assess moisture/condensation/freeze-thaw; if insulation is required, compare safe alternative positions and vapor-control strategy. Obtain climatic design values and normative calculation per current applicable SP 50.13330, SP 131.13330 and masonry SP 15.13330 (verify amendments). Do not substitute rules of thumb for hygrothermal calculation.

## 3. One-way precast slabs: dimensional logic, NOT a final product schedule
Use a manufacturer-confirmed type such as 1PK / PB designed for two-end support. Nominal width candidates 1000, 1200, 1500mm; actual manufacturing widths, length increments, permissible holes, ratings and bearing depths are product-specific. Do not assume every nominal combination is stocked.
Let A = distance between axes of supports; t1,t2 = supporting wall thicknesses; clear span = A - t1/2 - t2/2 (for centered wall axes). If exterior ceramic t1=380mm and central support t2=250mm (illustrative ONLY), A=5000mm => clear span = 5000-190-125=4685mm. With illustrative bearing 120mm each end, physical slab length needed ~4685+240=4925mm, BEFORE tolerance, end detailing and manufacturer rules. A 5.0m catalogue slab cannot be selected simply because axes are 5.0m; verify actual dimensions, bearing requirements, allowable deflection and load.
Slab span runs X, slab longitudinal axis X. Bearing only on end strips at exterior X walls and central X wall. Longitudinal sides (parallel to X) are non-bearing, with specified joints. Slabs array along Y; for 12000mm coordinate length, 10 strips x 1200mm is only an initial width arithmetic illustration; actual joint widths, walls, tolerances and stair openings make a detailed layout mandatory.
Ground-level slab: design for floor dead load, imposed occupancy loads, partition and local loads; support/foundation interaction, basement/crawlspace ventilation and rodent sealing. Upper slab: design for slab self weight, imposed maintenance/storage load as appropriate, roof-support point loads and load paths. Concentrated roof post loads on hollow-core slab are NOT accepted without designed distribution beams/walls and engineer check. Precast slabs do not automatically create a sealed rodent barrier: joints and penetrations must be sealed and detailing coordinated.
DO NOT fabricate slab mark, permissible loading, bearing length, mass, or supplier. Actual schedule requires manufacturer catalogue, certified dimensions and loads.

## 4. Timber intermediate floor: native BIM and checks
Joists span transversely X between exterior and central walls (~4.7m clear illustrative). Use Archicad native Beam, unique GUID each; include bearing/anchors, fire separation, moisture protection and acoustic detailing. Preliminary step to investigate 400 or 600mm on-center, NOT approved. Each beam section requires verified grade/species, service class, dead/live loads, bending/shear/deflection/vibration, bearing compression and fire resistance. The previous suggestion of arbitrary timber sections is prohibited. Decking modeled as native Slab layers or Composite where supported; acoustic mineral wool infill modeled as layered construction / native elements where feasible. No Morph joists. Perimeter and stair opening need doubled joists/header beams and verified supports; avoid inventing unsupported spans.

## 5. Warm gable roof and real load path
Roof ridge parallel to Y. Pitch 35deg. For 5000mm half-run without overhang: rise=5000*tan35°=3501mm; slope length=5000/cos35°=6104mm. Eave extension changes actual length and uplift. Roof structural solution remains UNSELECTED until supports are confirmed. Options:
A) Engineered ridge beam supported by continuous loadbearing walls/posts with verified transfer to foundation (not arbitrary hollow-core slabs).
B) Designed paired rafters with structural ties at correct level and verified outward thrust and lateral support, as applicable.
Do NOT depict decorative struts that stop short of bearing surfaces. Every rafter, purlin, post, brace and tie must connect to a physically valid supporting element with detailed bearing/fasteners and load path. Native Beam for timber members, Roof for covering layers, Slab where applicable. Insulated sloped roof includes warm-side airtight vapor control, insulation thickness determined thermally, diffusion-open underlay if suitable, ventilated counterbatten channel above underlay, battens and roofing; roof/terrace junctions need separate drainage and waterproofing.
Roof snow/wind load zones and coefficients MUST be checked against current SP 20.13330 with location, height, exposure, geometry, drift and shape factors. Do not assume a snow region or nominal characteristic value without sourced verification. Timber check SP 64.13330. Upper RC slab must not be used as an unchecked bearing support for roof columns.

## 6. Architectural room zoning (not measured plan)
Floor 1: entrance porch -> vestibule -> hall/stair; wardrobe by entry; bathroom, laundry and boiler grouped on services side; pantry directly off kitchen; kitchen-living room faces covered terrace with separate egress. Boiler room dimensions, glazing, ventilation, chimney and gas safety depend on actual heating equipment/fuel and applicable codes. Terrace support and roof independent or engineered tied to house; thermal movement, snow accumulation at junction and water discharge must be checked.
Floor 2: 3 bedrooms, bathroom aligned above first-floor wet area, landing and circulation. No exact room areas or window openings until structural grid and stair geometry are reconciled. Structural wall openings require engineered lintels; avoid placing door/window directly across precast slab bearing zones.

## 7. Required calculations / approval gates before construction claims
1. Site survey, geotechnics, groundwater, frost heave and foundation design.
2. Climatic data, envelope U/R, surface condensation and seasonal moisture assessment for full wall/roof assembly.
3. Masonry capacity/stability, bond and veneer anchors, lintels, RC ring beam and differential deformation.
4. Load takeoff, actual two-end supported precast slab manufacturer's series/marks and span tables, layout including stair opening, transport/crane logistics.
5. Timber joist sections, grade, vibration, fire/acoustics and connection details.
6. Rafter scheme with complete force path, snow/wind, member stability, fasteners, uplift, roof bracing, terrace/porch roofs.
7. MEP coordination, penetrations, ventilation, boiler room requirements, sanitary stack alignment.
8. Independent engineer review of any buildable structural design.

## 8. APA execution manifest — staged native-only
Phase 0: isolated PLN and active-document identity check, version/capability discovery; no changes to user's unrelated PLN. Capture baseline GUIDs and snapshot.
Phase 1: native Story levels, grids (if supported), walls with proper homeStory, materials; verify wall axes and thickness.
Phase 2: native Slab instances for EACH individual precast unit, no monolithic false slab. Maintain manufacturer mark metadata; end-bearing orientation, no side bearing, independent GUID, edge/joint and opening audit.
Phase 3: native Beam joists and headers, native Slab decking; optional native Composite layers; no Morph. Validate clearances and element-to-support geometry.
Phase 4: Roof surfaces + native Beam rafters, ridge/purlins/ties/posts/braces as designed, with actual physical bearing connections. Terrace and porch roof separately.
Phase 5: native doors/windows, stair if supported; rooms/zones if supported; finish and layers. If unsupported, mark BLOCKED rather than fake a Morph or claim full completion.
Phase 6: native geometry/material/story dump; all GUID and floor levels; 3D collision/contact checks (XY overlap alone not collision); IFC optional crosscheck; save, close, reopen PLN, independent reread and compare GUID/geometry/materials. Capture artifacts and publish results.
Acceptance: 0 fabricated slab marks, 0 unintended side supports, 0 Morph intermediate joists, 0 unsupported roof-bearing joints, no missing original GUID after reopen, no invented engineer approval.
Status: NOT EXECUTED in live Archicad. This document is a design and implementation specification only.

## 9. Explicit blockers
Actual geotechnical conditions; approved local climate load calculation; precise manufacturer data for block, mortar, veneer, slabs and timber; bearing walls thickness and ring beams; foundation and lateral bracing; stairs and openings; verified APA capability on current installed Archicad. These prevent truthful structural PASS and finished native PLN today. No local Archicad runtime available from this chat.
