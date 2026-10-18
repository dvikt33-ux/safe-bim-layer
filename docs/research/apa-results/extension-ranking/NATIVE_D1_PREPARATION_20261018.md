# APA AC29 native integration D1 — reuse and exact gaps

This is a separate native-preparation branch from PR #154's base SHA
`ca28e9b8003eeb3a38ca201ea96c0096e07b677f`. It contains no reading-package
implementation changes and **zero new callable native commands**.

## Verified local source evidence

The installed V1 session receipt matches the actual exported Tapir schema SHA
and both source-JS provenance hashes. Snapshot SHA:
`b355d2b1311b16d64a62e63c70c6eb5a01b7283a6675cfa2940ef5f247c1fa46`.
This proves source receipt integrity; it does not reacquire current registration.
The snapshot is labeled Tapir 1.5.10. Adjacent public versions are not substituted.
The installed AC29 executable metadata reads major 29/build 5101.

Installed APX file identity (read only): TapirAddOn_AC29_Win.apx, 3318784 bytes,
SHA256 `d6ccb7ea179bd17648fa79630ae22134b1832595f3859617232eb97ea5b0b8c8`.
Its Windows FileVersion is absent; file presence/hash does not prove loaded
Tapir version or native command registration. No Archicad process was found in
the process inventory in this run, so fresh native tests remain NOT RUN.

## Existing contracts and minimal next connection

| Area | Existing source contracts | Reuse / precise missing gate |
|---|---:|---|
| Native groups | 6 | CreateGroups, GetGroupsOfElements, GetElementsOfGroups, suspend-mode read/write, GetNativeGroupRootsV1 already exist. Reuse these, do not add another grouping engine. |
| Copy groups | Separate PR #164 | CloneNativeGroupV1 + code-owned verifier + original SceneWriter path already implemented at PR #164 SHA b156ae3787403d0e68d7af3135b8208eea90e247. Do not duplicate or install over another executor blindly. |
| Hotlink | 4 | GetHotlinks, CreateHotlinkNodes, CreateHotlinkInstances, ChangeHotlinkInstances already in the existing router's source catalog. Missing current runtime probe, scoped verifier and a disposable source-module fixture. |
| Publisher | 1 | PublishPublisherSet already exists; required publisherSetName, optional outputPath/selectedNavigatorItemIds. Missing current instance/set inventory and output-only fixture; retain document/output scope rather than model-create assumptions. |
| Grid axes | 0 | No matching Grid/Axis source contract in either checked installed catalog. Need an exact SDK29/library-part wrapper or existing bridge example before adding a callable command. No invented grid schema registered. |
| Bulk properties | 14 | Existing property read/write/definition/group/XML/IFC operations. Bind explicit property identities and batch element IDs; independently read back exact values through the original route. |
| Attributes | 12 | Existing attributes/layers/building materials/property routes. Bind owner/material identity and retained element baseline; preserve attribute/project scope and readback. |

Counts overlap for commands involving both properties and attributes. They are
existing contracts, not new features, live capabilities, or permission grants.
Full names, parameter keys and contract SHA are in the adjacent sanitized receipt.

## Preparation result and native acceptance sequence

`scripts/apa_ac29_native_contract_gap_report_d1.py` generates a read-only inventory
from the exact schema/manifest/receipt. It rejects stale schema/source provenance,
does not register commands or use network/native APIs, and records NOT_PROBED.
Two targeted source tests PASS; Windows Python 3.11/3.12 CI checks those tests.

The installed native verifier registry contains the existing scoped create/
translation verifier set; no Hotlink/Publisher/bulk-property/attribute verifier
was added by this report. PR #164's group verifier is an independent existing
source branch. Continue through DynamicCommands → BIM Graph → SceneWriter →
existing native bridge, using the existing grant/journal/readback mechanisms.

Next native slice: one Hotlink node + one instance, only after live AC29 identity
and exact runtime contracts are acquired. Create a uniquely named test PLN copy,
record original-file SHA and retained GUID/BREP baseline, bind the exact module
file SHA and transform, implement the narrowly scoped verifier on the existing
SceneWriter path, execute once, independently read back node/instance identity
and transform, save/reopen the test copy, verify original SHA and retained state.
Any unknown write outcome uses reconciliation rather than replay. Publisher and
bulk properties follow as separate slices after this one passes.

SOURCE VERIFIED / OFFLINE PASS / BUILD Python only / INSTALLED not applicable
to a non-callable inventory / LIVE NOT RUN / ACCEPTED NO. The user's autonomous
policy authorizes subsequent installs and tests on copies; the blocker here is
unavailable live instance and missing verified native slice, not permission.
No main, source PLN/APX, installed runtime, active schedules or plan #182 edits.
