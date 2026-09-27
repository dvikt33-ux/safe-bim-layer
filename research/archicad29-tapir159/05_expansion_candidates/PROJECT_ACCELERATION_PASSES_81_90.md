# Project acceleration research — passes 81–90

Sixth focused round. This round converts remaining research gaps into concrete contracts/policies rather than broad capability discovery.

No live Archicad writes were performed.

## Pass 81 — Project Profile should be versioned, hashable, and non-magical

A first machine-readable research draft is now stored at:

`00_master/project_profile_v0_1.schema.json`

The profile binds project standards to explicit compatibility/resource expectations instead of letting runtime code discover them ad hoc.

Core fields include:

- AC29/Tapir compatibility;
- seed project/template identity;
- story structure;
- libraries;
- Favorites and their dependencies;
- attributes/resources;
- Hotlink/GDL catalogs;
- annotation/document presets;
- global-operation policy.

This is an architecture proposal, not production schema yet.

## Pass 82 — reusable asset identity needs immutable source fingerprints

Recommended identity policy:

### Favorite
`element type + favorite name + source profile version + dependency fingerprint`

### Hotlink module
`role + immutable/versioned source path + SHA-256 + expected story structure`

### GDL object
`Main GUID + source/build version/hash`

### Library/package
`kind + name/path identity + availability + optional content hash/version`

This is safer than names alone and supports fast preflight caching.

## Pass 83 — native QA Issues need deterministic dedup keys

Proposed issue key:

`qa_rule_id + normalized exact offending GUID set + project/profile version`

Workflow:

1. run deterministic QA rule;
2. compute issue key;
3. search/read existing Safe-BIM-tagged issues;
4. create if absent, update/comment if present;
5. attach exact offending elements;
6. close/delete only under explicit lifecycle policy.

Reason: repeated QA runs must not flood Archicad with duplicate issues.

Tapir source supports issue GUIDs, tags/comments and exact element attachment/readback.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IssueCommands.cpp

## Pass 84 — Keynote identity should prefer native GUID after initial resolution

Proposed Keynote lifecycle:

- resolve existing item by project-controlled key/folder during preflight;
- once resolved/created, persist native Keynote GUID in the compiled recipe/job;
- modifications address GUID, not repeated fuzzy title search;
- user-manual tree edits trigger preflight conflict, not silent recreation.

Key/title are semantic lookup fields; GUID becomes execution identity.

Tapir's Keynote API exposes native folder/item IDs plus CRUD and autotext generation.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/KeynoteCommands.cpp

## Pass 85 — MEP needs a topology receipt, not an element receipt

Research receipt proposal:

```text
route_root_guid
requested_domain
requested_mep_system
requested_polyline
segment_guids[]
node_guids[]
ports[] { port_guid, element_guid, position, direction, connected_port_guid?, connected_element_guid? }
connection_side_effects { deleted_route?, split_route?, created_branch? }
```

Reconciliation reads the root route and exact topology. If a transport failure occurs during a split/merge/connect operation and exact side-effect identities cannot be established, state remains UNKNOWN_OUTCOME.

Source basis:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/MEPCommands.cpp

## Pass 86 — documentation invalidation should be dependency-based, not global

Research dependency policy:

- element geometry change -> invalidate its details and direct relations;
- zone-boundary-affecting change -> dirty related Zone update/QA;
- element referenced by associative dimensions/labels -> dirty those documentation nodes;
- view-setting/model-state change -> dirty affected drawing nodes;
- drawing source/update change -> dirty containing layout/publisher phase;
- annotation database change (Keynote/property/autotext) -> dirty dependent labels/texts/drawings, not model geometry.

The actual dependency edges must be discovered from exact GUID/native relations where available. Broad `rebuild everything` remains fallback only at explicit milestones.

## Pass 87 — global operations should have an approval matrix

Suggested default policy:

### Usually automatic after profile permission
- filtered reads;
- exact W1 create/modify;
- verified W2 relation writes;
- read-only QA.

### Require recipe/profile opt-in
- library set changes;
- geolocation changes;
- project save policy;
- broad zone rebuild;
- view/project-global settings.

### Require explicit per-run user approval
- story deletion/restructure;
- Hotlink relink/source replacement;
- destructive bulk delete;
- mass resource overwrite/import;
- publisher/external output when destination can overwrite deliverables.

This turns high-risk project-global behavior into visible workflow checkpoints.

## Pass 88 — AIResourceBroker should arbitrate local AI against CAD workload

Concrete broker responsibilities:

1. determine whether task can use deterministic recipe/rules;
2. if AI is required, check available RAM/VRAM and active high-load CAD/render processes;
3. start one provider/model on demand;
4. cap parallel inference at 1 by default;
5. pass only progressive capability schemas needed by the task;
6. return a typed plan;
7. unload/sleep/terminate the model;
8. only then allow physical BIM execution.

The broker owns process/resource policy, never BIM write authority.

Acceptance metric is not raw tokens/sec alone: measure user-visible planning latency plus RAM/VRAM release and Archicad/Twinmotion interference.

## Pass 89 — performance benchmark must be end-to-end and phase-aware

Proposed benchmark matrix on the user's Legion:

### Read path
- `GetDetailsOfElements` batch sizes 1/4/8/16/32/64;
- minimal verifier fields vs full details;
- relation/zone/collision reads.

### Write path
- one certified W1 create+readback;
- one exact modify+readback;
- SEO/trim relation write+readback;
- Hotlink instance placement+readback.

### Documentation
- section/elevation creation;
- dimension/label generation;
- drawing update;
- publisher run.

### Reuse
- create 100 elements individually vs equivalent repeated Hotlink module placement;
- Favorite-based create vs explicit large settings payload.

### AI
- cold start;
- planning latency;
- unload latency;
- RAM/VRAM before/peak/after;
- Archicad/Twinmotion responsiveness during inference.

Performance changes are accepted only if safety semantics stay identical.

## Pass 90 — final fast-path/slow-path split

### FAST PATH

For known project work:

`intent/selection -> recipe match -> parameter fill -> profile/resource preflight -> compile DAG -> execute certified ops -> batched readback -> incremental QA -> docs/publish`

No local AI process is needed.

### ASSISTED PATH

For a new/ambiguous task:

`intent -> on-demand AI planner -> typed recipe draft -> deterministic validation/compile -> unload AI -> FAST PATH executor`

### RESEARCH/UNSUPPORTED PATH

If a requested operation lacks a certified contract:

- no raw write fallback;
- produce an offline proposal/probe plan;
- certify separately;
- only later add to FAST PATH.

This separation is the strongest combined answer found for speed, low routine, low failure rate and maximum safe functional growth.

# Audit after passes 81–90

## Gaps converted into concrete artifacts/policies

- Project Profile has a first machine-readable schema draft.
- reusable asset identity policy is explicit;
- native QA Issue dedup lifecycle is explicit;
- Keynote execution identity policy is explicit;
- MEP topology receipt structure is explicit;
- documentation dirty-graph rules are concrete enough to prototype;
- high-risk global operations have a proposed approval matrix;
- AI runtime has a broker contract rather than being an always-on service;
- benchmark design covers whole workflow rather than isolated commands;
- fast/assisted/unsupported execution paths are separated.

## Remaining research/implementation uncertainty

1. empirical benchmark numbers on the user's machine;
2. a few narrow live semantics (Arc sign, Roof side, corrected Mesh Z, Morph body echo);
3. production validation of the Project Profile schema against real project/template resources;
4. exact MEP connection behavior under timeout/crash;
5. exact documentation invalidation coverage for every command;
6. migration/versioning rules once real Project Profiles/Recipes exist.

## Research saturation judgment

Broad source research is now strongly saturated for the stated objective. The remaining uncertainty is primarily empirical certification and implementation feedback.

A final audit should therefore consolidate the architecture, prioritize the shortest implementation path to measurable project-time reduction, and explicitly separate what is source-confirmed, architecture-proposed, and still requiring live evidence.
