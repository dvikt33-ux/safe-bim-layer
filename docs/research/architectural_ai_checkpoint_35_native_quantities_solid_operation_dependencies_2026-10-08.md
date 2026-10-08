# Architectural AI checkpoint 35 — Native Quantity Kernel & Solid Operation dependency-aware quantities
Date: 2026-10-08
Status: RESEARCH ONLY / AC29 LIVE NOT TESTED
Target: Archicad 29 only; single currently open PLN; read-only until explicit live experiment
Branch: feature/working-archicad-mvp

## 0. Integration with parallel studies, not duplication
Parallel research already documented:
- checkpoint 29 native collisions and Difference Generator;
- checkpoint 30 MEP System Browser calculated columns;
- checkpoint 31 dynamic IFC HookManager export;
- checkpoint 32 Navigator Add-On viewpoints and Activity/Equipment room-fit;
- checkpoint 33 semantic-object event invalidation;
- checkpoint 34 cross-representation release witness.
This checkpoint adds an unaddressed **quantitative source-of-truth read path** and the **SEO dependency edges** needed for stable quantities, details, estimates, schedules and issued drawings.

## 1. First-party quantity engine: REUSE, do not implement by recomputing triangles
Graphisoft documented:
- ACAPI_Element_GetQuantities(elemGuid, params, quantities, mask): quantity fields for a single element;
- ACAPI_Element_GetMoreQuantities(elemGuids, params, quantities, mask): batched elements of **the same type**;
- ACAPI_Element_GetSurfaceQuantities(elemGuids, coverElemGuids, quantities): element-part exposed surface areas optionally excluding cover elements;
- ACAPI_Element_GetComponents(elemGuid, components) and component property reads, where supported.
The API has element and composite/skin quantities; API_Quantities additionally supports element-part results (e.g. multiplane roofs and Morph parts).
Performance optimization is explicitly supported through quantity field masks.
These APIs predate AC29; exact local AC29 headers and runtime must be compiled/tested.

Official:
https://archicadapi.graphisoft.com/documentation/acapi_element_getquantities
https://archicadapi.graphisoft.com/documentation/acapi_element_getmorequantities
https://archicadapi.graphisoft.com/documentation/acapi_element_getsurfacequantities
https://archicadapi.graphisoft.com/documentation/api_quantities
https://archicadapi.graphisoft.com/documentation/api_quantitiesmask
https://archicadapi.graphisoft.com/documentation/acapi_elemcomponent_getpropertydefinitions

## 2. Important semantics: do NOT collapse area and volume types
API_WallQuantity separately exposes:
- volume / volume_cond / grossVolume;
- surface1/2/3 and grossSurf1/2;
- emptyHolesVolume / emptyHolesSurf1/2;
- windowsSurf / doorsSurf / emptyholesSurf;
- area / perimeter;
- length, centerLength, refLineLength;
- skin quantities.
Their semantics are distinct. Each rule must ask for an explicit quantity family and interpretation. Never use wall surface in place of zone floor area, or exposed surface in place of gross envelope area.

Source: https://archicadapi.graphisoft.com/documentation/api_wallquantity

## 3. CRITICAL: opening threshold affects wall measurements
API_QuantityPar.minOpeningSize is the minimum opening area in **m²** below which an opening is not subtracted from wall surface quantities. It is ignored for non-wall elements.
This must enter the query contract, cache key, witness/provenance and check settings. It is incorrect to silently reuse a cached wall net-surface result generated with a different minOpeningSize.
Source: https://archicadapi.graphisoft.com/documentation/api_quantitypar

## 4. Exposed surface requires explicitly declared cover elements
ACAPI_Element_GetSurfaceQuantities accepts coverElemGuids; overlapped surface area can be subtracted from reported exposed surfaces. Consequently:
- same target GUID with different cover set can yield different values;
- the cover set and its revision must enter cache dependencies;
- zero cover elements means a DIFFERENT question from “what is visible after slabs/adjacent elements are accounted for”.
Surface-quantity result is not a universal façades/painting estimator without a policy for which surfaces and covers matter.
Source: https://archicadapi.graphisoft.com/documentation/acapi_element_getsurfacequantities

## 5. SEO native dependency edges: REUSE
Existing first-party:
- ACAPI_Element_SolidLink_GetOperators(targetGuid, out operators);
- ACAPI_Element_SolidLink_GetTargets(operatorGuid, out targets);
- ACAPI_Element_SolidLink_GetOperation(target,operator,out operation);
- ACAPI_Element_SolidLink_GetFlags(target,operator,out flags).
Read access to SEO relations supports an explicit dependency graph:
  operator changes => affected target quantities / evaluated geometry / finish surface / section & detail may become stale.
Direction matters. An operator modifies a target; inverse does not follow automatically.
An SEO link is NOT equivalent to a generic collision, native wall junction, trimming, nor absence of clash.
Some links/operations and hotlink edit restrictions require testing.
Sources:
https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_getoperators
https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_gettargets
https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_getoperation
https://archicadapi.graphisoft.com/documentation/acapi_element_solidlink_getflags

## 6. Fast read design and cost model
HOT: events + changed GUID sets + GetHeader only for lightweight type/story/layer/stamp (not authoritative global freshness).
WARM: GetQuantities/GetMoreQuantities for the precisely requested quantity mask, GetComponents and connected/SEO relationships, limited cover set, actual Schedule/Zone readback.
COLD: evaluated geometry Model Dump only where the native scalar quantities cannot prove e.g. interference shapes, penetration profile, detail topology or geometric fitting.
Do not claim native quantity calls are faster until AC29 benchmark measures wall-count normalized latency and consistency.
Official Element Overview explicitly advises filtered enumeration/header read rather than conversion of every element:
https://archicadapi.graphisoft.com/documentation/element-overview

## 7. Canonical fact schema
Example (values intentionally absent):
```yaml
fact_kind: quantity
target_guid:
element_type:
quantity_family: wall.grossVolume | wall.volume | wall.surface1 | wall.emptyHolesSurf1 | roof.segment_volume | surface.exposed
native_field:
unit: m3 | m2 | m
query_params:
  min_opening_size_m2:
  cover_element_guids: []
  selection_filter:
  quantity_mask_fields: []
  renovation_filter:
dependencies:
  - target_guid
  - seo_operator_guids
  - cover_element_guids
  - related_building_material_guids
  - relevant_calculation_preferences
source: AC29 native quantities
model_revision_or_stamps:
evidence:
  last_native_readback:
  consistency_check:
status: PASS | FAIL | STALE | NOT_ASSESSABLE | BLOCKED
```
The schema is a candidate, not an existing implementation.

## 8. Source-of-truth & numerical consistency invariants
(1) Programmed Area (requirement) != actual measured Zone area (result).
(2) Actual dimensions -> geometry -> native quantity -> schedules -> drawings -> issued PDF/IFC. Downstream numbers must not be independently invented.
(3) A quantity field must retain unit, source API, query arguments, rule revision and exact element identities.
(4) A rendered label / schedule value / IFC QTO / estimate may each have different scope or rounding, and need an explicit normalization/coverage mapping before equality checks.
(5) If native calculation or provider mapping fails, status NOT_ASSESSABLE/BLOCKED, never PASS by triangulated approximation.
(6) Property and schedule equations may use preferences/filters; include relevant environment settings in invalidation.

## 9. AC29 read-only tests (no PLN editing)
QTO-01 One wall: request wall volume, grossVolume, surface1, grossSurf1, opening surfaces; validate units, difference and expected semantics against Archicad interactive schedule.
QTO-02 Group by element type: batched GetMoreQuantities vs single GetQuantities; compare values and total elapsed.
QTO-03 Vary minOpeningSize for wall with small/large existing openings (if fixture exists); observe correct scope and differences.
QTO-04 Existing slab-over-wall: expose surfaces with and without declared slab covers; no fabricated exposed-area semantics.
QTO-05 Multilayer wall: inspect element and skin/component quantities, map to BM GUID, reconcile layer descriptions.
QTO-06 Existing roof and Morph: inspect supported elemPartQuantities, check roof plane vs Morph floor specificity.
QTO-07 SEO chain (if available in project): enumerate operator -> target, record operation+flags; show dependencies.
QTO-08 Environment: record Renovation / Design Option / view scope; ensure fact type records filters and preferences.
QTO-09 Compare reading 10/100/1000 walls to full current baseline dump: elapsed, answer bytes, missing rates and CPU burden.
QTO-10 Reconcile native quantities vs user schedule vs BIM model geometry only where needed. Report mismatches, do not silently choose one value.
QTO-11 Failure test: nonexistent/deleted GUID, bad element type in batch, unsupported component or quantity; return typed error, no blanket zero.
QTO-12 Re-read same set twice with stable state; check deterministic values and provenance.

## 10. Controlled mutation tests LATER, only with user permission on scratch project
QTO-MUT-01 edit wall opening size / readback and verify invalidated quantity & dependent schedule.
QTO-MUT-02 modify SEO operator while target header might remain stable; verify target quantities invalidated via SEO graph.
QTO-MUT-03 change composite/Building Material calculation inputs, make sure quantity cache invalidates and releases are blocked pending recompute.
No work on production or source PLN during research phase.

## 11. Acceptance gates
- AC29 headers compile and exact ABI matches installed AC29;
- typed native quantities map correctly into canonical units/semantics;
- no silent mismatches vs native schedule for controlled fixtures;
- false negatives for affected SEO/cover dependencies identified;
- no custom triangle QTO engine needed for supported scalar fields;
- performance and error rate measured against full Model Dump baseline (previously 5,296 elements / 9,261 bodies / ~105MB / 12.85s; project-specific historic values, not current measurements);
- any unverified or partly supported calculation is reported NOT_ASSESSABLE.

## 12. Reuse decision
REUSE NOW AS RESEARCH CANDIDATE: Archicad native quantities, masks, batch calls, cover-aware surface queries, SEO link traversal, component property reads.
KEEP THIN BRIDGE ONLY IF NO EXISTING ADAPTER: expose exact native fields by GUID + quantity mask/params + SEO dependency GUIDs to Project Compiler.
DO NOT BUILD: separate general-purpose QTO-from-triangles engine, duplicate SEO topology model, or independent geometry-derived wall/net areas for ordinary reports.
LIVE STATUS: NOT VERIFIED. No AC29 runtime used, PLN untouched.
