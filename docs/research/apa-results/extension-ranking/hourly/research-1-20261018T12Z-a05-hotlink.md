# APA 12Z checks 27–30 — native bulk and hotlink

27. Tapir ElementCommands.cpp 1.5.9: MoveElements(copy=true) and RotateElements(copy=true) loop singleton ACAPI_Element_Edit per row. One JSON batch is not one SDK batch.

28. ProjectCommands.cpp SaveAsModuleFile(moduleFilePath,elements?) registered 1.5.9: explicit GUIDs allowed on AC29; existing .mod overwritten; malformed IDs may be skipped. No execution.

29. CreateHotlinkNodes/Instances/ChangeHotlinkInstances registered 1.5.9. Node dedup uses case-insensitive source path, not content SHA. Instance creation loops ACAPI_Element_Create; unspecified fields inherit tool defaults.

30. ProjectCommands.cpp states MoveElements/RotateElements on hotlink may return NoError yet move nothing. ChangeHotlinkInstances moves via transformation; angle/mirror rebuild loses scale/skew. GetDetailsOfElements exposes instance node/origin/rotation and child.hotlinkId. SOURCE only.
