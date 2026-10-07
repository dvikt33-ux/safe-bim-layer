# Architectural AI checkpoint 10 — zero-cost / low-cost normative fallback

Date: 2026-10-07
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp

## User constraint

Current GARANT demo access is temporary. The normative architecture must remain usable after GARANT access expires.

## Main conclusion

No currently verified service was found that provides a permanent **free** API key with the same combined capabilities as GARANT Connect:
- full-text legal/normative search;
- exact document/block retrieval;
- redaction/version history;
- incoming/outgoing legal links;
- document and fragment change monitoring;
- broad Russian legal + technical corpus.

Therefore the architecture must not depend on GARANT.

Use a layered fallback:

1. **Official/public state sources (free)** for legal identity, status and primary provenance:
   - Стройкомплекс.РФ Requirements Registry;
   - Росстандарт protect.gost.ru for ГОСТ/СП publication/status/change cards;
   - Минстрой / official publication portals for orders/amendments;
   - ЕГРОКН and other state spatial sources for heritage/context.

2. **TechExpert trial / future commercial evaluation**
   - currently offers temporary free access campaigns/demos;
   - Kodeks API exists, but no evidence found that permanent requirement-level API access/key is free;
   - potentially the best paid/partner replacement for curated atomic construction requirements.

3. **NormaCS Lite (free application)**
   - hundreds of thousands of document cards;
   - full-text/requisite search over catalog metadata;
   - only a limited subset of document texts is free;
   - statuses/texts are generally commercial;
   - NormaCS API/PRO is tied to paid products and is not a verified free web API-key service.

4. **Public/free web sources**
   - useful as redundancy/search, not authoritative API contract;
   - do not build production automation on undocumented scraping where avoidable.

5. **Our local Project Kernel cache**
   - cache only content we are legally allowed to cache;
   - preserve canonical IDs, status, source URL/ID, hashes, extracted verified Rule IR, and provenance;
   - do not require the commercial provider to be online during ordinary design-runtime work.

## Important findings

### GARANT

GARANT Connect requires an OAuth/Bearer token issued by the servicing organization.
It is not a generic permanently free API.
Its documented methods remain an excellent optional verifier/source while access exists.

### TechExpert / Kodeks API

TechExpert publicly confirms a developed Kodeks API and integration with CAD/enterprise systems.
Current pages also offer temporary free trials/campaign access (commonly around 7 days).
No public evidence found that Kodeks API or its requirement corpus provides a permanent free API key for private projects.

### NormaCS

NormaCS Lite is genuinely free to install/use for catalog-level work:
- 626k+ document cards reported on current Lite page;
- full-text/requisite search across indexed catalog;
- texts/status mostly commercial;
- a limited free document subset includes ESKD/SPDS materials.

NormaCS API is documented as COM/API functionality associated with NormaCS/NormaCS PRO, not as a free hosted API-key service.

### Стройкомплекс.РФ

Public requirement cards are free and include stable requirement IDs, statuses and versions.
A documented public developer API has not yet been verified.
Do not make production scraping the only access path.

### Росстандарт protect.gost.ru

Free official portal exposes ГОСТ/СП cards and publication/status information.
No documented public REST API key/service equivalent to GARANT was verified in this pass.

## Best no-cost architecture if GARANT disappears tomorrow

At L0 Project Compilation:

- query public state registries and official sources;
- use Opera/web/manual adapters where no stable API exists;
- capture stable IDs/status/versions/provenance;
- compile only the project's Active Rule Pack;
- store our own verified Rule IR + source hashes + provenance;
- optionally use TechExpert/NormaCS trials for cross-checking during research;
- never depend on those trials for interactive runtime.

At L2 Design Runtime:

- use the cached, versioned Active Project Rule Pack;
- no commercial normative service required for each wall/window edit.

At scheduled refresh / release audit:

- re-check official public sources;
- if paid verifier exists, use it;
- if not, use state sources + independent cross-checks and mark unresolved items NOT_VERIFIED.

## Product strategy

Priority is not "find one free GARANT clone".
Priority is:
**make the system provider-independent.**

A paid provider then improves:
- ingestion speed;
- coverage;
- change monitoring;
- legal/editorial metadata.

But loss of that provider does not disable the project.

## Future research targets

Search specifically for:
- official Стройкомплекс developer/bulk interface;
- Rosstandart/Federal Standards Fund open-data/API interfaces;
- current public/open datasets for legal publication metadata;
- university/educational TechExpert/NormaCS access available to students;
- APIs bundled with BIM/CAD educational licenses;
- regional ISOGD open APIs for site/context data.

## Gate

Do not commit to a paid normative platform before checking:
- student/academic license;
- trial duration;
- API entitlement;
- export/cache rights;
- rate limits;
- requirement-level granularity;
- offline/local availability.
