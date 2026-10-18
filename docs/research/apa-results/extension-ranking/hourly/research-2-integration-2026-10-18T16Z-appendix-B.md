# APA AC29 16Z — appendix B: Hotlink, Publisher, IfcPatch

SOURCE-only audit; checks 11–20 of 30. Each conclusion is a proposed integration gate, not an installed feature.

11. Tapir 1.5.9 CreateHotlinkInstances requires hotlinkNodeId and origin; rotationAngle in radians, optional floorIndex, mirrored, layerIndex. Source: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp#L2344-L2427 . Linked modules are not independent clones.
12. The same command calls ACAPI_Hotlink_GetHotlinkNode and uses the node type to set API_HotlinkID. Node GUID differs from instance GUID; store both for rollback. Source: same file L2434-L2507.
13. Graphisoft SDK29.3100 ACAPI_Hotlink_GetHotlinkInstances(const API_Guid*, GS::Array<API_Guid>*) provides readback by node. Source: https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___hotlink.html#L471-L490 . ABI for local build5101 not tested.
14. Tapir1.7.1 PublishPublisherSet input publisherSetName required, outputPath and selectedNavigatorItemIds optional. Source: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.1/archicad-addon/Sources/NavigatorCommands.cpp#L36-L59 . Check set identity before publishing.
15. Publisher selectedNavigatorItemIds=[] leaves selectedLinksPtr=nullptr and calls ACAPI_ProjectOperation_Publish. This can publish the whole set. Same source L82-L103. Fail closed with nonempty whitelist and isolated output path.
16. IfcPatch CLI -i/-r required; -o optional; if missing, output=input. Source: https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifcpatch/ifcpatch/__main__.py#L26-L43 . Never omit -o.
17. IfcPatch current master Python execute(args:dict) uses input,file,recipe,arguments, then write(output,path). Source: https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifcpatch/ifcpatch/__init__.py#L32-L85 . Do not assume this is installed APA 0.8.5.
18. IfcPatch write accepts file object or string; a string that points to a file may be moved to destination. Same source L85-L103. Source/output SHA and exclusive output required.
19. ExtractElements current master Patcher(src,file,logger,query='IfcWall'), filter_elements(selector). Source: https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifcpatch/ifcpatch/recipes/ExtractElements.py#L27-L68 . The previously claimed assume_asset_uniqueness_by_name parameter is NOT present in this revision.
20. ExtractElements append_asset with reuse_identities and rebuilds spatial containment/aggregation. Same source L77-L128. This does NOT prove IfcRelVoidsElement or port relations survive; compare against existing APA inspect_exchange_semantics.

Architectural choices: Hotlink via existing Router+Tapir only if local command exists, otherwise narrow SDK29 bridge; no second SceneWriter. Publisher prefer existing Tapir after read-only command discovery, otherwise SDK29 via existing Bridge. ExtractElements prefer one Python wrapper around the existing IFC export, no new IFC engine; compare against native export filter when a callable API29 contract is found.

Source/compatibility audit: Tapir tags 1.5.9 and 1.7.1 are NOT local 1.5.10. SDK29 docs not build5101 ABI proof. No actual write/publish/IFC mutation performed.
