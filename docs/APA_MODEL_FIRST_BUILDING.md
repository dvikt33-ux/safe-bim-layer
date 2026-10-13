# Native model-first building through the existing APA executor

The authored intent in `examples/accelerator/model-first-building.json` creates one connected two-story native test model: ten Walls, two Slabs, six Windows, two Doors and one SinglePlane Roof. Dimensions, concrete material and structural roles are explicit TEST parameters, not a designed or code-approved dwelling. Floors bind to actual project elevations 0 and 3 m. The existing project library/CSE and material resolver supply native attribute identities; hosted opening operations depend on their Wall GUID in the existing BIM Graph. No Morph is required.

## Creation and independent acceptance

Use the current installed schema, exact approved project identity and saved-byte hash, persistent SceneWriter SQLite journal and an empty clear placement envelope. The CLI remains `archicad_project_accelerator.py --intent ... --schema ... --output <new-directory> --isolated-port <port> --preflight`, then `--execute --run-id <unique-id> --confirm-plan-hash <returned-hash> --data-dir <existing-ledger>`. An explicitly authorized renamed saved copy is bound through the existing `bind_authorized_saved_copy` interface with path, name and actual SHA256; guessed paths or hashes do not authorize writes. Do not change the ledger or run ID to bypass an unknown outcome.

The opt-in `junctionPolicy` uses outer Wall faces for the Slab footprint and the intermediate Slab underside for lower-wall height: 2.8 m clear walls under a 0.2 m Slab at +3 m. Historical authored intents retain their original geometry. Partitions and Roof are additions to the same authored DAG. Typed Roof readback reuses the existing connected component adapter.

With `nativeRoofJunctions=true`, native BREP establishes the actual lower Roof face. A small measured lower-face/memo offset can be corrected by one owned native translation; no private geometric engine or contour imitation is used. Five upper Walls then receive native SubtractionUpwards links to the Roof. Actual sloped contact areas, native resultant faces and collision queries verify physical contact. A partial or unexpected existing link set blocks automatic replay; a complete verified set is reused without writes and uses persisted pre-SEO contact-area evidence.

Optional `structuralFunctions` refers only to explicit authored Wall/Slab/Roof step IDs. The installed built-in `Category_StructuralFunction` definition must be editable and contain the expected enum. The native Tapir property payload uses its actual localized display value; assigning a test bearing role does not establish load capacity.

If scene creation succeeded but a subsequent read stage failed, inspect the scene, journal and independently read every created GUID first. `archicad_authored_extension.finish_created_model` completes only that verified existing creation set. It never recreates Walls, Slabs or Roofs. Partial native relation outcomes remain blocked for reconciliation.

## Parameter edits

`prepare_building_parameter_edit` diffs the existing authored graph against a new structured intent. Wall height, Window/Door width or height and Roof level compile into explicit owned Modify or Move operations. `execute_model_operation` delegates to the same SceneWriter. GUID ownership, retained model signatures, saved file hash and actual identity are checked around each write; no Create is generated. Add/remove/tool changes, global story edits and unsupported Roof slope/contour edits fail before native mutation.

The live prototype changed Roof level +0.2 m. All five upper Wall resultant caps followed the new native Roof underside through existing SEO while their editable uncut heights remained 4 m. Changing a hosted Window width 1.2 to 1.4 m preserved its GUID and host and changed the host Wall BREP. Existing documentation snapshot/modelVersion functions recorded the new source version. Save/Open preserved all signatures. These are actual source parameter edits, not view settings.

## Verified scope and limitations

Two separately placed 21-element models were used: a first full creation/edit prototype, then the public orchestrator creation and reconciliation-safe completion scenario. The second scenario exposed a missing read-only GetSolidElementLinks router allowance after all 21 creations had already succeeded; the allowance is fixed. Existing created GUIDs were completed without repeating Create. Final model contains 168 main identities; original 126 and the edited prototype's 147 signatures are unchanged. Final completion reuse performs zero native writes; one connected component and no internal or new-to-retained native volume collisions are independently verified after Save/Open.

Native axes remain UNSUPPORTED: installed CreateObjects cannot specify SDK GridElement tool variation. Generic Structural Grid Object library parts are not accepted as native Grid tools. Global story mutation requires a separately authorized project because this shared isolated project also contains retained accepted geometry. SinglePlane Roof contour/slope editing is not qualified by PolyRoof ModifyRoofs. Hosted Door/Window openings are verified; this package adds no GenericOpening, Stair or structural calculation. The source's unverified stair requirement is retained.

`skipPolygonHoles=true` returns false in native SEO metadata: NOT_VERIFIED. This hole-free test's actual contacts are independently verified; roofs with holes are rejected by this completion scenario. Provider-invalid Beam/Column bounding boxes use complete available native body slots with actual segment vertices. Bodyless External elements remain semantically NOT_VERIFIED. Geometry evidence is scoped to available regenerated bodies under existing layer/design-option/3D filters.

A11.S03 remains PARTIAL. A07 dependencies, MEP S10 blocking, existing documentation, normative and Knowledge Graph implementations are retained. The next model task is a supported true native axis contract and story-isolated creation/edit test, followed by qualified geometry/host edits and the unresolved source staircase. No full engineering or normative acceptance is claimed.
