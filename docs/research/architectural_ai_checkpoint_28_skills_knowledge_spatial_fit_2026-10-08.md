# Architectural AI checkpoint 28 — skills, knowledge packs, spatial fit
Date: 2026-10-08
Status: SOURCE AUDIT ONLY (no local/native execution)
Target: Archicad 29. Continues checkpoints 20–27.

## Executive finding
Separate four things:
- SKILL = domain procedure, prompting and preconditions
- CAPABILITY = versioned executable tool with authority and schema
- EVIDENCE = model measurements/source citations/currentness/applicability
- EVAL = regression proof of this skill operating with this tool on realistic tasks

A SKILL.md file is NOT an independently verified engineering function. Do not auto-install hundreds.

## A. DDC Skills
Source: https://github.com/datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction
Direct GitHub tree audit: 1,026 entries; 238 SKILL.md; only 3 .py/.ts/.js files as standalone files (code samples also occur inside Markdown); no recognizable tests/ or __tests__ directories detected by tree path filter. README mentions both 238 and 221; actual source file count is 238.
Relevant procedures: IFC QTO, document reporting, converter orchestration, BIM QA, multiagent estimates.
Critical audit flaw in example:
1_DDC_Toolkit/BIM-Analysis/bim-clash-detection/SKILL.md tests axis-aligned bounding box overlaps, not exact solids.
The distance labelled penetration depth/clearance is computed from Euclidean bbox-center separation; this is not penetration depth or clearance.
Such example must never issue authoritative BIM clash/severity PASS/FAIL.
The IFC-to-QTO sample is batch conversion to XLSX, not live BIM synchronization despite README claims.
MIT applies to skills; separate database/cost corpus can carry CC-BY-NC or other restrictions.
Disposition: REFERENCE_ONLY / SELECTIVE_PROCEDURES. Requires code-specific tests.

## B. ArchSight AIOS
Source: https://github.com/ArchSightLabs/archsight-aios
Direct source tree: 509 entries, 33 SKILL.md, distinct CLI/runtime schemas, capability registry, local stdio MCP adapters and tests.
Knowledge Pack v1.5 flow:
source JSON + source-register + standard-register + clause-map + entity-relation-map + eval questions + reviewer notes
 -> compiled knowledge-pack.json -> lookup/eval/norm_lookup.
Reference status found/not_found/conflict/inapplicable/error; applicability applicable/not_applicable/need_context; returns citations and sourceVersion.
Capability registry distinguishes implemented, implemented-reference-runtime and adapter-required; enforces owner agents, allowed skills, authority, evidence fields, blocking rules, human escalation.
Actual adapters include knowledge.norm_lookup and architecture health. Separate solver adapter depends on external archsight-solver.
Project itself explicitly says it is NOT a production normative database; synthetic fixture tests do not prove Russian code correctness; restricted texts not copied.
Disposition: REUSE Knowledge Pack governance concepts and fail-closed states; possible COLD/WARM curated project knowledge. Do not replace ACCORD/AEC3PO/SHACL or official Russian source authority. Pilot against real verified clauses.

## C. Pascal Editor
Source: https://github.com/pascalorg/editor
Actual 3D editor with local MCP; scene Site/Building/Level/Zone/Wall/Item; dirty-node updates; placement and spatial evidence workflows.
Skill furniture-fit requires real measurements, distinguishes nominal level heights from measured clear heights, uses read-only candidate assessment, reports unknown and does not claim untested door swing, height or delivery path.
AABB and default door keep-outs are indicative checks, NOT Russian normative thresholds or 3D clash certification.
No verified native Archicad29 round-trip. Do not install as second source of building geometry by default.
Disposition: reference for equipment placement quality gates and optional stand-alone comparison.

## D. Naming false positive
govtech-bb/bimstack is a Barbados government digital service design-agent framework, not Building Information Modelling. Exclude from BIM tools. Source: https://github.com/govtech-bb/bimstack.

## Revised architect skill architecture
Only a small task-specific set should be loaded:
PROJECT_BRIEF_AND_SITE
ARCHITECTURAL_SCHEME_AND_ROOM_PROGRAM
CSE_AND_STRUCTURAL_SYSTEM_SELECTION
CHANGE_IMPACT_AND_INTENT_PRESERVATION
EQUIPMENT_AND_DOOR_CLEARANCE
RUSSIAN_RULE_RETRIEVAL_AND_APPLICATION
DOCUMENTATION_COMPILER_AND_VIEW_COVERAGE
RELEASE_AND_REGRESSION_AUDIT

Each skill contract must name:
trigger/scope; typology and site; required evidence; current rule editions; capability IDs + schemas; read/preview/write authority; hard invariants; unknown/conflict handling; postconditions/readback; rollback; negative evals; latency tier.

Do not spin up 8 independent LLM calls per wall movement.
Use HOT/LIGHT graph + deterministic tools for normal edits, MEDIUM solver for repair, HEAVY research/evaluation for new conditions or milestones.
The agent role is a policy boundary and may be fulfilled by the same model.

## Immediate test backlog
SKILL-01 DDC clash false-positive fixture, native exact collision oracle
KNOWLEDGE-01 conflicting/obsolete Russian rules with context, provenance and need_context
FIT-01 room polygon + equipment rotation + door-swing/maintenance envelopes; forbid unsupported 3D approval
ROUTER-01 choose minimum skill set for wall move, window edit, equipment substitution, SP change
MUTATION-01 dry run/preview/rollback on disposable Archicad test PLN

## Adoption rule
DISCOVERED -> SOURCE_AUDITED -> SANDBOX_TESTED -> AC29_VERIFIED -> PRODUCTION_ACCEPTED.
Never say installed=verified. Major current blockers: lack of executed AC29 integration tests, test fixtures and benchmark measurements.

## Source links
https://github.com/datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction/blob/main/1_DDC_Toolkit/BIM-Analysis/bim-clash-detection/SKILL.md
https://github.com/datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction/blob/main/1_DDC_Toolkit/BIM-Analysis/ifc-qto-extraction/SKILL.md
https://github.com/ArchSightLabs/archsight-aios/blob/main/docs/v1.5.0-knowledge-pack-runtime.md
https://github.com/ArchSightLabs/archsight-aios/blob/main/runtime/capability-registry.json
https://github.com/pascalorg/editor/blob/main/skills/furniture-fit/SKILL.md
