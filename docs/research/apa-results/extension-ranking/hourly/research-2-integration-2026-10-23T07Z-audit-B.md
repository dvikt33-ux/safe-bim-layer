# Counteraudit B | Dispatcher eligibility and independent persistence | STATIC

B-07Z-01 / 97: SceneWriter.ALLOWED_WRITES excludes CreateBeams. EXTENDED_WRITES permits it only with NativeAdapter. Existing archicad_connected_components.adapters(['beam']) has strict basic-beam checks. But authored run_project only loads adapters(['roof']) if roof present. Thus an added Beam can pass BIM Graph/preflight and then be rejected before CREATE as UNSUPPORTED_WRITE_RECIPE. This is not a LIVE error. Minimum: conditional beam adapter registration within SAME SceneWriter and fail-closed preflight of command dispatch eligibility.

B-07Z-02: historical Tapir 262-command snapshot omits GetModelDumpV1/GetAPARuntimeInfoV1. This does not prove absence in installed APX. Actual APX SHA, registration, multi-database inventory status, and independent BREP are unknown. Bounding boxes != BREP.

B-07Z-03: current BUILD-01 has no new scratch Save/GUI Close/Open or second changed brief. PR74 historical prototype cannot count as new G4/G5. Existing CREATE→MODIFY Slab requires separate exact-scope approval. Sources: SceneWriter 484c600a, compiler 439f6d26, connected adapters c5a99f59, issue #192. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.
