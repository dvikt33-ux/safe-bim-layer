# Task Brief — Architectural Model Quality v2

## Goal

Upgrade Safe BIM from a command-oriented Archicad writer into a staged architectural-model compiler capable of producing clean, coordinated, repeatable models with explicit geometry-quality gates.

Research basis:

- `docs/research/ARCHITECTURAL_MODEL_QUALITY_RESEARCH.md`
- `docs/research/GENERATION_PIPELINE_V2.md`
- `docs/research/QUALITY_GATES_AND_TEST_MATRIX.md`

## Do not solve this as one giant patch

Implementation must be split into reviewable milestones. Each milestone requires offline/unit tests before any live Archicad validation.

## Milestone 1 — Canonical geometry kernel

Add modules for:

- canonical vertex registry;
- canonical edge registry;
- polygon normalization;
- loop closure;
- self-intersection rejection;
- geometry fingerprinting.

Acceptance:

- cyclic/reversed/closed polygon variants normalize correctly;
- shared boundaries refer to one canonical edge;
- bow-tie and degenerate polygons fail closed;
- no Tapir writes in this milestone.

## Milestone 2 — Space/boundary graph

Add:

- SpaceGraph;
- adjacency validation;
- shared boundary ownership;
- perimeter extraction.

Acceptance:

- adjacent spaces cannot produce duplicate walls;
- external perimeter loops are deterministic;
- invalid adjacency stops before physical writes.

## Milestone 3 — Normalized read-back and receipts

Add:

- normalized comparison by quantity type;
- polygon semantic equality;
- durable execution receipts;
- geometry fingerprints;
- uncertain-write reconciliation.

Acceptance:

- different polygon start vertex does not cause false failure;
- rerun of verified step is idempotent;
- uncertain write never retries until reconciled.

## Milestone 4 — Typed collision/gap QA

Add:

- AABB spatial index;
- typed collision-intent matrix;
- duplicate detector;
- host containment checks;
- loop/gap checks.

Acceptance:

- intended Wall/Window host overlap is not reported as clash;
- duplicate Slab/Wall is reported;
- disconnected declared Wall junction is reported;
- undeclared overlap is ERROR.

## Milestone 5 — Connection layer

Add verified wrappers for pinned Tapir support:

- `TrimElements`;
- `CreateSolidElementLinks`;
- `GetSolidElementLinks`;
- corresponding trim/link read-back where available.

Acceptance:

- roof/wall trim can be created and verified;
- target/operator/operation are persisted;
- connection failure never triggers blind repair write.

## Milestone 6 — RoofGraph

Add:

- eave/ridge/valley graph;
- shared roof-face edge validation;
- ridge elevation agreement;
- deterministic roof-face compilation;
- support/trim wall mapping.

Acceptance:

- simple gable scene passes;
- L-shaped valley scene passes;
- mismatched ridge height fails before write.

## Milestone 7 — Morph validator

Add:

- edge incidence;
- manifold check;
- face orientation;
- degeneracy detection;
- triangulated self-intersection validation where practical.

Acceptance:

- cube passes;
- missing-face cube fails;
- reversed face detected/fixed only if unambiguous;
- self-intersecting body fails.

## Milestone 8 — StyleKit and Favorites

Add:

- Favorite/material/composite/profile resolver against project attributes and pinned schema;
- semantic style families;
- controlled overrides.

Acceptance:

- generated elements can use named project Favorites where schema supports it;
- missing required Favorite is explicit issue, not silent default.

## Milestone 9 — Façade grammar

Add:

- bay grids;
- alignment groups;
- window/door family rules;
- corner/entrance exceptions.

Acceptance:

- repeated openings align to bay/story datums;
- deliberate exceptions are explicit;
- opening collision with corner/junction is caught.

## Milestone 10 — Four-stage project generator

Each project emits/runs:

1. `01_skeleton.py`
2. `02_primary_elements.py`
3. `03_refinement.py`
4. `04_finalization.py`

All stages share execution state and can resume safely.

Acceptance:

- integration scenes in the quality matrix pass;
- final report ends in explicit status, never vague success;
- no duplicate geometry after resume tests.

## Required integration scenes

- clean room box;
- multi-room apartment;
- gable building;
- L-shaped roof valley building;
- terrain + road + retaining condition;
- Morph pavilion;
- façade alignment scene.

## Out of scope for the first v2 implementation

- fabrication-grade LOD 400 claims;
- arbitrary automatic architectural redesign to resolve clashes;
- storage of real `.pln`/`.pla` models in GitHub;
- visual screenshot QA until a verified capture workflow exists.

## Review rule

Keep `main` deployable. Implement each milestone in a focused branch/PR. Live Archicad validation is performed locally against an explicitly selected project copy after offline tests and code review.
