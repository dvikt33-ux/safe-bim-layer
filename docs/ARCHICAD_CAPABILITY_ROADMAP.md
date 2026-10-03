# Archicad Capability Roadmap

This roadmap expands Safe BIM functionality one verified capability at a time. Do not skip a failed gate.

## 1. Native hosted Windows and Doors

Goal: continuous Wall + native/library Window/Door, no facade fragmentation.

Acceptance:
- one continuous host Wall;
- Window/Door creation PASS;
- host GUID read-back/connection confirmed;
- width/height/sill/offset confirmed;
- custom library part identity confirmed where used;
- duplicate count zero;
- transparent glass visually confirmed for window test.

## 2. Slabs

Goal: reliable basic slab creation using only supported `CreateSlabs` fields.

Acceptance:
- outline correct;
- level/thickness/reference plane read back correctly;
- no unsupported `buildingMaterialId` in create payload;
- separate tested path for material/structure change if required.

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

Start at **1. Native hosted Windows and Doors**. The existing custom Door path and transparent GSM glass path are already verified; the remaining task is to freeze a canonical Window smoke test on one continuous host Wall and save the test in the repository.
