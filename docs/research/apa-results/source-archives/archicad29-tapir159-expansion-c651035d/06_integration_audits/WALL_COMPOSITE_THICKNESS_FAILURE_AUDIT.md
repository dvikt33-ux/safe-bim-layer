# Wall Composite / Thickness Failure Audit

## Problem reconstructed

A request such as “create a wall of thickness X” can be satisfied by fundamentally different Archicad structures:

- Basic wall: Building Material + element thickness.
- Composite wall: Composite attribute + its ordered skins; total thickness is the skin sum.
- Profile wall: Complex Profile geometry.

Selecting a Composite merely because its name/usage appears suitable, then also sending an arbitrary wall `thickness`, mixes two incompatible sources of truth. This can produce the previously observed class of wrong-thickness wall / wrong composite / failed readback.

## Tapir 1.5.9 source findings

1. `CreateWalls` schema requires a `thickness` field.
2. The create path assigns `element.wall.thickness` from that field.
3. `ApplyWallStructure` can subsequently set `modelElemStructureType = API_CompositeStructure` and an exact `compositeId`.
4. Archicad's Composite definition contains its own total thickness from the skin build-up.
5. `GetDetailsOfElements` reports wall `structureType` and exact `compositeId`.

Therefore `thickness` cannot be used as a general-purpose resize knob for a Composite wall. The Composite definition is authoritative for multilayer build-up.

## Correct compiler rule

### Basic wall

Authoritative fields:
- Building Material
- requested thickness
- geometry / vertical contract

Safe BIM may create a Basic wall at the requested thickness after Building Material resolution.

### Composite wall

Authoritative fields:
- exact Composite attribute ID
- exact ordered skins
- exact sum of skin thicknesses

The user's requested total thickness becomes a **constraint** on composite resolution/creation. Safe BIM must not choose the nearest existing Composite by name or visual similarity.

Because Tapir currently requires a `thickness` value in `CreateWalls`, Safe BIM should send a compatibility value equal to the already verified Composite total thickness. It must never send a conflicting arbitrary value and hope Archicad reshapes the Composite.

### Profile wall

Profile geometry is its own structure class and must not be selected as a fallback for Basic/Composite thickness requests without an explicit profile requirement.

## Required preflight for Composite wall

1. Resolve requested ConstructionAssemblySpec.
2. Resolve/create Composite attribute.
3. `GetComposites` by exact attribute ID.
4. Verify ordered skins and material GUIDs.
5. Verify `sum(skin.thickness) == requested_total_thickness` within a defined floating tolerance when a total-thickness constraint exists.
6. Verify `useWith` contains `Wall`.
7. Only then prepare `CreateWalls` with `structureType=Composite`, exact `compositeId`, and compatibility `thickness=verified_total_thickness`.

## Required readback

The wall write is not DONE until:
- receipt GUID exists;
- exact GUID `GetDetailsOfElements` says Wall;
- `structureType == Composite`;
- `compositeId` equals the verified attribute receipt;
- normal wall geometry/Z fields match;
- the Composite is re-read (or a verified cached receipt is used) and its exact fingerprint is still the intended one.

Element geometry alone never establishes ownership.

## Selection policy

Default `EXACT_ONLY`:
- exact fingerprint → reuse;
- same human name but different definition → do not reuse;
- same total thickness but different layers → do not reuse;
- closest thickness → do not reuse;
- fuzzy material/name match → do not reuse unless user confirms alias/approximation.

## Regression tests to add later

- Basic 250 mm request produces Basic 250 mm.
- Composite 250 mm request resolves only an exact 250 mm skin sum.
- Existing Composite 300 mm with similar name must not satisfy 250 mm request.
- Existing Composite same total thickness but different skin order/materials must not match.
- Tapir payload for Composite contains compatibility thickness equal to verified Composite total.
- Readback returning a different compositeId fails.
- Changing a foreign existing Composite is impossible under default policy.

## Verdict

The old failure class is preventable without asking Archicad to resize a Composite element. The fix belongs primarily in Safe BIM planning/resolution/verification, while Tapir's mandatory wall `thickness` field can be handled as a compatibility field until a future schema cleanup is separately audited.
