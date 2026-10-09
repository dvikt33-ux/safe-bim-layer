# APA TN-GDL-CREATE-01 — research/verification checkpoint

Date: 2026-10-09. Status: **NOT_VERIFIED / BLOCKED_BEFORE_WRITE**.
This block is not DONE. Publishing this checkpoint does not clear either blocker.

## Evidence boundary

This is a sanitized summary of the saved local REPORT, RESULT, contract and
inventory verification artifacts from the earlier read-only session. Those
private artifacts remain local. This publication pass made no Archicad calls
(read or write), changed no PLN, installed software, libraries or project settings.
Historical observations below are not a fresh live validation.

Base: [PR #16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), head
`bcac2e821a95f927fa6ae9f5fa5742b45d9ca2dd`, stacked on
[PR #15](https://github.com/dvikt33-ux/safe-bim-layer/pull/15), head
`f02a167eb73cb149713cf5e613911b144fce5be2`.

## Saved observations

| Item | Result and limitation |
| --- | --- |
| Runtime reported in saved evidence | Archicad 29 build 5101; Tapir 1.5.10 |
| CreateObjects contract | Input/output and 11 referenced schemas match PR #16; command schema version 1.5.7 is distinct from the Tapir version |
| Model writes / new objects / PLN saves | **0 / 0 / 0** in the saved session; creation and new-object readback NOT RUN |
| Source GDL parameters | All **96** equal the earlier saved baseline |
| Element inventory | **22 GUID**, identical before/after; no additions or removals |
| Library inventory | 7,490 readable entries; one matching name in that readable subset; **92 read errors** |
| Geometry coverage | **2 bodies / 22 inventory GUID**; existing 3D, layer and design-option filters remain active |

Saved CreateObjects accepts `libraryPartName` and coordinates. It exposes no
library-part GUID/index or full GDL-parameter payload; `additionalProperties=false`.
Therefore it does not automatically clone the source object's 96 parameters.
Source inspection indicates name resolution through `ACAPI_LibraryPart_Search`;
source evidence alone does not prove the installed binary's exact behavior.

## Blocker 1 — name-only library resolution

The readable subset contains one same-name entry with the expected library
identity, but the other 92 failed reads are unresolved. Five saved error samples
use code `-2130313112`; the cause and effect on inventory completeness are unknown.
Duplicate names are not established, and uniqueness is not established either.
CreateObjects cannot pin an identity, and an equivalent native read-only name
resolver has not been verified.

Clearance criterion: establish, before creation, that the exact name resolves to
the expected native index **and** ownUnID under the same search rules used by
CreateObjects. Account for all 92 errors and prove that unreadable or excluded
entries cannot change that resolution, using a complete inventory or an audited
equivalent native resolver. Fail closed on ambiguity, mismatch or unexplained
coverage. The private expected identity remains in local evidence.

## Blocker 2 — incomplete geometry/free-placement proof

Two bodies cannot establish full physical coverage of 22 GUID. Missing bodies
may represent nonphysical elements or filter exclusions; neither explanation is
proven for every missing element. No placement coordinate has been approved.
Moving the source geometry alone would not establish a safe prospective volume.
GetCollisions accepts two sets of existing GUID, not a proposed new volume.

Clearance criterion: reconcile every inventory GUID as physical, demonstrably
nonphysical, or excluded, with an evidenced reason. Cover every physical element
that could intersect the proposed placement, including elements excluded by
3D/layer/design-option filters; unresolved exclusions keep the gate closed.
Then define the proposed object's actual volume and justified clearances at a
specific coordinate and establish no intersection or clearance violation against
that complete coverage before creation. Do not substitute a collision check
between existing objects for prospective-placement proof. For any later,
separately authorized creation, require native new-GUID identity, parameter,
position, geometry and inventory readback plus body/clearance collision checks
with justified tolerances; the default volume tolerance of 0.001 m3 is not by
itself evidence that small intersections are absent.

## One next priority

**Audit library name resolution and the 92 read errors offline, using saved
evidence and source/contracts.** Produce one explicit result: either sufficient
proof meeting Blocker 1's criterion, or the precise missing evidence/capability.
Do not guess the error cause. If offline material cannot prove the criterion,
retain NOT_VERIFIED and specify a bounded future read-only probe for separate
authorization. Do not start geometry work, another APA track or a live write
while this priority is open. Blocker 2 remains independently required afterward.

Only after both blockers are evidenced as cleared may a separately authorized
single-object end-to-end creation/readback establish completion of this block.

## Offline publication verification

- The saved-evidence inventory remains historical: 7,490 readable parts, 92
  `ACAPI_LibraryPart_Get` errors, one readable candidate at index 7224, and no
  saved `partCount` or complete skipped-index list. The candidate does not clear
  name resolution.
- This branch adds one sanitized Tapir source patch and focused tests. The
  patch applies to the local Tapir 1.5.10 source; its four focused contract tests
  pass. The full repository suite passes **105/105** with workspace-local
  temporary files.
- MSVC 19.35.32217.1 compiled the modified library-command and registration
  translation units against AC29 DevKit 29.3000. The full APX target did not
  finish because resource compilation stopped at `AddOnFix.grc`; no new APX was
  produced. A read-only scan of the installed Tapir APX did not find the new
  command identifier. No installation, loading, or Archicad calls occurred.
- Blocker 1 remains **BLOCKED / NOT_VERIFIED**: the installed binary does not
  contain this diagnostic, so there is no fresh native search read-back or full
  current skipped-index/error list. The exact expected identity and current
  library registry still need identity-first native read evidence.
- This checkpoint contains no raw model dump, private request/response files,
  project identity, or personal filesystem path. The branch is stacked directly
  on PR #19 commit `39231a1e63ab91ff05cabe484bf737c176434a44`; main and PRs
  #15–#19 are unchanged.
