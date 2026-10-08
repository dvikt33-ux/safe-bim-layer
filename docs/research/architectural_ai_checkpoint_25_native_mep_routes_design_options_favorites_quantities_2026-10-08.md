# Architectural AI checkpoint 25 — native MEP routes, Design Options, Favorites, quantities and property expressions

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–24

## Executive conclusion

Five more areas shrink from custom subsystems to native/open reuse:

1. MEP physical routing is already a native Archicad execution API.
2. Design Alternatives should live in native Design Options.
3. Validated element recipes can live in Favorites rather than bespoke JSON.
4. Most quantity/area/volume/material checks should use Archicad native quantities before evaluated geometry.
5. Simple local derived facts can be compiled into Archicad Property Expressions.

The new data-cost ladder is:

`header/property/classification`
-> `native quantity`
-> `native relation`
-> `native 2D/drawing primitive`
-> `evaluated 3D summary`
-> `evaluated 3D mesh/topology`.

Deep geometry is now a last-resort semantic source, not the default source for measurements.

## 1. MEP routing is a first-party execution surface

Archicad 29 MEP API exposes native placement and modification of routing elements.

`ACAPI::MEP::RoutingElementDefault::Place(...)` accepts:
- a sequence of 3D routing-node coordinates;
- segment cross-section data;
- routing defaults/system context;
- circular or rectangular cross sections as appropriate.

Existing routing elements/nodes can be modified. Observed native capabilities include:
- moving Routing Nodes with SetPosition;
- changing a route's MEP system;
- logical connection of routes/elements;
- port-based connectivity;
- placement of terminals/fittings/accessories/take-offs;
- direct placement-and-connect workflows to an existing Port or RoutingNode.

Graphisoft documentation explicitly notes that repeated individual placements otherwise create separate undo scopes and recommends grouping a compound placement in one command scope for performance.

### Architecture consequence

SBIM should solve:
- where the route should go;
- applicable clearance/slope/fire/maintenance rules;
- sizing and system intent;
- collision/coordination policy;
- alternative ranking.

Archicad should solve the low-level physical realization of:
- segments;
- nodes;
- elbows/transitions where native behavior supports them;
- connected terminals/fittings/accessories.

Do not build a generic MEP geometry engine.

## 2. MEP-ROUTE-01

On AC29 scratch file:
1. place a route from 3D node coordinates;
2. test circular and rectangular section data;
3. move one RoutingNode;
4. change system/category where supported;
5. connect route to route;
6. place terminal/fitting connected to a port/node;
7. inspect DistributionSystemsGraph after each operation;
8. repeat as a compound single undo command;
9. compare latency and resulting topology.

Acceptance:
- native topology is authoritative;
- SBIM needs only path/constraint policy and thin capability wrappers.

## 3. Design Options should own geometric alternatives

Archicad Design Options API is substantially complete for our use.

`DesignOptionManager` supports or exposes operations for:
- Design Option Sets;
- Design Options;
- Design Option Combinations;
- creating sets/options/combinations;
- deleting/renaming/moving where API preconditions allow;
- checking whether an element can move to another option;
- relinking elements to a Design Option;
- querying elements of an option;
- querying option status;
- changing active options inside combinations;
- design-option settings on Views;
- Hotlink Design Options.

Current Tapir main already wraps this area.

Observed Tapir command classes:
- GetDesignOptionsCommand;
- GetDesignOptionSetsCommand;
- GetDesignOptionCombinationsCommand;
- GetElementsOfDesignOptionsCommand;
- GetDesignOptionForElementsCommand;
- CreateDesignOptionSetsCommand;
- CreateDesignOptionsCommand;
- CreateDesignOptionCombinationsCommand;
- SetActiveDesignOptionsInCombinationsCommand;
- MoveElementsToDesignOptionsCommand;
- MoveDesignOptionsToAnotherSetCommand.

SzamosiMate/tapir-archicad-MCP already generates MCP tools from those Tapir schemas.

### Design Healing consequence

Do not create separate project copies for ordinary architectural alternatives.

Preferred workflow:

`baseline`
-> `native Design Option candidate A/B/C`
-> `incremental checks + score + evidence`
-> `selected option`
-> `Decision Record`.

The external graph stores:
- candidate lineage;
- hypothesis/intent;
- score vector;
- rule/evidence results;
- decision rationale.

The PLN stores the actual alternative geometry.

## 4. DESIGN-OPTIONS-01

Verify on AC29:
- create Set + three Options;
- move/copy fixture elements into candidates;
- create Combination per candidate;
- bind combinations to Views;
- run quantity/rule checks per combination;
- switch selected candidate;
- verify placed Drawings/View status;
- delete/relink candidate safely;
- measure transaction/read-back behavior.

## 5. Favorites can be native validated recipes

Archicad FavoriteManager is richer than a simple style preset.

A Favorite can be created from ElementDefault or from element state including:
- API_Element;
- subelements;
- memo;
- marker element/memo;
- user properties;
- classifications;
- element category values.

Current Tapir supports:
- CreateFavoritesFromElements;
- ApplyFavoritesToElementDefaults;
- ApplyFavoritesToElements.

Tapir's current implementation explicitly propagates classifications, category values and user properties where required.

The MIT connector `davidharutyunyan/archicad-mcp-connector` additionally exposes and live-tests:
- get_favorites;
- apply_favorite to Defaults or Elements;
- create_favorite;
- delete_favorite;
- rename_favorite;
- export_favorites;
- import_favorites.

### ACP/recipe consequence

Do not serialize every reusable typified BIM recipe into a custom JSON object if Favorite can carry it natively.

Recommended split:

PLN / PRF Favorite:
- actual BIM defaults/settings;
- properties/classifications;
- memo/subelement-capable state.

External SBIM Recipe Record:
- recipe_id;
- Favorite identity/name/type;
- version/hash;
- applicability envelope;
- governing Rule IDs;
- normative provenance;
- verification status;
- expected read-back fingerprint.

Thus ACP becomes a governed Favorite plus external semantics, not a duplicate BIM serializer.

## 6. FAVORITE-ACP-01

Create verified Favorites from:
- Wall;
- hosted Window/Door;
- Slab/Roof;
- Stair;
- Curtain Wall if supported by provider;
- one MEP default/element where supported.

Verify:
- property/classification propagation;
- memo/part behavior;
- application to Defaults;
- application to existing Elements;
- create-from-Favorite deterministic read-back;
- export/import PRF;
- version/fingerprint drift.

## 7. Native quantities should precede deep geometry

Archicad already computes a broad element-quantity model via `ACAPI_Element_GetQuantities`.

The open MIT connector has already wrapped this into `GetElementQuantities` / `get_element_quantities` with descriptive typed output.

Observed coverage includes:

### Wall
- net/conditional/gross volumes;
- reference/opposite/edge surfaces;
- gross and conditional surfaces;
- area/perimeter/length/reference-line lengths;
- min/max heights;
- skin/insulation/air-gap thicknesses;
- window/door/opening surfaces and widths;
- empty-opening volume/surfaces.

### Beam / Column and segments
- net/gross/core/veneer volumes;
- surfaces;
- lengths;
- cross-section areas;
- hole counts/areas/volumes;
- min/max heights.

### Windows / Doors / Skylights
- nominal and actual dimensions;
- surface/gross surface;
- volume/gross volume;
- reveal/opposite-side surfaces;
- sill/head heights;
- opening surface/volume.

### Slab / Mesh
- volume/gross volume;
- top/bottom/edge surfaces;
- hole surfaces/perimeters;
- projected area;
- perimeter.

### Roof / Shell
- net/conditional/gross volume;
- top/reference/opposite/edge surfaces;
- gross surfaces;
- contour/floor-plan area;
- openings/holes;
- ridge/valley/gable/hip/eaves/peak lengths;
- connection lengths;
- skylight/hole counts.

### Zone
- area;
- net area;
- calculated area;
- reduction area;
- volume;
- perimeter/net perimeter;
- wall perimeter/surface;
- door/window width and surface;
- height/base/floor thickness;
- corner counts;
- extracted/reduced/low-height areas;
- wall/CurtainWall/column/fill extracted areas.

### Curtain Wall
- contour/boundary/panel surfaces;
- panel surfaces by orientation;
- frame lengths by class;
- panel count;
- frame dimensions/material;
- panel dimensions, area/perimeter, orientation and surfaces.

### Stair / Railing
- Stair area, volume, height, walking-line length, gradient, riser/tread counts;
- Tread/Riser/Structure quantities;
- Railing area/volume/3D length;
- many Railing subpart volumes/lengths.

### Morph / Objects / Hatches
- surface/volume;
- floor-plan area/perimeter;
- topology counts for Morph;
- hatch surface/perimeters.

## 8. Composite and material quantities

The wrapper asks Archicad for `API_CompositeQuantity` values and returns for each component/skin:
- Building Material;
- volume;
- projected area;
- core flag;
- finish flag;
- subElementGuid when present.

It also aggregates Building Material totals across the request.

With `includeParts`, it requests:
- API_ElemPartQuantity;
- API_ElemPartCompositeQuantity;
- quantity and composite data per element part.

This can replace a large fraction of geometry-derived QTO, cost and LCA calculations.

## 9. Exposed-surface quantities

The wrapper uses `ACAPI_Element_GetSurfaceQuantities` and can supply cover elements.

Output contains:
- source element;
- Surface attribute;
- Building Material where available;
- exposed area.

This is especially valuable for:
- finish quantities;
- façade/paint/cladding area;
- exposed material calculations;
- cost/LCA inputs.

Do not infer exposed area from raw mesh unless this native result is insufficient or needs independent audit.

## 10. Quantity parameter semantics

Walls require a non-null `API_QuantityPar`; the open implementation records the AC API quirk that a null parameter returns APIERR_BADPARS.

`minOpeningSize` controls whether small openings reduce wall surfaces.

This parameter is therefore part of the semantic ActionDigest for any result that depends on gross/net wall surfaces.

Never cache a quantity result without including quantity parameters and the relevant model/rule context.

## 11. Generic Opening remains a narrow quantity adapter gap

The open quantity wrapper currently has no explicit `API_OpeningID` case in `WriteQuantities`.

Therefore Generic Opening quantity coverage is NOT considered solved by this wrapper.

Research/test:
`OPENING-QUANTITY-01` must inspect AC29's raw quantity result for Generic Opening and decide whether:
- native quantity fields can be exposed;
- host-derived values are sufficient;
- deep topology is still required for specific opening checks.

## 12. Revised data-cost ladder

For every Rule IR input, ask for the cheapest authoritative source in this order:

1. Element header / direct field.
2. Property / classification / Favorite / attribute.
3. Native quantity.
4. Native relation / Zone/MEP/topology relation.
5. Native floor-plan/drawing primitive.
6. Evaluated 3D summary/bounding envelope.
7. Evaluated 3D mesh/topology/material provenance.
8. External specialist computation.

This becomes a mandatory input-planning rule for the Project Compiler.

## 13. QUANTITY-01

On a representative AC29 fixture compare native quantities against independent geometry-derived values for:
- Wall with Window/Door/Generic Opening;
- composite Wall;
- Slab with hole;
- Roof with hole/skylight;
- Zone with reductions;
- Curtain Wall;
- Stair;
- Railing.

Record:
- semantic definition of each value;
- exact/relative difference;
- runtime;
- invalidation facet;
- whether the quantity is sufficient for each planned Rule IR family.

## 14. QUANTITY-COST-01

Benchmark native quantity retrieval on the existing ~5,296-element project.

Run staged calls:
- only high-value types;
- no composites/parts/exposed surfaces;
- composites enabled;
- parts enabled;
- exposed surfaces enabled.

Compare against 12.85 s / 104.93 MB full Model Dump baseline.

Target:
make native quantities a WARM/on-demand source and avoid 104 MB geometry for QTO/routine compliance.

## 15. Property Expressions are a PLN-native LIGHT derived-fact engine

Archicad custom properties can have expression-based default values.

Official API exposes:
- `API_PropertyDefaultValue.hasExpression`;
- `propertyExpressions` array;
- expression syntax validation;
- property reference string generation;
- evaluated/not-evaluated property status.

Current Tapir supports reading, creating and updating expression-based Custom Property Definitions.

Tapir's expression tests demonstrate creation of expressions referencing:
- built-in DynamicBuiltIn real properties;
- built-in string properties using expression functions;
- custom numeric properties;
- multiple expressions;
- updating an existing expression property while retaining its property GUID.

The MIT connector also supports `defaultExpressions` in property-definition creation/modification and availability scoping.

## 16. Correct scope for Property Expressions

Use Property Expressions only for local deterministic derived facts that are useful inside Archicad, for example:
- normalized area/width/ratio;
- simple reserve/margin calculation;
- simple classification-derived status;
- lightweight report/schedule fields;
- a compiled boolean/text/numeric indicator when all dependencies are native properties.

Do NOT use Property Expressions as the legal Rule IR source of truth.

Reasons:
- expressions may evaluate to NotEvaluated;
- their language cannot represent every spatial/cross-element rule;
- legal applicability/version/provenance is external to the arithmetic expression;
- cyclic references and type/unit issues exist;
- multi-entity graph rules need the Project Compiler.

Recommended pattern:

`verified Rule IR`
-> optionally compile a safe local projection into Property Expression
-> Archicad evaluates for immediate UI/schedules
-> independent Rule IR remains authoritative.

## 17. PROPERTY-EXPR-01

Create a small SBIM property group with:
- one expression using native built-in area/quantity-like property;
- one custom-property dependency;
- one classification-scoped availability;
- one deliberately invalid expression;
- one deliberate cycle if safely testable.

Verify:
- syntax validation;
- evaluated values;
- NotEvaluated reporting;
- update in place with stable GUID;
- recalculation after source edit;
- event notification/property invalidation behavior;
- schedule visibility.

## 18. Revised custom ownership

STOP / DEFER custom ownership of:
- generic MEP route construction;
- alternative-geometry storage outside PLN;
- generic recipe serialization for Favorite-representable elements;
- geometry-derived routine area/volume/QTO engine;
- custom formula engine for simple local derived BIM fields.

KEEP custom ownership of:
- routing intent/path optimization and rule constraints;
- alternative lineage/scoring/decision evidence;
- ACP validity envelopes and normative provenance;
- Rule IR and legal applicability;
- incremental invalidation/action cache;
- independent verification;
- deep geometry only for rules whose required semantics are not available natively.

## Strategic conclusion

The live project can now be treated as a native compiled model, not a dumb geometry store:

`Favorites` = reusable governed BIM recipes
`Design Options` = native candidate geometry
`MEP Routing` = native physical route executor
`Native Quantities` = cheap WARM measurements
`Property Expressions` = local LIGHT derived facts
`SBIM` = intent + law + dependency compiler + verification + evidence.

This substantially reduces both code volume and runtime cost.