# APA 18Z: contracts 11-20 — PR165 IFC/DXF

11. V2 catalog: 8 IFC and 4 DXF commands; no second Router.
12. Source limit: 4 GiB per input, sample limit 5000.
13. IFCGlobalIdAudit declares nativeGuidMappingChecked=false.
14. IFCOpeningRelations counts IfcRelVoidsElement and IfcRelFillsElement separately.
15. IFCPortRelations counts IfcRelConnectsPorts; missing relation is not proof of a broken native connection.
16. IFCGeoReferenceAudit reads map conversion values but does not calibrate world coordinates.
17. DXFLayerInventory returns INSUNITS code without converting units.
18. DXFBlockInsertions counts INSERT entities, not all MINSERT placements.
19. DXFDimensionEntities does not recalculate measured geometry.
20. Evidence output must be new JSON; source and adapter hashes are checked.

Source: https://github.com/dvikt33-ux/safe-bim-layer/blob/5c0dc009e729db9834301b4a369512490a205ef7/scripts/apa_high_density_readonly_v2.py
Verdict: REUSE with coverage gates; next synthetic vs real IFC/DXF.
