# APA-P10.A01.S01 — AC29 native API signatures and writer error handling

**UTC run:** 2026-10-10 / APA-RUN-20261010-201457Z-sdk-native-signatures
**PLAN:** APA-P10 — Independent AC29 technical audit
**ACTION:** APA-P10.A01 — Native SDK and model
**SUBSTEP:** APA-P10.A01.S01 — AC29 SDK headers and native create/change/get signatures
**Claim:** GitHub CAS PARTIAL to IN_PROGRESS, commit 789350bc90239d1ea294718438028f6516b7a6a2, revision 26, readback PASS.
**Evidence levels:** SOURCE_VERIFIED for pinned SDK29 Command/Memo pages and Tapir 1.5.9 call sites; OFFLINE NOT_RUN; BUILD NOT_RUN; LIVE NOT_VERIFIED; PERFORMANCE NOT_MEASURED. Installed Tapir 1.5.10 and actual local SDK29 header declarations NOT_VERIFIED.
**Provenance:** independent direct reading of source lines (not just previous chat notes).

## 1. Exact primary sources

| ID | URL and section read | Git blob SHA |
|---|---|---|
| S1 | [Graphisoft DevKit 29.3100 Command scopes](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___command.html) — ACAPI_CallUndoableCommand | 148abb5e18a328b269dfb30cc67b105a3e26bc46 |
| S2 | [Graphisoft DevKit 29.3100 API_ElementMemo](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___element_memo.html) — coords, pends, params | 1bf3a607327dbfb4dea1789639126b9cd0499bec |
| S3 | [Graphisoft DevKit 29.3100 API_Elem_Head](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___elem___head.html) — guid, modiStamp, hasMemo | 72f0f788cff62c67556149faf4a4908a158b6b11 |
| S4 | [Tapir 1.5.9 ElementCreationCommands.cpp L45-L173, L1938-L1987](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp#L45-L173) | 716f52f230db435d27aca1e2cc11baf6066724ec |
| S5 | [Tapir 1.5.9 CommandBase.cpp L153-L170](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/CommandBase.cpp#L153-L170) | c39e4f341f183a7e5c8f65fc1142d77ddf2cd848 |
| S6 | [Tapir 1.5.9 ProjectCommands.cpp L2696-L2710](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp#L2696-L2710) — Hotlink Change | 99053b4ce5f32b33ae456a076f4355a68994e207 |

Unversioned official Graphisoft legacy reference pages were read in full for parameters, return codes and examples: [GetDefaults](https://archicadapi.graphisoft.com/documentation/acapi_element_getdefaults), [Create](https://archicadapi.graphisoft.com/documentation/acapi_element_create), [Change](https://archicadapi.graphisoft.com/documentation/acapi_element_change), [GetMemo](https://archicadapi.graphisoft.com/documentation/acapi_element_getmemo). Those pages are dated 2013/2019/2020 and **do not prove bit-identical SDK 29.3100 header declarations**. A fetch of pinned docs/group___element.html returned empty content through the GitHub connector; the missing DevKit 29 headers are an explicitly unresolved gate.

## 2. Native function/call-site matrix

| Function | Tapir 1.5.9 direct source invocation | Verification |
|---|---|---|
| ACAPI_Element_GetDefaults | (&element, &memo) — S4 L61, L129 | call-site SOURCE_VERIFIED |
| ACAPI_Element_Create | (&element, &memo) — S4 L141 | call-site SOURCE_VERIFIED |
| ACAPI_Element_Get | (&element) — S4 L1956 | call-site SOURCE_VERIFIED |
| ACAPI_Element_GetMemo | (element.header.guid, &memo, APIMemoMask_AddPars) — S4 L1972 | call-site SOURCE_VERIFIED |
| ACAPI_Element_Change | (&element, &mask, &memo, APIMemoMask_AddPars, true) — S4 L1980 | call-site SOURCE_VERIFIED |
| ACAPI_DisposeElemMemoHdls | (&memo), GS::OnExit — S4 L54, L1971 and S5 L156 | call-site SOURCE_VERIFIED |
| ACAPI_CallUndoableCommand | (undoString, callback) — S4 L51, L1946 | pinned SDK29 S1 additionally documents GSErrCode ACAPI_CallUndoableCommand(const GS::UniString&, const std::function<GSErrCode()>&) |

Legacy Graphisoft reference gives these full prototypes: GetDefaults(API_Element*,API_ElementMemo*), Create(API_Element*,API_ElementMemo*), GetMemo(const API_Guid&,API_ElementMemo*,UInt64), Change(API_Element*,const API_Element*,const API_ElementMemo*,UInt64,bool). Cross-version documentation corroborates Tapir call sites but the full SDK29 header ABI remains NOT_VERIFIED.

## 3. Three verified findings and consequences

### F1 — Batch writer success is not equivalent to successful placement of every requested element

S4 L96-L153 processes items individually. A GetDefaults/Create failure appends a per-item error then continues. S4 L166-L167 returns NoError from the callback; the outer ACAPI_CallUndoableCommand return is not inspected in this function. The code flow justifies a **per-item result and GUID-readback gate** for APA. It does **not** establish that runtime created an inconsistent PLN or that Undo fails. **Decision:** reuse Tapir writer and validate, not rewrite a custom writer.

### F2 — One unchecked GetMemo return on ModifyObjects/ModifyLamps path

In S4 L1954-L1984 the current element is read and type-checked. S4 L1972 invokes ACAPI_Element_GetMemo with APIMemoMask_AddPars but does not check its returned error code before ApplyObjectLampDetails then ACAPI_Element_Change. S4 L1971 uses GS::OnExit for memo handle cleanup. In contrast S5 L153-L159 explicitly checks GetMemo != NoError and uses the same cleanup pattern. **Decision:** use Tapir's existing checked, RAII-protected pattern in future APA native writer/adapter. **Risk:** bad input/error propagation; no proven crash or memory leak. LIVE NOT_VERIFIED.

### F3 — Favorites / AutoText are shared tool settings; restoration errors not all handled

S4 L63-L92 saves AutoText and optionally snapshots defaults. S4 L101-L112 applies favorites and restores defaults between items; S4 L155-L164 restores default settings and AutoText at exit. Return values for the initial GetDefaults L61, snapshot GetDefaults L92, ChangeDefaults L111 and L161 and AutoText change L66/L164 are not explicitly checked in this function. The existence of a restore call is not proof that it succeeded. **Decision:** include state snapshots, error propagation, and restoration readback before APA writers are production-ready. No live failure claimed.

## 4. Reuse comparison

| Architecture | Benefit | Limitation | APA decision |
|---|---|---|---|
| Existing Tapir CRUD/JSON | Ready native creation/change, batch per-item results | Unchecked paths and installed version identity unverified | INTEGRATE after guarded source/readback gates |
| Native Graphisoft SDK writer | Full access to missing native functions | Actual 29.3100 header/build, Undo and memory ownership require testing | USE ONLY FOR PROVEN GAPS |
| Current Native Model Dump | Geometry, materials, floors for model readback | No guarantee of writer transaction atomicity | PRESERVE |
| New universal writer | Full control in theory | Duplicates code and delays MVP | REJECT FOR MVP |
| IFC writer in place of PLN native CRUD | Useful for exchange | Not equivalent to native editable BIM elements | REJECT AS REPLACEMENT |

Source-version licence: Graphisoft DevKit under Graphisoft software agreement; Tapir open-source MIT was documented previously (current investigation did not independently fetch its LICENSE). No foreign paid AI/cloud dependency is needed. No performance improvement has been measured.

## 5. Next test, acceptance and audit handoff

**Test next:** locate legally accessible actual SDK 29.3100 headers (ACAPinc.h/Element API declarations), read exact prototypes and header path/hash, compare to S4/S5/S6. Then independently perform OFFLINE/build-only compatibility, without APX install; test per-item error handling and Favorites/AutoText restoration in separately authorized disposable PLN only. Installed Tapir 1.5.10 provenance remains NOT_VERIFIED.

**Acceptance state:** PARTIAL. Pinned SDK29 Command/ElementMemo types and Tapir 1.5.9 call sites are SOURCE_VERIFIED, but the task explicitly requires actual SDK29 headers. The presence of a publisher DONE_PUBLISHED receipt must NOT upgrade this S-ID to DONE_PUBLISHED.

**Audit handoff:** verify S1-S6 exact blobs and line ranges, check unhandled return paths, compare source against installed binary if available, and require isolated tests before BUILD/LIVE elevation.

**Proposal screen:** no TASK_PROPOSAL_V1. Error/memo restoration gates overlap this S-ID and existing downstream validation/writer tasks (APA-P20); a new work_key would duplicate existing work.

**Safety:** GitHub research metadata only; no main/master, PLN, APX, production branches, Work, Codex, paid API, or local LLM changed or used.


---

**Publication fallback (2026-10-10):** this standalone immutable Markdown copy was committed through GitHub contents API because the automatic V2 REPORT/receipt had not appeared at the time of recovery. SOURCE claims and task acceptance are separate from publication. A later V2 run, if created, is a second representation of the same run and should be deduplicated by run_id, not counted as a new research finding.
