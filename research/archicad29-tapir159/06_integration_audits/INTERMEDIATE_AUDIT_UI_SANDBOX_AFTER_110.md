# Intermediate Audit — UI / Sandbox / History / QA after pass 110

Date: 2026-09-27
Research-only branch. No product changes and no live writes.

## Executive result

The research has moved from a vague “safer UI” concept to a technically plausible three-layer protection architecture:

1. **Checkpoint** before a major stage.
2. **One native Undo command** for the whole stage when a custom C++ executor owns the command scope.
3. **Optional native sandbox** based primarily on Design Options, strengthened by Mark-Up and Renovation/highlight visualization.

Continuous QA and deterministic selection/recipe suggestions are feasible without loading a general AI model.

## Findings now sufficiently supported

### A. Compact one-window Russian palette — SUPPORTED

A single modeless palette with an internal browser renderer can host code, AI, selection criteria, history and QA without creating a user-visible second application.

Interaction requirements now fixed:

- main area collapsed by default;
- Code toggles open and may auto-close after successful execution;
- AI toggles open/closed manually and must not auto-close after response;
- backend version details are hidden unless unhealthy;
- one palette owns all flows.

### B. One Safe BIM stage = one Undo item — SUPPORTED IN CUSTOM EXECUTOR, NOT YET IN TAPIR PATH

Graphisoft command scopes directly support multiple mutations in one undoable command. Current external Tapir dispatch cannot be assumed to inherit this property across multiple JSON calls.

**Architecture decision:** grouped native Undo belongs in a future Safe BIM C++ executor, not in a wrapper around arbitrary Tapir calls.

### C. Photoshop-like Safe BIM History — SUPPORTED AS OWN JOURNAL, NOT AS RANDOM ACCESS TO THE COMPLETE ARCHICAD UNDO STACK

Safe BIM can reliably journal every Safe BIM stage and can observe broad model changes/undo-redo notifications while loaded. It cannot currently promise arbitrary restoration to every historic Archicad manual action.

Required UI wording: **История Safe BIM**.

### D. Renovation change visualization — SUPPORTED

Excellent for visually exposing proposal/new elements; insufficient for isolation/rollback of modified originals.

### E. Design Options sandbox — STRONG CANDIDATE

Archicad 29 API can create Design Options and relink elements. Duplicating originals into a Safe BIM option can preserve originals during experimentation.

Primary unresolved area: clone dependency closure for hosted/associative element graphs.

### F. Mark-Up change mapping — SUPPORTED

Original↔modified GUID mapping is explicitly supported for Mark-Up Modification components. This is an unusually good native fit for Safe BIM proposal review.

### G. Incremental continuous QA — SUPPORTED

Element/edit notifications, relation APIs and temporary highlight provide the primitives for model checks after every edit without full-model rescans.

### H. Wall-junction QA — INPUT DATA SUFFICIENT FOR OFFLINE IMPLEMENTATION DESIGN

The API exposes the exact classes of information needed to investigate the user’s known failure mode:

- Building Material priority;
- wall junction order/sequence;
- layer intersection group;
- wall reference geometry;
- actual wall relations.

A live corpus will still be needed to calibrate tolerances and confirm expected relation signatures.

### I. Similar-element checkbox selector — SUPPORTED

No AI needed for actual matching. AI/voice only translates intent into visible criteria.

### J. Lightweight Russian voice — MULTIPLE VIABLE CANDIDATES

`whisper.cpp tiny/base` and `sherpa-onnx small Russian Zipformer` can run CPU-side, avoiding GPU contention. Architecture should use push-to-talk + deterministic command parser.

### K. BIBIM-provider sharing — PARTIAL

BIBIM’s provider choices and local OpenAI-compatible support are documented. Safe BIM can point at the same local server. Silent reuse/decryption of BIBIM cloud credentials is not acceptable and is unnecessary.

Direct BIBIM bridge reuse remains undocumented as a stable external API.

## Gaps that still justify another focused pass series

The following are now the highest-value unknowns:

1. **Design Option dependency cloning:** doors/windows, hosted labels, dimensions, groups, zones, SEO/trim relations and other associative dependencies.
2. **Sandbox accept semantics:** safest promotion mechanism from proposal duplicate to original — deterministic replay vs replace/relink vs property transfer.
3. **Mark-Up review behavior:** how original/modified pairs appear in Archicad UI and whether they improve human review enough to justify automatic issue creation.
4. **Checkpoint implementation:** exact solo-PLN backup-copy behavior and a separate Teamwork strategy.
5. **History persistence:** optimal split between SQLite, project ModData/UserData and Element Sets.
6. **Passive contextual suggestions:** exact usefulness of Archicad 29 `EditNotificationInterface` for suggestion timing; it is post-edit, so it cannot be assumed to provide native-tool hover interception.
7. **Highlight styling:** temporary highlight is supported, but exact controllable color/style capabilities need final source verification.
8. **Voice latency/accuracy on Russian architectural vocabulary:** must be benchmarked on target hardware, not inferred from model size alone.
9. **BIBIM config import contract:** public README describes path/security/provider types, but stable field schema for non-secret provider/model/base URL should be audited before import support.
10. **Native stage Undo vs external SQLite crash semantics:** determine ordering of durable dispatch receipt/checkpoint records around a single native command scope.

## Risk ranking

| Topic | Risk | Reason |
|---|---:|---|
| Design Option sandbox for standalone elements | Medium | API clear, dependency closure not yet certified |
| Sandbox for host trees | High | clone/link dependencies can silently diverge |
| Native grouped Undo in own C++ executor | Medium | API clear; integration with durable journal must be designed |
| Full arbitrary Archicad history rollback | High / unsupported today | no proven random-access native Undo stack API |
| Renovation staging | Low | visualization only; easy to bound |
| Mark-Up mapping | Low–Medium | exact mapping API exists; UX usefulness needs prototype |
| Wall QA | Medium | inputs proven, tolerance/signature calibration remains |
| Similar selection | Low | deterministic API problem |
| Voice checkbox control | Low | failure can be non-destructive and visibly confirmed |
| BIBIM bridge dependency | High | private/unstable contract until audited |

## Decision after audit

Do **not** stop research yet. Another 10 focused passes are justified, but they should target the gaps above rather than broad feature discovery.

After those passes, perform a prefinal audit and decide which features move into the first Palette/Sandbox implementation backlog.