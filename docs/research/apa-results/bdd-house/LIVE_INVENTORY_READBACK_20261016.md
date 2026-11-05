# BDD house: confirmed live readback, 16 October 2026

**Evidence stage: LIVE_READ_PASS.** The earlier collector implementation stage `NOT_LIVE_TESTED` is now superseded for this run by the user's independent native Archicad console output and a matching authenticated private GitHub readback.

## Primary evidence
- Private GitHub result: https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/safe-bim-mailbox/gpt-live/results/apa-bdd-inventory-20261016T125933Z-40642102.json
- Capture (UTC): `20261016T125933Z`
- Engine: Archicad **29**, build **5101**, Tapir **1.5.10**.
- Matched endpoint: `archicad-19727`; exact saved project name `BDD дом ` (trailing space). Do not use automatic default-port routing.
- Result: `PASS`, `readOnly=true`, `mutationApplied=false`, warnings `[]`.
- Total elements `21`; details found `21/21`; 3D bounding boxes found `21/21`.
- All 21 reported elements are assigned to story index 0, level 0. Further empty stories exist at +3 m and +6 m.

## Native model inventory
| Type | Count | Native evidence |
| --- | ---: | --- |
| Object | 16 | All 16 bounding boxes have zMin=zMax=0; their geometry is flat in this readback. Some of these objects lie around the façade-marker rectangle; exact library-part roles are not proven by this report. |
| Elevation | 4 | Four elevation-view markers, flat bounding boxes. |
| Wall | 1 | GUID `744A9A2E-985A-434F-B6EA-851A42E6075B`, ID `ПЕР - 001`. Composite straight wall, height 3 m, 0.3 m thickness, story index 0, approx. 6.75 m diagonal baseline; located outside the perimeter formed by façade markers. |
| Slab | 0 | No native slab in inventory. |
| Roof | 0 | No native roof in inventory. |
| Window | 0 | No native window in inventory. |
| Door | 0 | No native door in inventory. |

**Conclusion:** This PLN is not yet a modeled house. The lone wall is geometrically isolated; its being a test wall is a plausible interpretation, but its purpose is **not proven**. Do not delete it automatically. The 16 flat objects should not be equated with building solids.

## Design-source data (structural PDF; not a native PLN readback)

The 2022 structural drawing set supplied for the house has:
- overall area marked 115.14 m² and one storey with cold attic;
- first-floor datum ±0.000, clear height 3.0 m, plinth 0.60 m, ridge +6.295 m relative to finish floor;
- structural axes X `0, 5.34, 6.77, 8.70, 14.28` m, Y `0, 1.09, 9.38` m, as transcribed from detailed structural sheets;
- note: general data gives 14.18 × 9.28 m axes while repeatedly-dimensioned structural sheets give 14.28 × 9.38 m. Treat **unresolved**, do not silently choose;
- bored-pile and grillage foundations, timber-frame walls, pitched roof and pergola terrace require verified detailed geometry.

These source-derived measurements are **not** contained in the native inventory and should never be presented as already constructed.

## Construction next steps

1. Preserve a read-only baseline and original PLN. Confirm model and attribute ownership before any writes. No deletion or blind cleanup of the 21 existing GUIDs.
2. Use structural drawings to resolve plan datum, footprint, wall runs, internal layout, opening coordinates, roof pitches and overhangs. Resolve the 100 mm axes mismatch against the dimension chains.
3. Create a **separate, explicitly authorized building writer**, with exact PLN allowlist and explicit port 19727 (or a verified copy); per-stage readback, GUID journal, conflict detection, single-writer serialization and no unrequested saving.
4. Assemble structural BIM in stages: (a) native story/grid/reference geometry where supported, (b) wall assemblies and partitions, (c) floor and support structures, (d) windows/doors, (e) roof system, (f) terrace/pergola/foundations, (g) materials.
5. Verify against structural drawings by coordinate and GUID, not by quantity-only smoke tests. Confirm visual fidelity and no unwanted edits to the reference/markers.

## Transport caveats
- The local `sync_bridge` remains read-only. A **local-only** scope quarantine patch has been applied; it is not persisted in that historical checkout.
- The old bootstrap resets that checkout to commit `7469b77` and would remove the patch. Do not rerun it until the fix is promoted and tested in a safe branch.
- No architecture house-writing command has been executed by this inventory pass.
