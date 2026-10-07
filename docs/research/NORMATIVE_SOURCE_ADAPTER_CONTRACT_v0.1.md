# Normative Source Adapter Contract v0.1

Date: 2026-10-07
Status: DRAFT

## Goal

Use one stable internal interface over several normative-data providers.

## Text providers

Suggested operations:
- search_documents
- get_document_metadata
- get_requirement_or_clause
- list_versions
- get_incoming_references
- get_outgoing_references
- watch_changes
- export_fragment
- get_status_at_date
- get_registry_mapping

Providers may return UNSUPPORTED for capabilities they do not expose.

## Spatial providers

Suggested operations:
- query_constraints by project geometry/bbox/date/jurisdiction
- get_constraint_geometry
- get_constraint_metadata
- get_protection_subject
- list_constraint_versions
- get_primary_source

## Pipeline

ProviderRecord
-> IdentityResolution
-> NormalizedRequirement
-> ApplicabilityAudit
-> ReferenceEdgeClassification
-> RuleIRCompilation
-> ProjectBinding
-> ActiveProjectRulePack

A provider record is evidence, not automatically an executable hard rule.

## Canonical record

Keep:
- internal requirement ID;
- provider references;
- source document and clause/block;
- retrieved date;
- edition/redaction/effective interval;
- text hash;
- status;
- applicability;
- variables/units/conditions/exceptions;
- provenance;
- compiler version.

## Reference policy

Automatically discovered links begin as REFERENCE_CANDIDATE.
Typed edges such as DATED_REFERENCE, UNDATED_REFERENCE, USES_DEFINITION,
USES_TABLE, USES_FORMULA, SPECIALIZES, EXCEPTION_TO and OVERRIDES require
semantic verification.

## Rule status

DRAFT -> VERIFIED -> ACTIVE -> SUPERSEDED

LLM extraction alone cannot promote a rule directly to ACTIVE.

## Provider roles

- State registry and primary official sources: legal identity/status/provenance.
- TechExpert: candidate curated atomic requirement corpus and requirement workflow.
- GARANT: source text, redactions, reference/change verification.
- NormaCS: broad technical/legacy/status/succession cross-check.
- Spatial government/heritage sources: geographic applicability.

The canonical layer composes evidence across sources and records disagreement.
