# Development Principle — Search Before Build

Status: ACTIVE PROJECT RULE
Date: 2026-10-07

## Core rule

Before implementing any substantial subsystem, always assume that someone may already have solved all or part of the problem.

The default question is:

> "Can we search further before coding this?"

Do not conclude "nothing exists" after a shallow search.

## Mandatory pre-build sweep

Before custom implementation, explicitly check:

1. Native Archicad features and official API/Add-On capabilities.
2. Existing Archicad extensions, MCP servers and automation products.
3. Commercial AEC/BIM products.
4. Open-source AEC/BIM frameworks and GitHub projects.
5. Standards/open schemas (IFC, IDS, bSDD, etc.).
6. Current academic/research prototypes where relevant.
7. General-purpose infrastructure that can be adapted instead of rebuilt.

## Decision outcome

For each candidate subsystem, classify existing solutions as:

- REUSE — use directly.
- WRAP — keep it and add our safety/semantic layer.
- ADAPT — extend/fork/configure it.
- COMPOSE — combine several existing tools.
- BUILD_GAP_ONLY — write only the missing part.
- BUILD_CUSTOM — only when no existing solution satisfies the requirement after evidence-based comparison.

## Required comparison before BUILD_CUSTOM

Document:
- candidates searched;
- exact capabilities;
- gaps;
- licensing/cost;
- deployment constraints;
- performance;
- reliability;
- API/automation access;
- data ownership/exportability;
- integration cost;
- why custom code is still justified.

## Anti-NIH rule

Do not prefer our own implementation merely because we already started it.

Existing work should be treated as:
- benchmark;
- verifier;
- fallback;
- specialized deep layer;
- migration path;

if a better external implementation is found.

## Verification rule

Do not assume a product is superior from marketing numbers alone.

Example:
"733 tools" vs "150 commands" is not a valid comparison until tool granularity, semantics, coverage, batch behavior, geometry depth, performance and reliability are tested.

## Architecture rule

Prefer owning the unique architectural intelligence layer:
- project causal graph;
- normative graph;
- design intent;
- impact propagation;
- constraints;
- audit and safety;
- project decision logic.

Commodity integration layers should be reused when reliable.

## Trigger

This rule must be applied again whenever we are about to:
- create a new writer/reader;
- invent a new database/schema;
- build a solver/checker;
- implement a connector;
- create a requirements/equipment system;
- build a model router;
- build synchronization/versioning;
- build a BIM validation layer.

Search first. Compare. Then code only the justified gap.


## Full-cycle and project-library policy (2026-10-08)

The binding product goal is **full-cycle autonomous architectural project creation or completion through final documentation and engineer coordination**, not structural handoff as the terminal product. See [canonical goal and story convention](FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md).

Before each project, deliberate **extensive, source-verified prebuild research** should compile an applicable project-specific library pack from a large, indexed global catalogue. Expand *coverage of construction conditions*, not just numbers of similar details; reuse `details/v2.12` as a source and preserve its unresolved blockers. Full research is allowed to take much longer than a single live design edit when it materially reduces subsequent rework. Freeze sources, rules, versions, compatibility and unresolved obligations; incremental refresh when changed.

The architect uses `1 этаж` at `±0,000` for the first above-ground storey. Never infer that the AC29 internal `floorIndex` equals the architectural label; resolve from actual native story table and `skipNullFloor`.

LIRA-FEM (formerly LIRA-SAPR) is a candidate COM-controlled engineering subsystem. No solver result is a professional sign-off and no unsupported national norm edition may be assumed. Keep dependencies optional until a licensed end-to-end test proves them.
