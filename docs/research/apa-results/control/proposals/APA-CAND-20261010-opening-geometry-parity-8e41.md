# TASK_PROPOSAL_V1 — AC29 Opening geometry/cut read-only parity gate

```yaml
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-20261010-opening-geometry-parity-8e41
origin: technical
proposer_run_id: apa-technical-20261010T1438Z-7f3b6d
source_substep_id: APA-P10.A01.S03
proposed_parent_plan: APA-P20
proposed_action: APA-P20.A01
suggested_substep_id: APA-P20.A01.S04
work_key: ac29-opening-geometry-cut-elements-parity
title: "Read-only AC29 OpeningGeometry/Extrusion/CutElements parity against Native Model Dump"
kind: VALIDATION
priority: 1
depends_on: [APA-P10.A01.S03, APA-P20.A01.S02]
related: [APA-P10.A01.S03]
inputs: [ART-SDK-SEO]
outputs: ["AC29 Opening read-only raw responses, shape/host/cut matrix, dump parity report"]
acceptance: "On a disposable/unchanged test PLN, source-to-installed-SDK provenance verified; read-only Rectangular/Circular/Polygonal openings compared for geometry, local axes, finite/infinite limits, parent vs cut GUIDs against existing Native Model Dump; missing values/errors classified, no false 3D PASS; raw evidence and GitHub readback recorded."
requires_approval: false
expected_mvp_benefit: "Avoid implementing manual opening/void reconstruction when native AC29 getters supply sufficient semantic extrusion geometry; reduce risk of missing secondary cut elements."
evidence_urls:
  - "https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening.html"
  - "https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening_geometry.html"
  - "https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening_extrusion_parameters.html"
risks: "API documentation SOURCE only; installed SDK/build and live coverage NOT_VERIFIED. Optional polygon/dimensions; finite/infinite cuts, hidden/locked elements and secondary hosts require read-only tests. Does not authorize changes to PLN/APX."
```

## Why this is a new executable slice, not duplicate research

Existing **APA-P10.A01.S03** inventories SDK geometry APIs and side effects, and **APA-P20.A01.S02** inventories command availability. Neither acceptance explicitly requires a **shape-specific, two-way semantic/geometry parity test** for AC29 Opening (primary parent versus all cut elements; custom polygon versus width/height; extrusion limit; coordinate basis) against the existing Native Model Dump. This is a narrow **validation gate**, not another broad generic-opening survey.

## Read primary versioned API text (SDK 29.3100)

- `ACAPI::Element::Opening::GetCutElements()` returns **all cut element IDs including parent**; `GetParentElement()` returns one optional parent via Result; `GetConnectedOpenings()` returns openings cutting a specified element. Source: [Opening class 29.3100](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening.html).
- `OpeningGeometry` provides anchor, local X/Y vectors, extrusion direction and `GetPolygon()`; polygon is `nullopt` when opening is not custom-shaped. Source: [OpeningGeometry 29.3100](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening_geometry.html).
- `OpeningExtrusionParameters` exposes shape type, limit type, finite length/start offset and optional width/height, plus end/extrusion surface override fields. Source: [OpeningExtrusionParameters 29.3100](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_element_1_1_opening_extrusion_parameters.html).

## Two implementation options

**A (recommended MVP):** existing Native Model Dump + small read-only AC29 typed Opening adapter; compare GUIDs and 3D cut geometry only where independently visible. **B:** reconstruct voids from all host mesh faces and manually infer host/shape. A reuses native semantics and has lower expected implementation scope; B is more geometry-heavy and brittle. No measured speedup or build PASS.

## Audit request

Check whether this is already subsumed by another **work_key** or existing PR code; validate schema, proposed ID, dependencies, test cost, access to disposable PLN and provenance. If distinct, accept into `PROJECT_PLAN.json` via GitHub SHA-CAS with symmetrical `related` links and a registered `ART-*` input. If not, mark `DUPLICATE`/ `NEEDS_EVIDENCE` with precise reason. **Current state: PENDING_AUDIT; NOT an executable task.**
