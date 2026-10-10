# APA / Archicad 29 — independent technical audit

> **Status:** RESEARCH_IN_PROGRESS. This is a publication index and verification checklist, **not** a completed technical report. No Archicad API claim is considered verified merely because it appears in this index.

## Scope

Independent technical audit of Archicad Project Accelerator (APA) for **Archicad 29**, focused on native BIM geometry, building materials, stories, library objects, MEP, interoperability, tests, and shortest credible MVP path.

Primary codebase: [safe-bim-layer](https://github.com/dvikt33-ux/safe-bim-layer). Priority review target: [PR #21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21).

## Planned deliverables

- [ ] `RESEARCH_INDEX.md` — evidence map and navigable findings index (this file will be expanded)
- [ ] `VERIFIED_FINDINGS.md` — independently checked facts, API signatures, source lines, versions
- [ ] `TOOLS_AND_INTEGRATIONS.md` — tool and library assessment; adopt/integrate/algorithm/reject
- [ ] `ARCHITECTURE_COMPARISON.md` — materially different options and decision matrix
- [ ] `BLOCKERS_AND_TESTS.md` — reproducible blockers, verification status, test procedures
- [ ] `MVP_IMPLEMENTATION_PLAN.md` — ordered, testable milestones and acceptance criteria

## Evidence policy

- **VERIFIED:** primary source or directly inspected code, with a precise URL, version, and relevant signature/line/section.
- **NOT_VERIFIED — DOCUMENT_NOT_READ:** a source was not read, was inaccessible, or only a title/summary/snippet was available.
- **TEST_REQUIRED:** source suggests an integration path but Archicad 29 behavior has not been validated experimentally.
- **BLOCKED:** a concrete, reproducible technical constraint is documented with its evidence and reproduction steps.

Archicad **29** must be distinguished from earlier releases and Archicad 30. Do not infer API behavior from a README or search snippet.

## Publication and safety

Research output belongs on this isolated branch. Do not alter `main`/`master`, PLN files, installed add-ons, or already validated implementations. No automatic merge.

## Current publication status

This branch was created to host the results. The independent Deep Research report has not yet been transferred into this branch; technical findings and the five remaining deliverables are pending. Do not interpret this index as proof that the audit is complete.
