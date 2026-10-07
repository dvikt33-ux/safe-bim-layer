# Architectural AI checkpoint 09 — Russian normative platforms deep audit

Date: 2026-10-07
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp

## Executive conclusion

The normative subsystem should NOT be built as a private hand-maintained copy of all Russian SP/GOST/PZ/heritage documents.

The strongest architecture after this audit is a **federated normative source layer**:

- **Стройкомплекс.РФ / Реестр требований** — authoritative state registry identity/status/version/applicability role.
- **Техэксперт Реестр требований + SMART/Kodeks API** — strongest current candidate for a ready-made granular requirements corpus, requirement workflows, history and project-specific requirement sets.
- **ГАРАНТ Connect API/MCP** — strongest currently documented programmable source for legal/document text, block-level retrieval, incoming/outgoing reference discovery, redactions and precise change monitoring.
- **NormaCS** — broad technical standards/document corpus with status, succession, amendments, monitoring, comparisons, CAD integrations and an advertised open API.
- **official Minstroy/Rosstandart/legal sources** — final primary provenance/status verification.
- **ЕГРОКН / spatial-government systems / ISOGD-class sources** — separate spatial regulation source family for heritage, territorial and site constraints.

No single commercial provider should become the single source of truth.

Our custom value is the **normalization, legal/applicability graph, cross-provider identity, executable rule compiler and binding to project variables/BIM**, not bulk PDF transcription.

---

## Critical legal-date correction

An earlier research pass repeated the former transition date **1 March 2026** for use of the Requirements Registry in project-documentation expertise.

This is now stale.

Current legal state in October 2026:
- the transition was postponed;
- the relevant amendments to expertise rules now enter into force **1 March 2027**;
- Government Resolution No. 1593 was correspondingly amended by Resolution No. 179 of 21 February 2026;
- current explanatory materials prepared by Minstroy in August/September 2026 also use **1 March 2027**.

This correction is important because older 2025 TechExpert promotional material still says 1 March 2026.

Rule for our system:
**provider marketing text can never override current primary legal status.**

---

## Provider A — Стройкомплекс.РФ / Реестр требований

### Confirmed current capabilities

Public requirement cards expose:
- stable requirement ID;
- registry section;
- status, including `Действует` / `Заменен`;
- publication date in the registry;
- source document ID/type/name;
- safety aspects where available;
- a Versions section;
- multiple historical versions on some requirements.

Examples observed:
- SP 485 requirement ID 158155 has version 1 marked replaced and version 2 current.
- SP 251 requirement ID 198334 exposes three versions.
- 384-ФЗ requirements are represented as individual requirement records.

Therefore this is not merely a list of document titles; it already has a requirement-level identity/version model.

### XML

Some registry/search surfaces expose an XML field/file, but it is not populated on every requirement card and public browser behavior is inconsistent.

Conclusion:
- do not assume complete XML availability;
- capture the exact XML schema and download behavior with an explicit technical test before using it as a bulk ingestion contract.

### Strength

Highest legal/applicability importance for the coming expertise regime.

### Weakness / unknown

No stable public developer API was verified in this pass.
Bulk export/query behavior remains UNKNOWN.
Current public site/browser behavior is inconsistent enough that it must not be our only operational interface.

### Decision

**REUSE as authoritative registry identity/status/applicability source.**
Build an adapter, but do not depend on undocumented scraping as the only transport.

---

## Provider B — Техэксперт Реестр требований: Строительство

### Confirmed current capabilities

Official current product documentation says:
- it contains an expert-selected targeted base of construction requirements;
- requirements include documents that are present in the state Стройкомплекс.РФ Documents Registry;
- requirements are linked with classifiers including KSI / capital-construction-object classifiers;
- it reports whether a requirement is included in the official Стройкомплекс.РФ registry;
- users can form project-specific requirement sets;
- users can work with current requirements;
- team folders are supported;
- checklists/control assignments can be formed;
- selected requirements can be saved to files;
- links to requirements can be placed in internal documents for subsequent actuality control.

A 21 September 2026 TechExpert partner publication states the current system contains:
- **more than 400,000 requirements**
- from **3,200 normative acts**
- including GOSTs, SPs, technical regulations and orders.

The new `Требование на контроле` service notifies a user when the exact controlled provision changes or is cancelled.

### Requirement revision history

`Ревизии требований` is available and tracks requirements changed after 1 May 2025, allowing comparison of requirement text across revisions.

### Export

Current TechExpert materials confirm requirement exports to at least PDF / RTF / XLSX in its requirements products.

### SMART representation

TechExpert's SMART stack describes normative documents as data containers containing:
- human-readable text;
- deeply structured text;
- metadata;
- editions/redactions;
- attachments including 3D models.

Requirements can be:
- extracted from structured text;
- attributed;
- classified;
- grouped into registries;
- change-tracked;
- exported/transferred into external software, including CAD.

This is extremely close to the normalized requirement layer we originally planned to build manually.

### API/integration

Official TechExpert integration documentation confirms:
- a developed `Kodeks API`;
- individual integration with systems including CAD/CAM/CAE/CAPP/PDM/CRM/PM/MDM/RM;
- retrieval of document information, search, status/currentness workflows and data exchange.

### Major unknown

Public documentation does **not** yet prove that the commercial API exposes the full requirement-level SMART data model directly.

Required demo/API questions:
1. Can API return one requirement by stable requirement ID?
2. Can it return the exact source clause/block?
3. Does API expose requirement revision history?
4. Does it expose official Стройкомплекс requirement ID linkage?
5. Are classifier IDs returned?
6. Are requirement-to-requirement/document references exposed?
7. Can project-specific requirement sets be created/read through API?
8. Can exact controlled requirements be subscribed/monitored through API?
9. What export formats/limits/rights apply?
10. Can requirement text/data legally be cached locally in our Project Kernel?
11. Is Kodeks API licensed separately?
12. What are rate/seat/server restrictions?

### Decision

**TOP PRIORITY DEMO / API AUDIT.**
If requirement-level API/export rights are strong, use TechExpert as the primary curated requirement corpus instead of manually normalizing thousands of clauses.

---

## Provider C — ГАРАНТ Connect API 2.3.0 + mcp.garant.ru

This is the most clearly documented programmable source found in this audit.

### Confirmed REST capabilities

- full-text search: `POST /v2/search`;
- find occurrences/blocks inside a document: `POST /v2/snippets`;
- detect links to normative documents in arbitrary text: `POST /v2/find-hyperlinks`;
- export full document HTML / RTF / ODT / PDF;
- export an individual document block as HTML;
- retrieve document metadata: `GET /v2/topic/{topic}`;
- retrieve redaction/version list: `GET /v2/redactions/{topic}`;
- document change monitoring: `POST /v2/find-modified`;
- exact fragment/block change monitoring: `POST /v2/block-on-control/changed`;
- query incoming/outgoing document/block relationships with the advanced query language using `Correspondents(...)` and `Respondents(...)`;
- inspect current API limits.

### MCP

`mcp.garant.ru` is an official MCP wrapper over the same REST API.

Documented tools include:
- `garant_search`;
- `garant_snippets`;
- `garant_find_hyperlinks`;
- document/block export;
- `garant_find_modified`;
- `garant_block_changed`;
- document metadata/redactions;
- limits.

This is directly compatible with our planned model/tool gateway architecture.

### Authentication

Requires a Bearer API token issued by the servicing GARANT organization.

Important:
**browser authorization / normal GARANT subscription must not be assumed to include API entitlement.**

### Architectural value

GARANT can give us:
- exact source text/block;
- document identity;
- redactions;
- change events;
- source-reference graph seeds;
- fragment-level control.

`Respondents/Correspondents` is particularly valuable for constructing/documenting normative-reference edges.

### Limitation

The API is a legal/document source, not a ready-made deterministic building-code solver.

`find-hyperlinks` detects references; it does not prove the semantic edge type:
- DATED_REFERENCE;
- UNDATED_REFERENCE;
- SPECIALIZES;
- EXCEPTION_TO;
- DEFINES_TERM;
etc.

Our semantic compiler still has to classify/verify these relationships.

### Limits

The API explicitly exposes `/v2/limits`, and public documentation notes product-specific usage restrictions.
Do not design bulk ingestion assuming unlimited extraction.

### Decision

**REUSE / WRAP.**
Excellent source-verification and change-monitor layer.
Potentially a normative-reference graph seed.
Not the sole bulk corpus backend.

---

## Provider D — NormaCS

### Confirmed capabilities

Current NormaCS materials advertise:
- current statuses;
- succession/replacement relationships;
- amendments;
- daily updates;
- texts and scans;
- change notifications;
- document comparisons;
- history/audit;
- **open API**;
- integrations with nanoCAD, MS Office, AutoCAD and KOMPAS-3D.

The interface includes:
- `Документы на контроле`;
- status-change notifications;
- succession graphs and recommended replacements;
- changes incorporated into text after effective date;
- manually prepared expert comparisons for important predecessor/successor documents.

### Strength

Very broad technical-document/document-history environment, valuable for:
- legacy norms;
- technical standards;
- old/typical series;
- succession;
- cross-reference/currentness verification.

### Unknown

Public pages found in this pass do not document the open API schema sufficiently to prove:
- clause-level requirement objects;
- requirement-level stable IDs;
- requirement revision endpoints;
- bulk API;
- requirement graph export.

### Decision

**REQUEST API DOCS / DEMO.**
Likely useful as a broad independent technical corpus.
Do not rank above TechExpert Requirements for atomic requirement management until API granularity is proven.

---

## Provider E — official Minstroy / Rosstandart / legal sources

Role:
- primary source/provenance;
- status verification;
- amendments/orders;
- XML schemas for official construction-document exchange.

Minstroy publishes XML schemas for project-documentation sections.

Do not expect these sites alone to provide the ergonomic requirement corpus/project workflow that commercial platforms provide.

Decision:
**always preserve as primary-source verification layer.**

---

## Separate but mandatory source family — spatial/context regulation

Textual standards are only one side of the project.

For historic/context constraints we also need a `Spatial Regulation Adapter Layer`.

### ЕГРОКН / Ministry of Culture

Public ЕГРОКН map records can expose:
- registration ID;
- heritage category/type;
- protection subject;
- boundary descriptions;
- protected views and composition characteristics.

Observed records include detailed protected-view and spatial-composition text.

### Why separate from normative text

A project can be legally constrained because its coordinates intersect:
- heritage territory;
- protection zone;
- historic settlement;
- protected landscape/view;
- other territorial restrictions.

The applicability trigger is spatial intersection, not merely document classification.

Future architecture:

`site geometry`
  -> `spatial regulation sources`
  -> `applicable geographic constraints`
  -> `context graph`
  -> `facade/massing/material/height intent constraints`.

Decision:
**build source adapters; do not manually retype territorial constraints into project notes.**

---

## Recommended provider role architecture

### Tier 1 — authoritative registry/status

`Стройкомплекс.РФ`
`official Minstroy/Rosstandart/legal sources`

Use for:
- legal identity;
- registry inclusion/status;
- applicability date;
- primary provenance.

### Tier 2 — structured requirement corpus

`Техэксперт Реестр требований / SMART`

Use if API/export rights confirm:
- atomic requirements;
- classifications;
- project requirement sets;
- revision history;
- currentness control.

### Tier 3 — independent legal/document verification

`ГАРАНТ API/MCP`

Use for:
- source text;
- redactions;
- references;
- controlled fragments;
- change confirmation.

### Tier 4 — broad technical corpus and legacy/independent cross-check

`NormaCS`

### Tier 5 — spatial/context sources

`ЕГРОКН / state/regional spatial systems / ISOGD-class sources`

---

## Why provider federation is better than choosing one database

A single vendor can have:
- licensing limits;
- API gaps;
- incomplete classification;
- stale integration metadata;
- different update timing;
- service outage;
- commercial lock-in.

Therefore normalized internal records keep multiple provider references:

`CanonicalRequirementId`
- official_registry_ref;
- TechExpert_ref;
- GARANT_topic/entry;
- NormaCS_ref;
- primary_source_ref;
- text_hash;
- edition/effective interval;
- provenance and last verification.

Disagreement is represented explicitly; it is never silently resolved by taking whichever provider answered first.

---

## Normative ingestion pipeline

`Provider source`
-> `SourceRecord`
-> `Canonical identity resolution`
-> `NormalizedRequirement`
-> `Legal/applicability audit`
-> `Reference-edge classification`
-> `Rule IR compilation`
-> `project binding`
-> `Active Project Rule Pack`.

Important:
**provider requirement text is not automatically an executable rule.**

Example:

Text requirement
-> identify variable/domain/conditions/exceptions
-> classify HARD_MIN/HARD_MAX/etc.
-> attach source/provenance
-> deterministic test where possible
-> human/independent review for critical rules
-> ACTIVE.

LLM extraction can produce DRAFT only.

---

## New internal source-adapter contract

Every textual provider adapter should aim to expose:

- `search_documents(query, filters)`
- `get_document_metadata(provider_document_id)`
- `get_requirement_or_clause(provider_requirement_id)`
- `list_versions(id)`
- `get_incoming_references(id)`
- `get_outgoing_references(id)`
- `watch_changes(ids, since)`
- `export_fragment(id)`
- `get_legal_status(id, at_date)`
- `get_registry_mapping(id)`

Adapters are allowed to return `UNSUPPORTED`; the canonical layer handles heterogeneous providers.

Spatial adapters use a separate contract:
- query by geometry/bbox;
- retrieve protected-zone geometry;
- retrieve legal source/protection subject;
- version/effective interval;
- exact spatial provenance.

---

## Provider capability matrix — current confidence

| Capability | Стройкомплекс | TechExpert | GARANT API/MCP | NormaCS |
|---|---|---|---|---|
| requirement-level identity | PASS | PASS | PARTIAL (block/entry) | UNKNOWN |
| versions/history | PASS | PASS | PASS | PASS doc-level |
| exact requirement monitoring | no public API proven | PASS product; API UNKNOWN | PASS fragment control | PARTIAL/UNKNOWN granularity |
| project requirement sets | no | PASS | no | not primary |
| machine API | UNKNOWN public | PASS Kodeks; requirement endpoints UNKNOWN | PASS REST+MCP | PASS advertised, docs needed |
| reference discovery | PARTIAL | likely/UNKNOWN API | PASS seed via links/respondents/correspondents | PASS doc links; API UNKNOWN |
| bulk-corpus suitability | UNKNOWN | likely commercial | constrained by API plan | likely local/server, API unknown |
| official-registry authority | PRIMARY | mapping/helper | verifier | verifier |
| atomic requirement curation | state registry | EXCELLENT | source blocks | UNKNOWN |
| spatial/context data | no | no | textual only | textual only |

This table must be updated from hands-on demos/API docs before purchase or deep integration.

---

## Buy/use vs build decision after this audit

### Do NOT build from scratch

- full-text normative document corpus;
- document status/redaction service;
- requirement history UI;
- generic requirement folders/checklists;
- generic document-control notifications;
- document hyperlink parser if GARANT/TechExpert already provides a reliable endpoint;
- full normative search engine.

### Build our integration/intelligence gaps

1. provider adapters;
2. canonical cross-provider IDs;
3. legal/applicability semantics;
4. typed normative reference graph;
5. executable Rule IR;
6. bindings between rule variables and project/BIM data;
7. normative change -> project impact propagation;
8. spatial-context applicability graph;
9. provenance/conflict resolution;
10. project-specific Active Rule Pack compiler.

---

## Immediate experiments

### Experiment N1 — GARANT API/MCP entitlement

Ask servicing organization for:
- Connect API/MCP token availability;
- plan limits;
- rights to SP/GOST corpus in subscribed package;
- local caching rights;
- automated change-monitoring usage.

Then test on SP 464:
- search;
- document metadata;
- snippets;
- block export;
- redactions;
- Respondents/Correspondents;
- fragment control.

### Experiment N2 — TechExpert demo/API

Request demo specifically for:
- Реестр требований: Строительство;
- SMART;
- Kodeks API.

Do not accept a generic product demo.

Require an API proof using one real SP:
- get atomic requirement;
- get source clause;
- get revision;
- get official registry mapping;
- export/read through API;
- monitor one requirement;
- retrieve classifications.

### Experiment N3 — Стройкомплекс registry adapter

Use a small set of known IDs from SP 1 / SP 54 / SP 118 / SP 464:
- capture stable requirement IDs;
- version histories;
- status changes;
- test any downloadable XML;
- inspect network/API behavior only through allowed/documented interfaces;
- do not build production scraper before terms/technical interface are clear.

### Experiment N4 — NormaCS API

Request:
- open API documentation;
- demo;
- clause/document ID model;
- version/status API;
- succession links;
- change subscriptions;
- export rights.

---

## Stop/go gate for manual normalization

Pause large-scale manual SP-to-YAML normalization until N1–N4 have been evaluated.

Existing normalized rules are retained as high-value:
- regression fixtures;
- reference examples;
- accuracy benchmarks;
- seed Rule IR;
- cross-provider comparison cases.

They are not wasted.

---

## Key architectural impact

The normative system now mirrors the BIM strategy:

For Archicad:
`HuskyBIM / native tools / dRofus / existing software`
-> our causal/safety layer.

For regulations:
`TechExpert / GARANT / Стройкомплекс / NormaCS / official sources`
-> our canonical/legal/causal rule layer.

Same principle:
**reuse commodity infrastructure; own the architectural intelligence.**
