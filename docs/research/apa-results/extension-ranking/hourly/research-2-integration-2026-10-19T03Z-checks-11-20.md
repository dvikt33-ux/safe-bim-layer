# APA №2 — проверки P11–P20 (03Z)
Graphisoft AC29: https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
Tapir 1.5.9 tagged: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp
P11. Master GUID? LayoutParameters 3098–3136 не содержит masterNavigatorItemId; CreateLayout 51–74 принимает его. Readback master через этот метод NOT_FOUND; искать Navigator relation.
P12. Wrong item? GetNavigatorItemsType(ids)→NavigatorItemIdAndTypeOrError, 870–874. Reuse type preflight; invalid fixture.
P13. 2D bounds? Get2DBoundingBoxes 195–211: global origin floor plan, only Element Information. Reuse read-only; rotated object.
P14. 3D bounds? Get3DBoundingBoxes 212–229: global origin, x/y/z min/max. Compare PR170 B3; units/placement gate.
P15. Unsupported? BoundingBox2DOrError/3DOrError 1715–1801. Не трактовать error как нулевой bbox; unsupported fixture.
P16. Saved view? Tapir GetViewSettingsCommand::Execute → layerCombination, penSetName, graphicOverrideCombination, drawingScale. Ready tagged binding; local 1.5.10 runtime unknown.
P17. Renovation GUID? Та же GetViewSettings выдаёт renovationFilterGuid только если не APINULLGuid. Reuse saved-view filter; null fixture.
P18. Wrong View? GetViewSettings задаёт API_PublicViewMap и возвращает error если ACAPI_Navigator_GetNavigatorView fails. Fail-closed; invalid item fixture.
P19. Layer combination? AC29 LayerCombinationAttribute 3054–3069 содержит layerAttributeIds, НЕ visibility map. Full visibility QA blocked; искать SDK read-only detail.
P20. Layer hidden? AC29 LayerAttribute 3000–3022 содержит isHidden/isLocked/isWireframe, но это не per-view combination override. Не приравнивать; compare two saved views.
SOURCE=10, OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=NOT_RUN.
