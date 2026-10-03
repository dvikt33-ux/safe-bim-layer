# Archicad Capability Roadmap

This roadmap expands Safe BIM functionality one verified capability at a time. Do not skip a failed gate.

## 1. Native hosted Windows and Doors — VERIFIED

Goal: continuous Wall + native/library Window/Door, no facade fragmentation.

Acceptance:
- one continuous host Wall;
- Window/Door creation PASS;
- host GUID read-back/connection confirmed;
- width/height/sill/offset exercised in live Archicad;
- duplicate/fragment count zero in isolated smoke region;
- Morph fallback zero.

Canonical smoke: `tests/smoke/native_window_door_continuous_wall.py`.

Live verification evidence (2026-10-03):
- Wall `FA9434E5-53CE-4FE6-BD43-9B9FDD14679B`;
- Window `D5C35B66-2814-43D7-A29D-4F615F76FAAC`;
- Door `8B0EBA3D-DF24-46FE-B772-160E23027044`;
- test-region Wall count remained `1`;
- `Window` and `Door` read-back types passed;
- Morph count `0`;
- wall fragmentation `0`.

## 2. Slabs

Goal: reliable basic slab creation using only supported `CreateSlabs` fields.

Acceptance:
- outline correct;
- level/thickness/reference plane read back correctly;
- no unsupported `buildingMaterialId` in create payload;
- separate tested path for material/structure change if required;
- isolated smoke leaves exactly one expected Slab and no unrelated writes.

## 3. Simple gable roof

Goal: one clean two-plane roof over a rectangular test building.

Acceptance:
- two roof planes meet at one ridge;
- no gap/overlap at ridge;
- eaves and overhang correct;
- pitch and elevations read back correctly.

## 4. Wall-to-roof trim

Goal: one full gable-end Wall trimmed to the validated roof, without wall fragmentation.

Acceptance:
- source Wall remains one Wall;
- final top contour follows roof;
- wall does not protrude through roof;
- no stepped Wall approximation;
- read-back/visual evidence stored.

## 5. Rafter family from validated roof

Goal: generate rafters from roof geometry.

Acceptance:
- rafters are native Beams;
- real pitch matches roof;
- lower ends meet wall plate/eave line;
- upper ends meet ridge;
- no members penetrate outside the roof envelope unintentionally.

## 6. Complex roof intersections

Goal: cross-gable / valley / hip relationships without holes or crude overlap.

Acceptance:
- roof intersection closes geometrically;
- valleys/ridges are located correctly;
- no visible holes;
- trim relationships are stable;
- rafter generation waits until roof passes.

## 7. Porch

Goal: reusable porch system using verified SEO/Profile-Beam capabilities.

Acceptance:
- three-sided step logic as required;
- canonical smooth decorative cutter profile;
- clean corner behavior (native 90-degree Beam cleanup and curved Beam where needed);
- top finish separated from structural body when required;
- no duplicate cutters/operators.

## 8. Integrated English house

Goal: combine only previously VERIFIED capabilities.

Acceptance:
- no new modeling method is invented inside the integration script;
- walls stay continuous;
- windows/doors are native/library parts;
- slabs, roofs, trims, rafters and porch are all produced through their already-tested modules;
- final automated audit passes before visual sign-off.

## Current next step

Proceed to **2. Slabs**. Build one isolated basic Slab using only fields proven by the current `CreateSlabs` schema, then read back outline, level, thickness and reference plane. Do not add roof or other systems until the slab gate is VERIFIED.
