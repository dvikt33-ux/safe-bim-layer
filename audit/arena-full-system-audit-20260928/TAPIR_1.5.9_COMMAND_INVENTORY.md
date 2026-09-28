# Tapir 1.5.9 command inventory (generated)
Source: `docs/archicad-addon/command_definitions.js` at git tag `1.5.9` (commit d0dbb11b13942e014661e1402b07958b70cd9dba) of https://github.com/ENZYME-APD/tapir-archicad-automation. Generated 2026-09-28 by Arena from a local clone; evidence grade for *existence of a command* = STATIC_CONFIRMED. Existence of a command is NOT evidence of live behaviour.
Total commands at 1.5.9: **250**. Total at ChatGPT research baseline b1dc828 (ADDON_VERSION 1.5.10, 76 commits after 1.5.9): **255**.
Commands present at b1dc828 but ABSENT in live 1.5.9: ImportClassificationsXml, ImportPropertiesXml, UpdateClassificationItems, UpdateClassificationSystems, UpdatePropertyGroups
Commands present at 1.5.9 but absent at b1dc828: (none)

## Application Commands (9)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetAddOnVersion` | 0.1.0 | Retrieves the version of the Tapir Additional JSON Commands Add-On. |
| `GetArchicadLocation` | 0.1.0 | Retrieves the location of the currently running Archicad executable. |
| `QuitArchicad` | 0.1.0 | Performs a quit operation on the currently running Archicad instance. |
| `GetPointFromUser` | 1.5.9 | Asks the designer to click a point in the current window and returns it. Archicad waits for the click or for Escape, and every other JSON... |
| `GetCurrentWindowType` | 1.0.7 | Returns the type of the current (active) window. |
| `ChangeWindow` | 1.3.1 | Changes the current (active) window to the given window. |
| `GetUserGSID` | 1.5.6 | Get the current registered User-GSID and OrganizationsID. Requires Archicad 27 or later. |
| `ShowAlert` | 1.5.6 | Display a dialog with up to three buttons. |
| `GetSpecialFolders` | 1.5.6 | Retrieves the filesystem paths of the special folders of the running Archicad (preferences, cache, data, temporary, application, defaults... |

## Project Commands (22)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetProjectInfo` | 0.1.0 | Retrieves information about the currently loaded project. |
| `GetProjectInfoFields` | 0.1.2 | Retrieves the names and values of all project info fields. |
| `SetProjectInfoField` | 0.1.2 | Sets the value of a project info field. |
| `CreateProjectInfoFields` | 1.5.2 | Creates one or more custom project info fields. |
| `DeleteProjectInfoFields` | 1.5.4 | Deletes one or more custom project info fields. Hardcoded fields cannot be deleted. |
| `GetStories` | 1.1.5 | Retrieves information about the story sructure of the currently loaded project. |
| `SetStories` | 1.1.5 | Sets the story sructure of the currently loaded project. |
| `GetAutoTextKeys` | 1.5.9 | Retrieves the available autotext keys (name and embeddable key), optionally for a specific element. Embed a key in a Text or Label conten... |
| `GetAutoTextName` | 1.5.9 | Retrieves the display names of one or more autotext keys (as returned inside a '<...>' embedded key), with a direct guid lookup for prope... |
| `GetHotlinks` | 0.1.0 | Gets the file system locations (path) of the hotlink modules. The hotlinks can have tree hierarchy in the project. |
| `CreateHotlinkNodes` | 1.5.9 | Creates hotlink module nodes from source files. A node that already points at the same file is returned instead of duplicated (Archicad 2... |
| `CreateHotlinkInstances` | 1.5.9 | Places instances of hotlink module nodes at an origin, rotation and mirroring. |
| `ChangeHotlinkInstances` | 1.5.9 | Moves, rotates or mirrors placed hotlink instances by changing their transformation. MoveElements and RotateElements do not work on hotli... |
| `OpenProject` | 1.0.7 | Opens the given project. |
| `CloseProject` | 1.3.1 | Closes the currently opened project. |
| `SaveProject` | 1.3.1 | Saves the currently opened project. |
| `SaveAsModuleFile` | 1.5.9 | Saves the given elements, or the current selection, as a hotlink module (.mod) file. |
| `GetCalculationUnits` | 1.4.0 | Gets the project calculation units. |
| `GetGeoLocation` | 1.1.6 | Gets the project location details. |
| `SetGeoLocation` | 1.2.9 | Sets the project location details. |
| `PrintView` | 1.3.1 | Prints from the current view. |
| `RebuildView` | 1.5.0 | Rebuilds the current view. |

## Element Commands (67)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetSelectedElements` | 0.1.0 | Gets the list of the currently selected elements. |
| `GetElementsByType` | 1.0.7 | Returns the identifier of every element of the given type on the plan. It works for any type. Use the optional filter parameter for filte... |
| `GetAllElements` | 1.0.7 | Returns the identifier of all elements on the plan. Use the optional filter parameter for filtering. |
| `ChangeSelectionOfElements` | 1.0.7 | Adds/removes a number of elements to/from the current selection. |
| `FilterElements` | 1.0.7 | Tests an elements by the given criterias. |
| `GetDetailsOfElements` | 1.5.7 | Gets the details of the given elements (geometry parameters etc). Use the optional fields parameter to return only the fields you need an... |
| `SetDetailsOfElements` | 1.0.7 | Sets the details of the given elements (floor, layer, order etc). |
| `Get3DBoundingBoxes` | 1.1.2 | Get the 3D bounding box of elements. The bounding box is calculated from the global origin in the 3D view. The output is the array of the... |
| `GetSubelementsOfHierarchicalElements` | 1.0.6 | Gets the subelements of the given hierarchical elements. |
| `GetConnectedElements` | 1.1.4 | Gets the elements hosted by (connected to) the given owner elements, filtered to the given element type: for example the Windows or Doors... |
| `GetSectionElements` | 1.5.8 | Gets the elements drawn in the given section, elevation or interior elevation databases, each with the owner element it was generated fro... |
| `GetRelationsOfElements` | 1.5.7 | Gets the type-specific relations of the given elements: endpoint and reference line connections of walls, beams and beam segments, bounda... |
| `GetZoneBoundaries` | 1.2.3 | Gets the boundaries of the given Zones (connected elements, neighbour zones, etc.). Accepts either a single zoneElementId or a list of zo... |
| `UpdateZones` | 1.5.4 | Updates all Zones (recalculates their geometry, updates their Zone Stamps and the connected elements). |
| `GetCollisions` | 1.2.2 | Detect collisions between the given two groups of elements. |
| `HighlightElements` | 1.0.3 | Highlights the elements given in the elements array. In case of empty elements array removes all previously set highlights. |
| `MoveElements` | 1.0.2 | Moves elements with a given vector. |
| `RotateElements` | 1.5.3 | Rotates elements around a reference point. |
| `DeleteElements` | 1.2.1 | Deletes elements. |
| `LockElements` | 1.5.2 | Locks the given elements. Manual lock, not teamwork! |
| `UnlockElements` | 1.5.2 | Unlocks the given elements. Manual lock, not teamwork! |
| `GetGDLParametersOfElements` | 1.5.7 | Gets all the GDL parameters (name, type, value) of the given elements. |
| `SetGDLParametersOfElements` | 1.5.7 | Sets the given GDL parameters of the given elements. |
| `CreateColumns` | 1.0.3 | Creates Column elements based on the given parameters. |
| `CreateWalls` | 1.4.0 | Creates Wall elements based on the given parameters. |
| `CreateBeams` | 1.4.0 | Creates Beam elements based on the given parameters. |
| `CreateStairs` | 1.5.0 | Creates Stair elements based on the given baseline and parameters. |
| `CreateSlabs` | 1.0.3 | Creates Slab elements based on the given parameters. |
| `CreateWindows` | 1.4.0 | Creates Window elements in host walls based on the given parameters. |
| `CreateDoors` | 1.4.0 | Creates Door elements in host walls based on the given parameters. |
| `CreateOpenings` | 1.4.0 | Creates Opening elements in the given host elements. |
| `CreateMorphs` | 1.4.0 | Creates Morph elements from simple box definitions. |
| `CreateRoofs` | 1.4.0 | Creates Roof elements based on footprint, level and roof profile data. Creates a multi-plane roof by default; pass 'pivotLine' (and optio... |
| `CreateAssociativeDimensions` | 1.4.0 | Creates associative linear dimensions from explicit witness point references. |
| `CreateAssociativeDimensionsOnSection` | 1.4.0 | Creates associative linear dimensions on section elements using common wall, slab, beam, column and opening presets. The preset points of... |
| `CreateWallThicknessDimensions` | 1.4.0 | Creates associative wall thickness dimensions for the given walls. |
| `GetDimensionData` | 1.5.0 | Gets witness point data (coordinates, measured values) from existing dimension chains. |
| `CreateZones` | 1.1.8 | Creates Zone elements based on the given parameters. |
| `CreatePolylines` | 1.1.5 | Creates Polyline elements based on the given parameters. |
| `CreateLineElements` | 1.5.6 | Creates Line elements based on the given parameters. |
| `CreateArcs` | 1.5.6 | Creates Arc elements based on the given parameters. |
| `CreateCircles` | 1.5.6 | Creates Circle elements based on the given parameters. |
| `CreateHotspots` | 1.5.6 | Creates Hotspot elements based on the given parameters. |
| `CreateHatches` | 1.5.6 | Creates Hatch elements based on the given parameters. |
| `CreateSplines` | 1.5.6 | Creates Spline elements based on the given parameters. |
| `CreateObjects` | 1.5.7 | Creates Object elements based on the given parameters. |
| `CreateLamps` | 1.5.7 | Creates Lamp elements based on the given parameters. |
| `CreateMeshes` | 1.1.9 | Creates Mesh elements based on the given parameters. |
| `CreateLabels` | 1.2.5 | Creates Label elements based on the given parameters. |
| `CreateTexts` | 1.5.0 | Creates standalone Text elements based on the given parameters. |
| `ModifyWalls` | 1.4.0 | Modifies Wall elements based on the given parameters. |
| `ModifyBeams` | 1.4.0 | Modifies Beam elements based on the given parameters. |
| `ModifySlabs` | 1.4.0 | Modifies Slab elements based on the given parameters. |
| `ModifyColumns` | 1.4.0 | Modifies Column elements based on the given parameters. |
| `ModifyWindows` | 1.4.0 | Modifies Window elements based on the given parameters. |
| `ModifyDoors` | 1.4.0 | Modifies Door elements based on the given parameters. |
| `ModifyMorphs` | 1.4.0 | Modifies Morph elements based on the given parameters. |
| `ModifyRoofs` | 1.4.0 | Modifies multi-plane Roof elements based on the given parameters. |
| `ModifyMeshes` | 1.5.4 | Modifies the attributes of Mesh elements based on the given parameters. |
| `ModifyObjects` | 1.5.7 | Modifies Object elements based on the given parameters. |
| `ModifyLamps` | 1.5.7 | Modifies Lamp elements based on the given parameters. |
| `ModifyTexts` | 1.5.9 | Modifies standalone Text elements based on the given parameters. |
| `ModifyLabels` | 1.5.9 | Modifies Label elements based on the given parameters. |
| `GetElementPreviewImage` | 1.2.7 | Returns the preview image of the given element. |
| `GetRoomImage` | 1.2.7 | Returns the room image of the given zone. |
| `SetElementNotificationClient` | 1.2.8 | Sets up a new notification client to receive element events. |
| `RemoveElementNotificationClient` | 1.2.8 | Removes an element notification client. |

## Element grouping Commands (5)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `CreateGroups` | 1.4.0 | Creates groups of the passed elements |
| `GetGroupsOfElements` | 1.5.6 | Gets the identifier of the group that directly contains each given element. Returns an error for elements that are not part of any group. |
| `GetElementsOfGroups` | 1.5.6 | Gets the elements directly contained by each given group. |
| `GetSuspendGroupsMode` | 1.5.6 | Gets the current state of the Suspend Groups mode. |
| `SetSuspendGroupsMode` | 1.5.6 | Turns the Suspend Groups mode on or off. Suspend groups to perform operations on elements that are part of a group; remember to restore t... |

## Favorites Commands (10)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetFavoritesByType` | 1.2.2 | Returns a list of the names of all favorites with the given element type |
| `GetFavoritePreviewImage` | 1.2.7 | Returns the preview image of the given favorite. |
| `ApplyFavoritesToElementDefaults` | 1.1.2 | Apply the given favorites to element defaults. |
| `CreateFavoritesFromElements` | 1.1.2 | Create favorites from the given elements. |
| `ImportFavorites` | 1.5.0 | Import Favorites from a .prefs file or folder into the current project. |
| `ExportFavorites` | 1.5.0 | Export the project's Favorites to a .prefs file or folder. |
| `ApplyFavoritesToElements` | 1.5.4 | Apply the given favorites to existing elements. Only settings-type parameters are changed - geometry (position, floor, and dimensions suc... |
| `UpdateFavoritesFromElements` | 1.5.4 | Update existing favorites from the given elements. |
| `RenameFavorites` | 1.5.4 | Rename existing favorites. |
| `DeleteFavorites` | 1.5.4 | Delete existing favorites. |

## Property Commands (10)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetAllProperties` | 1.1.3 | Returns all user defined and built-in properties. |
| `GetPropertyValuesOfElements` | 1.0.6 | Returns the property values of the elements for the given property. It works for subelements of hierarchal elements also. |
| `SetPropertyValuesOfElements` | 1.0.6 | Sets the property values of elements. It works for subelements of hierarchal elements also. |
| `GetPropertyValuesOfAttributes` | 1.1.8 | Returns the property values of the attributes for the given property. |
| `SetPropertyValuesOfAttributes` | 1.1.8 | Sets the property values of attributes. |
| `CreatePropertyGroups` | 1.0.7 | Creates Property Groups based on the given parameters. |
| `DeletePropertyGroups` | 1.0.9 | Deletes the given Custom Property Groups. |
| `CreatePropertyDefinitions` | 1.0.9 | Creates Custom Property Definitions based on the given parameters. |
| `DeletePropertyDefinitions` | 1.0.9 | Deletes the given Custom Property Definitions. |
| `UpdatePropertyDefinitions` | 1.5.4 | Updates existing Custom Property Definitions: the expression(s) of an expression-based property, or the possible enum values of an enumer... |

## Classification Commands (6)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetClassificationsOfElements` | 1.0.7 | Returns the classification of the given elements in the given classification systems. It works for subelements of hierarchal elements also. |
| `SetClassificationsOfElements` | 1.0.7 | Sets the classifications of elements. In order to set the classification of an element to unclassified, omit the classificationItemId fie... |
| `CreateClassificationSystems` | 1.5.0 | Creates Classification Systems including Classification Items based on the given parameters. |
| `CreateClassificationItems` | 1.5.0 | Creates Classification Items in the given Classification Systems based on the given parameters. |
| `DeleteClassificationSystems` | 1.5.2 | Deletes the given Classification Systems. |
| `DeleteClassificationItems` | 1.5.2 | Deletes the given Classification Items. |

## Attribute Commands (25)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetAttributesByType` | 1.1.3 | Returns the details of every attribute of the given type. |
| `DeleteAttributes` | 1.5.4 | Deletes the given attributes. |
| `CreateLayers` | 1.0.3 | Creates or overwrites Layer attributes based on the given parameters. |
| `CreateLayerCombinations` | 1.2.4 | Creates or overwrites Layer Combination attributes based on the given parameters. |
| `CreateLines` | 1.5.4 | Creates or overwrites Line attributes based on the given parameters. |
| `CreateFills` | 1.5.4 | Creates or overwrites Fill attributes based on the given parameters. |
| `CreateZoneCategories` | 1.5.4 | Creates or overwrites Zone Category attributes based on the given parameters. |
| `CreateMEPSystems` | 1.5.4 | Creates or overwrites MEP System attributes based on the given parameters. |
| `CreatePenTables` | 1.5.4 | Creates or overwrites Pen Table attributes based on the given parameters. |
| `CreateProfiles` | 1.5.4 | Creates or overwrites Profile attributes as a copy of an existing Profile's geometry, based on the given parameters. |
| `CreateBuildingMaterials` | 1.0.1 | Creates or overwrites Building Material attributes based on the given parameters. |
| `CreateComposites` | 1.0.2 | Creates or overwrites Composite attributes based on the given parameters. |
| `CreateSurfaces` | 1.2.2 | Creates or overwrites Surface attributes based on the given parameters. |
| `GetBuildingMaterialPhysicalProperties` | 0.1.3 | Retrieves the physical properties of the given Building Materials. |
| `GetLayerCombinations` | 1.2.4 | Returns the details of layer combination attributes. |
| `GetLines` | 1.5.4 | Returns the details of the given Line attributes. |
| `GetFills` | 1.5.4 | Returns the details of the given Fill attributes. |
| `GetZoneCategories` | 1.5.4 | Returns the details of the given Zone Category attributes. |
| `GetMEPSystems` | 1.5.4 | Returns the details of the given MEP System attributes. |
| `GetPenTables` | 1.5.4 | Returns the details of the given Pen Table attributes. |
| `GetProfiles` | 1.5.4 | Returns the details of the given Profile attributes. |
| `GetComposites` | 1.5.4 | Returns the details of the given Composite attributes. |
| `GetSurfaces` | 1.5.4 | Returns the details of the given Surface attributes. |
| `GetLayers` | 1.5.4 | Returns the details of the given Layer attributes. |
| `GetBuildingMaterials` | 1.5.4 | Returns the details of the given Building Material attributes. |

## IFC Commands (5)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `IFCFileOperation` | 1.2.6 | Executes an IFC file operation. |
| `GetElementsByIFCIds` | 1.5.1 | Retrieves the elements by the given IFC identifiers. |
| `GetIFCIdsOfElements` | 1.5.1 | Retrieves the IFC identifiers of the given elements. |
| `GetIFCTypeOfElements` | 1.5.1 | Retrieves the IFC types of the given elements. |
| `GetIFCPropertiesOfElements` | 1.5.1 | Retrieves the IFC properties of the given elements. |

## Library Commands (6)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetLibraries` | 1.0.1 | Gets the list of loaded libraries. |
| `ReloadLibraries` | 1.0.0 | Executes the reload libraries command. |
| `AddFilesToEmbeddedLibrary` | 1.2.2 | Adds the given files into the embedded library. |
| `SetLibraries` | 1.5.9 | Makes the given folders the project's local libraries; built-in, embedded, server and web libraries are kept. Set the libraries before op... |
| `AddLibraries` | 1.5.9 | Adds the given folders to the project's local libraries, skipping any already loaded. |
| `GetAvailableLibraryParts` | 1.5.0 | Lists library parts currently available to the project. Filter by typeId (e.g. 'Door', 'Window', 'Object', 'Lamp'). |

## Teamwork Commands (4)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `TeamworkSend` | 0.1.0 | Performs a send operation on the currently opened Teamwork project. |
| `TeamworkReceive` | 0.1.0 | Performs a receive operation on the currently opened Teamwork project. |
| `ReserveElements` | 1.1.4 | Reserves elements in Teamwork mode. |
| `ReleaseElements` | 1.1.4 | Releases the given elements in Teamwork mode. |

## Navigator Commands (28)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `PublishPublisherSet` | 0.1.0 | Performs a publish operation on the currently opened project. Only the given publisher set will be published. |
| `UpdateDrawings` | 1.1.4 | Performs a drawing update on the given elements. |
| `GetDatabaseIdFromNavigatorItemId` | 1.1.4 | Gets the ID of the database associated with the supplied navigator item id |
| `CreateDetails` | 1.4.0 | Creates independent Detail databases. |
| `CreateWorksheets` | 1.4.0 | Creates independent Worksheet databases. |
| `CreateLayout` | 1.4.0 | Creates Layouts and their backing master layouts. |
| `CreateLayoutSubset` | 1.4.0 | Creates Layout Book subsets. |
| `CreateDrawings` | 1.4.0 | Creates Drawing elements on the specified or active layout from navigator items. |
| `ChangeDrawingLink` | 1.5.7 | Relinks a Drawing to a different source navigator item. Archicad has no in-place relink API, so this recreates the Drawing against the ne... |
| `GetLayoutSettings` | 1.1.7 | Gets settings of layouts, including Layout Info Panel custom data fields. |
| `SetLayoutSettings` | 1.1.7 | Sets settings of layouts, including Layout Info Panel custom data fields. |
| `GetLayoutCustomScheme` | 1.1.7 | Gets the Layout Info Panel custom field definitions (name and key) from Book Settings. |
| `GetModelViewOptions` | 1.1.4 | Gets all model view options |
| `GetViewSettings` | 1.1.4 | Gets the view settings of navigator items |
| `SetViewSettings` | 1.1.4 | Sets the view settings of navigator items |
| `GetView2DTransformations` | 1.1.7 | Get zoom and rotation of 2D views |
| `SetViewRotation` | 1.1.7 | Set the rotation angle of 2D views via their floor plan database. |
| `CloneProjectMapItemToViewMap` | 1.1.7 | Clones Project Map viewpoints into the View Map, optionally into a specified folder. |
| `CreateViewsInViewMap` | 1.1.7 | Creates independent (non-clone) navigator views in the View Map by copying database and settings from source items. |
| `CreateViewMapFolder` | 1.1.7 | Creates a new folder in the View Map. |
| `Set3DCutPlanes` | 1.3.1 | Sets the 3D cut planes. |
| `FitInWindow` | 1.3.1 | Zooms to the given elements or fits everything in the window. |
| `CreateSections` | 1.5.0 | Creates Section elements on the floor plan. |
| `CreateInteriorElevations` | 1.5.8 | Creates Interior Elevation elements on the floor plan. Every consecutive pair of the given points becomes one segment, each with its own ... |
| `MoveNavigatorItem` | 1.1.7 | Moves a navigator item to a new parent in the navigator tree. |
| `RenameNavigatorItem` | 1.1.7 | Renames a navigator item or changes its ID. |
| `DeleteNavigatorItems` | 1.1.7 | Deletes navigator items from the navigator tree. |
| `GetNavigatorItemTree` | 1.1.7 | Returns the full navigator item tree for the specified map. |

## Issue Management Commands (10)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `CreateIssue` | 1.0.2 | Creates a new issue. |
| `DeleteIssue` | 1.0.2 | Deletes the specified issue. |
| `GetIssues` | 1.0.2 | Retrieves information about existing issues. |
| `AddCommentToIssue` | 1.0.6 | Adds a new comment to the specified issue. |
| `GetCommentsFromIssue` | 1.0.6 | Retrieves comments information from the specified issue. |
| `AttachElementsToIssue` | 1.0.6 | Attaches elements to the specified issue. |
| `DetachElementsFromIssue` | 1.0.6 | Detaches elements from the specified issue. |
| `GetElementsAttachedToIssue` | 1.0.6 | Retrieves attached elements to the specified issue, filtered by attachment type. |
| `ExportIssuesToBCF` | 1.0.6 | Exports specified issues to a BCF file. |
| `ImportIssuesFromBCF` | 1.0.6 | Imports issues from a BCF file. |

## Revision Management Commands (5)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetRevisionIssues` | 1.1.9 | Retrieves all issues. |
| `GetRevisionChanges` | 1.1.9 | Retrieves all changes. |
| `GetDocumentRevisions` | 1.1.9 | Retrieves all document revisions. |
| `GetCurrentRevisionChangesOfLayouts` | 1.1.9 | Retrieves all changes belong to the last revision of the given layouts. |
| `GetRevisionChangesOfElements` | 1.1.9 | Retrieves the changes belong to the given elements. |

## Design Options Commands (11)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetDesignOptions` | 1.2.9 | Retrieves information about existing design options. Available from Archicad 29. |
| `GetDesignOptionSets` | 1.2.9 | Retrieves information about existing design option sets. Available from Archicad 29. |
| `GetDesignOptionCombinations` | 1.2.9 | Retrieves information about existing design option combinations. |
| `GetElementsOfDesignOptions` | 1.5.1 | Retrieves the elements associated with the given design options. Available from Archicad 29. |
| `GetDesignOptionForElements` | 1.5.1 | Retrieves the design option association for the specified elements. Available from Archicad 29. |
| `CreateDesignOptionSets` | 1.5.1 | Creates new design option sets with the given names. Available from Archicad 29. |
| `CreateDesignOptions` | 1.5.1 | Creates new design options with the given parameters. Available from Archicad 29. |
| `CreateDesignOptionCombinations` | 1.5.1 | Creates new design option combinations with the given parameters. Available from Archicad 29. |
| `SetActiveDesignOptionsInCombinations` | 1.5.1 | Sets active design options in the given combinations. Available from Archicad 29. |
| `MoveElementsToDesignOptions` | 1.5.1 | Moves the given elements into the given design options. Use NULLGuid for design option to remove the element from any design options and ... |
| `MoveDesignOptionsToAnotherSet` | 1.5.1 | Moves the given design options to another sets. Available from Archicad 29. |

## Keynote Commands (9)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetKeynoteTree` | 1.5.6 | Retrieves the whole keynote folder and item hierarchy. The technical root folder is not included in the output; the top-level folders and... |
| `GetKeynoteAutoTexts` | 1.5.6 | Retrieves the autotext tokens of the given keynote items. The tokens can be used as label text content to reference the fields of a keyno... |
| `CreateKeynoteFolders` | 1.5.6 | Creates keynote folders under the given parent folders (or under the root folder). Available from Archicad 28. |
| `CreateKeynoteItems` | 1.5.6 | Creates keynote items in the given parent folders (or in the root folder). Available from Archicad 28. |
| `ModifyKeynoteFolders` | 1.5.6 | Modifies the key, title or reference of the given keynote folders. Available from Archicad 28. |
| `ModifyKeynoteItems` | 1.5.6 | Modifies the key, title, description or reference of the given keynote items. Available from Archicad 28. |
| `DeleteKeynoteFolders` | 1.5.6 | Deletes keynote folders including their content. Available from Archicad 28. |
| `DeleteKeynoteItems` | 1.5.6 | Deletes keynote items. Available from Archicad 28. |
| `CreateKeynoteLabels` | 1.5.6 | Creates Label elements that reference the given keynote items via autotext. Available from Archicad 28. |

## MEP Commands (9)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GetMEPElements` | 1.5.6 | Retrieves the MEP (Mechanical, Electrical, Plumbing) elements of the project, optionally filtered by type and domain. MEP elements are or... |
| `GetMEPRoutingElements` | 1.5.6 | Retrieves the details of the given MEP routing elements: domain, MEP system, route polyline, segments with cross section data and nodes. ... |
| `GetMEPPorts` | 1.5.6 | Retrieves the ports of the given MEP elements including position, shape, size and connection status. Available from Archicad 28. |
| `GetMEPDistributionSystems` | 1.5.6 | Retrieves the MEP distribution systems of the project with their domain, MEP system attribute and member elements. Available from Archica... |
| `CreateMEPRoutingElements` | 1.5.6 | Creates MEP routing elements (duct, pipe or cable carrier routes) along the given polylines with optional cross section data and MEP syst... |
| `CreateMEPElements` | 1.5.6 | Creates MEP elements (Terminal, Accessory, Equipment or Fitting) at the given positions. Available from Archicad 28. |
| `ModifyMEPRoutingElements` | 1.5.6 | Modifies the given MEP routing elements: MEP system, cross section data of all segments and node positions. Available from Archicad 28. |
| `ConnectMEPElements` | 1.5.6 | Connects MEP routing elements to other MEP elements or routes. Merges routes, splits routes or creates branch elements as needed. Availab... |
| `GetMEPPreferenceTables` | 1.5.7 | Gets the circular cross section preference tables (referenceId, diameter, description) of the Piping or Ventilation domain. Available fro... |

## Solid Element Operation Commands (6)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `CreateSolidElementLinks` | 1.5.4 | Creates solid element operation links between target and operator elements. |
| `RemoveSolidElementLinks` | 1.5.4 | Removes solid element operation links between target and operator elements. |
| `GetSolidElementLinks` | 1.5.4 | Returns solid element operation links for each queried element, grouped by role (target or operator). |
| `TrimElements` | 1.5.9 | Trims construction elements with a roof or shell: the roofs and shells in the list, or one given trimming element with a trim type. |
| `RemoveElementTrims` | 1.5.9 | Removes the trim between an element and the roof or shell trimming it. |
| `GetElementTrims` | 1.5.9 | Which roofs and shells trim each queried element, with the trim type, and which elements it trims. |

## Script UI Commands (2)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `ShowScriptUI` | 1.5.4 | Shows the given HTML content in a native Archicad palette (a tkinter alternative for Python scripts). |
| `GetScriptUIResult` | 1.5.4 | Retrieves and clears the result last submitted from the Script UI palette's page (via window.ACAPI.SubmitResult), if any. |

## Developer Commands (1)
| Command | Schema version | Description (truncated) |
|---|---|---|
| `GenerateDocumentation` | 1.0.7 | Generates files for the documentation. Used by Tapir developers only. |
