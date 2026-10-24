# Counteraudit A | Provider schema vs post-CREATE writer assumptions | STATIC

A-07Z-01 / 99: Tapir CreateDoors/CreateWindows require only ownerWallId and centerOffset. width, height, sillHeight are optional in pinned schema. BIM Graph validates provider schema and skips fit/overlap checks where width is missing. SceneWriter.verify_readback indexes expected['width'], ['height'], ['sillHeight'], ['centerOffset'] after native CREATE. Therefore an additional schema-valid incomplete opening can reach CREATE then fail readback with KeyError. CONDITIONAL source path, not observed LIVE.

A-07Z-02 / 98: Tapir CreateSlabs requires level/polygonCoordinates; floorIndex/thickness optional. SceneWriter indexes both after CREATE, including slab material MODIFY. Tapir CreateColumns requires coordinates only, while SceneWriter readback indexes height/width/depth and floorIndex. Existing base authored slabs explicitly set fields; exposure concerns added nativeComponents. compile_authored_intent does not perform equivalent story/envelope checks for added Beams/Slabs.

Minimum correction: fail-closed field/host/story/geometry checks in EXISTING compiler preflight; OFFLINE negative cases before any WRITE. Sources: Tapir blob e8ad53b6; compiler 439f6d26; graph 87fc7476; SceneWriter 484c600a. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.
