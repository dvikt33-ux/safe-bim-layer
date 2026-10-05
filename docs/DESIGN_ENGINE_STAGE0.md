# DESIGN ENGINE STAGE 0

Implements the existing `PROJECT_INTAKE_AND_DATA_GAP_STANDARD.md` and
`project_intake_stage0_contract.v1.json`. Those source documents remain unchanged.

This is an offline, file-to-file intake audit and permission gate. It adds no
runtime integration, network transport, Archicad/Tapir operation, UI, normative
base, constraints, layout or Stage 4 implementation.

## Working end-to-end scenario

From the repository root:

```powershell
python -m design_stage0 --registry docs/examples/design_stage0/registry.json --sources docs/examples/design_stage0/sources.json --output work/stage0-missing.json
# Exit 2: one blocking input, municipality, one precise question.
python -m design_stage0 --registry docs/examples/design_stage0/registry.json --sources docs/examples/design_stage0/sources.json --answers docs/examples/design_stage0/answers.json --output work/stage0-verified.json
# Exit 0: supplied answer -> complete re-audit -> VERIFIED, no questions.
python -m unittest tests.test_design_stage0 -v
```

The example registry and project are **synthetic acceptance fixtures**. They are
not regulatory guidance, typical building values or project defaults.

## Input boundary

The caller must enumerate all accessible sources in the active project context,
extract facts, and explicitly record each source's inspection status. The engine
indexes every supplied source before questions. An uninspected or malformed
source blocks the gate and suppresses user questions. The module does not claim
to have searched unlisted repositories, documents, prior chats or live models.
Collectors remain outside this change; existing read-back can be supplied as
evidence without any new BIM calls.

Source records carry `id`, `kind`, `revision`, `inspected`, and `facts`. Facts
carry `value`, `unit` (null for unitless data), `method`, and `verification`.
Only VERIFIED evidence of an accepted source kind, type, range and unit is
confirmed. Declared assumptions and forbidden fallback bases cannot pass.
Corrections supersede explicit `sourceId:inputId` evidence references only when
supplied as VERIFIED USER_CORRECTION or APPROVED_PROJECT_DECISION; dates alone
never resolve conflicts. Conflicting candidate values and provenance are kept.

The supplied approved, versioned registry defines classification inputs,
selective branches, and requirements. Each requirement declares its dependency,
reason, format, unit, source kinds, blocking status, priority and acquisition
owner. Branch conditions in this skeleton are explicit equality predicates;
missing evidence yields UNKNOWN. No normative rules are invented or researched.

Deterministic methods are limited to `count`, `sum`, and `closed_polygon_area`.
They require confirmed direct evidence, matching declared units, a valid result
and complete derivation provenance. Polygon area rejects open, degenerate and
self-intersecting polygons. It is a numerical fixture capability, not survey
approval. A failed derivation stays UNKNOWN_BUT_DERIVABLE and blocks progression.

## Flow and output

`COLLECT -> CLASSIFY -> APPLICABILITY -> REQUIRED INPUT MATRIX -> MAP KNOWN DATA
-> DERIVE -> CONFLICTS/GAPS -> REQUIRED_USER_INPUT_PACKAGE -> RE-AUDIT -> VERIFIED`

Re-audit recomputes applicability and the required matrix after derivation until
routing is stable. It catches requirements activated by a derived input. The
output includes classification, applicability, inputs, gaps, conflicts,
derivations, source evidence, gate proof, stable re-audit and context fingerprint.

`REQUIRED_USER_INPUT_PACKAGE` covers every active blocking missing/conflicting
input with WHAT, WHY, REQUIRED_BY, FORMAT (including units), derivation capability
and method, resolution owner and provenance. Resolution owners are separate:

- SYSTEM_CAN_FIND: search/acquisition work for the caller's collectors;
- SYSTEM_CAN_DERIVE: deterministic calculation work, including a failed method;
- USER_CLIENT_SURVEYOR_MUST_PROVIDE: explicit external evidence or conflict resolution.

The package is the complete blocker ledger. `questions` selects user-owned
blockers at the earliest dependency priority only. Known, derived, optional and
unrelated branch inputs do not create questions. System-owned blockers remain
visible and block the gate; they do not become user questions.

## VERIFIED gate and invalidation

`Stage0.require_verified()` returns the computed gate proof only when the latest
audit is VERIFIED and its full registry/source fingerprint still matches. It
raises on every other state. It executes no downstream operation.

All conditions from the existing contract must pass: verified classification,
complete applicability and required matrix, zero required gaps/conflicts/blocking
unknown derivations/assumptions, complete provenance for blocking inputs. Source
collection must also be complete. Optional missing data alone does not block.

`update_source()` and `update_registry()` invalidate a previous gate immediately.
No answer or material change is accepted as VERIFIED without `audit()` again.
Returned result copies cannot mutate or forge the session gate. Invalidation
reports known dependency IDs; source updates conservatively invalidate all active
blocking dependencies rather than claim an unproven narrow impact analysis.

## Regression boundary

Stage 2/3/Audit Pack are absent from the intake base commit. Their existing tests
are run unchanged from `work/audit-pack-fix` at
`03c64733bb2b4f59970f5247a3ed89e1236f3090`, with only the new Stage 0 files overlaid.
Stage 2: 44 tests; Stage 3: 4 offline adapter tests; Audit Pack: 47 tests. Tests
use synthetic adapters and existing evidence and make no live Archicad calls.
No merge of later-stage implementation into the intake branch is needed.
