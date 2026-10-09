# SomeStuff SyncGuids — experimental source overlay (AC29)

**Status: SOURCE STAGED / NOT COMPILED / NOT INSTALLED / NOT LIVE TESTED.**
This directory contains an **additive integration overlay** for the upstream
[kuvbur/AddOn_SomeStuff](https://github.com/kuvbur/AddOn_SomeStuff) add-on.
The original repository is read-only on the connected GitHub account. No changes
have been made to its trunk, and no deployed APX or user PLN was modified here.

## Baseline

- Source inspected: upstream **tag** `test-latest`, commit
  `bc371d9ee4b602315b1045e2ff1f71ea1e3b808c`.
- Target: **Windows Archicad 29 / SomeStuff 2.01**.
- Existing, live-tested command: `SomeStuffCommand.SyncAll`.
- Existing internal engine: `SyncArray(const SyncSettings&, GS::Array<API_Guid>&)`.
- This new `SomeStuffCommand.SyncGuids` endpoint has NOT been built or installed.
- Existing confirmed test: `SS-AB-02` 2000/2000, tracking OFF behavior, zero mismatches.

## Contents

- `Sources/AddOn/json_commands/SyncGuidsCommand.hpp`: endpoint declaration.
- `Sources/AddOn/json_commands/SyncGuidsCommand.cpp`: input validation,
  tracking-OFF guard, targeted SyncArray call and one recursive pass.
- `patches/registrar.diff`: additive registration in the upstream
  `Sources/AddOn/json_commands/JsonCommandRegistrar.cpp`.
- `smoke_syncguids.py`: future fail-closed LIVE test on **10 existing walls**,
  only after compiling and installing the experimental APX.

## One-command Windows source preparation / build

For the user's Windows 11 desktop, `prepare_build_ac29.ps1` performs an isolated
checkout of the pinned SomeStuff tag, downloads this overlay at a **pinned
SafeBIM commit**, checks and applies the registrar patch, verifies exactly
three expected source files, and (optionally) invokes the project's canonical
Archicad 29 build. It never installs APX, starts Archicad, saves PLN, or
modifies any existing checkout. It **refuses an existing destination**.

Run from PowerShell after downloading the script to a local file:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\prepare_build_ac29.ps1 -AllowDevKitDownload
```

The `-AllowDevKitDownload` switch explicitly authorizes the upstream build
script to download the public Graphisoft Archicad 29 DevKit if none is provided.
If the DevKit is already installed and accessible, prefer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\prepare_build_ac29.ps1 -DevKitPath 'D:\SomeStuff_addon\Build\DevKit\APIDevKit-29'
```

The DevKit path above is **illustrative, not a verified path**. The script
checks `Support\Inc\ACAPinc.h` and stops without building if it is absent.
To prepare source without invoking CMake or downloading a DevKit, use
`-SourceOnly` instead.

Default destination is `%USERPROFILE%\Documents\APA_SyncGuids_Build_20261009`.
Artifacts: `source-report.json`, `build-report.json` or `stop.json`, and
`build.log`. If the script stops after creating the checkout, do **not**
rerun into the same destination; inspect evidence first. A local build is still
required before any new API command can be called.

## Applying into a *separate upstream working copy*

Do not edit the installed SomeStuff.apx. Do not copy this overlay into the
original author checkout with uncommitted work; use a dedicated checkout at the
pinned commit above, then a new feature branch. In that checkout:

1. Copy the two `SyncGuidsCommand.*` sources into
   `Sources/AddOn/json_commands/`.
2. From the upstream repository root, run
   `git apply --check <path-to-overlay>/patches/registrar.diff`, then
   `git apply <path-to-overlay>/patches/registrar.diff`.
   Stop on conflict. Never blindly overwrite another checkout's registrar.
3. Run `clang-format -i` on both new files and the registrar.
4. Verify SDK APIs/signatures against the locally installed Archicad 29 DevKit;
   run LSP and the canonical build
   `python Tools/BuildAddOn.py -c config.json -v 29`.
   CMake's existing `GLOB_RECURSE CONFIGURE_DEPENDS` collects new C++ sources.
5. Inspect compiler/linker output and diff. A successful build is still **not**
   an installed or live-verified add-on. Back up the known-good APX. Do not
   load two builds of SomeStuff with the same add-on identity concurrently.
6. Only in the user's authorized disposable test PLN, after checking project
   identity and baseline, install the *experimental* APX, confirm
   `API.IsAddOnCommandAvailable(SyncGuids) == true` and run the 10-wall
   `smoke_syncguids.py` once.
7. Collect `report.json` or `stop.json`, classify partial errors, then test
   10 / 50 / 200 / 2000 GUIDs against the full-model `SyncAll` baseline on
   paired workloads.

No step above has been executed by this GitHub-only source-staging session.

## Endpoint contract

Namespace `SomeStuffCommand`, command `SyncGuids`, params:

```json
{"elementGuids":["C61E7B1F-6E32-45AC-BCC3-CC3D2FE47C6D"]}
```

- Between 1 and 5000 canonical, syntactically valid, unique GUID strings.
- The entire list is prevalidated (including Element_GetHeader) before work.
- Tracking must be OFF. Calls made with monitoring ON are rejected.
- Properties are synchronized by the *existing* `SyncArray` engine, with one
  extra pass on the engine's returned candidate list, matching `SyncSelected`.
- If the call returns, response `status="returned_unverified"` plus
  `requestedCount`, `secondPassCandidateCount`, `elapsedSeconds`,
  `engineSeconds`, `trackingEnabled=false`, `requiresReadback=true`.
- The response does **not** claim that every element was processed or written.

## Known risks / intentionally blocked claims

1. **Cancellation and write failures**: `SyncArray` may return early on
   cancellation, and its internal `ACAPI_CallUndoableCommand` result is not
   propagated to this wrapper. A returned candidate array is not a success
   receipt. Do NOT count it as `succeededCount`.
2. **Accessibility versus mutability**: `ACAPI_Element_GetHeader` proves a
   header is readable, not that the caller has authority to edit all associated
   elements. The server can partially apply changes; no automatic retries.
3. **Dependent elements**: `SyncArray` can touch related elements outside the
   input list. Only the specific simple wall property-copy rule is covered by
   the initial smoke script; other rules require additional tests.
4. **Semantic differences**: `SyncAll` calls `ResetProperty()` before its
   full sweep; `SyncArray` does not. They are not guaranteed to be equivalent
   for every SomeStuff rule or element class.
5. **Verification**: only independent post-call Archicad property/GUID/
   classification readback establishes an accepted result for our test.
6. **Build**: no Archicad DevKit/compiler available in this connected-chat
   execution. Syntax compatibility remains unverified pending the Windows AC29
   build. No compiled APX is supplied here.

## Benchmarks — existing observations, NOT measured for SyncGuids

| Test | Scope | Observation |
|---|---:|---|
| SS-BATCH-02 | 2000 new walls; automatic monitoring | 2000/2000 target values already updated before SyncAll |
| SS-AB-01 | 2000 existing walls; tracking presumed OFF | 2000/2000 updated before SyncAll — OFF not independently demonstrated |
| SS-AB-02 | 2000 existing walls; tracking toggled OFF | 0/2000 updated before SyncAll; after SyncAll 2000/2000 PASS |
| SyncGuids | none | **NOT BUILT / NOT MEASURED** |

Our current fallback remains **Track OFF + SyncAll**. The first experimental
SyncGuids benchmark should target **10 changed elements out of 2213**, because
that is where a narrower sweep is expected to matter. Do not infer speedup
until a proper paired run succeeds.
