# APA AC29 16Z — appendix A: existing APA and native grouping

SOURCE-only contract audit. GitHub source, not local execution.

1. APA external adapter PR154: VERSIONS dictionary pins ifcopenshell/ifcdiff/ifctester 0.8.5, pdfplumber 0.11.10; actual installed versions not read. Source: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_readonly.py#L19-L30
2. check_environment requires Windows, Python 3.11/3.12, metadata versions; no ifcpatch/bcf import gate. Same source L56-L71.
3. invoke_module whitelist only ifcclash/ifcdiff/ifctester. Same source L73-L81. IfcPatch cannot be called through this entry point as-is.
4. invoke_module calls Python -m, writes temporary vendor-result.json, parses JSON and caps 200 MiB; binary BCF is incompatible with this parser. Same source L77-L96.
5. APA main output uses exclusive open('x'), .json suffix, source SHA256, no overwrite. Same source L312-L347. Reuse output policy for future IFC/BCF.
6. inspect_export maps native GUID to IFC GlobalId and explicitly handles missing aggregate duct IFC root via physical child IDs. Source: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/archicad_connected_ifc.py
7. inspect_exchange_semantics checks IfcRelVoidsElement, IfcRelConnectsPorts and analytical members. Same source. Useful independent subset integrity oracle.
8. Existing DynamicCommands.clone_native_group calls prepare/execute through SceneWriter, with sourceRef/affected/saved_sha256. Source: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/scripts/archicad_dynamic_commands.py#L826-L866
9. Tapir tag1.5.9 CreateGroups input elementGroups[] and output groupGuids[]. Source: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementGroupingCommands.cpp#L32-L70
10. Tapir CreateGroups processes per-item errors and lambda returns NoError. Need check every returned group GUID and independent readback, not just success of outer call. Same source L72-L128.

Audit A: tagged Tapir 1.5.9 does not establish local 1.5.10; metadata pin does not establish installation.
Audit B: group clone already exists; do not introduce a second writer. No LIVE performed.
