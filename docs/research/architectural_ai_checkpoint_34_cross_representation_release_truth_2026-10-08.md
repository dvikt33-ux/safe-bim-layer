# Architectural AI checkpoint 34 — Cross-representation consistency & release truth

Date: 2026-10-08
Status: RESEARCH ONLY — not live-tested
Target: Archicad 29; no AC30 implementation

## Carry-over
Builds on checkpoints 25–26 documentation/view coverage and concurrent 26 native Issues/Revision, 32 native Navigator Add-On viewpoints, 33 native event/invalidation. Does not duplicate those.

## Problem
An internally correct BIM does NOT prove that plans, facades, sections, manually annotated dimensions, schedules, details, IFC and delivered PDFs/DWGs agree. Need a source-to-projection-to-issued-file QA chain.

## Newly found products — official evidence and limits

### Structured AI
Official docs: https://docs.getstructured.ai/
Trade press Oct 6: https://aecmag.com/bim/qa-qc-platform-links-bim-models-and-drawing-sets/
Vendor documents sheet QAQC, version comparison, comments, code review, IFC-model support, Revit links; trade press reports correlations between IFC/native Revit and PDFs/specs/schedules and model-element-linked sheet findings.
UNVERIFIED: Archicad native connector, precise IFC GUID response, API/webhook, Russian/metric support, accuracy. Candidate P0/P1 independent QA demo, not runtime dependency.

### Revizto
AC29 Windows native publishing plugin: https://help.revizto.com/hc/en-us/articles/360001637936
2D/3D overlay, split-view: https://revizto.com/product/unified-2d-3d-environment
API/portal: https://help.revizto.com/hc/en-us/articles/16924350271119-Revizto-developer-portal
Official MCP: https://help.revizto.com/hc/en-us/articles/16924308080271-Connecting-AI-tools-to-Revizto-MCP-server
Confirmed native Archicad 23–29 compatibility, overlay of imported PDF and model, API and MCP. Important limitations: MCP does NOT expose images/screenshots, model import/export, event subscriptions/webhooks, project logs. Extended API permission needed for per-object properties. Imported PDF alignment may require calibration. This is coordination/inspection, not authoritative live model reader.

### Bluebeam Max / Smart Review
Official: https://support.bluebeam.com/revu/how-to/use-smart-review.html
FAQ: https://support.bluebeam.com/revu/resources/smart-overlay-review-faq.html
MCP: https://support.bluebeam.com/revu/resources/revu-mcp.html
Checks missing/blank/duplicate-number sheets, absent sheet references, gridline coordination, door plan/schedule tags, plumbing tags. Smart Overlay compares revisions; MCP connects Revu to AI for PDF workflows.
CRITICAL: Smart Review CURRENTLY IMPERIAL UNITS ONLY, oriented to US vertical construction, preview status. Smart Overlay auto-matching is not generalized cross-discipline matching. NOT Russian metric/SPDS check authority. Method/UX benchmark only.

### AC29 native Model Compare + Revision Manager
Official Model Compare: https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm
Official Revision workflow: https://help.graphisoft.com/AC/29/INT/_AC29_Help/070_Documentation/070_Documentation-98.htm
Model Compare sees new/modified/deleted 3D elements and can create Issues. It explicitly does NOT compare 2D objects. A comparison is frozen at its snapshot and must be re-run after changes. Element-linked Revision Changes propagate to layouts ONLY WHEN affected Drawings are up to date. Do not confuse RVM Changes with regular BCF Issues.

### IfcTester
Official: https://docs.ifcopenshell.org/ifctester.html
Existing Python/CLI IDS validation of IFC and reports SQLite/JSON/HTML/ODS/BCF. It does not check annotations and PDF correspondence; reuse rather than rewrite.

### Bluebeam basic Compare/Overlay
Official: https://support.bluebeam.com/revu/features/compare-documents-vs-overlay-pages.html
Reusable 2D graphical diff of PDF revisions, but not a semantic correctness proof.

### Cross-view research
2026 study: https://www.sciencedirect.com/science/article/pii/S0926580526002128
Floorplan/elevation matching via a cost matrix + Hungarian algorithm gives a possible method for legacy external 2D files. It is NOT a replacement for native GUID/view lineage in Archicad.

## Four necessary classes of truth
1. BIM internal: model geometry/materials/stories/zones/systems.
2. BIM -> View: floorplan/section/elevation/schedule is current and correctly associates model objects.
3. View -> issued file: publisher result is complete, current, legible, correct revision and includes required annotations.
4. Cross-discipline: AR/KR/MEP/fire/specs/details share the applicable coordinates, levels, penetrations, requirements, and revisions.
PASS at level 1 never implies PASS at 2–4.

## Thin new concept: Representation Witness Record
Bind an authoritative BIM fact (source GUID, facet, unit, native readback, revision) to every declared representation (view GUID, schedule row, sheet, PDF issue/revision, detail family) and a set of tests (value equivalence, reference validity, freshness, coverage).
Statuses: PASS, FAIL, NOT_ASSESSABLE, STALE, BLOCKED. Never fabricate a pass when projection or external file is not independently checked.

## Twelve cross-representation invariants
- levels and floor-to-floor heights across floorplan, section, elevation;
- window width/height/sill/head, hosted wall and opening mark across model/view/schedule;
- door hand, clearance and swing vs schedule/egress;
- grid axes and spacing across AR/KR and published annotations;
- actual room bounded geometry/area vs zone/explication;
- CSE wall/roof/slab layers/thickness vs detail and specification;
- MEP route vs penetration/firestop/structural opening;
- all detail/section/elevation markers lead to existing, correct sheet/view/revision;
- sheet index and Publisher set match actual files;
- every Layout Drawing current and release revision valid;
- each source change dirties downstream representations and invalidates stale PASS;
- facade rhythm/massing/architectural intent preserved or explicitly reviewed.

## Reuse-first architecture
Archicad 29 native read/events + model facet state -> Representation Witness Index -> Views/Schedules/Details -> Publisher Release Manifest -> deterministic data/metadata checks (native/IfcTester) -> optional independent PDF/IFC reviewers (Structured AI, Revizto, Bluebeam) -> findings/BCF/Archicad Issues -> accountable release approval.
Reuse existing native revisions, BCF, issues and drawing storage; no new generic CDE, diff engine or PDF viewer.

## Two-tier gate
PRE-FLIGHT: source/view/drawing current, constraints/required information covered, schedule tags and detail refs resolved, title-block/SPDS version, expected files enumerated.
RELEASE: actual exported PDF/DWG files checked, page IDs and quantities matched, diff vs previous version inspected, independent reviewer optional for risk, unresolved findings adjudicated.
Mandatory NOT_ASSESSABLE, STALE or BLOCKED => NOT READY TO ISSUE.

## Failure injection benchmark (NOT RUN)
CROSSREP-01 wall moved on only one storey;
CROSSREP-02 window resized but external PDF facade stale;
CROSSREP-03 duplicate/missing door mark in schedule;
CROSSREP-04 manually typed 2D elevation contradicts BIM Z;
CROSSREP-05 composite changed without corresponding detail update;
CROSSREP-06 AR/KR axis displaced;
CROSSREP-07 Change recorded while Layout Drawing not updated;
CROSSREP-08 detail points to deleted/renumbered sheet;
CROSSREP-09 room area schedule differs from current zone calculation;
CROSSREP-10 PDF output missing sheet that index expects;
CROSSREP-11 MEP/structural penetration misaligned;
CROSSREP-12 changed window breaks facade design-intent rule.
Per test: exact source object, actual result, false positives, precision/recall by failure family, reviewer time, auto-fixed vs human-reviewed.

## Reuse classification
REUSE: AC29 Model Compare/RVM, native Schedules/Views/Publisher, IfcTester, BCF, Bluebeam PDF overlay when licensed.
BENCHMARK FIRST: Revizto AC29 + API/MCP, Structured AI model/PDF QA, Bluebeam Max Smart Review.
BUILD ONLY IF GAP PROVEN: small witness index, cross-representation coverage, Publisher manifest gate, Russian SPDS check mapping, architectural-intent relation checks.

## Next practical tests
RELEASE-MANIFEST-01: generate authoritative manifest and check exact PDF/IFC revisions/files.
REVIZTO-AC29-01: export one test AC29 model/sheet, overlay alignment + GUID query + issue roundtrip; compare MCP limitations.
STRUCTURED-IFC-PDF-01: independent AI checks seeded mismatches, measure exact element provenance and false negatives.
CROSSREP-01-12: run injected failures in separate scratch copy, no changes to source PLN.

## Verification status
No external SaaS accounts used; no Archicad file changed; no live testing; no new plugin installed. The checkpoint documents vendor-verified functionality and research hypotheses, not an achieved working integration.