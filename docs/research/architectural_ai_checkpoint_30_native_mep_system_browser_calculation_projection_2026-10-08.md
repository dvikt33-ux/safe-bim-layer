# Architectural AI checkpoint 30 — native MEP System Browser calculation projection

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–29

## Executive conclusion

Archicad 29 provides a first-party extension point for custom calculated columns directly inside the MEP System Browser:
`ACAPI::MEP::SystemBrowserCalculationCallbackInterface`.

This removes the need for a separate SBIM MEP-results table for most per-system/per-element engineering outputs.

Correct ownership:
- Project Compiler / specialist calculation = authoritative computation;
- DistributionSystemsGraph = native topology input;
- System Browser calculated columns = native display/projection;
- Rule IR / evidence store = authoritative compliance/evidence.

Archicad does not automatically calculate hydraulic/aerodynamic engineering values merely because the UI extension exists.

## 1. AC29 calculated-column contract

`ICalculationResultColumn` defines:
- globally unique technical column ID;
- default column width;
- localized/display title;
- optional display unit;
- value-to-display formatting;
- less-than comparison;
- equality comparison;
- supported MEP domains.

`TypedCalculationResultColumn<T>` is a helper for typed column values.

This is sufficient for both numeric and status/string projections.

## 2. Supported domains

AC29 MEP domains are:
- Ventilation;
- Piping;
- CableCarrier.

A calculated column can declare the domain set where it is applicable.

This permits discipline-specific output without a separate UI.

## 3. Calculation lifecycle

An Add-On implements:
`SystemBrowserCalculationCallbackInterface`.

It registers its columns through:
`RegisterCalculatedColumns()`.

The System Browser invokes:
`CalculationsRequested(rootElement, DistributionSystemsGraph)`
when it detects a model/system change that may affect registered calculated values.

Documented example triggers include:
- system elements added/removed;
- element dimensions changed;
- certain element-specific parameters changed;
- certain system-specific parameters changed.

The callback receives:
- root element GUID;
- native DistributionSystemsGraph for the affected system.

## 4. Result submission

Results are submitted with:
`SubmitCalculations(CalculationResultData)`.

Each `ColumnRowEntry` is identified by:
- `elemId` — element GUID;
- `columnId` — one registered column ID;
- `value` — `std::any` value.

The System Browser decides the actual table row; the Add-On maps results by BIM element identity, not by row index.

This is a strong fit for a canonical element-linked calculation model.

## 5. Add-On can push updates proactively

The interface explicitly allows the Add-On to call `SubmitCalculations` at any time, even without first receiving a `CalculationsRequested` callback.

Therefore Project Compiler invalidation can drive updates directly:

`model/event change`
-> `Project Compiler recalculates dirty MEP facts`
-> `SubmitCalculations`
-> `System Browser refreshes values`.

The browser callback is useful as a native hint/trigger, but is not our only invalidation source.

## 6. Browser triggers are not authoritative invalidation

Graphisoft documentation explicitly says the System Browser detects changes empirically and may:
- request recalculation even when a custom value is unaffected;
- fail to know every implementation-specific dependency of a third-party calculated value.

Therefore:
- do not use browser callbacks as the sole dependency engine;
- keep Project Compiler semantic facet invalidation authoritative;
- treat `CalculationsRequested` as an additional invalidation/reconciliation hint.

## 7. Good SBIM columns

Candidate calculated columns that can be projected natively include:
- design airflow / flow;
- calculated airflow / flow;
- velocity;
- pressure drop;
- accumulated pressure drop;
- hydraulic/aerodynamic reserve;
- nominal/required section or diameter;
- calculated sizing state;
- balancing result;
- connected-demand total;
- system capacity margin;
- rule/compliance status;
- calculation freshness/status.

Only expose values that are meaningful at the element/system row shown by System Browser.

Do not place long legal explanations/evidence blobs in calculated columns.

## 8. Sorting and units are native

Calculated columns provide:
- unit shown in header;
- formatting function;
- less-than comparison;
- equality comparison.

Thus native sorting can work with typed engineering values rather than lexicographic display strings.

Keep canonical units in the Project Compiler and explicitly control display-unit conversion/formatting in the column implementation.

## 9. No open wrapper found in this pass

Search of:
- current Tapir;
- davidharutyunyan/archicad-mcp-connector;
- alesdev88/Archicad-MCP;
- SzamosiMate/tapir-archicad-MCP

found no wrapper/adapter for `SystemBrowserCalculationCallbackInterface`.

Therefore this is a legitimate SMALL AC29 native bridge candidate.

It does not require a custom table, graph, calculation engine or UI framework.

## 10. Minimal bridge design

The native Add-On side needs only:
1. register stable calculated-column definitions at startup;
2. receive `CalculationsRequested` and forward affected root/system identity to Project Compiler if useful;
3. accept already-calculated `{elemGuid, columnId, typedValue}` rows from Project Compiler;
4. call `SubmitCalculations`;
5. unregister naturally with interface lifetime.

Column definitions should be deterministic and versioned.

## 11. MEP-CALC-UI-01

Build a minimal AC29 experiment with:
- one Ventilation column;
- one Piping column;
- one CableCarrier column;
- one numeric engineering value;
- one text/status value.

Verify:
1. columns appear in native System Browser;
2. units/header titles appear correctly;
3. values map to the correct element GUIDs;
4. numeric sorting uses typed comparison;
5. values update after `SubmitCalculations`;
6. edit system geometry/dimensions and observe `CalculationsRequested`;
7. add/remove an element and observe callback;
8. proactive `SubmitCalculations` without callback works;
9. Add-On unload/reload removes/re-registers columns cleanly;
10. save/reopen PLN behavior;
11. performance on a large network.

## 12. MEP-CALC-CACHE-01

Compare native callback triggers against Project Compiler invalidation for controlled changes:
- route geometry;
- segment dimension;
- system assignment;
- connected terminal/equipment;
- property-only change;
- classification change;
- Renovation status;
- Design Option;
- MEP graph connection;
- external design parameter.

Record false-positive and false-negative native triggers relative to actual custom-column dependencies.

Browser trigger must never become the authoritative cache key.

## 13. MEP calculation architecture

Recommended flow:

`native DistributionSystemsGraph`
-> `Project Compiler / specialist calculation`
-> `typed result facts keyed by element GUID`
-> `native System Browser calculated columns`
-> optional `RuleResult`
-> `Issue/BCF / Model Quality Check / highlight`.

This keeps topology, engineering results, compliance and UI cleanly separated.

## 14. Roadmap changes

STOP / DEFER:
- separate MEP-result grid/table UI;
- custom mapping between table row number and BIM identity;
- custom sorting/unit display framework for MEP results;
- persistent duplicate network tree solely for displaying calculated values.

KEEP:
- actual hydraulic/aerodynamic/electrical engineering computation where needed;
- Project Compiler dependency/invalidation;
- evidence/provenance;
- thin System Browser callback bridge;
- external specialist solver integration where calculations exceed project-local algorithms.

## Strategic conclusion

AC29 can host MEP calculation results in the same native browser that already exposes the system topology.

The ideal ownership becomes:

`Archicad = system topology + result display`
`SBIM/solver = calculation + law + evidence`.

This removes another custom UI subsystem without weakening calculation rigor.