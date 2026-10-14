# APA — GDL / LibraryPart factory: existing capability, identity gaps and non-interfering reuse plan

**Scope:** independent source read / no runtime execution. **2026-10-11.**  
**Associated existing S-IDs:** `APA-P00.A02.S03` (historical evidence reconciliation), `APA-P10.A02.S02` (GDL/TN identity and inventory errors), `APA-P70.A02.S04` (project library integration), `APA-P50.A02.S02` (adapter overlap).  
**Status:** SOURCE_REVIEW_ONLY; no claims that native library creation, import or any building modification passed LIVE.  
**Concurrency:** ChatGPT Work is developing APA on other branches. This report is **isolated** under `research/apa-gdl-factory-readonly-gap-gpt6-20261011`, from frozen canonical commit `106f8b59bcda05a3641afe9387adc96ae8c144ac`; it is **not** a change to `PROJECT_PLAN.json`, active Work PRs, the canonical research branch, `main`, Archicad, PLN, APX, SQLite or the Slack coordinator. It is meant for later review via **draft PR only**.

## 1. Why this is new rather than another copy of the 71 files

The complete 71-file archive was already preserved byte-for-byte by another concurrent run, and its Roof / Composite / Project Context interface gaps were already researched and published. This pass neither copies the archive nor re-implements any of those three topics. It examines an **additional** archival idea: [parametric GDL library factory](https://github.com/dvikt33-ux/safe-bim-layer/blob/477ba54a0620ce7c0efc1b835f1d0ad2f1a03ba5/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/05_expansion_candidates/PARAMETRIC_GDL_LIBRARY_FACTORY.md) (Git blob `d6f4bca6a7680a4dcd42fd0cb6793ad29bd2ec36`). That old work targeted **Tapir 1.5.9** and proposed HSF/GDL source → LP_XMLConverter → load library → CreateObjects with native Main GUID verification. It did not prove an installed compiler, executable implementation, live name resolution or reliable creation.

A newer stored [Tapir 1.5.10 command schema snapshot](https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/schemas/tapir-live-1.5.10/tapir-scene-live.json) (Git blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`) **already advertises** two custom companion commands:
- `SafeBIMGlobalLibraryPart` v`1.5.10-safe-bim.global.1`;
- `CreateLibraryPartFromScripts` v`1.5.9-safe-bim.1` (compatibility wrapper).

Both expose actions `AuditWindows`, `AuditDoors`, `Discover`, `Inspect`, `Register`, `Compile`, accept an **explicit** `expectedProjectPath` (required) and have inputs such as `root`, `filePath`, `prototypeGuid`, `script2D` and `script3D`. The first is described as a companion library operating in external storage.

**Crucial limitation:** this establishes a *saved schema contract*, **not** that the same command is currently present in the installed, loaded APX, nor its C++ implementation behavior, writer safety, filesystem side effects, version compatibility or successfully compiled GDL. The command's name is not enough to authorize invoking `Compile` or `Register` while Work runs.

## 2. Source-backed interface/identity matrix

| Existing component | What was actually checked | Verified boundary | Gap before use |
| --- | --- | --- | --- |
| Stored native companion library command | Saved 1.5.10 schema contains `SafeBIMGlobalLibraryPart` and `CreateLibraryPartFromScripts` with `Discover/Inspect/Register/Compile` | **PINNED_SCHEMA_VERIFIED**, no current installed runtime proof | Read exact implementation; verify APX binary identity, external-output mutation effects and exact project binding |
| `GetAvailableLibraryParts` | Returns library part `guid/index/documentName`, `skippedCount` and `skippedSample` | **PINNED_SCHEMA_VERIFIED** | Prior **92 read errors** were historical. Incomplete inventory cannot certify unique resolution |
| `CreateObjects` | Required item fields `libraryPartName`, `coordinates`; no `ownUnID/Main GUID` selector | **PINNED_SCHEMA_VERIFIED** | Must prove that name resolves through the **same native resolver** that the write command invokes |
| Post-create identity | `GetDetailsOfElements` includes `ObjectDetails.libPart`; `LibPartDetails` has `name`, `parentUnID`, `ownUnID` | **PINNED_SCHEMA_VERIFIED** | Saved schema supports exact Main ID **readback shape**, but current LIVE semantics and matches to expected revision/parameters not yet demonstrated |
| Parametric values | `GetGDLParametersOfElements` returns typed parameter details | **PINNED_SCHEMA_VERIFIED** | Need typed before/after values for exact newly-created GUID; not a substitute for libpart identity |
| Existing Project Library Pack | [PR #41 source](https://github.com/dvikt33-ux/safe-bim-layer/blob/83fd72e150e96cb90db75145436d023969365bd3/scripts/archicad_project_library_pack.py) resolves only one exact `BuildingMaterial`; read commands are `GetProjectInfo/GetStories/GetAttributesByType` | **SOURCE_READ**, no GDL load/writes | Its `importedLibraryObjects=[]` must remain truthful; **extend later**, don't replace it with a competing registry/writer |
| Existing native resolver probe patch | [PR #20 patch](https://github.com/dvikt33-ux/safe-bim-layer/blob/9b75c2fed9d51301a7a620ca94df7a36d5545870/docs/research/patches/tapir-1.5.10-blocker1-readonly-diagnostic.patch) calls `ACAPI_LibraryPart_Search(&probe,false,true)`, returns ownUnID, index, placeability/missing definition + unsampled failed inventory indices | **SOURCE_PATCH_ONLY** | No evidence that patched command was installed or returned real current project results |
| Global/Project library boundaries | [AC29 draft library migration policy](https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/docs/archicad-template/LIBRARY_MIGRATION_POLICY_v0.1.md) and [Checkpoint 37](https://github.com/dvikt33-ux/safe-bim-layer/blob/03f94e9bb67e01a0944813b25eaea50b1afa0ead/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md) favor AC29 Global Library plus small, rights-gated Project Library Pack | **DRAFT_POLICY_READ** | Don't load old monolithic/manufacturer catalogs or promote link-only source to approved project component |

The current source-backed Project Library Pack report is [P70.A02.S03 report](https://github.com/dvikt33-ux/safe-bim-layer/blob/106f8b59bcda05a3641afe9387adc96ae8c144ac/docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-163145Z-p70-a02-s03-library-pack/REPORT.md) (Git blob `80b55c7f404f4241f19c520320a2615d46d9c341`): its original scope is deliberately a Basic Slab/Building Material candidate with no imported GDL and no general structural approval.

## 3. Reuse first; no duplicate GDL engine

Two candidate paths exist, but **neither** is approved for execution in this review.

**Path A — first audit the existing native companion command.** It may already cover part of the desired LibraryPart source/inspection/compile flow. Before reuse, inspect actual C++ implementation and return semantics, verify which action modes are strictly read-only, confirm installed APX source/binary and schema parity, version constraints, persistent Main ID and Revision ID, Unicode and macro dependency semantics. In particular, a command named `Inspect` must not be assumed side-effect-free merely from its name: verify behavior in code and in a separately authorized disposable instance. **Do not invoke Register/Compile now.**

**Path B — fallback offline HSF + LP_XMLConverter.** The archived research describes a valid *architecture proposal*, not an installed tool or signed off reproducible build. If Path A proves unsuitable, only then validate AC29-specific `LP_XMLConverter.exe` location and hash, HSF skeleton/Main ID rules, locked generated-output root, fixed argv input, error handling, source hashing, rights and revisions. This is subordinate to existing `APA-P70.A02.S04` and must not create a second BIM writer.

Both paths must eventually terminate in the **existing guarded native executor** rather than invoking `CreateObjects` from an uncontrolled research agent.

## 4. Minimum acceptance ladder — independently falsifiable

1. **Source/ABI gate (read-only):** identify implementation/commit of `SafeBIMGlobalLibraryPart` and the actual installed APX; prove identity and command availability against the exact one open project. A stored 1.5.10 documentation export alone is insufficient.
2. **Pure inspection gate (read-only, separately checked):** freeze exact project identity/path; determine if an existing native `Discover/Inspect` action can safely read expected Main ID, subtype, revision, placeability and dependencies. No state-changing call permitted in an alleged read-only probe.
3. **Native resolver parity gate:** prove `libraryPartName` resolves with the exact search flags used by `CreateObjects`. Validate Main GUID, placeability, no missing definition and full inventory error coverage; historical 92 failed library reads cannot be waved away.
4. **Build/content gate (offline, later):** require source-controlled HSF/GDL or equivalent existing command inputs, stable Main ID policy, cryptographic source fingerprint, deterministic output path, rights/dependency manifest, Unicode regression tests and error rollback. No arbitrary AI-provided shell command.
5. **Separate permission gate:** obtain explicit scoped permission **before** any generated external file, registering/reloading project libraries, embedding GSM, SetGDLParameters or native `CreateObjects`. `AddLibraries`/`SetLibraries` are project-global side effects, not innocuous readback.
6. **One exactly-owned live placement gate (later):** after explicitly approved disposable PLN and frozen plan, create one Object, save the returned exact element GUID and independently read back `ObjectDetails.libPart.ownUnID` plus `GetGDLParametersOfElements`; refuse ambiguous identity, project drift or blind retries. Do not confuse newly created element GUID with the LibraryPart Main GUID.
7. **Project Library Pack integration gate:** only after provenance, AC29 version, storage/license and repeatable readback are verified may `importedLibraryObjects` become nonempty for the approved project revision. It must not auto-approve manufacturer detail systems or replace native Wall/Slab/Roof/MEP semantics.

## 5. Actionable handoff without interfering with Work

- **Existing `APA-P10.A02.S02`:** native resolver/92-error diagnosis and Main GUID identity proof; reuse PR #20's prepared diagnostic concept instead of a second resolver.
- **Existing `APA-P70.A02.S04`:** follow-on library-system material/GDL integration, exact per-project provenance, Unicode, permissions and live release gate **only after** Work has finished its current changes.
- **Existing `APA-P50.A02.S02`:** record that compiler-like custom schema commands exist before comparing adapters and selecting boundaries.
- **Existing `APA-P00.A02.S03`:** legacy source summary is *partially superseded* by the newer saved schema, not deleted; retain the original 71/71 historical records and add this later after review.

**No new S-ID proposed and none marked DONE.** All four S-IDs are pointers for later governance review, not claims or dispatched tasks. Research source verification does **not** certify deployed Archicad behavior. This independent draft must **not** be merged automatically or used to modify current Work tasks. See adjacent [machine-readable matrix](GDL_FACTORY_REUSE_GATES.json) for pinned blob identities and gates.

## 6. Safety / result

**SOURCE review completed.** No Archicad process, PLN/APX, global or embedded libraries, local SQLite, Slack coordinator, `main`, canonical research branch, existing Work feature branch/PR or `PROJECT_PLAN.json` was changed. No Windows program executed, compiler invoked, native library created, library reloaded, object placed, or architectural correctness claimed.

**Next decision (after Work's active run):** review Path A's actual C++ implementation and installed source/binary identity before opening any new code/compilation task. Full LIVE gate remains NOT_VERIFIED.
