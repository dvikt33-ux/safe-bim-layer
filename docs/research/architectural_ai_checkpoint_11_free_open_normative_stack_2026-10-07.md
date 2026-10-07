# Architectural AI checkpoint 11 — free/open normative stack and official-data adapters

Date: 2026-10-07
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp

## Why this checkpoint exists

GARANT demo access is temporary. This pass searched specifically for:
- zero-key / no-subscription machine interfaces;
- open legal corpora;
- free MCP adapters;
- open construction-standard datasets;
- state requirement registries;
- spatial/heritage machine data;
- update/version sources.

The goal is not to clone GARANT. It is to make GARANT optional.

## Executive result

A credible zero-cost baseline now exists, but it is **composed**, not one product.

### General Russian law
- Official Internet Portal of Legal Information (pravo.gov.ru) remains the authoritative publication source.
- The portal exposes public JSON endpoints used by community adapters without API keys.
- Those endpoints are not formally documented as a stable developer API, so they require contract tests/fallbacks.
- Open-source `pravo-mcp` already wraps them as MCP.
- `RusLawOD` provides a large current offline legal corpus for indexing/retrieval.
- `Russian-Law-MCP` provides a ready MCP/local SQLite accelerator but its bundled corpus freshness claims must be independently audited.

### Construction requirements / SP / GOST
- Стройкомплекс.РФ remains the strongest free state source for atomic construction requirement IDs/status/versions.
- protect.gost.ru remains the official free document/status/change-card source for SP/GOST.
- A new 2026 interface of the Requirements Registry is reported to provide rich filtering and XML/XLSX export; direct technical verification is still required before treating export as an API contract.
- A small open GitHub dataset `Akumsk/russian-construction-standards` can seed development/search but is too incomplete/stale to be authority.

### Spatial / historic context
- The Federal Spatial Data Portal (ФППД) exposes resource groups for ЕГРОКН and external-access/JSON surfaces.
- Official FPPD methodology supports map services such as TMS/WMTS; some portal resources expose external-access links.
- This is a strong candidate for a free spatial-regulation adapter.
- Coverage and field completeness must be checked layer-by-layer.

The resulting zero-cost architecture is strong enough that the normal interactive design runtime should not require a commercial legal service.

---

## Finding A — public pravo.gov.ru JSON endpoints, no API key

Open-source `AlsKozlov/ru-legal` contains `pravo-mcp` (Apache-2.0) and explicitly documents:
- no registration;
- no API key;
- source `publication.pravo.gov.ru/api/` for search/document text;
- source `ips.pravo.gov.ru/api/ips/` for versions;
- MCP tools for search, full document retrieval and a version at a date.

Its implementation currently uses:
- `/Documents`;
- `/Document/{eid}`;
- `/DocumentTypes`;
- `/SignatoryAuthorities`;
- IPS version endpoint.

### Important caveat

This is **not an officially documented public developer contract**.
The adapter authors say the response model was reverse-engineered and may break when the portal changes.

Their own May 2026 status file marked this integration YELLOW because of upstream TLS problems and a brittle IPS authentication detail.

Therefore:

**REUSE adapter code/idea, but wrap it in our own health/contract tests and never treat endpoint shape as guaranteed.**

### Recommended use

`pravo_public_adapter`:
- federal laws;
- decrees;
- Government resolutions;
- ministerial orders;
- official publication metadata;
- current/historical legal text where endpoint coverage permits.

Do not use it as a source for SP/GOST technical-standard text.

---

## Finding B — Russian-Law-MCP is useful but not current enough to be authority

`shodenis/Russian-Law-MCP` is Apache-2.0 and exposes:
- 12,369 federal statutes;
- 77,647 provisions;
- SQLite/FTS5 search;
- remote MCP endpoint;
- local npm package.

It is very convenient as a ready AI-search surface.

### Freshness audit

Its README presents automated freshness/update machinery, but:
- the bundled dataset metadata says last ingestion 2026-02-25;
- the inspected GitHub `check-updates.yml` schedule is weekly rather than daily;
- the public GitHub Actions run listing returned no workflow runs during this audit.

Therefore do **not** make it legal authority or freshness oracle.

Use it as:
- local search accelerator;
- provision/citation index;
- fallback/offline assistant;
- benchmark/reference implementation.

Every current critical result must be checked against a current official source.

---

## Finding C — ru-legal / pravo-mcp is the better building block than its full aggregator

The same `AlsKozlov/ru-legal` repo provides many legal MCPs and 145 skills.

Its own `MCP-STATUS.md` explicitly documents broken/partial integrations:
- some endpoints blocked/unstable;
- some were speculative;
- aggregator tool proxying was not yet implemented in that audit.

This honesty is useful.

Decision:
- consider **only the specific `pravo-mcp` adapter first**;
- do not import the entire legal MCP zoo into SBIM;
- apply the same capability/health matrix we use for BIM tools.

---

## Finding D — RusLawOD is a valuable offline corpus

Current `irlcode/RusLawOD` version 3.1 reports:
- 308,056 texts;
- about 198.8 million tokens;
- Russian legal acts and metadata from 1991 through 2026;
- state-source refresh on 2026-08-02.

The project was updated in September 2026.

Crucial legal caveat from the authors:
its main plaintext source is the state IPS "Законодательство РФ", but that representation itself is **not official publication** and does not have the same legal evidentiary status as signed official publication.

### Best role

Use RusLawOD for:
- offline FTS/vector indexing;
- entity/document discovery;
- corpus analytics;
- L0 Project Compiler retrieval;
- local model pre-processing.

Use pravo.gov.ru official publication / current authoritative source for final provenance.

This is potentially much more useful to us than repeatedly downloading general laws through commercial systems.

---

## Finding E — open construction-standard dataset exists

`Akumsk/russian-construction-standards` is an MIT/CC-BY open project with JSON metadata/text for Russian construction standards.

Current repository inspection found:
- 364 JSON files in `metadata/`;
- extracted page text, metadata, status/revision fields;
- scripts for extraction/status checks.

But:
- the repository's last code/data push was in May 2025;
- only a small subset of the Russian standards corpus is included;
- OCR/plain-text extraction loses diagrams, tables and formula structure;
- document status must be checked against official current sources.

Decision:
**REUSE as a development corpus / seed / benchmark only.**
Do not use as current normative authority.

Potentially useful for:
- parser tests;
- search prototype;
- clause/reference extraction development;
- comparison against our manually verified rule fixtures.

---

## Finding F — Стройкомплекс.РФ is even more valuable than the old interface suggested

Direct indexed state-registry pages verify that individual requirements contain:
- stable requirement ID;
- source document;
- status;
- publication date;
- safety aspects;
- version histories.

Examples in 2026 show requirements whose older versions are explicitly marked replaced.

### Reported new 2026 interface

A recent construction-industry report describes a new `/ntdrequirement` interface with:
- normal and advanced search;
- UIN;
- lifecycle stage;
- object type;
- territorial zones;
- document sections;
- requirement type;
- latest-version filter;
- programmatic-checkability flag;
- XML export;
- XLSX export.

This would be exceptionally valuable.

However:
- during this audit direct access to the new route had TLS/privacy errors in Opera;
- the XML/XLSX feature is therefore currently **SECONDARY-SOURCE CONFIRMED, PRIMARY-UI NOT YET VERIFIED**.

Do not code against it until we obtain one real XML/XLSX export and inspect its schema.

### Policy direction from Minstroy

The August 2026 Minstroy draft/explanatory material says machine-readable/machine-understandable registry information would be represented as XML schemas when content permits.

It also explicitly acknowledges that not all requirements can be converted into machine-understandable form.

That supports our constraint architecture:
- numeric/deterministic requirements can compile to executable Rule IR;
- qualitative/performance requirements need richer semantics/review;
- no "everything becomes one inequality" approach.

---

## Finding G — free official spatial/heritage data is more promising

The Federal Spatial Data Portal currently indexes a resource group:
`73_Сведения из ЕГРОКН (памятников истории и культуры) народов РФ`

with a layer for federal cultural-heritage objects.

The portal exposes "external access" and JSON views on resources.

Official FPPD/ЕЭКО methodology documents service delivery through standardized web-map interfaces such as TMS/WMTS. This shows the state spatial stack is designed for machine/GIS consumption rather than only human web pages.

### Caveat

One discovered heritage layer/resource view did not prove that every relevant object/zone is populated.
We need to test:
- feature count;
- fields;
- geometry;
- update date;
- federal vs regional coverage;
- heritage territories vs protection zones;
- historical settlements/protected panoramas.

### Decision

Promote FPPD to a first-class free `SpatialRegulationAdapter` candidate.

Do not rely solely on manually copied textual heritage descriptions.

---

## What replaces GARANT for free?

There is still no single free drop-in replacement with all GARANT editorial features.

But for our actual architecture, this combination is stronger than a single dependency:

### A. Federal/legal layer
`pravo.gov.ru public endpoints + pravo-mcp`
+
`RusLawOD offline corpus`

### B. Construction-rule layer
`Стройкомплекс.РФ Requirements Registry`
+
`protect.gost.ru`
+
`Minstroy official docs`

### C. Spatial/context layer
`FPPD / ЕГРОКН / regional GIS sources`

### D. Optional accelerators
`TechExpert`
`NormaCS`
`GARANT while available`

### E. Our persistent layer
`CanonicalRequirement + Rule IR + Project Rule Pack + provenance + hashes`

The commercial system becomes a quality accelerator/verifier rather than a runtime dependency.

---

## Revised source trust model

### AUTHORITY
Official publication/state registry/official standard status source.

### CURRENT_STRUCTURED_SOURCE
Current structured state/commercial source with stable IDs.

### CURATED_SECONDARY
TechExpert/NormaCS editorial enrichment.

### OPEN_CORPUS
RusLawOD, open construction datasets.

### COMMUNITY_ADAPTER
pravo-mcp, Russian-Law-MCP.

A lower-tier source can find a candidate but cannot by itself upgrade a rule to ACTIVE.

---

## Free-stack runtime architecture

### L0 / periodic refresh

```text
public sources
  pravo
  Stroykompleks
  protect.gost
  Minstroy
  FPPD
      |
open corpora
  RusLawOD
  construction dataset
      |
source adapters
      |
canonical identity
      |
legal/currentness checks
      |
Rule IR
      |
CompiledProjectKernel
```

### L2 interactive design

No network legal query for every BIM edit.

Use:
- cached Active Project Rule Pack;
- source/version hashes;
- validity envelopes.

### Refresh

Contract tests detect:
- API response changes;
- source version changes;
- stale local records.

Only dirty requirements/project bindings are rebuilt.

---

## New zero-cost adapter priorities

1. `pravo_public_adapter`
   - based on public JSON endpoints;
   - contract tests;
   - fallback to official publication URLs;
   - no API key.

2. `stroykompleks_requirement_adapter`
   - first test XML/XLSX export;
   - do not start with HTML scraping if exports are usable.

3. `protect_gost_adapter`
   - document/status/amendment metadata.

4. `ruslawod_local_index`
   - offline general-law retrieval.

5. `fppd_spatial_adapter`
   - heritage/context geometry.

6. Optional commercial adapters only after free baseline works.

---

## Search-before-build implications

Do NOT write:
- a generic federal-law text database;
- a generic FTS indexer from scratch;
- a generic legal MCP server;
- a static manually maintained list of all Russian legal acts;
- a custom GIS tile/vector service.

Reuse:
- pravo-mcp patterns;
- RusLawOD corpus;
- SQLite FTS / existing DB engines;
- state requirement IDs;
- FPPD services.

Write only:
- construction-specific normalization;
- canonical source reconciliation;
- legal/applicability semantics;
- source-health layer;
- Rule IR;
- project binding;
- normative -> project impact propagation.

---

## Next technical experiment: FREE-NORM-01

Use a single real project requirement chain around SP 464.

1. Find the enabling/amending legal acts through pravo public adapter.
2. Resolve SP 464 document/status through protect.gost and official Minstroy source.
3. Resolve atomic construction requirements in Стройкомплекс.
4. Compare against our previously verified manual SP 464 fixtures.
5. Build canonical IDs.
6. Change one source/version in the test fixture.
7. Confirm only the dependent Rule IR and project bindings become dirty.
8. Benchmark latency and source-call count.

This will tell us whether the free stack is good enough before purchasing any normative platform.
