# Architectural AI checkpoint 03 — context constraints and model capacity

Date: 2026-10-07
Status: intermediate research checkpoint, not final instruction.

## New mandatory layer: context / heritage / urban regulation

Architectural intent is not formed only by the designer. External context can legally constrain the intended image of the building.

The project graph must therefore include a CONTEXT_REGULATION layer above facade/envelope decisions.

Typical sources:
- historic settlement subject of protection;
- heritage protection zones;
- territorial zoning / PZZ;
- GPZU and site restrictions;
- protected panoramas and view corridors;
- red lines and building lines;
- height envelopes;
- silhouette / proportions;
- permitted or restricted facade materials;
- color requirements;
- rhythm / scale / parcel structure;
- signage, parking, landscaping and public-realm constraints.

For historic settlements, 73-FZ requires preservation of the subject of protection and allows urban-planning regulations to constrain building size/proportions, materials, color, planning structure, panoramas and other architectural characteristics.

Therefore:
EXTERNAL_CONTEXT_INTENT
  -> constrains
PROJECT_ARCHITECTURAL_INTENT
  -> constrains
MASSING / ENVELOPE / FACADE / ROOF / OPENINGS / MATERIALS

A protected external rule can override a preferred internal design intention.

## Context rule types

Add relation/rule categories:
- CONTEXT_APPLIES_TO_SITE
- HERITAGE_PROTECTION
- VIEW_CORRIDOR
- SILHOUETTE_LIMIT
- HEIGHT_LIMIT
- BUILDING_LINE
- MATERIAL_RESTRICTION
- COLOR_RESTRICTION
- PROPORTION_RESTRICTION
- RHYTHM_RESTRICTION
- PARCEL_PATTERN
- STREET_FRONTAGE_RULE
- PROTECTED_VIEW
- LANDSCAPE_CONSTRAINT

Each rule must keep exact source, spatial extent, edition/status, applicability and relaxation policy.

## Architectural intent hierarchy

Architectural intent must be split into:
1. EXTERNAL / CONTEXT-IMPOSED intent and constraints;
2. DESIGNER LOCKED intent;
3. DESIGNER PROTECTED intent;
4. PREFERRED intent;
5. FREE design space.

External legally binding constraints are not merely an aesthetic score.

## Computational architecture conclusion

GPT should not hold the whole building, all standards and all dependency edges in prompt/context at once.

GPT-5.6 Sol High should act as orchestration/reasoning layer:
- interpret design goals;
- choose which subsystem must run;
- compare candidate states;
- explain conflicts;
- decide escalation paths;
- preserve architectural intent.

Persistent state and exact calculations must live outside the model:
- typed project graph;
- normative graph;
- spatial index;
- rule database;
- solver;
- caches;
- Archicad/IFC model.

The model receives only the relevant subgraph / rule subset / candidate deltas for the current transaction.

This is necessary for reliability and speed.

## Capacity policy

Do not ask the model to:
- remember every rule;
- recalculate the whole building from prose;
- inspect the entire graph for every change;
- act as sole compliance checker.

Use:
changed entity
-> impact cone
-> affected subgraph
-> exact deterministic checks
-> candidate states
-> GPT evaluation
-> commit only after PASS.

## Next implementation research

Prototype a context-aware transaction:
1. site is within a historical settlement / protected context;
2. context rules define height, silhouette, material and facade constraints;
3. user requests an internal area increase;
4. solver considers internal wall, bearing wall and facade-opening alternatives;
5. candidates violating protected facade/context rules are rejected;
6. candidate with more operations is allowed if it preserves the protected architectural image and all hard constraints.
