# APA AC29 — reusable native copy execution and historical scene reconciliation

Scope: **finish the architecture of the accelerator, not build BDD house in this pass**. Base is autonomous GitHub bridge PR #139. Never change `main`, stable APA core, existing UI Dispatcher, APX, AC30, or the user's saved PLN.

## Existing components, reused unchanged

- `DynamicCommands.plan_reuse_existing` picks the matching source family using a translation-normalized original native ColumnSegment BREP + material + typed Column profile and story. It does **not** hardcode a source command.
- `DynamicCommands.copy_existing_many` sends exactly one native `MoveElements(copy=true)` call for 1–200 source-qualified repeated Columns. No `CreateColumns` fallback.
- `DynamicCommands.execute` → original `SceneWriter.execute_bound_operation` → existing SQLite ledger records a durable intent before native dispatch; `GetDetailsOfElements` and `GetModelDumpV1` independently verify changed root/child inventory, position, construction attributes and actual copied geometry.
- One original `SaveProject` scene is allowed only after the copy scene reaches PASS, and the working PLN gets an independently observed new SHA. Original source PLN remains guarded.
- Existing live catalog and source review policies apply; unregistered, UNKNOWN or blocked native commands still cannot execute.

## New, bounded glue

**`scripts/apa_ac29_reusable_native_copy.py`** accepts a typed `apa-ac29-native-column-copy/1` task. It contains **no BDD locations or source GUIDs**. It reuses the copy-first selector, original writer and one guarded save and enforces a strict no-overlapping-native-body default. Existing building junctions that need special roof/host validation are deliberately blocked until a source-qualified geometry verifier authorizes them. Other native element families require type-specific readback and are not silently represented as supported.

**`scripts/apa_ac29_scene_reconciliation.py`** reads existing `UNKNOWN_OUTCOME` rows from the original SQLite in **read-only** mode; finds the pre-mutation GUID inventory and native BREP snapshot in the original raw event log; confirms *exact equality* with the **current** read-only live model, including all GUIDs and every physical BREP geometry signature. Only then it returns an external evidence receipt: `PREVIOUS_UNKNOWN_EFFECT_ABSENT_FROM_CURRENT_MODEL_PASS`. It **does not** rewrite `UNKNOWN` to `PASS`, delete history, retry the original scene or assert the earlier command never ran. No raw pre-mutation BREP means FAIL CLOSED.

**`scripts/apa_ac29_autonomous_job_bridge.py`** now recognizes `APPROVED_NATIVE_COLUMN_COPY` in addition to prior READ-only jobs. It fetches a source task pinned to an exact Git commit and blob; requires an explicit per-task `USER_APPROVED_...` reference, exact approved BDD working PLN SHA and current native project/build, and creates one persistent attempted receipt before native execution. For the one known BDD historical UNKNOWN scene, the worker binds its **existing** raw event log, calls the reusable reconciliation gate before writing, and rejects other unresolved scenes. The generic copy module itself does not know BDD, only the current worker's project binding.

## Explicit scope and limits

- General native copy is prepared for verified **standalone Columns only**. A product-wide CREATE/MODIFY router for all 378 catalog contracts is **not claimed**. Roof/Wall/Slab/hosted library elements need existing source-qualified operation-specific verifiers and current native schema registration.
- No generic arbitrary GitHub-provided Python, shell commands, code execution, plugins, journal clearing or overwrite of original files.
- A `USER_APPROVED_` string is **not itself cryptographic proof of user consent**; the agent must not enqueue any write without the user's actual express authorization for its source task and saved project. Exact job blob pinning and runtime guards provide a separate technical bound.
- Unknown results from new attempts are never replayed. Save is not attempted after partial/unknown creation. The entire flow is one approved write job rather than N manual PowerShell commands.
- No live model writing was requested or conducted in this branch. Current installed worker still runs its previous version. A source-pinned upgrade of the **existing** receiver and a real Archicad one-shot write will be required before claiming runtime pass.

## Acceptance

A real user-authorized task must produce one source-qualified copy-first choice, one `MoveElements` native call, root/segment independent BREP PASS, one guarded `SaveProject`, and final GUID/project SHA readback; otherwise stop with `UNKNOWN` and never repeat.

CI runs only focused unit contracts for the **new modules**, no hundreds of repeated offline jobs or regression runs against already verified APA core.
