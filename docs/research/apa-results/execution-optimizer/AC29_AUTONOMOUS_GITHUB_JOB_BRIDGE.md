# APA AC29 — autonomous GitHub job bridge (minimum integrated executor)

## Actual boundary

This is an additive **one-time-installed local receiver**. It does NOT rewrite or repoint:
- the original GPT/Arena AI Dispatcher 2.2.19 or its signal.json, target schema, mutex or control chat;
- the existing `Test MER` dry-run watcher;
- the verified stable `C:\LocalAI\APA_AC29_Stable\scripts` APA core, DynamicCommands, SceneWriter or native add-on;
- the protected BDD House original or working PLN; or `safe-bim-layer/main`.

The user runs a **single installer once**. This stores the receiver in `C:\LocalAI\APA_AC29_Stable\controllers`, launches one background poller, and creates a **current-user Windows Startup entry**. The receive channel is `safe-bim-bridge/main/safe-bim-mailbox/apa-ac29/jobs`. The return channel is `.../results`. The receiver writes a unique durable `attempted.json` before any native operation; interrupted jobs are **never replayed automatically**. A stored result can be republished on network recovery without re-executing. The user may disable it by removing `APA-AC29-GPT-Bridge.vbs` from their current-user Windows Startup folder and stopping the worker process. No admin/service registration required.

## Current supported job actions

**BDD114_ROOF_FINALIZE:** automatically invokes the existing, pinned BDD production preflight using the verified APA native BREP and authored-geometry methods. It checks roof-face clearance and the accepted north-wall junction. Executes no Create/Modify/Save; publishes both original evidence and unique job result. This is the next outstanding work on the house (after 7 candidates AABB overlap), not a repeat of completed function tests.

**SOURCE_QUALIFIED_NATIVE_READ:** accepts only a task whose source is pinned to an exact GitHub commit and blob SHA, whose `apa-capability-task/1` steps are all `READ_ONLY` and have source verification. The job obtains the current AC29 live schema, calls `prepare_current_runtime_catalog_task`, then `APA.run_auto_optimized_native_task` on the very same router/API with `EvidenceAPI(execute=False)` and `SceneWriter` via the original workflow. Selected commands are called automatically; no user PowerShell per operation. Source and saved model hashes/inventory are verified.

**Explicitly not enabled:** general autonomous WRITE/CREATE/MODIFY. Native write without reviewed per-step scopes, expected live effects, source dimensions and user authorization would bypass existing SceneWriter. A later bounded adapter must use existing `DynamicCommands.execute_batch`/`copy_existing_many` on a unique source-verified scene and the original journal, after actual roof/junction clearance and user approval of calibrated X. No arbitrary GitHub-supplied code, shell command or user text is executed, and the GitHub job schema has a fixed action allowlist.

## Operator workflow

1. AI posts a typed task to the dedicated jobs folder via connected GitHub.
2. User's locally installed worker polls every 30 seconds, checks fixed PLN/source hashes, safe action enum, expiry and source provenance, and records intent before native commands.
3. Existing APA performs native selection/readback, or the pinned production-preflight module handles the specific BDD roof decision.
4. Worker records and publishes machine-readable result; AI reads it and chooses the next construction task. No repeated paste-run cycles.

**State today:** code prepared, PR + focused CI; NOT INSTALLED until the user runs the one-time bootstrap and proves `BRIDGE_AUTOSTART_INSTALLED_PROCESS_LAUNCHED`. No native write capability yet. The first queued BDD114 job will execute after installation if before expiry; otherwise publish a new task rather than replay.

## Safety / operational facts

- No arbitrary `script`, command names or `exec` fields in jobs.
- Source files and controller code are Git blob SHA pinned.
- Only one receiver runs via a Windows file lock; no duplicate jobs after crash.
- No automatic re-attempt after unknown native result.
- Missing or changed installed module, unsaved PLN drift or wrong active project results in a blocked status.
- The Windows task is a user-login Startup entry, not a system background service; it stops at logout. GitHub `gh` authentication and Archicad must remain available for live execution.


## First real autonomous task: BDD 1.14 (LIVE PASS, 2026-10-17)

- User installed the pinned worker with `BRIDGE_AUTOSTART_INSTALLED_PROCESS_LAUNCHED` (process PID 91336); current-user startup entry `APA-AC29-GPT-Bridge.vbs`. This is evidence from the user's PowerShell output, not an independent process-survival audit.
- Agent submitted job `bdd114-roof-auto-20261017` to `safe-bim-bridge/main/safe-bim-mailbox/apa-ac29/jobs/`. Local worker picked it up **without another manual operation**.
- [Durable machine result](https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/safe-bim-mailbox/apa-ac29/results/bdd114-roof-auto-20261017.json) (blob `b4f9aaa01a3ba0e6c95efc0021e4cbc1373cdee6`): `jobStatus=COMPLETE`; `geometryStatus=ROOF_NATIVE_FACE_CLEAR_NORTH_JUNCTION_MATCHES_EXISTING`; `modelWrites=0`; `nativeBuildExecuted=false`; `automaticRetry=false`; `modelWritesAuthorized=false`.
- [Detailed live native BREP report](https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/safe-bim-mailbox/gpt-live/results/apa-bdd114-native-roof-20261017T143031Z-2bc6fa9d.json) (blob `4c2aa7ae1b1d37319e145ad6706bc86635860755`): all seven positions at X=9.370m show roof face clearance above top Z=2.900m of, in order, `0.4932, 0.7568, 1.0211, 1.2816, 1.5427, 1.9220, 2.3013` meters; roof face scan reported `roofClearAtAllSevenMembers=true`. North-wall contact was compared to the **existing AABB precedent** of studs at X=3.53m and 7.15m; an AABB comparison does not prove load-bearing joint engineering acceptance.
- Source X=9.370m remains **calibrated from vectors**, not printed dimension; the user has not explicitly approved use of that graphical estimate for a model-writing operation. Thus BDD CREATE/COPY still requires a fresh explicit source/placement approval and an original SceneWriter-scoped, collision-checked, single native operation.
- **Acceptance**: real end-to-end automatic GitHub inbox → locally running stable APA native read/geometry preflight → GitHub report is now `LIVE_PASS` for this reviewed **read-only BDD task**. It is **not** a general autonomous Archicad CREATE/MODIFY `LIVE_PASS`.
