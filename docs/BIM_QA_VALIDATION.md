# Offline BIM-QA validation

Date: 2026-10-03. Branch: `chatgpt/archicad-modeling-standard-v1`, PR #5.

This report covers the offline auditor update adding:

- BIM-QA-008 STORY_ASSIGNMENT;
- BIM-QA-011 MINIMUM_ELEMENT_COUNT / operations-before-fragmentation;
- stricter reviewed handling of `api_limitation` fragmentation exceptions.

| Verification | Result |
| --- | --- |
| Reconstructed regression suite + new policy tests | **PASS: 61 tests, 0 failures, 0 errors** |
| Previous 43 regression tests | **PASS in the reconstructed suite** |
| BIM-QA-008 positive / negative cases | **PASS** |
| BIM-QA-011 one-Wall+trim / fragmented gable cases | **PASS** |
| BIM-QA-011 porch one/minimal Slab + operation / many-slab cases | **PASS** |
| API limitation without reviewed fallback | **PASS: blocked as intended** |
| Missing/incomplete new evidence | **PASS: NOT_VERIFIED as intended** |
| PASS_DEPENDENCY exposure of 008/011 | **PASS** |
| Syntax/import smoke | **PASS** |
| Live Archicad / production PLN validation | **NOT_VERIFIED** |
| Full roof/wall-top/rafter model acceptance | **NOT_VERIFIED: rules 004–007 remain TO_IMPLEMENT** |

## What the new tests establish

The new element-economy rule does not merely search for duplicate IDs. It checks
a trusted semantic construction contract that declares the smallest known valid
element count and strategy for each controlled role.

Examples verified offline:

```text
gable:
  one Wall + TrimElementsToRoofShell
  maxElementCount = 1
  => PASS

gable:
  several Walls for the same semantic role
  maxElementCount = 1
  no reviewed construction exception
  => FAIL

porch/platform:
  one Slab + SlabPolygonSubtract
  maxElementCount = 1
  => PASS

porch/platform:
  five small Slabs for the same role
  maxElementCount = 1
  => FAIL
```

`api_limitation` is not accepted merely because the current bridge lacks an
operation. It additionally requires `fallbackReviewed: true`; otherwise
fragmentation remains a blocker.

## Story assignment boundary

BIM-QA-008 requires a trusted intent for every controlled GUID. Floor/story index
must match read-back. When `elevationMode == ABSOLUTE_BASE`, base elevation must
also match. Missing actual story/elevation evidence is `NOT_VERIFIED`, never PASS.

## Remaining boundary

This work is still **offline validation**. `liveValidationState` remains
`NOT_VERIFIED` for every implemented rule until a controlled read-only capture
from Archicad exercises the contract. Existing generation/runtime operations are
not mutated by the auditor.

Rules 004 ROOF_COLLISIONS, 005 ROOF_GAPS, 006 WALL_TOPS and 007 RAFTER_ALIGNMENT
remain the next geometric blockers before a complete roof/rafter pipeline can
receive PASS.
